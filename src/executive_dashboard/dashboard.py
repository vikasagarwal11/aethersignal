"""
Main Executive Dashboard - Phase 3J Step 5
Assembles all components into a complete executive dashboard.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from .loaders import load_unified_ae_data
from .aggregator import ExecutiveAggregator
from .config import load_config, is_feature_enabled
from .visual.tiles import render_kpi_tiles
from .visual.trends import render_multi_source_trends
from .visual.tables import render_signal_ranking_table
from .visual.risk_matrix import render_severity_matrix
from .visual.novelty import render_novelty_panel
from .visual.geo import render_geographic_heatmap
from .narrative_ai import (
    build_context,
    generate_executive_summary,
    generate_risk_alert,
    generate_trending_risks
)

logger = logging.getLogger(__name__)


def render_executive_dashboard():
    """
    Render the complete Executive Drug Safety Dashboard.
    Main entry point for executive-level safety intelligence.
    Note: st.set_page_config() must be called in the page file, not here.
    """
    st.title("🌍 Executive Drug Safety Dashboard")
    st.caption("High-level multi-source safety intelligence for VPs, Directors, and Regulatory Leaders")
    
    # Load configuration
    config = load_config()
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")
        
        # Drug filter
        drug_filter = st.text_input(
            "Drug Name (optional)",
            value="",
            help="Filter by specific drug, or leave empty for all drugs"
        )
        
        # Days back
        days_back = st.number_input(
            "Days Back",
            min_value=7,
            max_value=365,
            value=config.get("display", {}).get("default_days_back", 90),
            help="Number of days to look back"
        )
        
        # Source selection
        st.subheader("📊 Data Sources")
        source_faers = st.checkbox("FAERS", value=config.get("sources", {}).get("faers", True))
        source_social = st.checkbox("Social AE", value=config.get("sources", {}).get("social", True))
        source_literature = st.checkbox("Literature", value=config.get("sources", {}).get("literature", True))
        
        # Feature toggles
        st.subheader("⚙️ Features")
        show_geo = st.checkbox("Geographic Analysis", value=config.get("features", {}).get("geo_analysis", False))
        show_narrative = st.checkbox("AI Narrative", value=config.get("features", {}).get("narrative_ai", True))
    
    # Load data
    with st.spinner("🔄 Loading multi-source safety data..."):
        try:
            sources_to_load = []
            if source_faers:
                sources_to_load.append("faers")
            if source_social:
                sources_to_load.append("social")
            if source_literature:
                sources_to_load.append("literature")
            
            df = load_unified_ae_data(
                drug=drug_filter if drug_filter else None,
                days_back=days_back,
                sources=sources_to_load if sources_to_load else None
            )
            
            if df.empty:
                st.warning("⚠️ No data available for the selected filters. Try adjusting your filters or ensure data sources are enabled.")
                st.info("💡 Tip: Check the Data Source Manager to ensure sources are configured and enabled.")
                return
            
            st.success(f"✅ Loaded {len(df):,} unified AE records from {df['source'].nunique() if 'source' in df.columns else 'multiple'} sources")
        
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            st.error(f"❌ Error loading data: {str(e)}")
            st.info("💡 Check logs for details. Ensure data sources are properly configured.")
            return
    
    # Initialize aggregator
    aggregator = ExecutiveAggregator()
    
    # Compute metrics
    with st.spinner("📊 Computing executive metrics..."):
        kpis = aggregator.compute_kpis(df, drug_filter if drug_filter else None, days_back=30)
        trends = aggregator.compute_trends(df, period="M")
        source_trends = aggregator.compute_source_trends(df, period="M")
        signal_ranking = aggregator.compute_signal_ranking(df, limit=50)
        novelty_signals = aggregator.compute_novelty_signals(df, limit=20)
    
    # Render KPI Tiles
    st.markdown("---")
    st.subheader("📊 Key Performance Indicators")
    render_kpi_tiles(kpis)
    st.markdown("---")
    
    # Multi-Source Trends
    st.subheader("📈 Multi-Source AE Trends")
    render_multi_source_trends(trends, source_trends)
    st.markdown("---")
    
    # Signal Ranking Table
    st.subheader("🔥 Top Safety Signals (Quantum-Ranked)")
    render_signal_ranking_table(signal_ranking, limit=50)
    st.markdown("---")
    
    # Novelty Panel
    st.subheader("🔍 Emerging & Novel Signals")
    render_novelty_panel(novelty_signals, show_venn=True)
    st.markdown("---")
    
    # Severity Matrix
    if is_feature_enabled("risk_matrix"):
        st.subheader("🚨 Severity Distribution Matrix")
        render_severity_matrix(df, drug_filter if drug_filter else None)
        st.markdown("---")
    
    # Geographic Heatmap
    if show_geo and is_feature_enabled("geo_analysis"):
        st.subheader("🌍 Geographic Distribution")
        render_geographic_heatmap(df, drug_filter if drug_filter else None)
        st.markdown("---")
    
    # AI Narrative Section
    if show_narrative and is_feature_enabled("narrative_ai"):
        st.subheader("📘 Executive Summary (AI-Generated)")
        
        # Build context for AI
        try:
            # Get mechanism labels if available
            mechanism_labels = None
            if is_feature_enabled("mechanism_ai") and "mechanism_label" in df.columns:
                mechanism_labels = df["mechanism_label"].dropna().unique().tolist()[:5]
            
            # Source breakdown
            source_breakdown = {}
            if "source" in df.columns:
                source_counts = df["source"].value_counts().to_dict()
                source_breakdown = source_counts
            
            context = build_context(
                kpis=kpis,
                top_signals=signal_ranking,
                novelty_df=novelty_signals,
                trend_df=trends,
                mechanism_labels=mechanism_labels,
                source_breakdown=source_breakdown
            )
            
            # Generate executive summary
            summary = generate_executive_summary(context)
            st.write(summary)
            
            # Risk alert
            st.subheader("⚠️ Internal Risk Alert")
            alert = generate_risk_alert(context)
            st.info(alert)
            
            # Trending risks (optional)
            with st.expander("📈 Trending Risks Analysis"):
                trending = generate_trending_risks(context)
                st.write(trending)
        
        except Exception as e:
            logger.error(f"Error generating AI narrative: {e}")
            st.warning("⚠️ AI narrative generation failed. Showing fallback summary.")
            st.write(_fallback_summary(kpis, signal_ranking))
    
    # Debug panel (SuperAdmin only)
    with st.expander("🔧 Debug: View Raw Data (SuperAdmin)"):
        st.write("**Data Summary:**")
        st.write(f"- Total Records: {len(df):,}")
        st.write(f"- Sources: {df['source'].unique().tolist() if 'source' in df.columns else 'N/A'}")
        st.write(f"- Date Range: {df['created_date'].min() if 'created_date' in df.columns else 'N/A'} to {df['created_date'].max() if 'created_date' in df.columns else 'N/A'}")
        
        st.write("**Sample Data:**")
        st.dataframe(df.head(100), use_container_width=True, height=400)
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data sources: {', '.join(df['source'].unique().tolist() if 'source' in df.columns else ['Multiple'])}")


def _fallback_summary(kpis: Dict[str, Any], signals: pd.DataFrame) -> str:
    """Generate fallback summary without AI."""
    summary = f"**Safety Summary:**\n\n"
    summary += f"Total Adverse Events: {kpis.get('total_ae', 0):,}. "
    summary += f"Last 30 days: {kpis.get('recent_count', 0):,} "
    summary += f"({kpis.get('change_pct', 0):+.1f}% change).\n\n"
    
    if not signals.empty:
        top_signal = signals.iloc[0]
        summary += f"**Top Signal:** {top_signal.get('reaction', 'Unknown')} "
        summary += f"(Quantum Score: {top_signal.get('quantum_score', 0):.2f}, "
        summary += f"Frequency: {top_signal.get('frequency', 0)}).\n\n"
    
    if kpis.get('novel_signal_count', 0) > 0:
        summary += f"**Novel Signals:** {kpis.get('novel_signal_count', 0)} reactions detected in social/literature but not yet in FAERS.\n\n"
    
    summary += "*AI narrative unavailable - showing fallback summary.*"
    
    return summary

