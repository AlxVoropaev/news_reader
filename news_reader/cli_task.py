#!/usr/bin/env python3
"""
CLI Task - Handles interactive command-line interface
"""

from typing import TYPE_CHECKING
from colorama import Fore
import aioconsole
import pyperclip
from news_reader.logging_config import get_logger

if TYPE_CHECKING:
    from news_reader.app import NewsReaderApp

logger = get_logger(__name__)

class CLITask:
    def __init__(self, app: 'NewsReaderApp'):
        self.app = app
        self.running = False
    
    async def start(self):
        """Start interactive CLI loop"""
        print(f"\n{Fore.CYAN}💬 Interactive CLI started. Type 'help' for available commands.")
        
        self.running = True
        while self.running:
            try:
                print(f"{Fore.GREEN}> ", end="", flush=True)
                command = await aioconsole.ainput("")
                
                if not command.strip():
                    continue
                
                await self._process_command(command.strip())
                
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                logger.error(f"CLI error: {e}")
                print(f"{Fore.RED}❌ Error: {e}")
    
    def stop(self):
        """Stop CLI"""
        self.running = False
    
    async def _process_command(self, command: str):
        """Process user commands"""
        parts = command.lower().split()
        if not parts:
            return
        
        cmd = parts[0]
        
        if cmd == 'help':
            await self._show_help()
        elif cmd == 'status':
            await self._show_status()
        elif cmd == 'channels':
            await self._list_channels()
        elif cmd == 'copy':
            if len(parts) > 1:
                await self._copy_channel_id(parts[1])
            else:
                print(f"{Fore.RED}❌ Please specify a channel ID to copy. Usage: copy <channel_id>")
        elif cmd == 'update':
            if len(parts) > 1 and parts[1] == 'list':
                await self._update_channels_list()
            else:
                print(f"{Fore.RED}❌ Unknown update command. Use 'update list' to refresh channel cache.")
        elif cmd == 'monitor':
            if len(parts) > 1 and parts[1] == 'setup':
                await self._setup_monitoring()
            else:
                await self._show_monitoring_status()
        elif cmd == 'reload':
            await self._reload_config()
        elif cmd == 'quit' or cmd == 'exit':
            print(f"{Fore.YELLOW}👋 Shutting down...")
            self.app.running = False
            self.running = False
            return  # Exit the command processing to break the CLI loop
        else:
            print(f"{Fore.RED}❌ Unknown command: {cmd}. Type 'help' for available commands.")
    
    async def _show_help(self):
        """Show available commands"""
        print(f"\n{Fore.CYAN}📚 Available Commands:")
        print(f"{Fore.WHITE}  help           - Show this help message")
        print(f"{Fore.WHITE}  status         - Show application status")
        print(f"{Fore.WHITE}  channels       - List all your channels (from cache)")
        print(f"{Fore.WHITE}  copy <id>      - Copy channel ID to clipboard")
        print(f"{Fore.WHITE}  update list    - Refresh channel list from Telegram API")
        print(f"{Fore.WHITE}  monitor        - Show monitoring status")
        print(f"{Fore.WHITE}  monitor setup  - Setup channel monitoring")
        print(f"{Fore.WHITE}  reload         - Reload configuration")
        print(f"{Fore.WHITE}  quit/exit      - Exit the application")
    
    async def _show_status(self):
        """Show application status"""
        print(f"\n{Fore.CYAN}📊 Application Status:")
        print(f"{Fore.WHITE}  User: {self.app.session_data.get('user_name', 'Unknown')}")
        print(f"{Fore.WHITE}  Login Time: {self.app.session_data.get('login_time', 'Unknown')}")
        print(f"{Fore.WHITE}  Connected: {'Yes' if self.app.client and self.app.client.is_connected() else 'No'}")
        print(f"{Fore.WHITE}  Monitoring: {len(self.app.monitored_channels)} channels")
        print(f"{Fore.WHITE}  Running: {'Yes' if self.app.running else 'No'}")
        
        # Show cache information
        cache_info = self.app.db_client.get_cache_info()
        if cache_info.get('has_cache'):
            print(f"{Fore.WHITE}  Cached Channels: {cache_info.get('channels_count', 0)} (last updated: {cache_info.get('cached_at', 'Unknown')})")
        else:
            print(f"{Fore.WHITE}  Cached Channels: None (use 'update list' to cache)")
    
    async def _list_channels(self):
        """List all user's channels from cache"""
        try:
            # Check if we have cached channels
            if not self.app.cached_channels:
                print(f"{Fore.YELLOW}📭 No cached channels found.")
                print(f"{Fore.CYAN}💡 Use 'update list' to fetch channels from Telegram API")
                return
            
            cache_info = self.app.db_client.get_cache_info()
            print(f"{Fore.CYAN}📺 Your channels (cached at: {cache_info.get('cached_at', 'Unknown')}):")
            print(f"{Fore.CYAN}{'ID':<15} {'Title'}")
            print("-" * 60)
            
            for channel in self.app.cached_channels:
                monitored = "✅" if channel['id'] in self.app.monitored_channels else "  "
                print(f"{Fore.WHITE}{monitored} {channel['id']:<15} {channel['title']}")
            
            print(f"\n{Fore.YELLOW}💡 Tip: Use 'copy <channel_id>' to copy a channel ID to clipboard")
                       
        except Exception as e:
            logger.error(f"❌ Failed to list channels: {e}")
            print(f"{Fore.RED}❌ Failed to list channels: {e}")
    
    async def _copy_channel_id(self, channel_id_str: str):
        """Copy channel ID to clipboard"""
        try:
            # Convert to integer to validate
            channel_id = int(channel_id_str)
            
            # Check if channel exists in cached channels
            if not self.app.cached_channels:
                print(f"{Fore.YELLOW}📭 No cached channels found.")
                print(f"{Fore.CYAN}💡 Use 'update list' to fetch channels from Telegram API first")
                return
            
            # Find the channel
            channel_found = None
            for channel in self.app.cached_channels:
                if channel['id'] == channel_id:
                    channel_found = channel
                    break
            
            if not channel_found:
                print(f"{Fore.RED}❌ Channel ID {channel_id} not found in your channels list")
                print(f"{Fore.CYAN}💡 Use 'channels' command to see available channels")
                return
            
            # Copy to clipboard
            pyperclip.copy(str(channel_id))
            print(f"{Fore.GREEN}✅ Copied channel ID {channel_id} to clipboard!")
            print(f"{Fore.CYAN}📋 Channel: {channel_found['title']}")
            
        except ValueError:
            print(f"{Fore.RED}❌ Invalid channel ID. Please enter a numeric channel ID.")
        except Exception as e:
            logger.error(f"❌ Failed to copy channel ID: {e}")
            print(f"{Fore.RED}❌ Failed to copy channel ID: {e}")
    
    async def _update_channels_list(self):
        """Update channels list by fetching from Telegram API"""
        try:
            user_name = self.app.session_data.get('user_name', 'system')
            if await self.app.refresh_channels_cache(user_name):
                print(f"{Fore.GREEN}✅ Channel list updated successfully!")
                
                # Show updated count
                cache_info = self.app.db_client.get_cache_info()
                print(f"{Fore.CYAN}📊 Total channels: {cache_info.get('channels_count', 0)}")
            else:
                print(f"{Fore.RED}❌ Failed to update channel list")
                
        except Exception as e:
            logger.error(f"❌ Failed to update channels list: {e}")
            print(f"{Fore.RED}❌ Failed to update channels list: {e}")
    
    async def _setup_monitoring(self):
        """Setup channel monitoring"""
        try:
            # Check if we have cached channels
            if not self.app.cached_channels:
                print(f"{Fore.YELLOW}📭 No cached channels found.")
                print(f"{Fore.CYAN}💡 Use 'update list' first to fetch channels from Telegram API")
                return
            
            # First list channels
            await self._list_channels()
            
            print(f"\n{Fore.YELLOW}🔧 Select channels to monitor:")
            print(f"{Fore.CYAN}Enter channel IDs separated by commas (or 'all' for all channels):")
            
            user_input = await aioconsole.ainput(f"{Fore.WHITE}> ")
            user_input = user_input.strip()
            
            # Use cached channels
            channels = self.app.cached_channels
            
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
                        return
                    
                    # Show selected channels
                    selected_titles = [ch['title'] for ch in channels if ch['id'] in selected_channels]
                    print(f"{Fore.GREEN}✅ Selected {len(selected_channels)} channels:")
                    for title in selected_titles:
                        print(f"  - {title}")
                        
                except ValueError:
                    print(f"{Fore.RED}❌ Invalid input. Please enter numeric channel IDs.")
                    return
            
            # Save selected channels
            if self.app.db_client.set_monitored_channels(selected_channels, user=self.app.session_data.get('user_name', 'system')):
                print(f"{Fore.GREEN}💾 Saved monitoring configuration")
                # Reload monitored channels
                await self.app._load_monitored_channels()
                # Update monitoring task
                if self.app.monitoring_task_instance:
                    self.app.monitoring_task_instance.update_channels(self.app.monitored_channels)
            else:
                print(f"{Fore.RED}❌ Failed to save monitoring configuration")
                
        except Exception as e:
            logger.error(f"❌ Failed to setup monitoring: {e}")
            print(f"{Fore.RED}❌ Failed to setup monitoring: {e}")
    
    async def _show_monitoring_status(self):
        """Show monitoring status"""
        print(f"\n{Fore.CYAN}📡 Monitoring Status:")
        if self.app.monitored_channels:
            print(f"{Fore.GREEN}✅ Monitoring {len(self.app.monitored_channels)} channels:")
            for channel_id in self.app.monitored_channels:
                channel_info = self.app.db_client.get_channel_info(channel_id)
                title = channel_info.get('channel_title', f'Channel {channel_id}')
                print(f"  - {title} ({channel_id})")
        else:
            print(f"{Fore.YELLOW}⚠️ No channels configured for monitoring")
            print(f"{Fore.CYAN}💡 Use 'monitor setup' to configure channels")
    
    async def _reload_config(self):
        """Reload configuration"""
        print(f"{Fore.YELLOW}🔄 Reloading configuration...")
        await self.app._load_monitored_channels()
        # Update monitoring task
        if self.app.monitoring_task_instance:
            self.app.monitoring_task_instance.update_channels(self.app.monitored_channels)
        print(f"{Fore.GREEN}✅ Configuration reloaded")
    
    async def _save_channel_info(self, channels):
        """Save channel information to database"""
        try:
            for channel in channels:
                channel_username = getattr(channel['entity'], 'username', None)
                self.app.db_client.add_channel_info(
                    channel_id=channel['id'],
                    channel_title=channel['title'],
                    channel_username=channel_username
                )
            
            logger.info(f"Saved information for {len(channels)} channels to database")
            
        except Exception as e:
            logger.error(f"❌ Failed to save channel info: {e}")
