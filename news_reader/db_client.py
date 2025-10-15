#!/usr/bin/env python3
"""
Database Client - Client for interacting with TinyDB
"""

import logging
from typing import List, Dict, Any
import os
from datetime import datetime

logger = logging.getLogger(__name__)

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
                "updated_at": datetime.now().isoformat(),
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
                "cached_at": datetime.now().isoformat(),
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

def get_db_client() -> TinyDBClient:
    """Get database client instance"""
    try:
        return TinyDBClient()
    except Exception as e:
        logger.error(f"Failed to create database client: {e}")
        # Fallback to a simple implementation if TinyDB fails
        return SimpleFallbackClient()

class SimpleFallbackClient:
    """Simple fallback client using JSON file if pysonDB fails"""
    
    def __init__(self, file_path: str = 'monitoring_config_fallback.json'):
        self.file_path = file_path
    
    def health_check(self) -> bool:
        return True
    
    def get_monitored_channels(self) -> List[int]:
        try:
            import json
            if not os.path.exists(self.file_path):
                return []
            
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            
            return data.get('monitored_channels', [])
        except Exception as e:
            logger.error(f"Fallback: Failed to read file: {e}")
            return []
    
    def set_monitored_channels(self, channels: List[int], user: str = 'system') -> bool:
        try:
            import json
            data = {
                'monitored_channels': channels,
                'updated_at': datetime.now().isoformat(),
                'updated_by': user
            }
            
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Fallback: Saved {len(channels)} channels")
            return True
        except Exception as e:
            logger.error(f"Fallback: Failed to write file: {e}")
            return False
    
    def clear_monitored_channels(self) -> bool:
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            return True
        except Exception as e:
            logger.error(f"Fallback: Failed to clear file: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        return {}
    
    def add_channel_info(self, channel_id: int, channel_title: str, channel_username: str = None) -> bool:
        return True
    
    def get_channel_info(self, channel_id: int) -> Dict[str, Any]:
        return {}
    
    def cache_channels_list(self, channels: List[Dict[str, Any]], user: str = 'system') -> bool:
        return True
    
    def get_cached_channels(self) -> List[Dict[str, Any]]:
        return []
    
    def clear_cached_channels(self) -> bool:
        return True
    
    def get_cache_info(self) -> Dict[str, Any]:
        return {"has_cache": False}
