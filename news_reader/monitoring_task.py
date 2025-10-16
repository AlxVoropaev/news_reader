#!/usr/bin/env python3
"""
Monitoring Task - Handles Telegram message monitoring
"""

import asyncio
from typing import List
from datetime import datetime
from telethon import TelegramClient, events, utils
from colorama import Fore
from news_reader.logging_config import get_logger

logger = get_logger(__name__)

class MonitoringTask:
    def __init__(self, client: TelegramClient, monitored_channels: List[int], gui_logger=None):
        self.client = client
        self.monitored_channels = monitored_channels
        self.running = False
        self.gui_logger = gui_logger  # Reference to GUI logger (TextualCLITask)
    
    def log_to_gui(self, message: str) -> None:
        """Send log message to GUI if available, otherwise use logger"""
        if self.gui_logger:
            try:
                self.gui_logger.add_log_message(message)
            except Exception as e:
                logger.error(f"Failed to send message to GUI: {e}")
        else:
            logger.info(message)
    
    async def start(self):
        """Start monitoring for new messages"""
        if not self.monitored_channels:
            logger.info("No channels configured for monitoring")
            return
        
        logger.info(f"Starting monitoring for {len(self.monitored_channels)} channels")
        
        # Register event handlers
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                chat = await event.get_chat()
                
                # Check if message is from a monitored channel
                # Convert real_id to marked identifier for comparison
                if hasattr(chat, 'id'):
                    # Get the marked identifier from the real ID
                    marked_id = utils.get_peer_id(chat)
                    if marked_id not in self.monitored_channels:
                        return  # Skip messages from non-monitored channels
                
                sender = await event.get_sender()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sender_name = getattr(sender, 'first_name', 'Unknown') or 'Unknown'
                chat_name = getattr(chat, 'title', getattr(chat, 'first_name', 'Private'))
                
                # Format message for GUI display
                message_text = event.text[:200] + ('...' if len(event.text) > 200 else '') if event.text else '[No text]'
                
                log_message = (
                    f"[cyan]📨 [{timestamp}] New message[/cyan]\n"
                    f"[yellow]👤 From: {sender_name}[/yellow]\n"
                    f"[blue]💬 Chat: {chat_name} (ID: {chat.id})[/blue]\n"
                    f"[white]📝 Message: {message_text}[/white]\n"
                )
                
                self.log_to_gui(log_message)
                
            except Exception as e:
                logger.error(f"❌ Error handling message: {e}")
                self.log_to_gui(f"[red]❌ Error handling message: {e}[/red]")
                
        self.log_to_gui(f"[green]📡 Monitoring started for {len(self.monitored_channels)} channels[/green]")
        
        # Keep monitoring running
        self.running = True
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Monitoring task cancelled")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
    
    def update_channels(self, channels: List[int]):
        """Update monitored channels"""
        self.monitored_channels = channels
