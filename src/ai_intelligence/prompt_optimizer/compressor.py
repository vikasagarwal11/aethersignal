"""
Prompt Compressor - Reduces prompt size for faster inference
"""

import re
import logging
from typing import str

logger = logging.getLogger(__name__)


def compress_prompt(prompt: str, max_length: int = 2000) -> str:
    """
    Compress prompt by removing unnecessary content.
    
    Args:
        prompt: Input prompt
        max_length: Maximum prompt length
    
    Returns:
        Compressed prompt
    """
    if len(prompt) <= max_length:
        return prompt
    
    lines = prompt.split("\n")
    cleaned = []
    
    for line in lines:
        # Skip empty lines
        if len(line.strip()) == 0:
            continue
        
        # Skip very long lines that look like data dumps
        if len(line) > 300 and any(x in line.lower() for x in ["table", "json", "data", "array"]):
            # Try to summarize instead
            if "json" in line.lower():
                cleaned.append("[JSON data truncated]")
            elif "table" in line.lower():
                cleaned.append("[Table data truncated]")
            continue
        
        cleaned.append(line)
    
    compressed = "\n".join(cleaned)
    
    # If still too long, truncate intelligently
    if len(compressed) > max_length:
        # Keep first part (usually instructions) and last part (usually query)
        first_part = compressed[:max_length // 2]
        last_part = compressed[-max_length // 2:]
        compressed = f"{first_part}\n[... truncated ...]\n{last_part}"
    
    return compressed


def optimize_prompt(prompt: str) -> str:
    """
    Optimize prompt for better LLM performance.
    
    Args:
        prompt: Input prompt
    
    Returns:
        Optimized prompt
    """
    # Remove excessive whitespace
    prompt = re.sub(r'\n{3,}', '\n\n', prompt)
    prompt = re.sub(r' {2,}', ' ', prompt)
    
    # Remove redundant phrases
    redundant_phrases = [
        r"please note that",
        r"it is important to",
        r"i would like to",
        r"could you please",
    ]
    
    for phrase in redundant_phrases:
        prompt = re.sub(phrase, "", prompt, flags=re.IGNORECASE)
    
    # Compress if needed
    prompt = compress_prompt(prompt)
    
    return prompt.strip()

