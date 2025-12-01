"""
KPI Tiles Component - Phase 3J Step 3
Executive-level KPI summary tiles.
"""

import streamlit as st
from typing import Dict, Any


def render_kpi_tiles(kpis: Dict[str, Any]):
    """
    Render KPI summary tiles.
    
    Args:
        kpis: Dictionary with KPI metrics
    """
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            "Total AEs",
            f"{kpis.get('total_ae', 0):,}",
            delta=None
        )
    
    with col2:
        recent_count = kpis.get('recent_count', 0)
        change_pct = kpis.get('change_pct', 0.0)
        delta = f"{change_pct:+.1f}%" if change_pct != 0 else None
        st.metric(
            "Last 30 Days",
            f"{recent_count:,}",
            delta=delta
        )
    
    with col3:
        top_reaction = kpis.get('top_reaction', '—')
        top_count = kpis.get('top_reaction_count', 0)
        st.metric(
            "Top Reaction",
            top_reaction[:20] if top_reaction else "—",
            delta=f"{top_count} cases" if top_count > 0 else None
        )
    
    with col4:
        severe_reaction = kpis.get('severe_reaction', '—')
        severe_count = kpis.get('severe_count', 0)
        st.metric(
            "Severe Reaction",
            severe_reaction[:20] if severe_reaction else "—",
            delta=f"{severe_count} cases" if severe_count > 0 else None
        )
    
    with col5:
        novel_count = kpis.get('novel_signal_count', 0)
        st.metric(
            "Novel Signals",
            novel_count,
            delta="New" if novel_count > 0 else None
        )
    
    with col6:
        avg_quantum = kpis.get('avg_quantum_score', 0.0)
        st.metric(
            "Avg Quantum Score",
            f"{avg_quantum:.2f}",
            delta=None
        )

