"""
Quantitative Signal Prioritization (QSP) Engine (CHUNK 6.21.1 - Part 22)
Multi-factor quantitative scoring system for prioritizing safety signals by urgency,
regulatory impact, and clinical seriousness.
"""
import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

try:
    from .medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class QSPEngine:
    """
    Quantitative Signal Prioritization Engine.
    
    Computes QSP scores (0-100) using weighted dimensions:
    - Clinical Seriousness (30%)
    - Frequency / Reporting Rate (25%)
    - Disproportionality / Trend Acceleration (20%)
    - Population Vulnerability (10%)
    - Label Status / Novelty (10%)
    - Evidence Strength (5%)
    """

    def __init__(self):
        """Initialize the QSP Engine."""
        # QSP dimension weights (regulatory-aligned)
        self.weights = {
            "clinical_seriousness": 0.30,
            "frequency": 0.25,
            "disproportionality_trend": 0.20,
            "population_vulnerability": 0.10,
            "label_novelty": 0.10,
            "evidence_strength": 0.05
        }

    def compute_qsp_scores(self, signals: List[Dict[str, Any]],
                          label_info: Optional[List[str]] = None,
                          df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        """
        Compute Quantitative Signal Prioritization scores for signals.
        
        Args:
            signals: List of signal dictionaries
            label_info: Optional list of known reactions already on label
            df: Optional DataFrame for computing additional metrics
            
        Returns:
            List of signals with QSP scores and priority categories
        """
        if not signals:
            return []
        
        # Convert to DataFrame for easier processing
        signals_df = pd.DataFrame(signals)
        
        # Extract or compute component scores
        scored_signals = []
        
        for signal in signals:
            # Compute normalized component scores (0-1)
            components = {}
            
            # 1. Clinical Seriousness (30%)
            components["clinical_seriousness"] = self._compute_seriousness_score(signal, df)
            
            # 2. Frequency / Reporting Rate (25%)
            components["frequency"] = self._compute_frequency_score(signal, df)
            
            # 3. Disproportionality / Trend Acceleration (20%)
            components["disproportionality_trend"] = self._compute_disproportionality_trend_score(signal, df)
            
            # 4. Population Vulnerability (10%)
            components["population_vulnerability"] = self._compute_vulnerability_score(signal)
            
            # 5. Label Novelty (10%)
            components["label_novelty"] = self._compute_label_novelty_score(signal, label_info)
            
            # 6. Evidence Strength (5%)
            components["evidence_strength"] = self._compute_evidence_strength_score(signal)
            
            # Compute weighted QSP score
            qsp_score = sum(
                components[dim] * self.weights[dim]
                for dim in self.weights.keys()
            ) * 100
            
            qsp_score = max(0, min(100, round(qsp_score, 2)))
            
            # Determine priority category
            priority = self._categorize_priority(qsp_score)
            
            # Add to signal
            scored_signal = signal.copy()
            scored_signal["qsp_score"] = qsp_score
            scored_signal["qsp_priority"] = priority
            scored_signal["qsp_components"] = components
            scored_signal["qsp_computed_at"] = datetime.datetime.utcnow().isoformat()
            
            scored_signals.append(scored_signal)
        
        # Sort by QSP score (highest first)
        scored_signals.sort(key=lambda x: x.get("qsp_score", 0), reverse=True)
        
        return scored_signals

    def _compute_seriousness_score(self, signal: Dict[str, Any], df: Optional[pd.DataFrame]) -> float:
        """
        Compute clinical seriousness score (0-1).
        
        Based on: serious case rate, fatal cases, hospitalization, etc.
        """
        # Check for serious case rate
        serious_rate = signal.get("serious_rate")
        if serious_rate is None:
            # Calculate from signal data
            total_cases = signal.get("cases", signal.get("count", 0))
            serious_cases = signal.get("serious_cases", signal.get("serious_count", 0))
            if total_cases > 0:
                serious_rate = serious_cases / total_cases
            else:
                serious_rate = 0.0
        
        # Check for fatal cases
        fatal_cases = signal.get("fatal_cases", signal.get("fatal_count", 0))
        total_cases = signal.get("cases", signal.get("count", 1))
        fatal_rate = fatal_cases / total_cases if total_cases > 0 else 0.0
        
        # Combine seriousness metrics
        # Serious rate (0-0.7) + Fatal rate (0-0.3)
        score = min(serious_rate * 1.4, 0.7) + min(fatal_rate * 3.0, 0.3)
        
        return max(0, min(1, score))

    def _compute_frequency_score(self, signal: Dict[str, Any], df: Optional[pd.DataFrame]) -> float:
        """
        Compute frequency / reporting rate score (0-1).
        
        Based on: case count, reporting rate, time-normalized frequency.
        """
        # Case count
        cases = signal.get("cases", signal.get("count", 0))
        
        # Normalize case count (log scale for better distribution)
        if cases == 0:
            return 0.0
        elif cases >= 100:
            return 1.0
        elif cases >= 50:
            return 0.8
        elif cases >= 20:
            return 0.6
        elif cases >= 10:
            return 0.4
        elif cases >= 5:
            return 0.3
        elif cases >= 3:
            return 0.2
        else:
            return 0.1

    def _compute_disproportionality_trend_score(self, signal: Dict[str, Any], df: Optional[pd.DataFrame]) -> float:
        """
        Compute disproportionality and trend acceleration score (0-1).
        
        Based on: PRR/ROR magnitude, trend acceleration, change-point significance.
        """
        # Disproportionality (PRR/ROR)
        prr = signal.get("prr", signal.get("PRR", 1))
        ror = signal.get("ror", signal.get("ROR", 1))
        disproportionality = max(prr, ror) if (prr > 1 or ror > 1) else 1
        
        # Normalize disproportionality (PRR/ROR >= 2.0 is significant)
        if disproportionality >= 4:
            disproportionality_score = 1.0
        elif disproportionality >= 2:
            disproportionality_score = 0.7
        elif disproportionality >= 1.5:
            disproportionality_score = 0.5
        else:
            disproportionality_score = 0.2
        
        # Trend acceleration (from risk_dynamics or trend alerts)
        trend_acceleration = 0.0
        risk_dynamics = signal.get("risk_dynamics", {})
        if isinstance(risk_dynamics, dict):
            acceleration = risk_dynamics.get("acceleration", 0)
            if acceleration > 0.1:
                trend_acceleration = min(acceleration * 2, 0.5)
        
        # Combine: disproportionality (0.6 weight) + trend (0.4 weight)
        combined_score = (disproportionality_score * 0.6) + (trend_acceleration * 0.4)
        
        return max(0, min(1, combined_score))

    def _compute_vulnerability_score(self, signal: Dict[str, Any]) -> float:
        """
        Compute population vulnerability score (0-1).
        
        Based on: age groups (pediatric/elderly), pregnancy, comorbidities.
        """
        # Check subgroups for vulnerable populations
        subgroups = signal.get("subgroups", {})
        
        if not subgroups or not isinstance(subgroups, dict):
            return 0.3  # Default moderate
        
        vulnerability_indicators = 0
        total_subgroups = len(subgroups)
        
        # Check for vulnerable age groups
        for subgroup_key, subgroup_data in subgroups.items():
            if isinstance(subgroup_data, dict):
                # Pediatric or elderly
                if any(term in str(subgroup_key).lower() for term in ["pediatric", "child", "elderly", "age"]):
                    if subgroup_data.get("prr", 0) > 1.5 or subgroup_data.get("ror", 0) > 1.5:
                        vulnerability_indicators += 1
                
                # Pregnancy-related
                if any(term in str(subgroup_key).lower() for term in ["pregnancy", "pregnant", "lactation"]):
                    if subgroup_data.get("prr", 0) > 1.5 or subgroup_data.get("ror", 0) > 1.5:
                        vulnerability_indicators += 1
        
        if total_subgroups > 0:
            vulnerability_score = min(vulnerability_indicators / total_subgroups * 2, 1.0)
        else:
            vulnerability_score = 0.3
        
        return max(0, min(1, vulnerability_score))

    def _compute_label_novelty_score(self, signal: Dict[str, Any], label_info: Optional[List[str]]) -> float:
        """
        Compute label novelty score (0-1).
        
        New signals (not on label) = higher priority.
        """
        if label_info is None:
            return 1.0  # Assume new if no label info
        
        reaction = signal.get("reaction", signal.get("event", "")).lower()
        drug = signal.get("drug", "").lower()
        
        # Check if reaction is in known label
        is_labeled = any(
            reaction in known.lower() or known.lower() in reaction
            for known in label_info
        )
        
        # Also check if drug-reaction pair is known
        if is_labeled:
            return 0.2  # Known risk, lower novelty
        else:
            return 1.0  # New signal, high novelty

    def _compute_evidence_strength_score(self, signal: Dict[str, Any]) -> float:
        """
        Compute evidence strength score (0-1).
        
        Based on: case quality, narrative richness, dechallenge/rechallenge, consistency.
        """
        score = 0.0
        
        # Case count (more cases = stronger evidence)
        cases = signal.get("cases", signal.get("count", 0))
        if cases >= 50:
            score += 0.3
        elif cases >= 20:
            score += 0.2
        elif cases >= 10:
            score += 0.1
        
        # Narrative support
        narratives = signal.get("narratives", signal.get("case_narratives", []))
        if narratives and len(narratives) >= 3:
            score += 0.3
        elif narratives and len(narratives) >= 1:
            score += 0.15
        
        # Subgroup consistency
        subgroups = signal.get("subgroups", {})
        if subgroups and isinstance(subgroups, dict) and len(subgroups) >= 3:
            score += 0.2
        
        # Dechallenge/rechallenge (if available)
        if signal.get("positive_dechallenge_rate", 0) > 50:
            score += 0.1
        if signal.get("positive_rechallenge_rate", 0) > 50:
            score += 0.1
        
        return max(0, min(1, score))

    def _categorize_priority(self, qsp_score: float) -> str:
        """Categorize QSP score into priority level."""
        if qsp_score >= 70:
            return "High"
        elif qsp_score >= 40:
            return "Medium"
        else:
            return "Low"

    def generate_qsp_narrative(self, scored_signals: List[Dict[str, Any]]) -> str:
        """
        Generate AI-powered narrative summary of QSP results.
        
        Args:
            scored_signals: List of signals with QSP scores
            
        Returns:
            Narrative text
        """
        if not scored_signals:
            return "No signals available for QSP prioritization."
        
        if not LLM_AVAILABLE:
            # Fallback narrative
            high_priority = [s for s in scored_signals if s.get("qsp_priority") == "High"]
            medium_priority = [s for s in scored_signals if s.get("qsp_priority") == "Medium"]
            low_priority = [s for s in scored_signals if s.get("qsp_priority") == "Low"]
            
            narrative_parts = [
                f"Quantitative Signal Prioritization (QSP) analysis identified {len(scored_signals)} signals:",
                f"- High Priority: {len(high_priority)} signals",
                f"- Medium Priority: {len(medium_priority)} signals",
                f"- Low Priority: {len(low_priority)} signals"
            ]
            
            if high_priority:
                narrative_parts.append("\nTop High-Priority Signals:")
                for i, sig in enumerate(high_priority[:5], 1):
                    drug = sig.get("drug", "Unknown")
                    reaction = sig.get("reaction", "Unknown")
                    score = sig.get("qsp_score", 0)
                    narrative_parts.append(f"{i}. {drug} - {reaction} (QSP Score: {score:.1f})")
            
            return "\n".join(narrative_parts)
        
        # Format signal summary for LLM
        signal_summaries = []
        for sig in scored_signals[:10]:  # Top 10
            drug = sig.get("drug", "Unknown")
            reaction = sig.get("reaction", sig.get("event", "Unknown"))
            score = sig.get("qsp_score", 0)
            priority = sig.get("qsp_priority", "Unknown")
            components = sig.get("qsp_components", {})
            
            signal_summaries.append(
                f"{drug} - {reaction}: QSP {score:.1f} ({priority}) - "
                f"Seriousness: {components.get('clinical_seriousness', 0):.2f}, "
                f"Frequency: {components.get('frequency', 0):.2f}, "
                f"Disproportionality: {components.get('disproportionality_trend', 0):.2f}"
            )
        
        prompt = f"""
You are a pharmacovigilance expert explaining Quantitative Signal Prioritization (QSP) results.

Based on QSP scoring, the following signals have been prioritized:

{chr(10).join(signal_summaries)}

QSP scoring weights:
- Clinical Seriousness: 30%
- Frequency/Reporting Rate: 25%
- Disproportionality/Trend: 20%
- Population Vulnerability: 10%
- Label Novelty: 10%
- Evidence Strength: 5%

Provide:
1. Executive summary of QSP prioritization
2. Key high-priority signals and why they ranked high
3. Medium-priority signals requiring attention
4. Recommendations for signal review order
5. Regulatory considerations for high-priority signals

Format as a professional regulatory narrative suitable for governance review and audit documentation.
"""
        
        try:
            system_prompt = "You are a pharmacovigilance expert providing quantitative signal prioritization summaries for regulatory signal management."
            return call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=1500,
                temperature=0.3
            ) or "QSP narrative generation unavailable."
        except Exception as e:
            return f"QSP narrative generation error: {str(e)}"

    def prioritize_signals(self, signals: List[Dict[str, Any]],
                          label_info: Optional[List[str]] = None,
                          df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Complete QSP prioritization workflow.
        
        Args:
            signals: List of signal dictionaries
            label_info: Optional list of known label reactions
            df: Optional DataFrame for metric computation
            
        Returns:
            Dictionary with prioritized signals, summary, and narrative
        """
        scored_signals = self.compute_qsp_scores(signals, label_info, df)
        
        # Generate summary statistics
        high_priority = [s for s in scored_signals if s.get("qsp_priority") == "High"]
        medium_priority = [s for s in scored_signals if s.get("qsp_priority") == "Medium"]
        low_priority = [s for s in scored_signals if s.get("qsp_priority") == "Low"]
        
        # Generate narrative
        narrative = self.generate_qsp_narrative(scored_signals)
        
        return {
            "signals": scored_signals,
            "summary": {
                "total_signals": len(scored_signals),
                "high_priority_count": len(high_priority),
                "medium_priority_count": len(medium_priority),
                "low_priority_count": len(low_priority),
                "average_qsp_score": round(sum(s.get("qsp_score", 0) for s in scored_signals) / len(scored_signals), 2) if scored_signals else 0,
                "max_qsp_score": max((s.get("qsp_score", 0) for s in scored_signals), default=0)
            },
            "narrative": narrative,
            "computed_at": datetime.datetime.utcnow().isoformat()
        }

