"""
AI Trend Alerts Engine (CHUNK 6.11)
Automatically detects trends, spikes, anomalies, and emerging safety signal patterns.
Includes LLM-powered interpretation (CHUNK 6.11-B).

CHUNK 6.11.1: Foundation structure with TrendAlert dataclass and lightweight alerts.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

# Import existing spike detection
from src.longitudinal_spike import detect_spikes, detect_statistical_spikes, analyze_trend_changepoint
from src.utils import safe_divide, normalize_text, parse_date

# =========================================================
# CHUNK 6.11.1: Unified Alert Structure (Enterprise-grade standard)
# =========================================================

@dataclass
class TrendAlert:
    """Standardized trend alert structure (CHUNK 6.11.1 + 6.11.5 + 6.11.7 + 6.11.8 + 6.11.9 + 6.11.10 + 6.11.12 + 6.11.13)."""
    id: str
    title: str
    severity: str  # "info", "warning", "critical"
    summary: str
    metric_value: Optional[float] = None
    metric_unit: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    suggested_action: Optional[str] = None
    llm_explanation: Optional[Dict[str, Any]] = None  # CHUNK 6.11.5: LLM interpretation
    time_series: Optional[Dict[str, Any]] = None  # CHUNK 6.11.7: Time-series analysis
    subgroups: Optional[Dict[str, Any]] = None  # CHUNK 6.11.8: Subgroup analysis
    subgroup_interpretation: Optional[Dict[str, Any]] = None  # CHUNK 6.11.8: LLM subgroup interpretation
    dose_response: Optional[Dict[str, Any]] = None  # CHUNK 6.11.9: Dose-response analysis
    cumulative_risk: Optional[Dict[str, Any]] = None  # CHUNK 6.11.9: Cumulative risk analysis
    dose_interpretation: Optional[Dict[str, Any]] = None  # CHUNK 6.11.9: LLM dose-response interpretation
    risk_dynamics: Optional[Dict[str, Any]] = None  # CHUNK 6.11.10: Risk acceleration and change-points
    risk_dynamics_interpretation: Optional[Dict[str, Any]] = None  # CHUNK 6.11.10: LLM risk dynamics interpretation
    narrative_clusters: Optional[List[Dict[str, Any]]] = None  # CHUNK 6.11.12: Narrative semantic clusters
    lot_alerts: Optional[List[Dict[str, Any]]] = None  # CHUNK 6.11.13: Lot/batch spike alerts

# =========================================================
# CHUNK 6.11.1: Helper Utilities
# =========================================================

def safe_pct_change(old: float, new: float) -> Optional[float]:
    """
    Calculate safe percent change, avoid divide-by-zero (CHUNK 6.11.1).
    
    Args:
        old: Old value
        new: New value
        
    Returns:
        Percent change or None if cannot calculate
    """
    try:
        if old is None or old == 0:
            return None
        return (new - old) / old * 100
    except (TypeError, ZeroDivisionError):
        return None


def get_last_90_days(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Return subset for last 90 days (CHUNK 6.11.1).
    
    Args:
        df: DataFrame with date column
        date_col: Name of date column
        
    Returns:
        Filtered DataFrame with last 90 days
    """
    if date_col not in df.columns:
        return pd.DataFrame()  # Return empty if column missing
    
    try:
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")
        df_copy = df_copy[df_copy[date_col].notna()]
        
        if df_copy.empty:
            return pd.DataFrame()
        
        cutoff = datetime.now() - timedelta(days=90)
        return df_copy[df_copy[date_col] >= cutoff]
    except Exception:
        return pd.DataFrame()

# =========================================================
# CHUNK 6.11.1: Light Statistical Alerts (FAST)
# These run after every query in Hybrid Mode.
# =========================================================

def _alert_top_reaction_spikes(df: pd.DataFrame) -> Optional[TrendAlert]:
    """
    Detect reactions that increased most in 90 days (CHUNK 6.11.1).
    
    Returns:
        TrendAlert or None if no spike detected
    """
    # Find date column
    date_col = None
    for col in ["event_date", "report_date", "receipt_date", "receive_date", "received_date"]:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col or "reaction" not in df.columns:
        return None
    
    recent = get_last_90_days(df, date_col)
    if recent.empty:
        return None
    
    # Handle multi-value reactions
    reaction_series = recent["reaction"].astype(str).str.split("; ").explode()
    reaction_series = reaction_series[reaction_series.notna() & (reaction_series != 'nan')]
    
    if reaction_series.empty:
        return None
    
    top_recent = reaction_series.value_counts().head(1)
    if top_recent.empty:
        return None
    
    reaction = top_recent.index[0]
    recent_count = top_recent.values[0]
    
    # Compare against full dataset distribution
    full_reaction_series = df["reaction"].astype(str).str.split("; ").explode()
    full_reaction_series = full_reaction_series[full_reaction_series.notna() & (full_reaction_series != 'nan')]
    total = full_reaction_series.value_counts().get(reaction, 0)
    
    older_count = total - recent_count
    pct = safe_pct_change(older_count, total)
    
    if pct is None or pct < 10:  # Only alert if >10% increase
        return None
    
    return TrendAlert(
        id="reaction_spike",
        title=f"Spike in '{reaction}' reports (90d)",
        severity="warning",
        summary=f"'{reaction}' shows the highest increase in the last 90 days.",
        metric_value=pct,
        metric_unit="percent",
        details={"recent_count": int(recent_count), "total_count": int(total), "reaction": reaction},
        suggested_action=f"Review clusters and serious cases for '{reaction}'."
    )


def _alert_top_drug_spikes(df: pd.DataFrame) -> Optional[TrendAlert]:
    """
    Detect drugs that increased the most in 90 days (CHUNK 6.11.1).
    
    Returns:
        TrendAlert or None if no spike detected
    """
    # Find date column
    date_col = None
    for col in ["event_date", "report_date", "receipt_date", "receive_date", "received_date"]:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col or "drug_name" not in df.columns:
        return None
    
    recent = get_last_90_days(df, date_col)
    if recent.empty:
        return None
    
    # Handle multi-value drugs
    drug_series = recent["drug_name"].astype(str).str.split("; ").explode()
    drug_series = drug_series[drug_series.notna() & (drug_series != 'nan')]
    
    if drug_series.empty:
        return None
    
    top_recent = drug_series.value_counts().head(1)
    if top_recent.empty:
        return None
    
    drug = top_recent.index[0]
    recent_count = top_recent.values[0]
    
    # Compare against full dataset
    full_drug_series = df["drug_name"].astype(str).str.split("; ").explode()
    full_drug_series = full_drug_series[full_drug_series.notna() & (full_drug_series != 'nan')]
    total = full_drug_series.value_counts().get(drug, 0)
    
    older_count = total - recent_count
    pct = safe_pct_change(older_count, total)
    
    if pct is None or pct < 10:  # Only alert if >10% increase
        return None
    
    return TrendAlert(
        id="drug_spike",
        title=f"Emerging increase in '{drug}' reports",
        severity="info",
        summary=f"'{drug}' shows the strongest short-term volume increase.",
        metric_value=pct,
        metric_unit="percent",
        details={"recent_count": int(recent_count), "total_count": int(total), "drug": drug},
        suggested_action=f"Check frequent reactions and seriousness trends for '{drug}'."
    )


def _alert_serious_case_shift(df: pd.DataFrame) -> Optional[TrendAlert]:
    """
    Detect changes in serious/non-serious case proportions (CHUNK 6.11.1).
    
    Returns:
        TrendAlert or None if no significant shift
    """
    serious_col = None
    for col in ["seriousness", "serious"]:
        if col in df.columns:
            serious_col = col
            break
    
    if not serious_col:
        return None
    
    total_cases = len(df)
    if total_cases == 0:
        return None
    
    # Handle boolean or string values
    serious_series = df[serious_col]
    if serious_series.dtype == bool:
        serious_count = serious_series.sum()
    else:
        serious_count = serious_series.astype(str).str.lower().isin(['true', '1', 'yes', 'y', 'serious']).sum()
    
    pct = (serious_count / total_cases * 100) if total_cases > 0 else 0
    
    # Only alert for extreme proportions
    if pct >= 20 and pct <= 80:
        return None  # Normal range
    
    # This is an edge case - alert
    severity = "critical" if (pct < 5 or pct > 95) else "warning"
    
    return TrendAlert(
        id="serious_shift",
        title="Serious case proportion change",
        severity=severity,
        summary=f"Serious cases account for {pct:.1f}% of all cases.",
        metric_value=pct,
        metric_unit="percent",
        details={"serious_cases": int(serious_count), "total_cases": int(total_cases)},
        suggested_action="Review causes of seriousness shift."
    )

# =========================================================
# CHUNK 6.11.1: MAIN PUBLIC API
# =========================================================

def get_trend_alerts(
    df: pd.DataFrame, 
    enrich_with_llm: bool = False,
    enrich_with_timeseries: bool = False,
    enrich_with_subgroups: bool = False,
    enrich_with_dose_response: bool = False,
    enrich_with_risk_dynamics: bool = False,
    enrich_with_narrative_clusters: bool = False,
    enrich_with_lot_alerts: bool = False
) -> List[TrendAlert]:
    """
    Public API for lightweight trend alerts (CHUNK 6.11.1 + 6.11.5 + 6.11.7 + 6.11.8 + 6.11.9 + 6.11.10 + 6.11.12 + 6.11.13).
    
    Used by:
    - suggestions_engine.py
    - chat_interface.py
    - quickstats_panel.py
    
    Returns FAST trend alerts only (Hybrid Mode).
    Optionally enriches with LLM interpretation, time-series analysis, subgroup analysis, 
    dose-response analysis, risk dynamics analysis, narrative clustering, and lot detection.
    
    Args:
        df: DataFrame with PV data
        enrich_with_llm: If True, add LLM interpretation for high/critical alerts (CHUNK 6.11.5)
        enrich_with_timeseries: If True, add time-series analysis (CHUNK 6.11.7)
        enrich_with_subgroups: If True, add subgroup analysis (CHUNK 6.11.8)
        enrich_with_dose_response: If True, add dose-response and cumulative risk analysis (CHUNK 6.11.9)
        enrich_with_risk_dynamics: If True, add risk acceleration and change-point analysis (CHUNK 6.11.10)
        enrich_with_narrative_clusters: If True, add narrative semantic clustering (CHUNK 6.11.12)
        enrich_with_lot_alerts: If True, add lot/batch spike detection (CHUNK 6.11.13)
        
    Returns:
        List of TrendAlert objects
    """
    alerts: List[TrendAlert] = []
    
    if df is None or len(df) == 0:
        return alerts
    
    # CHUNK 6.11.7: Initialize time-series engine if needed
    ts_engine = None
    if enrich_with_timeseries:
        try:
            from src.ai.timeseries_engine import TimeSeriesEngine
            ts_engine = TimeSeriesEngine()
        except Exception:
            ts_engine = None
    
    # CHUNK 6.11.8: Initialize subgroup engine if needed
    sg_engine = None
    if enrich_with_subgroups:
        try:
            from src.ai.subgroup_engine import SubgroupEngine
            sg_engine = SubgroupEngine()
        except Exception:
            sg_engine = None
    
    # CHUNK 6.11.9: Initialize dose-response engine if needed
    dr_engine = None
    if enrich_with_dose_response:
        try:
            from src.ai.dose_response_engine import DoseResponseEngine
            dr_engine = DoseResponseEngine()
        except Exception:
            dr_engine = None
    
    # CHUNK 6.11.10: Initialize risk dynamics engines if needed
    rae = None
    cpe = None
    if enrich_with_risk_dynamics:
        try:
            from src.ai.risk_acceleration_engine import RiskAccelerationEngine
            from src.ai.change_point_engine import ChangePointEngine
            rae = RiskAccelerationEngine()
            cpe = ChangePointEngine()
        except Exception:
            rae = None
            cpe = None
    
    # CHUNK 6.11.12: Initialize narrative clustering engine if needed
    nce = None
    if enrich_with_narrative_clusters:
        try:
            from src.ai.narrative_clustering_engine import NarrativeClusteringEngine
            nce = NarrativeClusteringEngine(use_openai_embeddings=True)
        except Exception:
            nce = None
    
    # CHUNK 6.11.13: Initialize lot detection engine if needed
    lot_engine = None
    if enrich_with_lot_alerts:
        try:
            from src.ai.lot_detection_engine import LotDetectionEngine
            lot_engine = LotDetectionEngine(min_cases=5, spike_factor=2.0)
        except Exception:
            lot_engine = None
    
    for fn in [
        _alert_top_reaction_spikes,
        _alert_top_drug_spikes,
        _alert_serious_case_shift,
    ]:
        try:
            alert = fn(df)
            if alert:
                # CHUNK 6.11.5: Enrich high/critical alerts with LLM if requested
                if enrich_with_llm and alert.severity in ["critical", "high", "warning"]:
                    try:
                        alert = _enrich_alert_with_llm(alert, df)
                    except Exception:
                        # If LLM enrichment fails, continue with original alert
                        pass
                
                # CHUNK 6.11.7: Attach time-series analysis if requested and engine available
                if enrich_with_timeseries and ts_engine:
                    try:
                        alert = _attach_time_series(alert, df, ts_engine)
                    except Exception:
                        # If time-series enrichment fails, continue without it
                        pass
                
                # CHUNK 6.11.8: Attach subgroup analysis if requested and engine available
                if enrich_with_subgroups and sg_engine:
                    try:
                        alert = _attach_subgroups(alert, df, sg_engine, enrich_with_llm)
                    except Exception:
                        # If subgroup enrichment fails, continue without it
                        pass
                
                # CHUNK 6.11.9: Attach dose-response and cumulative risk analysis if requested
                if enrich_with_dose_response and dr_engine:
                    try:
                        alert = _attach_dose_response(alert, df, dr_engine, enrich_with_llm)
                    except Exception:
                        # If dose-response enrichment fails, continue without it
                        pass
                
                # CHUNK 6.11.10: Attach risk dynamics analysis if requested
                # Note: Requires cumulative_risk to be available first
                if enrich_with_risk_dynamics and rae and cpe:
                    try:
                        # Ensure cumulative_risk exists first
                        if not alert.cumulative_risk and dr_engine:
                            # Try to compute it now
                            alert = _attach_dose_response(alert, df, dr_engine, False)
                        alert = _attach_risk_dynamics(alert, df, rae, cpe, enrich_with_llm)
                    except Exception:
                        # If risk dynamics enrichment fails, continue without it
                        pass
                
                # CHUNK 6.11.12: Attach narrative clustering if requested
                if enrich_with_narrative_clusters and nce:
                    try:
                        alert = _attach_narrative_clusters(alert, df, nce, enrich_with_llm)
                    except Exception:
                        # If narrative clustering fails, continue without it
                        pass
                
                # CHUNK 6.11.13: Attach lot alerts if requested
                if enrich_with_lot_alerts and lot_engine:
                    try:
                        alert = _attach_lot_alerts(alert, df, lot_engine, enrich_with_llm)
                    except Exception:
                        # If lot detection fails, continue without it
                        pass
                
                alerts.append(alert)
        except Exception:
            # Do not break — fail gracefully
            continue
    
    return alerts


def _attach_time_series(alert: TrendAlert, df: pd.DataFrame, ts_engine) -> TrendAlert:
    """
    Attach time-series analysis to an alert (CHUNK 6.11.7).
    
    Args:
        alert: TrendAlert object to enrich
        df: DataFrame for time-series analysis
        ts_engine: TimeSeriesEngine instance
        
    Returns:
        TrendAlert with time_series field populated
    """
    try:
        # Extract drug and reaction from alert details or title
        drug = None
        reaction = None
        
        if alert.details:
            drug = alert.details.get("drug") or alert.details.get("drug_name")
            reaction = alert.details.get("reaction") or alert.details.get("reaction_name")
        
        # If not in details, try to extract from title/summary (basic heuristic)
        if not drug and "drug" in alert.id:
            # Try to extract from title - this is a fallback
            title_lower = alert.title.lower()
            # Could add more sophisticated extraction here if needed
        
        # Run time-series analysis
        ts_result = ts_engine.summarize_timeseries(
            df=df,
            drug=drug,
            reaction=reaction
        )
        
        if ts_result:
            alert.time_series = ts_result
        else:
            alert.time_series = None
            
    except Exception:
        # Fail gracefully
        alert.time_series = None
    
    return alert


def _enrich_alert_with_llm(alert: TrendAlert, df: pd.DataFrame) -> TrendAlert:
    """
    Enrich a TrendAlert with LLM clinical interpretation (CHUNK 6.11.5).
    
    Args:
        alert: TrendAlert object to enrich
        df: DataFrame for context
        
    Returns:
        TrendAlert with llm_explanation field populated
    """
    try:
        from src.ai.medical_llm import interpret_trend_alert
        
        interpretation = interpret_trend_alert(
            alert_title=alert.title,
            alert_summary=alert.summary,
            severity=alert.severity,
            metric_value=alert.metric_value,
            metric_unit=alert.metric_unit,
            suggested_action=alert.suggested_action,
            details=alert.details,
            df=df
        )
        
        if interpretation:
            alert.llm_explanation = interpretation
        else:
            # Set default if LLM fails
            alert.llm_explanation = {
                "clinical_relevance": "LLM explanation unavailable.",
                "possible_causes": [],
                "case_characteristics": "",
                "regulatory_context": "",
                "recommended_followups": [],
                "single_sentence_summary": alert.summary
            }
            
    except Exception:
        # Fail gracefully - set default explanation
        alert.llm_explanation = {
            "clinical_relevance": "LLM explanation unavailable.",
            "possible_causes": [],
            "case_characteristics": "",
            "regulatory_context": "",
            "recommended_followups": [],
            "single_sentence_summary": alert.summary
        }
    
    return alert


def _attach_subgroups(
    alert: TrendAlert, 
    df: pd.DataFrame, 
    sg_engine, 
    enrich_with_llm: bool = False
) -> TrendAlert:
    """
    Attach subgroup analysis to an alert (CHUNK 6.11.8).
    
    Args:
        alert: TrendAlert object to enrich
        df: DataFrame for subgroup analysis
        sg_engine: SubgroupEngine instance
        enrich_with_llm: If True, also add LLM interpretation of subgroups
        
    Returns:
        TrendAlert with subgroups and subgroup_interpretation fields populated
    """
    try:
        # Extract drug and reaction from alert details
        drug = None
        reaction = None
        
        if alert.details:
            drug = alert.details.get("drug") or alert.details.get("drug_name")
            reaction = alert.details.get("reaction") or alert.details.get("reaction_name")
        
        # Run enhanced subgroup analysis (CHUNK 6.11.11: with statistical tests and PRR/ROR)
        # Use enhanced version if drug and reaction are available
        if drug and reaction:
            subgroups_result = sg_engine.analyze_subgroups_enhanced(
                df=df,
                drug=drug,
                reaction=reaction,
                include_statistical_tests=True,
                include_subgroup_prr_ror=True,
                include_concomitants=True
            )
            # Extract subgroups from enhanced result
            if subgroups_result and "subgroups" in subgroups_result:
                alert.subgroups = subgroups_result["subgroups"]
                # Store concomitants separately if available
                if "concomitants" in subgroups_result:
                    if alert.details is None:
                        alert.details = {}
                    alert.details["concomitant_drugs"] = subgroups_result["concomitants"]
            else:
                alert.subgroups = None
        else:
            # Fallback to basic subgroup analysis
            subgroups_result = sg_engine.analyze_subgroups(
                df=df,
                drug=drug,
                reaction=reaction
            )
            
            if subgroups_result:
                alert.subgroups = subgroups_result
            else:
                alert.subgroups = None
        
        # CHUNK 6.11.8: Add LLM interpretation of subgroups if requested (for both enhanced and basic)
        if enrich_with_llm and alert.subgroups:
            try:
                from src.ai.medical_llm import interpret_subgroup_findings
                interpretation = interpret_subgroup_findings(
                    alert_title=alert.title,
                    alert_summary=alert.summary,
                    subgroups=alert.subgroups
                )
                if interpretation:
                    alert.subgroup_interpretation = interpretation
                else:
                    alert.subgroup_interpretation = None
            except Exception:
                # If LLM interpretation fails, continue without it
                alert.subgroup_interpretation = None
        else:
            alert.subgroup_interpretation = None
            
    except Exception:
        # Fail gracefully
        alert.subgroups = None
        alert.subgroup_interpretation = None
    
    return alert


def _attach_dose_response(
    alert: TrendAlert, 
    df: pd.DataFrame, 
    dr_engine, 
    enrich_with_llm: bool = False
) -> TrendAlert:
    """
    Attach dose-response and cumulative risk analysis to an alert (CHUNK 6.11.9).
    
    Args:
        alert: TrendAlert object to enrich
        df: DataFrame for dose-response analysis
        dr_engine: DoseResponseEngine instance
        enrich_with_llm: If True, also add LLM interpretation of dose-response findings
        
    Returns:
        TrendAlert with dose_response, cumulative_risk, and dose_interpretation fields populated
    """
    try:
        # Extract drug and reaction from alert details
        drug = None
        reaction = None
        
        if alert.details:
            drug = alert.details.get("drug") or alert.details.get("drug_name")
            reaction = alert.details.get("reaction") or alert.details.get("reaction_name")
        
        # Run dose-response analysis
        dose_response_result = dr_engine.compute_dose_response(
            df=df,
            drug=drug,
            reaction=reaction
        )
        
        if dose_response_result:
            alert.dose_response = dose_response_result
        
        # Run cumulative risk analysis
        cumulative_risk_result = dr_engine.compute_cumulative_risk(
            df=df,
            drug=drug,
            reaction=reaction
        )
        
        if cumulative_risk_result:
            alert.cumulative_risk = cumulative_risk_result
        
        # CHUNK 6.11.9: Add LLM interpretation if requested and we have results
        if enrich_with_llm and (dose_response_result or cumulative_risk_result):
            try:
                from src.ai.medical_llm import interpret_dose_response
                interpretation = interpret_dose_response(
                    alert_title=alert.title,
                    alert_summary=alert.summary,
                    dose_response=dose_response_result,
                    cumulative_risk=cumulative_risk_result
                )
                if interpretation:
                    alert.dose_interpretation = interpretation
            except Exception:
                # If LLM interpretation fails, continue without it
                alert.dose_interpretation = None
                
    except Exception:
        # Fail gracefully
        alert.dose_response = None
        alert.cumulative_risk = None
        alert.dose_interpretation = None
    
    return alert


def _attach_risk_dynamics(
    alert: TrendAlert, 
    df: pd.DataFrame, 
    rae, 
    cpe,
    enrich_with_llm: bool = False
) -> TrendAlert:
    """
    Attach risk dynamics analysis (velocity, acceleration, change-points) to an alert (CHUNK 6.11.10).
    
    Args:
        alert: TrendAlert object to enrich
        df: DataFrame for analysis
        rae: RiskAccelerationEngine instance
        cpe: ChangePointEngine instance
        enrich_with_llm: If True, also add LLM interpretation
        
    Returns:
        TrendAlert with risk_dynamics and risk_dynamics_interpretation fields populated
    """
    try:
        # Need cumulative_risk data to compute dynamics
        if not alert.cumulative_risk or not alert.cumulative_risk.get("monthly"):
            alert.risk_dynamics = None
            alert.risk_dynamics_interpretation = None
            return alert
        
        monthly_series = alert.cumulative_risk["monthly"]
        periods = alert.cumulative_risk.get("periods", [])
        
        # Compute velocity and acceleration
        velocity_accel_result = rae.compute_velocity_acceleration(monthly_series)
        
        # Compute incident rate slope
        slope_result = rae.compute_incident_rate_slope(monthly_series)
        
        # Detect change-points
        changepoints_indices = cpe.detect_changepoints(monthly_series, method="all")
        
        # Get change-points with context
        changepoints_with_context = cpe.detect_changepoints_with_context(
            monthly_series,
            periods=periods
        )
        
        # Combine all results
        risk_dynamics = {
            "velocity_acceleration": velocity_accel_result,
            "incident_rate_slope": slope_result,
            "changepoints": changepoints_indices,
            "changepoints_with_context": changepoints_with_context
        }
        
        alert.risk_dynamics = risk_dynamics
        
        # CHUNK 6.11.10: Add LLM interpretation if requested
        if enrich_with_llm and (velocity_accel_result or slope_result or changepoints_with_context):
            try:
                from src.ai.medical_llm import interpret_risk_dynamics
                interpretation = interpret_risk_dynamics(
                    alert_title=alert.title,
                    alert_summary=alert.summary,
                    risk_dynamics=risk_dynamics
                )
                if interpretation:
                    alert.risk_dynamics_interpretation = interpretation
            except Exception:
                # If LLM interpretation fails, continue without it
                alert.risk_dynamics_interpretation = None
        else:
            alert.risk_dynamics_interpretation = None
            
    except Exception:
        # Fail gracefully
        alert.risk_dynamics = None
        alert.risk_dynamics_interpretation = None
    
    return alert


def _attach_narrative_clusters(
    alert: TrendAlert,
    df: pd.DataFrame,
    nce,
    enrich_with_llm: bool = False
) -> TrendAlert:
    """
    Attach narrative clustering analysis to an alert (CHUNK 6.11.12).
    
    Args:
        alert: TrendAlert object to enrich
        df: DataFrame for analysis
        nce: NarrativeClusteringEngine instance
        enrich_with_llm: If True, add LLM interpretation for clusters
        
    Returns:
        TrendAlert with narrative_clusters field populated
    """
    try:
        # Extract drug and reaction from alert
        drug = None
        reaction = None
        
        if alert.details:
            drug = alert.details.get("drug") or alert.details.get("drug_name")
            reaction = alert.details.get("reaction") or alert.details.get("reaction_name")
        
        # Run narrative clustering (synchronous for Streamlit compatibility)
        clusters = nce.cluster_narratives(df, drug=drug, reaction=reaction)
        
        if clusters:
            # Enrich clusters with LLM labels if requested
            if enrich_with_llm:
                try:
                    from src.ai.medical_llm import summarize_narrative_cluster
                    import asyncio
                    
                    # Run async LLM labeling synchronously for Streamlit
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    for cluster in clusters:
                        narratives = cluster.get("all_narratives", cluster.get("examples", []))
                        if narratives and len(narratives) > 0:
                            # Run LLM labeling (synchronously for Streamlit compatibility)
                            summary = loop.run_until_complete(
                                summarize_narrative_cluster(narratives)
                            )
                            if summary:
                                cluster["summary"] = summary
                except Exception:
                    # If LLM enrichment fails, continue without it
                    pass
            
            alert.narrative_clusters = clusters
        else:
            alert.narrative_clusters = None
            
    except Exception:
        # Fail gracefully
        alert.narrative_clusters = None
    
    return alert


def _attach_lot_alerts(
    alert: TrendAlert,
    df: pd.DataFrame,
    lot_engine,
    enrich_with_llm: bool = False
) -> TrendAlert:
    """
    Attach lot/batch spike alerts to an alert (CHUNK 6.11.13).
    
    Args:
        alert: TrendAlert object to enrich
        df: DataFrame for analysis
        lot_engine: LotDetectionEngine instance
        enrich_with_llm: If True, add LLM interpretation for lot alerts
        
    Returns:
        TrendAlert with lot_alerts field populated
    """
    try:
        # Extract drug and reaction from alert
        drug = None
        reaction = None
        
        if alert.details:
            drug = alert.details.get("drug") or alert.details.get("drug_name")
            reaction = alert.details.get("reaction") or alert.details.get("reaction_name")
        
        # Detect lot spikes
        lot_alerts = lot_engine.detect_lot_spikes(df, drug=drug, reaction=reaction)
        
        if lot_alerts:
            # Enrich with LLM interpretation if requested
            if enrich_with_llm:
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    from src.ai.medical_llm import interpret_lot_alert
                    
                    for lot_alert in lot_alerts:
                        interpretation = loop.run_until_complete(
                            interpret_lot_alert(lot_alert)
                        )
                        if interpretation:
                            lot_alert["interpretation"] = interpretation
                except Exception:
                    # If LLM enrichment fails, continue without it
                    pass
            
            alert.lot_alerts = lot_alerts
        else:
            alert.lot_alerts = None
            
    except Exception:
        # Fail gracefully
        alert.lot_alerts = None
    
    return alert

# =========================================================
# END CHUNK 6.11.1 FOUNDATION
# =========================================================

# =========================================================
# CHUNK 6.11.2: Medium-Level Statistical Alerts
# Rolling baselines, Z-scores, moving averages, expected vs actual
# =========================================================

def _rolling_baseline(df: pd.DataFrame, date_col: str, group_col: str, months: int) -> Optional[pd.Series]:
    """
    Compute rolling n-month baseline counts grouped by drug/reaction (CHUNK 6.11.2).
    
    Args:
        df: DataFrame with date and group columns
        date_col: Name of date column
        group_col: Name of column to group by (drug_name, reaction, etc.)
        months: Number of months for rolling baseline
        
    Returns:
        Series with value counts or None if insufficient data
    """
    if date_col not in df.columns or group_col not in df.columns:
        return None
    
    try:
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")
        df_copy = df_copy[df_copy[date_col].notna()]
        
        if df_copy.empty:
            return None
        
        cutoff = datetime.now() - timedelta(days=30 * months)
        recent = df_copy[df_copy[date_col] >= cutoff]
        
        if recent.empty:
            return None
        
        # Handle multi-value columns (split by "; ")
        group_series = recent[group_col].astype(str).str.split("; ").explode()
        group_series = group_series[group_series.notna() & (group_series != 'nan')]
        
        if group_series.empty:
            return None
        
        return group_series.value_counts()
    except Exception:
        return None


def _alert_reaction_zscore(df: pd.DataFrame) -> Optional[TrendAlert]:
    """
    Detect reactions whose frequency is significantly higher than expected
    using a rolling 12-month baseline and Z-score anomaly detection (CHUNK 6.11.2).
    
    Returns:
        TrendAlert or None if no significant anomaly detected
    """
    # Find date column
    date_col = None
    for col in ["event_date", "report_date", "receipt_date", "receive_date", "received_date"]:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col or "reaction" not in df.columns:
        return None
    
    # Baseline: 12-month rolling baseline
    baseline = _rolling_baseline(df, date_col, "reaction", months=12)
    if baseline is None or len(baseline) == 0:
        return None
    
    # Recent: 90 days
    recent = get_last_90_days(df, date_col)
    if recent.empty:
        return None
    
    # Handle multi-value reactions
    recent_series = recent["reaction"].astype(str).str.split("; ").explode()
    recent_series = recent_series[recent_series.notna() & (recent_series != 'nan')]
    
    if recent_series.empty:
        return None
    
    recent_counts = recent_series.value_counts()
    
    # Align reactions - combine baseline and recent
    all_reactions = set(baseline.index) | set(recent_counts.index)
    
    combined_data = []
    for reaction in all_reactions:
        baseline_count = baseline.get(reaction, 0)
        recent_count = recent_counts.get(reaction, 0)
        combined_data.append({
            "reaction": reaction,
            "baseline": baseline_count,
            "recent": recent_count
        })
    
    combined = pd.DataFrame(combined_data)
    combined = combined[combined["baseline"] > 0]  # Only reactions with baseline data
    
    if combined.empty:
        return None
    
    # Calculate Z-scores
    baseline_mean = combined["baseline"].mean()
    baseline_std = combined["baseline"].std()
    
    if baseline_std == 0 or pd.isna(baseline_std):
        return None
    
    combined["z_score"] = (combined["recent"] - baseline_mean) / baseline_std
    
    # Find highest anomaly
    top_idx = combined["z_score"].idxmax()
    top_reaction = combined.loc[top_idx]
    
    z_score = top_reaction["z_score"]
    
    if pd.isna(z_score) or z_score < 2.0:  # Not strong enough anomaly (< 2 standard deviations)
        return None
    
    severity = "critical" if z_score >= 4.0 else "warning"
    
    return TrendAlert(
        id="reaction_zscore",
        title=f"Reaction '{top_reaction['reaction']}' shows abnormal growth",
        severity=severity,
        summary=f"Z-score of {z_score:.2f} indicates unusual increase compared to 12-month baseline.",
        metric_value=float(z_score),
        metric_unit="z-score",
        details={
            "reaction": top_reaction["reaction"],
            "baseline_count": int(top_reaction["baseline"]),
            "recent_count": int(top_reaction["recent"]),
            "baseline_mean": float(baseline_mean),
            "baseline_std": float(baseline_std)
        },
        suggested_action=f"Review '{top_reaction['reaction']}' reaction for clinical clustering and seriousness pattern."
    )


def _alert_drug_baseline_delta(df: pd.DataFrame) -> Optional[TrendAlert]:
    """
    Compare drug frequency against 6-month baseline and detect sharp deviations (CHUNK 6.11.2).
    
    Returns:
        TrendAlert or None if no significant deviation
    """
    # Find date column
    date_col = None
    for col in ["event_date", "report_date", "receipt_date", "receive_date", "received_date"]:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col or "drug_name" not in df.columns:
        return None
    
    # Baseline: 6-month rolling baseline
    baseline = _rolling_baseline(df, date_col, "drug_name", months=6)
    if baseline is None or len(baseline) == 0:
        return None
    
    # Recent: 90 days
    recent = get_last_90_days(df, date_col)
    if recent.empty:
        return None
    
    # Handle multi-value drugs
    recent_series = recent["drug_name"].astype(str).str.split("; ").explode()
    recent_series = recent_series[recent_series.notna() & (recent_series != 'nan')]
    
    if recent_series.empty:
        return None
    
    recent_counts = recent_series.value_counts()
    
    # Align drugs - combine baseline and recent
    all_drugs = set(baseline.index) | set(recent_counts.index)
    
    combined_data = []
    for drug in all_drugs:
        baseline_count = baseline.get(drug, 0)
        recent_count = recent_counts.get(drug, 0)
        combined_data.append({
            "drug": drug,
            "baseline": baseline_count,
            "recent": recent_count
        })
    
    combined = pd.DataFrame(combined_data)
    combined = combined[combined["baseline"] > 0]  # Only drugs with baseline data
    
    if combined.empty:
        return None
    
    # Calculate percent change
    combined["pct_change"] = ((combined["recent"] - combined["baseline"]) / combined["baseline"]) * 100
    
    # Find highest deviation
    top_idx = combined["pct_change"].idxmax()
    top_drug = combined.loc[top_idx]
    
    pct_change = top_drug["pct_change"]
    
    if pd.isna(pct_change) or pct_change < 50:  # <50% change is not notable
        return None
    
    severity = "warning" if pct_change >= 100 else "info"
    
    return TrendAlert(
        id="drug_baseline_delta",
        title=f"Drug '{top_drug['drug']}' deviates from 6-month baseline",
        severity=severity,
        summary=f"'{top_drug['drug']}' increased by {pct_change:.1f}% compared to 6-month baseline.",
        metric_value=float(pct_change),
        metric_unit="percent_change",
        details={
            "drug": top_drug["drug"],
            "baseline_count": int(top_drug["baseline"]),
            "recent_count": int(top_drug["recent"]),
            "baseline_period_months": 6,
            "recent_period_days": 90
        },
        suggested_action=f"Investigate reaction distribution and case narratives for '{top_drug['drug']}'."
    )


def _alert_seriousness_trend_stability(df: pd.DataFrame) -> Optional[TrendAlert]:
    """
    Detect if seriousness proportion is unstable over time (CHUNK 6.11.2).
    Uses 6-month rolling baseline vs recent 90 days.
    
    Returns:
        TrendAlert or None if trend is stable
    """
    # Find date column and seriousness column
    date_col = None
    for col in ["event_date", "report_date", "receipt_date", "receive_date", "received_date"]:
        if col in df.columns:
            date_col = col
            break
    
    serious_col = None
    for col in ["seriousness", "serious"]:
        if col in df.columns:
            serious_col = col
            break
    
    if not date_col or not serious_col:
        return None
    
    try:
        # Get baseline (6-month) serious rate
        baseline_cutoff = datetime.now() - timedelta(days=180)
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")
        df_copy = df_copy[df_copy[date_col].notna()]
        
        baseline_df = df_copy[df_copy[date_col] >= baseline_cutoff]
        baseline_df = baseline_df[baseline_df[date_col] < (datetime.now() - timedelta(days=90))]
        
        if len(baseline_df) == 0:
            return None
        
        # Calculate baseline serious rate
        if serious_col in baseline_df.columns:
            serious_series = baseline_df[serious_col]
            if serious_series.dtype == bool:
                baseline_serious = serious_series.sum()
            else:
                baseline_serious = serious_series.astype(str).str.lower().isin(['true', '1', 'yes', 'y', 'serious']).sum()
            baseline_rate = baseline_serious / len(baseline_df) * 100
        else:
            return None
        
        # Get recent (90 days) serious rate
        recent = get_last_90_days(df, date_col)
        if recent.empty:
            return None
        
        if serious_col in recent.columns:
            serious_series = recent[serious_col]
            if serious_series.dtype == bool:
                recent_serious = serious_series.sum()
            else:
                recent_serious = serious_series.astype(str).str.lower().isin(['true', '1', 'yes', 'y', 'serious']).sum()
            recent_rate = recent_serious / len(recent) * 100
        else:
            return None
        
        # Calculate change
        change = recent_rate - baseline_rate
        change_pct = safe_pct_change(baseline_rate, recent_rate)
        
        # Only alert for significant changes (>20 percentage points or >30% relative change)
        if abs(change) < 20 and (change_pct is None or abs(change_pct) < 30):
            return None
        
        severity = "warning" if abs(change) >= 30 or (change_pct and abs(change_pct) >= 50) else "info"
        
        return TrendAlert(
            id="seriousness_trend_stability",
            title="Seriousness proportion trend instability detected",
            severity=severity,
            summary=f"Serious case rate changed from {baseline_rate:.1f}% (6-month baseline) to {recent_rate:.1f}% (recent 90 days).",
            metric_value=float(change),
            metric_unit="percentage_points",
            details={
                "baseline_rate": float(baseline_rate),
                "recent_rate": float(recent_rate),
                "change": float(change),
                "change_percent": change_pct,
                "baseline_cases": len(baseline_df),
                "recent_cases": len(recent)
            },
            suggested_action="Review causes of seriousness trend shift - may indicate reporting changes or true safety signal."
        )
    except Exception:
        return None

# =========================================================
# END CHUNK 6.11.2 MEDIUM-LEVEL STATISTICAL ALERTS
# =========================================================


def detect_trend_alerts_light(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Light-weight trend alerts (Option 3 Hybrid - fast, always-on).
    Uses cached data and simple calculations for instant results.
    
    CHUNK 6.11: Fast trend detection for real-time alerts.
    
    Returns:
        Dictionary with top alerts (limited set for speed)
    """
    if df is None or len(df) == 0:
        return {
            "alerts": [],
            "spikes": [],
            "emerging_signals": [],
            "trend_notes": [],
            "meta": {"total_cases": 0, "mode": "light"}
        }
    
    alerts = []
    spikes = []
    emerging_signals = []
    
    date_col = _find_date_column(df)
    
    # Light detection: Only check top 10 drugs/reactions (fast)
    if "drug_name" in df.columns and date_col:
        try:
            drug_series = df["drug_name"].astype(str).str.split("; ").explode()
            drug_series = drug_series[drug_series.notna() & (drug_series != 'nan')]
            top_drugs = drug_series.value_counts().head(10).index.tolist()
            
            for drug in top_drugs[:5]:  # Only top 5 for speed
                drug_mask = df["drug_name"].astype(str).str.contains(drug, case=False, na=False)
                drug_df = df[drug_mask].copy()
                
                if len(drug_df) < 20:
                    continue
                
                try:
                    drug_df[date_col] = pd.to_datetime(drug_df[date_col], errors="coerce")
                    drug_df = drug_df[drug_df[date_col].notna()]
                    
                    if len(drug_df) < 6:
                        continue
                    
                    drug_df["month"] = drug_df[date_col].dt.to_period("M")
                    monthly_counts = drug_df.groupby("month").size()
                    
                    if len(monthly_counts) >= 3:
                        # Simple spike: last month vs average of previous 3
                        recent = monthly_counts.tail(1).iloc[0] if len(monthly_counts) >= 1 else 0
                        baseline = monthly_counts.tail(4).head(3).mean() if len(monthly_counts) >= 4 else monthly_counts.mean()
                        
                        if baseline > 0 and recent > baseline * 2.5:  # 2.5x spike
                            spike_ratio = recent / baseline
                            spikes.append({
                                "type": "drug_spike",
                                "drug": drug,
                                "period": str(monthly_counts.index[-1]),
                                "count": int(recent),
                                "baseline": float(baseline),
                                "increase_ratio": float(spike_ratio),
                                "severity": "high" if spike_ratio > 4.0 else "medium",
                                "message": f"🚨 {drug} cases spiked {spike_ratio:.1f}x in {str(monthly_counts.index[-1])} "
                                         f"({int(recent)} cases vs {baseline:.1f} baseline)"
                            })
                except Exception:
                    continue
        except Exception:
            pass
    
    # Return limited set for speed (top 5)
    return {
        "alerts": [],
        "spikes": spikes[:5],  # Top 5 only
        "emerging_signals": [],
        "trend_notes": [],
        "meta": {
            "total_cases": len(df),
            "mode": "light",
            "detection_date": datetime.now().isoformat()
        }
    }


def detect_trend_alerts_heavy(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Heavy-weight trend alerts (Option 3 Hybrid - on-demand only).
    Full comprehensive analysis with all detectors and LLM interpretation.
    
    CHUNK 6.11: Complete trend detection for detailed analysis.
    
    Returns:
        Full dictionary with all alerts, signals, and interpretations
    """
    # Call full analysis with mode="heavy"
    return detect_trend_alerts(df, mode="heavy")


def detect_trend_alerts(df: pd.DataFrame, mode: str = "auto") -> Dict[str, Any]:
    """
    Analyze dataset and detect meaningful safety-related trends,
    spikes, anomalies, and emerging signal-like patterns.
    
    CHUNK 6.11: Comprehensive trend alerts engine.
    
    Args:
        df: DataFrame with PV data
        mode: "auto" (smart selection), "light" (fast), or "heavy" (full analysis)
    
    Returns:
        A dictionary containing:
        {
            "alerts": [...],          # High-priority alerts
            "spikes": [...],          # Temporal spikes detected
            "emerging_signals": [...], # Emerging drug-reaction signals
            "trend_notes": [...],     # Notable trends
            "meta": {...}             # Metadata
        }
    """
    # Smart mode selection (Option 3 Hybrid)
    if mode == "light":
        return detect_trend_alerts_light(df)
    # mode == "auto" or "heavy" - use full analysis below
    
    if df is None or len(df) == 0:
        return {
            "alerts": [],
            "spikes": [],
            "emerging_signals": [],
            "trend_notes": [],
            "meta": {"total_cases": 0}
        }
    
    alerts = []
    spikes = []
    emerging_signals = []
    trend_notes = []
    
    total_cases = len(df)
    
    # Helper: Find date column
    date_col = _find_date_column(df)
    
    # ============================================================
    # PART 1: Drug-Level Trend Detection
    # ============================================================
    drug_trends = _detect_drug_trends(df, date_col)
    if drug_trends:
        alerts.extend(drug_trends.get("alerts", []))
        spikes.extend(drug_trends.get("spikes", []))
        trend_notes.extend(drug_trends.get("notes", []))
    
    # ============================================================
    # PART 2: Reaction-Level Trend Detection
    # ============================================================
    reaction_trends = _detect_reaction_trends(df, date_col)
    if reaction_trends:
        alerts.extend(reaction_trends.get("alerts", []))
        spikes.extend(reaction_trends.get("spikes", []))
        trend_notes.extend(reaction_trends.get("notes", []))
    
    # ============================================================
    # PART 3: Emerging Drug-Reaction Signals
    # ============================================================
    signals = _detect_emerging_signals(df, date_col)
    if signals:
        emerging_signals.extend(signals)
    
    # ============================================================
    # PART 4: Overall Dataset Trends
    # ============================================================
    overall_trends = _detect_overall_trends(df, date_col)
    if overall_trends:
        alerts.extend(overall_trends.get("alerts", []))
        trend_notes.extend(overall_trends.get("notes", []))
    
    # ============================================================
    # PART 5: Disproportionality Changes
    # ============================================================
    disproportionality_changes = _detect_disproportionality_changes(df, date_col)
    if disproportionality_changes:
        alerts.extend(disproportionality_changes)
    
    # ============================================================
    # CHUNK 6.12: Risk Prioritization Framework (RPF)
    # ============================================================
    rpf_ranked = []
    if mode == "heavy" and (alerts or emerging_signals):
        try:
            from src.ai.risk_prioritization import RiskPrioritizationEngine
            rpf_engine = RiskPrioritizationEngine()
            
            # Extract signals from alerts and emerging_signals
            all_signals_for_rpf = rpf_engine.extract_signals_from_alerts(alerts + emerging_signals, df)
            
            # Prioritize signals
            if all_signals_for_rpf:
                rpf_ranked = rpf_engine.prioritize(all_signals_for_rpf)
        except Exception:
            # Fail gracefully if RPF engine not available
            rpf_ranked = []
    
    # ============================================================
    # PART 5B: Medium-Level Statistical Alerts (CHUNK 6.11.2)
    # ============================================================
    medium_alerts = []
    for fn in [
        _alert_reaction_zscore,
        _alert_drug_baseline_delta,
        _alert_seriousness_trend_stability,
    ]:
        try:
            alert = fn(df)
            if alert:
                # Convert TrendAlert to dict format for consistency
                medium_alerts.append({
                    "type": alert.id,
                    "severity": alert.severity,
                    "message": alert.title,
                    "summary": alert.summary,
                    "metric_value": alert.metric_value,
                    "metric_unit": alert.metric_unit,
                    "details": alert.details,
                    "suggested_action": alert.suggested_action,
                    "source": "medium_statistical"
                })
        except Exception:
            continue
    
    alerts.extend(medium_alerts)
    
    # Sort alerts by severity/priority
    alerts = _prioritize_alerts(alerts)
    
    # ============================================================
    # CHUNK 6.12: Risk Prioritization Framework (RPF)
    # ============================================================
    rpf_ranked = []
    if mode == "heavy" and (alerts or emerging_signals):
        try:
            from src.ai.risk_prioritization import RiskPrioritizationEngine
            rpf_engine = RiskPrioritizationEngine()
            
            # Extract signals from alerts and emerging_signals
            all_signals_for_rpf = rpf_engine.extract_signals_from_alerts(alerts + emerging_signals, df)
            
            # Prioritize signals
            if all_signals_for_rpf:
                rpf_ranked = rpf_engine.prioritize(all_signals_for_rpf)
        except Exception:
            # Fail gracefully if RPF engine not available
            rpf_ranked = []
    
    # ============================================================
    # PART 6: LLM-Based Interpretation (CHUNK 6.11-B)
    # ============================================================
    # Add LLM interpretation to top alerts
    interpreted_alerts = _add_llm_interpretation(alerts[:5])  # Interpret top 5
    interpreted_signals = _add_llm_interpretation_to_signals(emerging_signals[:3])  # Interpret top 3
    
    # Merge interpreted alerts back
    final_alerts = interpreted_alerts + alerts[5:10]  # Top 5 interpreted + next 5 without interpretation
    
    return {
        "alerts": final_alerts[:10],  # Top 10 alerts (with LLM interpretation for top 5)
        "spikes": spikes[:10],  # Top 10 spikes
        "emerging_signals": interpreted_signals + emerging_signals[3:10],  # Top 3 interpreted + next 7
        "trend_notes": trend_notes[:10],  # Top 10 notes
        "rpf_ranked": rpf_ranked,  # CHUNK 6.12: Risk Prioritization Framework
        "meta": {
            "total_cases": total_cases,
            "total_alerts": len(alerts),
            "total_spikes": len(spikes),
            "total_signals": len(emerging_signals),
            "detection_date": datetime.now().isoformat(),
            "llm_interpretation_enabled": True,
            "mode": "heavy",
            "rpf_enabled": len(rpf_ranked) > 0  # CHUNK 6.12
        }
    }


def _find_date_column(df: pd.DataFrame) -> Optional[str]:
    """Find the best date column in the dataframe."""
    date_columns = ["report_date", "receipt_date", "receive_date", "received_date", 
                    "event_date", "onset_date", "date"]
    
    for col in date_columns:
        if col in df.columns:
            return col
    return None


def _detect_drug_trends(df: pd.DataFrame, date_col: Optional[str]) -> Dict[str, List]:
    """
    Detect drug-level trends, spikes, and anomalies.
    
    Returns:
        Dict with "alerts", "spikes", "notes" lists
    """
    alerts = []
    spikes = []
    notes = []
    
    if date_col is None or "drug_name" not in df.columns:
        return {"alerts": alerts, "spikes": spikes, "notes": notes}
    
    # Get top drugs by frequency
    drug_series = df["drug_name"].astype(str).str.split("; ").explode()
    drug_series = drug_series[drug_series.notna() & (drug_series != 'nan')]
    top_drugs = drug_series.value_counts().head(20).index.tolist()
    
    # Analyze each top drug
    for drug in top_drugs:
        # Filter cases for this drug
        drug_mask = df["drug_name"].astype(str).str.contains(drug, case=False, na=False)
        drug_df = df[drug_mask].copy()
        
        if len(drug_df) < 10:  # Need minimum cases
            continue
        
        # Get monthly trend
        try:
            drug_df[date_col] = pd.to_datetime(drug_df[date_col], errors="coerce")
            drug_df = drug_df[drug_df[date_col].notna()]
            
            if len(drug_df) < 6:  # Need enough time points
                continue
            
            drug_df["month"] = drug_df[date_col].dt.to_period("M")
            monthly_counts = drug_df.groupby("month").size()
            
            if len(monthly_counts) < 3:
                continue
            
            # Convert to dict for spike detection
            trend_dict = {str(period): int(count) for period, count in monthly_counts.items()}
            
            # Detect spikes
            detected_spikes = detect_spikes(trend_dict, window_size=3, threshold_multiplier=2.0, min_cases=5)
            
            if detected_spikes:
                for spike in detected_spikes[:3]:  # Top 3 spikes per drug
                    spike_ratio = spike.get("spike_ratio", 1.0)
                    if spike_ratio > 2.0:  # 2x increase
                        spikes.append({
                            "type": "drug_spike",
                            "drug": drug,
                            "period": spike.get("period_str", ""),
                            "count": spike.get("count", 0),
                            "baseline": spike.get("baseline_mean", 0),
                            "increase_ratio": spike_ratio,
                            "severity": "high" if spike_ratio > 3.0 else "medium",
                            "message": f"⚠️ {drug} cases spiked {spike_ratio:.1f}x in {spike.get('period_str', 'period')} "
                                     f"({spike.get('count', 0)} cases vs {spike.get('baseline_mean', 0):.1f} baseline)"
                        })
            
            # Detect changepoint (sudden shift in baseline)
            changepoint = analyze_trend_changepoint(trend_dict)
            if changepoint and changepoint.get("change_ratio", 1.0) > 1.5:
                alerts.append({
                    "type": "drug_trend_change",
                    "drug": drug,
                    "changepoint_period": changepoint.get("split_period_str", ""),
                    "before_avg": changepoint.get("before_mean", 0),
                    "after_avg": changepoint.get("after_mean", 0),
                    "change_ratio": changepoint.get("change_ratio", 1.0),
                    "severity": "medium",
                    "message": f"📈 {drug} shows sustained trend change starting {changepoint.get('split_period_str', 'period')}: "
                             f"{changepoint.get('after_mean', 0):.1f} avg vs {changepoint.get('before_mean', 0):.1f} avg before"
                })
            
            # Quarter-over-quarter comparison
            if len(monthly_counts) >= 6:
                recent_3m = monthly_counts.tail(3).sum()
                previous_3m = monthly_counts.tail(6).head(3).sum()
                
                if previous_3m > 0:
                    qoq_change = safe_divide(recent_3m - previous_3m, previous_3m, 0.0)
                    if abs(qoq_change) > 0.3:  # 30% change
                        direction = "increased" if qoq_change > 0 else "decreased"
                        notes.append({
                            "type": "drug_quarter_trend",
                            "drug": drug,
                            "direction": direction,
                            "change_pct": abs(qoq_change) * 100,
                            "recent_count": int(recent_3m),
                            "previous_count": int(previous_3m),
                            "message": f"📊 {drug} cases {direction} {abs(qoq_change)*100:.1f}% "
                                     f"in last quarter ({int(recent_3m)} vs {int(previous_3m)})"
                        })
        
        except Exception:
            continue  # Skip if analysis fails
    
    return {"alerts": alerts, "spikes": spikes, "notes": notes}


def _detect_reaction_trends(df: pd.DataFrame, date_col: Optional[str]) -> Dict[str, List]:
    """
    Detect reaction-level trends and spikes.
    
    Returns:
        Dict with "alerts", "spikes", "notes" lists
    """
    alerts = []
    spikes = []
    notes = []
    
    if date_col is None or "reaction" not in df.columns:
        return {"alerts": alerts, "spikes": spikes, "notes": notes}
    
    # Get top reactions
    reaction_series = df["reaction"].astype(str).str.split("; ").explode()
    reaction_series = reaction_series[reaction_series.notna() & (reaction_series != 'nan')]
    top_reactions = reaction_series.value_counts().head(20).index.tolist()
    
    for reaction in top_reactions:
        # Filter cases for this reaction
        reaction_mask = df["reaction"].astype(str).str.contains(reaction, case=False, na=False)
        reaction_df = df[reaction_mask].copy()
        
        if len(reaction_df) < 10:
            continue
        
        try:
            reaction_df[date_col] = pd.to_datetime(reaction_df[date_col], errors="coerce")
            reaction_df = reaction_df[reaction_df[date_col].notna()]
            
            if len(reaction_df) < 6:
                continue
            
            reaction_df["month"] = reaction_df[date_col].dt.to_period("M")
            monthly_counts = reaction_df.groupby("month").size()
            
            if len(monthly_counts) < 3:
                continue
            
            trend_dict = {str(period): int(count) for period, count in monthly_counts.items()}
            
            # Detect spikes
            detected_spikes = detect_spikes(trend_dict, window_size=3, threshold_multiplier=2.0, min_cases=5)
            
            if detected_spikes:
                for spike in detected_spikes[:2]:  # Top 2 spikes per reaction
                    spike_ratio = spike.get("spike_ratio", 1.0)
                    if spike_ratio > 2.5:
                        spikes.append({
                            "type": "reaction_spike",
                            "reaction": reaction,
                            "period": spike.get("period_str", ""),
                            "count": spike.get("count", 0),
                            "increase_ratio": spike_ratio,
                            "severity": "high" if spike_ratio > 3.5 else "medium",
                            "message": f"⚠️ {reaction} cases spiked {spike_ratio:.1f}x in {spike.get('period_str', 'period')} "
                                     f"({spike.get('count', 0)} cases)"
                        })
        
        except Exception:
            continue
    
    return {"alerts": alerts, "spikes": spikes, "notes": notes}


def _detect_emerging_signals(df: pd.DataFrame, date_col: Optional[str]) -> List[Dict]:
    """
    Detect emerging drug-reaction combinations (new or rapidly increasing).
    
    Returns:
        List of emerging signal dictionaries
    """
    signals = []
    
    if date_col is None or "drug_name" not in df.columns or "reaction" not in df.columns:
        return signals
    
    try:
        df_with_date = df.copy()
        df_with_date[date_col] = pd.to_datetime(df_with_date[date_col], errors="coerce")
        df_with_date = df_with_date[df_with_date[date_col].notna()]
        
        if len(df_with_date) < 50:
            return signals
        
        # Split drug_name and reaction (handle multi-value)
        df_with_date["drug_list"] = df_with_date["drug_name"].astype(str).str.split("; ")
        df_with_date["reaction_list"] = df_with_date["reaction"].astype(str).str.split("; ")
        
        # Explode to get all drug-reaction pairs
        drug_reaction_pairs = []
        for idx, row in df_with_date.iterrows():
            drugs = row["drug_list"]
            reactions = row["reaction_list"]
            date_val = row[date_col]
            
            for drug in drugs:
                if pd.notna(drug) and str(drug).strip() and str(drug).lower() != 'nan':
                    for reaction in reactions:
                        if pd.notna(reaction) and str(reaction).strip() and str(reaction).lower() != 'nan':
                            drug_reaction_pairs.append({
                                "drug": str(drug).strip(),
                                "reaction": str(reaction).strip(),
                                "date": date_val
                            })
        
        pairs_df = pd.DataFrame(drug_reaction_pairs)
        
        if len(pairs_df) == 0:
            return signals
        
        # Get recent vs older periods
        pairs_df["month"] = pairs_df["date"].dt.to_period("M")
        max_date = pairs_df["date"].max()
        cutoff_date = max_date - timedelta(days=90)  # Last 3 months
        
        recent_df = pairs_df[pairs_df["date"] >= cutoff_date]
        older_df = pairs_df[pairs_df["date"] < cutoff_date]
        
        # Count pairs in each period
        recent_counts = recent_df.groupby(["drug", "reaction"]).size()
        older_counts = older_df.groupby(["drug", "reaction"]).size()
        
        # Find pairs that are new or rapidly increasing
        for (drug, reaction), recent_count in recent_counts.items():
            older_count = older_counts.get((drug, reaction), 0)
            
            # Must have minimum cases in recent period
            if recent_count < 5:
                continue
            
            # New signal (not in older period) or rapid increase
            if older_count == 0 and recent_count >= 5:
                # New emerging signal
                signals.append({
                    "type": "emerging_signal",
                    "drug": drug,
                    "reaction": reaction,
                    "recent_cases": int(recent_count),
                    "older_cases": 0,
                    "growth_ratio": float('inf'),
                    "severity": "medium",
                    "message": f"🆕 Emerging signal: {drug} + {reaction} "
                             f"({int(recent_count)} cases in last 3 months, new combination)"
                })
            elif older_count > 0:
                growth_ratio = safe_divide(recent_count, older_count, 0.0)
                if growth_ratio > 3.0:  # 3x increase
                    signals.append({
                        "type": "rapid_increase",
                        "drug": drug,
                        "reaction": reaction,
                        "recent_cases": int(recent_count),
                        "older_cases": int(older_count),
                        "growth_ratio": growth_ratio,
                        "severity": "high" if growth_ratio > 5.0 else "medium",
                        "message": f"📈 Rapid increase: {drug} + {reaction} "
                                 f"({int(recent_count)} cases vs {int(older_count)} in previous period, "
                                 f"{growth_ratio:.1f}x increase)"
                    })
    
    except Exception as e:
        # Fail silently - return empty signals
        pass
    
    return signals


def _detect_overall_trends(df: pd.DataFrame, date_col: Optional[str]) -> Dict[str, List]:
    """
    Detect overall dataset trends (not drug/reaction specific).
    
    Returns:
        Dict with "alerts", "notes" lists
    """
    alerts = []
    notes = []
    
    if date_col is None:
        return {"alerts": alerts, "notes": notes}
    
    try:
        df_with_date = df.copy()
        df_with_date[date_col] = pd.to_datetime(df_with_date[date_col], errors="coerce")
        df_with_date = df_with_date[df_with_date[date_col].notna()]
        
        if len(df_with_date) < 12:
            return {"alerts": alerts, "notes": notes}
        
        df_with_date["month"] = df_with_date[date_col].dt.to_period("M")
        monthly_counts = df_with_date.groupby("month").size()
        
        if len(monthly_counts) < 6:
            return {"alerts": alerts, "notes": notes}
        
        # Overall trend direction
        sorted_periods = sorted(monthly_counts.index)
        first_half = monthly_counts[sorted_periods[:len(sorted_periods)//2]].sum()
        second_half = monthly_counts[sorted_periods[len(sorted_periods)//2:]].sum()
        
        if first_half > 0:
            trend_ratio = safe_divide(second_half, first_half, 0.0)
            
            if trend_ratio > 1.3:
                alerts.append({
                    "type": "overall_increase",
                    "change_pct": (trend_ratio - 1.0) * 100,
                    "severity": "medium",
                    "message": f"📊 Overall case volume increased {(trend_ratio - 1.0)*100:.1f}% "
                             f"in second half of dataset"
                })
            elif trend_ratio < 0.7:
                notes.append({
                    "type": "overall_decrease",
                    "change_pct": (1.0 - trend_ratio) * 100,
                    "message": f"📉 Overall case volume decreased {(1.0 - trend_ratio)*100:.1f}% "
                             f"in second half of dataset"
                })
        
        # Detect overall spike
        trend_dict = {str(period): int(count) for period, count in monthly_counts.items()}
        overall_spikes = detect_spikes(trend_dict, window_size=3, threshold_multiplier=2.5, min_cases=10)
        
        if overall_spikes:
            spike = overall_spikes[0]  # Most significant
            alerts.append({
                "type": "overall_spike",
                "period": spike.get("period_str", ""),
                "count": spike.get("count", 0),
                "increase_ratio": spike.get("spike_ratio", 1.0),
                "severity": "high",
                "message": f"⚠️ Overall dataset spike detected in {spike.get('period_str', 'period')}: "
                         f"{spike.get('count', 0)} cases ({spike.get('spike_ratio', 1.0):.1f}x increase)"
            })
    
    except Exception:
        pass
    
    return {"alerts": alerts, "notes": notes}


def _detect_disproportionality_changes(df: pd.DataFrame, date_col: Optional[str]) -> List[Dict]:
    """
    Detect changes in disproportionality (PRR/ROR) over time.
    Note: This is a simplified version - full PRR/ROR requires signal_stats module.
    
    Returns:
        List of disproportionality alert dictionaries
    """
    alerts = []
    
    # This is a placeholder for more complex disproportionality analysis
    # Full implementation would require:
    # - Splitting data by time periods
    # - Calculating PRR/ROR for each period
    # - Detecting significant changes
    
    return alerts


def _prioritize_alerts(alerts: List[Dict]) -> List[Dict]:
    """
    Sort alerts by severity and importance.
    
    Priority order:
    1. High severity
    2. Medium severity
    3. Low severity
    """
    severity_order = {"high": 0, "medium": 1, "low": 2}
    
    def alert_key(alert):
        severity = alert.get("severity", "low")
        return (severity_order.get(severity, 2), alert.get("increase_ratio", 0))
    
    return sorted(alerts, key=alert_key)


def _add_llm_interpretation(alerts: List[Dict]) -> List[Dict]:
    """
    Add LLM-powered clinical interpretation to alerts (CHUNK 6.11-B).
    
    Args:
        alerts: List of alert dictionaries
        
    Returns:
        List of alerts with added 'llm_interpretation' field
    """
    if not alerts:
        return alerts
    
    try:
        from src.ai.medical_llm import call_medical_llm
    except Exception:
        # If LLM not available, return alerts as-is
        return alerts
    
    interpreted_alerts = []
    
    for alert in alerts:
        # Create interpretation prompt
        alert_type = alert.get("type", "")
        message = alert.get("message", "")
        drug = alert.get("drug", "")
        reaction = alert.get("reaction", "")
        increase_ratio = alert.get("increase_ratio", 1.0)
        period = alert.get("period", alert.get("changepoint_period", ""))
        severity = alert.get("severity", "medium")
        
        # Build context for LLM
        context = f"""
Alert Type: {alert_type}
Drug: {drug if drug else 'N/A'}
Reaction: {reaction if reaction else 'N/A'}
Time Period: {period}
Severity: {severity}
Increase Ratio: {increase_ratio:.1f}x
Alert Message: {message}
"""
        
        system_prompt = """You are an expert pharmacovigilance analyst AI. 
Analyze safety alerts and provide:
1. Clinical interpretation (what this might mean)
2. Possible mechanisms (if known)
3. Regulatory risk level (low/medium/high)
4. Next steps for investigation

Be concise (2-3 sentences), medically appropriate, and emphasize that these are exploratory metrics requiring further investigation."""
        
        prompt = f"""Analyze this pharmacovigilance alert:

{context}

Provide a brief interpretation covering:
1. Clinical significance
2. Possible causes/mechanisms
3. Recommended next steps

Format as a single concise paragraph (2-3 sentences)."""
        
        # Call LLM for interpretation
        interpretation = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="causal_reasoning",  # Prefers Claude for better reasoning
            max_tokens=200,
            temperature=0.3
        )
        
        # Add interpretation to alert (or keep original if LLM fails)
        alert_copy = alert.copy()
        if interpretation:
            alert_copy["llm_interpretation"] = interpretation.strip()
            alert_copy["has_llm_interpretation"] = True
        else:
            alert_copy["has_llm_interpretation"] = False
        
        interpreted_alerts.append(alert_copy)
    
    return interpreted_alerts


def _add_llm_interpretation_to_signals(signals: List[Dict]) -> List[Dict]:
    """
    Add LLM-powered interpretation to emerging signals (CHUNK 6.11-B).
    
    Args:
        signals: List of emerging signal dictionaries
        
    Returns:
        List of signals with added 'llm_interpretation' field
    """
    if not signals:
        return signals
    
    try:
        from src.ai.medical_llm import call_medical_llm
    except Exception:
        return signals
    
    interpreted_signals = []
    
    for signal in signals:
        signal_type = signal.get("type", "")
        drug = signal.get("drug", "")
        reaction = signal.get("reaction", "")
        recent_cases = signal.get("recent_cases", 0)
        older_cases = signal.get("older_cases", 0)
        growth_ratio = signal.get("growth_ratio", 1.0)
        message = signal.get("message", "")
        
        context = f"""
Signal Type: {signal_type}
Drug: {drug}
Reaction: {reaction}
Recent Cases (last 3 months): {recent_cases}
Previous Cases: {older_cases}
Growth Ratio: {growth_ratio:.1f}x
Signal Message: {message}
"""
        
        system_prompt = """You are an expert pharmacovigilance signal detection AI.
Analyze emerging drug-reaction signals and provide:
1. Clinical relevance assessment
2. Signal strength evaluation
3. Recommended investigation priority
4. Potential regulatory implications

Be concise and emphasize that early signals require validation."""
        
        prompt = f"""Analyze this emerging safety signal:

{context}

Provide a brief assessment covering:
1. Signal strength and clinical relevance
2. Whether this warrants immediate investigation
3. Recommended analytical next steps

Format as a single concise paragraph (2-3 sentences)."""
        
        interpretation = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="causal_reasoning",
            max_tokens=200,
            temperature=0.3
        )
        
        signal_copy = signal.copy()
        if interpretation:
            signal_copy["llm_interpretation"] = interpretation.strip()
            signal_copy["has_llm_interpretation"] = True
        else:
            signal_copy["has_llm_interpretation"] = False
        
        interpreted_signals.append(signal_copy)
    
    return interpreted_signals
