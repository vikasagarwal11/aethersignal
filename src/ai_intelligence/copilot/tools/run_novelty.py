"""
Novelty Tool - Detect novel signals
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class NoveltyTool:
    """Tool for novelty detection."""
    
    name = "novelty"
    description = "Detect if AE is a novel signal (not on label)"
    
    def run(self, drug: str, reaction: Optional[str] = None) -> Dict[str, Any]:
        """
        Run novelty detection.
        
        Args:
            drug: Drug name
            reaction: Optional specific reaction
        
        Returns:
            Novelty analysis dictionary
        """
        try:
            from src.ai_intelligence.advanced.novelty_engine import NoveltyEngine
            
            engine = NoveltyEngine()
            
            # Get label reactions (placeholder)
            label_set = []  # Will be populated from DailyMed
            
            # Get detected reactions from sources
            try:
                from src.storage.federated_query_engine import FederatedQueryEngine
                from src.storage.unified_storage import UnifiedStorageEngine
                
                storage = UnifiedStorageEngine()
                query_engine = FederatedQueryEngine(storage)
                
                # Query for reactions
                results = query_engine.query(f"drug:{drug}", limit=100)
                
                faers_set = [r.get("reaction", "") for r in results if r.get("source") == "faers"]
                social_set = [r.get("reaction", "") for r in results if r.get("source") == "social"]
                literature_set = [r.get("reaction", "") for r in results if r.get("source") == "literature"]
                
            except Exception:
                faers_set = []
                social_set = []
                literature_set = []
            
            # Detect novelty
            novelty_result = engine.detect(
                label_set=label_set,
                faers_set=faers_set,
                social_set=social_set,
                literature_set=literature_set
            )
            
            # Filter by specific reaction if provided
            if reaction:
                novel_reactions = [r for r in novelty_result["novel_reactions"] if reaction.lower() in r.lower()]
            else:
                novel_reactions = novelty_result["novel_reactions"]
            
            return {
                "tool": self.name,
                "drug": drug,
                "reaction": reaction,
                "novel_reactions": novel_reactions[:10],  # Top 10
                "total_novel_count": len(novel_reactions),
                "novelty_breakdown": {
                    "in_social_only": novelty_result.get("in_social_only", []),
                    "in_literature_only": novelty_result.get("in_literature_only", []),
                    "in_faers_only": novelty_result.get("in_faers_only", [])
                },
                "summary": f"Found {len(novel_reactions)} novel reactions for {drug}"
            }
            
        except Exception as e:
            logger.error(f"Novelty tool error: {e}")
            return {
                "tool": self.name,
                "error": str(e),
                "drug": drug
            }

