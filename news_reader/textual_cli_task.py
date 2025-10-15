#!/usr/bin/env python3
"""
Textual CLI Task - Handles interactive menu-based interface using Textual library
"""

import asyncio
import logging
from typing import TYPE_CHECKING, List, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Static, Button, Label, ListItem, ListView, 
    Input, Checkbox, DataTable, Rule
)
from textual.screen import Screen
from textual.binding import Binding
from textual.message import Message
from textual import on
from colorama import Fore

if TYPE_CHECKING:
    from news_reader.app import NewsReaderApp

logger = logging.getLogger(__name__)

class StatusScreen(Screen):
    """Screen showing application status"""
    
    BINDINGS = [
        Binding("escape", "back", "Back to Main Menu"),
        Binding("q", "quit", "Quit Application"),
    ]
    
    def __init__(self, app_instance: 'NewsReaderApp'):
        super().__init__()
        self.app_instance = app_instance
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📊 Application Status", classes="title"),
            Rule(),
            Static(id="status_content"),
            classes="status_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        self.update_status()
    
    def update_status(self) -> None:
        """Update status information"""
        status_lines = [
            f"User: {self.app_instance.session_data.get('user_name', 'Unknown')}",
            f"Login Time: {self.app_instance.session_data.get('login_time', 'Unknown')}",
            f"Connected: {'Yes' if self.app_instance.client and self.app_instance.client.is_connected() else 'No'}",
            f"Monitoring: {len(self.app_instance.monitored_channels)} channels",
            f"Running: {'Yes' if self.app_instance.running else 'No'}",
        ]
        
        # Add cache information
        cache_info = self.app_instance.db_client.get_cache_info()
        if cache_info.get('has_cache'):
            status_lines.append(f"Cached Channels: {cache_info.get('channels_count', 0)} (last updated: {cache_info.get('cached_at', 'Unknown')})")
        else:
            status_lines.append("Cached Channels: None (use Update Channels to cache)")
        
        status_widget = self.query_one("#status_content", Static)
        status_widget.update("\n".join(status_lines))
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        self.app.exit()

class ChannelsScreen(Screen):
    """Screen showing channels list"""
    
    BINDINGS = [
        Binding("escape", "back", "Back to Main Menu"),
        Binding("u", "update", "Update Channels"),
        Binding("q", "quit", "Quit Application"),
    ]
    
    def __init__(self, app_instance: 'NewsReaderApp'):
        super().__init__()
        self.app_instance = app_instance
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📺 Your Channels", classes="title"),
            Rule(),
            Static("Press 'u' to update channels from Telegram API", classes="help_text"),
            DataTable(id="channels_table"),
            classes="channels_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        self.update_channels_display()
    
    def update_channels_display(self) -> None:
        """Update channels display"""
        table = self.query_one("#channels_table", DataTable)
        table.clear(columns=True)
        table.add_columns("Status", "ID", "Title")
        
        if not self.app_instance.cached_channels:
            table.add_row("", "", "No cached channels found. Press 'u' to fetch from Telegram API")
            return
        
        for channel in self.app_instance.cached_channels:
            monitored = "✅" if channel['id'] in self.app_instance.monitored_channels else ""
            table.add_row(monitored, str(channel['id']), channel['title'])
    
    async def action_update(self) -> None:
        """Update channels from Telegram API"""
        # Show loading message
        table = self.query_one("#channels_table", DataTable)
        table.clear(columns=True)
        table.add_columns("Status")
        table.add_row("📡 Fetching channels from Telegram API...")
        
        user_name = self.app_instance.session_data.get('user_name', 'system')
        success = await self.app_instance.refresh_channels_cache(user_name)
        
        if success:
            self.notify("✅ Channel list updated successfully!")
        else:
            self.notify("❌ Failed to update channel list", severity="error")
        
        self.update_channels_display()
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        self.app.exit()

class MonitoringScreen(Screen):
    """Screen showing monitoring status and setup"""
    
    BINDINGS = [
        Binding("escape", "back", "Back to Main Menu"),
        Binding("s", "setup", "Setup Monitoring"),
        Binding("q", "quit", "Quit Application"),
    ]
    
    def __init__(self, app_instance: 'NewsReaderApp'):
        super().__init__()
        self.app_instance = app_instance
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📡 Monitoring Status", classes="title"),
            Rule(),
            Static("Press 's' to setup monitoring configuration", classes="help_text"),
            Static(id="monitoring_content"),
            classes="monitoring_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        self.update_monitoring_display()
    
    def update_monitoring_display(self) -> None:
        """Update monitoring display"""
        content_lines = []
        
        if self.app_instance.monitored_channels:
            content_lines.append(f"✅ Monitoring {len(self.app_instance.monitored_channels)} channels:")
            for channel_id in self.app_instance.monitored_channels:
                channel_info = self.app_instance.db_client.get_channel_info(channel_id)
                title = channel_info.get('channel_title', f'Channel {channel_id}')
                content_lines.append(f"  - {title} ({channel_id})")
        else:
            content_lines.append("⚠️ No channels configured for monitoring")
            content_lines.append("💡 Press 's' to configure channels")
        
        content_widget = self.query_one("#monitoring_content", Static)
        content_widget.update("\n".join(content_lines))
    
    def action_setup(self) -> None:
        """Setup monitoring configuration"""
        self.app.push_screen(MonitoringSetupScreen(self.app_instance))
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        self.app.exit()

class MonitoringSetupScreen(Screen):
    """Screen for setting up monitoring configuration"""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("ctrl+s", "save", "Save Configuration"),
        Binding("ctrl+a", "select_all", "Select All"),
        Binding("ctrl+n", "select_none", "Select None"),
    ]
    
    def __init__(self, app_instance: 'NewsReaderApp'):
        super().__init__()
        self.app_instance = app_instance
        self.checkboxes: List[Checkbox] = []
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("🔧 Setup Channel Monitoring", classes="title"),
            Rule(),
            Static("Select channels to monitor (Ctrl+S to save, Ctrl+A/N to select all/none):", classes="help_text"),
            Container(id="channels_list"),
            Horizontal(
                Button("Save Configuration", id="save_btn", variant="primary"),
                Button("Select All", id="select_all_btn"),
                Button("Select None", id="select_none_btn"),
                Button("Cancel", id="cancel_btn"),
                classes="button_row"
            ),
            classes="setup_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        self.populate_channels()
    
    def populate_channels(self) -> None:
        """Populate channels list with checkboxes"""
        container = self.query_one("#channels_list", Container)
        
        if not self.app_instance.cached_channels:
            container.mount(Static("No cached channels found. Please update channels first."))
            return
        
        self.checkboxes = []
        for channel in self.app_instance.cached_channels:
            is_monitored = channel['id'] in self.app_instance.monitored_channels
            checkbox = Checkbox(
                f"{channel['title']} ({channel['id']})",
                value=is_monitored,
                id=f"channel_{channel['id']}"
            )
            self.checkboxes.append(checkbox)
            container.mount(checkbox)
    
    @on(Button.Pressed, "#save_btn")
    async def save_configuration(self) -> None:
        """Save monitoring configuration"""
        selected_channels = []
        
        for checkbox in self.checkboxes:
            if checkbox.value:
                # Extract channel ID from checkbox ID
                channel_id = int(checkbox.id.replace("channel_", ""))
                selected_channels.append(channel_id)
        
        user_name = self.app_instance.session_data.get('user_name', 'system')
        if self.app_instance.db_client.set_monitored_channels(selected_channels, user=user_name):
            self.notify(f"✅ Saved monitoring configuration for {len(selected_channels)} channels")
            # Reload monitored channels
            await self.app_instance._load_monitored_channels()
            # Update monitoring task
            if self.app_instance.monitoring_task_instance:
                self.app_instance.monitoring_task_instance.update_channels(self.app_instance.monitored_channels)
            self.app.pop_screen()
        else:
            self.notify("❌ Failed to save monitoring configuration", severity="error")
    
    @on(Button.Pressed, "#select_all_btn")
    def select_all(self) -> None:
        """Select all channels"""
        for checkbox in self.checkboxes:
            checkbox.value = True
    
    @on(Button.Pressed, "#select_none_btn")
    def select_none(self) -> None:
        """Deselect all channels"""
        for checkbox in self.checkboxes:
            checkbox.value = False
    
    @on(Button.Pressed, "#cancel_btn")
    def cancel_setup(self) -> None:
        """Cancel setup"""
        self.app.pop_screen()
    
    def action_save(self) -> None:
        """Save configuration hotkey"""
        self.query_one("#save_btn", Button).press()
    
    def action_select_all(self) -> None:
        """Select all hotkey"""
        self.select_all()
    
    def action_select_none(self) -> None:
        """Select none hotkey"""
        self.select_none()
    
    def action_back(self) -> None:
        self.app.pop_screen()

class MainMenuScreen(Screen):
    """Main menu screen"""
    
    BINDINGS = [
        Binding("1", "status", "Application Status"),
        Binding("2", "channels", "View Channels"),
        Binding("3", "monitoring", "Monitoring"),
        Binding("4", "reload", "Reload Config"),
        Binding("q", "quit", "Quit Application"),
    ]
    
    def __init__(self, app_instance: 'NewsReaderApp'):
        super().__init__()
        self.app_instance = app_instance
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("🗞️ News Reader - Main Menu", classes="title"),
            Rule(),
            Vertical(
                Button("1. Application Status", id="status_btn", classes="menu_button"),
                Button("2. View Channels", id="channels_btn", classes="menu_button"),
                Button("3. Monitoring", id="monitoring_btn", classes="menu_button"),
                Button("4. Reload Configuration", id="reload_btn", classes="menu_button"),
                Rule(),
                Button("Q. Quit Application", id="quit_btn", variant="error", classes="menu_button"),
                classes="menu_container"
            ),
            classes="main_container"
        )
        yield Footer()
    
    @on(Button.Pressed, "#status_btn")
    def show_status(self) -> None:
        self.app.push_screen(StatusScreen(self.app_instance))
    
    @on(Button.Pressed, "#channels_btn")
    def show_channels(self) -> None:
        self.app.push_screen(ChannelsScreen(self.app_instance))
    
    @on(Button.Pressed, "#monitoring_btn")
    def show_monitoring(self) -> None:
        self.app.push_screen(MonitoringScreen(self.app_instance))
    
    @on(Button.Pressed, "#reload_btn")
    async def reload_config(self) -> None:
        """Reload configuration"""
        await self.app_instance._load_monitored_channels()
        # Update monitoring task
        if self.app_instance.monitoring_task_instance:
            self.app_instance.monitoring_task_instance.update_channels(self.app_instance.monitored_channels)
        self.notify("✅ Configuration reloaded")
    
    @on(Button.Pressed, "#quit_btn")
    def quit_app(self) -> None:
        self.app.exit()
    
    def action_status(self) -> None:
        self.show_status()
    
    def action_channels(self) -> None:
        self.show_channels()
    
    def action_monitoring(self) -> None:
        self.show_monitoring()
    
    def action_reload(self) -> None:
        asyncio.create_task(self.reload_config())
    
    def action_quit(self) -> None:
        self.app.exit()

class NewsReaderTextualApp(App):
    """Main Textual application"""
    
    CSS = """
    .title {
        text-align: center;
        text-style: bold;
        color: cyan;
        margin: 1;
    }
    
    .help_text {
        text-align: center;
        color: yellow;
        margin: 1;
    }
    
    .menu_container {
        align: center middle;
        width: 50%;
        height: auto;
    }
    
    .menu_button {
        width: 100%;
        margin: 1;
    }
    
    .main_container {
        align: center middle;
    }
    
    .status_container, .channels_container, .monitoring_container, .setup_container {
        padding: 1;
        margin: 1;
    }
    
    .button_row {
        align: center middle;
        margin: 1;
    }
    
    DataTable {
        height: 20;
    }
    
    #channels_list {
        height: 15;
        overflow-y: auto;
        border: solid white;
        margin: 1;
        padding: 1;
    }
    """
    
    def __init__(self, app_instance: 'NewsReaderApp'):
        super().__init__()
        self.app_instance = app_instance
        self.title = "News Reader"
        self.sub_title = "Telegram News Monitoring"
    
    def on_mount(self) -> None:
        self.push_screen(MainMenuScreen(self.app_instance))

class TextualCLITask:
    """Textual-based CLI task that replaces the old CLI task"""
    
    def __init__(self, app: 'NewsReaderApp'):
        self.app = app
        self.running = False
        self.textual_app = None
    
    async def start(self):
        """Start the Textual interface"""
        logger.info("Starting Textual CLI interface...")
        
        self.running = True
        self.textual_app = NewsReaderTextualApp(self.app)
        
        try:
            # Run the Textual app
            await self.textual_app.run_async()
        except Exception as e:
            logger.error(f"Textual CLI error: {e}")
        finally:
            self.running = False
            # Signal main app to shutdown
            self.app.running = False
    
    def stop(self):
        """Stop the Textual interface"""
        self.running = False
        if self.textual_app:
            self.textual_app.exit()
