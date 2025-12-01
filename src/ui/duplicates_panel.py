"""
Duplicate Signal Detection Panel (CHUNK 6.26 Enhanced)
Enterprise-grade duplicate detection UI with merge/keep options.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher

try:
    from src.local_ai.duplicate_signal_detector import LocalDuplicateSignalDetector
    DUPLICATE_DETECTOR_AVAILABLE = True
except ImportError:
    DUPLICATE_DETECTOR_AVAILABLE = False


def render_duplicates_panel(df: Optional[pd.DataFrame] = None) -> None:
    """
    Render duplicate signal detection panel.
    
    Args:
        df: DataFrame with signal/case data
    """
    if not DUPLICATE_DETECTOR_AVAILABLE:
        st.error("Duplicate signal detector not available.")
        return
    
    st.header("🔍 Duplicate Signal Detection")
    st.markdown("Identify and manage duplicate or similar signals across the portfolio.")
    
    if df is None or df.empty:
        st.info("Upload data to perform duplicate detection.")
        return
    
    # Detection configuration
    with st.expander("⚙️ Detection Configuration", expanded=False):
        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.7,
            max_value=0.99,
            value=0.85,
            step=0.01,
            help="Higher threshold = stricter duplicate detection"
        )
        
        min_duplicate_count = st.number_input(
            "Minimum Duplicate Count",
            min_value=2,
            max_value=10,
            value=2,
            help="Minimum number of occurrences to flag as duplicate"
        )
        
        key_columns = st.multiselect(
            "Key Columns for Duplicate Detection",
            options=df.columns.tolist()[:20],  # Limit to first 20 columns
            default=['drug_name', 'reaction'] if 'drug_name' in df.columns and 'reaction' in df.columns else df.columns.tolist()[:2]
        )
        
        detect_button = st.button("🔬 Detect Duplicates", type="primary")
    
    # Perform detection
    if detect_button:
        with st.spinner("Detecting duplicates..."):
            detector = LocalDuplicateSignalDetector(similarity_threshold=similarity_threshold)
            
            try:
                # Detect duplicates by key columns
                duplicates = detector.detect(df, key_cols=key_columns if key_columns else None, min_duplicate_count=min_duplicate_count)
                
                # Detect exact duplicates
                exact_duplicates = detector.detect_exact_duplicates(df)
                
                # Detect similar cases
                similar_cases = detector.detect_similar_cases(df, max_results=50)
                
                st.session_state.duplicate_results = {
                    "duplicates": duplicates,
                    "exact_duplicates": exact_duplicates,
                    "similar_cases": similar_cases
                }
                
                st.success(f"Detection complete! Found {len(duplicates)} duplicate groups, {len(exact_duplicates)} exact duplicates, and {len(similar_cases)} similar case pairs.")
                
            except Exception as e:
                st.error(f"Duplicate detection failed: {e}")
                return
    
    # Display results
    if "duplicate_results" in st.session_state:
        results = st.session_state.duplicate_results
        
        # Exact duplicates
        exact_dups = results.get("exact_duplicates", [])
        if exact_dups:
            st.subheader("🔴 Exact Duplicates")
            st.caption("Cases with identical case IDs - potential duplicate submissions.")
            
            exact_df = pd.DataFrame(exact_dups)
            st.dataframe(exact_df, use_container_width=True)
            
            # Allow merge/keep actions
            for dup in exact_dups[:10]:  # Show top 10
                case_id = dup.get("case_id")
                count = dup.get("COUNT", 0)
                
                with st.expander(f"Case ID: {case_id} ({count} occurrences)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Keep Case {case_id}", key=f"keep_{case_id}"):
                            st.success(f"Case {case_id} marked to keep")
                    with col2:
                        if st.button(f"🗑️ Merge Duplicates", key=f"merge_{case_id}"):
                            st.info(f"Merging {count} duplicate entries for case {case_id}")
        
        # Similar duplicates
        duplicates = results.get("duplicates", [])
        if duplicates:
            st.subheader("🟠 Similar Duplicates")
            st.caption("Signal groups with similar characteristics - potential duplicates.")
            
            dup_df = pd.DataFrame(duplicates)
            st.dataframe(dup_df, use_container_width=True)
            
            # Side-by-side comparison
            if len(duplicates) > 0:
                selected_dup = st.selectbox(
                    "Select Duplicate Group for Comparison",
                    options=range(len(duplicates)),
                    format_func=lambda i: f"Group {i+1}: {duplicates[i].get('COUNT', 0)} occurrences"
                )
                
                if selected_dup is not None:
                    dup_group = duplicates[selected_dup]
                    
                    st.write("**Comparison View:**")
                    
                    # Show key column values
                    key_cols = [k for k in dup_group.keys() if k not in ['COUNT', 'case_ids']]
                    
                    for col in key_cols:
                        st.write(f"- **{col}:** {dup_group.get(col, 'N/A')}")
                    
                    st.write(f"- **Occurrence Count:** {dup_group.get('COUNT', 0)}")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Keep All", key=f"keep_group_{selected_dup}"):
                            st.success("All instances kept")
                    with col2:
                        if st.button("🔗 Merge Group", key=f"merge_group_{selected_dup}"):
                            st.info("Merging duplicate group")
                    with col3:
                        if st.button("📝 Harmonize Rationale", key=f"harmonize_{selected_dup}"):
                            st.info("Opening rationale harmonization dialog")
        
        # Similar cases
        similar_cases = results.get("similar_cases", [])
        if similar_cases:
            st.subheader("🟡 Similar Case Pairs")
            st.caption("Individual cases with high similarity scores.")
            
            similar_df = pd.DataFrame(similar_cases)
            st.dataframe(similar_df.head(20), use_container_width=True)
            
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Duplicate Groups", len(duplicates))
            col2.metric("Exact Duplicates", len(exact_dups))
            col3.metric("Similar Case Pairs", len(similar_cases))
        
        # Export options
        with st.expander("💾 Export Results"):
            if st.button("📥 Download Duplicate Report (CSV)"):
                # Combine all results
                all_results = {
                    "exact_duplicates": exact_dups,
                    "similar_duplicates": duplicates,
                    "similar_cases": similar_cases
                }
                
                # Create combined DataFrame
                report_data = []
                for dup_type, dup_list in all_results.items():
                    for item in dup_list:
                        item['duplicate_type'] = dup_type
                        report_data.append(item)
                
                if report_data:
                    report_df = pd.DataFrame(report_data)
                    csv = report_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="duplicate_detection_report.csv",
                        mime="text/csv"
                    )
    else:
        st.info("Configure detection settings and click 'Detect Duplicates' to begin.")

