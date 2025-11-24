"""
Drill-down component for AetherSignal.
Enables clicking on table rows to see detailed case information.
"""

import pandas as pd
import streamlit as st
from typing import Dict, Optional, List, Tuple
from src.utils import normalize_text


def render_drill_down_table(
    df: pd.DataFrame,
    filtered_df: pd.DataFrame,
    key_prefix: str,
    drill_column: str,
    detail_columns: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Render a table with drill-down capability.
    
    Args:
        df: DataFrame to display (summary table)
        filtered_df: Full filtered DataFrame for drill-down
        key_prefix: Unique key prefix for this table
        drill_column: Column name to use for filtering (e.g., "Drug", "Reaction")
        detail_columns: Optional list of columns to show in detail view
        
    Returns:
        Selected value if row selected, None otherwise
    """
    # Display the summary table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        key=f"{key_prefix}_table",
    )
    
    # Use selectbox for row selection (works reliably in all Streamlit versions)
    if len(df) > 0:
        row_options = [f"{row[drill_column]} ({row.get('Count', 'N/A')} cases)" 
                       for _, row in df.iterrows()]
        
        selected_idx = st.selectbox(
            f"Select {drill_column.lower()} to drill down",
            range(len(df)),
            format_func=lambda x: row_options[x] if x < len(row_options) else "",
            key=f"{key_prefix}_select",
            label_visibility="collapsed",
        )
        
        if selected_idx is not None and selected_idx < len(df):
            selected_value = df.iloc[selected_idx][drill_column]
            return selected_value
    
    return None


def render_case_details(
    cases_df: pd.DataFrame,
    selected_value: str,
    filter_column: str,
    title: str,
    max_cases: int = 100,
) -> None:
    """
    Render detailed case information for selected drill-down value.
    
    Args:
        cases_df: Full DataFrame with all cases
        selected_value: Value to filter by (e.g., drug name, reaction name)
        filter_column: Column name to filter on
        title: Title for the detail section
        max_cases: Maximum number of cases to show
    """
    if cases_df.empty or not selected_value:
        return
    
    # Filter cases
    # Handle semicolon-separated values (e.g., "DUPIXENT; TACROLIMUS")
    if filter_column in cases_df.columns:
        # Check if the selected value appears in the column (handles semicolon-separated)
        mask = cases_df[filter_column].astype(str).str.contains(
            str(selected_value), case=False, na=False
        )
        filtered_cases = cases_df[mask].copy()
    else:
        return
    
    if filtered_cases.empty:
        st.info(f"No cases found for {title}: {selected_value}")
        return
    
    # Limit cases for performance
    display_cases = filtered_cases.head(max_cases)
    total_cases = len(filtered_cases)
    
    st.markdown("---")
    st.markdown(f"### 📋 Detailed Cases: {title} = **{selected_value}**")
    st.caption(f"Showing {len(display_cases):,} of {total_cases:,} cases")
    
    # Show case count summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cases", f"{total_cases:,}")
    with col2:
        if "seriousness" in display_cases.columns:
            serious_count = display_cases["seriousness"].apply(
                lambda x: normalize_text(str(x)) in ['1', 'yes', 'y', 'true', 'serious']
            ).sum()
            st.metric("Serious Cases", f"{serious_count:,}")
    with col3:
        if "outcome" in display_cases.columns or "outc_cod" in display_cases.columns:
            outcome_col = "outcome" if "outcome" in display_cases.columns else "outc_cod"
            fatal_count = display_cases[outcome_col].astype(str).str.contains(
                "death|fatal|died", case=False, na=False
            ).sum()
            st.metric("Fatal Cases", f"{fatal_count:,}")
    
    # Show detailed case table
    # Select relevant columns for display
    display_columns = []
    priority_columns = [
        "caseid", "primaryid", "drug_name", "reaction", "age", "sex", 
        "country", "seriousness", "outcome", "outc_cod", "report_date",
        "event_date", "onset_date"
    ]
    
    for col in priority_columns:
        if col in display_cases.columns:
            display_columns.append(col)
    
    # Add any other columns that exist
    for col in display_cases.columns:
        if col not in display_columns and col not in ["reaction_meddra"]:
            display_columns.append(col)
    
    # Limit to first 20 columns for readability
    display_columns = display_columns[:20]
    
    if display_columns:
        st.dataframe(
            display_cases[display_columns],
            use_container_width=True,
            height=400,
            hide_index=True,
        )
    
    # Export button
    if total_cases > 0:
        csv_data = filtered_cases.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"📥 Download all {total_cases:,} cases (CSV)",
            csv_data,
            f"cases_{selected_value.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True,
        )
    
    if total_cases > max_cases:
        st.info(
            f"⚠️ Showing first {max_cases:,} cases. Use the download button to get all {total_cases:,} cases."
        )


def render_drug_reaction_drill_down(
    drug: str,
    reaction: str,
    filtered_df: pd.DataFrame,
) -> None:
    """
    Render detailed cases for a specific drug-reaction combination.
    
    Args:
        drug: Drug name
        reaction: Reaction name
        filtered_df: Full filtered DataFrame
    """
    if filtered_df.empty:
        return
    
    # Filter for cases with both drug and reaction
    drug_mask = filtered_df["drug_name"].astype(str).str.contains(
        str(drug), case=False, na=False
    )
    reaction_mask = filtered_df["reaction"].astype(str).str.contains(
        str(reaction), case=False, na=False
    )
    
    cases = filtered_df[drug_mask & reaction_mask].copy()
    
    if cases.empty:
        st.info(f"No cases found for drug '{drug}' and reaction '{reaction}'")
        return
    
    st.markdown("---")
    st.markdown(f"### 📋 Detailed Cases: **{drug}** + **{reaction}**")
    st.caption(f"Showing {len(cases):,} cases")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cases", f"{len(cases):,}")
    with col2:
        if "seriousness" in cases.columns:
            serious_count = cases["seriousness"].apply(
                lambda x: normalize_text(str(x)) in ['1', 'yes', 'y', 'true', 'serious']
            ).sum()
            st.metric("Serious Cases", f"{serious_count:,}")
    with col3:
        if "outcome" in cases.columns or "outc_cod" in cases.columns:
            outcome_col = "outcome" if "outcome" in cases.columns else "outc_cod"
            fatal_count = cases[outcome_col].astype(str).str.contains(
                "death|fatal|died", case=False, na=False
            ).sum()
            st.metric("Fatal Cases", f"{fatal_count:,}")
    
    # Display columns
    display_columns = []
    priority_columns = [
        "caseid", "primaryid", "drug_name", "reaction", "age", "sex",
        "country", "seriousness", "outcome", "outc_cod", "report_date"
    ]
    
    for col in priority_columns:
        if col in cases.columns:
            display_columns.append(col)
    
    # Add other columns
    for col in cases.columns:
        if col not in display_columns and col not in ["reaction_meddra"]:
            display_columns.append(col)
    
    display_columns = display_columns[:20]
    
    if display_columns:
        st.dataframe(
            cases[display_columns],
            use_container_width=True,
            height=400,
            hide_index=True,
        )
    
    # Export
    csv_data = cases.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"📥 Download {len(cases):,} cases (CSV)",
        csv_data,
        f"cases_{drug.replace(' ', '_')}_{reaction.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        use_container_width=True,
    )

