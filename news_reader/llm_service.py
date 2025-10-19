#!/usr/bin/env python3
"""
LLM Service - Handles OpenAI API integration for message summarization
"""

import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI
from news_reader.logging_config import get_logger
from news_reader.config import Config

logger = get_logger(__name__)

class LLMService:
    """Service for handling LLM operations using OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize LLM service with OpenAI configuration"""
        self.api_key = api_key if api_key is not None else Config.LLM_API_KEY
        self.model_name = model_name if model_name is not None else (Config.LLM_MODEL_NAME or "gpt-3.5-turbo")
        self.base_url = base_url if base_url is not None else Config.LLM_ENDPOINT_URL
        
        if not self.api_key or self.api_key.strip() == '':
            logger.warning("OpenAI API key not provided. LLM processing will be disabled.")
            logger.warning(f"API Key: {'✗'}, Model: {self.model_name}")
            self.client = None
        else:
            # Initialize OpenAI client
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
                logger.info(f"OpenAI service initialized with custom endpoint - Base URL: {self.base_url}, Model: {self.model_name}")
            else:
                logger.info(f"OpenAI service initialized - Model: {self.model_name}")
            
            self.client = AsyncOpenAI(**client_kwargs)
        
        # Load summarization prompt
        self.prompt_template = self._load_prompt_template()
        
        # Load classification prompt
        self.classify_prompt_template = self._load_classify_prompt_template()
    
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
    
    def _load_classify_prompt_template(self) -> str:
        """Load the classification prompt template from file"""
        try:
            prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts', 'classify.txt')
            
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    template = f.read().strip()
                logger.info("Loaded classification prompt template")
                return template
            else:
                logger.error(f"Classification prompt template not found at {prompt_path}")
                raise FileNotFoundError(f"Required classification prompt template not found at {prompt_path}")
                
        except Exception as e:
            logger.error(f"Failed to load classification prompt template: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if LLM service is available (has valid configuration)"""
        return self.client is not None and bool(self.api_key)
    
    
    async def summarize_message(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Summarize a message using OpenAI API
        
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
                timestamp=message_data.get('timestamp', 'Unknown'),
                message_link=message_data.get('message_link', '')
            )
            
            # Make the API request using OpenAI client
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful news summarization assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
                timeout=60.0  # 60 second timeout
            )
            
            # Extract summary from response
            if response.choices and len(response.choices) > 0:
                summary = response.choices[0].message.content.strip()
                
                logger.info(f"Successfully generated summary for message from {message_data.get('sender_name', 'Unknown')}")
                logger.debug(f"Summary: {summary[:100]}...")
                
                return summary
            else:
                logger.error("No choices returned in OpenAI response")
                return None
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None
    
    async def classify_message(self, message_text: str) -> Optional[str]:
        """
        Classify a message using OpenAI API
        
        Args:
            message_text: The text content to classify
        
        Returns:
            Classification string ("SUMMARY", "INTERESTING", or "REST") or None if processing failed
        """
        if not self.is_available():
            logger.warning("LLM service not available - skipping classification")
            return None
        
        if not message_text or len(message_text.strip()) == 0:
            logger.warning("Empty message text - skipping classification")
            return "REST"
        
        try:
            # Prepare the prompt with message text
            prompt = self.classify_prompt_template + "\n" + message_text
            
            # Make the API request using OpenAI client
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a text classifier. Respond with only one word: SUMMARY, INTERESTING, or REST."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.0,  # Use 0 temperature for consistent classification
                timeout=30.0  # 30 second timeout for classification
            )
            
            # Extract classification from response
            if response.choices and len(response.choices) > 0:
                classification = response.choices[0].message.content.strip().upper()
                
                # Validate classification result
                valid_classifications = ["SUMMARY", "INTERESTING", "REST"]
                if classification in valid_classifications:
                    logger.info(f"Successfully classified message as: {classification}")
                    return classification
                else:
                    logger.warning(f"Invalid classification result: {classification}, defaulting to REST")
                    return "REST"
            else:
                logger.error("No choices returned in OpenAI classification response")
                return "REST"
            
        except Exception as e:
            logger.error(f"Failed to classify message: {e}")
            return "REST"  # Default to REST on error
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources"""
        if self.client:
            await self.client.close()


# Global instance
_llm_service = None

def get_llm_service(api_key: Optional[str] = None, model_name: Optional[str] = None, base_url: Optional[str] = None) -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(api_key, model_name, base_url)
    return _llm_service