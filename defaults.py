"""
Default configuration values for HemPa Mitra Agent.
These values are used as fallbacks when no user configuration is provided.
"""

import os

# Default configuration values
DEFAULTS = {
    # OpenAI configuration
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": 0.7,

    # Logging configuration
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    
    # Server configuration
    "SERVER_HOST": "0.0.0.0",
    "SERVER_PORT": 8501,
    "SERVER_DEBUG": False,
    
    # Application configuration
    "APP_NAME": "HemPa Mitra: AI Assistant",
    "APP_DESCRIPTION": "Dynamic MCP-powered AI assistant with multi-tool capabilities",
    "APP_ICON": "🤖",
    "APP_LAYOUT": "wide",
    
    # MCP Client configuration
    "MCP_TIMEOUT": 300,  # 5 minutes timeout
    "MCP_MAX_RETRIES": 3,
    "MCP_RETRY_DELAY": 1,
    
    # Chat configuration
    "MAX_CHAT_HISTORY": 50,
    "CHAT_INPUT_PLACEHOLDER": "Ask me anything! I can help with math, weather, files, food data, and more...",
    "DEFAULT_RESPONSE_TIMEOUT": 30,
}

# MCP Server configurations
MCP_SERVER_CONFIGS = {
    "filesystem": {
        "name": "filesystem",
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-filesystem",
            "/Users/hemantapatil/Documents/"
        ],
        "env": {},
        "transport": "stdio",
        "enabled": True,
        "description": "Access local filesystem"
    },
    "math_tool": {
        "name": "My Math Tool",
        "command": "/Users/hemantapatil/Documents/dev/ai_class/math_mcp/.venv/bin/python",
        "args": [
            "/Users/hemantapatil/Documents/dev/ai_class/math_mcp/math_server.py"
        ],
        "env": {
            "workingDirectory": "/Users/hemantapatil/Documents/dev/ai_class/math_mcp"
        },
        "transport": "stdio",
        "enabled": True,
        "description": "Mathematical operations"
    },
    "weather": {
        "name": "weather",
        "command": "/Users/hemantapatil/Documents/dev/ai_class/weather_mcp/.venv/bin/python",
        "args": [
            "/Users/hemantapatil/Documents/dev/ai_class/weather_mcp/weather.py"
        ],
        "env": {
            "workingDirectory": "/Users/hemantapatil/Documents/dev/ai_class/weather_mcp"
        },
        "transport": "stdio",
        "enabled": True,
        "description": "Get Weather Information"
    },
    "usda": {
        "name": "USDA",
        "command": "/Users/hemantapatil/Documents/dev/ai_class/mcp_postgres/.venv/bin/python",
        "args": [
            "/Users/hemantapatil/Documents/dev/ai_class/mcp_postgres/main.py"
        ],
        "env": {
            "workingDirectory": "/Users/hemantapatil/Documents/dev/ai_class/mcp_postgres"
        },
        "transport": "stdio",
        "enabled": True,
        "description": "USDA Food and Nutrition Database"
    }
}

# UI Categories and their corresponding tools
UI_CATEGORIES = {
    "Mathematics": {
        "description": "Perform calculations and solve mathematical problems",
        "tools": ["add", "sub", "multiply"],
        "icon": "🧮",
        "examples": [
            "Calculate 15 + 25",
            "What is 50 * 8?", 
            "Solve 100 - 37"
        ]
    },
    "Weather": {
        "description": "Get current weather and forecasts",
        "tools": ["get_forecast", "get_alerts"],
        "icon": "🌤️",
        "examples": [
            "What's the weather in Austin?",
            "Get forecast for Dallas",
            "Weather alerts for Texas"
        ]
    },
    "File System": {
        "description": "Browse and manage files and directories",
        "tools": ["list_files", "read_file", "write_file"],
        "icon": "📁",
        "examples": [
            "List files in Documents",
            "Show me files in current directory",
            "Read contents of a specific file"
        ]
    },
    "Food & Nutrition": {
        "description": "Search USDA food database and nutrition information",
        "tools": ["search_foods", "get_nutrition_profile", "compare_foods_nutrition"],
        "icon": "🥗",
        "examples": [
            "Search for high protein foods",
            "Compare nutrition of different foods",
            "Find foods rich in Vitamin C"
        ]
    }
}

# Required fields for validation
REQUIRED_FIELDS = {
    "openai": ["api_key"],
    "mcp": ["servers"]
}

# UI Styling
UI_STYLES = {
    "primary_color": "#4CAF50",
    "secondary_color": "#45a049",
    "background_color": "#f0f2f6",
    "text_color": "#333333",
    "border_radius": "5px",
    "button_padding": "0.25rem 1rem",
    "container_padding": "20px"
}