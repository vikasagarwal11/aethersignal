"""
Unified Evidence Fusion Engine
Merges evidence from multiple sources into consolidated evidence object
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EvidenceUnifier:
    """Unifies evidence from multiple sources."""
    
    def unify(
        self,
        faers: Optional[Dict[str, Any]] = None,
        social: Optional[Dict[str, Any]] = None,
        literature: Optional[Dict[str, Any]] = None,
        mechanism: Optional[Dict[str, Any]] = None,
        causality: Optional[Dict[str, Any]] = None,
        label: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Unify evidence from all sources.
        
        Args:
            faers: FAERS evidence
            social: Social media evidence
            literature: Literature evidence
            mechanism: Mechanism reasoning evidence
            causality: Causality assessment evidence
            label: Label information
        
        Returns:
            Unified evidence dictionary
        """
        unified = {
            "faers": faers or {},
            "social": social or {},
            "literature": literature or {},
            "mechanism": mechanism or {},
            "causality": causality or {},
            "label": label or {},
            "unified_at": datetime.now().isoformat(),
            "sources": []
        }
        
        # Track which sources provided evidence
        if faers:
            unified["sources"].append("faers")
        if social:
            unified["sources"].append("social")
        if literature:
            unified["sources"].append("literature")
        if mechanism:
            unified["sources"].append("mechanism")
        if causality:
            unified["sources"].append("causality")
        if label:
            unified["sources"].append("label")
        
        # Calculate consensus score
        unified["consensus_score"] = self._calculate_consensus(unified)
        
        # Determine evidence strength
        unified["evidence_strength"] = self._determine_strength(unified)
        
        return unified
    
    def _calculate_consensus(self, unified: Dict[str, Any]) -> float:
        """
        Calculate consensus score across sources.
        
        Args:
            unified: Unified evidence dictionary
        
        Returns:
            Consensus score (0.0 to 1.0)
        """
        source_count = len(unified["sources"])
        
        if source_count == 0:
            return 0.0
        
        # More sources = higher consensus
        base_score = min(1.0, source_count / 5.0)
        
        # Boost if multiple sources agree on same reaction
        reactions = set()
        for source in ["faers", "social", "literature"]:
            if source in unified and "reactions" in unified[source]:
                reactions.update(unified[source]["reactions"])
        
        if len(reactions) > 0:
            # Agreement boost
            agreement_boost = min(0.2, len(reactions) * 0.05)
            return min(1.0, base_score + agreement_boost)
        
        return base_score
    
    def _determine_strength(self, unified: Dict[str, Any]) -> str:
        """
        Determine overall evidence strength.
        
        Args:
            unified: Unified evidence dictionary
        
        Returns:
            Strength level: "STRONG", "MODERATE", "WEAK", "INSUFFICIENT"
        """
        consensus = unified.get("consensus_score", 0.0)
        source_count = len(unified["sources"])
        
        if consensus >= 0.7 and source_count >= 3:
            return "STRONG"
        elif consensus >= 0.5 and source_count >= 2:
            return "MODERATE"
        elif consensus >= 0.3 or source_count >= 1:
            return "WEAK"
        else:
            return "INSUFFICIENT"

