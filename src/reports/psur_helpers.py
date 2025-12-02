"""
PSUR Helper Functions
Data loading and summary computation for PSUR/DSUR generation.
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.executive_dashboard.loaders import load_unified_ae_data
from src.executive_dashboard.aggregator import ExecutiveAggregator

logger = logging.getLogger(__name__)


def load_unified_ae_data_for_period(
    period_start: datetime,
    period_end: datetime,
    drug: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> pd.DataFrame:
    """
    Load unified AE data for a specific period.
    
    Args:
        period_start: Period start date
        period_end: Period end date
        drug: Optional drug name filter
        tenant_id: Optional tenant ID for filtering
    
    Returns:
        Unified DataFrame
    """
    try:
        # Calculate days back
        days_back = (period_end - period_start).days + 1
        
        # Load data
        df = load_unified_ae_data(
            drug=drug,
            days_back=days_back,
            sources=None  # Load all sources
        )
        
        if df.empty:
            return df
        
        # Filter by date range
        if "created_date" in df.columns:
            df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
            df = df[
                (df["created_date"] >= period_start) &
                (df["created_date"] <= period_end)
            ]
        
        # Filter by tenant if provided
        if tenant_id and "organization" in df.columns:
            df = df[df["organization"] == tenant_id]
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading unified AE data: {e}")
        return pd.DataFrame()


def compute_signal_summary(df: pd.DataFrame, drug: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute signal summary from unified AE data.
    
    Args:
        df: Unified AE DataFrame
        drug: Optional drug filter
    
    Returns:
        Dictionary with signal summary
    """
    if df.empty:
        return {
            "total_signals": 0,
            "top_signals": [],
            "total_cases": 0,
            "sources": {}
        }
    
    # Filter by drug if provided
    if drug and "drug" in df.columns:
        df = df[df["drug"].str.contains(drug, case=False, na=False)]
    
    if df.empty:
        return {
            "total_signals": 0,
            "top_signals": [],
            "total_cases": 0,
            "sources": {}
        }
    
    # Use aggregator to compute signal ranking (requires drug and reaction columns)
    top_signals = []
    sources = {}
    
    if "drug" in df.columns and "reaction" in df.columns:
        aggregator = ExecutiveAggregator()
        signal_ranking = aggregator.compute_signal_ranking(df, limit=20)
        
        # Get top signals
        if not signal_ranking.empty:
            for _, row in signal_ranking.head(10).iterrows():
                top_signals.append({
                    "drug": row.get("drug", ""),
                    "reaction": row.get("reaction", ""),
                    "quantum_score": float(row.get("quantum_score", 0.0)),
                    "gri_score": float(row.get("severity_score", 0.0)),
                    "frequency": int(row.get("frequency", 0)),
                    "priority": "high" if row.get("quantum_score", 0) > 0.7 else "medium" if row.get("quantum_score", 0) > 0.5 else "low"
                })
    
    # Count sources
    if "source" in df.columns:
        source_counts = df["source"].value_counts().to_dict()
        sources = {k: int(v) for k, v in source_counts.items()}
    
    return {
        "total_signals": len(signal_ranking) if not signal_ranking.empty else 0,
        "top_signals": top_signals,
        "total_cases": len(df),
        "sources": sources
    }


def compute_literature_summary(
    drug: str,
    period_start: datetime,
    period_end: datetime
) -> Dict[str, Any]:
    """
    Compute literature summary (stub for now).
    
    Args:
        drug: Drug name
        period_start: Period start
        period_end: Period end
    
    Returns:
        Dictionary with literature summary
    """
    # TODO: Implement literature integration
    return {
        "total_citations": 0,
        "key_papers": [],
        "summary": "Literature summary not yet integrated."
    }


def summarize_trends_for_prompt(df: pd.DataFrame) -> str:
    """
    Summarize trends for LLM prompt.
    
    Args:
        df: Unified AE DataFrame
    
    Returns:
        String summary of trends
    """
    if df.empty or "created_date" not in df.columns:
        return "No trend data available."
    
    try:
        aggregator = ExecutiveAggregator()
        trends = aggregator.compute_trends(df, period="M")
        
        if trends.empty:
            return "No trend data available."
        
        first_count = trends.iloc[0]["count"] if len(trends) > 0 else 0
        last_count = trends.iloc[-1]["count"] if len(trends) > 0 else 0
        change = last_count - first_count
        direction = "increase" if change > 0 else "decrease" if change < 0 else "stable"
        
        return (
            f"Reported cases changed from {int(first_count)} to {int(last_count)} "
            f"over the reporting period, representing a {direction} of {abs(change)} cases."
        )
    except Exception as e:
        logger.error(f"Error summarizing trends: {e}")
        return "Trend analysis unavailable."


def summarize_alignment_for_prompt(df: pd.DataFrame) -> str:
    """
    Summarize source alignment for LLM prompt.
    
    Args:
        df: Unified AE DataFrame
    
    Returns:
        String summary of source alignment
    """
    if df.empty or "source" not in df.columns:
        return "No source data available."
    
    try:
        source_counts = df["source"].value_counts().to_dict()
        total = len(df)
        
        parts = []
        for source, count in source_counts.items():
            pct = (count / total * 100) if total > 0 else 0
            parts.append(f"{source}: {count} cases ({pct:.1f}%)")
        
        return f"Source distribution: {', '.join(parts)}"
    except Exception as e:
        logger.error(f"Error summarizing alignment: {e}")
        return "Source alignment analysis unavailable."

