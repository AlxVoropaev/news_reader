#!/usr/bin/env python3
"""
Channel Sender Service - Handles sending messages to Telegram channels
"""

import asyncio
from typing import Optional, Union
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError, ChatWriteForbiddenError, FloodWaitError
from news_reader.logging_config import get_logger
from news_reader.config import Config
from telethon.utils import get_peer_id

logger = get_logger(__name__)

class ChannelSender:
    """Service for sending messages to Telegram channels"""
    
    def __init__(self, client: TelegramClient):
        """Initialize channel sender with Telegram client"""
        self.client = client
        self.sink_channel = Config.SINK_CHANNEL
        
    def is_configured(self) -> bool:
        """Check if SINK_CHANNEL is configured"""
        return True
    
    async def send_summary_to_sink_channel(self, summary: str, original_message_data: dict) -> bool:
        """
        Send a summary message to the configured SINK_CHANNEL
        
        Args:
            summary: The LLM-generated summary to send
            original_message_data: Dictionary containing original message information
                - chat_name: Name of the source channel/chat
                - sender_name: Name of the message sender
                - timestamp: When the message was received
                - message_text: Original message text (for reference)
        
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("SINK_CHANNEL not configured - skipping summary sending")
            return False
        
        if not self.client or not self.client.is_connected():
            logger.error("Telegram client not connected - cannot send summary")
            return False
        
        try:
            # Format the summary message
            formatted_message = self._format_summary_message(summary, original_message_data)
            
            # Send the message to SINK_CHANNEL
            await self.client.send_message(self.sink_channel, formatted_message)
            
            logger.info(f"Successfully sent summary to SINK_CHANNEL ({self.sink_channel})")
            return True
            
        except ChannelPrivateError:
            logger.error(f"Cannot send to SINK_CHANNEL ({self.sink_channel}): Channel is private or bot is not a member")
            return False
        except ChatWriteForbiddenError:
            logger.error(f"Cannot send to SINK_CHANNEL ({self.sink_channel}): No permission to write to this channel")
            return False
        except FloodWaitError as e:
            logger.warning(f"Rate limited when sending to SINK_CHANNEL: must wait {e.seconds} seconds")
            return False
        except Exception as e:
            logger.error(f"Failed to send summary to SINK_CHANNEL ({self.sink_channel}): {e}")
            return False
    
    async def forward_message_to_sink_channel(self, message_text: str, original_message_data: dict) -> bool:
        """
        Forward a message as-is to the configured SINK_CHANNEL
        
        Args:
            message_text: The original message text to forward
            original_message_data: Dictionary containing original message information
        
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("SINK_CHANNEL not configured - skipping message forwarding")
            return False
        
        if not self.client or not self.client.is_connected():
            logger.error("Telegram client not connected - cannot forward message")
            return False
        
        try:
            # Format the forwarded message
            formatted_message = self._format_forwarded_message(message_text, original_message_data)
            
            # Send the message to SINK_CHANNEL
            await self.client.send_message(self.sink_channel, formatted_message)
            
            logger.info(f"Successfully forwarded message to SINK_CHANNEL ({self.sink_channel})")
            return True
            
        except ChannelPrivateError:
            logger.error(f"Cannot forward to SINK_CHANNEL ({self.sink_channel}): Channel is private or bot is not a member")
            return False
        except ChatWriteForbiddenError:
            logger.error(f"Cannot forward to SINK_CHANNEL ({self.sink_channel}): No permission to write to this channel")
            return False
        except FloodWaitError as e:
            logger.warning(f"Rate limited when forwarding to SINK_CHANNEL: must wait {e.seconds} seconds")
            return False
        except Exception as e:
            logger.error(f"Failed to forward message to SINK_CHANNEL ({self.sink_channel}): {e}")
            return False
    
    def _format_summary_message(self, summary: str, original_message_data: dict) -> str:
        """
        Format the summary message for sending to SINK_CHANNEL
        
        Args:
            summary: The LLM-generated summary
            original_message_data: Original message metadata
        
        Returns:
            Formatted message string
        """
        chat_name = original_message_data.get('chat_name', 'Unknown Channel')
        sender_name = original_message_data.get('sender_name', 'Unknown Sender')
        timestamp = original_message_data.get('timestamp', 'Unknown Time')
        message_link = original_message_data.get('message_link', '')
        
        # Create a formatted summary message
        formatted_message = f"**Source:** {chat_name} \n\n{summary} \n\n [Original Message]({message_link})"

        return formatted_message
    
    def _format_forwarded_message(self, message_text: str, original_message_data: dict) -> str:
        """
        Format the forwarded message for sending to SINK_CHANNEL
        
        Args:
            message_text: The original message text
            original_message_data: Original message metadata
        
        Returns:
            Formatted message string
        """
        chat_name = original_message_data.get('chat_name', 'Unknown Channel')
        sender_name = original_message_data.get('sender_name', 'Unknown Sender')
        message_link = original_message_data.get('message_link', '')
        
        # Create a formatted forwarded message
        formatted_message = f"**Source:** {chat_name}\n\n{message_text}\n\n[Original Message]({message_link})"

        return formatted_message
    
    async def test_sink_channel_access(self) -> tuple[bool, str]:
        """
        Test if the bot can access and send messages to the SINK_CHANNEL
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_configured():
            return False, "SINK_CHANNEL not configured"
        
        if not self.client.is_connected():
            return False, "Telegram client not connected"
        
        try:
            # Try to get channel info
            # Convert sink_channel to proper TelegramPeer id
            entity = await self.client.get_entity(int(self.sink_channel))
            
            # Try to send a test message
            test_message = "🔧 Test message from News Reader Bot - SINK_CHANNEL is working!"
            await self.client.send_message(entity, test_message)
            
            return True, f"Successfully tested SINK_CHANNEL access: {getattr(entity, 'title', self.sink_channel)}"
            
        except ChannelPrivateError:
            return False, f"SINK_CHANNEL ({self.sink_channel}) is private or bot is not a member"
        except ChatWriteForbiddenError:
            return False, f"No permission to write to SINK_CHANNEL ({self.sink_channel})"
        except Exception as e:
            return False, f"Failed to access SINK_CHANNEL ({self.sink_channel}): {e}"


# Global instance
_channel_sender_instance: Optional[ChannelSender] = None

def get_channel_sender(client: Optional[TelegramClient] = None) -> Optional[ChannelSender]:
    """Get the global ChannelSender instance"""
    global _channel_sender_instance
    
    if client and (_channel_sender_instance is None or _channel_sender_instance.client != client):
        _channel_sender_instance = ChannelSender(client)
    
    return _channel_sender_instance
