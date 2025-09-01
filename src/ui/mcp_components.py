"""
UI components for MCP server configuration
"""
import streamlit as st
from typing import Dict, List, Optional, Any
from config.mcp_config import MCPConfigManager, MCPServerConfig, MCPTransportType, MCP_SERVER_TEMPLATES

class MCPUIComponents:
    """UI components for MCP server management"""
    
    @staticmethod
    def render_mcp_sidebar(mcp_manager: MCPConfigManager) -> None:
        """Render MCP configuration section in sidebar"""
        st.markdown("### MCP Servers")
        
        # Server status overview
        all_servers = mcp_manager.get_all_servers()
        enabled_servers = mcp_manager.get_enabled_servers()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", len(all_servers))
        with col2:
            st.metric("Enabled", len(enabled_servers))
        
        # Quick enable/disable toggles for existing servers
        if all_servers:
            st.markdown("#### Quick Controls")
            for name, server in all_servers.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    status = "🟢" if server.enabled else "🔴"
                    st.text(f"{status} {server.name}")
                with col2:
                    if st.button("Toggle", key=f"toggle_{name}", help=f"Toggle {name}"):
                        if server.enabled:
                            mcp_manager.disable_server(name)
                        else:
                            mcp_manager.enable_server(name)
                        st.rerun()
        
        # Configuration button
        if st.button("⚙️ Configure MCP", use_container_width=True):
            st.session_state.show_mcp_config = True
            st.rerun()
    
    @staticmethod
    def render_mcp_config_page(mcp_manager: MCPConfigManager) -> None:
        """Render full MCP configuration page"""
        st.markdown("# MCP Server Configuration")
        st.markdown("Configure Model Context Protocol servers to extend AI capabilities.")
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Server List", "➕ Add Server", "📥 Import/Export", "ℹ️ About MCP"])
        
        with tab1:
            MCPUIComponents._render_server_list(mcp_manager)
        
        with tab2:
            MCPUIComponents._render_add_server(mcp_manager)
        
        with tab3:
            MCPUIComponents._render_import_export(mcp_manager)
        
        with tab4:
            MCPUIComponents._render_mcp_info()
    
    @staticmethod
    def _render_server_list(mcp_manager: MCPConfigManager) -> None:
        """Render list of configured servers"""
        servers = mcp_manager.get_all_servers()
        
        if not servers:
            st.info("No MCP servers configured yet. Use the 'Add Server' tab to get started.")
            return
        
        # Search/filter
        search = st.text_input("🔍 Search servers:", placeholder="Filter by name or description")
        
        # Filter servers based on search
        filtered_servers = servers
        if search:
            filtered_servers = {
                name: server for name, server in servers.items()
                if search.lower() in name.lower() or 
                   (server.description and search.lower() in server.description.lower())
            }
        
        # Display servers
        for name, server in filtered_servers.items():
            with st.expander(f"{'🟢' if server.enabled else '🔴'} {server.name}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Description:** {server.description or 'No description'}")
                    st.markdown(f"**Command:** `{server.command} {' '.join(server.args)}`")
                    st.markdown(f"**Transport:** {server.transport.value}")
                    
                    if server.env:
                        st.markdown("**Environment Variables:**")
                        for key, value in server.env.items():
                            masked_value = "***" if any(secret in key.lower() for secret in ['key', 'token', 'secret', 'password']) else value
                            st.code(f"{key}={masked_value}")
                
                with col2:
                    # Enable/Disable
                    if st.button("Enable" if not server.enabled else "Disable", 
                               key=f"enable_{name}",
                               type="primary" if not server.enabled else "secondary"):
                        if server.enabled:
                            mcp_manager.disable_server(name)
                        else:
                            mcp_manager.enable_server(name)
                        st.rerun()
                    
                    # Edit button
                    if st.button("✏️ Edit", key=f"edit_{name}"):
                        st.session_state[f"edit_server_{name}"] = True
                        st.rerun()
                    
                    # Delete button
                    if st.button("🗑️ Delete", key=f"delete_{name}"):
                        if st.session_state.get(f"confirm_delete_{name}", False):
                            mcp_manager.remove_server(name)
                            del st.session_state[f"confirm_delete_{name}"]
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{name}"] = True
                            st.rerun()
                    
                    if st.session_state.get(f"confirm_delete_{name}", False):
                        st.error("Click delete again to confirm")
                
                # Edit form
                if st.session_state.get(f"edit_server_{name}", False):
                    MCPUIComponents._render_edit_server_form(mcp_manager, name, server)
    
    @staticmethod
    def _render_edit_server_form(mcp_manager: MCPConfigManager, name: str, server: MCPServerConfig) -> None:
        """Render edit form for a server"""
        st.markdown("---")
        st.markdown("### Edit Server Configuration")
        
        with st.form(f"edit_server_form_{name}"):
            new_name = st.text_input("Server Name", value=server.name)
            description = st.text_input("Description", value=server.description or "")
            command = st.text_input("Command", value=server.command)
            args_text = st.text_input("Arguments (space-separated)", value=" ".join(server.args))
            
            transport = st.selectbox(
                "Transport Type",
                options=[t.value for t in MCPTransportType],
                index=[t.value for t in MCPTransportType].index(server.transport.value)
            )
            
            url = st.text_input("URL (for HTTP transport)", value=server.url or "")
            
            # Environment variables
            st.markdown("**Environment Variables**")
            env_vars = {}
            
            # Show existing env vars
            for i, (key, value) in enumerate(server.env.items()):
                col1, col2 = st.columns(2)
                with col1:
                    env_key = st.text_input(f"Env Key {i+1}", value=key, key=f"env_key_{name}_{i}")
                with col2:
                    env_value = st.text_input(f"Env Value {i+1}", value=value, key=f"env_value_{name}_{i}", type="password" if any(secret in key.lower() for secret in ['key', 'token', 'secret', 'password']) else "default")
                if env_key:
                    env_vars[env_key] = env_value
            
            # Add new env var
            col1, col2 = st.columns(2)
            with col1:
                new_env_key = st.text_input("New Env Key", key=f"new_env_key_{name}")
            with col2:
                new_env_value = st.text_input("New Env Value", key=f"new_env_value_{name}")
            
            if new_env_key:
                env_vars[new_env_key] = new_env_value
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Save Changes", type="primary"):
                    updated_server = MCPServerConfig(
                        name=new_name,
                        command=command,
                        args=args_text.split() if args_text else [],
                        env=env_vars,
                        transport=MCPTransportType(transport),
                        url=url if url else None,
                        enabled=server.enabled,
                        description=description if description else None
                    )
                    
                    # Remove old server if name changed
                    if new_name != name:
                        mcp_manager.remove_server(name)
                    
                    mcp_manager.add_server(updated_server)
                    del st.session_state[f"edit_server_{name}"]
                    st.success("Server updated successfully!")
                    st.rerun()
            
            with col2:
                if st.form_submit_button("Cancel"):
                    del st.session_state[f"edit_server_{name}"]
                    st.rerun()
    
    @staticmethod
    def _render_add_server(mcp_manager: MCPConfigManager) -> None:
        """Render add server form"""
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### Add from Template")
            template_name = st.selectbox(
                "Choose Template",
                options=[""] + list(MCP_SERVER_TEMPLATES.keys()),
                format_func=lambda x: "Select a template..." if x == "" else MCP_SERVER_TEMPLATES[x]["name"] if x else ""
            )
            
            if template_name:
                template = MCP_SERVER_TEMPLATES[template_name]
                st.markdown(f"**{template['name']}**")
                st.markdown(template['description'])
                
                if template['env_vars']:
                    st.markdown("**Required Environment Variables:**")
                    for var, desc in template['env_vars'].items():
                        st.code(f"{var}: {desc}")
                
                if st.button("Use This Template", key=f"use_template_{template_name}"):
                    st.session_state.selected_template = template_name
                    st.rerun()
        
        with col2:
            st.markdown("### Manual Configuration")
            if st.button("Create Custom Server"):
                st.session_state.show_custom_form = True
                st.rerun()
        
        # Show template form
        if st.session_state.get('selected_template'):
            MCPUIComponents._render_template_form(mcp_manager, st.session_state.selected_template)
        
        # Show custom form
        if st.session_state.get('show_custom_form'):
            MCPUIComponents._render_custom_form(mcp_manager)
    
    @staticmethod
    def _render_template_form(mcp_manager: MCPConfigManager, template_name: str) -> None:
        """Render form for template-based server creation"""
        template = MCP_SERVER_TEMPLATES[template_name]
        
        st.markdown("---")
        st.markdown(f"### Configure {template['name']}")
        
        with st.form(f"template_form_{template_name}"):
            server_name = st.text_input("Server Name", value=template_name)
            description = st.text_input("Description", value=template['description'])
            
            # Environment variables
            env_vars = {}
            if template['env_vars']:
                st.markdown("**Environment Variables**")
                for var, desc in template['env_vars'].items():
                    value = st.text_input(
                        var,
                        help=desc,
                        type="password" if any(secret in var.lower() for secret in ['key', 'token', 'secret', 'password']) else "default"
                    )
                    if value:
                        env_vars[var] = value
            
            # Additional arguments
            additional_args = st.text_input("Additional Arguments", help="Space-separated additional arguments")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Add Server", type="primary"):
                    args = template['args'].copy()
                    if additional_args:
                        args.extend(additional_args.split())
                    
                    server = MCPServerConfig(
                        name=server_name,
                        command=template['command'],
                        args=args,
                        env=env_vars,
                        description=description,
                        enabled=True
                    )
                    
                    errors = mcp_manager.validate_server_config(server)
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        mcp_manager.add_server(server)
                        del st.session_state.selected_template
                        st.success(f"Added {server_name} server!")
                        st.rerun()
            
            with col2:
                if st.form_submit_button("Cancel"):
                    del st.session_state.selected_template
                    st.rerun()
    
    @staticmethod
    def _render_custom_form(mcp_manager: MCPConfigManager) -> None:
        """Render form for custom server creation"""
        st.markdown("---")
        st.markdown("### Custom Server Configuration")
        
        # Environment variable management outside the form
        if 'custom_env_count' not in st.session_state:
            st.session_state.custom_env_count = 1
        
        # Environment variables section (outside form for dynamic buttons)
        st.markdown("**Environment Variables**")
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("Configure environment variables for your server:")
        with col2:
            if st.button("➕ Add Variable", key="add_env_var"):
                st.session_state.custom_env_count += 1
                st.rerun()
        
        # Environment variable inputs
        env_vars = {}
        for i in range(st.session_state.custom_env_count):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                key = st.text_input(f"Key", key=f"custom_env_key_{i}", placeholder="ENV_VAR_NAME")
            with col2:
                value = st.text_input(
                    f"Value", 
                    key=f"custom_env_value_{i}", 
                    type="password" if key and any(secret in key.lower() for secret in ['key', 'token', 'secret', 'password']) else "default",
                    placeholder="env_var_value"
                )
            with col3:
                if st.button("🗑️", key=f"remove_env_{i}", help="Remove this variable") and st.session_state.custom_env_count > 1:
                    st.session_state.custom_env_count -= 1
                    st.rerun()
            
            if key and value:
                env_vars[key] = value
        
        # Main server configuration form
        with st.form("custom_server_form"):
            name = st.text_input("Server Name", help="Unique identifier for this server")
            description = st.text_input("Description", help="Optional description")
            command = st.text_input("Command", help="Executable command (e.g., 'npx', 'python', 'node')")
            args_text = st.text_input("Arguments", help="Space-separated command arguments")
            
            transport = st.selectbox(
                "Transport Type",
                options=[t.value for t in MCPTransportType],
                help="Communication method with the server"
            )
            
            url = st.text_input("URL", help="Required for HTTP transport")
            
            # Display current environment variables (read-only in form)
            if env_vars:
                st.markdown("**Current Environment Variables:**")
                for key, value in env_vars.items():
                    masked_value = "***" if any(secret in key.lower() for secret in ['key', 'token', 'secret', 'password']) else value
                    st.code(f"{key}={masked_value}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Add Server", type="primary"):
                    server = MCPServerConfig(
                        name=name,
                        command=command,
                        args=args_text.split() if args_text else [],
                        env=env_vars,
                        transport=MCPTransportType(transport),
                        url=url if url else None,
                        description=description if description else None,
                        enabled=True
                    )
                    
                    errors = mcp_manager.validate_server_config(server)
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        mcp_manager.add_server(server)
                        del st.session_state.show_custom_form
                        st.session_state.custom_env_count = 1
                        st.success(f"Added {name} server!")
                        st.rerun()
            
            with col2:
                if st.form_submit_button("Cancel"):
                    del st.session_state.show_custom_form
                    st.session_state.custom_env_count = 1
                    st.rerun()
    
    @staticmethod
    def _render_import_export(mcp_manager: MCPConfigManager) -> None:
        """Render import/export functionality"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Export Configuration")
            if st.button("📤 Export All Servers"):
                config_json = mcp_manager.export_config()
                st.download_button(
                    label="Download mcp_config.json",
                    data=config_json,
                    file_name="mcp_config.json",
                    mime="application/json"
                )
                st.text_area("Configuration JSON:", value=config_json, height=200)
        
        with col2:
            st.markdown("### Import Configuration")
            uploaded_file = st.file_uploader("Choose configuration file", type=['json'])
            
            if uploaded_file:
                try:
                    config_data = uploaded_file.read().decode('utf-8')
                    if st.button("Import Configuration"):
                        if mcp_manager.import_config(config_data):
                            st.success("Configuration imported successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to import configuration. Please check the file format.")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
            
            st.markdown("Or paste configuration JSON:")
            json_input = st.text_area("Paste JSON here:", height=200)
            if json_input and st.button("Import from Text"):
                if mcp_manager.import_config(json_input):
                    st.success("Configuration imported successfully!")
                    st.rerun()
                else:
                    st.error("Failed to import configuration. Please check the JSON format.")
    
    @staticmethod
    def _render_mcp_info() -> None:
        """Render information about MCP"""
        st.markdown("### About Model Context Protocol (MCP)")
        
        # Create tabs for different types of information
        info_tab1, info_tab2, info_tab3, info_tab4 = st.tabs(["📖 Overview", "🚀 Quick Start", "💡 Examples", "🔗 Resources"])
        
        with info_tab1:
            st.markdown("""
            The Model Context Protocol (MCP) is an open standard that enables AI applications to securely connect with external data sources and tools.
            
            #### Key Benefits:
            - **🔒 Secure Integration**: Safe connections between AI and external resources
            - **📋 Standardized Protocol**: Open standard for consistent integrations
            - **🔧 Extensible**: Support for custom servers and tools
            - **⚡ Real-time Data**: Access to live data and dynamic content
            
            #### Available Server Types:
            - **📁 Filesystem**: Access local files and directories
            - **🔍 Web Search**: Search capabilities via Brave Search API
            - **🐙 GitHub**: Repository and issue management
            - **🗄️ Database**: PostgreSQL and SQLite connections
            - **☁️ Google Drive**: Cloud file access
            - **⚙️ Custom**: Build your own servers
            
            #### How It Works:
            1. **Servers** provide tools and resources (like APIs)
            2. **AI Assistant** discovers available capabilities automatically
            3. **Users** interact naturally - AI uses appropriate servers
            4. **Results** are integrated seamlessly into conversations
            """)
        
        with info_tab2:
            st.markdown("""
            ### 🚀 Quick Start Guide
            
            #### Step 1: Choose Your First Server
            **Recommended for beginners:** Filesystem Server
            - Easy to set up (no API keys needed)
            - Immediate practical value
            - Safe to experiment with
            
            #### Step 2: Set Up the Server
            ```bash
            # Run the setup script
            ./setup_examples/setup_filesystem_server.sh
            ```
            
            #### Step 3: Configure in HemPa Mitra
            1. Go to "Add Server" tab
            2. Select "Filesystem Server" template
            3. Set the directory path (e.g., your Documents folder)
            4. Click "Add Server"
            
            #### Step 4: Test It Out
            Try these chat prompts:
            - "List files in my Documents folder"
            - "Show me the contents of my README file"
            - "Create a new file called test.txt"
            
            #### Step 5: Add More Servers
            Once comfortable, try:
            - **Web Search** (needs Brave API key)
            - **GitHub** (needs personal access token)
            - **Weather Demo** (no setup required)
            """)
        
        with info_tab3:
            st.markdown("""
            ### 💡 Practical Examples
            
            #### 📁 Filesystem Server Examples
            ```
            User: "What files do I have in my project folder?"
            AI: *Lists all files and folders with details*
            
            User: "Show me my TODO list"
            AI: *Reads and displays todo.txt content*
            
            User: "Create a meeting notes file for today"
            AI: *Creates file with current date and basic structure*
            ```
            
            #### 🔍 Web Search Examples
            ```
            User: "What's the latest news about renewable energy?"
            AI: *Searches web and provides current information*
            
            User: "Find Python tutorials for machine learning"
            AI: *Searches and summarizes relevant tutorials*
            ```
            
            #### 🐙 GitHub Examples
            ```
            User: "What are my open issues?"
            AI: *Lists GitHub issues with priorities and labels*
            
            User: "Show recent commits on main branch"
            AI: *Displays recent commit history with messages*
            
            User: "Create an issue for the bug I found"
            AI: *Creates GitHub issue based on your description*
            ```
            
            #### 🗄️ Database Examples
            ```
            User: "How many users registered this month?"
            AI: *Queries database and provides count with insights*
            
            User: "Show me top selling products"
            AI: *Runs analytics query and formats results*
            ```
            
            #### 🌤️ Weather Demo Examples
            ```
            User: "What's the weather like in London?"
            AI: *Provides current weather with temperature and conditions*
            
            User: "Give me a 5-day forecast for Tokyo"
            AI: *Shows detailed weather forecast*
            ```
            """)
        
        with info_tab4:
            st.markdown("""
            ### 🔗 Resources and Links
            
            #### Official Documentation
            - [MCP Documentation](https://modelcontextprotocol.io/) - Official specification and guides
            - [Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Build custom servers
            - [Server Repository](https://github.com/modelcontextprotocol/servers) - Pre-built servers
            
            #### Setup Files in This Project
            - `MCP_USAGE_EXAMPLES.md` - Comprehensive usage guide
            
            #### API Keys and Credentials
            - [Brave Search API](https://brave.com/search/api) - For web search
            - [GitHub Tokens](https://github.com/settings/tokens) - For GitHub integration
            - [Google Cloud Console](https://console.cloud.google.com/) - For Google Drive
            - [OpenWeatherMap](https://openweathermap.org/api) - For real weather data
            
            #### Troubleshooting
            **Common Issues:**
            - **Node.js not installed**: Install from [nodejs.org](https://nodejs.org/)
            - **Permission denied**: Check file/directory permissions
            - **API key invalid**: Verify key is correct and has proper scopes
            - **Server won't start**: Check environment variables and paths
            
            **Debug Commands:**
            ```bash
            # Test MCP installation
            pip install mcp[cli]
            
            # Test a server manually
            npx -y @modelcontextprotocol/server-filesystem /tmp
            
            # Check Node.js version
            node --version
            ```
            """)
        
        # Add quick action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📁 Try Filesystem Server", help="Quick setup for filesystem access"):
                st.session_state.selected_template = 'filesystem'
                st.rerun()
        
        with col2:
            if st.button("🌤️ Try Weather Demo", help="Demo server with no setup required"):
                st.session_state.selected_template = 'custom'
                st.session_state.demo_weather = True
                st.rerun()
        
        with col3:
            if st.button("📋 View All Templates", help="Go to Add Server tab"):
                st.session_state.mcp_active_tab = 1  # Add Server tab
                st.rerun()