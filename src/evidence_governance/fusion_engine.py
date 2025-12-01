"""
Evidence Strength Fusion Engine - Phase 3L Step 5
Combines provenance + quality + source reliability + novelty into single ESS score.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EvidenceFusionEngine:
    """
    Evidence Strength Fusion Engine - Combines all governance metrics.
    
    Fuses:
    - Provenance score
    - Data quality score
    - Source reliability
    - Novelty factor
    
    Into a single Evidence Strength Score (ESS) 0-100.
    """
    
    def __init__(self):
        """Initialize fusion engine with CIOMS/EMA-aligned weights."""
        # Weight schema aligned with CIOMS & EMA EV guidelines
        self.weights = {
            "provenance": 0.35,      # Trust of source + pipeline transformations
            "data_quality": 0.35,    # Completeness, consistency, noise, etc.
            "source_reliability": 0.15, # Built-in goodness of source (FAERS > Reddit)
            "novelty_factor": 0.15   # New evidence vs existing literature/FAERS
        }
        
        # Default novelty score (placeholder until lit/FAERS cross-match)
        self.default_novelty = 0.50
    
    def compute_novelty(
        self,
        record: Dict[str, Any],
        novelty_engine: Optional[Any] = None
    ) -> float:
        """
        Compute novelty score for a record.
        
        Args:
            record: AE record
            novelty_engine: Optional novelty detection engine
        
        Returns:
            Novelty score (0-1)
        """
        # If full novelty engine available (FAERS+Lit cross-check)
        if novelty_engine:
            try:
                return novelty_engine.novelty_score(record)
            except Exception as e:
                logger.debug(f"Novelty engine error: {e}")
        
        # Fallback: If appears only on social + high confidence
        source = record.get("source", "").lower()
        if source in ["reddit", "social_reddit", "twitter", "x", "social_x", "tiktok"]:
            confidence = float(record.get("confidence", 0) or record.get("confidence_score", 0))
            if confidence > 0.60:
                return 0.70  # Moderate-high novelty for social-only
        
        # Default moderate novelty
        return self.default_novelty
    
    def fuse(
        self,
        provenance: Dict[str, Any],
        quality: Dict[str, Any],
        record: Dict[str, Any],
        novelty_engine: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Fuse all governance metrics into Evidence Strength Score.
        
        Args:
            provenance: Provenance score dictionary
            quality: Quality score dictionary
            record: AE record
            novelty_engine: Optional novelty detection engine
        
        Returns:
            Fusion score dictionary with ESS
        """
        # Extract scores (normalize to 0-1)
        prov_score = provenance.get("final_provenance_score", 0) / 100.0
        qual_score = quality.get("final_quality_score", 0) / 100.0
        
        # Source reliability baseline from quality engine
        source_reliability = quality.get("source_quality_baseline", 0.50)
        
        # Novelty score
        novelty = self.compute_novelty(record, novelty_engine)
        
        # Weighted fusion
        fused = (
            self.weights["provenance"] * prov_score +
            self.weights["data_quality"] * qual_score +
            self.weights["source_reliability"] * source_reliability +
            self.weights["novelty_factor"] * novelty
        )
        
        # Ensure score is between 0 and 1
        fused = max(0.0, min(1.0, fused))
        
        return {
            "evidence_strength_score": round(fused * 100, 2),
            "components": {
                "provenance": round(prov_score * 100, 2),
                "data_quality": round(qual_score * 100, 2),
                "source_reliability": round(source_reliability * 100, 2),
                "novelty": round(novelty * 100, 2)
            },
            "weights": self.weights
        }

