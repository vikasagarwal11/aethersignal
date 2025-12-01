"""
OpenAI Client - Wrapper for OpenAI API calls
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for OpenAI API."""
    
    @staticmethod
    def is_available() -> bool:
        """
        Check if OpenAI API is available.
        
        Returns:
            True if API key is set
        """
        return bool(os.getenv("OPENAI_API_KEY", ""))
    
    @staticmethod
    def run(prompt: str, model: str = "gpt-4o-mini", **kwargs) -> Optional[str]:
        """
        Run a prompt through OpenAI API.
        
        Args:
            prompt: Input prompt
            model: Model to use
            **kwargs: Additional parameters
        
        Returns:
            Response text or None if failed
        """
        if not OpenAIClient.is_available():
            logger.warning("OpenAI API key not set")
            return None
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a pharmacovigilance expert assistant."},
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    @staticmethod
    def embed(text: str, model: str = "text-embedding-3-small") -> Optional[list]:
        """
        Generate embeddings using OpenAI.
        
        Args:
            text: Text to embed
            model: Embedding model
        
        Returns:
            Embedding vector or None if failed
        """
        if not OpenAIClient.is_available():
            return None
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return None

