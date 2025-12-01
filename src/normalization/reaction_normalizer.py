"""
Reaction Normalizer - Unified normalization engine.
REUSES existing map_to_meddra_pt and extends with fuzzy matching, semantic similarity, and LLM.
"""

import re
from typing import Optional, List, Dict, Tuple
import logging

from .reaction_dictionary import (
    REACTION_DICTIONARY, get_reaction_pt, get_reaction_category,
    get_all_pts, get_synonyms
)
from src.utils import map_to_meddra_pt
from src.social_ae.social_mapper import EMOJI_AE_MAP

logger = logging.getLogger(__name__)

# Try to import fuzzy matching
try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logger.warning("rapidfuzz not available, fuzzy matching disabled")


class ReactionNormalizer:
    """
    Unified reaction normalizer that combines:
    - Emoji lookup
    - Dictionary/synonym matching
    - Pattern matching
    - Fuzzy matching
    - Semantic similarity (via embeddings)
    - LLM fallback
    """
    
    def __init__(self, embedding_engine=None, use_llm: bool = False):
        """
        Initialize reaction normalizer.
        
        Args:
            embedding_engine: Optional embedding engine for semantic matching
            use_llm: Whether to use LLM for normalization
        """
        self.embedding_engine = embedding_engine
        self.use_llm = use_llm
    
    def normalize(self, text: str, drug: Optional[str] = None) -> Dict[str, any]:
        """
        Normalize reaction text to Preferred Term.
        
        Args:
            text: Reaction text to normalize
            drug: Optional drug name for context
        
        Returns:
            Dictionary with:
            - pt: Preferred Term
            - category: Category name
            - method: How it was matched (emoji, synonym, pattern, fuzzy, semantic, llm, none)
            - confidence: Confidence score (0.0-1.0)
        """
        if not text or not isinstance(text, str):
            return {
                "pt": text or "",
                "category": "Other",
                "method": "none",
                "confidence": 0.0
            }
        
        text_lower = text.lower().strip()
        
        # Step 1: Emoji lookup
        pt, method = self._emoji_lookup(text)
        if pt:
            category = get_reaction_category(pt)
            return {
                "pt": pt,
                "category": category,
                "method": "emoji",
                "confidence": 0.9
            }
        
        # Step 2: Direct dictionary/synonym match
        pt, method = self._synonym_lookup(text_lower)
        if pt:
            category = get_reaction_category(pt)
            return {
                "pt": pt,
                "category": category,
                "method": "synonym",
                "confidence": 0.85
            }
        
        # Step 3: Pattern matching
        pt, method = self._pattern_match(text_lower)
        if pt:
            category = get_reaction_category(pt)
            return {
                "pt": pt,
                "category": category,
                "method": "pattern",
                "confidence": 0.75
            }
        
        # Step 4: REUSE existing map_to_meddra_pt
        pt = map_to_meddra_pt(text)
        if pt and pt.lower() != text_lower:
            category = get_reaction_category(pt)
            return {
                "pt": pt,
                "category": category,
                "method": "meddra_dict",
                "confidence": 0.7
            }
        
        # Step 5: Fuzzy matching
        if FUZZY_AVAILABLE:
            pt, score = self._fuzzy_match(text_lower)
            if pt and score >= 80:
                category = get_reaction_category(pt)
                return {
                    "pt": pt,
                    "category": category,
                    "method": "fuzzy",
                    "confidence": score / 100.0
                }
        
        # Step 6: Semantic similarity (if embedding engine available)
        if self.embedding_engine:
            pt, similarity = self._semantic_match(text, drug)
            if pt and similarity >= 0.7:
                category = get_reaction_category(pt)
                return {
                    "pt": pt,
                    "category": category,
                    "method": "semantic",
                    "confidence": similarity
                }
        
        # Step 7: LLM fallback (optional, expensive)
        if self.use_llm:
            pt = self._llm_reasoner(text, drug)
            if pt:
                category = get_reaction_category(pt)
                return {
                    "pt": pt,
                    "category": category,
                    "method": "llm",
                    "confidence": 0.6
                }
        
        # Step 8: No match - return original
        return {
            "pt": text.title(),
            "category": "Other",
            "method": "none",
            "confidence": 0.0
        }
    
    def _emoji_lookup(self, text: str) -> Tuple[Optional[str], str]:
        """Lookup reaction via emoji."""
        for char in text:
            if char in EMOJI_AE_MAP:
                reaction = EMOJI_AE_MAP[char]
                pt = get_reaction_pt(reaction)
                if pt:
                    return pt, "emoji"
        return None, ""
    
    def _synonym_lookup(self, text_lower: str) -> Tuple[Optional[str], str]:
        """Lookup reaction via synonym dictionary."""
        # Direct PT match
        for pt in get_all_pts():
            if pt.lower() == text_lower:
                return pt, "synonym"
        
        # Synonym match
        for pt, info in REACTION_DICTIONARY.items():
            for synonym in info["synonyms"]:
                if synonym.lower() == text_lower or synonym.lower() in text_lower:
                    return pt, "synonym"
        
        return None, ""
    
    def _pattern_match(self, text_lower: str) -> Tuple[Optional[str], str]:
        """Match reaction via regex patterns."""
        for pt, info in REACTION_DICTIONARY.items():
            for pattern in info["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return pt, "pattern"
        return None, ""
    
    def _fuzzy_match(self, text_lower: str) -> Tuple[Optional[str], float]:
        """Fuzzy match against all PTs."""
        if not FUZZY_AVAILABLE:
            return None, 0.0
        
        pt_list = get_all_pts()
        if not pt_list:
            return None, 0.0
        
        result = process.extractOne(text_lower, pt_list, scorer=fuzz.ratio)
        if result:
            pt, score, _ = result
            return pt, score
        return None, 0.0
    
    def _semantic_match(self, text: str, drug: Optional[str] = None) -> Tuple[Optional[str], float]:
        """Semantic match using embeddings."""
        if not self.embedding_engine:
            return None, 0.0
        
        try:
            # Get embedding for text
            embedding = self.embedding_engine.embed(text)
            if embedding is None:
                return None, 0.0
            
            # Find similar reactions (would need vector store - implemented in next step)
            # For now, return None
            return None, 0.0
        except Exception as e:
            logger.debug(f"Semantic match error: {str(e)}")
            return None, 0.0
    
    def _llm_reasoner(self, text: str, drug: Optional[str] = None) -> Optional[str]:
        """Use LLM to suggest PT (expensive, use sparingly)."""
        try:
            import openai
            import os
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return None
            
            prompt = f"""Given this patient description: "{text}"
{f"Drug: {drug}" if drug else ""}

Suggest the best pharmacovigilance Preferred Term (PT).
Return ONLY the PT name, nothing else."""
            
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            pt = response.choices[0].message.content.strip()
            # Validate it's a reasonable PT
            if pt and len(pt) < 100:
                return pt
            
            return None
        except Exception as e:
            logger.debug(f"LLM reasoner error: {str(e)}")
            return None

