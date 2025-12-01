"""
Multi-AE Extraction Engine
Unified engine for extracting multiple adverse reactions from social media posts.
REUSES existing components from social_mapper and adds LLM fallback + unified severity/confidence.
"""

import re
from typing import List, Dict, Optional, Tuple
import logging

# Reuse existing components
from .social_mapper import (
    extract_emoji_reactions,
    extract_multiple_reactions,
    _is_negated
)
from .social_severity import classify_severity_from_text, severity_score_from_label
from .confidence_engine import final_confidence

logger = logging.getLogger(__name__)


def extract_reactions_llm(text: str, drug: Optional[str] = None) -> List[str]:
    """
    Use LLM to extract reactions (fallback when regex+emoji fails).
    
    Args:
        text: Text to analyze
        drug: Optional drug name for context
    
    Returns:
        List of reactions found via LLM
    """
    try:
        import openai
    except ImportError:
        logger.warning("OpenAI not available, skipping LLM extraction")
        return []
    
    # Check if API key is available
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.debug("OpenAI API key not found, skipping LLM extraction")
        return []
    
    try:
        prompt = f"""Extract all adverse reactions/side effects from this social media post.
Return ONLY a Python list of reaction terms, lowercase, simple medical terms.
Do not include explanations or other text.

Post: "{text}"
{f"Drug: {drug}" if drug else ""}

Reactions:"""
        
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to parse as Python list
        try:
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("python"):
                    content = content[6:]
            content = content.strip()
            
            # Try eval (safe for simple lists)
            if content.startswith("[") and content.endswith("]"):
                reactions = eval(content)
                if isinstance(reactions, list):
                    return [str(r).lower().strip() for r in reactions if r]
        except Exception as e:
            logger.debug(f"Failed to parse LLM response: {e}")
            # Fallback: try to extract terms from text
            reactions = []
            for line in content.split("\n"):
                line = line.strip().strip("-").strip("*").strip()
                if line and len(line) < 50:  # Reasonable reaction term length
                    reactions.append(line.lower())
            return reactions[:5]  # Limit to 5 reactions
        
        return []
    except Exception as e:
        logger.warning(f"LLM extraction error: {str(e)}")
        return []


def extract_all_reactions(
    text: str,
    drug: Optional[str] = None,
    use_llm: bool = True
) -> Dict:
    """
    Master extractor: REUSES existing extract_multiple_reactions() and adds LLM fallback + unified scoring.
    
    This function wraps the existing social_mapper.extract_multiple_reactions() and adds:
    - LLM fallback when no reactions found
    - Unified severity classification
    - Unified confidence scoring v2.0
    
    Args:
        text: Text to analyze
        drug: Optional drug name for context
        use_llm: Whether to use LLM fallback if regex+emoji finds nothing
    
    Returns:
        Dictionary with reactions, severity, and confidence
    """
    if not text or not isinstance(text, str):
        return {
            "reactions": [],
            "severity_label": "unknown",
            "severity_score": 0.1,
            "confidence": 0.0,
            "llm_used": False
        }
    
    # Step 1: REUSE existing extract_multiple_reactions (handles emoji + regex + slang + negation)
    # This already does emoji extraction, slang mapping, pattern matching, and negation detection
    reactions_with_conf = extract_multiple_reactions(text, return_confidence=True)
    
    # Separate reactions and their individual confidences
    reactions = [r[0] for r in reactions_with_conf] if reactions_with_conf else []
    reaction_confidences = [r[1] for r in reactions_with_conf] if reactions_with_conf else []
    
    # Step 2: Extract emoji and regex separately for confidence calculation
    # (needed for confidence_engine which needs to know source of each reaction)
    emoji_rx = extract_emoji_reactions(text)
    text_lower = text.lower()
    
    # Get regex-based reactions (from existing extract_multiple_reactions logic)
    # We can infer this by checking which reactions came from emoji vs regex
    regex_rx = [r for r in reactions if r not in emoji_rx]
    
    # Step 3: LLM fallback if nothing found
    llm_used = False
    if len(reactions) == 0 and use_llm:
        llm_rx = extract_reactions_llm(text, drug)
        if llm_rx:
            reactions = llm_rx
            regex_rx = []  # LLM reactions are not regex-based
            llm_used = True
    
    # Step 4: Classify severity (REUSES existing function)
    severity_label = classify_severity_from_text(text)
    sev_score = severity_score_from_label(severity_label)
    
    # Step 5: Calculate unified confidence (NEW - uses confidence_engine v2.0)
    conf_score = final_confidence(
        text=text,
        reactions=reactions,
        regex_rx=regex_rx,
        emoji_rx=emoji_rx,
        severity=severity_label,
        drug=drug or "",
        llm_used=llm_used
    )
    
    return {
        "reactions": reactions,
        "severity_label": severity_label,
        "severity_score": sev_score,
        "confidence": conf_score,
        "llm_used": llm_used
    }

