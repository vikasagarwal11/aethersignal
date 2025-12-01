"""
Multi-Source Quantum Scoring Engine (Phase 2D.1)
Enhanced quantum scoring that combines:
- Frequency, Severity, Novelty, Burst Detection
- Cross-Source Consensus
- AI/LLM-supported mechanistic plausibility
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from src.quantum_ranking import quantum_rerank_signals
from src.ai.qsp_engine import QSPEngine
from src.quantum_anomaly import score_time_series, detect_time_anomalies

logger = logging.getLogger(__name__)


class MultiSourceQuantumScoring:
    """
    Multi-Source Quantum Scoring Engine.
    
    Combines:
    - Frequency (25%)
    - Severity (20%)
    - Burst Score (15%)
    - Novelty Score (15%)
    - Cross-Source Agreement (15%)
    - Mechanism Plausibility (10%)
    """
    
    def __init__(self):
        """Initialize multi-source quantum scoring engine."""
        self.qsp_engine = QSPEngine()
        self.weights = {
            "frequency": 0.25,
            "severity": 0.20,
            "burst": 0.15,
            "novelty": 0.15,
            "consensus": 0.15,
            "mechanism": 0.10
        }
    
    def compute_quantum_score(
        self,
        drug: str,
        reaction: str,
        df: pd.DataFrame,
        sources: Optional[List[str]] = None,
        label_reactions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compute comprehensive quantum score for a drug-reaction pair.
        
        Args:
            drug: Drug name
            reaction: Reaction PT
            df: DataFrame with AE entries
            sources: Optional list of sources to consider
            label_reactions: Optional list of known label reactions
        
        Returns:
            Dictionary with quantum score and component breakdown
        """
        # Filter for this drug-reaction pair
        filtered = df[
            (df["drug"].str.contains(drug, case=False, na=False)) &
            (df["reaction"] == reaction)
        ].copy()
        
        if filtered.empty:
            return {
                "quantum_score": 0.0,
                "components": {},
                "alert_level": "none"
            }
        
        # Compute components
        components = {}
        
        # 1. Frequency (25%)
        components["frequency"] = self._compute_frequency_score(filtered)
        
        # 2. Severity (20%)
        components["severity"] = self._compute_severity_score(filtered)
        
        # 3. Burst Score (15%)
        components["burst"] = self._compute_burst_score(filtered)
        
        # 4. Novelty Score (15%)
        components["novelty"] = self._compute_novelty_score(
            reaction, label_reactions, filtered
        )
        
        # 5. Cross-Source Consensus (15%)
        components["consensus"] = self._compute_consensus_score(
            filtered, sources
        )
        
        # 6. Mechanism Plausibility (10%)
        components["mechanism"] = self._compute_mechanism_score(
            drug, reaction, filtered
        )
        
        # Compute weighted quantum score
        quantum_score = sum(
            components[dim] * self.weights[dim]
            for dim in self.weights.keys()
        )
        
        quantum_score = max(0.0, min(1.0, quantum_score))
        
        # Determine alert level
        alert_level = self._determine_alert_level(quantum_score, components)
        
        return {
            "quantum_score": round(quantum_score, 3),
            "components": components,
            "alert_level": alert_level,
            "drug": drug,
            "reaction": reaction,
            "total_cases": len(filtered),
            "sources": filtered["source"].unique().tolist() if "source" in filtered.columns else []
        }
    
    def _compute_frequency_score(self, df: pd.DataFrame) -> float:
        """Compute frequency score (0-1)."""
        count = len(df)
        
        # Normalize using log scale
        if count == 0:
            return 0.0
        elif count >= 100:
            return 1.0
        elif count >= 50:
            return 0.8
        elif count >= 20:
            return 0.6
        elif count >= 10:
            return 0.4
        elif count >= 5:
            return 0.3
        elif count >= 3:
            return 0.2
        else:
            return 0.1
    
    def _compute_severity_score(self, df: pd.DataFrame) -> float:
        """Compute severity score (0-1)."""
        if "severity" in df.columns:
            avg_severity = df["severity"].mean()
            return float(avg_severity) if not pd.isna(avg_severity) else 0.0
        
        if "severity_score" in df.columns:
            avg_severity = df["severity_score"].mean()
            return float(avg_severity) if not pd.isna(avg_severity) else 0.0
        
        # Fallback: check for serious keywords
        if "text" in df.columns:
            serious_keywords = ["hospital", "er", "emergency", "severe", "death", "fatal"]
            serious_count = df["text"].str.lower().str.contains(
                "|".join(serious_keywords), na=False
            ).sum()
            return min(serious_count / len(df), 1.0) if len(df) > 0 else 0.0
        
        return 0.0
    
    def _compute_burst_score(self, df: pd.DataFrame) -> float:
        """Compute burst/anomaly score (0-1)."""
        if "timestamp" not in df.columns or len(df) < 5:
            return 0.0
        
        try:
            # Create time series
            df["date"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df[df["date"].notna()]
            
            if len(df) < 5:
                return 0.0
            
            # Group by date
            daily = df.groupby(df["date"].dt.date).size().reset_index(name="count")
            daily.columns = ["Period", "Count"]
            
            # Score time series for anomalies
            scored = score_time_series(daily)
            
            if scored.empty or "anomaly_score" not in scored.columns:
                return 0.0
            
            # Get max anomaly score
            max_anomaly = scored["anomaly_score"].max()
            
            # Normalize to 0-1 (threshold at 2.5)
            burst_score = min(max_anomaly / 2.5, 1.0)
            
            return float(burst_score)
        except Exception as e:
            logger.debug(f"Burst score calculation error: {str(e)}")
            return 0.0
    
    def _compute_novelty_score(
        self,
        reaction: str,
        label_reactions: Optional[List[str]],
        df: pd.DataFrame
    ) -> float:
        """Compute novelty score (0-1)."""
        # Check if reaction is in label
        if label_reactions:
            is_labeled = any(
                reaction.lower() in known.lower() or known.lower() in reaction.lower()
                for known in label_reactions
            )
            if is_labeled:
                return 0.0  # Known, not novel
        
        # Check recency (more recent = more novel)
        if "timestamp" in df.columns:
            try:
                df["date"] = pd.to_datetime(df["timestamp"], errors="coerce")
                df = df[df["date"].notna()]
                
                if not df.empty:
                    days_ago = (datetime.now() - df["date"].max()).days
                    
                    # More recent = higher novelty
                    if days_ago <= 30:
                        return 1.0
                    elif days_ago <= 90:
                        return 0.8
                    elif days_ago <= 180:
                        return 0.6
                    elif days_ago <= 365:
                        return 0.4
                    else:
                        return 0.2
            except Exception:
                pass
        
        # Default: moderate novelty
        return 0.5
    
    def _compute_consensus_score(
        self,
        df: pd.DataFrame,
        sources: Optional[List[str]]
    ) -> float:
        """Compute cross-source consensus score (0-1)."""
        if "source" not in df.columns:
            return 0.0
        
        unique_sources = df["source"].unique().tolist()
        source_count = len(unique_sources)
        
        # Available sources (if specified)
        if sources:
            available_sources = len(sources)
        else:
            # Default available sources
            available_sources = 7  # Social, FAERS, PubMed, ClinicalTrials, DailyMed, EMA, etc.
        
        # Consensus = sources reporting / total available
        consensus = min(source_count / available_sources, 1.0)
        
        # Boost if multiple high-confidence sources agree
        if "confidence" in df.columns:
            high_conf_sources = df[df["confidence"] >= 0.7]["source"].nunique()
            if high_conf_sources >= 3:
                consensus = min(consensus + 0.2, 1.0)
        
        return consensus
    
    def _compute_mechanism_score(
        self,
        drug: str,
        reaction: str,
        df: pd.DataFrame
    ) -> float:
        """Compute mechanism plausibility score (0-1)."""
        # For now, use a simple heuristic
        # In production, this would use LLM to assess mechanistic plausibility
        
        # Check if reaction appears in literature (PubMed)
        if "source" in df.columns:
            has_literature = "pubmed" in df["source"].values or "literature" in df["source"].values
            if has_literature:
                return 0.7  # Literature support = plausible
        
        # Check if reaction appears in clinical trials
        has_clinical = "clinicaltrials" in df["source"].values if "source" in df.columns else False
        if has_clinical:
            return 0.8  # Clinical trial support = more plausible
        
        # Default: moderate plausibility
        return 0.5
    
    def _determine_alert_level(
        self,
        quantum_score: float,
        components: Dict[str, float]
    ) -> str:
        """Determine alert level based on quantum score and components."""
        if quantum_score >= 0.95:
            return "critical"
        elif quantum_score >= 0.80:
            return "high"
        elif quantum_score >= 0.65:
            return "moderate"
        elif quantum_score >= 0.45:
            return "watchlist"
        elif quantum_score >= 0.25:
            return "low"
        else:
            return "none"

