"""
Conversational Safety Engine for AetherSignal
Interprets conversational queries and generates natural language responses.

Handles queries like:
- "Is Dupixent showing any new red flags recently?"
- "Are there signals for pancreatitis with GLP-1 agonists?"
- "What's going on with Paxlovid in seniors lately?"
"""

from typing import Dict, Optional, List, Any
import pandas as pd
import os
import json
from src import signal_stats
from src import longitudinal_spike
from src.ai.hybrid_router import route_query
from src.ai.signal_summarizer import generate_comprehensive_summary

# NEW imports for CHUNK 6.4: Multi-Turn Memory
from src.ai.memory_engine import update_memory_state
from src.ai.memory_prompt_builder import build_memory_prompt, build_context_messages

# NEW imports for CHUNK 6.6: Follow-Up Intelligence
from src.ai.followup_logic import followup_analysis

# CHUNK 6.11.3: Import Trend Alerts for conversational context
try:
    from src.ai.trend_alerts import get_trend_alerts
except ImportError:
    get_trend_alerts = None


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
    
    # CHUNK 6.11.3: Add trend alerts context to trends dict
    # CHUNK 6.12: Check for RPF-related queries
    query_lower = query.lower()
    is_rpf_query = any(keyword in query_lower for keyword in [
        "top signal", "urgent", "priority", "which signal", "what should i review",
        "highest risk", "most important", "critical signal", "rank", "prioritize"
    ])
    
    if get_trend_alerts:
        try:
            trend_alerts = get_trend_alerts(normalized_df)
            if trend_alerts:
                # Add trend alerts summaries to trends for context
                trends["trend_alerts"] = [alert.summary for alert in trend_alerts[:3]]  # Top 3
            
            # CHUNK 6.12: For RPF queries, get heavy mode data
            if is_rpf_query:
                try:
                    import streamlit as st
                    from src.ai.trend_alerts import detect_trend_alerts_heavy
                    
                    # Get heavy mode results with RPF
                    heavy_results = detect_trend_alerts_heavy(normalized_df)
                    rpf_ranked = heavy_results.get("rpf_ranked", [])
                    
                    if rpf_ranked:
                        # Store in session state for suggestions
                        st.session_state["last_trend_alerts_result"] = heavy_results
                        # Add RPF data to trends for response generation
                        trends["rpf_ranked"] = rpf_ranked[:5]  # Top 5 for context
                except Exception:
                    pass
        except Exception:
            pass
    
    # Detect red flags
    red_flags = _detect_red_flags(summary, prr_ror, trends)
    
    # Generate natural language response
    response = _generate_response(
        query, filters, summary, prr_ror, trends, red_flags, use_llm, normalized_df
    )
    
    # ============================================================
    # CHUNK 6.11.4 + 6.11.5: Trend Alerts Injection (Light Mode)
    # CHUNK 6.11.5: Enrich high/critical alerts with LLM interpretation
    # ============================================================
    alert_cards = []
    try:
        if get_trend_alerts:
            # CHUNK 6.11.5 + 6.11.7 + 6.11.8 + 6.11.9 + 6.11.10 + 6.11.12 + 6.11.13: Enrich with all analyses if enabled
            try:
                import streamlit as st
                use_llm_enabled = st.session_state.get("enable_ai_enhanced", False)
                # For chat, add time-series, subgroups, dose-response, risk dynamics, narrative clusters, and lot alerts in heavy mode only (performance)
                enrich_timeseries = st.session_state.get("run_heavy_alerts", False)
                enrich_subgroups = st.session_state.get("run_heavy_alerts", False)
                enrich_dose_response = st.session_state.get("run_heavy_alerts", False)
                enrich_risk_dynamics = st.session_state.get("run_heavy_alerts", False)  # CHUNK 6.11.10
                enrich_narrative_clusters = st.session_state.get("run_heavy_alerts", False)  # CHUNK 6.11.12
                enrich_lot_alerts = st.session_state.get("run_heavy_alerts", False)  # CHUNK 6.11.13
            except Exception:
                use_llm_enabled = False
                enrich_timeseries = False
                enrich_subgroups = False
                enrich_dose_response = False
                enrich_risk_dynamics = False
                enrich_narrative_clusters = False
                enrich_lot_alerts = False
            
            enrich_llm = use_llm_enabled  # Only enrich if LLM is enabled
            
            light_alerts = get_trend_alerts(
                normalized_df, 
                enrich_with_llm=enrich_llm,
                enrich_with_timeseries=enrich_timeseries,
                enrich_with_subgroups=enrich_subgroups,
                enrich_with_dose_response=enrich_dose_response,
                enrich_with_risk_dynamics=enrich_risk_dynamics,  # CHUNK 6.11.10
                enrich_with_narrative_clusters=enrich_narrative_clusters,  # CHUNK 6.11.12
                enrich_with_lot_alerts=enrich_lot_alerts  # CHUNK 6.11.13
            )
            for alert in light_alerts[:3]:  # Top 3 alerts
                if alert:
                    alert_dict = {
                        "type": "trend_alert",
                        "id": alert.id,
                        "title": alert.title,
                        "summary": alert.summary,
                        "severity": alert.severity,
                        "action": alert.suggested_action,
                        "metric": alert.metric_value,
                        "unit": alert.metric_unit,
                        "details": alert.details
                    }
                    
                    # CHUNK 6.11.5: Add LLM explanation if available
                    if alert.llm_explanation:
                        alert_dict["llm_explanation"] = alert.llm_explanation
                    
                    # CHUNK 6.11.7: Add time-series analysis if available
                    if alert.time_series:
                        alert_dict["time_series"] = alert.time_series
                    
                    # CHUNK 6.11.8: Add subgroup analysis if available
                    if alert.subgroups:
                        alert_dict["subgroups"] = alert.subgroups
                    
                    # CHUNK 6.11.8: Add subgroup interpretation if available
                    if alert.subgroup_interpretation:
                        alert_dict["subgroup_interpretation"] = alert.subgroup_interpretation
                    
                    # CHUNK 6.11.9: Add dose-response analysis if available
                    if alert.dose_response:
                        alert_dict["dose_response"] = alert.dose_response
                    
                    # CHUNK 6.11.9: Add cumulative risk analysis if available
                    if alert.cumulative_risk:
                        alert_dict["cumulative_risk"] = alert.cumulative_risk
                    
                    # CHUNK 6.11.9: Add dose interpretation if available
                    if alert.dose_interpretation:
                        alert_dict["dose_interpretation"] = alert.dose_interpretation
                    
                    alert_cards.append(alert_dict)
    except Exception:
        # Fail gracefully - alerts are optional
        pass
    
    # Add alerts to response metadata
    if alert_cards:
        if isinstance(response, dict):
            response["trend_alerts"] = alert_cards
        else:
            # If response is a string, wrap it in dict
            response = {
                "response": response,
                "trend_alerts": alert_cards
            }
    
    # CHUNK 6.12: Add RPF data to response if available
    try:
        import streamlit as st
        if "last_trend_alerts_result" in st.session_state:
            rpf_ranked = st.session_state["last_trend_alerts_result"].get("rpf_ranked", [])
            if rpf_ranked:
                if isinstance(response, dict):
                    response["rpf_ranked"] = rpf_ranked[:5]  # Top 5 for chat display
                else:
                    if not isinstance(response, dict):
                        response = {"response": response}
                    response["rpf_ranked"] = rpf_ranked[:5]
    except Exception:
        pass
    
    # ----------------------------------------------
    # NEW: Update memory_state based on current query (CHUNK 6.4)
    # ----------------------------------------------
    memory_state = {}
    try:
        import streamlit as st
        # Update memory with extracted information from query
        if "memory_state" not in st.session_state:
            st.session_state.memory_state = {}
        
        st.session_state.memory_state = update_memory_state(
            query,
            st.session_state.memory_state,
            normalized_df
        )
        memory_state = st.session_state.memory_state
    except Exception:
        # If not in Streamlit context, skip memory update
        pass
    
    # ----------------------------------------------
    # NEW: Run fast follow-up analysis (CHUNK 6.6)
    # ----------------------------------------------
    quick_results = {}
    try:
        # Use filtered_df for faster follow-up analysis (already filtered)
        quick_results = followup_analysis(
            filtered_df if not filtered_df.empty else normalized_df,
            memory_state,
            include_all=True  # Include all quick insights
        )
        
        # CHUNK 6.7: Store quick results in session state for debug panel
        try:
            import streamlit as st
            st.session_state.last_quick_results = quick_results
        except Exception:
            pass  # If not in Streamlit context, skip
    except Exception as e:
        # If follow-up analysis fails, continue without it
        pass
    
    return {
        "filters": filters,
        "method": method,
        "confidence": confidence,
        "summary": summary,
        "prr_ror": prr_ror,
        "trends": trends,
        "red_flags": red_flags,
        "response": response_text,
        "filtered_df": filtered_df,  # For further analysis
        "memory": memory_state,  # CHUNK 6.4: Include memory state
        "rpf_ranked": trends.get("rpf_ranked", [])[:5] if trends.get("rpf_ranked") else [],  # CHUNK 6.12: RPF data
        "quick_results": quick_results,  # CHUNK 6.6: Include quick insights
        "trend_alerts": alert_cards  # CHUNK 6.11.4: Alert cards for chat UI
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


def build_llm_messages(
    user_message: str,
    filters: Dict,
    summary: Dict,
    prr_ror: Optional[Dict],
    trends: Dict,
    red_flags: List[str],
    normalized_df: Optional[pd.DataFrame] = None
) -> List[Dict[str, str]]:
    """
    Build the optimized multi-turn message sequence (CHUNK 6.4):
    - System (memory)
    - Last assistant message (for continuity)
    - Last user message (previous turn)
    - Current user message with data context
    
    Args:
        user_message: Current user query
        filters: Extracted filters
        summary: Statistical summary
        prr_ror: PRR/ROR metrics
        trends: Trend analysis
        red_flags: List of red flags
        
    Returns:
        List of message dictionaries for LLM API
    """
    # Try to get session state (may not be available if called outside Streamlit)
    try:
        import streamlit as st
        memory_state = st.session_state.get("memory_state", {})
        chat_history = st.session_state.get("chat_history", [])
    except Exception:
        # Fallback if not in Streamlit context
        memory_state = {}
        chat_history = []
    
    # Build memory-aware system prompt
    system_prompt = build_memory_prompt(memory_state)
    
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # Add last assistant & last user messages (if exist) for continuity
    if len(chat_history) >= 2:
        # Get last assistant message
        last_assistant = None
        for msg in reversed(chat_history):
            if msg.get("role") == "assistant" and msg.get("status") == "complete":
                last_assistant = msg.get("content")
                break
        
        # Get last user message (before current)
        last_user = None
        user_count = 0
        for msg in reversed(chat_history):
            if msg.get("role") == "user":
                user_count += 1
                if user_count == 2:  # Second-to-last user message
                    last_user = msg.get("content")
                    break
        
        if last_assistant:
            messages.append({"role": "assistant", "content": last_assistant})
        if last_user:
            messages.append({"role": "user", "content": last_user})
    
    # Build current user message with data context
    context_text = f"""User Query: {user_message}

Extracted Filters: {json.dumps(filters, indent=2)}

Results:
- Matching Cases: {summary.get('matching_cases', 0):,}
- Total Cases: {summary.get('total_cases', 0):,}
- Serious Cases: {summary.get('serious_count', 0):,} ({summary.get('serious_percentage', 0):.1f}%)
"""

    if prr_ror:
        context_text += f"""Disproportionality:
- PRR: {prr_ror.get('prr', 0):.2f} (CI: {prr_ror.get('prr_ci_lower', 0):.2f} - {prr_ror.get('prr_ci_upper', 0):.2f})
- ROR: {prr_ror.get('ror', 0):.2f} (CI: {prr_ror.get('ror_ci_lower', 0):.2f} - {prr_ror.get('ror_ci_upper', 0):.2f})
"""

    # CHUNK 6.11.3: Add Trend Alerts context
    if get_trend_alerts and normalized_df is not None:
        try:
            trend_alerts = get_trend_alerts(normalized_df)
            if trend_alerts:
                context_text += f"\n\nActive Trend Alerts ({len(trend_alerts)} detected):\n"
                for alert in trend_alerts[:3]:  # Top 3 alerts
                    context_text += f"- {alert.summary}\n"
        except Exception:
            pass  # Fail silently
    
    if trends.get("has_trend"):
        context_text += f"""Trends:
- Direction: {trends.get('direction', 'stable')}
- Spikes: {len(trends.get('spikes', []))}
"""
    
    # CHUNK 6.11.3: Add trend alerts from trends dict (if available)
    if trends.get("trend_alerts"):
        context_text += f"\nRecent Trend Alerts:\n"
        for alert_summary in trends.get("trend_alerts", [])[:3]:
            context_text += f"- {alert_summary}\n"
    
    # CHUNK 6.12: Add RPF-ranked signals if available
    if trends.get("rpf_ranked"):
        context_text += f"\n\nRisk Prioritization Framework (RPF) - Top Priority Signals:\n"
        for idx, entry in enumerate(trends.get("rpf_ranked", [])[:5], 1):
            signal = entry.get("signal", {})
            rpf_score = entry.get("rpf_score", 0)
            risk_level = entry.get("risk_level", "Unknown")
            drug = signal.get("drug", "Unknown")
            reaction = signal.get("reaction", "Unknown")
            context_text += f"{idx}. {risk_level}: {drug} → {reaction} (RPF Score: {rpf_score:.1f})\n"

    if red_flags:
        context_text += f"Red Flags: {', '.join(red_flags)}\n"
    
    context_text += "\nAnswer the user's query in a conversational way:"
    
    messages.append({"role": "user", "content": context_text})
    
    return messages


def _generate_response(
    query: str,
    filters: Dict,
    summary: Dict,
    prr_ror: Optional[Dict],
    trends: Dict,
    red_flags: List[str],
    use_llm: bool,
    normalized_df: Optional[pd.DataFrame] = None
) -> str:
    """Generate natural language response to the query."""
    
    # If LLM is enabled, use it for richer responses with memory (CHUNK 6.4)
    if use_llm:
        try:
            # Check if LLM is configured
            from src.llm_explain import has_llm_configured
            if not has_llm_configured():
                # Fall back to rule-based
                pass
            else:
                # Build memory-aware multi-turn messages (CHUNK 6.4)
                messages = build_llm_messages(
                    query, filters, summary, prr_ror, trends, red_flags, normalized_df
                )
                
                # Call LLM with memory-aware messages
                import os
                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key:
                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key, timeout=15.0)
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                            max_tokens=500,
                            temperature=0.3
                        )
                        
                        content = response.choices[0].message.content
                        if content:
                            return content.strip()
                    except Exception:
                        pass  # Fall back to rule-based
                
                # Fallback to old method if memory-aware call fails
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

