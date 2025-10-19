#!/usr/bin/env python3
"""
Database Client - Client for interacting with TinyDB
"""

from typing import List, Dict, Any
import os
from datetime import datetime
from news_reader.logging_config import get_logger
from news_reader.message_utils import get_current_timestamp

logger = get_logger(__name__)

class TinyDBClient:
    """Database client using TinyDB for local JSON database"""
    
    def __init__(self, db_path: str = None):
        """Initialize TinyDB client"""
        if db_path is None:
            # Use data directory if it exists, otherwise current directory
            if os.path.exists('data'):
                db_path = 'data/monitoring_config.json'
            else:
                db_path = 'monitoring_config.json'
        
        self.db_path = db_path
        self._ensure_db_dir()
        
        # Initialize TinyDB
        try:
            from tinydb import TinyDB, Query
            self.db = TinyDB(self.db_path)
            self.Query = Query()  # Create Query instance
            logger.info(f"Initialized TinyDB at: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize TinyDB: {e}")
            raise
    
    def _ensure_db_dir(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            # Try to read from database
            self.db.all()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_monitored_channels(self) -> List[int]:
        """Get list of monitored channel IDs"""
        try:
            # Look for monitoring configuration
            configs = self.db.search(self.Query.type == "monitoring_channels")
            
            if configs:
                # Get the most recent configuration
                latest_config = max(configs, key=lambda x: x.get('updated_at', ''))
                channels = latest_config.get('channels', [])
                logger.info(f"Retrieved {len(channels)} monitored channels from database")
                return channels
            else:
                logger.info("No monitoring channels configuration found in database")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get monitored channels: {e}")
            return []
    
    def set_monitored_channels(self, channels: List[int], user: str = 'system') -> bool:
        """Set monitored channel IDs"""
        try:
            # Remove existing monitoring configurations
            self.db.remove(self.Query.type == "monitoring_channels")
            
            # Add new configuration
            config_data = {
                "type": "monitoring_channels",
                "channels": channels,
                "updated_at": get_current_timestamp(),
                "updated_by": user
            }
            
            self.db.insert(config_data)
            logger.info(f"Successfully saved {len(channels)} monitored channels to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set monitored channels: {e}")
            return False
    
    def clear_monitored_channels(self) -> bool:
        """Clear all monitored channels"""
        try:
            # Remove all monitoring configurations
            self.db.remove(self.Query.type == "monitoring_channels")
            
            logger.info("Successfully cleared all monitored channels from database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear monitored channels: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration data"""
        try:
            all_data = self.db.all()
            return {"configurations": all_data}
        except Exception as e:
            logger.error(f"Failed to get all config: {e}")
            return {}
    
    def add_channel_info(self, channel_id: int, channel_title: str, channel_username: str = None) -> bool:
        """Add or update channel information"""
        try:
            # Remove existing channel info if it exists
            self.db.remove((self.Query.type == "channel_info") & (self.Query.channel_id == channel_id))
            
            # Add new channel info
            channel_data = {
                "type": "channel_info",
                "channel_id": channel_id,
                "channel_title": channel_title,
                "channel_username": channel_username,
                "updated_at": datetime.now().isoformat()
            }
            
            self.db.insert(channel_data)
            logger.info(f"Added channel info for: {channel_title} ({channel_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add channel info: {e}")
            return False
    
    def get_channel_info(self, channel_id: int) -> Dict[str, Any]:
        """Get channel information by ID"""
        try:
            channel_info = self.db.search((self.Query.type == "channel_info") & (self.Query.channel_id == channel_id))
            if channel_info:
                return channel_info[0]
            return {}
        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")
            return {}
    
    def cache_channels_list(self, channels: List[Dict[str, Any]], user: str = 'system') -> bool:
        """Cache the complete channels list"""
        try:
            # Remove existing cached channels
            self.db.remove(self.Query.type == "cached_channels")
            
            # Add new cached channels
            cache_data = {
                "type": "cached_channels",
                "channels": channels,
                "cached_at": get_current_timestamp(),
                "cached_by": user
            }
            
            self.db.insert(cache_data)
            logger.info(f"Successfully cached {len(channels)} channels to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache channels list: {e}")
            return False
    
    def get_cached_channels(self) -> List[Dict[str, Any]]:
        """Get cached channels list"""
        try:
            # Look for cached channels
            cached_data = self.db.search(self.Query.type == "cached_channels")
            
            if cached_data:
                # Get the most recent cache
                latest_cache = max(cached_data, key=lambda x: x.get('cached_at', ''))
                channels = latest_cache.get('channels', [])
                cached_at = latest_cache.get('cached_at', 'Unknown')
                logger.info(f"Retrieved {len(channels)} cached channels from database (cached at: {cached_at})")
                return channels
            else:
                logger.info("No cached channels found in database")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get cached channels: {e}")
            return []
    
    def clear_cached_channels(self) -> bool:
        """Clear cached channels"""
        try:
            # Remove all cached channels
            self.db.remove(self.Query.type == "cached_channels")
            
            logger.info("Successfully cleared cached channels from database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cached channels: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cached channels"""
        try:
            cached_data = self.db.search(self.Query.type == "cached_channels")
            
            if cached_data:
                latest_cache = max(cached_data, key=lambda x: x.get('cached_at', ''))
                return {
                    "has_cache": True,
                    "channels_count": len(latest_cache.get('channels', [])),
                    "cached_at": latest_cache.get('cached_at', 'Unknown'),
                    "cached_by": latest_cache.get('cached_by', 'Unknown')
                }
            else:
                return {"has_cache": False}
                
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {"has_cache": False}
    
    def save_incoming_message(self, message_data: Dict[str, Any]) -> bool:
        """Save an incoming message to the database"""
        try:
            message_record = {
                "type": "incoming_message",
                "message_id": message_data.get('message_id'),
                "chat_id": message_data.get('chat_id'),
                "chat_name": message_data.get('chat_name'),
                "sender_id": message_data.get('sender_id'),
                "sender_name": message_data.get('sender_name'),
                "message_text": message_data.get('message_text'),
                "timestamp": message_data.get('timestamp'),
                "message_link": message_data.get('message_link'),  # Store message link
                "received_at": get_current_timestamp(),
                "llm_summary": message_data.get('llm_summary'),  # Store LLM summary
                "summary_generated_at": message_data.get('summary_generated_at')  # When summary was created
            }
            
            self.db.insert(message_record)
            logger.debug(f"Saved incoming message from {message_data.get('sender_name')} in {message_data.get('chat_name')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save incoming message: {e}")
            return False
    
    def get_all_incoming_messages(self) -> List[Dict[str, Any]]:
        """Get all incoming messages from the database"""
        try:
            messages = self.db.search(self.Query.type == "incoming_message")
            logger.info(f"Retrieved {len(messages)} incoming messages from database")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get incoming messages: {e}")
            return []
    
    def clear_incoming_messages(self) -> bool:
        """Clear all incoming messages from the database"""
        try:
            removed_count = len(self.db.search(self.Query.type == "incoming_message"))
            self.db.remove(self.Query.type == "incoming_message")
            logger.info(f"Successfully cleared {removed_count} incoming messages from database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear incoming messages: {e}")
            return False
    
    def update_message_summary(self, message_id: int, summary: str) -> bool:
        """Update a message with its LLM-generated summary"""
        try:
            # Find and update the message
            updated = self.db.update(
                {
                    'llm_summary': summary,
                    'summary_generated_at': get_current_timestamp()
                },
                (self.Query.type == "incoming_message") & 
                (self.Query.message_id == message_id)
            )
            
            if updated:
                logger.debug(f"Updated message {message_id} with LLM summary")
                return True
            else:
                logger.warning(f"No message found with ID {message_id} to update")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update message summary: {e}")
            return False
    
    def get_messages_without_summary(self) -> List[Dict[str, Any]]:
        """Get all incoming messages that don't have LLM summaries yet"""
        try:
            messages = self.db.search(
                (self.Query.type == "incoming_message") & 
                (~self.Query.llm_summary.exists() | (self.Query.llm_summary == None))
            )
            logger.info(f"Found {len(messages)} messages without summaries")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages without summaries: {e}")
            return []

def get_db_client() -> TinyDBClient:
    """Get database client instance"""
    try:
        return TinyDBClient()
    except Exception as e:
        logger.error(f"Failed to create database client: {e}")
        logger.error("Database is required for the application to function properly")
        raise RuntimeError(f"Cannot initialize database client: {e}. The application cannot work without a database.")
