"""
Global Risk Management Engine (Phase 3F)
Multi-factor risk scoring and prioritization based on regulatory criteria.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from src.ai.multi_source_quantum_scoring import MultiSourceQuantumScoring
from src.ai.novelty_detection import NoveltyDetectionEngine
from src.mechanism.mechanistic_plausibility_scorer import MechanisticPlausibilityScorer
from src.ai.cross_source_consensus import CrossSourceConsensusEngine

logger = logging.getLogger(__name__)


class GlobalRiskManager:
    """
    Global Risk Management Engine.
    
    Implements multi-factor risk scoring aligned with:
    - EMA GVP IX
    - FDA Signal Management Framework
    - CIOMS VIII
    - WHO-UMC Signal Criteria
    - MHRA Signal KPIs
    """
    
    def __init__(self):
        """Initialize risk manager."""
        self.quantum_scoring = MultiSourceQuantumScoring()
        self.novelty_engine = NoveltyDetectionEngine()
        self.mechanism_scorer = MechanisticPlausibilityScorer()
        self.consensus_engine = CrossSourceConsensusEngine()
        
        # Risk dimension weights
        self.weights = {
            "frequency_evidence": 0.20,
            "severity_seriousness": 0.20,
            "novelty_label_gaps": 0.15,
            "mechanistic_plausibility": 0.15,
            "trend_burst": 0.15,
            "clinical_evidence": 0.10,
            "impact_exposure": 0.05
        }
    
    def calculate_global_risk_index(
        self,
        drug: str,
        reaction: str,
        df: pd.DataFrame,
        label_reactions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate Global Risk Index (GRI) for drug-reaction pair.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            df: DataFrame with AE entries
            label_reactions: Optional list of known label reactions
        
        Returns:
            Dictionary with GRI score, components, and recommendations
        """
        # Filter for this drug-reaction pair
        filtered = df[
            (df["drug"].str.contains(drug, case=False, na=False)) &
            (df["reaction"] == reaction)
        ].copy()
        
        if filtered.empty:
            return {
                "drug": drug,
                "reaction": reaction,
                "gri_score": 0.0,
                "priority_category": "minimal",
                "components": {},
                "recommended_action": "monitor"
            }
        
        # Calculate component scores
        components = {}
        
        # 1. Frequency & Strength of Evidence (20%)
        components["frequency_evidence"] = self._calculate_frequency_evidence(filtered)
        
        # 2. Severity & Seriousness (20%)
        components["severity_seriousness"] = self._calculate_severity_seriousness(filtered)
        
        # 3. Novelty & Label Gaps (15%)
        components["novelty_label_gaps"] = self._calculate_novelty_label_gaps(
            drug, reaction, filtered, label_reactions
        )
        
        # 4. Mechanistic Plausibility (15%)
        components["mechanistic_plausibility"] = self._calculate_mechanistic_plausibility(
            drug, reaction, filtered
        )
        
        # 5. Trend & Burst Metrics (15%)
        components["trend_burst"] = self._calculate_trend_burst(filtered)
        
        # 6. Clinical Evidence Alignment (10%)
        components["clinical_evidence"] = self._calculate_clinical_evidence(filtered)
        
        # 7. Impact & Exposure (5%)
        components["impact_exposure"] = self._calculate_impact_exposure(filtered)
        
        # Calculate weighted GRI
        gri_score = sum(
            components[dim] * self.weights[dim]
            for dim in self.weights.keys()
        )
        
        gri_score = max(0.0, min(1.0, gri_score))
        
        # Determine priority category
        priority_category = self._categorize_priority(gri_score)
        
        # Recommend action
        recommended_action = self._recommend_action(
            gri_score, components, filtered
        )
        
        return {
            "drug": drug,
            "reaction": reaction,
            "gri_score": round(gri_score, 3),
            "priority_category": priority_category,
            "components": components,
            "recommended_action": recommended_action,
            "total_cases": len(filtered),
            "sources": filtered["source"].unique().tolist() if "source" in filtered.columns else []
        }
    
    def _calculate_frequency_evidence(self, df: pd.DataFrame) -> float:
        """Calculate frequency and evidence strength score."""
        count = len(df)
        
        # Normalize count (log scale)
        if count >= 1000:
            freq_score = 1.0
        elif count >= 500:
            freq_score = 0.9
        elif count >= 200:
            freq_score = 0.8
        elif count >= 100:
            freq_score = 0.7
        elif count >= 50:
            freq_score = 0.6
        elif count >= 20:
            freq_score = 0.5
        elif count >= 10:
            freq_score = 0.4
        elif count >= 5:
            freq_score = 0.3
        else:
            freq_score = 0.2
        
        # Boost for multiple sources
        if "source" in df.columns:
            source_count = df["source"].nunique()
            if source_count >= 5:
                freq_score = min(freq_score + 0.2, 1.0)
            elif source_count >= 3:
                freq_score = min(freq_score + 0.1, 1.0)
        
        # Boost for high confidence
        if "confidence" in df.columns:
            avg_confidence = df["confidence"].mean()
            if avg_confidence >= 0.8:
                freq_score = min(freq_score + 0.1, 1.0)
        
        return freq_score
    
    def _calculate_severity_seriousness(self, df: pd.DataFrame) -> float:
        """Calculate severity and seriousness score."""
        score = 0.0
        
        # Check severity scores
        if "severity" in df.columns or "severity_score" in df.columns:
            severity_col = "severity_score" if "severity_score" in df.columns else "severity"
            avg_severity = df[severity_col].mean()
            score += float(avg_severity) * 0.5 if not pd.isna(avg_severity) else 0.0
        
        # Check serious flags
        if "serious" in df.columns:
            serious_rate = df["serious"].sum() / len(df) if len(df) > 0 else 0.0
            score += serious_rate * 0.5
        
        # Check for serious keywords
        if "text" in df.columns:
            serious_keywords = ["hospital", "er", "emergency", "icu", "death", "fatal", "life-threatening"]
            serious_count = df["text"].str.lower().str.contains(
                "|".join(serious_keywords), na=False
            ).sum()
            serious_rate = serious_count / len(df) if len(df) > 0 else 0.0
            score += serious_rate * 0.3
        
        return min(score, 1.0)
    
    def _calculate_novelty_label_gaps(
        self,
        drug: str,
        reaction: str,
        df: pd.DataFrame,
        label_reactions: Optional[List[str]]
    ) -> float:
        """Calculate novelty and label gap score."""
        # Use novelty engine
        novelty_result = self.novelty_engine.compute_novelty_score(
            drug, reaction, df, label_reactions
        )
        
        novelty_score = novelty_result.get("novelty_score", 0.0)
        
        # Higher novelty = higher risk (if not on label)
        return novelty_score
    
    def _calculate_mechanistic_plausibility(
        self,
        drug: str,
        reaction: str,
        df: pd.DataFrame
    ) -> float:
        """Calculate mechanistic plausibility score."""
        # Use mechanism scorer
        plausibility_result = self.mechanism_scorer.calculate_score(
            drug, reaction
        )
        
        return plausibility_result.get("plausibility_score", 0.5)
    
    def _calculate_trend_burst(self, df: pd.DataFrame) -> float:
        """Calculate trend and burst score."""
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
            
            if len(daily) < 5:
                return 0.0
            
            # Calculate trend (recent vs older)
            recent_days = 30
            cutoff_date = datetime.now().date() - timedelta(days=recent_days)
            
            recent = daily[daily["date"] >= cutoff_date]["count"].sum()
            older = daily[daily["date"] < cutoff_date]["count"].sum()
            
            if older > 0:
                trend_ratio = recent / older
                # Normalize trend ratio
                if trend_ratio >= 2.0:
                    trend_score = 1.0
                elif trend_ratio >= 1.5:
                    trend_score = 0.8
                elif trend_ratio >= 1.2:
                    trend_score = 0.6
                elif trend_ratio >= 1.0:
                    trend_score = 0.4
                else:
                    trend_score = 0.2
            else:
                trend_score = 0.8 if recent > 0 else 0.0
            
            # Check burst score if available
            if "burst_score" in df.columns:
                avg_burst = df["burst_score"].mean()
                burst_score = float(avg_burst) if not pd.isna(avg_burst) else 0.0
            else:
                burst_score = 0.0
            
            # Combine trend and burst
            combined = (trend_score * 0.7) + (burst_score * 0.3)
            
            return min(combined, 1.0)
        except Exception as e:
            logger.debug(f"Trend burst calculation error: {str(e)}")
            return 0.0
    
    def _calculate_clinical_evidence(self, df: pd.DataFrame) -> float:
        """Calculate clinical evidence alignment score."""
        if "source" not in df.columns:
            return 0.5
        
        # Check for clinical trial sources
        clinical_sources = ["clinicaltrials", "clinical"]
        has_clinical = df["source"].isin(clinical_sources).any()
        
        if has_clinical:
            return 0.8
        
        # Check for literature support
        lit_sources = ["pubmed", "literature"]
        has_literature = df["source"].isin(lit_sources).any()
        
        if has_literature:
            return 0.6
        
        # Default moderate
        return 0.5
    
    def _calculate_impact_exposure(self, df: pd.DataFrame) -> float:
        """Calculate impact and exposure score."""
        # Simplified heuristic
        # In production, would use prescription volume data
        
        count = len(df)
        
        # Normalize by case count
        if count >= 500:
            return 1.0
        elif count >= 200:
            return 0.8
        elif count >= 100:
            return 0.6
        elif count >= 50:
            return 0.4
        else:
            return 0.2
    
    def _categorize_priority(self, gri_score: float) -> str:
        """Categorize GRI score into priority category."""
        if gri_score >= 0.85:
            return "critical"
        elif gri_score >= 0.70:
            return "high"
        elif gri_score >= 0.55:
            return "moderate"
        elif gri_score >= 0.30:
            return "low"
        else:
            return "minimal"
    
    def _recommend_action(
        self,
        gri_score: float,
        components: Dict[str, float],
        df: pd.DataFrame
    ) -> str:
        """Recommend risk management action."""
        severity = components.get("severity_seriousness", 0.0)
        novelty = components.get("novelty_label_gaps", 0.0)
        trend = components.get("trend_burst", 0.0)
        
        # Critical - Public health alert
        if gri_score >= 0.85 and severity >= 0.8 and trend >= 0.7:
            return "public_health_alert"
        
        # High - Regulatory submission
        if gri_score >= 0.70 and novelty >= 0.7:
            return "regulatory_submission"
        
        # High - Label update
        if gri_score >= 0.65 and novelty >= 0.6:
            return "label_update_recommended"
        
        # Moderate - Medical review
        if gri_score >= 0.55 and (severity >= 0.6 or trend >= 0.6):
            return "trigger_medical_review"
        
        # Moderate - Enhanced surveillance
        if gri_score >= 0.45 and trend >= 0.5:
            return "enhanced_surveillance"
        
        # Low - Monitor
        return "monitor_only"
    
    def prioritize_signals(
        self,
        df: pd.DataFrame,
        drug: Optional[str] = None,
        label_reactions: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Prioritize all drug-reaction signals in DataFrame.
        
        Args:
            df: DataFrame with AE entries
            drug: Optional drug filter
            label_reactions: Optional list of known label reactions
            limit: Maximum number of signals to return
        
        Returns:
            List of prioritized signals with GRI scores
        """
        if df.empty:
            return []
        
        # Filter by drug if specified
        if drug:
            df = df[df["drug"].str.contains(drug, case=False, na=False)]
        
        if df.empty:
            return []
        
        # Get unique drug-reaction pairs
        if "drug" not in df.columns or "reaction" not in df.columns:
            return []
        
        drug_reaction_pairs = df.groupby(["drug", "reaction"]).size().reset_index(name="count")
        
        # Calculate GRI for each pair
        prioritized = []
        
        for _, row in drug_reaction_pairs.iterrows():
            drug_name = row["drug"]
            reaction = row["reaction"]
            
            gri_result = self.calculate_global_risk_index(
                drug_name, reaction, df, label_reactions
            )
            
            prioritized.append(gri_result)
        
        # Sort by GRI score (highest first)
        prioritized.sort(key=lambda x: x.get("gri_score", 0), reverse=True)
        
        return prioritized[:limit]

