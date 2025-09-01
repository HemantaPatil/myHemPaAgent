"""
Modern Streamlit app for HemPa Mitra - MCP-powered AI Assistant.
"""

import streamlit as st
import asyncio
import json
from typing import Dict, Any
import pandas as pd
import os
from mcp_client import HemPaMCPClient
from defaults import DEFAULTS, UI_CATEGORIES, UI_STYLES

# Set page config
st.set_page_config(
    page_title=DEFAULTS["APP_NAME"],
    page_icon=DEFAULTS["APP_ICON"],
    layout=DEFAULTS["APP_LAYOUT"],
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown(f"""
    <style>
    .stTextArea > div {{
        width: 100% !important;
    }}
    .stTextArea > div > div > textarea {{
        font-size: 16px;
        width: 100% !important;
        border: 2px solid {UI_STYLES["primary_color"]} !important;
        border-radius: {UI_STYLES["border_radius"]} !important;
        padding: 8px !important;
    }}
    .stButton > button {{
        font-size: 14px;
        background-color: {UI_STYLES["primary_color"]};
        color: white;
        padding: {UI_STYLES["button_padding"]};
        min-width: 120px;
        margin-top: 10px;
        border-radius: {UI_STYLES["border_radius"]};
        border: none;
    }}
    .stButton > button:hover {{
        background-color: {UI_STYLES["secondary_color"]};
    }}
    .response-box {{
        background-color: {UI_STYLES["background_color"]};
        padding: {UI_STYLES["container_padding"]};
        border-radius: {UI_STYLES["border_radius"]};
        margin: 10px 0;
        border-left: 4px solid {UI_STYLES["primary_color"]};
    }}
    .category-header {{
        font-size: 1.2em;
        font-weight: bold;
        color: {UI_STYLES["primary_color"]};
        margin-top: 0.5em;
        margin-bottom: 0.5em;
    }}
    .tool-example {{
        background-color: #f8f9fa;
        padding: 8px 12px;
        border-radius: 4px;
        margin: 4px 0;
        font-size: 0.9em;
        border-left: 3px solid {UI_STYLES["primary_color"]};
    }}
    </style>
""", unsafe_allow_html=True)

# Header with logo - compact version
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("Fudge.jpg", width=60)
    except:
        st.markdown(f"## {DEFAULTS['APP_ICON']}")  # Smaller fallback emoji
with col2:
    st.markdown(f"## {DEFAULTS['APP_NAME']}")  # Smaller title
    st.caption(DEFAULTS['APP_DESCRIPTION'])  # Caption instead of markdown for smaller text

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = None

if "client_initialized" not in st.session_state:
    st.session_state.client_initialized = False

def initialize_mcp_client():
    """Initialize MCP client if not already done"""
    if not st.session_state.client_initialized:
        with st.spinner("🔧 Connecting to MCP tools..."):
            try:
                st.session_state.mcp_client = HemPaMCPClient()
                success = st.session_state.mcp_client.initialize()
                if success:
                    st.session_state.client_initialized = True
                    st.success("✅ MCP tools connected successfully!")
                    return True
                else:
                    st.error("❌ Failed to initialize MCP tools")
                    return False
            except Exception as e:
                st.error(f"❌ Error initializing MCP client: {str(e)}")
                return False
    return True

def handle_category_click(category: str):
    """Handle category selection from sidebar"""
    st.session_state.selected_category = category
    st.session_state.custom_query = ""

# Sidebar
with st.sidebar:
    # Enhanced logo in sidebar - 50% larger and perfectly aligned title
    try:
        # Center the logo
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("Fudge.jpg", width=105)  # 50% larger: 70 * 1.5 = 105
    except:
        pass  # If image not found, just continue without it
    
    # Title perfectly aligned below logo using same column structure
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            "<h3 style='text-align: center; margin-top: 10px;'>🤖 HemPa Mitra</h3>", 
            unsafe_allow_html=True
        )
    
    # About section - collapsed by default to save space
    with st.expander("About", expanded=False):
        st.markdown("""
            AI assistant with MCP tools for:
            - 🧮 Math calculations
            - 🌤️ Weather info  
            - 📁 File operations
            - 🥗 Food & nutrition
        """)
    
    # Categories section
    st.markdown("### 🔧 Tool Categories")
    
    # Display categories
    for category_name, category_info in UI_CATEGORIES.items():
        with st.expander(f"{category_info['icon']} {category_name}", expanded=False):
            st.markdown(f"**{category_info['description']}**")
            
            # Show example queries
            st.markdown("**Examples:**")
            for example in category_info['examples']:
                if st.button(f"💡 {example}", key=f"example_{category_name}_{example}", use_container_width=True):
                    st.session_state.custom_query = example
                    st.session_state.selected_category = category_name
    
    st.markdown("---")
    
    # Settings section
    with st.expander("⚙️ Settings", expanded=False):
        st.markdown("### Model Configuration")
        model = st.selectbox(
            "OpenAI Model",
            options=["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"],
            index=0,
            key="model_selector"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=DEFAULTS["OPENAI_TEMPERATURE"],
            step=0.1,
            key="temperature_selector"
        )
        
        if st.button("🔄 Reset MCP Client", use_container_width=True):
            if st.session_state.mcp_client:
                st.session_state.mcp_client.cleanup()
            st.session_state.client_initialized = False
            st.session_state.mcp_client = None
            st.rerun()

# Initialize session state for custom query
if "custom_query" not in st.session_state:
    st.session_state.custom_query = ""

# Main content area - compact header
st.markdown("#### 💬 Chat")  # Smaller header with shorter text

# Query input form
placeholder_text = DEFAULTS["CHAT_INPUT_PLACEHOLDER"]
if st.session_state.selected_category:
    category_info = UI_CATEGORIES[st.session_state.selected_category]
    placeholder_text = f"Ask me about {category_info['description'].lower()}..."

with st.form("chat_form"):
    query = st.text_area(
        "Ask me anything:",  # Shorter label
        value=st.session_state.custom_query,
        key="query_input",
        placeholder=placeholder_text,
        height=80  # Reduced height
    )
    
    # Submit button (this will trigger on Enter key)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        submit_button = st.form_submit_button("🚀 Ask HemPa", use_container_width=True)
    with col2:
        clear_button = st.form_submit_button("🗑️ Clear", use_container_width=True)

if clear_button:
    st.session_state.custom_query = ""
    st.rerun()

# Process query
if submit_button and query and query.strip():
    # Initialize MCP client if needed
    if not initialize_mcp_client():
        st.stop()
    
    with st.spinner("🤔 Thinking..."):
        try:
            # Process the query
            response = st.session_state.mcp_client.process_query(query)
            
            # Add to chat history
            st.session_state.chat_history.append({
                "query": query,
                "response": response,
                "category": st.session_state.selected_category
            })
            
            # Display response - compact
            st.markdown("**🎯 Response**")  # Smaller, bold text instead of header
            st.markdown('<div class="response-box">', unsafe_allow_html=True)
            
            # Try to parse JSON response for structured data
            try:
                response_data = json.loads(response)
                if isinstance(response_data, dict):
                    # Display structured data
                    for section, data in response_data.items():
                        st.subheader(section.replace("_", " ").title())
                        if isinstance(data, dict):
                            df = pd.DataFrame([data])
                            st.dataframe(df, use_container_width=True)
                        elif isinstance(data, list):
                            for item in data:
                                st.write(f"• {item}")
                        else:
                            st.write(data)
                else:
                    st.markdown(response)
            except json.JSONDecodeError:
                # Display as markdown
                st.markdown(response)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")

elif submit_button and not query.strip():
    st.warning("⚠️ Please enter a question.")

# Chat History - compact
if st.session_state.chat_history:
    st.markdown("**📜 Recent Chats**")  # Smaller header
    
    # Show recent conversations
    for i, chat in enumerate(reversed(st.session_state.chat_history[-3:])):  # Last 3 chats only
        with st.expander(f"💬 {chat['query'][:45]}{'...' if len(chat['query']) > 45 else ''}", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("**Question:**")
                st.write(chat['query'])
            with col2:
                if chat.get('category'):
                    category_info = UI_CATEGORIES.get(chat['category'], {})
                    icon = category_info.get('icon', '🔧')
                    st.markdown(f"**Category:** {icon} {chat['category']}")
            
            st.markdown("**Answer:**")
            try:
                # Try to format as JSON if possible
                response_data = json.loads(chat['response'])
                st.json(response_data)
            except json.JSONDecodeError:
                st.write(chat['response'])
    
    # Clear history button
    if len(st.session_state.chat_history) > 0:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

# Footer - compact
with st.expander("🔧 MCP Status", expanded=False):  # Collapsed by default
    if st.session_state.client_initialized and st.session_state.mcp_client:
        try:
            tools = st.session_state.mcp_client.get_available_tools()
            if tools:
                st.success(f"✅ {len(tools)} tools connected")
                st.caption("Math, Weather, Files, Food & Nutrition tools ready")
            else:
                st.warning("⚠️ Connected but no tools available")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    else:
        st.info("🔄 Click 'Ask HemPa' to connect")

# Cleanup on app shutdown
import atexit
def cleanup_mcp():
    if st.session_state.get("mcp_client"):
        st.session_state.mcp_client.cleanup()

atexit.register(cleanup_mcp)