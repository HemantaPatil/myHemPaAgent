"""
Configuration settings for HemPa Mitra application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AppConfig:
    """Application configuration settings"""
    
    # App Info
    APP_NAME = "HemPa Mitra"
    APP_ICON = "🐶"
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Model Options
    MODEL_OPTIONS = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
    DEFAULT_MODEL = "gpt-3.5-turbo"
    
    # Text Processing (for chat responses)
    CONTEXT_LENGTH = 1000
    
    # UI Settings
    LOGO_WIDTH_SIDEBAR = 120
    LOGO_WIDTH_MAIN = 80
    CHAT_INPUT_PLACEHOLDER = "Message HemPa Mitra..."
    
    # Analytics
    WORD_FREQUENCY_LIMIT = 10
    READABILITY_METRICS_ENABLED = True
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        return True

class UIConfig:
    """UI-specific configuration"""
    
    # CSS Styles
    MAIN_HEADER_STYLE = """
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1a1a1a;
        text-align: center;
        margin-bottom: 1rem;
    }
    """
    
    CHAT_CONTAINER_STYLE = """
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e5e5e5;
        border-radius: 10px;
        background-color: #f9f9f9;
    }
    """
    
    USER_MESSAGE_STYLE = """
    .user-message {
        background-color: #007aff;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 18px;
        margin: 0.5rem 0;
        margin-left: 20%;
        text-align: right;
    }
    """
    
    ASSISTANT_MESSAGE_STYLE = """
    .assistant-message {
        background-color: #f1f1f1;
        color: #1a1a1a;
        padding: 0.5rem 1rem;
        border-radius: 18px;
        margin: 0.5rem 0;
        margin-right: 20%;
    }
    """
    
    SIDEBAR_SECTION_STYLE = """
    .sidebar-section {
        margin-bottom: 2rem;
    }
    """
    
    LOGO_CIRCLE_STYLE = """
    .logo-circle {
        border-radius: 50%;
        border: 3px solid #007aff;
        padding: 5px;
        display: block;
        margin: 0 auto;
    }
    """
    
    @classmethod
    def get_all_styles(cls):
        """Get combined CSS styles"""
        return f"""
        <style>
        {cls.MAIN_HEADER_STYLE}
        {cls.CHAT_CONTAINER_STYLE}
        {cls.USER_MESSAGE_STYLE}
        {cls.ASSISTANT_MESSAGE_STYLE}
        {cls.SIDEBAR_SECTION_STYLE}
        {cls.LOGO_CIRCLE_STYLE}
        </style>
        """