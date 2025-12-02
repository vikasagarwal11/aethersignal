"""
Novel Signal Detector - Cross-source novel signal detection using KG
"""

from typing import Dict, Any, List, Optional
from .kg_core import KnowledgeGraph
from .kg_router import KGRouter
import logging

logger = logging.getLogger(__name__)


class NovelSignalDetector:
    """
    Detects novel signals by:
    - Comparing across sources
    - Checking KG for new patterns
    - Identifying emerging associations
    """
    
    def __init__(self, kg: KnowledgeGraph, router: KGRouter):
        self.kg = kg
        self.router = router
    
    def detect_novel(self, drug: str, reaction: str, sources: Dict[str, int]) -> Dict[str, Any]:
        """
        Detect if a drug-reaction pair is novel.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            sources: Dictionary with source counts (e.g., {"social": 10, "faers": 0})
        
        Returns:
            Novelty assessment
        """
        # Check if link exists in KG
        kg_path = self.router.find_mechanistic_path(drug, reaction)
        kg_exists = kg_path is not None
        
        # Check source distribution
        total_count = sum(sources.values())
        source_diversity = len([s for s in sources.values() if s > 0])
        
        # Novelty indicators
        is_novel = False
        novelty_reasons = []
        
        # Novel if: only in one source and not in KG
        if source_diversity == 1 and not kg_exists:
            is_novel = True
            novelty_reasons.append("Single-source signal not in knowledge graph")
        
        # Novel if: high count in one source, low/zero in others
        if total_count >= 10:
            dominant_source = max(sources.items(), key=lambda x: x[1])
            if dominant_source[1] / total_count > 0.8:
                is_novel = True
                novelty_reasons.append(f"Dominant in {dominant_source[0]} source")
        
        # Novel if: emerging pattern (recent increase)
        if sources.get("social", 0) > 20 and sources.get("faers", 0) < 5:
            is_novel = True
            novelty_reasons.append("High social media mentions, low FAERS")
        
        return {
            "drug": drug,
            "reaction": reaction,
            "is_novel": is_novel,
            "novelty_score": 0.8 if is_novel else 0.2,
            "novelty_reasons": novelty_reasons,
            "kg_exists": kg_exists,
            "source_distribution": sources,
            "total_count": total_count,
            "source_diversity": source_diversity
        }
    
    def find_emerging_patterns(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """
        Find emerging patterns in the KG.
        
        Args:
            threshold: Minimum count threshold
        
        Returns:
            List of emerging patterns
        """
        emerging = []
        
        # Get all drug-reaction edges
        for source, target, data in self.kg.g.edges(data=True):
            source_attrs = self.kg.get_node_attributes(source)
            target_attrs = self.kg.get_node_attributes(target)
            
            if source_attrs.get("type") == "drug" and target_attrs.get("type") == "reaction":
                # Check source distribution
                source_info = data.get("source", "unknown")
                weight = data.get("weight", 1.0)
                
                # Check if emerging
                if weight >= threshold:
                    emerging.append({
                        "drug": source,
                        "reaction": target,
                        "weight": weight,
                        "source": source_info,
                        "edge_data": data
                    })
        
        # Sort by weight
        emerging.sort(key=lambda x: x["weight"], reverse=True)
        
        return emerging[:20]  # Top 20

