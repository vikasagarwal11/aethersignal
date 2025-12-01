"""
Heatmap Chart Renderer for AE Explorer
Creates heatmap visualizations for reaction-by-source analysis.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


def render_reaction_heatmap(df: pd.DataFrame, max_reactions: int = 20) -> go.Figure:
    """
    Render heatmap showing reaction counts by source.
    
    Args:
        df: DataFrame with AE entries
        max_reactions: Maximum number of reactions to display (top N by count)
    
    Returns:
        Plotly figure
    """
    if df.empty:
        # Return empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Prepare data
    df = df.copy()
    
    # Get top reactions by count
    if "reaction" in df.columns:
        top_reactions = df["reaction"].value_counts().head(max_reactions).index.tolist()
        df = df[df["reaction"].isin(top_reactions)]
    
    if df.empty or "source" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Create pivot table
    try:
        pivot = pd.pivot_table(
            df,
            values="drug" if "drug" in df.columns else df.columns[0],
            index="reaction",
            columns="source",
            aggfunc="count",
            fill_value=0
        )
        
        # Sort by total count
        pivot["total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("total", ascending=False)
        pivot = pivot.drop(columns=["total"])
        
    except Exception as e:
        # Fallback: simple count
        pivot = df.groupby(["reaction", "source"]).size().unstack(fill_value=0)
    
    if pivot.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Create heatmap
    fig = px.imshow(
        pivot,
        labels=dict(x="Source", y="Reaction", color="Count"),
        color_continuous_scale="Inferno",
        aspect="auto",
        title="Reaction × Source Heatmap"
    )
    
    fig.update_layout(
        height=max(400, len(pivot) * 25 + 100),
        xaxis_title="Source",
        yaxis_title="Reaction",
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    
    return fig


def render_severity_heatmap(df: pd.DataFrame, max_reactions: int = 20) -> go.Figure:
    """
    Render heatmap showing average severity by reaction and source.
    
    Args:
        df: DataFrame with AE entries
        max_reactions: Maximum number of reactions to display
    
    Returns:
        Plotly figure
    """
    if df.empty or "severity" not in df.columns:
        return render_reaction_heatmap(df, max_reactions)
    
    # Prepare data
    df = df.copy()
    
    # Get top reactions by count
    if "reaction" in df.columns:
        top_reactions = df["reaction"].value_counts().head(max_reactions).index.tolist()
        df = df[df["reaction"].isin(top_reactions)]
    
    if df.empty or "source" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Create pivot table with average severity
    try:
        pivot = pd.pivot_table(
            df,
            values="severity",
            index="reaction",
            columns="source",
            aggfunc="mean",
            fill_value=0
        )
        
        # Sort by total average severity
        pivot["avg"] = pivot.mean(axis=1)
        pivot = pivot.sort_values("avg", ascending=False)
        pivot = pivot.drop(columns=["avg"])
        
    except Exception:
        pivot = df.groupby(["reaction", "source"])["severity"].mean().unstack(fill_value=0)
    
    if pivot.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Create heatmap
    fig = px.imshow(
        pivot,
        labels=dict(x="Source", y="Reaction", color="Avg Severity"),
        color_continuous_scale="Reds",
        aspect="auto",
        title="Average Severity by Reaction × Source"
    )
    
    fig.update_layout(
        height=max(400, len(pivot) * 25 + 100),
        xaxis_title="Source",
        yaxis_title="Reaction",
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    
    return fig

