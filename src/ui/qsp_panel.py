"""
Quantitative Signal Prioritization (QSP) Panel (CHUNK 6.21.1 - Part 22)
Streamlit UI for displaying QSP prioritization results.
"""
import datetime
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from src.ai.qsp_engine import QSPEngine
    QSP_AVAILABLE = True
except ImportError:
    QSP_AVAILABLE = False


def extract_signals_from_df(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract signal-like structures from DataFrame for QSP analysis.
    
    Args:
        df: Normalized DataFrame
        
    Returns:
        List of signal dictionaries
    """
    if df is None or df.empty:
        return []
    
    signals = []
    
    # Detect column names
    drug_cols = ["drug", "drug_name", "drug_concept_name"]
    reaction_cols = ["reaction", "reaction_pt", "pt", "adverse_reaction"]
    serious_cols = ["serious", "seriousness", "serious_flag"]
    
    drug_col = next((col for col in drug_cols if col in df.columns), None)
    reaction_col = next((col for col in reaction_cols if col in df.columns), None)
    serious_col = next((col for col in serious_cols if col in df.columns), None)
    
    if not drug_col or not reaction_col:
        return []
    
    # Group by drug-reaction pairs
    grouped = df.groupby([drug_col, reaction_col])
    
    for (drug, reaction), group_df in grouped:
        total_cases = len(group_df)
        
        # Calculate serious cases
        if serious_col:
            serious_mask = group_df[serious_col].astype(str).str.lower().isin(["1", "yes", "y", "true", "serious"])
            serious_cases = serious_mask.sum()
        else:
            serious_cases = 0
        
        serious_rate = serious_cases / total_cases if total_cases > 0 else 0
        
        # Calculate PRR/ROR if available
        prr = 1
        ror = 1
        
        # Extract from group if available
        if "prr" in group_df.columns:
            prr = group_df["prr"].iloc[0] if not group_df["prr"].isna().all() else 1
        if "ror" in group_df.columns:
            ror = group_df["ror"].iloc[0] if not group_df["ror"].isna().all() else 1
        
        signal_dict = {
            "drug": drug,
            "reaction": reaction,
            "cases": total_cases,
            "count": total_cases,
            "serious_cases": serious_cases,
            "serious_count": serious_cases,
            "serious_rate": serious_rate,
            "fatal_cases": 0,  # Would need outcome column
            "prr": prr,
            "ror": ror,
        }
        
        signals.append(signal_dict)
    
    return signals


def render_qsp_tab(df: pd.DataFrame, signals: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Render Quantitative Signal Prioritization tab.
    
    Args:
        df: Normalized DataFrame
        signals: Optional pre-computed signals list
    """
    if not QSP_AVAILABLE:
        st.error("QSP Engine not available. Please install required dependencies.")
        return
    
    st.subheader("🔥 Quantitative Signal Prioritization (QSP)")
    
    st.markdown("""
    **QSP** ranks signals by urgency, regulatory impact, and clinical seriousness using:
    - Clinical Seriousness (30%)
    - Frequency/Reporting Rate (25%)
    - Disproportionality/Trend Acceleration (20%)
    - Population Vulnerability (10%)
    - Label Novelty (10%)
    - Evidence Strength (5%)
    """)
    
    # Extract signals if not provided
    if signals is None:
        with st.spinner("Extracting signals from data..."):
            signals = extract_signals_from_df(df)
    
    if not signals:
        st.warning("No signals found in the dataset. QSP requires drug-reaction pairs.")
        return
    
    # Initialize QSP engine
    qsp_engine = QSPEngine()
    
    # Compute QSP scores
    with st.spinner(f"Computing QSP scores for {len(signals)} signals..."):
        qsp_result = qsp_engine.prioritize_signals(signals, df=df)
    
    scored_signals = qsp_result.get("signals", [])
    summary = qsp_result.get("summary", {})
    narrative = qsp_result.get("narrative", "")
    
    if not scored_signals:
        st.warning("No signals could be scored.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Signals", summary.get("total_signals", 0))
    with col2:
        st.metric("High Priority", summary.get("high_priority_count", 0), 
                 delta=f"{summary.get('high_priority_count', 0)} require urgent review")
    with col3:
        st.metric("Medium Priority", summary.get("medium_priority_count", 0))
    with col4:
        st.metric("Avg QSP Score", f"{summary.get('average_qsp_score', 0):.1f}")
    
    st.divider()
    
    # Ranked Signal Priorities Table
    st.markdown("### 🔥 Ranked Signal Priorities")
    
    # Prepare display dataframe
    display_data = []
    for sig in scored_signals:
        components = sig.get("qsp_components", {})
        display_data.append({
            "Rank": len(display_data) + 1,
            "Drug": sig.get("drug", "Unknown"),
            "Reaction": sig.get("reaction", sig.get("event", "Unknown")),
            "QSP Score": f"{sig.get('qsp_score', 0):.1f}",
            "Priority": sig.get("qsp_priority", "Unknown"),
            "Cases": sig.get("cases", sig.get("count", 0)),
            "Serious Rate": f"{sig.get('serious_rate', 0)*100:.1f}%" if sig.get('serious_rate') else "N/A",
            "PRR": f"{sig.get('prr', 1):.2f}" if sig.get('prr') else "N/A",
            "ROR": f"{sig.get('ror', 1):.2f}" if sig.get('ror') else "N/A"
        })
    
    display_df = pd.DataFrame(display_data)
    
    # Color code by priority
    def color_priority(val):
        if val == "High":
            return "background-color: #ffcccc"
        elif val == "Medium":
            return "background-color: #fff4cc"
        else:
            return "background-color: #ccffcc"
    
    styled_df = display_df.style.applymap(color_priority, subset=["Priority"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Priority Distribution
    if PLOTLY_AVAILABLE:
        st.markdown("### 🧭 Priority Distribution")
        priority_counts = pd.Series([s.get("qsp_priority", "Unknown") for s in scored_signals]).value_counts()
        
        fig = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            title="Signal Priority Breakdown",
            color_discrete_map={
                "High": "#ff4444",
                "Medium": "#ffaa00",
                "Low": "#44ff44"
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # QSP Score Distribution
        st.markdown("### 📈 QSP Score Distribution")
        
        qsp_scores = [s.get("qsp_score", 0) for s in scored_signals]
        priorities = [s.get("qsp_priority", "Unknown") for s in scored_signals]
        
        fig2 = px.histogram(
            x=qsp_scores,
            color=priorities,
            nbins=20,
            title="Distribution of QSP Scores by Priority",
            labels={"x": "QSP Score", "y": "Number of Signals"},
            color_discrete_map={
                "High": "#ff4444",
                "Medium": "#ffaa00",
                "Low": "#44ff44"
            }
        )
        fig2.update_layout(template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
        
        # QSP Component Breakdown (for top signals)
        if len(scored_signals) > 0:
            st.markdown("### 📊 QSP Component Breakdown (Top 10 Signals)")
            
            top_10 = scored_signals[:10]
            component_data = []
            
            for sig in top_10:
                components = sig.get("qsp_components", {})
                signal_label = f"{sig.get('drug', 'Unknown')} - {sig.get('reaction', 'Unknown')}"
                
                component_data.append({
                    "Signal": signal_label,
                    "Clinical Seriousness": components.get("clinical_seriousness", 0) * 30,
                    "Frequency": components.get("frequency", 0) * 25,
                    "Disproportionality/Trend": components.get("disproportionality_trend", 0) * 20,
                    "Vulnerability": components.get("population_vulnerability", 0) * 10,
                    "Label Novelty": components.get("label_novelty", 0) * 10,
                    "Evidence Strength": components.get("evidence_strength", 0) * 5
                })
            
            component_df = pd.DataFrame(component_data)
            
            # Create stacked bar chart
            fig3 = go.Figure()
            
            components_cols = ["Clinical Seriousness", "Frequency", "Disproportionality/Trend",
                             "Vulnerability", "Label Novelty", "Evidence Strength"]
            colors = ["#e74c3c", "#3498db", "#f39c12", "#9b59b6", "#1abc9c", "#95a5a6"]
            
            for i, col in enumerate(components_cols):
                fig3.add_trace(go.Bar(
                    name=col,
                    x=component_df["Signal"],
                    y=component_df[col],
                    marker_color=colors[i]
                ))
            
            fig3.update_layout(
                title="QSP Component Contributions (Top 10 Signals)",
                xaxis_title="Signal",
                yaxis_title="Component Score",
                barmode="stack",
                height=500,
                template="plotly_white",
                xaxis_tickangle=-45
            )
            
            st.plotly_chart(fig3, use_container_width=True)
    
    # AI Narrative
    if narrative:
        st.markdown("### 🤖 QSP Prioritization Summary")
        with st.expander("View AI-Generated Narrative", expanded=True):
            st.markdown(narrative)
    
    # Export option
    st.markdown("### 💾 Export QSP Results")
    
    # Create export dataframe
    export_df = pd.DataFrame([
        {
            "Drug": s.get("drug", ""),
            "Reaction": s.get("reaction", s.get("event", "")),
            "QSP_Score": s.get("qsp_score", 0),
            "Priority": s.get("qsp_priority", ""),
            "Cases": s.get("cases", s.get("count", 0)),
            "Serious_Cases": s.get("serious_cases", s.get("serious_count", 0)),
            "Serious_Rate": s.get("serious_rate", 0),
            "PRR": s.get("prr", 1),
            "ROR": s.get("ror", 1)
        }
        for s in scored_signals
    ])
    
    # CSV export
    csv = export_df.to_csv(index=False)
    st.download_button(
        label="📥 Download QSP Results (CSV)",
        data=csv,
        file_name=f"qsp_prioritization_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

