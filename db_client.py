#!/usr/bin/env python3
"""
Database Client - Client for interacting with pysonDB
"""

import logging
from typing import List, Dict, Any
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class PysonDBClient:
    """Database client using pysonDB for local JSON database"""
    
    def __init__(self, db_path: str = None):
        """Initialize pysonDB client"""
        if db_path is None:
            # Use data directory if it exists, otherwise current directory
            if os.path.exists('data'):
                db_path = 'data/monitoring_config.json'
            else:
                db_path = 'monitoring_config.json'
        
        self.db_path = db_path
        self._ensure_db_dir()
        
        # Initialize pysonDB
        try:
            from pysondb import db
            self.db = db.getDb(self.db_path)
            logger.info(f"Initialized pysonDB at: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize pysonDB: {e}")
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
            self.db.getAll()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_monitored_channels(self) -> List[int]:
        """Get list of monitored channel IDs"""
        try:
            # Look for monitoring configuration
            configs = self.db.getByQuery({"type": "monitoring_channels"})
            
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
            existing_configs = self.db.getByQuery({"type": "monitoring_channels"})
            for config in existing_configs:
                self.db.deleteById(config['id'])
            
            # Add new configuration
            config_data = {
                "type": "monitoring_channels",
                "channels": channels,
                "updated_at": datetime.now().isoformat(),
                "updated_by": user
            }
            
            self.db.add(config_data)
            logger.info(f"Successfully saved {len(channels)} monitored channels to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set monitored channels: {e}")
            return False
    
    def clear_monitored_channels(self) -> bool:
        """Clear all monitored channels"""
        try:
            # Remove all monitoring configurations
            existing_configs = self.db.getByQuery({"type": "monitoring_channels"})
            for config in existing_configs:
                self.db.deleteById(config['id'])
            
            logger.info("Successfully cleared all monitored channels from database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear monitored channels: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration data"""
        try:
            all_data = self.db.getAll()
            return {"configurations": all_data}
        except Exception as e:
            logger.error(f"Failed to get all config: {e}")
            return {}
    
    def add_channel_info(self, channel_id: int, channel_title: str, channel_username: str = None) -> bool:
        """Add or update channel information"""
        try:
            # Remove existing channel info if it exists
            existing_info = self.db.getByQuery({"type": "channel_info", "channel_id": channel_id})
            for info in existing_info:
                self.db.deleteById(info['id'])
            
            # Add new channel info
            channel_data = {
                "type": "channel_info",
                "channel_id": channel_id,
                "channel_title": channel_title,
                "channel_username": channel_username,
                "updated_at": datetime.now().isoformat()
            }
            
            self.db.add(channel_data)
            logger.info(f"Added channel info for: {channel_title} ({channel_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add channel info: {e}")
            return False
    
    def get_channel_info(self, channel_id: int) -> Dict[str, Any]:
        """Get channel information by ID"""
        try:
            channel_info = self.db.getByQuery({"type": "channel_info", "channel_id": channel_id})
            if channel_info:
                return channel_info[0]
            return {}
        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")
            return {}

def get_db_client() -> PysonDBClient:
    """Get database client instance"""
    try:
        return PysonDBClient()
    except Exception as e:
        logger.error(f"Failed to create database client: {e}")
        # Fallback to a simple implementation if pysonDB fails
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
