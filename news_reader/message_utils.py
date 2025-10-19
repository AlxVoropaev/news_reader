#!/usr/bin/env python3
"""
Message Utilities - Common message data handling functions
"""

from typing import Dict, Any
from datetime import datetime

def extract_message_metadata(message_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract common message metadata with consistent defaults
    
    Args:
        message_data: Dictionary containing message information
    
    Returns:
        Dictionary with standardized message metadata
    """
    return {
        'chat_name': message_data.get('chat_name', 'Unknown Channel'),
        'sender_name': message_data.get('sender_name', 'Unknown Sender'),
        'timestamp': message_data.get('timestamp', 'Unknown Time'),
        'message_link': message_data.get('message_link', '')
    }

def get_sender_name(message_data: Dict[str, Any]) -> str:
    """Get sender name with consistent default"""
    return message_data.get('sender_name', 'Unknown')

def get_chat_name(message_data: Dict[str, Any]) -> str:
    """Get chat name with consistent default"""
    return message_data.get('chat_name', 'Unknown')

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()

def format_message_for_display(text: str, max_length: int = 200) -> str:
    """
    Format message text for display with length limit
    
    Args:
        text: Original message text
        max_length: Maximum length before truncation
    
    Returns:
        Formatted message text
    """
    if not text:
        return '[No text]'
    
    if len(text) > max_length:
        return text[:max_length] + '...'
    
    return text

def create_telegram_message_link(chat_id: int, message_id: int) -> str:
    """
    Create Telegram message link for channels
    
    Args:
        chat_id: Channel ID
        message_id: Message ID
    
    Returns:
        Formatted Telegram message link
    """
    # Remove the -100 prefix from channel IDs for the link
    chat_id_for_link = str(chat_id)[4:] if str(chat_id).startswith('-100') else str(chat_id)
    return f"https://t.me/c/{chat_id_for_link}/{message_id}"
