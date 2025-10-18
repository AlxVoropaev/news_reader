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
from news_reader.channel_sender import get_channel_sender
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
        self.channel_sender = get_channel_sender(client)  # Channel sender for SINK_CHANNEL
    
    def log_to_gui(self, message: str) -> None:
        """Send log message to GUI if available, otherwise use logger"""
        if self.gui_logger:
            try:
                self.gui_logger.add_log_message(message)
            except Exception as e:
                logger.error(f"Failed to send message to GUI: {e}")
        else:
            logger.info(message)
    
    async def _process_message_by_algorithm(self, message_data: dict, message_text: str) -> None:
        """
        Process message according to the specified algorithm:
        1. Classify the post type using LLM and classify.txt prompt
        2. If SUMMARY type - forward as is to sink channel
        3. If INTERESTING - send summary to sink channel. If small (< 30 chars) - forward as is
        4. If REST - do nothing
        """
        if not message_text or len(message_text.strip()) == 0:
            self.log_to_gui(f"[yellow]⚠️ Empty message - skipping processing[/yellow]")
            return
        
        sender_name = message_data.get('sender_name', 'Unknown')
        
        # Step 1: Classify the post type
        classification = None
        if self.llm_service.is_available():
            try:
                classification = await self.llm_service.classify_message(message_text)
                if classification:
                    self.log_to_gui(f"[cyan]🏷️ Classified message from {sender_name} as: {classification}[/cyan]")
                    message_data['classification'] = classification
                    message_data['classification_generated_at'] = datetime.now().isoformat()
                else:
                    self.log_to_gui(f"[yellow]⚠️ Failed to classify message from {sender_name}[/yellow]")
                    classification = "REST"  # Default to REST if classification fails
            except Exception as e:
                logger.error(f"Error classifying message: {e}")
                self.log_to_gui(f"[red]❌ Classification failed: {e}[/red]")
                classification = "REST"  # Default to REST on error
        else:
            self.log_to_gui(f"[yellow]⚠️ LLM service not available - defaulting to REST[/yellow]")
            classification = "REST"
        
        # Step 2-4: Process based on classification
        if classification == "SUMMARY":
            # Forward as is to sink channel
            await self._handle_summary_post(message_data, message_text)
        elif classification == "INTERESTING":
            # Send summary or forward if small
            await self._handle_interesting_post(message_data, message_text)
        else:  # REST
            # Do nothing
            await self._handle_rest_post(message_data)
    
    async def _handle_summary_post(self, message_data: dict, message_text: str) -> None:
        """Handle SUMMARY type posts - forward as is to sink channel"""
        sender_name = message_data.get('sender_name', 'Unknown')
        
        if not self.channel_sender or not self.channel_sender.is_configured():
            self.log_to_gui(f"[yellow]⚠️ SINK_CHANNEL not configured - cannot forward SUMMARY post[/yellow]")
            return
        
        try:
            sent_successfully = await self.channel_sender.forward_message_to_sink_channel(message_text, message_data)
            if sent_successfully:
                self.log_to_gui(f"[green]📤 Forwarded SUMMARY post from {sender_name} to SINK_CHANNEL[/green]")
                logger.info(f"Successfully forwarded SUMMARY post from {sender_name} to SINK_CHANNEL")
            else:
                self.log_to_gui(f"[yellow]⚠️ Failed to forward SUMMARY post from {sender_name}[/yellow]")
        except Exception as e:
            logger.error(f"Error forwarding SUMMARY post: {e}")
            self.log_to_gui(f"[red]❌ Error forwarding SUMMARY post: {e}[/red]")
    
    async def _handle_interesting_post(self, message_data: dict, message_text: str) -> None:
        """Handle INTERESTING type posts - summarize or forward if small (< 30 chars)"""
        sender_name = message_data.get('sender_name', 'Unknown')
        
        if not self.channel_sender or not self.channel_sender.is_configured():
            self.log_to_gui(f"[yellow]⚠️ SINK_CHANNEL not configured - cannot process INTERESTING post[/yellow]")
            return
        
        # Check if message is small (less than 30 characters)
        if len(message_text.strip()) < 30:
            # Forward as is
            try:
                sent_successfully = await self.channel_sender.forward_message_to_sink_channel(message_text, message_data)
                if sent_successfully:
                    self.log_to_gui(f"[green]📤 Forwarded small INTERESTING post from {sender_name} to SINK_CHANNEL[/green]")
                    logger.info(f"Successfully forwarded small INTERESTING post from {sender_name} to SINK_CHANNEL")
                else:
                    self.log_to_gui(f"[yellow]⚠️ Failed to forward small INTERESTING post from {sender_name}[/yellow]")
            except Exception as e:
                logger.error(f"Error forwarding small INTERESTING post: {e}")
                self.log_to_gui(f"[red]❌ Error forwarding small INTERESTING post: {e}[/red]")
        else:
            # Generate summary and send it
            if self.llm_service.is_available():
                try:
                    summary = await self.llm_service.summarize_message(message_data)
                    if summary:
                        message_data['llm_summary'] = summary
                        message_data['summary_generated_at'] = datetime.now().isoformat()
                        self.log_to_gui(f"[green]🤖 Generated summary for INTERESTING post from {sender_name}[/green]")
                        
                        # Send summary to SINK_CHANNEL
                        sent_successfully = await self.channel_sender.send_summary_to_sink_channel(summary, message_data)
                        if sent_successfully:
                            self.log_to_gui(f"[green]📤 Sent INTERESTING post summary from {sender_name} to SINK_CHANNEL[/green]")
                            logger.info(f"Successfully sent INTERESTING post summary from {sender_name} to SINK_CHANNEL")
                        else:
                            self.log_to_gui(f"[yellow]⚠️ Failed to send INTERESTING post summary from {sender_name}[/yellow]")
                    else:
                        self.log_to_gui(f"[yellow]⚠️ Failed to generate summary for INTERESTING post from {sender_name}[/yellow]")
                except Exception as e:
                    logger.error(f"Error processing INTERESTING post: {e}")
                    self.log_to_gui(f"[red]❌ Error processing INTERESTING post: {e}[/red]")
            else:
                self.log_to_gui(f"[yellow]⚠️ LLM service not available - cannot summarize INTERESTING post[/yellow]")
    
    async def _handle_rest_post(self, message_data: dict) -> None:
        """Handle REST type posts - do nothing"""
        sender_name = message_data.get('sender_name', 'Unknown')
        self.log_to_gui(f"[dim]🚫 REST post from {sender_name} - no action taken[/dim]")
        logger.debug(f"REST post from {sender_name} - no action taken")
    
    async def start(self):
        """Start monitoring for new messages"""
        if not self.monitored_channels:
            logger.info("No channels configured for monitoring")
            return
        
        logger.info(f"Starting monitoring for {len(self.monitored_channels)} channels")
        
        # Test SINK_CHANNEL configuration if enabled
        if self.channel_sender and self.channel_sender.is_configured():
            try:
                success, message = await self.channel_sender.test_sink_channel_access()
                if success:
                    self.log_to_gui(f"[green]✅ SINK_CHANNEL test successful: {message}[/green]")
                    logger.info(f"SINK_CHANNEL test successful: {message}")
                else:
                    self.log_to_gui(f"[red]❌ SINK_CHANNEL test failed: {message}[/red]")
                    logger.warning(f"SINK_CHANNEL test failed: {message}")
            except Exception as e:
                self.log_to_gui(f"[red]❌ Error testing SINK_CHANNEL: {e}[/red]")
                logger.error(f"Error testing SINK_CHANNEL: {e}")
        else:
            self.log_to_gui(f"[yellow]ℹ️ SINK_CHANNEL not configured - summaries will not be forwarded[/yellow]")
            logger.info("SINK_CHANNEL not configured - summaries will not be forwarded")
        
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
                
                # Create message link
                # For channels, use format: https://t.me/c/{chat_id_without_prefix}/{message_id}
                # Remove the -100 prefix from channel IDs for the link
                chat_id_for_link = str(chat.id)[4:] if str(chat.id).startswith('-100') else str(chat.id)
                message_link = f"https://t.me/c/{chat_id_for_link}/{event.id}"
                
                # Prepare message data
                message_data = {
                    'message_id': event.id,
                    'chat_id': chat.id,
                    'chat_name': chat_name,
                    'sender_id': sender.id if sender else None,
                    'sender_name': sender_name,
                    'message_text': event.text or '[No text]',
                    'timestamp': timestamp,
                    'message_link': message_link
                }
                
                # Process message according to the algorithm
                await self._process_message_by_algorithm(message_data, event.text or '')
                
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
        finally:
            pass
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        
    
    def update_channels(self, channels: List[int]):
        """Update monitored channels"""
        self.monitored_channels = channels
    
