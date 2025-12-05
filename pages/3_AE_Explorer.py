"""
AetherSignal - Unified AE Explorer
Dashboard for exploring adverse events from all sources (Social, FAERS, Literature, Free APIs).
"""

# Load environment variables from .env file (must be first!)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# PHASE 1.1: Session restoration is now centralized in initialize_session()
# No need to call restore_session() here - it's called in initialize_session()

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.auth.auth import is_authenticated
from src.ae_pipeline import AEPipeline
from src.ui.trend_chart import render_trend_chart
from src.ui.heatmap_chart import render_reaction_heatmap

# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="AetherSignal – AE Explorer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",  # Enables collapse/expand arrow
    menu_items=None,                    # Removes three-dot menu
)

# -------------------------------------------------------------------
# Apply centralized theme stylesheet
# -------------------------------------------------------------------
apply_theme()

# -------------------------------------------------------------------
# TOP NAVIGATION - MUST BE FIRST st.* CALL AFTER apply_theme()
# -------------------------------------------------------------------
render_top_nav()

# -------------------------------------------------------------------
# AUTHENTICATION CHECK
# -------------------------------------------------------------------
if not is_authenticated():
    st.warning("⚠️ Please log in to access the AE Explorer")
    if st.button("Go to Login"):
        st.switch_page("pages/Login.py")
    st.stop()

# -------------------------------------------------------------------
# PAGE CONTENT
# -------------------------------------------------------------------

st.title("🔍 Adverse Event Explorer")
st.markdown("**Unified dashboard showing FAERS + Social + Literature + Free APIs**")
st.caption("Aggregates adverse events from all configured data sources into a single view")

st.markdown("---")

# -------------------------------------------------------------------
# FILTERS
# -------------------------------------------------------------------

col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

with col1:
    drug = st.text_input(
        "Drug Name",
        value="Ozempic",
        help="Enter drug name to search across all sources"
    )

with col2:
    days_back = st.number_input(
        "Days Back (Social AE)",
        min_value=1,
        max_value=365,
        value=30,
        help="How many days back to search social media"
    )

with col3:
    include_social = st.checkbox("Include Social", value=True, help="Include social media sources")
    include_faers = st.checkbox("Include FAERS", value=True, help="Include FAERS data")

with col4:
    include_literature = st.checkbox("Include Literature", value=True, help="Include PubMed/ClinicalTrials")
    include_free_apis = st.checkbox("Include Free APIs", value=True, help="Include OpenFDA, EMA, etc.")

run_btn = st.button("🚀 Run Pipeline", type="primary", use_container_width=True)

if not run_btn or not drug:
    st.info("👆 Enter a drug name and click 'Run Pipeline' to start")
    st.stop()

# -------------------------------------------------------------------
# RUN PIPELINE
# -------------------------------------------------------------------

with st.spinner("🔄 Fetching and combining multi-source AE data... This may take a minute."):
    try:
        pipeline = AEPipeline()
        df = pipeline.run(
            drug=drug,
            days_back=days_back,
            include_social=include_social,
            include_faers=include_faers,
            include_literature=include_literature,
            include_free_apis=include_free_apis,
            store_results=True
        )
    except Exception as e:
        st.error(f"❌ Pipeline error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        st.stop()

if df.empty:
    st.warning(f"⚠️ No AE data found for '{drug}'. Try a different drug name or adjust filters.")
    st.info("💡 **Tip:** Make sure at least one source is enabled in the Data Source Manager")
    st.stop()

# -------------------------------------------------------------------
# SUMMARY METRICS
# -------------------------------------------------------------------

st.subheader("📊 Summary")

colA, colB, colC, colD = st.columns(4)

with colA:
    st.metric("Total AE Entries", f"{len(df):,}")

with colB:
    unique_reactions = df["reaction"].nunique()
    st.metric("Unique Reactions", f"{unique_reactions:,}")

with colC:
    unique_sources = df["source"].nunique()
    st.metric("Data Sources", f"{unique_sources:,}")

with colD:
    avg_confidence = df["confidence"].mean() if "confidence" in df.columns else 0
    st.metric("Avg Confidence", f"{avg_confidence:.2f}")

st.markdown("---")

# -------------------------------------------------------------------
# SOURCE BREAKDOWN
# -------------------------------------------------------------------

st.subheader("📈 Source Breakdown")

source_counts = df["source"].value_counts()
source_df = pd.DataFrame({
    "Source": source_counts.index,
    "Count": source_counts.values,
    "Percentage": (source_counts.values / len(df) * 100).round(1)
})

col1, col2 = st.columns([2, 1])

with col1:
    import plotly.express as px
    fig_bar = px.bar(
        source_df,
        x="Source",
        y="Count",
        title="AE Entries by Source",
        color="Count",
        color_continuous_scale="Blues"
    )
    fig_bar.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.dataframe(source_df, use_container_width=True, hide_index=True)

st.markdown("---")

# -------------------------------------------------------------------
# TRENDS
# -------------------------------------------------------------------

st.subheader("📈 AE Trend Over Time")

try:
    trend_fig = render_trend_chart(df)
    st.plotly_chart(trend_fig, use_container_width=True)
except Exception as e:
    st.error(f"Trend chart error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())

st.markdown("---")

# -------------------------------------------------------------------
# HEATMAP
# -------------------------------------------------------------------

st.subheader("🔥 Reaction Heatmap (Reaction × Source)")

try:
    heatmap_fig = render_reaction_heatmap(df)
    st.plotly_chart(heatmap_fig, use_container_width=True)
except Exception as e:
    st.error(f"Heatmap error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())

st.markdown("---")

# -------------------------------------------------------------------
# SEVERITY & CONFIDENCE DISTRIBUTION
# -------------------------------------------------------------------

if "severity" in df.columns and "confidence" in df.columns:
    st.subheader("📊 Severity & Confidence Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_severity = px.histogram(
            df,
            x="severity",
            nbins=20,
            title="Severity Distribution",
            labels={"severity": "Severity Score", "count": "Count"}
        )
        fig_severity.update_layout(height=300)
        st.plotly_chart(fig_severity, use_container_width=True)
    
    with col2:
        fig_confidence = px.histogram(
            df,
            x="confidence",
            nbins=20,
            title="Confidence Distribution",
            labels={"confidence": "Confidence Score", "count": "Count"}
        )
        fig_confidence.update_layout(height=300)
        st.plotly_chart(fig_confidence, use_container_width=True)
    
    st.markdown("---")

# -------------------------------------------------------------------
# TABLE VIEW
# -------------------------------------------------------------------

st.subheader("📋 AE Records")

# Filters
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    sources = st.multiselect(
        "Filter by Source",
        options=sorted(df["source"].unique()),
        default=None,
        help="Select sources to display"
    )

with filter_col2:
    reactions = st.multiselect(
        "Filter by Reaction",
        options=sorted(df["reaction"].unique()),
        default=None,
        help="Select reactions to display"
    )

with filter_col3:
    min_confidence = st.slider(
        "Min Confidence",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        help="Filter by minimum confidence score"
    )

# Apply filters
filtered = df.copy()

if sources:
    filtered = filtered[filtered["source"].isin(sources)]

if reactions:
    filtered = filtered[filtered["reaction"].isin(reactions)]

if "confidence" in filtered.columns:
    filtered = filtered[filtered["confidence"] >= min_confidence]

# Display filtered results
st.caption(f"Showing {len(filtered)} of {len(df)} records")

# Select columns to display
display_columns = ["timestamp", "drug", "reaction", "source", "confidence", "severity", "text"]
available_columns = [col for col in display_columns if col in filtered.columns]

st.dataframe(
    filtered[available_columns],
    use_container_width=True,
    height=500,
    hide_index=True
)

# Download button
if not filtered.empty:
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Results (CSV)",
        data=csv,
        file_name=f"ae_records_{drug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

