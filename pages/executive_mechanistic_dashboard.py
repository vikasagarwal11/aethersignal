"""
Executive Mechanistic Dashboard - Global mechanistic safety intelligence
"""

import streamlit as st
from typing import List, Dict, Any, Optional
import pandas as pd

from src.ui.executive.mech_fusion_tiles import mech_tile
from src.ui.executive.mech_ranking_table import mech_ranking_table
from src.ui.executive.global_mech_heatmap import global_mech_heatmap
from src.ui.executive.mechanistic_signal_card import mechanistic_signal_card
from src.ui.layout.base_layout import render_base_layout


def _get_mechanistic_results() -> List[Dict[str, Any]]:
    """
    Get mechanistic analysis results.
    This should integrate with actual data sources.
    
    Returns:
        List of mechanistic analysis entries
    """
    # TODO: Integrate with actual MechanismSupervisor and data sources
    # For now, return empty list (will be populated by actual analysis)
    return st.session_state.get("mechanistic_results", [])


def render_executive_mechanistic_dashboard():
    """
    Render the Executive Mechanistic Dashboard.
    """
    def page_content():
        st.title("🏛 Global Mechanistic Safety Dashboard")
        st.caption("Executive-level view of mechanism-validated safety signals")
        
        # Get mechanistic results
        entries = _get_mechanistic_results()
        
        if not entries:
            st.info("""
            **No mechanistic analysis results available.**
            
            To generate results:
            1. Run analyses in the Mechanism Explorer
            2. Or configure automatic batch processing
            """)
            
            # Demo mode toggle
            if st.checkbox("Show Demo Data"):
                entries = [
                    {
                        "drug": "semaglutide",
                        "reaction": "nausea",
                        "fusion": {"fusion_score": 0.85},
                        "causal": {"causal_score": 0.78},
                        "novel": False,
                        "alert": {"alert": True, "alert_score": 0.82},
                        "evidence_score": {"score": 0.81}
                    },
                    {
                        "drug": "semaglutide",
                        "reaction": "pancreatitis",
                        "fusion": {"fusion_score": 0.72},
                        "causal": {"causal_score": 0.65},
                        "novel": True,
                        "alert": {"alert": True, "alert_score": 0.75},
                        "evidence_score": {"score": 0.70}
                    },
                    {
                        "drug": "tirzepatide",
                        "reaction": "gastroparesis",
                        "fusion": {"fusion_score": 0.68},
                        "causal": {"causal_score": 0.60},
                        "novel": False,
                        "alert": {"alert": False, "alert_score": 0.55},
                        "evidence_score": {"score": 0.62}
                    }
                ]
        
        if not entries:
            return
        
        # KPI Tiles
        st.markdown("### 📊 Mechanistic KPIs")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            mech_tile("Signals Evaluated", len(entries))
        
        with col2:
            high_alerts = sum(1 for e in entries if e.get("alert", {}).get("alert", False))
            mech_tile("High Alerts", high_alerts, "#dc2626")
        
        with col3:
            novel_pairs = sum(1 for e in entries if e.get("novel", False))
            mech_tile("Novel Pairs", novel_pairs, "#10b981")
        
        with col4:
            avg_evidence = sum(
                e.get("evidence_score", {}).get("score", 0.0) if isinstance(e.get("evidence_score"), dict)
                else float(e.get("evidence_score", 0.0))
                for e in entries
            ) / len(entries) if entries else 0.0
            mech_tile("Avg Evidence", f"{avg_evidence:.3f}", "#f59e0b")
        
        st.markdown("---")
        
        # Global Heatmap
        st.markdown("### 🌐 Global Evidence Heatmap")
        st.caption("Cross-drug and cross-reaction mechanistic evidence strength")
        global_mech_heatmap(entries)
        
        st.markdown("---")
        
        # Ranking Table
        st.markdown("### 🏆 Evidence Ranking")
        st.caption("Signals ranked by unified evidence score (Quantum + Causal + Mechanistic)")
        mech_ranking_table(entries)
        
        st.markdown("---")
        
        # Filtering Options
        with st.expander("🔍 Filter Options"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_evidence = st.slider(
                    "Min Evidence Score",
                    0.0, 1.0, 0.0, 0.05
                )
            
            with col2:
                show_novel_only = st.checkbox("Novel Signals Only", False)
            
            with col3:
                show_alerts_only = st.checkbox("Alerts Only", False)
            
            # Apply filters
            filtered_entries = entries
            if min_evidence > 0:
                filtered_entries = [
                    e for e in filtered_entries
                    if (e.get("evidence_score", {}).get("score", 0.0) if isinstance(e.get("evidence_score"), dict)
                        else float(e.get("evidence_score", 0.0))) >= min_evidence
                ]
            if show_novel_only:
                filtered_entries = [e for e in filtered_entries if e.get("novel", False)]
            if show_alerts_only:
                filtered_entries = [e for e in filtered_entries if e.get("alert", {}).get("alert", False)]
        
        # Individual Signal Cards
        st.markdown("### 🧩 Detailed Mechanistic Signal Cards")
        st.caption(f"Showing {len(filtered_entries)} signal(s)")
        
        if filtered_entries:
            for e in filtered_entries:
                mechanistic_signal_card(e)
        else:
            st.info("No signals match the selected filters.")
        
        st.markdown("---")
        
        # Export Options
        st.markdown("### 📥 Export")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export to CSV"):
                try:
                    df = pd.DataFrame([
                        {
                            "Drug": e.get("drug"),
                            "Reaction": e.get("reaction"),
                            "Evidence Score": e.get("evidence_score", {}).get("score", 0.0) if isinstance(e.get("evidence_score"), dict) else float(e.get("evidence_score", 0.0)),
                            "Fusion": e.get("fusion", {}).get("fusion_score", 0.0) if isinstance(e.get("fusion"), dict) else 0.0,
                            "Causal": e.get("causal", {}).get("causal_score", 0.0) if isinstance(e.get("causal"), dict) else 0.0,
                            "Novel": e.get("novel", False),
                            "Alert": e.get("alert", {}).get("alert", False)
                        }
                        for e in filtered_entries
                    ])
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="mechanistic_signals.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Export error: {e}")
        
        with col2:
            if st.button("Export to JSON"):
                try:
                    import json
                    json_data = json.dumps(filtered_entries, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name="mechanistic_signals.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Export error: {e}")
    
    render_base_layout(page_content)

