"""
Dynamic MCP Client implementation using actual MCP protocol
This client dynamically discovers server capabilities and forwards tool calls
"""
import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import uuid
from config.mcp_config import MCPConfigManager, MCPServerConfig, MCPTransportType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    """Represents an MCP tool/function"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    server_name: str

@dataclass
class MCPResource:
    """Represents an MCP resource"""
    uri: str
    name: str
    description: Optional[str]
    mimeType: Optional[str]
    server_name: str

class MCPServerConnection:
    """Manages connection to a single MCP server"""
    
    def __init__(self, server_config: MCPServerConfig):
        self.config = server_config
        self.process: Optional[subprocess.Popen] = None
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self._initialized = False
    
    async def connect(self) -> bool:
        """Connect to the MCP server"""
        try:
            if self.config.transport == MCPTransportType.STDIO:
                return await self._connect_stdio()
            else:
                logger.error(f"Transport {self.config.transport} not yet implemented")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to {self.config.name}: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Connect via STDIO transport"""
        try:
            # Start the MCP server process
            env = dict(self.config.env) if self.config.env else {}
            
            self.process = subprocess.Popen(
                [self.config.command] + (self.config.args or []),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**dict(os.environ), **env} if env else None
            )
            
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": True},
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "HemPa-MCP-Client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self._send_request(init_request)
            if not response or "error" in response:
                logger.error(f"Initialize failed for {self.config.name}: {response}")
                return False
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await self._send_notification(initialized_notification)
            
            # Discover tools and resources
            await self._discover_capabilities()
            
            self._initialized = True
            logger.info(f"Successfully connected to MCP server: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"STDIO connection failed for {self.config.name}: {e}")
            if self.process:
                self.process.terminate()
            return False
    
    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request and wait for response"""
        if not self.process:
            return None
            
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            # Read response - handle bidirectional communication
            request_id = request.get("id")
            while True:
                response_line = self.process.stdout.readline()
                if not response_line:
                    return None
                    
                response = json.loads(response_line.strip())
                
                # Handle incoming requests from server (like roots/list)
                if response.get("method") and "id" in response:
                    await self._handle_server_request(response)
                    continue
                
                # Return our response if it matches the request ID
                if response.get("id") == request_id:
                    return response
                    
                # Skip other messages
                continue
            
        except Exception as e:
            logger.error(f"Request failed for {self.config.name}: {e}")
            return None
    
    async def _send_notification(self, notification: Dict[str, Any]) -> None:
        """Send a JSON-RPC notification (no response expected)"""
        if not self.process:
            return
            
        try:
            notification_json = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_json)
            self.process.stdin.flush()
        except Exception as e:
            logger.error(f"Notification failed for {self.config.name}: {e}")
    
    async def _handle_server_request(self, request: Dict[str, Any]) -> None:
        """Handle incoming requests from the server"""
        method = request.get("method")
        request_id = request.get("id")
        
        try:
            if method == "roots/list":
                # Respond to roots/list request
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "roots": []  # Empty roots list for now
                    }
                }
                response_json = json.dumps(response) + "\n"
                self.process.stdin.write(response_json)
                self.process.stdin.flush()
            else:
                # Send error for unhandled methods
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                response_json = json.dumps(error_response) + "\n"
                self.process.stdin.write(response_json)
                self.process.stdin.flush()
                
        except Exception as e:
            logger.error(f"Error handling server request {method}: {e}")
    
    async def _discover_capabilities(self) -> None:
        """Discover tools and resources from the server"""
        # List tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list"
        }
        
        tools_response = await self._send_request(tools_request)
        if tools_response and "result" in tools_response:
            tools_data = tools_response["result"].get("tools", [])
            for tool_data in tools_data:
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    inputSchema=tool_data.get("inputSchema", {}),
                    server_name=self.config.name
                )
                self.tools[tool.name] = tool
        
        # List resources
        resources_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "resources/list"
        }
        
        resources_response = await self._send_request(resources_request)
        if resources_response and "result" in resources_response:
            resources_data = resources_response["result"].get("resources", [])
            for resource_data in resources_data:
                resource = MCPResource(
                    uri=resource_data["uri"],
                    name=resource_data["name"],
                    description=resource_data.get("description"),
                    mimeType=resource_data.get("mimeType"),
                    server_name=self.config.name
                )
                self.resources[resource.uri] = resource
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """Call a tool on this server"""
        if not self._initialized or tool_name not in self.tools:
            return False, f"Tool {tool_name} not available on server {self.config.name}"
        
        try:
            call_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await self._send_request(call_request)
            if not response:
                return False, "No response from server"
            
            if "error" in response:
                error = response["error"]
                return False, f"Server error: {error.get('message', 'Unknown error')}"
            
            if "result" in response:
                result = response["result"]
                # Format the result content
                if "content" in result:
                    content_items = result["content"]
                    formatted_content = []
                    for item in content_items:
                        if item.get("type") == "text":
                            formatted_content.append(item.get("text", ""))
                    return True, "\n".join(formatted_content)
                else:
                    return True, json.dumps(result, indent=2)
            
            return False, "No result in response"
            
        except Exception as e:
            logger.error(f"Tool call failed for {tool_name} on {self.config.name}: {e}")
            return False, f"Tool execution error: {str(e)}"
    
    async def read_resource(self, resource_uri: str) -> Tuple[bool, str]:
        """Read a resource from this server"""
        if not self._initialized or resource_uri not in self.resources:
            return False, f"Resource {resource_uri} not available on server {self.config.name}"
        
        try:
            read_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "resources/read",
                "params": {
                    "uri": resource_uri
                }
            }
            
            response = await self._send_request(read_request)
            if not response:
                return False, "No response from server"
            
            if "error" in response:
                error = response["error"]
                return False, f"Server error: {error.get('message', 'Unknown error')}"
            
            if "result" in response:
                result = response["result"]
                if "contents" in result:
                    contents = result["contents"]
                    formatted_content = []
                    for content in contents:
                        if content.get("type") == "text":
                            formatted_content.append(content.get("text", ""))
                    return True, "\n".join(formatted_content)
                else:
                    return True, json.dumps(result, indent=2)
            
            return False, "No result in response"
            
        except Exception as e:
            logger.error(f"Resource read failed for {resource_uri} on {self.config.name}: {e}")
            return False, f"Resource read error: {str(e)}"
    
    def disconnect(self):
        """Disconnect from the server"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self.process = None
        self._initialized = False

class DynamicMCPClient:
    """Dynamic MCP Client that connects to actual MCP servers"""
    
    def __init__(self, config_manager: MCPConfigManager):
        """Initialize Dynamic MCP client"""
        self.config_manager = config_manager
        self.server_connections: Dict[str, MCPServerConnection] = {}
        self.available_tools: Dict[str, MCPTool] = {}
        self.available_resources: Dict[str, MCPResource] = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize client and connect to all enabled servers"""
        try:
            enabled_servers = self.config_manager.get_enabled_servers()
            
            # Connect to each enabled server
            connection_tasks = []
            for server_name, server_config in enabled_servers.items():
                connection = MCPServerConnection(server_config)
                self.server_connections[server_name] = connection
                connection_tasks.append(self._connect_server(connection))
            
            # Wait for all connections
            results = await asyncio.gather(*connection_tasks, return_exceptions=True)
            
            # Collect all tools and resources
            for connection in self.server_connections.values():
                if connection._initialized:
                    self.available_tools.update(connection.tools)
                    self.available_resources.update(connection.resources)
            
            self._initialized = True
            
            success_count = sum(1 for r in results if r is True)
            total_count = len(enabled_servers)
            
            logger.info(f"Dynamic MCP Client initialized: {success_count}/{total_count} servers connected")
            logger.info(f"Available tools: {len(self.available_tools)}")
            logger.info(f"Available resources: {len(self.available_resources)}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to initialize Dynamic MCP Client: {e}")
            return False
    
    async def _connect_server(self, connection: MCPServerConnection) -> bool:
        """Connect to a single server"""
        return await connection.connect()
    
    def get_available_tools(self) -> Dict[str, MCPTool]:
        """Get all available tools from connected servers"""
        if not self._initialized:
            asyncio.run(self.initialize())
        return self.available_tools.copy()
    
    def get_available_resources(self) -> Dict[str, MCPResource]:
        """Get all available resources from connected servers"""
        if not self._initialized:
            asyncio.run(self.initialize())
        return self.available_resources.copy()
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute a tool by forwarding to the appropriate server"""
        if tool_name not in self.available_tools:
            return False, f"Tool {tool_name} not found"
        
        tool = self.available_tools[tool_name]
        connection = self.server_connections.get(tool.server_name)
        
        if not connection or not connection._initialized:
            return False, f"Server {tool.server_name} not connected"
        
        return await connection.call_tool(tool_name, parameters)
    
    async def read_resource(self, resource_uri: str) -> Tuple[bool, str]:
        """Read a resource by forwarding to the appropriate server"""
        if resource_uri not in self.available_resources:
            return False, f"Resource {resource_uri} not found"
        
        resource = self.available_resources[resource_uri]
        connection = self.server_connections.get(resource.server_name)
        
        if not connection or not connection._initialized:
            return False, f"Server {resource.server_name} not connected"
        
        return await connection.read_resource(resource_uri)
    
    def get_tools_description(self) -> str:
        """Get a description of all available tools"""
        if not self._initialized:
            asyncio.run(self.initialize())
        
        if not self.available_tools:
            return "No MCP servers are currently connected."
        
        descriptions = ["Available tools from connected MCP servers:"]
        
        # Group tools by server
        tools_by_server = {}
        for tool_name, tool in self.available_tools.items():
            if tool.server_name not in tools_by_server:
                tools_by_server[tool.server_name] = []
            tools_by_server[tool.server_name].append(tool)
        
        for server_name, tools in tools_by_server.items():
            descriptions.append(f"\n🔧 {server_name} Server:")
            for tool in tools:
                descriptions.append(f"  • {tool.name}: {tool.description}")
        
        descriptions.append("\nYou can use these tools to help users with their requests.")
        return "\n".join(descriptions)
    
    def has_capability(self, capability: str) -> bool:
        """Check if any connected server has a specific capability"""
        capability_lower = capability.lower()
        
        # Define capability mappings based on available tool patterns
        capability_patterns = {
            'weather': ['forecast', 'weather', 'alerts', 'temperature', 'climate'],
            'math': ['add', 'sub', 'multiply', 'calculate', 'solve', 'equation'],
            'search': ['search', 'find', 'lookup'],
            'filesystem': ['list_files', 'read_file', 'write_file', 'file'],
            'database': ['query', 'table', 'sql', 'database'],
            'usda': ['food', 'nutrition', 'usda'],
            'food': ['food', 'nutrition', 'usda'],
            'nutrition': ['food', 'nutrition', 'usda']
        }
        
        # Check if we have tools that match this capability
        if capability_lower in capability_patterns:
            patterns = capability_patterns[capability_lower]
            for tool_name in self.available_tools:
                for pattern in patterns:
                    if pattern in tool_name.lower():
                        return True
        
        # Fallback: check if capability name is in any tool name
        for tool_name in self.available_tools:
            if capability_lower in tool_name.lower():
                return True
        
        return False
    
    async def cleanup(self):
        """Disconnect from all servers"""
        for connection in self.server_connections.values():
            connection.disconnect()
        
        self.server_connections.clear()
        self.available_tools.clear()
        self.available_resources.clear()
        self._initialized = False
        
        logger.info("Dynamic MCP Client disconnected from all servers")

# Synchronous wrapper for compatibility
class DynamicMCPClientSync:
    """Synchronous wrapper for DynamicMCPClient"""
    
    def __init__(self, config_manager: MCPConfigManager):
        self.async_client = DynamicMCPClient(config_manager)
        self._loop = None
    
    @property
    def _initialized(self) -> bool:
        """Check if the client is initialized"""
        return self.async_client._initialized
    
    def _get_loop(self):
        """Get or create event loop"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop
    
    def initialize(self) -> bool:
        """Initialize the client synchronously"""
        loop = self._get_loop()
        return loop.run_until_complete(self.async_client.initialize())
    
    def get_available_tools(self) -> Dict[str, MCPTool]:
        """Get available tools synchronously"""
        return self.async_client.get_available_tools()
    
    def get_available_resources(self) -> Dict[str, MCPResource]:
        """Get available resources synchronously"""
        return self.async_client.get_available_resources()
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute tool synchronously"""
        loop = self._get_loop()
        return loop.run_until_complete(self.async_client.execute_tool(tool_name, parameters))
    
    def read_resource(self, resource_uri: str) -> Tuple[bool, str]:
        """Read resource synchronously"""
        loop = self._get_loop()
        return loop.run_until_complete(self.async_client.read_resource(resource_uri))
    
    def get_tools_description(self) -> str:
        """Get tools description synchronously"""
        return self.async_client.get_tools_description()
    
    def has_capability(self, capability: str) -> bool:
        """Check capability synchronously"""
        return self.async_client.has_capability(capability)
    
    def cleanup(self):
        """Cleanup synchronously"""
        if self._loop and not self._loop.is_closed():
            self._loop.run_until_complete(self.async_client.cleanup())
            self._loop.close()
        self._loop = None