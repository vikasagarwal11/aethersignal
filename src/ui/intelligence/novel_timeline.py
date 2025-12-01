"""
Novel Signal Timeline - Visualize novel AE trends over time
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Optional


def render_novel_timeline(df: pd.DataFrame, reaction_col: str = "reaction", date_col: str = "date"):
    """
    Render novel AE timeline chart.
    
    Args:
        df: DataFrame with reaction and date columns
        reaction_col: Name of reaction column
        date_col: Name of date column
    """
    if df.empty:
        st.warning("No data available for timeline")
        return
    
    if reaction_col not in df.columns or date_col not in df.columns:
        st.error(f"Required columns not found: {reaction_col}, {date_col}")
        return
    
    try:
        # Prepare data
        timeline_df = df.copy()
        timeline_df[date_col] = pd.to_datetime(timeline_df[date_col])
        
        # Group by date and reaction
        daily_counts = timeline_df.groupby([date_col, reaction_col]).size().reset_index(name="count")
        
        # Create line chart
        fig = px.line(
            daily_counts,
            x=date_col,
            y="count",
            color=reaction_col,
            title="Novel AE Timelines",
            labels={
                date_col: "Date",
                "count": "Report Count",
                reaction_col: "Reaction"
            }
        )
        
        fig.update_layout(
            height=400,
            hovermode="x unified",
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error rendering timeline: {e}")

