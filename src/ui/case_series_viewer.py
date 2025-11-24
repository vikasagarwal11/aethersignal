"""
Case Series Viewer for AetherSignal.
Displays individual cases with timeline visualization and narrative.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
import streamlit as st
from datetime import datetime
from src.utils import parse_date
from src.app_helpers import format_reaction_with_meddra


def render_case_series_viewer(
    df: pd.DataFrame,
    drug: Optional[str] = None,
    reaction: Optional[str] = None,
    max_cases: int = 50
) -> None:
    """
    Render case series viewer with timeline and case details.
    
    Args:
        df: DataFrame with case data
        drug: Optional drug filter
        reaction: Optional reaction filter
        max_cases: Maximum number of cases to display
    """
    filtered_df = df.copy()
    
    # Apply filters
    if drug and "drug_name" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["drug_name"].str.contains(drug, case=False, na=False)]
    
    if reaction and "reaction" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["reaction"].str.contains(reaction, case=False, na=False)]
    
    if filtered_df.empty:
        st.info("No cases found matching the criteria.")
        return
    
    # Limit cases
    display_df = filtered_df.head(max_cases)
    
    st.markdown("### 📋 Case Series")
    st.caption(f"Showing {len(display_df)} of {len(filtered_df)} matching cases")
    
    # Timeline visualization
    if "onset_date" in display_df.columns or "report_date" in display_df.columns:
        _render_timeline(display_df)
    
    # Case details
    _render_case_details(display_df)


def _render_timeline(df: pd.DataFrame) -> None:
    """Render timeline visualization of cases."""
    st.markdown("#### 📅 Timeline")
    
    # Prepare timeline data
    timeline_data = []
    
    for idx, row in df.iterrows():
        case_id = str(row.get("caseid", row.get("primaryid", f"Case-{idx}")))
        
        # Onset date
        onset_date = None
        if "onset_date" in row.index:
            onset_date = parse_date(row["onset_date"])
        
        # Report date
        report_date = None
        if "report_date" in row.index:
            report_date = parse_date(row["report_date"])
        
        # Drug start date (if available)
        start_date = None
        if "start_date" in row.index:
            start_date = parse_date(row["start_date"])
        
        if onset_date or report_date:
            timeline_data.append({
                "case_id": case_id,
                "onset_date": onset_date,
                "report_date": report_date,
                "start_date": start_date,
                "drug": row.get("drug_name", "Unknown"),
                "reaction": row.get("reaction", "Unknown"),
                "serious": row.get("seriousness", False),
            })
    
    if not timeline_data:
        st.info("No date information available for timeline.")
        return
    
    # Create timeline plot
    fig = go.Figure()
    
    # Plot onset dates
    onset_dates = [d["onset_date"] for d in timeline_data if d["onset_date"]]
    if onset_dates:
        onset_y = list(range(len(onset_dates)))
        fig.add_trace(go.Scatter(
            x=onset_dates,
            y=onset_y,
            mode='markers',
            name='Onset Date',
            marker=dict(color='red', size=8, symbol='circle'),
            hovertemplate='<b>%{text}</b><br>Onset: %{x}<extra></extra>',
            text=[d["case_id"] for d in timeline_data if d["onset_date"]]
        ))
    
    # Plot report dates
    report_dates = [d["report_date"] for d in timeline_data if d["report_date"]]
    if report_dates:
        report_y = list(range(len(report_dates)))
        fig.add_trace(go.Scatter(
            x=report_dates,
            y=report_y,
            mode='markers',
            name='Report Date',
            marker=dict(color='blue', size=8, symbol='square'),
            hovertemplate='<b>%{text}</b><br>Report: %{x}<extra></extra>',
            text=[d["case_id"] for d in timeline_data if d["report_date"]]
        ))
    
    # Plot drug start dates (if available)
    start_dates = [d["start_date"] for d in timeline_data if d["start_date"]]
    if start_dates:
        start_y = list(range(len(start_dates)))
        fig.add_trace(go.Scatter(
            x=start_dates,
            y=start_y,
            mode='markers',
            name='Drug Start',
            marker=dict(color='green', size=8, symbol='triangle-up'),
            hovertemplate='<b>%{text}</b><br>Drug Start: %{x}<extra></extra>',
            text=[d["case_id"] for d in timeline_data if d["start_date"]]
        ))
    
    fig.update_layout(
        title="Case Timeline",
        xaxis_title="Date",
        yaxis_title="Case Index",
        height=400,
        hovermode='closest',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_case_details(df: pd.DataFrame) -> None:
    """Render detailed case information."""
    st.markdown("#### 📄 Case Details")
    
    # Case selection
    case_ids = [str(row.get("caseid", row.get("primaryid", f"Case-{idx}"))) 
                for idx, row in df.iterrows()]
    
    if len(case_ids) > 1:
        selected_case = st.selectbox("Select case to view details:", case_ids, key="case_series_selection")
    else:
        selected_case = case_ids[0] if case_ids else None
    
    if not selected_case:
        return
    
    # Find selected case
    case_idx = case_ids.index(selected_case)
    case_row = df.iloc[case_idx]
    
    # Display case information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Case Information**")
        st.write(f"**Case ID:** {selected_case}")
        
        if "primaryid" in case_row.index:
            st.write(f"**Primary ID:** {case_row['primaryid']}")
        
        if "report_date" in case_row.index:
            report_date = parse_date(case_row["report_date"])
            if report_date:
                st.write(f"**Report Date:** {report_date.strftime('%Y-%m-%d')}")
        
        if "onset_date" in case_row.index:
            onset_date = parse_date(case_row["onset_date"])
            if onset_date:
                st.write(f"**Onset Date:** {onset_date.strftime('%Y-%m-%d')}")
        
        if "seriousness" in case_row.index:
            serious = case_row["seriousness"]
            serious_label = "✅ Serious" if serious else "ℹ️ Non-serious"
            st.write(f"**Seriousness:** {serious_label}")
        
        if "outcome" in case_row.index:
            st.write(f"**Outcome:** {case_row['outcome']}")
    
    with col2:
        st.markdown("**Patient Information**")
        
        if "age" in case_row.index:
            st.write(f"**Age:** {case_row['age']}")
        
        if "sex" in case_row.index:
            st.write(f"**Sex:** {case_row['sex']}")
        
        if "country" in case_row.index:
            st.write(f"**Country:** {case_row['country']}")
        
        if "weight" in case_row.index:
            st.write(f"**Weight:** {case_row['weight']}")
    
    # Drugs
    st.markdown("**💊 Drug(s)**")
    if "drug_name" in case_row.index:
        drugs = str(case_row["drug_name"]).split(";")
        for drug in drugs:
            drug = drug.strip()
            if drug:
                st.write(f"- {drug}")
    else:
        st.write("No drug information available")
    
    # Reactions
    st.markdown("**⚠️ Reaction(s)**")
    if "reaction" in case_row.index:
        reactions = str(case_row["reaction"]).split(";")
        for reaction in reactions:
            reaction = reaction.strip()
            if reaction:
                # Format with MedDRA if available
                formatted = format_reaction_with_meddra(reaction, case_row)
                st.write(f"- {formatted}")
    else:
        st.write("No reaction information available")
    
    # Narrative (if available)
    if "narrative" in case_row.index or "case_narrative" in case_row.index:
        narrative = case_row.get("narrative") or case_row.get("case_narrative", "")
        if narrative and str(narrative) != "nan":
            st.markdown("**📝 Narrative**")
            st.text_area("", value=str(narrative), height=150, disabled=True, key=f"narrative_{selected_case}")
    
    # Time-to-onset (if available)
    if "tto_days" in case_row.index and pd.notna(case_row["tto_days"]):
        tto = case_row["tto_days"]
        if tto >= 0:
            st.markdown("**⏱️ Time-to-Onset**")
            st.write(f"{int(tto)} days")
    
    st.markdown("---")

