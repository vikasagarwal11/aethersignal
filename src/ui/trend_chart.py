"""
Trend Chart Renderer for AE Explorer
Creates time-series trend visualizations for adverse events.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
from datetime import datetime


def render_trend_chart(df: pd.DataFrame, date_col: str = "timestamp") -> go.Figure:
    """
    Render trend chart showing AE counts over time.
    
    Args:
        df: DataFrame with AE entries
        date_col: Name of date column
    
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
    
    # Convert timestamp to datetime
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df[df[date_col].notna()]
    
    if df.empty:
        # Return empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No valid timestamps available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Group by date
    df["date"] = df[date_col].dt.date
    trend = df.groupby("date").size().reset_index(name="count")
    trend = trend.sort_values("date")
    
    # Create line chart
    fig = px.line(
        trend,
        x="date",
        y="count",
        markers=True,
        title="AE Trends Over Time",
        color_discrete_sequence=["#2563eb"]
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="AE Count",
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified"
    )
    
    # Add moving average if enough data points
    if len(trend) >= 3:
        trend["ma"] = trend["count"].rolling(window=min(3, len(trend)), min_periods=1).mean()
        fig.add_trace(
            go.Scatter(
                x=trend["date"],
                y=trend["ma"],
                mode="lines",
                name="Moving Average (3-day)",
                line=dict(color="#ef4444", dash="dash", width=2),
                hovertemplate="MA: %{y:.1f}<extra></extra>"
            )
        )
    
    return fig


def render_trend_by_source(df: pd.DataFrame, date_col: str = "timestamp") -> go.Figure:
    """
    Render trend chart with separate lines for each source.
    
    Args:
        df: DataFrame with AE entries
        date_col: Name of date column
    
    Returns:
        Plotly figure
    """
    if df.empty or "source" not in df.columns:
        return render_trend_chart(df, date_col)
    
    # Prepare data
    df = df.copy()
    
    # Convert timestamp to datetime
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df[df[date_col].notna()]
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid timestamps available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Group by date and source
    df["date"] = df[date_col].dt.date
    trend = df.groupby(["date", "source"]).size().reset_index(name="count")
    trend = trend.sort_values("date")
    
    # Create line chart with color by source
    fig = px.line(
        trend,
        x="date",
        y="count",
        color="source",
        markers=True,
        title="AE Trends Over Time by Source",
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="AE Count",
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

