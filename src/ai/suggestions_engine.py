"""
Dynamic AI-Driven Suggestions Engine (CHUNK 6.10-B + 6.11)
Generates contextual, data-driven suggestions based on actual dataset content.
No hardcoded strings - all suggestions are computed at runtime.
Now includes trend alerts integration (CHUNK 6.11 Part 3 + 6.11.3).
"""
import pandas as pd
import streamlit as st
from typing import List, Optional, Dict, Any
import re

# CHUNK 6.11.3: Import Trend Alerts
try:
    from src.ai.trend_alerts import (
        get_trend_alerts,
        detect_trend_alerts_light,
        detect_trend_alerts_heavy,
        TrendAlert
    )
except ImportError:
    # Graceful fallback if trend alerts not available
    get_trend_alerts = None
    detect_trend_alerts_light = None
    detect_trend_alerts_heavy = None
    TrendAlert = None


def compute_dynamic_suggestions(
    normalized_df: pd.DataFrame,
    memory_state: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Generate intelligent, data-driven suggestions based on actual dataset.
    
    Args:
        normalized_df: Normalized DataFrame with PV data
        memory_state: Optional conversation memory state (from st.session_state.memory_state)
        
    Returns:
        List of contextual suggestion strings (max 5 unique suggestions)
    """
    suggestions: List[str] = []
    
    if normalized_df is None or len(normalized_df) == 0:
        # Fallback suggestions if no data
        return [
            "Upload your PV dataset to get personalized suggestions",
            "Load FAERS data to see dynamic insights",
            "Once data is loaded, I'll suggest relevant queries"
        ]
    
    total_cases = len(normalized_df)
    
    # Helper function to get top drug
    def _get_top_drug() -> Optional[str]:
        if "drug_name" in normalized_df.columns:
            drug_series = normalized_df["drug_name"].astype(str).str.split("; ").explode()
            drug_series = drug_series[drug_series.notna() & (drug_series != 'nan')]
            if len(drug_series) > 0:
                return drug_series.value_counts().index[0]
        return None
    
    # Helper function to get top reaction
    def _get_top_reaction() -> Optional[str]:
        reaction_col = None
        if "reaction" in normalized_df.columns:
            reaction_col = "reaction"
        elif "reaction_pt" in normalized_df.columns:
            reaction_col = "reaction_pt"
        
        if reaction_col:
            reaction_series = normalized_df[reaction_col].astype(str).str.split("; ").explode()
            reaction_series = reaction_series[reaction_series.notna() & (reaction_series != 'nan')]
            if len(reaction_series) > 0:
                return reaction_series.value_counts().index[0]
        return None
    
    # Helper function to detect date column
    def _get_date_column() -> Optional[str]:
        for col_name in ["report_date", "receipt_date", "receive_date", "received_date", "event_date", "onset_date"]:
            if col_name in normalized_df.columns:
                return col_name
        return None
    
    # Helper function to check if serious cases exist
    def _get_serious_count() -> Optional[int]:
        serious_col = None
        if "seriousness" in normalized_df.columns:
            serious_col = "seriousness"
        elif "serious" in normalized_df.columns:
            serious_col = "serious"
        
        if serious_col:
            serious_series = normalized_df[serious_col]
            if serious_series.dtype == bool:
                return int(serious_series.sum())
            else:
                return int(serious_series.astype(str).str.lower().isin(['true', '1', 'yes', 'y', 'serious']).sum())
        return None
    
    # -------------------------------
    # 1. Most Reported Drug Suggestions
    # -------------------------------
    top_drug = _get_top_drug()
    if top_drug:
        suggestions.append(f"What are the top reactions for {top_drug}?")
        suggestions.append(f"Show me trends for {top_drug} in the last 12 months.")
        suggestions.append(f"How many serious cases involve {top_drug}?")
    
    # -------------------------------
    # 2. Most Reported Reaction Suggestions
    # -------------------------------
    top_reaction = _get_top_reaction()
    if top_reaction:
        suggestions.append(f"Show me serious cases of {top_reaction}.")
        suggestions.append(f"Which drugs most commonly cause {top_reaction}?")
        suggestions.append(f"Show me the trend for {top_reaction} over time.")
    
    # -------------------------------
    # 3. Seriousness-Based Suggestions
    # -------------------------------
    serious_count = _get_serious_count()
    if serious_count is not None and total_cases > 0:
        serious_rate = serious_count / total_cases
        if serious_rate > 0.2:
            suggestions.append("Which drugs contribute most to serious cases?")
            suggestions.append("Show me serious case trends over the last year.")
        elif serious_rate < 0.1:
            suggestions.append("Show me non-serious case patterns.")
            suggestions.append("What are the most common non-serious reactions?")
        else:
            suggestions.append("Break down cases by seriousness level.")
    
    # -------------------------------
    # 4. Trend-Based Suggestions (Last 12 Months)
    # -------------------------------
    date_col = _get_date_column()
    if date_col:
        try:
            temp_df = normalized_df.copy()
            temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors="coerce")
            temp_df = temp_df[temp_df[date_col].notna()]
            
            if len(temp_df) > 0:
                max_date = temp_df[date_col].max()
                one_year_ago = max_date - pd.Timedelta(days=365)
                recent_df = temp_df[temp_df[date_col] >= one_year_ago]
                
                if len(recent_df) > 100:  # Only suggest if we have enough recent data
                    suggestions.append("Which reactions increased the most in the last 12 months?")
                    suggestions.append("Show me drugs with decreasing case trends this year.")
                    
                    # Check for spikes
                    monthly_counts = temp_df.groupby(pd.Grouper(key=date_col, freq="M")).size()
                    if len(monthly_counts) >= 3:
                        recent_avg = monthly_counts.tail(3).mean()
                        older_avg = monthly_counts.head(len(monthly_counts) - 3).mean() if len(monthly_counts) > 3 else recent_avg
                        if recent_avg > older_avg * 1.2:  # 20% increase
                            suggestions.append("I detected a recent spike in cases. What's causing it?")
        except Exception:
            pass  # Skip if date analysis fails
    
    # -------------------------------
    # 5. Dataset Size-Based Suggestions
    # -------------------------------
    if total_cases > 50000:
        suggestions.append("Show me high-level SOC (System Organ Class) trends.")
        suggestions.append("Summarize the dataset at a global level.")
        suggestions.append("What are the key safety signals in this large dataset?")
    elif total_cases > 10000:
        suggestions.append("Break down the dataset by drug classes.")
        suggestions.append("What are the most significant drug-reaction combinations?")
    else:
        suggestions.append("Show me a detailed breakdown of all cases.")
    
    # -------------------------------
    # 6. Memory State-Based Suggestions (Conversation Context)
    # -------------------------------
    if memory_state:
        drug = memory_state.get("drug")
        reactions = memory_state.get("reactions", [])
        
        if drug:
            suggestions.append(f"Compare {drug} with other drugs in the same class.")
            suggestions.append(f"Show me new safety signals for {drug}.")
            suggestions.append(f"Break down {drug} reactions by demographic groups.")
        
        if reactions and len(reactions) > 0:
            top_rxn = reactions[0] if isinstance(reactions, list) else str(reactions)
            suggestions.append(f"Which other reactions co-occur with {top_rxn}?")
            suggestions.append(f"Show me temporal patterns for {top_rxn}.")
    
    # -------------------------------
    # 7. Drug Class Detection (if possible)
    # -------------------------------
    # Check for biologics, vaccines, etc. (simple heuristic)
    if top_drug:
        drug_lower = str(top_drug).lower()
        if any(keyword in drug_lower for keyword in ['mab', 'mab-', '-mab', 'monoclonal', 'biologic']):
            suggestions.append("Compare biologics vs non-biologics this year.")
        elif any(keyword in drug_lower for keyword in ['vaccine', 'vax']):
            suggestions.append("Show me vaccine-related safety patterns.")
    
    # -------------------------------
    # 8. Demographic-Based Suggestions
    # -------------------------------
    if "age" in normalized_df.columns or "sex" in normalized_df.columns or "gender" in normalized_df.columns:
        suggestions.append("Show me cases broken down by patient demographics.")
        
        if "age" in normalized_df.columns:
            suggestions.append("Which age groups show the highest case rates?")
        
        if "sex" in normalized_df.columns or "gender" in normalized_df.columns:
            suggestions.append("Compare case patterns between male and female patients.")
    
    # -------------------------------
    # 9. Country/Geography-Based Suggestions
    # -------------------------------
    if "country" in normalized_df.columns:
        suggestions.append("Show me cases by country or region.")
        suggestions.append("Which countries have the highest case volumes?")
    
    # -------------------------------
    # 10. Outcome-Based Suggestions
    # -------------------------------
    if "outcome" in normalized_df.columns:
        suggestions.append("What are the most common patient outcomes?")
        suggestions.append("Show me fatal cases and their patterns.")
    
    # -------------------------------
    # 11. Trend Alerts-Based Suggestions (CHUNK 6.11.3 + 6.11.4)
    # Light alerts always (fast) - Hybrid Mode
    # -------------------------------
    trend_alerts_list = []  # Store for follow-up suggestions
    try:
        if get_trend_alerts:
            # CHUNK 6.11.3: Use light alerts (fast, always-on)
            trend_alerts_list = get_trend_alerts(normalized_df)
            
            # Convert TrendAlert objects to suggestion strings
            for alert in trend_alerts_list[:3]:  # Top 3 alerts
                if alert and alert.severity in ["critical", "warning", "info"]:
                    # Use suggested_action if available, otherwise create from summary
                    if alert.suggested_action:
                        suggestions.append(alert.suggested_action)
                    else:
                        # Create suggestion from alert title and summary
                        suggestion_text = f"Investigate: {alert.title}"
                        if alert.metric_value:
                            suggestions.append(f"{alert.title} ({alert.metric_value:.1f} {alert.metric_unit or ''})")
                        else:
                            suggestions.append(suggestion_text)
        elif detect_trend_alerts_light:
            # Fallback: Use light detection if get_trend_alerts not available
            light_results = detect_trend_alerts_light(normalized_df)
            for spike in light_results.get("spikes", [])[:2]:
                if spike.get("severity") in ["high", "medium"]:
                    message = spike.get("message", "")
                    if message:
                        suggestions.append(f"🚨 {message}")
    
    except Exception:
        pass  # Fail silently if trend alerts not available
    
    # -------------------------------
    # 12. Trend Alert-Based Follow-Up Questions (CHUNK 6.11.4 + 6.11.5)
    # -------------------------------
    try:
        if trend_alerts_list:
            for alert in trend_alerts_list[:2]:  # Top 2 alerts for follow-ups
                if alert and alert.title:
                    # Generate contextual follow-up questions
                    title_lower = alert.title.lower()
                    suggestions.append(f"Why is {title_lower} happening?")
                    suggestions.append(f"Show me the cases contributing to {title_lower}")
                    suggestions.append(f"Is this trend clinically significant?")
                    
                    # CHUNK 6.11.5: Use LLM explanation for suggestions if available
                    if alert.llm_explanation:
                        expl = alert.llm_explanation
                        # Add single sentence summary as suggestion
                        if expl.get("single_sentence_summary"):
                            suggestions.append(expl["single_sentence_summary"])
                        # Add recommended follow-ups
                        if expl.get("recommended_followups"):
                            suggestions.extend(expl["recommended_followups"][:2])  # Top 2 follow-ups
                    
                    # CHUNK 6.11.7: Use time-series significance for suggestions
                    if alert.time_series and alert.time_series.get("significance", 0) > 2:
                        sig = alert.time_series["significance"]
                        suggestions.append(
                            f"{alert.title}: significant deviation detected "
                            f"(Z={sig:.2f}σ)"
                        )
                    
                    # CHUNK 6.11.12: Add narrative cluster suggestions
                    if alert.narrative_clusters:
                        for cluster in alert.narrative_clusters[:2]:  # Top 2 clusters
                            summary = cluster.get("summary", {})
                            if summary and summary.get("one_sentence_summary"):
                                suggestions.append(f"🧠 Narrative pattern: {summary['one_sentence_summary']}")
                    
                    # CHUNK 6.11.13: Add lot alert suggestions
                    if alert.lot_alerts:
                        for lot in alert.lot_alerts[:2]:  # Top 2 lot alerts
                            lot_num = lot.get("lot_number", "N/A")
                            spike_ratio = lot.get("spike_ratio", 0.0)
                            interpretation = lot.get("interpretation", {})
                            if interpretation and interpretation.get("one_sentence_summary"):
                                suggestions.append(f"🏭 Batch {lot_num}: {interpretation['one_sentence_summary']}")
                            else:
                                suggestions.append(
                                    f"🏭 Investigate lot {lot_num} related to {lot.get('drug', 'N/A')} — "
                                    f"{lot.get('count', 0)} cases ({spike_ratio:.1f}× spike)"
                                )
                    
                    # CHUNK 6.12: Add RPF-based suggestions (if available in heavy mode)
                    # This will be added from the trend alerts result if RPF is available
                    
    except Exception:
        pass  # Fail silently
    
    # CHUNK 6.12: Add RPF-ranked signal suggestions if available
    try:
        # Check if we have RPF data from heavy mode analysis
        if "rpf_ranked" in st.session_state.get("last_trend_alerts_result", {}):
            rpf_ranked = st.session_state.last_trend_alerts_result.get("rpf_ranked", [])
            if rpf_ranked:
                top_rpf = rpf_ranked[0]
                signal = top_rpf.get("signal", {})
                rpf_score = top_rpf.get("rpf_score", 0)
                risk_level = top_rpf.get("risk_level", "")
                
                drug = signal.get("drug", "Unknown")
                reaction = signal.get("reaction", "Unknown")
                
                suggestions.append(
                    f"⚠️ {risk_level} priority signal: {drug} → {reaction} (RPF Score: {rpf_score:.1f})"
                )
                
                # Add top 3 critical/high priority signals
                for entry in rpf_ranked[:3]:
                    if "Critical" in entry.get("risk_level", "") or "High" in entry.get("risk_level", ""):
                        sig = entry.get("signal", {})
                        suggestions.append(
                            f"📊 Review {sig.get('drug', 'Unknown')} → {sig.get('reaction', 'Unknown')} "
                            f"(Score: {entry.get('rpf_score', 0):.1f})"
                        )
    except Exception:
        pass  # Fail gracefully
    
    # -------------------------------
    # Return Top 5 Unique Suggestions
    # -------------------------------
    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s.lower() not in seen:
            seen.add(s.lower())
            unique_suggestions.append(s)
            if len(unique_suggestions) >= 5:
                break
    
    return unique_suggestions[:5]


def compute_dynamic_suggestions_with_memory(normalized_df: pd.DataFrame) -> List[str]:
    """
    Wrapper that automatically loads memory state from session state.
    Use this when called from Streamlit context.
    """
    try:
        memory_state = st.session_state.get("memory_state", None)
    except Exception:
        memory_state = None
    
    return compute_dynamic_suggestions(normalized_df, memory_state)


def generate_query_autosuggestions(
    normalized_df: pd.DataFrame,
    user_query: str = ""
) -> List[str]:
    """
    Generate auto-suggestions for chat query input (CHUNK 6.11.3).
    
    Args:
        normalized_df: DataFrame with PV data
        user_query: Current user query (optional, for context)
        
    Returns:
        List of auto-suggestion strings
    """
    autosuggestions: List[str] = []
    
    if normalized_df is None or len(normalized_df) == 0:
        return autosuggestions
    
    # CHUNK 6.11.3: Add trend-based auto suggestions
    try:
        if get_trend_alerts:
            trend_alerts = get_trend_alerts(normalized_df)
            for alert in trend_alerts[:2]:  # Top 2 alerts
                if alert and alert.title:
                    autosuggestions.append(
                        f"Show me more about why {alert.title.lower()}"
                    )
                    if alert.suggested_action:
                        # Extract the actionable part
                        action = alert.suggested_action.split(".")[0] if "." in alert.suggested_action else alert.suggested_action
                        autosuggestions.append(action)
    except Exception:
        pass
    
    # CHUNK 6.11.3: Check for heavy trend analysis requests
    if user_query:
        heavy_keywords = ["heavy trend", "detailed trend", "full trend", "comprehensive trend", "run heavy"]
        if any(keyword in user_query.lower() for keyword in heavy_keywords):
            try:
                if detect_trend_alerts_heavy:
                    # This will trigger heavy analysis in the UI
                    autosuggestions.append("Running comprehensive trend analysis with medium-level statistical alerts...")
            except Exception:
                pass
    
    return autosuggestions[:3]  # Return top 3 auto-suggestions


def build_suggestions_with_heavy_mode(
    normalized_df: pd.DataFrame,
    user_query: str = "",
    enable_heavy: bool = False
) -> Dict[str, Any]:
    """
    Build suggestions including heavy trend alerts when requested (CHUNK 6.11.3).
    
    Args:
        normalized_df: DataFrame with PV data
        user_query: User query text (to detect heavy mode requests)
        enable_heavy: Explicit flag to enable heavy analysis
        
    Returns:
        Dictionary with suggestions and metadata
    """
    suggestions = compute_dynamic_suggestions(normalized_df)
    
    # CHUNK 6.11.3: Add medium/heavy alerts if requested
    heavy_alerts = []
    
    # Check if user explicitly requests heavy analysis
    if enable_heavy or (user_query and any(keyword in user_query.lower() 
                                           for keyword in ["heavy", "detailed", "full", "comprehensive", "run heavy"])):
        try:
            if detect_trend_alerts_heavy:
                heavy_results = detect_trend_alerts_heavy(normalized_df)
                
                # Add medium-level statistical alerts as suggestions
                for alert_dict in heavy_results.get("alerts", []):
                    if alert_dict.get("source") == "medium_statistical":
                        suggestion_text = alert_dict.get("suggested_action", alert_dict.get("message", ""))
                        if suggestion_text:
                            heavy_alerts.append(suggestion_text)
        except Exception:
            pass
    
    return {
        "suggestions": suggestions,
        "heavy_alerts": heavy_alerts,
        "total_suggestions": len(suggestions) + len(heavy_alerts)
    }

