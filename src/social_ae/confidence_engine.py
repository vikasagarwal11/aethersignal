"""
Confidence Scoring Engine v2.0
Hybrid system for calculating confidence scores for extracted reactions.
"""

import re
from typing import List, Optional


def base_confidence(
    regex_reactions: List[str],
    emoji_reactions: List[str],
    llm_used: bool
) -> float:
    """
    Calculate base confidence from extraction method.
    
    Args:
        regex_reactions: Reactions found via regex
        emoji_reactions: Reactions found via emoji
        llm_used: Whether LLM was used
    
    Returns:
        Base confidence score (0.0-0.6)
    """
    score = 0.0
    
    # Emoji reactions are high confidence
    if emoji_reactions:
        score += 0.3
    
    # Regex reactions are high confidence
    if regex_reactions:
        score += 0.3
    
    # LLM-only extraction is lower confidence
    if llm_used and not (emoji_reactions or regex_reactions):
        return 0.4
    
    return min(score, 0.6)


def drug_context_boost(text: str, drug: str) -> float:
    """
    Boost confidence if drug is explicitly mentioned.
    
    Args:
        text: Post text
        drug: Drug name
    
    Returns:
        Boost score (0.0-0.1)
    """
    if not drug:
        return 0.0
    
    text_lower = text.lower()
    drug_lower = drug.lower()
    
    # Check for exact drug name
    if drug_lower in text_lower:
        return 0.1
    
    # Check for common drug name variations
    drug_words = drug_lower.split()
    if len(drug_words) > 0:
        if drug_words[0] in text_lower:
            return 0.05
    
    return 0.0


def multi_reaction_boost(reactions: List[str]) -> float:
    """
    Boost confidence if multiple reactions are detected.
    
    Args:
        reactions: List of reactions
    
    Returns:
        Boost score (0.0-0.1)
    """
    if len(reactions) >= 2:
        return 0.1
    return 0.0


def severity_boost(severity: str) -> float:
    """
    Boost confidence based on severity indicators.
    
    Args:
        severity: Severity label
    
    Returns:
        Boost score (0.0-0.1)
    """
    if severity == "severe":
        return 0.1
    if severity == "moderate":
        return 0.05
    return 0.0


def pattern_strength_boost(text: str, reactions: List[str]) -> float:
    """
    Boost confidence based on pattern match strength.
    
    Args:
        text: Post text
        reactions: Detected reactions
    
    Returns:
        Boost score (0.0-0.1)
    """
    if not reactions:
        return 0.0
    
    text_lower = text.lower()
    boost = 0.0
    
    # Check for explicit reaction mentions
    for reaction in reactions:
        reaction_lower = reaction.lower()
        # Exact match
        if f" {reaction_lower} " in f" {text_lower} ":
            boost += 0.02
        # Partial match
        elif reaction_lower in text_lower:
            boost += 0.01
    
    return min(boost, 0.1)


def final_confidence(
    text: str,
    reactions: List[str],
    regex_rx: List[str],
    emoji_rx: List[str],
    severity: str,
    drug: str,
    llm_used: bool
) -> float:
    """
    Calculate final confidence score combining all factors.
    
    Args:
        text: Post text
        reactions: All detected reactions
        regex_rx: Reactions found via regex
        emoji_rx: Reactions found via emoji
        severity: Severity label
        drug: Drug name
        llm_used: Whether LLM was used
    
    Returns:
        Final confidence score (0.0-1.0)
    """
    score = 0.0
    
    # Base confidence from extraction method
    score += base_confidence(regex_rx, emoji_rx, llm_used)
    
    # Context boosts
    score += drug_context_boost(text, drug)
    score += multi_reaction_boost(reactions)
    score += severity_boost(severity)
    score += pattern_strength_boost(text, reactions)
    
    # Clamp to [0.0, 1.0]
    return round(min(score, 1.0), 2)

