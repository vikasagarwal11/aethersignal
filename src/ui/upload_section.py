"""
Upload section component for AetherSignal.
Handles file upload, loading, and schema display.
"""

import pandas as pd
import streamlit as st

from src import analytics
from src import pv_schema
from src.app_helpers import cached_detect_and_normalize, load_all_files


def render_upload_section():
    """Render file upload UI and handle loading."""
    st.markdown(
        """
        <div class="session-chip-row" style="margin-bottom: 16px !important;">
            <div class="session-chip">🗂 Session-based, no login</div>
            <div class="session-chip">📄 Works with FAERS / CSV / Excel / PDF exports</div>
            <div class="session-chip">⚛️ Quantum-inspired ranking (demo)</div>
        </div>
        <div class='block-card' style="margin-top: 0 !important;">
            <h3>📤 1️⃣ Upload safety dataset</h3>
        """,
        unsafe_allow_html=True,
    )

    uploaded_files = st.file_uploader(
        "Drop FAERS ASCII, Argus/Veeva exports, CSV, Excel, text, ZIP or PDF",
        type=["csv", "xlsx", "xls", "txt", "zip", "pdf"],
        accept_multiple_files=True,
        help=(
            "You can upload multiple files. FAERS ASCII (DEMO/DRUG/REAC/OUTC…), "
            "Argus/Veeva exports, or ad-hoc CSV/Excel are supported."
        ),
    )

    load_clicked = st.button("🔄 Load & map data", disabled=not uploaded_files)

    if load_clicked and uploaded_files:
        with st.spinner("Loading and mapping data…"):
            raw_df = load_all_files(uploaded_files)
            if raw_df is None or raw_df.empty:
                st.error("❌ Could not read any rows from the provided files. Please verify formats.")
                
                # Add helpful suggestions
                st.markdown("**💡 What to try:**")
                st.markdown("""
                - **FAERS exports**: Ensure you upload all 7 ASCII files (DEMO, DRUG, REAC, OUTC, THER, INDI, RPSR) 
                  or a ZIP containing them.
                - **Argus/Veeva exports**: Export as CSV or Excel. Column names should include drug/reaction identifiers.
                - **CSV files**: Ensure proper comma separation and headers in the first row.
                - **Excel files**: Check that data starts in row 1 with headers.
                - **PDF files**: Only tabular PDFs are supported. Try exporting to CSV/Excel instead.
                """)
                
                if st.session_state.get("analytics_enabled"):
                    analytics.log_event("upload_failed", {"file_count": len(uploaded_files)})
            else:
                st.session_state.data = raw_df
                if st.session_state.get("analytics_enabled"):
                    analytics.log_event(
                        "upload_success",
                        {
                            "file_count": len(uploaded_files),
                            "row_count": len(raw_df),
                            "columns": len(raw_df.columns),
                        },
                    )

                # Use cached detection and normalization
                mapping, normalized = cached_detect_and_normalize(raw_df)
                st.session_state.schema_mapping = mapping

                essential = ["drug_name", "reaction", "case_id"]
                found = [f for f in essential if f in mapping]
                if len(found) == 0:
                    st.error(
                        "Critical: could not detect any essential PV fields "
                        "(drug_name, reaction, case_id). Check column names or input format."
                    )
                elif len(found) < 2:
                    st.warning(
                        "Only detected "
                        f"{len(found)} essential field(s): {', '.join(found)}. "
                        "Some analysis features may be limited."
                    )
                st.session_state.normalized_data = normalized
                st.success(f"✅ Loaded {len(raw_df):,} rows")

                # Dataset snapshot KPIs
                try:
                    drugs = (
                        normalized["drug_name"].nunique() if "drug_name" in normalized.columns else 0
                    )
                    reactions = (
                        normalized["reaction"].nunique() if "reaction" in normalized.columns else 0
                    )

                    dates = None
                    if "onset_date" in normalized.columns:
                        dates = pd.to_datetime(normalized["onset_date"], errors="coerce")
                    elif "report_date" in normalized.columns:
                        dates = pd.to_datetime(normalized["report_date"], errors="coerce")

                    if dates is not None:
                        dates = dates.dropna()
                        min_date = dates.min()
                        max_date = dates.max()
                    else:
                        min_date = max_date = None

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(
                            f"<p class='kpi-value'>{len(raw_df):,}</p>"
                            "<p class='kpi-label'>Rows loaded</p>",
                            unsafe_allow_html=True,
                        )
                    with c2:
                        st.markdown(
                            f"<p class='kpi-value'>{drugs:,}</p>"
                            "<p class='kpi-label'>Distinct drugs</p>",
                            unsafe_allow_html=True,
                        )
                    with c3:
                        st.markdown(
                            f"<p class='kpi-value'>{reactions:,}</p>"
                            "<p class='kpi-label'>Distinct reactions</p>",
                            unsafe_allow_html=True,
                        )

                    if min_date and max_date:
                        st.caption(
                            f"Detected date range: **{min_date.date().isoformat()} – {max_date.date().isoformat()}**"
                        )
                except Exception:
                    pass

                if mapping:
                    with st.expander("Detected schema mapping", expanded=False):
                        st.dataframe(
                            pv_schema.get_schema_summary(mapping),
                            use_container_width=True,
                            hide_index=True,
                        )
                st.session_state.show_results = False
                st.rerun()

    elif not uploaded_files:
        st.info("Upload at least one file to get started.")
    st.markdown("</div>", unsafe_allow_html=True)

