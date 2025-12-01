"""
Alerts Engine (Phase 2D.5)
Real-time alert generation based on quantum scoring, burst detection, consensus, and novelty.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import uuid

from src.ai.multi_source_quantum_scoring import MultiSourceQuantumScoring
from src.ai.cross_source_consensus import CrossSourceConsensusEngine
from src.ai.novelty_detection import NoveltyDetectionEngine
from src.quantum_anomaly import detect_time_anomalies

logger = logging.getLogger(__name__)


class AlertsEngine:
    """
    Real-time alerts engine.
    Generates alerts based on quantum scoring, burst detection, consensus, and novelty.
    """
    
    def __init__(self):
        """Initialize alerts engine."""
        self.quantum_scoring = MultiSourceQuantumScoring()
        self.consensus_engine = CrossSourceConsensusEngine()
        self.novelty_engine = NoveltyDetectionEngine()
    
    def generate_alerts(
        self,
        df: pd.DataFrame,
        drug: Optional[str] = None,
        label_reactions: Optional[List[str]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate alerts for all drug-reaction pairs in DataFrame.
        
        Args:
            df: DataFrame with normalized AE entries
            drug: Optional drug filter
            label_reactions: Optional list of known label reactions
            thresholds: Optional custom thresholds
        
        Returns:
            List of alert dictionaries
        """
        if df.empty:
            return []
        
        # Default thresholds
        default_thresholds = {
            "quantum_score": 0.65,
            "burst_score": 0.5,
            "novelty_score": 0.7,
            "consensus_score": 0.6,
            "severity": 0.6
        }
        thresholds = thresholds or default_thresholds
        
        alerts = []
        
        # Group by drug-reaction pairs
        if drug:
            df = df[df["drug"].str.contains(drug, case=False, na=False)]
        
        if "drug" not in df.columns or "reaction" not in df.columns:
            return []
        
        drug_reaction_pairs = df.groupby(["drug", "reaction"]).size().reset_index(name="count")
        
        for _, row in drug_reaction_pairs.iterrows():
            drug_name = row["drug"]
            reaction = row["reaction"]
            
            # Compute quantum score
            quantum_result = self.quantum_scoring.compute_quantum_score(
                drug_name, reaction, df, label_reactions=label_reactions
            )
            
            # Check if alert should be generated
            should_alert = False
            alert_type = None
            
            # High Priority Alert conditions
            if (quantum_result["quantum_score"] >= thresholds["quantum_score"] and
                quantum_result["components"]["severity"] >= thresholds["severity"] and
                quantum_result["components"]["consensus"] >= thresholds["consensus_score"]):
                should_alert = True
                alert_type = "high_priority"
            
            # Burst Alert
            elif quantum_result["components"]["burst"] >= thresholds["burst_score"]:
                should_alert = True
                alert_type = "burst"
            
            # Novel AE Alert
            elif quantum_result["components"]["novelty"] >= thresholds["novelty_score"]:
                should_alert = True
                alert_type = "novel_ae"
            
            # Watchlist Alert
            elif quantum_result["quantum_score"] >= 0.45:
                should_alert = True
                alert_type = "watchlist"
            
            if should_alert:
                # Compute consensus
                consensus = self.consensus_engine.compute_consensus(
                    drug_name, reaction, df
                )
                
                # Compute novelty
                novelty = self.novelty_engine.compute_novelty_score(
                    drug_name, reaction, df, label_reactions
                )
                
                # Create alert
                alert = self._create_alert(
                    drug_name, reaction, quantum_result, consensus, novelty, alert_type, df
                )
                alerts.append(alert)
        
        # Sort by quantum score (highest first)
        alerts.sort(key=lambda x: x.get("quantum_score", 0), reverse=True)
        
        return alerts
    
    def _create_alert(
        self,
        drug: str,
        reaction: str,
        quantum_result: Dict[str, Any],
        consensus: Dict[str, Any],
        novelty: Dict[str, Any],
        alert_type: str,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Create alert dictionary."""
        alert_id = str(uuid.uuid4())
        
        # Filter for this drug-reaction
        filtered = df[
            (df["drug"].str.contains(drug, case=False, na=False)) &
            (df["reaction"] == reaction)
        ]
        
        # Get source breakdown
        sources = filtered["source"].unique().tolist() if "source" in filtered.columns else []
        
        # Generate summary
        summary = self._generate_alert_summary(
            drug, reaction, quantum_result, consensus, novelty, alert_type
        )
        
        return {
            "alert_id": alert_id,
            "timestamp": datetime.now().isoformat(),
            "drug": drug,
            "reaction": reaction,
            "alert_type": alert_type,
            "severity": quantum_result["alert_level"],
            "quantum_score": quantum_result["quantum_score"],
            "components": quantum_result["components"],
            "consensus": consensus,
            "novelty": novelty,
            "sources": sources,
            "source_count": len(sources),
            "total_cases": len(filtered),
            "summary": summary,
            "suggested_action": self._suggest_action(alert_type, quantum_result),
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "alert_version": "2.0"
            }
        }
    
    def _generate_alert_summary(
        self,
        drug: str,
        reaction: str,
        quantum_result: Dict[str, Any],
        consensus: Dict[str, Any],
        novelty: Dict[str, Any],
        alert_type: str
    ) -> str:
        """Generate alert summary text."""
        quantum_score = quantum_result["quantum_score"]
        source_count = consensus.get("source_count", 0)
        
        if alert_type == "high_priority":
            return (
                f"🚨 High Priority Alert: {drug} → {reaction}. "
                f"Quantum Score: {quantum_score:.2f}. "
                f"Confirmed by {source_count} source(s). "
                f"Requires immediate review."
            )
        elif alert_type == "burst":
            return (
                f"📈 Burst Alert: {drug} → {reaction}. "
                f"Sudden increase detected. "
                f"Quantum Score: {quantum_score:.2f}."
            )
        elif alert_type == "novel_ae":
            return (
                f"🧪 Novel AE Alert: {drug} → {reaction}. "
                f"New adverse event detected. "
                f"Quantum Score: {quantum_score:.2f}."
            )
        else:
            return (
                f"⚠️ Watchlist Alert: {drug} → {reaction}. "
                f"Quantum Score: {quantum_score:.2f}. "
                f"Monitor for trends."
            )
    
    def _suggest_action(
        self,
        alert_type: str,
        quantum_result: Dict[str, Any]
    ) -> str:
        """Suggest action based on alert type."""
        if alert_type == "high_priority":
            return "Immediate signal evaluation required. Consider regulatory notification."
        elif alert_type == "burst":
            return "Investigate cause of sudden increase. Check for batch issues or external factors."
        elif alert_type == "novel_ae":
            return "Review literature and clinical data. Consider label update if confirmed."
        else:
            return "Monitor trends. Review if pattern continues."

