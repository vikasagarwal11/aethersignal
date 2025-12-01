"""
Portfolio Trend Visualizer (CHUNK 6.29)
Enterprise dashboard showing portfolio-wide safety trends and heatmaps.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

try:
    from src.portfolio.portfolio_trends import PortfolioTrendEngine
    PORTFOLIO_ENGINE_AVAILABLE = True
except ImportError:
    PORTFOLIO_ENGINE_AVAILABLE = False


def render_portfolio_trend_visualizer(df: Optional[pd.DataFrame] = None) -> None:
    """
    Render portfolio trend visualizer with heatmaps and trend lines.
    
    Args:
        df: DataFrame with portfolio data (multiple products/drugs)
    """
    if df is None or df.empty:
        st.info("Upload portfolio data to view trend visualizations.")
        return
    
    st.header("📊 Portfolio Trend Visualizer")
    st.markdown("Portfolio-wide safety intelligence across all therapeutic areas.")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔥 Portfolio Heatmap",
        "📈 Therapeutic Class Trends",
        "🌱 Emerging Signals",
        "⚡ Portfolio Risk Score"
    ])
    
    # Find relevant columns
    drug_col = _find_column(df, ["drug", "drug_name", "DRUG", "DRUGNAME"])
    reaction_col = _find_column(df, ["reaction", "reaction_pt", "PT", "REACTION"])
    date_col = _find_column(df, ["fda_dt", "FDA_DT", "date", "DATE"])
    
    if not drug_col or not reaction_col:
        st.error("Required columns (drug, reaction) not found in data.")
        return
    
    # TAB 1: Portfolio Heatmap
    with tab1:
        render_portfolio_heatmap(df, drug_col, reaction_col, date_col)
    
    # TAB 2: Therapeutic Class Trends
    with tab2:
        render_therapeutic_class_trends(df, drug_col, date_col)
    
    # TAB 3: Emerging Signals
    with tab3:
        render_emerging_signals(df, drug_col, reaction_col, date_col)
    
    # TAB 4: Portfolio Risk Score
    with tab4:
        render_portfolio_risk_score(df, drug_col, reaction_col)


def render_portfolio_heatmap(df: pd.DataFrame, drug_col: str, reaction_col: str, date_col: Optional[str]) -> None:
    """Render portfolio heatmap (Drug × Reaction Class)."""
    st.subheader("🔥 Portfolio Risk Heatmap")
    st.caption("Drug × Reaction Class trend deltas and risk scores.")
    
    # Group by drug and reaction
    pivot = df.groupby([drug_col, reaction_col]).size().reset_index(name='count')
    
    # Calculate trend delta if date available
    if date_col:
        # Get recent vs older counts
        df['period'] = pd.to_datetime(df[date_col], errors='coerce').dt.to_period('M')
        recent_periods = df['period'].dropna().nlargest(3)
        
        recent_counts = df[df['period'].isin(recent_periods)].groupby([drug_col, reaction_col]).size()
        older_counts = df[~df['period'].isin(recent_periods)].groupby([drug_col, reaction_col]).size()
        
        # Calculate trend delta
        trend_delta = {}
        for (drug, reaction), recent_count in recent_counts.items():
            older_count = older_counts.get((drug, reaction), 0)
            if older_count > 0:
                delta = ((recent_count - older_count) / older_count) * 100
                trend_delta[(drug, reaction)] = delta
            else:
                trend_delta[(drug, reaction)] = 100 if recent_count > 0 else 0
        
        pivot['trend_delta'] = pivot.apply(
            lambda row: trend_delta.get((row[drug_col], row[reaction_col]), 0),
            axis=1
        )
        
        # Create heatmap
        heatmap_data = pivot.pivot_table(
            index=drug_col,
            columns=reaction_col,
            values='trend_delta',
            aggfunc='mean',
            fill_value=0
        )
        
        fig = px.imshow(
            heatmap_data,
            aspect="auto",
            color_continuous_scale="RdYlGn_r",  # Red = increasing, Green = decreasing
            title="Drug × Reaction Trend Delta Heatmap",
            labels=dict(color="Trend Delta (%)")
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Simple count heatmap if no dates
        heatmap_data = pivot.pivot_table(
            index=drug_col,
            columns=reaction_col,
            values='count',
            aggfunc='sum',
            fill_value=0
        )
        
        fig = px.imshow(
            heatmap_data,
            aspect="auto",
            color_continuous_scale="Blues",
            title="Drug × Reaction Case Count Heatmap"
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)


def render_therapeutic_class_trends(df: pd.DataFrame, drug_col: str, date_col: Optional[str]) -> None:
    """Render therapeutic class trend lines."""
    st.subheader("📈 Therapeutic Class Trend Lines")
    st.caption("Rolling 3-6-12 month trends by therapeutic class.")
    
    if not date_col:
        st.info("Date column required for trend analysis.")
        return
    
    # Group by drug and date
    df['period'] = pd.to_datetime(df[date_col], errors='coerce').dt.to_period('M')
    monthly = df.groupby([drug_col, 'period']).size().reset_index(name='count')
    monthly['period'] = monthly['period'].astype(str)
    
    # Plot trend lines for each drug
    fig = go.Figure()
    
    for drug in monthly[drug_col].unique()[:20]:  # Top 20 drugs
        drug_data = monthly[monthly[drug_col] == drug].sort_values('period')
        
        # Calculate moving averages
        values = drug_data['count'].values
        ma3 = pd.Series(values).rolling(3, min_periods=1).mean()
        ma6 = pd.Series(values).rolling(6, min_periods=1).mean()
        
        fig.add_trace(go.Scatter(
            x=drug_data['period'],
            y=ma6,
            mode='lines',
            name=drug,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title="Therapeutic Class Trends (6-Month Moving Average)",
        xaxis_title="Period",
        yaxis_title="Case Count",
        height=500,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_emerging_signals(df: pd.DataFrame, drug_col: str, reaction_col: str, date_col: Optional[str]) -> None:
    """Render emerging class signals."""
    st.subheader("🌱 Top Emerging Class Signals")
    st.caption("Signals showing significant increases across the portfolio.")
    
    if not date_col:
        st.info("Date column required for emerging signal detection.")
        return
    
    # Calculate emerging scores
    df['period'] = pd.to_datetime(df[date_col], errors='coerce').dt.to_period('M')
    recent_periods = sorted(df['period'].dropna().unique())[-3:]
    older_periods = sorted(df['period'].dropna().unique())[:-3] if len(df['period'].dropna().unique()) > 3 else []
    
    emerging_scores = []
    
    for drug in df[drug_col].unique():
        for reaction in df[reaction_col].unique():
            drug_reac_data = df[(df[drug_col] == drug) & (df[reaction_col] == reaction)]
            
            if len(drug_reac_data) < 5:  # Need minimum cases
                continue
            
            recent_count = len(drug_reac_data[drug_reac_data['period'].isin(recent_periods)])
            older_count = len(drug_reac_data[drug_reac_data['period'].isin(older_periods)]) if older_periods else recent_count
            
            # Calculate MOM and YOY changes
            mom_change = ((recent_count - older_count) / older_count * 100) if older_count > 0 else 0
            
            # Emerging score
            emerging_score = (
                abs(mom_change) * 0.5 +
                recent_count * 0.3 +
                (recent_count - older_count) * 0.2
            )
            
            if emerging_score > 0:
                emerging_scores.append({
                    "drug": drug,
                    "reaction": reaction,
                    "emerging_score": emerging_score,
                    "mom_change": mom_change,
                    "recent_cases": recent_count,
                    "older_cases": older_count
                })
    
    # Sort and display top signals
    emerging_df = pd.DataFrame(emerging_scores).sort_values('emerging_score', ascending=False)
    
    if not emerging_df.empty:
        st.dataframe(emerging_df.head(20), use_container_width=True)
        
        # Visualize top signals
        top_signals = emerging_df.head(10)
        
        fig = px.bar(
            top_signals,
            x='drug',
            y='emerging_score',
            color='mom_change',
            title="Top 10 Emerging Signals",
            labels={'emerging_score': 'Emerging Score', 'mom_change': 'MOM Change (%)'},
            color_continuous_scale="Reds"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No emerging signals detected.")


def render_portfolio_risk_score(df: pd.DataFrame, drug_col: str, reaction_col: str) -> None:
    """Render portfolio risk score (PRS) per drug."""
    st.subheader("⚡ Portfolio Risk Score (PRS)")
    st.caption("Aggregate risk score per drug combining RPF, trends, and case growth.")
    
    # Calculate PRS for each drug
    prs_scores = []
    
    for drug in df[drug_col].unique():
        drug_data = df[df[drug_col] == drug]
        
        # Simplified PRS calculation
        case_count = len(drug_data)
        serious_count = len(drug_data[drug_data.get('serious', False)]) if 'serious' in drug_data.columns else 0
        
        # RPF component (simplified)
        rpf_component = min(100, (case_count / 100) * 0.6 + (serious_count / 10) * 0.4)
        
        # Trend component (simplified - would use actual trend engine)
        trend_component = 50  # Placeholder
        
        # Case growth component
        growth_component = min(100, case_count / 10)
        
        # PRS calculation
        prs = (rpf_component * 0.6) + (trend_component * 0.3) + (growth_component * 0.1)
        
        prs_scores.append({
            "drug": drug,
            "prs_score": prs,
            "case_count": case_count,
            "serious_count": serious_count,
            "risk_level": "high" if prs > 70 else "medium" if prs > 40 else "low"
        })
    
    prs_df = pd.DataFrame(prs_scores).sort_values('prs_score', ascending=False)
    
    # Display as gauges and table
    st.dataframe(prs_df, use_container_width=True)
    
    # Visualize PRS scores
    fig = px.bar(
        prs_df.head(15),
        x='drug',
        y='prs_score',
        color='risk_level',
        title="Portfolio Risk Score by Drug",
        labels={'prs_score': 'PRS Score', 'drug': 'Drug'},
        color_discrete_map={'high': 'red', 'medium': 'orange', 'low': 'green'}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def _find_column(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
    """Find column by possible names."""
    for name in possible_names:
        if name in df.columns:
            return name
    return None

