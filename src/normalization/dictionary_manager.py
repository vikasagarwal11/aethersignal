"""
Dictionary Manager - Manages the global reaction dictionary.
Handles adding new PTs, synonyms, patterns, and admin approval workflow.
"""

import pandas as pd
from typing import List, Dict, Optional
import logging

from .reaction_dictionary import (
    REACTION_DICTIONARY, add_reaction_entry, get_reaction_pt,
    get_reaction_category, get_all_pts
)

logger = logging.getLogger(__name__)

# Try to import Supabase
try:
    from supabase import create_client
    import os
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class DictionaryManager:
    """
    Manages the global reaction dictionary with database persistence.
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialize dictionary manager.
        
        Args:
            supabase_client: Optional Supabase client
        """
        self.supabase = supabase_client
        self._load_from_db()
    
    def _load_from_db(self):
        """Load dictionary from database if available."""
        if not self.supabase or not SUPABASE_AVAILABLE:
            return
        
        try:
            response = self.supabase.table("reaction_dictionary").select("*").execute()
            
            for row in response.data:
                pt = row.get("pt")
                if pt:
                    add_reaction_entry(
                        pt=pt,
                        synonyms=row.get("synonyms", []),
                        category=row.get("category", "Other"),
                        patterns=row.get("patterns", []),
                        emoji=row.get("emoji", [])
                    )
        except Exception as e:
            logger.warning(f"Error loading dictionary from DB: {str(e)}")
    
    def add_pt(
        self,
        pt: str,
        synonyms: List[str] = None,
        category: str = "Other",
        patterns: List[str] = None,
        emoji: List[str] = None,
        llm_notes: Optional[str] = None
    ) -> bool:
        """
        Add a new Preferred Term to the dictionary.
        
        Args:
            pt: Preferred Term
            synonyms: List of synonyms
            category: Category name
            patterns: List of regex patterns
            emoji: List of emoji characters
            llm_notes: Optional LLM justification
        
        Returns:
            True if successful
        """
        try:
            # Add to in-memory dictionary
            add_reaction_entry(pt, synonyms, category, patterns, emoji)
            
            # Save to database if available
            if self.supabase and SUPABASE_AVAILABLE:
                self.supabase.table("reaction_dictionary").upsert({
                    "pt": pt,
                    "synonyms": synonyms or [],
                    "patterns": patterns or [],
                    "emoji": emoji or [],
                    "category": category,
                    "llm_notes": llm_notes
                }).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error adding PT: {str(e)}")
            return False
    
    def get_suggested_pts(self, min_count: int = 5) -> pd.DataFrame:
        """
        Get suggested new PTs from emerging reactions.
        
        Args:
            min_count: Minimum occurrence count
        
        Returns:
            DataFrame with suggested PTs
        """
        # This would query the reaction_vectors table for reactions
        # that appear frequently but aren't in dictionary
        # For now, return empty - will be populated by discovery engine
        return pd.DataFrame()
    
    def merge_pt(self, source_pt: str, target_pt: str) -> bool:
        """
        Merge one PT into another (consolidation).
        
        Args:
            source_pt: PT to merge from
            target_pt: PT to merge into
        
        Returns:
            True if successful
        """
        try:
            if source_pt not in REACTION_DICTIONARY or target_pt not in REACTION_DICTIONARY:
                return False
            
            # Merge synonyms, patterns, emoji
            source_info = REACTION_DICTIONARY[source_pt]
            target_info = REACTION_DICTIONARY[target_pt]
            
            target_info["synonyms"].extend(source_info["synonyms"])
            target_info["synonyms"] = list(set(target_info["synonyms"]))
            
            target_info["patterns"].extend(source_info["patterns"])
            target_info["patterns"] = list(set(target_info["patterns"]))
            
            target_info["emoji"].extend(source_info["emoji"])
            target_info["emoji"] = list(set(target_info["emoji"]))
            
            # Remove source PT
            del REACTION_DICTIONARY[source_pt]
            
            # Update database
            if self.supabase and SUPABASE_AVAILABLE:
                # Update target
                self.supabase.table("reaction_dictionary").update({
                    "synonyms": target_info["synonyms"],
                    "patterns": target_info["patterns"],
                    "emoji": target_info["emoji"]
                }).eq("pt", target_pt).execute()
                
                # Delete source
                self.supabase.table("reaction_dictionary").delete().eq("pt", source_pt).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error merging PTs: {str(e)}")
            return False
    
    def get_dictionary_stats(self) -> Dict:
        """Get statistics about the dictionary."""
        return {
            "total_pts": len(REACTION_DICTIONARY),
            "total_synonyms": sum(len(info["synonyms"]) for info in REACTION_DICTIONARY.values()),
            "total_patterns": sum(len(info["patterns"]) for info in REACTION_DICTIONARY.values()),
            "total_emoji": sum(len(info["emoji"]) for info in REACTION_DICTIONARY.values()),
            "categories": {
                cat: sum(1 for info in REACTION_DICTIONARY.values() if info["category"] == cat)
                for cat in set(info["category"] for info in REACTION_DICTIONARY.values())
            }
        }

