"""
Manual Schema Mapping UI Component
Allows users to manually map their column names to standard PV fields for multi-vendor support.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple
from src import pv_schema
from src import mapping_templates
from difflib import SequenceMatcher


def render_schema_mapper(raw_df: pd.DataFrame, detected_mapping: Dict[str, str]) -> Optional[Dict[str, str]]:
    """
    Render UI for manual schema mapping.
    
    Args:
        raw_df: Original DataFrame with actual column names
        detected_mapping: Auto-detected mapping from pv_schema.detect_schema()
        
    Returns:
        Final mapping dictionary (user-corrected or auto-detected), or None if cancelled
    """
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.markdown("### 🔧 Column Mapping Configuration")
    st.caption(
        "Auto-detection found some columns, but you can manually adjust the mapping below. "
        "This ensures your data structure is correctly interpreted."
    )
    
    # Standard PV fields with descriptions
    STANDARD_FIELDS_INFO = {
        'case_id': {
            'label': 'Case/Report ID',
            'required': True,
            'description': 'Unique identifier for each case (e.g., ISR, primaryid, caseid)'
        },
        'drug_name': {
            'label': 'Drug Name',
            'required': True,
            'description': 'Name of the drug/medication (e.g., drug, medication, product)'
        },
        'reaction': {
            'label': 'Adverse Reaction',
            'required': True,
            'description': 'Adverse event/reaction (e.g., reaction, adverse_event, PT)'
        },
        'age': {
            'label': 'Patient Age',
            'required': False,
            'description': 'Patient age in years'
        },
        'sex': {
            'label': 'Gender/Sex',
            'required': False,
            'description': 'Patient gender (M/F)'
        },
        'country': {
            'label': 'Country',
            'required': False,
            'description': 'Country code or name'
        },
        'seriousness': {
            'label': 'Seriousness Flag',
            'required': False,
            'description': 'Whether case is serious (True/False, Y/N, etc.)'
        },
        'onset_date': {
            'label': 'Onset Date',
            'required': False,
            'description': 'Date when adverse event started'
        },
        'report_date': {
            'label': 'Report Date',
            'required': False,
            'description': 'Date when report was received'
        },
        'outcome': {
            'label': 'Outcome',
            'required': False,
            'description': 'Patient outcome (e.g., fatal, recovered, etc.)'
        },
    }
    
    # Get available columns from raw_df
    available_columns = list(raw_df.columns)
    
    # Create manual mapping
    manual_mapping = {}
    
    # Show all standard fields
    st.markdown("#### Map Your Columns to Standard Fields")
    
    # Group by required vs optional
    required_fields = {k: v for k, v in STANDARD_FIELDS_INFO.items() if v['required']}
    optional_fields = {k: v for k, v in STANDARD_FIELDS_INFO.items() if not v['required']}
    
    # Required fields first
    st.markdown("**Required Fields** (at least 2 of 3 needed)")
    for standard_field, info in required_fields.items():
        with st.container():
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"**{info['label']}** {':red[*]' if info['required'] else ''}")
                st.caption(info['description'])
            with col2:
                # Get current mapping or detected mapping
                current_value = detected_mapping.get(standard_field, "")
                
                # Find best matches from available columns
                best_matches = _find_best_column_matches(standard_field, available_columns, raw_df)
                
                # Create selectbox with current value and suggestions
                options = ["(Not mapped)"] + available_columns
                default_idx = 0
                if current_value in available_columns:
                    default_idx = available_columns.index(current_value) + 1
                
                selected = st.selectbox(
                    f"Select column for {standard_field}",
                    options=options,
                    index=default_idx,
                    key=f"schema_map_{standard_field}",
                    label_visibility="collapsed",
                    help=f"Best matches: {', '.join(best_matches[:3]) if best_matches else 'None found'}"
                )
                
                if selected != "(Not mapped)":
                    manual_mapping[standard_field] = selected
                
                # Show similarity score if auto-detected
                if current_value and current_value in available_columns:
                    similarity = _column_similarity_score(current_value, standard_field)
                    if similarity > 0.7:
                        st.caption(f"✓ Auto-detected (similarity: {similarity:.0%})")
                    elif similarity > 0.5:
                        st.caption(f"⚠ Low confidence (similarity: {similarity:.0%})")
    
    # Optional fields in an expander
    with st.expander("📋 Optional Fields (expand to map)", expanded=False):
        for standard_field, info in optional_fields.items():
            with st.container():
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.markdown(f"**{info['label']}**")
                    st.caption(info['description'])
                with col2:
                    current_value = detected_mapping.get(standard_field, "")
                    options = ["(Not mapped)"] + available_columns
                    default_idx = 0
                    if current_value in available_columns:
                        default_idx = available_columns.index(current_value) + 1
                    
                    selected = st.selectbox(
                        f"Select column for {standard_field}",
                        options=options,
                        index=default_idx,
                        key=f"schema_map_{standard_field}",
                        label_visibility="collapsed"
                    )
                    
                    if selected != "(Not mapped)":
                        manual_mapping[standard_field] = selected
    
    # Show column preview
    st.markdown("---")
    st.markdown("#### 📊 Column Preview")
    with st.expander("View available columns and sample data", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Available Columns:**")
            for col in available_columns:
                non_null_count = raw_df[col].notna().sum()
                st.caption(f"• `{col}` ({non_null_count:,} non-null values)")
        with col2:
            st.markdown("**Sample Data (first 3 rows):**")
            st.dataframe(
                raw_df.head(3),
                use_container_width=True,
                hide_index=True
            )
    
    # Validation
    essential_fields = ['case_id', 'drug_name', 'reaction']
    mapped_essential = [f for f in essential_fields if f in manual_mapping]
    
    if len(mapped_essential) < 2:
        st.error(
            f"⚠️ **At least 2 of 3 essential fields must be mapped:**\n"
            f"- Case/Report ID: {'✓' if 'case_id' in manual_mapping else '✗'}\n"
            f"- Drug Name: {'✓' if 'drug_name' in manual_mapping else '✗'}\n"
            f"- Adverse Reaction: {'✓' if 'reaction' in manual_mapping else '✗'}\n\n"
            "Please map the missing fields above to continue."
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return None
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        apply_mapping = st.button("✅ Apply Mapping", type="primary", use_container_width=True)
    with col2:
        use_auto = st.button("🔄 Use Auto-Detected", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if apply_mapping:
        # Validate no duplicate mappings
        mapped_columns = [col for col in manual_mapping.values() if col]
        if len(mapped_columns) != len(set(mapped_columns)):
            st.error("❌ Each column can only be mapped to one field. Please check for duplicates.")
            return None
        
        st.success(f"✅ Mapping applied! {len(manual_mapping)} fields mapped.")
        return manual_mapping
    
    if use_auto:
        st.info("Using auto-detected mapping.")
        return detected_mapping
    
    return None


def _find_best_column_matches(standard_field: str, available_columns: List[str], df: pd.DataFrame) -> List[str]:
    """
    Find best matching columns for a standard field based on name similarity and data content.
    
    Args:
        standard_field: Standard field name (e.g., 'drug_name')
        available_columns: List of available column names
        df: DataFrame to analyze
        
    Returns:
        List of column names sorted by similarity score (best first)
    """
    matches = []
    
    # Get possible names for this standard field
    possible_names = pv_schema.STANDARD_FIELDS.get(standard_field, [])
    
    for col in available_columns:
        score = _column_similarity_score(col, standard_field, possible_names)
        matches.append((col, score))
    
    # Sort by score (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    # Return only columns with reasonable similarity (>0.3)
    return [col for col, score in matches if score > 0.3]


def _column_similarity_score(column_name: str, standard_field: str, possible_names: Optional[List[str]] = None) -> float:
    """
    Calculate similarity score between a column name and a standard field.
    
    Args:
        column_name: Actual column name
        standard_field: Standard field name
        possible_names: Optional list of possible names for the standard field
        
    Returns:
        Similarity score between 0 and 1
    """
    if possible_names is None:
        possible_names = pv_schema.STANDARD_FIELDS.get(standard_field, [])
    
    column_lower = column_name.lower().strip()
    column_norm = column_lower.replace('_', ' ').replace('-', ' ')
    
    best_score = 0.0
    
    # Compare against standard field name itself
    field_norm = standard_field.replace('_', ' ').lower()
    score = SequenceMatcher(None, column_norm, field_norm).ratio()
    best_score = max(best_score, score)
    
    # Compare against possible names
    for possible_name in possible_names:
        possible_norm = possible_name.lower().replace('_', ' ').replace('-', ' ')
        
        # Exact match
        if column_lower == possible_norm or column_lower == possible_name.lower():
            return 1.0
        
        # Sequence match
        score = SequenceMatcher(None, column_norm, possible_norm).ratio()
        best_score = max(best_score, score)
        
        # Substring match (boost score)
        if possible_norm in column_norm or column_norm in possible_norm:
            best_score = max(best_score, min(0.9, best_score + 0.2))
    
    return best_score

