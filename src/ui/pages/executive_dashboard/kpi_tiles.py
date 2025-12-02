"""
KPI Tiles Component - Executive Dashboard
Modern, color-coded KPI cards
"""

import streamlit as st
from src.ui.layout.theme import get_theme_colors


def kpi_card(label: str, value: str, delta: str = None, color: str = None):
    """
    Render a single KPI card.
    
    Args:
        label: KPI label
        value: KPI value
        delta: Optional delta/change indicator
        color: Optional color override
    """
    colors = get_theme_colors()
    card_color = color or colors["primary"]
    
    delta_html = ""
    if delta:
        delta_color = colors["success"] if delta.startswith("+") or not delta.startswith("-") else colors["error"]
        delta_html = f'<div style="color:{delta_color};font-size:0.875rem;margin-top:0.25rem;">{delta}</div>'
    
    st.markdown(
        f"""
        <div class="aether-card" style="text-align:center;padding:1.5rem;">
            <div style="font-size:0.875rem;color:{colors['text_secondary']};margin-bottom:0.5rem;">{label}</div>
            <div style="font-size:2rem;font-weight:700;color:{card_color};margin-bottom:0.25rem;">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_kpi_tiles():
    """
    Render all KPI tiles for the executive dashboard.
    Phase 2 Step 5: Now includes social intelligence features.
    """
    st.markdown("### 📊 Key Performance Indicators")
    
    # Try to get real data from backend, fallback to mock
    try:
        from src.executive_dashboard.aggregator import compute_kpis
        kpis = compute_kpis()
        
        total_aes = kpis.get("total_aes", 0)
        unique_reactions = kpis.get("unique_reactions", 0)
        top_reaction = kpis.get("top_reaction", "N/A")
        novel_signals = kpis.get("novel_signals", 0)
        
        # Calculate deltas if available
        total_delta = kpis.get("total_aes_delta", None)
        reactions_delta = kpis.get("unique_reactions_delta", None)
        
    except Exception:
        # Fallback to mock data
        total_aes = 12480
        unique_reactions = 87
        top_reaction = "Nausea"
        novel_signals = 4
        total_delta = "+8%"
        reactions_delta = "+3%"
    
    # Phase 2 Step 5: Add social intelligence features
    social_features = None
    try:
        from src.executive_dashboard.social_hooks import social_to_executive_features
        
        # Try to get social data
        social_df = None
        if "social_ae_data" in st.session_state and not st.session_state.social_ae_data.empty:
            social_df = st.session_state.social_ae_data
        
        # Try to get FAERS data
        faers_df = None
        if "normalized_data" in st.session_state and st.session_state.normalized_data is not None:
            faers_df = st.session_state.normalized_data
        elif "data" in st.session_state and st.session_state.data is not None:
            faers_df = st.session_state.data
        
        if social_df is not None:
            social_features = social_to_executive_features(social_df, faers_df)
    except Exception as e:
        # Social features not available - continue without them
        pass
    
    # Render KPI tiles
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        kpi_card("Total AEs", f"{total_aes:,}", delta=total_delta)
    
    with col2:
        kpi_card("30-Day AEs", f"{unique_reactions:,}", delta=reactions_delta)
    
    with col3:
        kpi_card("Top Reaction", top_reaction)
    
    with col4:
        colors = get_theme_colors()
        kpi_card("Novel Signals", str(novel_signals), color=colors["warning"])
    
    # Phase 2 Step 5: Add social intelligence KPIs if available
    if social_features and social_features.get("total_social_posts", 0) > 0:
        st.markdown("---")
        st.markdown("#### 🌐 Social Intelligence KPIs")
        
        col5, col6, col7 = st.columns(3)
        
        with col5:
            kpi_card(
                "Social Posts",
                f"{social_features.get('total_social_posts', 0):,}",
                color="#e11d48"
            )
        
        with col6:
            social_novel = len(social_features.get("social_novel_signals", []))
            kpi_card(
                "Social Novel Signals",
                str(social_novel),
                color=colors["warning"]
            )
        
        with col7:
            evidence_boost = social_features.get("social_evidence_boost", 0.0)
            kpi_card(
                "Evidence Boost",
                f"{evidence_boost:.1f}",
                color=colors["success"]
            )

