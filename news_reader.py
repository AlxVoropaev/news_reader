import asyncio
import logging
from typing import Optional, List
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.network import MTProtoSender
from telethon.network.connection import ConnectionTcpFull
from config import Config
import click
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsReader:
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.config = Config()
        
    async def initialize_client(self):
        """Initialize Telegram client with MTProto configuration"""
        try:
            # Validate configuration
            self.config.validate()
            
            # Create client with custom MTProto server settings
            self.client = TelegramClient(
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
                device_model='News Reader Client',
                system_version='1.0',
                app_version='1.0',
                lang_code='en',
                system_lang_code='en'
            )
            
            # Connect to the client
            await self.client.connect()
            
            # Check if we're authorized
            if not await self.client.is_user_authorized():
                await self._authorize_user()
            
            logger.info("✅ Successfully connected to Telegram!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize client: {e}")
            return False
    
    async def _authorize_user(self):
        """Handle user authorization"""
        try:
            # Send code request
            await self.client.send_code_request(self.config.PHONE_NUMBER)
            print(f"{Fore.YELLOW}📱 Code sent to {self.config.PHONE_NUMBER}")
            
            # Get code from user
            code = input(f"{Fore.CYAN}Enter the code you received: ")
            
            try:
                # Sign in with the code
                await self.client.sign_in(self.config.PHONE_NUMBER, code)
                print(f"{Fore.GREEN}✅ Successfully authorized!")
                
            except Exception as e:
                if "Two-step verification" in str(e):
                    # Handle 2FA
                    password = input(f"{Fore.CYAN}Enter your 2FA password: ")
                    await self.client.sign_in(password=password)
                    print(f"{Fore.GREEN}✅ Successfully authorized with 2FA!")
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Authorization failed: {e}")
            raise
    
    
    async def list_channels(self):
        """List all user's channels"""
        try:
            if not self.client:
                print(f"{Fore.RED}❌ Client not initialized. Please connect first.")
                return []
            
            print(f"{Fore.CYAN}📡 Fetching your channels...")
            channels = []
            
            async for dialog in self.client.iter_dialogs():
                if dialog.is_channel:
                    channels.append({
                        'id': dialog.id,
                        'title': dialog.title,
                        'entity': dialog.entity
                    })
            
            if not channels:
                print(f"{Fore.YELLOW}📭 No channels found.")
                return []
            
            print(f"\n{Fore.GREEN}📺 Your channels:")
            print(f"{Fore.CYAN}{'ID':<15} {'Title'}")
            print("-" * 60)
            
            for channel in channels:
                print(f"{Fore.WHITE}{channel['id']:<15} {channel['title']}")
            
            # Save channel information to database
            await self._save_channel_info(channels)
            
            return channels
            
        except Exception as e:
            logger.error(f"❌ Failed to list channels: {e}")
            print(f"{Fore.RED}❌ Failed to list channels: {e}")
            return []
    
    async def select_channels_for_monitoring(self):
        """Interactive channel selection for monitoring"""
        try:
            channels = await self.list_channels()
            if not channels:
                return []
            
            print(f"\n{Fore.YELLOW}🔧 Select channels to monitor:")
            print(f"{Fore.CYAN}Enter channel IDs separated by commas (or 'all' for all channels):")
            
            user_input = input(f"{Fore.WHITE}> ").strip()
            
            if user_input.lower() == 'all':
                selected_channels = [ch['id'] for ch in channels]
                print(f"{Fore.GREEN}✅ Selected all {len(selected_channels)} channels for monitoring")
            else:
                try:
                    # Parse comma-separated channel IDs
                    channel_ids = [int(id_str.strip()) for id_str in user_input.split(',') if id_str.strip()]
                    
                    # Validate channel IDs
                    valid_ids = [ch['id'] for ch in channels]
                    selected_channels = [ch_id for ch_id in channel_ids if ch_id in valid_ids]
                    
                    if not selected_channels:
                        print(f"{Fore.RED}❌ No valid channel IDs provided")
                        return []
                    
                    # Show selected channels
                    selected_titles = [ch['title'] for ch in channels if ch['id'] in selected_channels]
                    print(f"{Fore.GREEN}✅ Selected {len(selected_channels)} channels:")
                    for title in selected_titles:
                        print(f"  - {title}")
                        
                except ValueError:
                    print(f"{Fore.RED}❌ Invalid input. Please enter numeric channel IDs.")
                    return []
            
            # Save selected channels to config file
            await self._save_monitored_channels(selected_channels)
            return selected_channels
            
        except Exception as e:
            logger.error(f"❌ Failed to select channels: {e}")
            print(f"{Fore.RED}❌ Failed to select channels: {e}")
            return []
    
    async def _save_monitored_channels(self, channel_ids):
        """Save monitored channels using database client"""
        try:
            from db_client import get_db_client
            
            db_client = get_db_client()
            
            if db_client.set_monitored_channels(channel_ids, user='news_reader'):
                print(f"{Fore.GREEN}💾 Saved monitoring configuration to database")
            else:
                print(f"{Fore.RED}❌ Failed to save monitoring configuration")
            
        except Exception as e:
            logger.error(f"❌ Failed to save channel config: {e}")
            print(f"{Fore.RED}❌ Failed to save channel config: {e}")
    
    async def _save_channel_info(self, channels):
        """Save channel information to database"""
        try:
            from db_client import get_db_client
            
            db_client = get_db_client()
            
            for channel in channels:
                channel_username = getattr(channel['entity'], 'username', None)
                db_client.add_channel_info(
                    channel_id=channel['id'],
                    channel_title=channel['title'],
                    channel_username=channel_username
                )
            
            logger.info(f"Saved information for {len(channels)} channels to database")
            
        except Exception as e:
            logger.error(f"❌ Failed to save channel info: {e}")
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            print(f"{Fore.YELLOW}👋 Disconnected from Telegram")

# CLI Interface
@click.group()
@click.pass_context
def cli(ctx):
    """News Reader - Telegram CLI Client with MTProto support"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = NewsReader()

@cli.command()
@click.pass_context
async def connect(ctx):
    """Connect to Telegram"""
    client = ctx.obj['client']
    success = await client.initialize_client()
    if success:
        print(f"{Fore.GREEN}🚀 Connected to Telegram successfully!")
    else:
        print(f"{Fore.RED}❌ Failed to connect to Telegram")

@cli.command()
@click.pass_context
async def channels(ctx):
    """List all your channels"""
    client = ctx.obj['client']
    if not await client.initialize_client():
        return
    await client.list_channels()
    await client.disconnect()

@cli.command()
@click.pass_context
async def setup_monitoring(ctx):
    """Setup channel monitoring - select which channels to monitor"""
    client = ctx.obj['client']
    if not await client.initialize_client():
        return
    await client.select_channels_for_monitoring()
    await client.disconnect()


def main():
    """Main entry point"""
    try:
        # Run the CLI with asyncio support
        import sys
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Monkey patch click to support async
        import functools
        
        def async_command(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                return asyncio.run(f(*args, **kwargs))
            return wrapper
        
        # Apply async wrapper to all commands
        for command_name in ['connect', 'channels', 'setup_monitoring']:
            command = cli.commands[command_name]
            command.callback = async_command(command.callback)
        
        cli()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Goodbye!")
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}")

if __name__ == '__main__':
    main()
