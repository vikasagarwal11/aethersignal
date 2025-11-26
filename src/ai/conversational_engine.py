"""
Conversational Safety Engine for AetherSignal
Interprets conversational queries and generates natural language responses.

Handles queries like:
- "Is Dupixent showing any new red flags recently?"
- "Are there signals for pancreatitis with GLP-1 agonists?"
- "What's going on with Paxlovid in seniors lately?"
"""

from typing import Dict, Optional, List
import pandas as pd
from src import signal_stats
from src import longitudinal_spike
from src.ai.hybrid_router import route_query
from src.ai.signal_summarizer import generate_comprehensive_summary


def process_conversational_query(
    query: str,
    normalized_df: pd.DataFrame,
    use_llm: bool = False
) -> Dict:
    """
    Process conversational query and return comprehensive response.
    
    Args:
        query: Natural language query
        normalized_df: Full dataset
        use_llm: Whether to use LLM for interpretation/summarization
        
    Returns:
        Dictionary with:
        - filters: Extracted filters
        - summary: Statistical summary
        - prr_ror: Disproportionality metrics
        - trends: Trend analysis
        - response: Natural language response
        - charts: Chart data (optional)
    """
    # Route query through hybrid router
    filters, method, confidence = route_query(query, normalized_df, use_llm)
    
    # Apply filters
    filtered_df = signal_stats.apply_filters(normalized_df, filters)
    
    if filtered_df.empty:
        return {
            "filters": filters,
            "method": method,
            "confidence": confidence,
            "summary": None,
            "response": "No cases found matching your query. Please refine your search criteria.",
            "error": "no_cases"
        }
    
    # Get summary statistics
    summary = signal_stats.get_summary_stats(filtered_df, normalized_df)
    
    # Calculate PRR/ROR if drug and reaction specified
    prr_ror = None
    if "drug" in filters and "reaction" in filters:
        drug = filters["drug"] if isinstance(filters["drug"], str) else filters["drug"][0]
        reaction = filters["reaction"] if isinstance(filters["reaction"], str) else filters["reaction"][0]
        prr_ror = signal_stats.calculate_prr_ror(drug, reaction, normalized_df)
    
    # Analyze trends
    trends = _analyze_trends(filtered_df, summary)
    
    # Detect red flags
    red_flags = _detect_red_flags(summary, prr_ror, trends)
    
    # Generate natural language response
    response = _generate_response(
        query, filters, summary, prr_ror, trends, red_flags, use_llm
    )
    
    return {
        "filters": filters,
        "method": method,
        "confidence": confidence,
        "summary": summary,
        "prr_ror": prr_ror,
        "trends": trends,
        "red_flags": red_flags,
        "response": response,
        "filtered_df": filtered_df  # For further analysis
    }


def _analyze_trends(filtered_df: pd.DataFrame, summary: Dict) -> Dict:
    """Analyze temporal trends in the data."""
    trends = {
        "has_trend": False,
        "direction": None,  # "increasing", "decreasing", "stable"
        "spikes": [],
        "changepoint": None
    }
    
    if not summary.get("time_trend"):
        return trends
    
    trend_data = summary["time_trend"]
    if len(trend_data) < 3:
        return trends
    
    # Detect spikes
    spikes = longitudinal_spike.detect_spikes(trend_data, window_size=3, threshold_multiplier=2.0)
    if spikes:
        trends["has_trend"] = True
        trends["spikes"] = spikes[:5]  # Top 5 spikes
    
    # Detect changepoint
    changepoint = longitudinal_spike.analyze_trend_changepoint(trend_data)
    if changepoint:
        trends["changepoint"] = changepoint
        trends["has_trend"] = True
    
    # Determine overall direction
    if len(trend_data) >= 6:
        sorted_periods = sorted(trend_data.keys())
        first_half = [trend_data[p] for p in sorted_periods[:len(sorted_periods)//2]]
        second_half = [trend_data[p] for p in sorted_periods[len(sorted_periods)//2:]]
        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0
        
        if second_avg > first_avg * 1.2:
            trends["direction"] = "increasing"
        elif second_avg < first_avg * 0.8:
            trends["direction"] = "decreasing"
        else:
            trends["direction"] = "stable"
    
    return trends


def _detect_red_flags(summary: Dict, prr_ror: Optional[Dict], trends: Dict) -> List[str]:
    """Detect potential red flags in the data."""
    red_flags = []
    
    # High PRR/ROR
    if prr_ror:
        prr = prr_ror.get("prr", 0)
        if prr > 3.0:
            red_flags.append(f"High PRR ({prr:.2f}) suggests strong signal")
        ror = prr_ror.get("ror", 0)
        if ror > 3.0:
            red_flags.append(f"High ROR ({ror:.2f}) indicates disproportionality")
    
    # High seriousness rate
    serious_pct = summary.get("serious_percentage", 0)
    if serious_pct > 50:
        red_flags.append(f"High seriousness rate ({serious_pct:.1f}%)")
    
    # Increasing trend
    if trends.get("direction") == "increasing":
        red_flags.append("Increasing trend detected - cases rising over time")
    
    # Recent spikes
    if trends.get("spikes"):
        recent_spikes = [s for s in trends["spikes"] if s.get("spike_ratio", 0) > 2.0]
        if recent_spikes:
            red_flags.append(f"{len(recent_spikes)} significant spike(s) detected")
    
    # High case count
    matching_cases = summary.get("matching_cases", 0)
    if matching_cases > 100:
        red_flags.append(f"Large number of cases ({matching_cases})")
    
    return red_flags


def _generate_response(
    query: str,
    filters: Dict,
    summary: Dict,
    prr_ror: Optional[Dict],
    trends: Dict,
    red_flags: List[str],
    use_llm: bool
) -> str:
    """Generate natural language response to the query."""
    
    # If LLM is enabled, use it for richer responses
    if use_llm:
        try:
            from src.ai.signal_summarizer import generate_conversational_response
            return generate_conversational_response(
                query, filters, summary, prr_ror, trends, red_flags
            )
        except Exception:
            pass  # Fall back to rule-based
    
    # Rule-based response generation
    response_parts = []
    
    # Opening
    if "drug" in filters:
        drug = filters["drug"] if isinstance(filters["drug"], str) else filters["drug"][0]
        response_parts.append(f"**Analysis for {drug}**")
    
    # Case count
    matching_cases = summary.get("matching_cases", 0)
    total_cases = summary.get("total_cases", 0)
    pct = summary.get("percentage", 0)
    response_parts.append(f"\nFound **{matching_cases:,} cases** ({pct:.1f}% of {total_cases:,} total cases).")
    
    # PRR/ROR
    if prr_ror:
        prr = prr_ror.get("prr", 0)
        ror = prr_ror.get("ror", 0)
        response_parts.append(f"\n**Disproportionality metrics:**")
        response_parts.append(f"- PRR: {prr:.2f} (95% CI: {prr_ror.get('prr_ci_lower', 0):.2f} - {prr_ror.get('prr_ci_upper', 0):.2f})")
        response_parts.append(f"- ROR: {ror:.2f} (95% CI: {prr_ror.get('ror_ci_lower', 0):.2f} - {prr_ror.get('ror_ci_upper', 0):.2f})")
    
    # Trends
    if trends.get("has_trend"):
        if trends.get("direction") == "increasing":
            response_parts.append(f"\n**Trend:** Cases are **increasing** over time.")
        elif trends.get("direction") == "decreasing":
            response_parts.append(f"\n**Trend:** Cases are **decreasing** over time.")
        if trends.get("spikes"):
            response_parts.append(f"Detected {len(trends['spikes'])} significant spike(s).")
    
    # Red flags
    if red_flags:
        response_parts.append(f"\n**⚠️ Red Flags:**")
        for flag in red_flags:
            response_parts.append(f"- {flag}")
    
    # Demographics
    age_stats = summary.get("age_stats", {})
    if age_stats.get("mean"):
        response_parts.append(f"\n**Demographics:**")
        response_parts.append(f"- Average age: {age_stats['mean']:.0f} years")
        if summary.get("sex_distribution"):
            response_parts.append(f"- Sex distribution: {summary['sex_distribution']}")
    
    return "\n".join(response_parts)

