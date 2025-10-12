import asyncio
import logging
from typing import Optional, List
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
        for command_name in ['connect']:
            command = cli.commands[command_name]
            command.callback = async_command(command.callback)
        
        cli()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Goodbye!")
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}")

if __name__ == '__main__':
    main()
