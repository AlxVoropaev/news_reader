#!/usr/bin/env python3
"""
Monitoring Task - Handles Telegram message monitoring
"""

import asyncio
import logging
from typing import List
from datetime import datetime
from telethon import TelegramClient, events
from colorama import Fore

logger = logging.getLogger(__name__)

class MonitoringTask:
    def __init__(self, client: TelegramClient, monitored_channels: List[int]):
        self.client = client
        self.monitored_channels = monitored_channels
        self.running = False
    
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
                print(f"{Fore.GREEN}> ", end="", flush=True)  # Show prompt again
                
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
                print(f"{Fore.GREEN}> ", end="", flush=True)  # Show prompt again
                
            except Exception as e:
                logger.error(f"❌ Error handling edited message: {e}")
        
        print(f"{Fore.GREEN}📡 Monitoring started for {len(self.monitored_channels)} channels")
        
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
