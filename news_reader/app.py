#!/usr/bin/env python3
"""
News Reader - Unified Telegram Client Application
Main application controller that coordinates monitoring and CLI tasks
"""

import asyncio
import aioconsole
import getpass
import logging
import signal
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.network.connection import ConnectionTcpFull
from telethon.errors import SessionPasswordNeededError
from news_reader.config import Config
from news_reader.db_client import get_db_client
from news_reader.monitoring_task import MonitoringTask
from news_reader.textual_cli_task import TextualCLITask
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsReaderApp:
    def __init__(self):
        # Validate configuration
        self.config = Config()
        self.config.validate()

        # Initialize Telegram client
        self.client: TelegramClient = TelegramClient(
            session=self.config.SESSION_NAME,
            api_id=self.config.API_ID,
            api_hash=self.config.API_HASH,
            connection=ConnectionTcpFull,
            use_ipv6=False,
            proxy=None,
            local_addr=None,
            timeout=10,
            request_retries=5,
            connection_retries=5,
            retry_delay=1,
            auto_reconnect=True,
            sequential_updates=False,
            flood_sleep_threshold=60,
            device_model='News Reader App',
            system_version='2.0.0',
            app_version='2.0.0',
            lang_code='en',
            system_lang_code='en'
        )

        # Initialize rest of the application
        self.db_client = get_db_client()
        self.running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.cli_task: Optional[asyncio.Task] = None
        self.monitoring_task_instance: Optional[MonitoringTask] = None
        self.cli_task_instance: Optional[TextualCLITask] = None
        self.monitored_channels: List[int] = []
        self.session_data: Dict[str, Any] = {}
        self.cached_channels: List[Dict[str, Any]] = []
        
    async def startup(self):
        """Initialize the application and perform user login"""
        print(f"{Fore.CYAN}🚀 Starting News Reader Application...")
        
        # Initialize Telegram client
        if not await self._initialize_client():
            return False
            
        # Load user session data into memory
        await self._load_session_data()
        
        # Load monitored channels configuration
        await self._load_monitored_channels()
        
        # Load cached channels or fetch them if not cached
        await self._load_cached_channels()
        
        print(f"{Fore.GREEN}✅ Application started successfully!")
        print(f"{Fore.YELLOW}📱 User: {self.session_data.get('user_name', 'Unknown')}")
        print(f"{Fore.YELLOW}📺 Monitoring {len(self.monitored_channels)} channels")
        
        cache_info = self.db_client.get_cache_info()
        if cache_info.get('has_cache'):
            print(f"{Fore.CYAN}💾 Cached {cache_info.get('channels_count', 0)} channels (last updated: {cache_info.get('cached_at', 'Unknown')})")
        else:
            print(f"{Fore.YELLOW}⚠️ No channel cache found - will fetch on first 'channels' command")
        
        return True
    
    async def _initialize_client(self):
        """Initialize Telegram client with MTProto configuration"""
        try:            
            # Connect to the client
            await self.client.connect()
            
            # Check if we're authorized
            if not await self.client.is_user_authorized():
                await self._authorize_user()
            
            logger.info("✅ Successfully connected to Telegram!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize client: {e}")
            print(f"{Fore.RED}❌ Failed to initialize client: {e}")
            return False
    
    async def _authorize_user(self):
        """Handle user authorization"""
        try:
            print(f"{Fore.YELLOW}🔐 Authorization required...")
            
            # Send code request
            ret = await self.client.send_code_request(self.config.PHONE_NUMBER)
            print(ret)
            print(f"{Fore.YELLOW}📱 Code sent to {self.config.PHONE_NUMBER}")
            
            # Get code from user
            code = await aioconsole.ainput(f"{Fore.CYAN}Enter the code you received: ")
            
            try:
                # Sign in with the code
                await self.client.sign_in(self.config.PHONE_NUMBER, code)
                print(f"{Fore.GREEN}✅ Successfully authorized!")
                
            except SessionPasswordNeededError as e:
                # Handle 2FA - use getpass for secure password input
                print(f"{Fore.CYAN}Enter your 2FA password (input will be hidden): ", end="", flush=True)
                password = getpass.getpass("")
                await self.client.sign_in(password=password)
                print(f"{Fore.GREEN}✅ Successfully authorized with 2FA!")
                    
        except Exception as e:
            logger.error(f"❌ Authorization failed: {e}")
            raise
    
    async def _load_session_data(self):
        """Load user session data into memory"""
        try:
            if self.client:
                me = await self.client.get_me()
                self.session_data = {
                    'user_id': me.id,
                    'user_name': f"{me.first_name} {me.last_name or ''}".strip(),
                    'username': me.username,
                    'phone': me.phone,
                    'login_time': datetime.now().isoformat()
                }
                logger.info(f"Loaded session data for user: {self.session_data['user_name']}")
        except Exception as e:
            logger.error(f"Failed to load session data: {e}")
            self.session_data = {'user_name': 'Unknown', 'login_time': datetime.now().isoformat()}
    
    async def _load_monitored_channels(self):
        """Load monitored channels from database"""
        try:
            self.monitored_channels = self.db_client.get_monitored_channels()
            logger.info(f"Loaded {len(self.monitored_channels)} monitored channels")
        except Exception as e:
            logger.error(f"Failed to load monitored channels: {e}")
            self.monitored_channels = []
    
    async def _load_cached_channels(self):
        """Load cached channels from database"""
        try:
            self.cached_channels = self.db_client.get_cached_channels()
            logger.info(f"Loaded {len(self.cached_channels)} cached channels")
        except Exception as e:
            logger.error(f"Failed to load cached channels: {e}")
            self.cached_channels = []
    
    async def refresh_channels_cache(self, user: str = 'system') -> bool:
        """Refresh channels cache by fetching from Telegram API"""
        try:
            if not self.client:
                logger.error("Client not initialized")
                return False
            
            print(f"{Fore.CYAN}📡 Fetching channels from Telegram API...")
            channels = []
            
            async for dialog in self.client.iter_dialogs():
                if dialog.is_channel:
                    channel_data = {
                        'id': dialog.id,
                        'title': dialog.title,
                        'username': getattr(dialog.entity, 'username', None)
                    }
                    channels.append(channel_data)
                    
                    # Also save individual channel info
                    self.db_client.add_channel_info(
                        channel_id=dialog.id,
                        channel_title=dialog.title,
                        channel_username=getattr(dialog.entity, 'username', None)
                    )
            
            # Cache the channels list
            if self.db_client.cache_channels_list(channels, user):
                self.cached_channels = channels
                print(f"{Fore.GREEN}✅ Successfully cached {len(channels)} channels")
                logger.info(f"Refreshed channels cache with {len(channels)} channels")
                return True
            else:
                print(f"{Fore.RED}❌ Failed to cache channels")
                return False
                
        except Exception as e:
            logger.error(f"Failed to refresh channels cache: {e}")
            print(f"{Fore.RED}❌ Failed to refresh channels cache: {e}")
            return False
    
    async def run(self):
        """Main application loop"""
        if not await self.startup():
            return
        
        self.running = True
        
        # Create task instances
        self.cli_task_instance = TextualCLITask(self)
        self.monitoring_task_instance = MonitoringTask(self.client, self.monitored_channels, self.cli_task_instance)
        
        # Start background tasks
        self.monitoring_task = asyncio.create_task(self.monitoring_task_instance.start())
        self.cli_task = asyncio.create_task(self.cli_task_instance.start())
        
        # Setup signal handlers for graceful shutdown
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, self._signal_handler)
        
        try:
            # Wait for tasks to complete or for shutdown signal
            while self.running:
                # Check if CLI task has finished
                if self.cli_task.done():
                    break
                await asyncio.sleep(0.1)
            
            # If we're here, either running=False or CLI task finished
            if not self.running:
                logger.info("Shutdown requested, stopping tasks...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n{Fore.YELLOW}🛑 Received shutdown signal...")
        self.running = False
    
    async def shutdown(self):
        """Graceful shutdown"""
        print(f"{Fore.YELLOW}🛑 Shutting down application...")
        
        self.running = False
        
        # Stop task instances
        if self.monitoring_task_instance:
            self.monitoring_task_instance.stop()
        
        if self.cli_task_instance:
            self.cli_task_instance.stop()
        
        # Cancel tasks
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.cli_task and not self.cli_task.done():
            self.cli_task.cancel()
            try:
                await self.cli_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect client
        if self.client:
            await self.client.disconnect()
            print(f"{Fore.YELLOW}📱 Disconnected from Telegram")
        
        print(f"{Fore.GREEN}✅ Application shutdown complete")
