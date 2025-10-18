#!/usr/bin/env python3
"""
LLM Service - Handles custom LLM API integration for message summarization
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
from news_reader.logging_config import get_logger
from news_reader.config import Config

logger = get_logger(__name__)

class LLMService:
    """Service for handling LLM operations using custom API endpoint"""
    
    def __init__(self, endpoint_url: Optional[str] = None, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize LLM service with custom endpoint configuration"""
        self.endpoint_url = endpoint_url or Config.LLM_ENDPOINT_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME
        self.api_key = api_key or Config.LLM_API_KEY
        
        if not all([self.endpoint_url, self.model_name, self.api_key]):
            logger.warning("Custom LLM configuration incomplete. LLM processing will be disabled.")
            logger.warning(f"Endpoint: {'✓' if self.endpoint_url else '✗'}, Model: {'✓' if self.model_name else '✗'}, API Key: {'✓' if self.api_key else '✗'}")
        else:
            logger.info(f"Custom LLM service initialized - Endpoint: {self.endpoint_url}, Model: {self.model_name}")
        
        # Load summarization prompt
        self.prompt_template = self._load_prompt_template()
        
        # HTTP session for reusing connections
        self.session = None
    
    def _load_prompt_template(self) -> str:
        """Load the summarization prompt template from file"""
        try:
            prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts', 'summary.txt')
            
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    template = f.read().strip()
                logger.info("Loaded summarization prompt template")
                return template
            else:
                logger.error(f"Prompt template not found at {prompt_path}")
                raise FileNotFoundError(f"Required prompt template not found at {prompt_path}")
                
        except Exception as e:
            logger.error(f"Failed to load prompt template: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if LLM service is available (has valid configuration)"""
        return all([self.endpoint_url, self.model_name, self.api_key])
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _close_session(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def summarize_message(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Summarize a message using custom LLM API
        
        Args:
            message_data: Dictionary containing message information
                - message_text: The text content to summarize
                - chat_name: Name of the channel/chat
                - sender_name: Name of the message sender
                - timestamp: When the message was received
        
        Returns:
            Summary string or None if processing failed
        """
        if not self.is_available():
            logger.warning("LLM service not available - skipping summarization")
            return None
        
        try:
            # Prepare the prompt with message data
            prompt = self.prompt_template.format(
                message_text=message_data.get('message_text', ''),
                channel_name=message_data.get('chat_name', 'Unknown'),
                sender_name=message_data.get('sender_name', 'Unknown'),
                timestamp=message_data.get('timestamp', 'Unknown')
            )
            
            # Prepare the request payload (OpenAI-compatible format)
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful news summarization assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.3
            }
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Make the API request
            session = await self._get_session()
            async with session.post(self.endpoint_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract summary from response (OpenAI-compatible format)
                    if 'choices' in result and len(result['choices']) > 0:
                        summary = result['choices'][0]['message']['content'].strip()
                        
                        logger.info(f"Successfully generated summary for message from {message_data.get('sender_name', 'Unknown')}")
                        logger.debug(f"Summary: {summary[:100]}...")
                        
                        return summary
                    else:
                        logger.error(f"Unexpected response format: {result}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"LLM API request failed with status {response.status}: {error_text}")
                    return None
            
        except asyncio.TimeoutError:
            logger.error("LLM API request timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None
    
    async def batch_summarize_messages(self, messages: list[Dict[str, Any]]) -> Dict[str, str]:
        """
        Summarize multiple messages in batch
        
        Args:
            messages: List of message data dictionaries
        
        Returns:
            Dictionary mapping message IDs to their summaries
        """
        if not self.is_available():
            logger.warning("LLM service not available - skipping batch summarization")
            return {}
        
        summaries = {}
        
        # Process messages with rate limiting (to avoid API limits)
        for i, message in enumerate(messages):
            try:
                message_id = str(message.get('message_id', f'unknown_{i}'))
                summary = await self.summarize_message(message)
                
                if summary:
                    summaries[message_id] = summary
                
                # Add small delay to avoid rate limiting
                if i < len(messages) - 1:  # Don't delay after the last message
                    await asyncio.sleep(0.5)  # 500ms delay between requests
                    
            except Exception as e:
                logger.error(f"Failed to summarize message {i}: {e}")
                continue
        
        logger.info(f"Successfully generated {len(summaries)} summaries out of {len(messages)} messages")
        return summaries
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup session"""
        await self._close_session()


# Global instance
_llm_service = None

def get_llm_service(endpoint_url: Optional[str] = None, model_name: Optional[str] = None, api_key: Optional[str] = None) -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(endpoint_url, model_name, api_key)
    return _llm_service