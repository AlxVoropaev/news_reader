#!/usr/bin/env python3
"""
Telegram Monitor - Continuous monitoring service for incoming messages
"""

import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from config import Config
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramMonitor:
    def __init__(self):
        self.config = Config()
        self.client = None
        self.running = False
        self.monitored_channels = []
    
    def load_monitored_channels(self):
        """Load monitored channels from database"""
        try:
            from db_client import get_db_client
            
            db_client = get_db_client()
            channels = db_client.get_monitored_channels()
            
            if not channels:
                logger.warning("⚠️ No monitored channels configuration found. Run 'python news_reader.py setup-monitoring' first.")
                return []
            
            logger.info(f"📡 Loaded {len(channels)} monitored channels from database")
            return channels
            
        except Exception as e:
            logger.error(f"❌ Failed to load monitored channels: {e}")
            return []
    
    async def initialize(self):
        """Initialize the Telegram client"""
        try:
            self.config.validate()
            
            # Load monitored channels
            self.monitored_channels = self.load_monitored_channels()
            if not self.monitored_channels:
                print(f"{Fore.YELLOW}⚠️ No channels configured for monitoring.")
                print(f"{Fore.CYAN}💡 Run 'python news_reader.py setup-monitoring' to select channels.")
                return False
            
            self.client = TelegramClient(
                session=f"{self.config.SESSION_NAME}_monitor",
                api_id=self.config.API_ID,
                api_hash=self.config.API_HASH,
                device_model='Telegram Monitor',
                system_version='1.0',
                app_version='1.0'
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error("❌ Client not authorized. Please run the main client first to authorize.")
                return False
            
            logger.info("✅ Monitor initialized successfully!")
            print(f"{Fore.GREEN}📺 Monitoring {len(self.monitored_channels)} channels")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize monitor: {e}")
            return False
    
    async def start_monitoring(self):
        """Start monitoring for new messages"""
        if not await self.initialize():
            return
        
        self.running = True
        
        # Register event handlers
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                chat = await event.get_chat()
                
                # Check if message is from a monitored channel
                if hasattr(chat, 'id') and chat.id not in self.monitored_channels:
                    return  # Skip messages from non-monitored channels
                
                sender = await event.get_sender()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sender_name = getattr(sender, 'first_name', 'Unknown') or 'Unknown'
                chat_name = getattr(chat, 'title', getattr(chat, 'first_name', 'Private'))
                
                print(f"\n{Fore.CYAN}📨 [{timestamp}] New message")
                print(f"{Fore.YELLOW}👤 From: {sender_name}")
                print(f"{Fore.BLUE}💬 Chat: {chat_name} (ID: {chat.id})")
                print(f"{Fore.WHITE}📝 Message: {event.text[:200]}{'...' if len(event.text) > 200 else ''}")
                print("-" * 60)
                
            except Exception as e:
                logger.error(f"❌ Error handling message: {e}")
        
        @self.client.on(events.MessageEdited)
        async def handle_edited_message(event):
            try:
                chat = await event.get_chat()
                
                # Check if message is from a monitored channel
                if hasattr(chat, 'id') and chat.id not in self.monitored_channels:
                    return  # Skip messages from non-monitored channels
                
                sender = await event.get_sender()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sender_name = getattr(sender, 'first_name', 'Unknown') or 'Unknown'
                chat_name = getattr(chat, 'title', getattr(chat, 'first_name', 'Private'))
                
                print(f"\n{Fore.MAGENTA}✏️ [{timestamp}] Message edited by {sender_name}")
                print(f"{Fore.BLUE}💬 Chat: {chat_name} (ID: {chat.id})")
                print(f"{Fore.WHITE}📝 New content: {event.text[:200]}{'...' if len(event.text) > 200 else ''}")
                print("-" * 60)
                
            except Exception as e:
                logger.error(f"❌ Error handling edited message: {e}")
        
        print(f"{Fore.GREEN}🚀 Telegram Monitor started!")
        print(f"{Fore.YELLOW}📡 Monitoring for new messages... (Press Ctrl+C to stop)")
        print("=" * 60)
        
        try:
            # Keep the client running
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⏹️ Stopping monitor...")
        finally:
            self.running = False
            await self.client.disconnect()
            print(f"{Fore.RED}👋 Monitor stopped")

async def main():
    """Main entry point for the monitor"""
    monitor = TelegramMonitor()
    await monitor.start_monitoring()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Monitor error: {e}")
