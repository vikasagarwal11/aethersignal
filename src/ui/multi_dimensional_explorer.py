"""
Multi-Dimensional AE Explorer UI (Phase 3B)
Interactive dashboard with pivot tables, drill-down, and 20+ visualizations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from src.analytics.pivot_cube import PivotCube
from src.storage.federated_query_engine import FederatedQueryEngine

logger = logging.getLogger(__name__)


def render_multi_dimensional_explorer(
    query_engine: Optional[FederatedQueryEngine] = None
):
    """
    Render multi-dimensional AE explorer dashboard.
    
    Args:
        query_engine: Optional federated query engine
    """
    st.header("🔍 Multi-Dimensional AE Explorer")
    st.caption("Interactive pivot analysis, drill-down, and cross-source comparison")
    
    if query_engine is None:
        from src.storage.federated_query_engine import FederatedQueryEngine
        from src.storage.unified_storage import UnifiedStorageEngine
        storage = UnifiedStorageEngine()
        query_engine = FederatedQueryEngine(storage)
    
    # Initialize pivot cube
    pivot_cube = PivotCube(query_engine)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Pivot Analysis",
        "📈 Visualizations",
        "🌍 Cross-Source Comparison",
        "🔍 Drill-Down",
        "💾 Saved Views",
        "🤖 AI Insights"
    ])
    
    with tab1:
        render_pivot_analysis_tab(pivot_cube)
    
    with tab2:
        render_visualizations_tab(pivot_cube)
    
    with tab3:
        render_cross_source_tab(pivot_cube)
    
    with tab4:
        render_drill_down_tab(pivot_cube)
    
    with tab5:
        render_saved_views_tab()
    
    with tab6:
        render_ai_insights_tab(pivot_cube)


def render_pivot_analysis_tab(pivot_cube: PivotCube):
    """Render pivot analysis tab."""
    st.subheader("📊 Pivot Analysis")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        drug_filter = st.text_input("Drug Filter", "")
    with col2:
        reaction_filter = st.text_input("Reaction Filter", "")
    with col3:
        source_filter = st.multiselect(
            "Source Filter",
            options=["faers", "social", "pubmed", "clinicaltrials", "dailymed", "ema"],
            default=None
        )
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    # Build cube
    if st.button("🔨 Build Cube", type="primary"):
        with st.spinner("Building pivot cube..."):
            filters = {}
            if drug_filter:
                filters["drug"] = drug_filter
            if reaction_filter:
                filters["reaction"] = reaction_filter
            if source_filter:
                filters["sources"] = source_filter
            
            cube_df = pivot_cube.build_cube(
                filters=filters if filters else None,
                date_range=(start_date, end_date)
            )
            
            if not cube_df.empty:
                st.session_state["pivot_cube_data"] = cube_df
                st.success(f"✅ Cube built with {len(cube_df)} records")
            else:
                st.warning("⚠️ No data found for selected filters")
    
    # Pivot configuration
    if "pivot_cube_data" in st.session_state:
        st.markdown("---")
        st.subheader("Configure Pivot Table")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            index_dims = st.multiselect(
                "Row Dimensions",
                options=["drug_normalized", "reaction_normalized", "source", "severity_bucket", "age_group"],
                default=["drug_normalized", "reaction_normalized"]
            )
        with col2:
            column_dims = st.multiselect(
                "Column Dimensions",
                options=["source", "severity_bucket", "age_group", "sex"],
                default=["source"]
            )
        with col3:
            measure = st.selectbox(
                "Measure",
                options=["count", "mean", "sum"],
                index=0
            )
        
        if st.button("📊 Generate Pivot Table"):
            pivot_df = pivot_cube.pivot(
                index=index_dims,
                columns=column_dims if column_dims else None,
                aggfunc=measure
            )
            
            st.dataframe(pivot_df, use_container_width=True, height=500)


def render_visualizations_tab(pivot_cube: PivotCube):
    """Render visualizations tab."""
    st.subheader("📈 Visualizations")
    
    if "pivot_cube_data" not in st.session_state:
        st.info("👆 Build cube first in Pivot Analysis tab")
        return
    
    cube_df = st.session_state["pivot_cube_data"]
    
    # Visualization selector
    viz_type = st.selectbox(
        "Select Visualization",
        options=[
            "Trendlines",
            "Global Heatmap",
            "Severity Pyramid",
            "Reaction Clusters Map",
            "Co-occurrence Network",
            "Source Comparison",
            "Novelty Radar",
            "Burst Detection",
            "Age/Sex Breakdown",
            "Geographic Map"
        ]
    )
    
    if viz_type == "Trendlines":
        render_trendlines(pivot_cube, cube_df)
    elif viz_type == "Global Heatmap":
        render_global_heatmap(cube_df)
    elif viz_type == "Severity Pyramid":
        render_severity_pyramid(cube_df)
    elif viz_type == "Source Comparison":
        render_source_comparison(pivot_cube, cube_df)
    elif viz_type == "Age/Sex Breakdown":
        render_age_sex_breakdown(cube_df)


def render_trendlines(pivot_cube: PivotCube, cube_df: pd.DataFrame):
    """Render trendlines visualization."""
    st.markdown("### 📈 Trendlines")
    
    col1, col2 = st.columns(2)
    with col1:
        drug = st.selectbox("Select Drug", options=sorted(cube_df["drug_normalized"].unique()) if "drug_normalized" in cube_df.columns else [])
    with col2:
        reaction = st.selectbox("Select Reaction", options=sorted(cube_df["reaction_normalized"].unique()) if "reaction_normalized" in cube_df.columns else [])
    
    if drug and reaction:
        trend_df = pivot_cube.get_trend(drug=drug, reaction=reaction, period="month")
        
        if not trend_df.empty:
            fig = px.line(
                trend_df,
                x="period",
                y="count",
                markers=True,
                title=f"Trend: {drug} → {reaction}",
                labels={"period": "Period", "count": "AE Count"}
            )
            st.plotly_chart(fig, use_container_width=True)


def render_global_heatmap(cube_df: pd.DataFrame):
    """Render global heatmap."""
    st.markdown("### 🔥 Global Heatmap (Drug × Reaction)")
    
    if "drug_normalized" in cube_df.columns and "reaction_normalized" in cube_df.columns:
        pivot = pd.pivot_table(
            cube_df,
            index="reaction_normalized",
            columns="drug_normalized",
            values="ae_id" if "ae_id" in cube_df.columns else cube_df.columns[0],
            aggfunc="count",
            fill_value=0
        )
        
        fig = px.imshow(
            pivot,
            labels=dict(x="Drug", y="Reaction", color="Count"),
            color_continuous_scale="Inferno",
            aspect="auto"
        )
        st.plotly_chart(fig, use_container_width=True)


def render_severity_pyramid(cube_df: pd.DataFrame):
    """Render severity pyramid."""
    st.markdown("### ⚠️ Severity Pyramid")
    
    if "severity_bucket" in cube_df.columns:
        severity_counts = cube_df["severity_bucket"].value_counts()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=severity_counts.values,
            y=severity_counts.index,
            orientation='h',
            marker_color='lightblue'
        ))
        fig.update_layout(
            title="Severity Distribution",
            xaxis_title="Count",
            yaxis_title="Severity Level"
        )
        st.plotly_chart(fig, use_container_width=True)


def render_source_comparison(pivot_cube: PivotCube, cube_df: pd.DataFrame):
    """Render cross-source comparison."""
    st.markdown("### 🌍 Cross-Source Comparison")
    
    drug = st.selectbox("Select Drug", options=sorted(cube_df["drug_normalized"].unique()) if "drug_normalized" in cube_df.columns else [])
    
    if drug:
        comparison_df = pivot_cube.get_cross_source_comparison(drug=drug)
        
        if not comparison_df.empty:
            st.dataframe(comparison_df, use_container_width=True)
            
            # Visualize
            fig = px.bar(
                comparison_df,
                x="source",
                y="case_count",
                title=f"Case Count by Source: {drug}",
                labels={"source": "Source", "case_count": "Case Count"}
            )
            st.plotly_chart(fig, use_container_width=True)


def render_age_sex_breakdown(cube_df: pd.DataFrame):
    """Render age/sex breakdown."""
    st.markdown("### 👥 Age/Sex Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if "age_group" in cube_df.columns:
            age_counts = cube_df["age_group"].value_counts()
            fig_age = px.pie(
                values=age_counts.values,
                names=age_counts.index,
                title="Age Group Distribution"
            )
            st.plotly_chart(fig_age, use_container_width=True)
    
    with col2:
        if "sex" in cube_df.columns:
            sex_counts = cube_df["sex"].value_counts()
            fig_sex = px.pie(
                values=sex_counts.values,
                names=sex_counts.index,
                title="Sex Distribution"
            )
            st.plotly_chart(fig_sex, use_container_width=True)


def render_cross_source_tab(pivot_cube: PivotCube):
    """Render cross-source comparison tab."""
    st.subheader("🌍 Cross-Source Comparison")
    
    if "pivot_cube_data" not in st.session_state:
        st.info("👆 Build cube first")
        return
    
    cube_df = st.session_state["pivot_cube_data"]
    
    drug = st.selectbox("Select Drug", options=sorted(cube_df["drug_normalized"].unique()) if "drug_normalized" in cube_df.columns else [])
    reaction = st.selectbox("Select Reaction", options=sorted(cube_df["reaction_normalized"].unique()) if "reaction_normalized" in cube_df.columns else [])
    
    if drug and reaction:
        comparison_df = pivot_cube.get_cross_source_comparison(drug=drug, reaction=reaction)
        
        if not comparison_df.empty:
            st.dataframe(comparison_df, use_container_width=True)
            
            # Comparison chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=comparison_df["source"],
                y=comparison_df["case_count"],
                name="Case Count",
                marker_color="lightblue"
            ))
            fig.add_trace(go.Bar(
                x=comparison_df["source"],
                y=comparison_df["avg_quantum_score"] * 100,
                name="Avg Quantum Score (×100)",
                marker_color="orange"
            ))
            fig.update_layout(
                title=f"Cross-Source Comparison: {drug} → {reaction}",
                xaxis_title="Source",
                yaxis_title="Value",
                barmode="group"
            )
            st.plotly_chart(fig, use_container_width=True)


def render_drill_down_tab(pivot_cube: PivotCube):
    """Render drill-down tab."""
    st.subheader("🔍 Drill-Down Explorer")
    
    if "pivot_cube_data" not in st.session_state:
        st.info("👆 Build cube first")
        return
    
    cube_df = st.session_state["pivot_cube_data"]
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        drug = st.selectbox("Drug", options=[""] + sorted(cube_df["drug_normalized"].unique().tolist()) if "drug_normalized" in cube_df.columns else [""])
    with col2:
        reaction = st.selectbox("Reaction", options=[""] + sorted(cube_df["reaction_normalized"].unique().tolist()) if "reaction_normalized" in cube_df.columns else [""])
    
    level = st.selectbox("Detail Level", options=["summary", "detail", "raw"])
    
    if st.button("🔍 Drill Down"):
        filters = {}
        if drug:
            filters["drug_normalized"] = drug
        if reaction:
            filters["reaction_normalized"] = reaction
        
        result_df = pivot_cube.drill_down(filters, level=level)
        
        if not result_df.empty:
            st.dataframe(result_df, use_container_width=True, height=500)
        else:
            st.info("No data found for selected filters")


def render_saved_views_tab():
    """Render saved views tab."""
    st.subheader("💾 Saved Views")
    st.info("💡 Enterprise feature - Save and share custom dashboards")
    
    # Placeholder for saved views functionality
    st.write("Coming soon: Save custom pivot configurations, filters, and visualizations")


def render_ai_insights_tab(pivot_cube: PivotCube):
    """Render AI insights tab."""
    st.subheader("🤖 AI Insights")
    
    if "pivot_cube_data" not in st.session_state:
        st.info("👆 Build cube first")
        return
    
    cube_df = st.session_state["pivot_cube_data"]
    
    query = st.text_area("Ask about the data", placeholder="What's trending for GLP-1 drugs?")
    
    if st.button("🤖 Generate Insights"):
        # Placeholder for AI insights
        st.info("AI insights generation coming soon - will use LLM to analyze cube data and generate explanations")

