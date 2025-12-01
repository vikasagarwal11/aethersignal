"""
Geographic Heatmap - Phase 3J Step 3
Geographic distribution of adverse events.
"""

import pandas as pd
import streamlit as st
from typing import Optional
import plotly.express as px
import plotly.graph_objects as go


def render_geographic_heatmap(
    df: pd.DataFrame,
    drug: Optional[str] = None
):
    """
    Render geographic heatmap.
    
    Args:
        df: Unified AE DataFrame
        drug: Optional drug filter
    """
    if df.empty:
        st.info("No data available for geographic analysis")
        return
    
    if "country" not in df.columns:
        st.info("No geographic data available")
        return
    
    # Filter by drug if specified
    if drug:
        df = df[df["drug"].str.contains(drug, case=False, na=False)]
    
    if df.empty:
        st.info("No data for selected drug")
        return
    
    # Filter out unknown countries
    geo_df = df[df["country"].notna() & (df["country"] != "unknown")]
    
    if geo_df.empty:
        st.info("No valid geographic data available")
        return
    
    # Aggregate by country
    country_counts = geo_df.groupby("country").size().reset_index(name="count")
    country_counts = country_counts.sort_values("count", ascending=False)
    
    # Create choropleth map
    try:
        fig = px.choropleth(
            country_counts,
            locations="country",
            locationmode="country names",
            color="count",
            color_continuous_scale="Reds",
            title="Global AE Distribution by Country",
            labels={"count": "AE Count"}
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        # Fallback to bar chart if choropleth fails
        st.warning(f"Choropleth map unavailable: {e}. Showing bar chart instead.")
        
        fig = px.bar(
            country_counts.head(20),
            x="country",
            y="count",
            labels={"country": "Country", "count": "AE Count"},
            title="Top 20 Countries by AE Count"
        )
        
        fig.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Top countries table
    st.markdown("#### Top Countries")
    st.dataframe(
        country_counts.head(20),
        use_container_width=True,
        hide_index=True
    )

