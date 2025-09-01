"""
MCP (Model Context Protocol) server configuration module
"""
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Import defaults from root level
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from defaults import DEFAULTS, MCP_SERVER_CONFIGS

class MCPTransportType(Enum):
    """MCP server transport types"""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str] = None
    env: Dict[str, str] = None
    transport: MCPTransportType = MCPTransportType.STDIO
    url: Optional[str] = None
    enabled: bool = True
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.env is None:
            self.env = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        data = asdict(self)
        data['transport'] = self.transport.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPServerConfig':
        """Create from dictionary representation"""
        if 'transport' in data:
            data['transport'] = MCPTransportType(data['transport'])
        return cls(**data)

class MCPConfigManager:
    """Manages MCP server configurations"""
    
    def __init__(self, config_file: str = "mcp_config.json"):
        """Initialize MCP configuration manager"""
        self.config_file = config_file
        self.servers: Dict[str, MCPServerConfig] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.servers = {
                        name: MCPServerConfig.from_dict(config)
                        for name, config in data.get('servers', {}).items()
                    }
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error loading MCP config: {e}")
                self.servers = {}
        else:
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create default MCP server configurations"""
        default_servers = {}
        for name, config in MCP_SERVER_CONFIGS.items():
            default_servers[name] = MCPServerConfig(
                name=config["name"],
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env", {}),
                transport=MCPTransportType(config.get("transport", "stdio")),
                enabled=config.get("enabled", True),
                description=config.get("description", "")
            )
        self.servers = default_servers
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        data = {
            'servers': {
                name: server.to_dict()
                for name, server in self.servers.items()
            }
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving MCP config: {e}")
    
    def add_server(self, server: MCPServerConfig) -> None:
        """Add a new MCP server configuration"""
        self.servers[server.name] = server
        self._save_config()
    
    def remove_server(self, name: str) -> bool:
        """Remove an MCP server configuration"""
        if name in self.servers:
            del self.servers[name]
            self._save_config()
            return True
        return False
    
    def update_server(self, name: str, server: MCPServerConfig) -> bool:
        """Update an existing MCP server configuration"""
        if name in self.servers:
            self.servers[name] = server
            self._save_config()
            return True
        return False
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get an MCP server configuration by name"""
        return self.servers.get(name)
    
    def get_all_servers(self) -> Dict[str, MCPServerConfig]:
        """Get all MCP server configurations"""
        return self.servers.copy()
    
    def get_enabled_servers(self) -> Dict[str, MCPServerConfig]:
        """Get only enabled MCP server configurations"""
        return {
            name: server for name, server in self.servers.items()
            if server.enabled
        }
    
    def enable_server(self, name: str) -> bool:
        """Enable an MCP server"""
        if name in self.servers:
            self.servers[name].enabled = True
            self._save_config()
            return True
        return False
    
    def disable_server(self, name: str) -> bool:
        """Disable an MCP server"""
        if name in self.servers:
            self.servers[name].enabled = False
            self._save_config()
            return True
        return False
    
    def validate_server_config(self, server: MCPServerConfig) -> List[str]:
        """Validate MCP server configuration and return list of errors"""
        errors = []
        
        if not server.name or not server.name.strip():
            errors.append("Server name is required")
        
        if not server.command or not server.command.strip():
            errors.append("Server command is required")
        
        if server.transport == MCPTransportType.HTTP and not server.url:
            errors.append("URL is required for HTTP transport")
        
        # Check for duplicate names
        if server.name in self.servers:
            errors.append(f"Server with name '{server.name}' already exists")
        
        return errors
    
    def export_config(self) -> str:
        """Export configuration as JSON string"""
        return json.dumps({
            'servers': {
                name: server.to_dict()
                for name, server in self.servers.items()
            }
        }, indent=2)
    
    def import_config(self, json_data: str) -> bool:
        """Import configuration from JSON string"""
        try:
            data = json.loads(json_data)
            servers = {}
            for name, config in data.get('servers', {}).items():
                servers[name] = MCPServerConfig.from_dict(config)
            self.servers = servers
            self._save_config()
            return True
        except Exception as e:
            print(f"Error importing MCP config: {e}")
            return False

# Predefined MCP server templates
MCP_SERVER_TEMPLATES = {
    "filesystem": {
        "name": "Filesystem Server",
        "command": "npx", 
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/Documents"],
        "description": "Access local filesystem (Documents folder)",
        "env_vars": {}
    },
    "brave-search": {
        "name": "Brave Search Server",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "description": "Search the web using Brave Search API",
        "env_vars": {"BRAVE_API_KEY": "Required - Get from brave.com/search/api"}
    },
    "github": {
        "name": "GitHub Server",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "description": "Access GitHub repositories and issues",
        "env_vars": {"GITHUB_PERSONAL_ACCESS_TOKEN": "Required - Generate from GitHub settings"}
    },
    "postgres": {
        "name": "PostgreSQL Server",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
        "description": "Connect to PostgreSQL databases",
        "env_vars": {"POSTGRES_CONNECTION_STRING": "Required - postgresql://user:pass@host/db"}
    },
    "sqlite": {
        "name": "SQLite Server",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite"],
        "description": "Connect to SQLite databases",
        "env_vars": {}
    },
    "google-drive": {
        "name": "Google Drive Server",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-gdrive"],
        "description": "Access Google Drive files",
        "env_vars": {
            "GDRIVE_CLIENT_ID": "Required - Google Cloud Console client ID",
            "GDRIVE_CLIENT_SECRET": "Required - Google Cloud Console client secret"
        }
    }
}