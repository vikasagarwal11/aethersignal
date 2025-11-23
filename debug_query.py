"""
Debug script to check why queries aren't matching data.
Run this in Streamlit or as a standalone script to diagnose data issues.
"""

import pandas as pd
import streamlit as st

def debug_data_issues(normalized_df: pd.DataFrame):
    """Check for common data issues that prevent queries from matching."""
    
    st.markdown("## 🔍 Data Diagnostic Report")
    
    # Check 1: Column existence
    st.markdown("### 1. Column Check")
    required_cols = ['drug_name', 'reaction', 'caseid', 'primaryid']
    missing_cols = [col for col in required_cols if col not in normalized_df.columns]
    if missing_cols:
        st.error(f"❌ Missing columns: {missing_cols}")
        st.info(f"Available columns: {list(normalized_df.columns)[:20]}")
    else:
        st.success("✅ All required columns present")
    
    # Check 2: Sample data for DUPIXENT
    st.markdown("### 2. Sample Data Check - DUPIXENT")
    if 'drug_name' in normalized_df.columns:
        dupixent_mask = normalized_df['drug_name'].astype(str).str.contains('DUPIXENT', case=False, na=False)
        dupixent_rows = normalized_df[dupixent_mask]
        st.write(f"**Rows containing 'DUPIXENT':** {len(dupixent_rows)}")
        
        if len(dupixent_rows) > 0:
            st.write("**Sample drug_name values:**")
            sample_drugs = dupixent_rows['drug_name'].head(10).tolist()
            for i, drug in enumerate(sample_drugs, 1):
                st.write(f"{i}. `{drug}`")
            
            # Check reactions for DUPIXENT cases
            if 'reaction' in normalized_df.columns:
                dupixent_reactions = dupixent_rows['reaction'].dropna().head(20)
                st.write("**Reactions in DUPIXENT cases:**")
                for i, reaction in enumerate(dupixent_reactions, 1):
                    st.write(f"{i}. `{reaction}`")
                
                # Check for "Off label use"
                off_label_mask = dupixent_rows['reaction'].astype(str).str.contains('off label', case=False, na=False)
                off_label_count = off_label_mask.sum()
                st.write(f"**DUPIXENT cases with 'Off label use':** {off_label_count}")
                
                if off_label_count > 0:
                    st.write("**Sample matching rows:**")
                    matching = dupixent_rows[off_label_mask].head(5)
                    display_cols = ['caseid', 'primaryid', 'drug_name', 'reaction']
                    available_cols = [c for c in display_cols if c in matching.columns]
                    st.dataframe(matching[available_cols], use_container_width=True)
        else:
            st.warning("⚠️ No rows found containing 'DUPIXENT'")
            st.write("**Top 10 drugs in dataset:**")
            top_drugs = normalized_df['drug_name'].value_counts().head(10)
            st.write(top_drugs)
    
    # Check 3: Sample data for "Off label use"
    st.markdown("### 3. Sample Data Check - 'Off label use'")
    if 'reaction' in normalized_df.columns:
        off_label_mask = normalized_df['reaction'].astype(str).str.contains('off label', case=False, na=False)
        off_label_rows = normalized_df[off_label_mask]
        st.write(f"**Rows containing 'off label':** {len(off_label_rows)}")
        
        if len(off_label_rows) > 0:
            st.write("**Sample reaction values:**")
            sample_reactions = off_label_rows['reaction'].head(10).tolist()
            for i, reaction in enumerate(sample_reactions, 1):
                st.write(f"{i}. `{reaction}`")
            
            # Check drugs for "Off label use" cases
            if 'drug_name' in normalized_df.columns:
                off_label_drugs = off_label_rows['drug_name'].dropna().head(20)
                st.write("**Drugs in 'Off label use' cases:**")
                for i, drug in enumerate(off_label_drugs, 1):
                    st.write(f"{i}. `{drug}`")
        else:
            st.warning("⚠️ No rows found containing 'off label'")
            st.write("**Top 10 reactions in dataset:**")
            top_reactions = normalized_df['reaction'].value_counts().head(10)
            st.write(top_reactions)
    
    # Check 4: Case ID matching
    st.markdown("### 4. Case ID Check")
    if 'caseid' in normalized_df.columns:
        caseid_sample = normalized_df['caseid'].dropna().head(10)
        st.write("**Sample caseid values:**")
        st.write(caseid_sample.tolist())
    
    if 'primaryid' in normalized_df.columns:
        primaryid_sample = normalized_df['primaryid'].dropna().head(10)
        st.write("**Sample primaryid values:**")
        st.write(primaryid_sample.tolist())
    
    # Check 5: Data types
    st.markdown("### 5. Data Type Check")
    if 'drug_name' in normalized_df.columns:
        st.write(f"**drug_name dtype:** {normalized_df['drug_name'].dtype}")
        st.write(f"**Sample values (first 5):** {normalized_df['drug_name'].head().tolist()}")
    
    if 'reaction' in normalized_df.columns:
        st.write(f"**reaction dtype:** {normalized_df['reaction'].dtype}")
        st.write(f"**Sample values (first 5):** {normalized_df['reaction'].head().tolist()}")
    
    # Check 6: Test the actual filter
    st.markdown("### 6. Filter Test")
    from src.signal_stats import apply_filters
    
    test_filters = {
        'drug': 'DUPIXENT',
        'reaction': 'Off label use'
    }
    
    st.write(f"**Testing filters:** {test_filters}")
    filtered = apply_filters(normalized_df, test_filters)
    st.write(f"**Filtered rows:** {len(filtered)}")
    
    if len(filtered) > 0:
        st.success("✅ Filter works! Showing first 5 rows:")
        display_cols = ['caseid', 'primaryid', 'drug_name', 'reaction']
        available_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(filtered[available_cols].head(5), use_container_width=True)
    else:
        st.error("❌ Filter returned 0 rows")
        
        # Try individual filters
        st.write("**Testing drug filter alone:**")
        drug_only = apply_filters(normalized_df, {'drug': 'DUPIXENT'})
        st.write(f"Rows with DUPIXENT: {len(drug_only)}")
        
        st.write("**Testing reaction filter alone:**")
        reaction_only = apply_filters(normalized_df, {'reaction': 'Off label use'})
        st.write(f"Rows with 'Off label use': {len(reaction_only)}")


if __name__ == "__main__":
    # For standalone testing
    import sys
    if len(sys.argv) > 1:
        df_path = sys.argv[1]
        df = pd.read_csv(df_path)
        debug_data_issues(df)
    else:
        print("Usage: python debug_query.py <path_to_normalized_data.csv>")
        print("Or use in Streamlit with: debug_query.debug_data_issues(st.session_state.normalized_data)")

