import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram API credentials
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')
    PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
    
    # MTProto server configuration
    MTPROTO_SERVER_IP = os.getenv('MTPROTO_SERVER_IP', '149.154.167.50')
    MTPROTO_SERVER_PORT = int(os.getenv('MTPROTO_SERVER_PORT', '443'))
    MTPROTO_PUBLIC_KEY = os.getenv('MTPROTO_PUBLIC_KEY', '')
    
    # Session settings - using StringSession (in-memory only, no disk storage)
    
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
