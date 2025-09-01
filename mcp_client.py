"""
Modern MCP Client for HemPa Mitra using LangChain MCP adapters.
Based on the reference architecture from genai_streamlit_app.
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, cast
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import HumanMessage, AIMessage, BaseMessage, SystemMessage

# Import configurations
from defaults import DEFAULTS, MCP_SERVER_CONFIGS
from system_message_prompt import SYSTEM_MESSAGE

# Set up logging
logging.basicConfig(
    level=getattr(logging, DEFAULTS["LOG_LEVEL"]),
    format=DEFAULTS["LOG_FORMAT"],
)
logger = logging.getLogger("hempa-mcp-client")

# Load environment variables
load_dotenv()

# Initialize OpenAI model
model = ChatOpenAI(
    model=DEFAULTS["OPENAI_MODEL"],
    api_key=DEFAULTS["OPENAI_API_KEY"],
    temperature=DEFAULTS["OPENAI_TEMPERATURE"],
)

# Initialize embeddings for MCP sampling
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=DEFAULTS["OPENAI_API_KEY"],
)

# Global client and agent initialization
client = None
agent = None

def extract_last_assistant_reply(payload: Any) -> str:
    """Return the content of the final assistant message.

    Works whether *payload* is a list of BaseMessage objects, a list of dicts,
    or a dict wrapping those under the key "messages".
    """
    # unwrap {"messages": [...]} if necessary
    messages: Any = (
        payload.get("messages") if isinstance(payload, dict) else payload
    )

    if not messages:
        return ""

    texts: List[str] = []

    for m in messages:
        # LangChain message objects
        if isinstance(m, AIMessage) and m.content:
            content = m.content
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, list):
                text_parts: List[str] = []
                for part in content:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict):
                        text_val = part.get("text")
                        if isinstance(text_val, str):
                            text_parts.append(text_val)
                if text_parts:
                    texts.append(" ".join(text_parts))
        # plain dicts {"role": "assistant", "content": "..."}
        elif isinstance(m, dict):
            if m.get("role") == "assistant" and m.get("content"):
                texts.append(m["content"])

    return texts[-1] if texts else ""

async def initialize_client_and_agent():
    """Initialize the MCP client and agent."""
    global client, agent
    
    try:
        # Use our working dynamic MCP client
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        from config.mcp_config import MCPConfigManager
        from handlers.dynamic_mcp_client import DynamicMCPClient
        
        # Initialize MCP config and client
        config_manager = MCPConfigManager()
        client = DynamicMCPClient(config_manager)
        
        # Initialize the client
        success = await client.initialize()
        if not success:
            raise Exception("Failed to initialize MCP client")
        
        # Get available tools
        available_tools = client.get_available_tools()
        tools_count = len(available_tools)
        
        logger.info(f"MCP Client initialized with {tools_count} tools")
        logger.info(f"Available tools: {list(available_tools.keys())}")
        
        # For now, we'll use the client directly instead of creating a REACT agent
        # This gives us more control over the dynamic tool selection
        agent = client
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP client and agent: {e}")
        raise

async def run_agent(query: str):
    """Process query using dynamic MCP tool selection."""
    global agent, client
    
    # Ensure client and agent are initialized
    if agent is None or client is None:
        await initialize_client_and_agent()
        assert agent is not None

    logger.info("Processing query: %s", query)

    try:
        # Get available tools for dynamic selection
        available_tools = client.get_available_tools()
        logger.info(f"Got {len(available_tools)} available tools")
        
        # Create dynamic tool selection prompt
        tools_context = _create_tools_context(available_tools)
        logger.info("Created tools context")
        
        # Use AI to determine which tool to use
        logger.info("Calling AI tool decision...")
        tool_decision = await _get_ai_tool_decision(query, tools_context)
        
        if tool_decision and tool_decision.get('tool_name') and tool_decision.get('tool_name') != 'null' and 'parameters' in tool_decision:
            tool_name = tool_decision['tool_name']
            parameters = tool_decision['parameters']
            
            logger.info(f"Selected tool: {tool_name} with parameters: {parameters}")
            
            # Execute the tool
            success, result = await client.execute_tool(tool_name, parameters)
            if success:
                logger.info("Tool executed successfully")
                # Return in conversation format for compatibility
                return [
                    SystemMessage(content=SYSTEM_MESSAGE),
                    HumanMessage(content=query),
                    AIMessage(content=result)
                ]
            else:
                error_msg = f"Tool execution failed: {result}"
                logger.error(error_msg)
                return [
                    SystemMessage(content=SYSTEM_MESSAGE),
                    HumanMessage(content=query),
                    AIMessage(content=error_msg)
                ]
        else:
            # No tool selected, use LLM fallback
            logger.info("No suitable tool found, using LLM fallback")
            llm_response = await _get_llm_fallback_response(query)
            return [
                SystemMessage(content=SYSTEM_MESSAGE),
                HumanMessage(content=query),
                AIMessage(content=llm_response)
            ]
            
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        logger.error(error_msg)
        return [
            SystemMessage(content=SYSTEM_MESSAGE),
            HumanMessage(content=query),
            AIMessage(content=error_msg)
        ]

def _create_tools_context(available_tools: Dict[str, Any]) -> str:
    """Create a context description of available tools for AI decision making"""
    if not available_tools:
        return "No tools available."
    
    context_parts = ["Available MCP tools:"]
    
    for tool_name, tool in available_tools.items():
        # Get tool description and schema
        description = tool.description or "No description available"
        schema = tool.inputSchema or {}
        
        # Extract required parameters
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        param_info = []
        for param_name, param_details in properties.items():
            param_type = param_details.get('type', 'any')
            param_desc = param_details.get('description', '')
            is_required = param_name in required
            
            param_str = f"{param_name} ({param_type})"
            if is_required:
                param_str += " [required]"
            if param_desc:
                param_str += f": {param_desc}"
            param_info.append(param_str)
        
        tool_info = f"- {tool_name}: {description}"
        if param_info:
            tool_info += f"\n  Parameters: {', '.join(param_info)}"
        
        context_parts.append(tool_info)
    
    return "\n".join(context_parts)

async def _get_ai_tool_decision(query: str, tools_context: str) -> Dict[str, Any]:
    """Use AI to decide which tool to use and extract parameters"""
    logger.info("Starting AI tool decision process")
    prompt = f"""You are an AI assistant that can use various tools to help users. Analyze the user's request and determine if any available tools can help.

{tools_context}

User request: "{query}"

Analyze the user's request and determine:
1. If any of the available tools can help with this request
2. Which specific tool would be most appropriate  
3. What parameters should be passed to that tool

Respond with a JSON object in this exact format:
{{
    "tool_name": "exact_tool_name_or_null",
    "parameters": {{"param1": "value1", "param2": "value2"}},
    "reasoning": "brief explanation of why this tool was chosen or why no tool can help"
}}

Important guidelines:
- Use exact tool names from the available tools list
- Extract parameter values from the user's input when possible
- For weather: convert cities to coordinates (Austin: 30.2672,-97.7431, Dallas: 32.7767,-96.7970, Houston: 29.7604,-95.3698)
- For math: extract numbers and determine operation (add, sub, multiply)  
- For food/nutrition: use USDA tools (get_food_categories, search_foods, get_nutrition_profile, etc.)
- For files: expand paths (documents→~/Documents, desktop→~/Desktop)
- If no tool can help, set tool_name to null
- Always provide valid JSON

Examples:
- "What is 15 + 25?" → use "add" tool with {{a: 15, b: 25}}
- "Weather in Austin" → use "get_forecast" with coordinates  
- "Get food categories" → use "get_food_categories" tool (no parameters needed)
- "Search for apples" → use "search_foods" with {{query: "apples"}}
- "List files in documents" → use "list_directory" with {{path: "/Users/hemantapatil/Documents/"}}
- "List files" → use "list_directory" with {{path: "/Users/hemantapatil/Documents/"}}
- "Show files in my documents" → use "list_directory" with {{path: "/Users/hemantapatil/Documents/"}}"""

    try:
        logger.info("Invoking OpenAI model for tool selection")
        response = model.invoke([
            {"role": "system", "content": "You are a precise tool selection assistant. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ])
        logger.info("Got response from OpenAI model")
        
        response_text = response.content.strip()
        logger.info(f"AI tool decision response: {response_text}")
        
        # Try to parse the JSON response
        import json
        
        # Extract JSON if wrapped in markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            if json_end > json_start:
                response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            if json_end > json_start:
                response_text = response_text[json_start:json_end].strip()
        
        tool_decision = json.loads(response_text)
        return tool_decision
        
    except Exception as e:
        logger.error(f"Error in AI tool decision: {e}")
        return {"tool_name": None, "parameters": {}, "reasoning": f"Error processing request: {str(e)}"}

async def _get_llm_fallback_response(query: str) -> str:
    """Get response from LLM when no MCP tool can handle the request"""
    try:
        fallback_prompt = f"""You are HemPa Mitra, a helpful AI assistant. A user asked: "{query}"

While I have specialized tools for mathematical calculations, weather information, file system operations, and food/nutrition data, I can still help answer general questions using my knowledge.

Please provide a comprehensive, helpful response to the user's question. If it's something that would be better handled by one of my specialized tools, mention that, but still provide the best answer you can based on your general knowledge.

Available specialized tools (mention only if relevant):
- Mathematical calculations (add, subtract, multiply)
- Weather information and forecasts  
- File system operations (list directories, read/write files, search files)
- Food and nutrition database queries

Answer the user's question directly and helpfully."""

        response = model.invoke([
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": fallback_prompt}
        ])
        
        return response.content.strip()
        
    except Exception as e:
        logger.error(f"Error in LLM fallback: {e}")
        return f"I apologize, but I encountered an error processing your request: {str(e)}"

async def cleanup():
    """Clean up MCP client connections."""
    global client, agent
    
    if client:
        try:
            await client.cleanup()
        except Exception as e:
            logger.error(f"Error during client cleanup: {e}")
    
    client = None
    agent = None
    logger.info("MCP client cleaned up")

# Synchronous wrapper for Streamlit compatibility
class HemPaMCPClient:
    """Synchronous wrapper for HemPa Mitra MCP Client."""
    
    def __init__(self):
        self._initialized = False
        self._loop = None
    
    def _get_loop(self):
        """Get or create event loop"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop
    
    def initialize(self) -> bool:
        """Initialize the MCP client synchronously"""
        try:
            loop = self._get_loop()
            loop.run_until_complete(initialize_client_and_agent())
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            return False
    
    def process_query(self, query: str) -> str:
        """Process a query and return the assistant's response"""
        if not self._initialized:
            if not self.initialize():
                return "I apologize, but I'm having trouble connecting to my tools right now."
        
        try:
            loop = self._get_loop()
            conversation = loop.run_until_complete(run_agent(query))
            return extract_last_assistant_reply(conversation)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        if not self._initialized or not client:
            return []
        
        try:
            available_tools = client.get_available_tools()
            return list(available_tools.keys()) if available_tools else []
        except Exception as e:
            logger.error(f"Error getting tools: {e}")
            return []
    
    def cleanup(self):
        """Clean up resources"""
        if self._initialized:
            try:
                loop = self._get_loop()
                loop.run_until_complete(cleanup())
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                if self._loop and not self._loop.is_closed():
                    self._loop.close()
                self._loop = None
                self._initialized = False

if __name__ == "__main__":
    # Test the client
    import sys
    
    try:
        if len(sys.argv) > 1:
            query = " ".join(sys.argv[1:])
        else:
            query = input("Enter your query: ")

        client = HemPaMCPClient()
        answer = client.process_query(query)

        print("\nHemPa Mitra says:\n" + "-" * 50)
        print(answer)
        print("-" * 50)

    except Exception as exc:
        logger.error("Fatal error: %s", exc)
        raise
    finally:
        if 'client' in locals():
            client.cleanup()