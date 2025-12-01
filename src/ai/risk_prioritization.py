"""
Risk Prioritization Framework (RPF) Engine for AetherSignal (CHUNK 6.12)
FDA/EMA-aligned automated signal prioritization based on 5-pillar weighted scoring.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


class RiskPrioritizationEngine:
    """
    Risk Prioritization Framework Engine (CHUNK 6.12).
    
    Computes priority scores for safety signals using FDA/EMA-aligned methodology:
    - Disproportionality Strength (30%)
    - Seriousness Impact (25%)
    - Clinical Coherence (15%)
    - Temporal Trend Strength (20%)
    - Lot/Batch Risk (10%)
    """
    
    def __init__(self):
        # FDA/EMA aligned weights
        self.weights = {
            "disproportionality": 0.30,
            "seriousness": 0.25,
            "clinical_coherence": 0.15,
            "trend_strength": 0.20,
            "lot_risk": 0.10,
        }

    def compute_disproportionality_score(self, signal: Dict[str, Any]) -> float:
        """
        Compute disproportionality score based on ROR/PRR magnitude.
        
        Args:
            signal: Signal dictionary with ROR, PRR, CI values
            
        Returns:
            Score from 0-10
        """
        ror = signal.get("ror", signal.get("ROR", 1))
        prr = signal.get("prr", signal.get("PRR", 1))
        ci_high = signal.get("ci_high", signal.get("ci_upper", signal.get("ror_ci_upper", 1)))
        
        # Use ROR if available, otherwise PRR
        disproportionality_value = ror if ror > 1 else prr
        
        if disproportionality_value < 1:
            return 0.0
        
        # Score based on magnitude and CI width
        base_score = min(disproportionality_value - 1, 9)  # Max 9 from magnitude
        ci_bonus = min((ci_high - disproportionality_value) * 0.5, 1)  # Up to 1 from CI
        
        return np.clip(base_score + ci_bonus, 0, 10)

    def compute_seriousness_score(self, signal: Dict[str, Any]) -> float:
        """
        Compute seriousness impact score.
        
        Args:
            signal: Signal dictionary with seriousness data
            
        Returns:
            Score from 0-10
        """
        serious_count = signal.get("serious_count", signal.get("serious_cases", 0))
        total_count = signal.get("case_count", signal.get("total_cases", signal.get("count", 1)))
        
        if total_count == 0:
            return 0.0
        
        serious_pct = serious_count / total_count
        
        # Higher weight for fatal cases if available
        fatal_count = signal.get("fatal_count", signal.get("death_count", 0))
        fatal_pct = fatal_count / total_count if total_count > 0 else 0
        
        # Base score from seriousness percentage, bonus for fatalities
        base_score = min(serious_pct * 8, 8)  # Max 8 from seriousness
        fatal_bonus = min(fatal_pct * 20, 2)  # Up to 2 from fatalities (high impact)
        
        return np.clip(base_score + fatal_bonus, 0, 10)

    def compute_clinical_coherence_score(self, signal: Dict[str, Any]) -> float:
        """
        Compute clinical coherence score.
        
        Args:
            signal: Signal dictionary with clinical coherence indicators
            
        Returns:
            Score from 0-10
        """
        score = 5.0  # Baseline
        
        # Check for known adverse reactions (lower score if expected)
        if signal.get("consistent_with_label", False):
            score -= 2  # Expected reaction, lower priority
        elif signal.get("unexpected", signal.get("unlabeled", False)):
            score += 3  # Unexpected reaction, higher priority
        
        # Check for MedDRA cluster matches
        if signal.get("meddra_cluster_match", False):
            score += 2
        
        # Check for biological plausibility
        if signal.get("biological_plausibility", False):
            score += 1
        
        # Check for dose-response relationship (from dose_response analysis)
        dose_response = signal.get("dose_response", {})
        if dose_response and dose_response.get("significance", 1) > 2:
            score += 1
        
        return np.clip(score, 0, 10)

    def compute_trend_strength_score(self, signal: Dict[str, Any]) -> float:
        """
        Compute temporal trend strength score.
        
        Args:
            signal: Signal dictionary with trend data
            
        Returns:
            Score from 0-10
        """
        # Check time-series data
        time_series = signal.get("time_series", {})
        risk_dynamics = signal.get("risk_dynamics", {})
        
        score = 0.0
        
        # From time-series analysis
        if time_series:
            significance = time_series.get("significance", 0)
            delta = abs(time_series.get("delta", 0))
            score += min(significance * 2, 5)  # Up to 5 from significance
            score += min(delta / 10, 2)  # Up to 2 from absolute delta
        
        # From risk dynamics (acceleration)
        if risk_dynamics:
            vel_acc = risk_dynamics.get("velocity_acceleration", {})
            if vel_acc:
                acceleration_score = abs(vel_acc.get("acceleration_score", 0))
                trend_class = vel_acc.get("trend_classification", "")
                if "accelerating" in trend_class.lower():
                    score += min(acceleration_score * 2, 3)  # Up to 3 for acceleration
        
        # From spike detection
        spike_factor = signal.get("spike_factor", signal.get("spike_ratio", 1))
        if spike_factor > 2:
            score += min((spike_factor - 2) * 1.5, 3)  # Up to 3 for spikes
        
        # From cumulative risk (if increasing)
        cumulative_risk = signal.get("cumulative_risk", {})
        if cumulative_risk and cumulative_risk.get("is_increasing", False):
            score += 1
        
        return np.clip(score, 0, 10)

    def compute_lot_risk_score(self, signal: Dict[str, Any]) -> float:
        """
        Compute lot/batch risk score.
        
        Args:
            signal: Signal dictionary with lot alert data
            
        Returns:
            Score from 0-10
        """
        lot_alerts = signal.get("lot_alerts", [])
        
        if not lot_alerts or len(lot_alerts) == 0:
            return 0.0
        
        # Score based on number and severity of lot alerts
        score = 5.0  # Base score for having lot alerts
        
        for lot in lot_alerts:
            spike_ratio = lot.get("spike_ratio", 1)
            serious_count = lot.get("serious_count", 0)
            
            # Higher score for more extreme spikes
            if spike_ratio > 5:
                score += 2
            elif spike_ratio > 3:
                score += 1
            
            # Higher score if serious cases in lot
            if serious_count > 0:
                score += 1
        
        return np.clip(score, 0, 10)

    def score_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute comprehensive RPF score for a signal.
        
        Args:
            signal: Signal dictionary with all available data
            
        Returns:
            Dictionary with signal, sub-scores, RPF score, and risk level
        """
        # Compute sub-scores
        scores = {
            "disproportionality": self.compute_disproportionality_score(signal),
            "seriousness": self.compute_seriousness_score(signal),
            "clinical_coherence": self.compute_clinical_coherence_score(signal),
            "trend_strength": self.compute_trend_strength_score(signal),
            "lot_risk": self.compute_lot_risk_score(signal),
        }

        # Weighted final RPF score (0–100)
        total_score = sum(scores[p] * self.weights[p] for p in scores) * 10

        return {
            "signal": signal,
            "scores": scores,
            "rpf_score": round(total_score, 2),
            "risk_level": self.classify(total_score)
        }

    def classify(self, score):
        if score >= 80:
            return "🔥 Critical"
        elif score >= 60:
            return "⚠️ High"
        elif score >= 40:
            return "🟡 Medium"
        else:
            return "🟢 Low"

    def prioritize(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize a list of signals by RPF score.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            Sorted list of scored signals (highest RPF score first)
        """
        if not signals:
            return []
        
        ranked = [self.score_signal(s) for s in signals]
        return sorted(ranked, key=lambda x: x["rpf_score"], reverse=True)
    
    def extract_signals_from_alerts(self, alerts: List[Any], df: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
        """
        Extract signal dictionaries from TrendAlert objects for RPF scoring.
        
        Args:
            alerts: List of TrendAlert objects or alert dictionaries
            df: Optional DataFrame for calculating PRR/ROR
            
        Returns:
            List of signal dictionaries suitable for RPF scoring
        """
        signals = []
        
        # Import signal stats for PRR/ROR calculation if needed
        try:
            from src.signal_stats import calculate_prr_ror
        except ImportError:
            calculate_prr_ror = None
        
        for alert in alerts:
            # Convert TrendAlert to dict if needed
            if hasattr(alert, 'details'):
                alert_dict = alert.details or {}
                alert_id = alert.id
                alert_title = alert.title
                alert_severity = alert.severity
            elif isinstance(alert, dict):
                alert_dict = alert.get("details", alert)
                alert_id = alert.get("id", "unknown")
                alert_title = alert.get("title", "Unknown Signal")
                alert_severity = alert.get("severity", "info")
            else:
                continue
            
            # Extract drug and reaction
            drug = alert_dict.get("drug") or alert_dict.get("drug_name", "")
            reaction = alert_dict.get("reaction") or alert_dict.get("reaction_name", "")
            
            if not drug and not reaction:
                continue
            
            # Build signal dictionary
            signal = {
                "id": alert_id,
                "title": alert_title,
                "drug": drug,
                "reaction": reaction,
                "severity": alert_severity,
                "case_count": alert_dict.get("recent_count", alert_dict.get("total_count", alert_dict.get("count", 0))),
                "serious_count": alert_dict.get("serious_cases", alert_dict.get("serious_count", 0)),
                "fatal_count": alert_dict.get("death_count", alert_dict.get("fatal_count", 0)),
            }
            
            # Add PRR/ROR if we have data
            if df is not None and calculate_prr_ror and drug and reaction:
                try:
                    prr_ror = calculate_prr_ror(drug, reaction, df)
                    if prr_ror:
                        signal.update({
                            "ror": prr_ror.get("ror", 1),
                            "prr": prr_ror.get("prr", 1),
                            "ci_high": prr_ror.get("ror_ci_upper", prr_ror.get("prr_ci_upper", 1)),
                            "ci_lower": prr_ror.get("ror_ci_lower", prr_ror.get("prr_ci_lower", 1)),
                        })
                except Exception:
                    pass
            
            # Add spike data
            if alert_dict.get("spike_ratio"):
                signal["spike_factor"] = alert_dict["spike_ratio"]
            
            # Add enrichment data from alert
            if hasattr(alert, 'time_series') and alert.time_series:
                signal["time_series"] = alert.time_series
            elif isinstance(alert, dict) and alert.get("time_series"):
                signal["time_series"] = alert["time_series"]
            
            if hasattr(alert, 'risk_dynamics') and alert.risk_dynamics:
                signal["risk_dynamics"] = alert.risk_dynamics
            elif isinstance(alert, dict) and alert.get("risk_dynamics"):
                signal["risk_dynamics"] = alert["risk_dynamics"]
            
            if hasattr(alert, 'dose_response') and alert.dose_response:
                signal["dose_response"] = alert.dose_response
            elif isinstance(alert, dict) and alert.get("dose_response"):
                signal["dose_response"] = alert["dose_response"]
            
            if hasattr(alert, 'cumulative_risk') and alert.cumulative_risk:
                signal["cumulative_risk"] = alert.cumulative_risk
            elif isinstance(alert, dict) and alert.get("cumulative_risk"):
                signal["cumulative_risk"] = alert["cumulative_risk"]
            
            if hasattr(alert, 'lot_alerts') and alert.lot_alerts:
                signal["lot_alerts"] = alert.lot_alerts
            elif isinstance(alert, dict) and alert.get("lot_alerts"):
                signal["lot_alerts"] = alert["lot_alerts"]
            
            signals.append(signal)
        
        return signals
