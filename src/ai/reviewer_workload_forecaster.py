"""
Reviewer Workload Forecaster (CHUNK B6)
Risk-weighted workload forecasting and load balancing for PV reviewers.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

try:
    from .medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


def compute_reviewer_risk_load_score(
    reviewer_signals: List[Dict[str, Any]]
) -> float:
    """
    Compute Reviewer Risk Load Score (RLS) for a reviewer.
    
    Formula: RLS = Σ (severity_weight × lifecycle_weight × 1 / days_until_due)
    
    Args:
        reviewer_signals: List of signals assigned to this reviewer
        
    Returns:
        Risk Load Score (higher = more burdened)
    """
    if not reviewer_signals:
        return 0.0
    
    severity_weights = {
        "high": 1.0,
        "critical": 1.0,
        "medium": 0.6,
        "low": 0.3
    }
    
    lifecycle_weights = {
        "assessment": 1.0,
        "capa": 1.0,
        "corrective/preventive action (capa)": 1.0,
        "evaluation": 0.7,
        "validation": 0.7,
        "recommendation": 0.7,
        "triaging": 0.3,
        "triage": 0.3,
        "closed": 0.3,
        "archived": 0.3
    }
    
    total_rls = 0.0
    
    for signal in reviewer_signals:
        # Severity weight
        priority = signal.get("priority", signal.get("qsp_priority", "low")).lower()
        severity_weight = severity_weights.get(priority, 0.5)
        
        # Lifecycle weight
        lifecycle = signal.get("lifecycle", signal.get("status", "")).lower()
        lifecycle_weight = lifecycle_weights.get(lifecycle, 0.5)
        
        # Days until due (urgency factor)
        due_date_str = signal.get("due_date")
        days_until_due = 30.0  # Default to 30 days if not specified
        
        if due_date_str:
            try:
                if isinstance(due_date_str, str):
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    days_until_due = max(1.0, (due_date - datetime.now()).days)
                else:
                    days_until_due = max(1.0, (due_date_str - datetime.now()).days)
            except Exception:
                days_until_due = 30.0
        
        # Urgency factor (inverse of days until due)
        urgency_factor = 1.0 / max(1.0, days_until_due)
        
        # Calculate signal contribution to RLS
        signal_rls = severity_weight * lifecycle_weight * urgency_factor
        total_rls += signal_rls
    
    return round(total_rls, 2)


def forecast_reviewer_workload(
    reviewers_df: pd.DataFrame,
    signals: List[Dict[str, Any]],
    forecast_days: int = 30
) -> pd.DataFrame:
    """
    Forecast reviewer workload for the next N days.
    
    Args:
        reviewers_df: DataFrame with reviewer information
        signals: List of all signals
        forecast_days: Number of days to forecast ahead
        
    Returns:
        DataFrame with forecasted workload metrics
    """
    if reviewers_df is None or reviewers_df.empty:
        return pd.DataFrame()
    
    reviewer_stats = []
    
    for _, reviewer_row in reviewers_df.iterrows():
        reviewer_name = reviewer_row.get("name", "Unknown")
        
        # Get signals assigned to this reviewer
        reviewer_signals = [
            s for s in signals
            if s.get("owner") == reviewer_name or
               s.get("reviewer") == reviewer_name or
               s.get("assigned_reviewer") == reviewer_name
        ]
        
        # Calculate current metrics
        open_reviews = len(reviewer_signals)
        rls = compute_reviewer_risk_load_score(reviewer_signals)
        
        # Count by priority
        high_priority_count = sum(
            1 for s in reviewer_signals
            if s.get("priority", "").lower() in ["high", "critical"]
        )
        
        # Count overdue
        overdue_count = 0
        upcoming_deadlines = 0
        
        for signal in reviewer_signals:
            due_date_str = signal.get("due_date")
            if due_date_str:
                try:
                    if isinstance(due_date_str, str):
                        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    else:
                        due_date = due_date_str
                    
                    days_until = (due_date - datetime.now()).days
                    
                    if days_until < 0:
                        overdue_count += 1
                    elif days_until <= forecast_days:
                        upcoming_deadlines += 1
                except Exception:
                    pass
        
        # Average days until due
        due_dates = []
        for signal in reviewer_signals:
            due_date_str = signal.get("due_date")
            if due_date_str:
                try:
                    if isinstance(due_date_str, str):
                        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    else:
                        due_date = due_date_str
                    days_until = (due_date - datetime.now()).days
                    if days_until >= 0:
                        due_dates.append(days_until)
                except Exception:
                    pass
        
        avg_due_in_days = np.mean(due_dates) if due_dates else None
        
        # Capacity risk classification
        capacity_risk = _classify_capacity_risk(rls, open_reviews, overdue_count)
        
        reviewer_stats.append({
            "name": reviewer_name,
            "expertise": reviewer_row.get("expertise", "General"),
            "open_reviews": open_reviews,
            "risk_load_score": rls,
            "high_priority_count": high_priority_count,
            "overdue_count": overdue_count,
            "upcoming_deadlines": upcoming_deadlines,
            "avg_due_in_days": round(avg_due_in_days, 1) if avg_due_in_days else None,
            "capacity_risk": capacity_risk
        })
    
    return pd.DataFrame(reviewer_stats)


def _classify_capacity_risk(rls: float, open_reviews: int, overdue_count: int) -> str:
    """
    Classify reviewer capacity risk.
    
    Returns:
        Risk level: "Critical", "High", "Medium", "Low"
    """
    if overdue_count > 3 or rls > 10.0 or (open_reviews > 15 and rls > 7.0):
        return "Critical"
    elif overdue_count > 0 or rls > 7.0 or open_reviews > 10:
        return "High"
    elif rls > 4.0 or open_reviews > 5:
        return "Medium"
    else:
        return "Low"


def generate_workload_forecast_summary(
    forecast_df: pd.DataFrame
) -> str:
    """
    Generate AI-powered summary of workload forecast.
    
    Args:
        forecast_df: Reviewer workload forecast DataFrame
        
    Returns:
        Summary text
    """
    if forecast_df is None or forecast_df.empty:
        return "No reviewer workload data available."
    
    if not LLM_AVAILABLE:
        # Fallback summary
        critical_reviewers = forecast_df[forecast_df["capacity_risk"] == "Critical"]
        high_reviewers = forecast_df[forecast_df["capacity_risk"] == "High"]
        
        summary_parts = [
            f"Workload Forecast Summary:",
            f"- Total Reviewers: {len(forecast_df)}",
            f"- Critical Risk: {len(critical_reviewers)} reviewer(s)",
            f"- High Risk: {len(high_reviewers)} reviewer(s)"
        ]
        
        if len(critical_reviewers) > 0:
            summary_parts.append("\nCritical Risk Reviewers:")
            for _, r in critical_reviewers.iterrows():
                summary_parts.append(f"  • {r['name']}: RLS {r['risk_load_score']:.1f}, {r['overdue_count']} overdue")
        
        return "\n".join(summary_parts)
    
    # Format data for LLM
    forecast_summary_text = forecast_df.to_string(index=False)
    
    prompt = f"""
You are a pharmacovigilance operations manager analyzing reviewer workload distribution.

Reviewer Workload Forecast:
{forecast_summary_text}

Analyze and provide:
1. Who is overloaded (Critical/High risk)
2. Who should NOT be assigned additional work
3. Who can absorb more workload (Low/Medium risk)
4. Any upcoming risks or deadlines to watch
5. Recommendations for load balancing

Format as a clear, actionable summary suitable for management review.
"""
    
    try:
        system_prompt = "You are a pharmacovigilance operations manager providing workload analysis and load balancing recommendations."
        return call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="general",
            max_tokens=1000,
            temperature=0.3
        ) or "Workload forecast summary unavailable."
    except Exception as e:
        return f"Workload forecast summary generation error: {str(e)}"

