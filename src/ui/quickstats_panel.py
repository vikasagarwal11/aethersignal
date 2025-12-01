import streamlit as st
import pandas as pd
import altair as alt
from typing import Dict, Any

def render_quickstats(normalized_df: pd.DataFrame):
    """
    Compact, enterprise-style quick insights panel.
    Shown before chat for fast dataset orientation.
    """
    if normalized_df is None or len(normalized_df) == 0:
        return

    st.markdown("### 📊 Quick Dataset Insights")

    st.markdown('<div class="quick-insights-block">', unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 1. TOTAL CASE COUNT
    # ---------------------------------------------------------
    total_cases = len(normalized_df)
    st.metric("Total Cases", f"{total_cases:,}")

    # ---------------------------------------------------------
    # 2. TOP DRUGS
    # ---------------------------------------------------------
    if "drug_name" in normalized_df.columns:
        # Handle multi-value drugs (split by semicolon)
        drug_series = normalized_df["drug_name"].astype(str).str.split("; ").explode()
        top_drugs = (
            drug_series
            .value_counts()
            .head(5)
            .to_dict()
        )

        st.markdown("**Top Drugs**")
        for drug, count in top_drugs.items():
            if pd.notna(drug) and str(drug) != 'nan':
                st.markdown(
                    f"<span class='quick-insights-chip'>{drug}: {count:,}</span>",
                    unsafe_allow_html=True
                )

    # ---------------------------------------------------------
    # 3. TOP REACTIONS
    # ---------------------------------------------------------
    reaction_col = None
    if "reaction" in normalized_df.columns:
        reaction_col = "reaction"
    elif "reaction_pt" in normalized_df.columns:
        reaction_col = "reaction_pt"
    
    if reaction_col:
        # Handle multi-value reactions (split by semicolon)
        reaction_series = normalized_df[reaction_col].astype(str).str.split("; ").explode()
        top_rxns = (
            reaction_series
            .value_counts()
            .head(5)
            .to_dict()
        )

        st.markdown("**Top Reactions**")
        for r, count in top_rxns.items():
            if pd.notna(r) and str(r) != 'nan':
                st.markdown(
                    f"<span class='quick-insights-chip'>{r}: {count:,}</span>",
                    unsafe_allow_html=True
                )

    # ---------------------------------------------------------
    # 4. LAST 12 MONTHS SPARKLINE
    # ---------------------------------------------------------
    date_col = None
    for col_name in ["report_date", "receipt_date", "receive_date", "received_date", "event_date", "onset_date"]:
        if col_name in normalized_df.columns:
            date_col = col_name
            break
    
    if date_col:
        temp_df = normalized_df.copy()
        temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors="coerce")
        # Filter out NaT dates
        temp_df = temp_df[temp_df[date_col].notna()]
        if len(temp_df) > 0:
            monthly = temp_df.groupby(pd.Grouper(key=date_col, freq="M")).size().tail(12)

            if len(monthly) > 0:
                st.markdown("**12-Month Trend**")
                chart_data = pd.DataFrame({"month": monthly.index, "count": monthly.values})
                chart = (
                    alt.Chart(chart_data)
                    .mark_line(color="#3B82F6", point=True)
                    .encode(
                        x=alt.X("month:T", title=""),
                        y=alt.Y("count:Q", title="", axis=alt.Axis(labels=False))
                    )
                    .properties(height=60)
                )
                st.altair_chart(chart, use_container_width=True)

    # ---------------------------------------------------------
    # 5. Serious vs Non-serious
    # ---------------------------------------------------------
    serious_col = None
    if "seriousness" in normalized_df.columns:
        serious_col = "seriousness"
    elif "serious" in normalized_df.columns:
        serious_col = "serious"
    
    if serious_col:
        # Handle boolean or string values
        serious_series = normalized_df[serious_col]
        if serious_series.dtype == bool:
            serious_count = serious_series.sum()
        else:
            # Try to convert string/binary values
            serious_count = serious_series.astype(str).str.lower().isin(['true', '1', 'yes', 'y', 'serious']).sum()
        
        non_serious = total_cases - serious_count

        if total_cases > 0:
            st.markdown("**Case Seriousness**")
            st.progress(serious_count / total_cases)

            st.markdown(
                f"<span class='quick-insights-chip'>Serious: {serious_count:,}</span> "
                f"<span class='quick-insights-chip'>Non-Serious: {non_serious:,}</span>",
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 6. TREND ALERTS (CHUNK 6.11-C: UI Integration)
    # ---------------------------------------------------------
    _render_trend_alerts(normalized_df)

    # ---------------------------------------------------------
    # 7. AI Suggestions (CHUNK 6.10-B: Dynamic, Data-Driven)
    # ---------------------------------------------------------
    _render_ai_suggestions(normalized_df)


def _render_trend_alerts(normalized_df: pd.DataFrame):
    """
    Render trend alerts section (CHUNK 6.11-C: UI Integration - Option D).
    Shows active alerts, spikes, and emerging signals detected in the dataset.
    Uses light mode for fast preview (Option 3 Hybrid).
    """
    try:
        from src.ai.trend_alerts import detect_trend_alerts_light
        
        # Detect trend alerts (light mode for fast preview)
        alerts_result = detect_trend_alerts_light(normalized_df)
        
        if not alerts_result:
            return
        
        alerts = alerts_result.get("alerts", [])
        spikes = alerts_result.get("spikes", [])
        emerging_signals = alerts_result.get("emerging_signals", [])
        meta = alerts_result.get("meta", {})
        
        total_alerts = len(alerts)
        total_spikes = len(spikes)
        total_signals = len(emerging_signals)
        
        # Only show if there are alerts
        if total_alerts == 0 and total_spikes == 0 and total_signals == 0:
            return
        
        st.markdown("### ⚠️ Trend Alerts (Auto-Generated)")
        st.markdown('<div class="quick-insights-block">', unsafe_allow_html=True)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("High-Priority Alerts", total_alerts, delta=None)
        with col2:
            st.metric("Detected Spikes", total_spikes, delta=None)
        with col3:
            st.metric("Emerging Signals", total_signals, delta=None)
        
        # Show top 3 high-priority alerts
        if alerts:
            st.markdown("**🔴 High-Priority Alerts:**")
            for alert in alerts[:3]:  # Top 3
                severity = alert.get("severity", "medium")
                message = alert.get("message", "")
                alert_type = alert.get("type", "")
                
                # Color coding based on severity
                if severity == "high":
                    icon = "🚨"
                    color_class = "quick-insights-chip-high"
                elif severity == "medium":
                    icon = "⚠️"
                    color_class = "quick-insights-chip-medium"
                else:
                    icon = "ℹ️"
                    color_class = "quick-insights-chip"
                
                # Show alert with optional LLM interpretation
                if alert.get("has_llm_interpretation"):
                    interpretation = alert.get("llm_interpretation", "")
                    st.markdown(
                        f'<span class="{color_class}">{icon} {message}</span>',
                        unsafe_allow_html=True
                    )
                    st.caption(f"💡 {interpretation[:150]}..." if len(interpretation) > 150 else f"💡 {interpretation}")
                else:
                    st.markdown(
                        f'<span class="{color_class}">{icon} {message}</span>',
                        unsafe_allow_html=True
                    )
        
        # Show top 2 emerging signals
        if emerging_signals:
            st.markdown("**🆕 Emerging Signals:**")
            for signal in emerging_signals[:2]:  # Top 2
                message = signal.get("message", "")
                drug = signal.get("drug", "")
                reaction = signal.get("reaction", "")
                
                if signal.get("has_llm_interpretation"):
                    interpretation = signal.get("llm_interpretation", "")
                    st.markdown(
                        f'<span class="quick-insights-chip-medium">🆕 {message}</span>',
                        unsafe_allow_html=True
                    )
                    st.caption(f"💡 {interpretation[:150]}..." if len(interpretation) > 150 else f"💡 {interpretation}")
                else:
                    st.markdown(
                        f'<span class="quick-insights-chip-medium">🆕 {message}</span>',
                        unsafe_allow_html=True
                    )
        
        # Show top 2 spikes
        if spikes:
            st.markdown("**📈 Recent Spikes:**")
            for spike in spikes[:2]:  # Top 2
                message = spike.get("message", "")
                st.markdown(
                    f'<span class="quick-insights-chip-medium">📈 {message}</span>',
                    unsafe_allow_html=True
                )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception:
        # Fail silently if trend alerts not available
        pass


def _render_ai_suggestions(normalized_df: pd.DataFrame):
    """
    Render AI-powered suggestions with auto-fill functionality.
    CHUNK 6.10-B: Now uses dynamic, data-driven suggestions engine.
    """
    st.markdown("### 💡 Try asking…")
    
    # CHUNK 6.10-B: Use dynamic suggestions engine instead of hardcoded strings
    from src.ai.suggestions_engine import compute_dynamic_suggestions_with_memory
    
    suggestions = compute_dynamic_suggestions_with_memory(normalized_df)
    
    if not suggestions:
        st.info("💡 Upload data to see personalized suggestions based on your dataset.")
        return
    
    pills_html = ""
    for s in suggestions:
        # Escape quotes for JavaScript
        escaped_query = s.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
        pills_html += f"""<span class="suggestion-pill" onclick="suggest_prefill('{escaped_query}')" title="{s}">{s}</span>"""
    
    st.markdown(pills_html, unsafe_allow_html=True)
