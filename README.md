# 🤖 HemPa Mitra: The Next Generation AI Assistant

*"Mitra" means "friend" in Marathi — your digital buddy that actually gets things done*

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red.svg)](https://streamlit.io)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green.svg)](https://modelcontextprotocol.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com)

---

## 🌟 What is HemPa Mitra?

HemPa Mitra is an AI assistant that bridges the gap between conversation and action. Unlike traditional AI assistants that only talk about things, HemPa Mitra actually **does** things using specialized tools through the Model Context Protocol (MCP).

### The Problem We Solve

Traditional AI assistants give you responses like:
- *"I can't access real-time weather data, but you can check..."* ❌
- *"I don't have access to current nutritional databases, but generally speaking..."* ❌

HemPa Mitra gives you actual results:
- **"Current weather in Austin: 72°F, sunny with light winds"** ✅
- **"Here are all 24 USDA food categories with their food counts"** ✅

---

## ✨ Key Features

### 🎯 **Dynamic Tool Selection**
- AI intelligently selects the right tool for each request
- No hardcoded logic - fully dynamic decision making
- Seamless fallback to general AI knowledge when tools can't help

### 🛠️ **29+ Specialized Tools**
- **🧮 Mathematics**: Real calculations (add, subtract, multiply)
- **🌤️ Weather**: Live forecast data and weather alerts  
- **📁 File Operations**: List directories, read files, search files
- **🥗 Nutrition**: USDA food database with 8,000+ foods

### 🔄 **Real-Time Data**
- Live weather conditions and forecasts
- Current file system state
- Up-to-date nutritional information
- Dynamic tool discovery and integration

### 🎨 **Professional UI**
- Clean Streamlit interface with custom styling
- Categorized tools with click-to-try examples
- Structured data display for JSON responses
- Chat history with conversation persistence

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js (for MCP servers)
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd myHemPaAgent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

### First Steps
Try these example queries:
- *"What is 25 + 17?"* (Math tool)
- *"What's the weather like today?"* (Weather tool)  
- *"List files in my Documents folder"* (Filesystem tool)
- *"Show me food categories"* (USDA nutrition tool)
- *"What is the capital of France?"* (General AI knowledge)

---

## 🏗️ Architecture

### Core Components

```
app.py                          # Main Streamlit application
mcp_client.py                   # MCP client with AI tool selection
defaults.py                     # Configuration and MCP server definitions  
system_message_prompt.py        # AI behavior configuration
src/
├── config/
│   ├── mcp_config.py          # MCP server configuration management
│   └── settings.py            # Application settings
└── handlers/
    └── dynamic_mcp_client.py  # Core MCP protocol implementation
```

### MCP Server Architecture

HemPa Mitra connects to multiple MCP servers simultaneously:

| Server | Purpose | Tools Provided |
|--------|---------|----------------|
| **Filesystem** | File operations | `list_directory`, `read_file`, `search_files` |
| **Math** | Calculations | `add`, `sub`, `multiply` |
| **Weather** | Weather data | `get_forecast`, `get_alerts` |  
| **USDA** | Nutrition data | `get_food_categories`, `search_foods`, `get_nutrition_profile` |

---

## 🔧 Configuration

### Adding New MCP Servers

1. **Install the MCP server**
   ```bash
   npm install -g @modelcontextprotocol/server-github
   ```

2. **Add configuration to `defaults.py`**
   ```python
   MCP_SERVER_CONFIGS = {
       "github": {
           "name": "GitHub Integration",
           "command": "npx",
           "args": ["-y", "@modelcontextprotocol/server-github"],
           "env": {
               "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token"
           },
           "transport": "stdio",
           "enabled": True,
           "description": "Access GitHub repositories and issues"
       }
   }
   ```

3. **Restart HemPa Mitra** - New tools are automatically discovered!

### Environment Variables

Create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
```

---

## 💡 Usage Examples

### Mathematical Calculations
```
User: "Calculate 15% tip on $87.50"
HemPa Mitra: [Uses multiply tool] "15% tip on $87.50 is $13.13"
```

### Weather Information  
```
User: "What's the weather in Austin?"
HemPa Mitra: [Uses weather tool] "Current conditions in Austin: 75°F, partly cloudy..."
```

### File Operations
```
User: "List Python files in my project"  
HemPa Mitra: [Uses filesystem tools] "Found 12 Python files: app.py, mcp_client.py..."
```

### Nutrition Data
```
User: "Compare nutrition of apples vs oranges"
HemPa Mitra: [Uses USDA tools] "Nutritional comparison: Apples (95 cal/medium)..."
```

### General Knowledge (AI Fallback)
```
User: "Explain quantum computing"
HemPa Mitra: [Uses AI knowledge] "Quantum computing leverages quantum mechanics..."
```

---

## 🛠️ Development

### Project Structure

```
myHemPaAgent/
├── app.py                      # Main Streamlit app
├── mcp_client.py              # MCP client implementation  
├── defaults.py                # Configuration
├── requirements.txt           # Dependencies
├── Fudge.jpg                 # Application logo
├── src/
│   ├── config/
│   │   ├── mcp_config.py     # MCP configuration manager
│   │   └── settings.py       # App settings
│   └── handlers/
│       └── dynamic_mcp_client.py  # Core MCP client
└── README.md                  # This file
```

### Key Classes

- **`HemPaMCPClient`**: Main client interface (synchronous wrapper)
- **`DynamicMCPClient`**: Async MCP client with tool discovery
- **`MCPServerConnection`**: Individual server connection handler
- **`MCPConfigManager`**: Configuration management

### Testing

```bash
# Test command line interface
python mcp_client.py "What is 5 + 3?"

# Test specific functionality
python -c "
from mcp_client import HemPaMCPClient
client = HemPaMCPClient()
print(client.process_query('List available food categories'))
client.cleanup()
"
```

---

## 🌐 Technology Stack

### Backend
- **Python 3.13**: Core language
- **AsyncIO**: Concurrent operations
- **OpenAI API**: LLM for decision making and fallback responses
- **Model Context Protocol**: Tool integration standard

### MCP Servers
- **@modelcontextprotocol/server-filesystem**: File operations
- **Custom Math Server**: Mathematical calculations  
- **Custom Weather Server**: Weather data integration
- **Custom USDA Server**: Nutrition database access

### Frontend  
- **Streamlit**: Web application framework
- **Custom CSS**: Professional styling
- **Responsive Design**: Desktop and mobile support

### Data Processing
- **JSON-RPC 2.0**: MCP communication protocol
- **Pandas**: Data manipulation (for structured responses)
- **AsyncIO**: Non-blocking I/O operations

---

## 🔮 Future Enhancements

### Planned Features
- [ ] **Enterprise Integration**: Database connectivity, API integrations
- [ ] **Multi-Modal Capabilities**: Image analysis, document processing  
- [ ] **Workflow Automation**: Chain multiple tools together
- [ ] **Custom Tool Builder**: GUI for creating MCP tools
- [ ] **Team Collaboration**: Shared chat sessions and tool access

### MCP Ecosystem
- [ ] **Email Integration**: Gmail/Outlook MCP servers
- [ ] **Calendar Management**: Google Calendar/Outlook Calendar
- [ ] **Social Media**: Twitter/LinkedIn posting tools
- [ ] **IoT Control**: Smart home device integration
- [ ] **Development Tools**: Git operations, code analysis

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Adding New MCP Servers
1. Create or find an MCP-compliant server
2. Add configuration to `defaults.py`  
3. Update UI categories if needed
4. Test integration and submit PR

### Improving Core Features
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

### Bug Reports
Use GitHub Issues with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

---

## 📜 License

This project is open source. Feel free to use, modify, and distribute according to the license terms.

---

## 🙏 Acknowledgments

- **Model Context Protocol**: For providing the foundation for tool integration
- **Streamlit**: For the excellent web app framework  
- **OpenAI**: For powerful language models
- **MCP Community**: For creating amazing tool servers

---

## 📞 Support

- **Documentation**: Check this README and code comments
- **Issues**: Use GitHub Issues for bug reports
- **Questions**: Open a discussion for usage questions

---

**HemPa Mitra** - Because the best AI assistant is one that feels less like a tool and more like a trusted friend. 🤖❤️

*Built with ❤️ using the Model Context Protocol*