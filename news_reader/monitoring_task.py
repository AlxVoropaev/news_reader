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
from news_reader.message_utils import get_sender_name, get_current_timestamp, format_message_for_display, create_telegram_message_link

logger = get_logger(__name__)

class MonitoringTask:
    def __init__(self, client: TelegramClient, monitored_channels: List[int]):
        self.client = client
        self.monitored_channels = monitored_channels
        self.running = False
        self.db_client = get_db_client()  # Database client for saving messages
        self.llm_service = get_llm_service()  # LLM service for message summarization
        self.channel_sender = get_channel_sender(client)  # Channel sender for SINK_CHANNEL
    
    
    async def _process_message_by_algorithm(self, message_data: dict, message_text: str) -> None:
        """
        Process message according to the specified algorithm:
        1. Classify the post type using LLM and classify.txt prompt
        2. If SUMMARY type - forward as is to sink channel
        3. If INTERESTING - send summary to sink channel. If small (< 30 chars) - forward as is
        4. If REST - do nothing
        """
        if not message_text or len(message_text.strip()) == 0:
            logger.warning("Empty message - skipping processing")
            return
        
        sender_name = get_sender_name(message_data)
        
        # Step 1: Classify the post type
        classification = None
        if self.llm_service.is_available():
            try:
                classification = await self.llm_service.classify_message(message_text)
                if classification:
                    logger.info(f"Classified message from {sender_name} as: {classification}")
                    message_data['classification'] = classification
                    message_data['classification_generated_at'] = get_current_timestamp()
                else:
                    logger.warning(f"Failed to classify message from {sender_name}")
                    classification = "REST"  # Default to REST if classification fails
            except Exception as e:
                logger.error(f"Error classifying message: {e}")
                classification = "REST"  # Default to REST on error
        else:
            logger.warning("LLM service not available - defaulting to REST")
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
        sender_name = get_sender_name(message_data)
        
        if not self.channel_sender or not self.channel_sender.is_configured():
            logger.warning("SINK_CHANNEL not configured - cannot forward SUMMARY post")
            return
        
        try:
            sent_successfully = await self.channel_sender.forward_message_to_sink_channel(message_text, message_data)
            if sent_successfully:
                logger.info(f"Successfully forwarded SUMMARY post from {sender_name} to SINK_CHANNEL")
            else:
                logger.warning(f"Failed to forward SUMMARY post from {sender_name}")
        except Exception as e:
            logger.error(f"Error forwarding SUMMARY post: {e}")
    
    async def _handle_interesting_post(self, message_data: dict, message_text: str) -> None:
        """Handle INTERESTING type posts - summarize or forward if small (< 30 chars)"""
        sender_name = get_sender_name(message_data)
        
        if not self.channel_sender or not self.channel_sender.is_configured():
            logger.warning("SINK_CHANNEL not configured - cannot process INTERESTING post")
            return
        
        # Check if message is small (less than 30 characters)
        if len(message_text.strip()) < 30:
            # Forward as is
            try:
                sent_successfully = await self.channel_sender.forward_message_to_sink_channel(message_text, message_data)
                if sent_successfully:
                    logger.info(f"Successfully forwarded small INTERESTING post from {sender_name} to SINK_CHANNEL")
                else:
                    logger.warning(f"Failed to forward small INTERESTING post from {sender_name}")
            except Exception as e:
                logger.error(f"Error forwarding small INTERESTING post: {e}")
        else:
            # Generate summary and send it
            if self.llm_service.is_available():
                try:
                    summary = await self.llm_service.summarize_message(message_data)
                    if summary:
                        message_data['llm_summary'] = summary
                        message_data['summary_generated_at'] = get_current_timestamp()
                        logger.info(f"Generated summary for INTERESTING post from {sender_name}")
                        
                        # Send summary to SINK_CHANNEL
                        sent_successfully = await self.channel_sender.send_summary_to_sink_channel(summary, message_data)
                        if sent_successfully:
                            logger.info(f"Successfully sent INTERESTING post summary from {sender_name} to SINK_CHANNEL")
                        else:
                            logger.warning(f"Failed to send INTERESTING post summary from {sender_name}")
                    else:
                        logger.warning(f"Failed to generate summary for INTERESTING post from {sender_name}")
                except Exception as e:
                    logger.error(f"Error processing INTERESTING post: {e}")
            else:
                logger.warning("LLM service not available - cannot summarize INTERESTING post")
    
    async def _handle_rest_post(self, message_data: dict) -> None:
        """Handle REST type posts - do nothing"""
        sender_name = get_sender_name(message_data)
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
                    logger.info(f"SINK_CHANNEL test successful: {message}")
                else:
                    logger.warning(f"SINK_CHANNEL test failed: {message}")
            except Exception as e:
                logger.error(f"Error testing SINK_CHANNEL: {e}")
        else:
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
                message_text = format_message_for_display(event.text)
                
                # Create message link
                message_link = create_telegram_message_link(chat.id, event.id)
                
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
                
                logger.info(f"New message from {sender_name} in {chat_name}: {message_text}")
                
            except Exception as e:
                logger.error(f"❌ Error handling message: {e}")
                
        logger.info(f"Monitoring started for {len(self.monitored_channels)} channels")
        
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
    
