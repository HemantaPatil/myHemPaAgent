"""
UI components for the HemPa Mitra application
"""
import streamlit as st
import base64
from typing import Optional, List, Dict, Any

class UIComponents:
    """Reusable UI components"""
    
    @staticmethod
    def render_logo(image_path: str, width: int, is_circular: bool = True) -> None:
        """
        Render logo image
        
        Args:
            image_path: Path to the logo image
            width: Width of the image
            is_circular: Whether to make the image circular
        """
        try:
            with open(image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
            
            border_style = "border-radius: 50%; border: 3px solid #007aff;" if is_circular else ""
            
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 1rem;">
                <img src="data:image/jpeg;base64,{img_data}" 
                     style="{border_style} 
                            width: {width}px; 
                            height: {width}px; 
                            object-fit: cover;">
            </div>
            """, unsafe_allow_html=True)
        except FileNotFoundError:
            st.info(f"Logo image not found at {image_path}")
        except Exception as e:
            st.error(f"Error loading logo: {str(e)}")
    
    @staticmethod
    def render_header_with_logo(app_name: str, logo_path: str, logo_width: int = 80) -> None:
        """Render application header with logo"""
        try:
            with open(logo_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <img src="data:image/jpeg;base64,{img_data}" 
                     style="border-radius: 50%; 
                            border: 3px solid #007aff; 
                            width: {logo_width}px; 
                            height: {logo_width}px; 
                            object-fit: cover; 
                            margin-right: 1rem;">
                <h1 style="font-size: 2.5rem; font-weight: 600; color: #1a1a1a; margin: 0;">{app_name}</h1>
            </div>
            """, unsafe_allow_html=True)
        except:
            # Fallback without logo
            st.markdown(f'<h1 class="main-header">{app_name}</h1>', unsafe_allow_html=True)
    
    @staticmethod
    def render_chat_message(role: str, content: str, avatar: str = None) -> None:
        """Render a chat message"""
        if role == "user":
            st.markdown(f"""
            <div class="user-message">
                👤 {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-message">
                🤖 {content}
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_welcome_message(app_name: str) -> None:
        """Render welcome message"""
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; color: #666;">
            <h3>Hello! I'm {app_name}</h3>
            <p>I can help you with questions, data analysis, and more!</p>
            <p>Let's start chatting!</p>
        </div>
        """, unsafe_allow_html=True)
    
    
    @staticmethod
    def render_model_selector(current_model: str, model_options: List[str]) -> str:
        """Render model selection dropdown"""
        return st.selectbox(
            "Choose AI Model:",
            model_options,
            index=model_options.index(current_model) if current_model in model_options else 0
        )
    
    @staticmethod
    def render_chat_history(chat_history: List[Dict[str, Any]], max_display: int = 5) -> Optional[Dict[str, Any]]:
        """
        Render chat history sidebar
        
        Returns:
            Selected chat data if any chat is clicked
        """
        if not chat_history:
            st.info("No chat history yet")
            return None
        
        selected_chat = None
        
        # Show most recent chats
        recent_chats = chat_history[-max_display:] if len(chat_history) > max_display else chat_history
        
        for i, chat in enumerate(reversed(recent_chats), 1):
            chat_title = chat.get('title', 'Untitled')[:25] + ('...' if len(chat.get('title', '')) > 25 else '')
            
            if st.button(f"💬 {chat_title}", key=f"chat_{chat.get('id', i)}", use_container_width=True):
                selected_chat = chat
        
        return selected_chat
    
    @staticmethod
    def render_metrics_row(metrics: Dict[str, Any], columns: int = 4) -> None:
        """Render a row of metrics"""
        cols = st.columns(columns)
        
        for i, (label, value) in enumerate(metrics.items()):
            if i < len(cols):
                with cols[i]:
                    if isinstance(value, (int, float)):
                        if isinstance(value, float):
                            st.metric(label, f"{value:.2f}")
                        else:
                            st.metric(label, f"{value:,}")
                    else:
                        st.metric(label, str(value))
    
    @staticmethod
    def render_expandable_section(title: str, content: str, max_length: int = 200) -> None:
        """Render an expandable section for long content"""
        if len(content) <= max_length:
            st.write(content)
        else:
            preview = content[:max_length] + "..."
            st.write(preview)
            
            with st.expander("Show full content"):
                st.write(content)
    
    
    @staticmethod
    def render_error_message(message: str, error_type: str = "Error") -> None:
        """Render error message with icon"""
        st.error(f"❌ {error_type}: {message}")
    
    @staticmethod
    def render_success_message(message: str) -> None:
        """Render success message with icon"""
        st.success(f"✅ {message}")
    
    @staticmethod
    def render_info_message(message: str) -> None:
        """Render info message with icon"""
        st.info(f"ℹ️ {message}")