"""
Groq Client - Wrapper for Groq API calls (fast inference)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for Groq API (fast inference)."""
    
    @staticmethod
    def is_available() -> bool:
        """
        Check if Groq API is available.
        
        Returns:
            True if API key is set
        """
        return bool(os.getenv("GROQ_API_KEY", ""))
    
    @staticmethod
    def run(prompt: str, model: str = "llama-3.1-8b-instant", **kwargs) -> Optional[str]:
        """
        Run a prompt through Groq API.
        
        Args:
            prompt: Input prompt
            model: Model to use
            **kwargs: Additional parameters
        
        Returns:
            Response text or None if failed
        """
        if not GroqClient.is_available():
            logger.warning("Groq API key not set")
            return None
        
        try:
            from groq import Groq
            
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            
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
            logger.error(f"Groq API error: {e}")
            return None

