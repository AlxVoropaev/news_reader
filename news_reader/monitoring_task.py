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
from news_reader.db_client import get_db_client
from news_reader.llm_service import get_llm_service
from news_reader.config import Config

logger = get_logger(__name__)

class MonitoringTask:
    def __init__(self, client: TelegramClient, monitored_channels: List[int], gui_logger=None):
        self.client = client
        self.monitored_channels = monitored_channels
        self.running = False
        self.gui_logger = gui_logger  # Reference to GUI logger (TextualCLITask)
        self.db_client = get_db_client()  # Database client for saving messages
        self.llm_service = get_llm_service()  # LLM service for message summarization
        self.hourly_task = None  # Task for hourly message processing
    
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
                
                # Prepare message data
                message_data = {
                    'message_id': event.id,
                    'chat_id': chat.id,
                    'chat_name': chat_name,
                    'sender_id': sender.id if sender else None,
                    'sender_name': sender_name,
                    'message_text': event.text or '[No text]',
                    'timestamp': timestamp
                }
                
                # Generate LLM summary if service is available
                summary = None
                if self.llm_service.is_available() and event.text and len(event.text.strip()) > 10:
                    try:
                        summary = await self.llm_service.summarize_message(message_data)
                        if summary:
                            message_data['llm_summary'] = summary
                            message_data['summary_generated_at'] = datetime.now().isoformat()
                            self.log_to_gui(f"[green]🤖 Generated LLM summary for message from {sender_name}[/green]")
                    except Exception as llm_error:
                        logger.error(f"Failed to generate LLM summary: {llm_error}")
                        self.log_to_gui(f"[red]❌ LLM summarization failed: {llm_error}[/red]")
                
                # Save to database
                try:
                    self.db_client.save_incoming_message(message_data)
                except Exception as db_error:
                    logger.error(f"Failed to save message to database: {db_error}")
                
                log_message = (
                    f"[cyan]📨 [{timestamp}] New message[/cyan]\n"
                    f"[yellow]👤 From: {sender_name}[/yellow]\n"
                    f"[blue]💬 Chat: {chat_name} (ID: {chat.id})[/blue]\n"
                    f"[white]📝 Message: {message_text}[/white]\n"
                )
                
                # Add summary to log if available
                if summary:
                    summary_preview = summary[:150] + ('...' if len(summary) > 150 else '')
                    log_message += f"[green]🤖 Summary: {summary_preview}[/green]\n"
                
                self.log_to_gui(log_message)
                
            except Exception as e:
                logger.error(f"❌ Error handling message: {e}")
                self.log_to_gui(f"[red]❌ Error handling message: {e}[/red]")
                
        self.log_to_gui(f"[green]📡 Monitoring started for {len(self.monitored_channels)} channels[/green]")
        
        # Keep monitoring running
        self.running = True
        
        # Start hourly message processing task
        self.hourly_task = asyncio.create_task(self.process_hourly_messages())
        logger.info("Started hourly message processing task")
        
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Monitoring task cancelled")
        finally:
            # Cancel hourly task if it's running
            if self.hourly_task and not self.hourly_task.done():
                self.hourly_task.cancel()
                try:
                    await self.hourly_task
                except asyncio.CancelledError:
                    logger.info("Hourly processing task cancelled")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        
        # Cancel hourly task if it exists
        if self.hourly_task and not self.hourly_task.done():
            self.hourly_task.cancel()
            logger.info("Cancelled hourly processing task")
    
    def update_channels(self, channels: List[int]):
        """Update monitored channels"""
        self.monitored_channels = channels
    
    async def process_hourly_messages(self):
        """Process messages from database every hour - log them and remove them"""
        while self.running:
            try:
                # Wait for one hour (3600 seconds)
                await asyncio.sleep(3600)
                
                if not self.running:
                    break
                
                # Fetch all incoming messages from database
                messages = self.db_client.get_all_incoming_messages()
                
                if messages:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Log summary
                    summary_message = f"[green]📊 [{timestamp}] Hourly Message Summary - Processing {len(messages)} messages[/green]"
                    self.log_to_gui(summary_message)
                    logger.info(f"Processing {len(messages)} messages from database")
                    
                    # Log each message
                    for i, msg in enumerate(messages, 1):
                        log_entry = (
                            f"[cyan]📨 Message {i}/{len(messages)}[/cyan]\n"
                            f"[yellow]👤 From: {msg.get('sender_name', 'Unknown')}[/yellow]\n"
                            f"[blue]💬 Chat: {msg.get('chat_name', 'Unknown')} (ID: {msg.get('chat_id', 'Unknown')})[/blue]\n"
                            f"[white]📝 Message: {msg.get('message_text', '[No text]')[:200]}{'...' if len(msg.get('message_text', '')) > 200 else ''}[/white]\n"
                            f"[dim]🕒 Received: {msg.get('timestamp', 'Unknown')}[/dim]\n"
                        )
                        
                        # Add summary if available
                        if msg.get('llm_summary'):
                            summary_preview = msg['llm_summary'][:150] + ('...' if len(msg['llm_summary']) > 150 else '')
                            log_entry += f"[green]🤖 Summary: {summary_preview}[/green]\n"
                        
                        # Log to both GUI and file
                        self.log_to_gui(log_entry)
                        logger.info(f"Message from {msg.get('sender_name')} in {msg.get('chat_name')}: {msg.get('message_text', '')[:100]}")
                    
                    # Clear messages from database
                    if self.db_client.clear_incoming_messages():
                        completion_message = f"[green]✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Successfully processed and cleared {len(messages)} messages[/green]"
                        self.log_to_gui(completion_message)
                        logger.info(f"Successfully processed and cleared {len(messages)} messages from database")
                    else:
                        error_message = f"[red]❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to clear messages from database[/red]"
                        self.log_to_gui(error_message)
                        logger.error("Failed to clear messages from database")
                else:
                    # No messages to process
                    logger.debug("No messages to process in hourly check")
                    
            except asyncio.CancelledError:
                logger.info("Hourly message processing task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in hourly message processing: {e}")
                error_message = f"[red]❌ Error in hourly processing: {e}[/red]"
                self.log_to_gui(error_message)
