"""
Dynamic Chat Handler with AI-powered MCP tool selection - like Claude Desktop
"""
import streamlit as st
import json
from typing import Dict, Any, List, Optional
from langchain.schema import HumanMessage, AIMessage
from datetime import datetime
from .dynamic_mcp_client import DynamicMCPClientSync as MCPClient


class ChatHandler:
    """Enhanced chat handler with dynamic MCP tool integration"""
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-3.5-turbo", mcp_client: Optional[MCPClient] = None):
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.mcp_client = mcp_client
        self.conversation_history = []
        
        # Initialize LLM
        self._initialize_llm()
    
    def _initialize_llm(self) -> None:
        """Initialize the language model"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        except ImportError:
            st.error("OpenAI library not found. Please install it: pip install openai")
            
    def process_input(self, user_input: str, context: Optional[str] = None) -> str:
        """Process user input and return response"""
        try:
            # First try MCP tools using dynamic selection
            mcp_result = self._try_dynamic_mcp_tools(user_input)
            if mcp_result:
                return mcp_result
            
            # If MCP doesn't handle it, use LLM
            return self._get_llm_response(user_input, context)
            
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _try_dynamic_mcp_tools(self, user_input: str) -> Optional[str]:
        """Try to handle user input with MCP tools using AI-powered dynamic selection"""
        if not self.mcp_client or not self.mcp_client._initialized:
            return None
        
        # Get all available tools
        available_tools = self.mcp_client.get_available_tools()
        if not available_tools:
            return None
        
        # Create tools context for AI decision making
        tools_context = self._create_tools_context(available_tools)
        
        # Use AI to determine which tool to use and extract parameters
        tool_decision = self._get_ai_tool_decision(user_input, tools_context)
        
        if tool_decision and tool_decision.get('tool_name') and tool_decision.get('parameters'):
            tool_name = tool_decision['tool_name']
            parameters = tool_decision['parameters']
            
            # Execute the tool
            success, result = self.mcp_client.execute_tool(tool_name, parameters)
            if success:
                return result
            else:
                return f"I encountered an issue using the {tool_name} tool: {result}"
        
        return None
    
    def _create_tools_context(self, available_tools: Dict[str, Any]) -> str:
        """Create a context description of available tools for AI decision making"""
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
    
    def _get_ai_tool_decision(self, user_input: str, tools_context: str) -> Optional[Dict[str, Any]]:
        """Use AI to decide which tool to use and extract parameters - like Claude Desktop"""
        prompt = f"""You are an AI assistant that can use various tools to help users. Analyze the user's request and determine if any available tools can help.

{tools_context}

User request: "{user_input}"

Analyze the user's request and determine:
1. If any of the available tools can help with this request
2. Which specific tool would be most appropriate
3. What parameters should be passed to that tool

If a tool can help, respond with a JSON object in this exact format:
{{
    "tool_name": "exact_tool_name",
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }},
    "reasoning": "brief explanation of why this tool was chosen"
}}

If no tool can help, respond with:
{{
    "tool_name": null,
    "parameters": null,
    "reasoning": "explanation of why no tool can help"
}}

Important guidelines:
- Use exact tool names from the available tools list
- Extract parameter values from the user's input when possible
- For weather requests with cities, convert to coordinates: Austin (30.2672, -97.7431), Dallas (32.7767, -96.7970), Houston (29.7604, -95.3698), NYC (40.7128, -74.0060), LA (34.0522, -118.2437), Frisco (33.1507, -96.8236)
- For math operations, extract numbers from expressions like "15 + 25" and determine the operation (add, sub, multiply)
- For file operations, expand common paths: "documents" -> ~/Documents, "desktop" -> ~/Desktop, etc.
- Be precise with parameter names and types as specified in the tool schema"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise tool selection assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse the JSON response
            tool_decision = json.loads(response_text)
            return tool_decision
            
        except Exception as e:
            print(f"Error in AI tool decision: {e}")
            return None
    
    def _get_llm_response(self, user_input: str, context: Optional[str] = None) -> str:
        """Get response from LLM when MCP tools don't handle the request"""
        try:
            # Prepare the prompt
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Be concise and accurate in your responses."}
            ]
            
            # Add context if provided
            if context:
                messages.append({"role": "system", "content": f"Additional context: {context}"})
            
            # Add MCP tools information if available
            if self.mcp_client and self.mcp_client._initialized:
                tools_description = self.mcp_client.get_tools_description()
                messages.append({"role": "system", "content": f"Note: I have access to these tools but they don't seem relevant to your current request:\n{tools_description}"})
            
            messages.append({"role": "user", "content": user_input})
            
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"I apologize, but I encountered an error processing your request: {str(e)}"


class MessageManager:
    """Manages chat messages and history"""
    
    @staticmethod
    def add_message(role: str, content: str) -> None:
        """Add a message to the session state"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        st.session_state.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    @staticmethod
    def clear_messages() -> None:
        """Clear all messages"""
        st.session_state.messages = []
    
    @staticmethod
    def get_messages() -> List[Dict[str, Any]]:
        """Get all messages"""
        return st.session_state.get("messages", [])
    
    @staticmethod
    def save_chat_to_history() -> None:
        """Save current chat to history"""
        if "messages" not in st.session_state or not st.session_state.messages:
            return
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Create a summary of the chat
        first_message = st.session_state.messages[0]["content"] if st.session_state.messages else "Empty chat"
        summary = first_message[:50] + "..." if len(first_message) > 50 else first_message
        
        chat_data = {
            "id": datetime.now().isoformat(),
            "summary": summary,
            "messages": st.session_state.messages.copy(),
            "timestamp": datetime.now().isoformat()
        }
        
        st.session_state.chat_history.append(chat_data)
    
    @staticmethod
    def load_chat_from_history(chat_data: Dict[str, Any]) -> None:
        """Load a chat from history"""
        st.session_state.messages = chat_data.get("messages", [])
    
    @staticmethod
    def start_new_chat() -> None:
        """Start a new chat session"""
        MessageManager.save_chat_to_history()
        MessageManager.clear_messages()