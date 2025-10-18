import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram API credentials
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')
    PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
    SESSION_NAME = os.getenv('SESSION_NAME', '')
    
    # OpenAI API configuration
    LLM_API_KEY = os.getenv('LLM_API_KEY', '')  # OpenAI API key
    LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo')  # OpenAI model name
    LLM_ENDPOINT_URL = os.getenv('LLM_ENDPOINT_URL', '')  # Optional: Custom base URL for OpenAI-compatible APIs
    
    # Channel configuration
    SINK_CHANNEL = int(os.getenv('SINK_CHANNEL', ''))  # Channel ID or username to send summaries to
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.API_ID or cls.API_ID == 0:
            raise ValueError("API_ID is required")
        if not cls.API_HASH:
            raise ValueError("API_HASH is required")
        if not cls.PHONE_NUMBER:
            raise ValueError("PHONE_NUMBER is required")
        return True
