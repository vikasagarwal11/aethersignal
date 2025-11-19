"""
Helper functions for AetherSignal app.
Extracted from app.py for better modularity.
"""

import json
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Set

import pandas as pd
import streamlit as st

import faers_loader
import pv_schema
import signal_stats
from utils import normalize_text


def initialize_session():
    """Initialize session state with default values."""
    DEFAULT_SESSION_KEYS = {
        "data": None,
        "schema_mapping": {},
        "normalized_data": None,
        "last_filters": None,
        "last_query_text": "",
        "last_query_source": None,
        "quantum_enabled": False,
        "show_results": False,
        "query_history": [],
        "analytics_enabled": True,
    }

    for key, default in DEFAULT_SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def load_all_files(uploaded_files) -> Optional[pd.DataFrame]:
    """
    Best-effort loader: tries FAERS helpers, PDF extraction, and CSV/Excel.
    """
    if not uploaded_files:
        return None

    frames: List[pd.DataFrame] = []
    processed_files: Set[int] = set()

    def _reset_file_pointer(file_obj):
        try:
            file_obj.seek(0)
        except Exception:
            pass

    # 1) Try FAERS ZIP / ASCII detection via faers_loader
    faers_like_files = [f for f in uploaded_files if f.name.lower().endswith((".zip", ".txt"))]
    if faers_like_files:
        for f in faers_like_files:
            try:
                if f.name.lower().endswith(".zip"):
                    df = faers_loader.load_faers_zip(f)
                else:
                    df = faers_loader.load_faers_file(f)
                if df is not None and not df.empty:
                    frames.append(df)
                    processed_files.add(id(f))
                    continue
            except Exception:
                pass  # will fall back to generic parsing

    # 2) PDFs via faers_loader.load_pdf_files
    pdf_files = [f for f in uploaded_files if f.name.lower().endswith(".pdf")]
    if pdf_files:
        try:
            pdf_df = faers_loader.load_pdf_files(pdf_files)
            if pdf_df is not None and not pdf_df.empty:
                frames.append(pdf_df)
        except Exception:
            pass

    # 3) CSV / Excel / txt / generic zip
    for file in uploaded_files:
        if id(file) in processed_files:
            continue
        name = file.name.lower()
        if name.endswith(".pdf"):
            continue  # already handled
        try:
            _reset_file_pointer(file)
            if name.endswith(".csv"):
                frames.append(pd.read_csv(file))
            elif name.endswith((".xlsx", ".xls")):
                frames.append(pd.read_excel(file))
            elif name.endswith(".txt"):
                try:
                    frames.append(pd.read_csv(file, sep=","))
                except Exception:
                    # Fallback: whitespace-delimited TXT (e.g., FAERS-like exports)
                    frames.append(pd.read_csv(file, sep=r"\s+"))
            elif name.endswith(".zip"):
                # If not caught by FAERS logic, attempt CSV in zip
                with zipfile.ZipFile(file, "r") as z:
                    for fn in z.namelist():
                        if fn.lower().endswith(".csv"):
                            with z.open(fn) as f:
                                frames.append(pd.read_csv(f))
        except Exception as e:
            st.error(f"Error loading {file.name}: {e}")

    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


@st.cache_data(show_spinner=False)
def cached_detect_and_normalize(raw_df: pd.DataFrame):
    """
    Cached schema detection and normalization.
    """
    mapping = pv_schema.detect_schema(raw_df)
    normalized = pv_schema.normalize_dataframe(raw_df, mapping)
    return mapping, normalized


def format_reaction_with_meddra(reaction: str, meddra_pt: Optional[str] = None) -> str:
    """
    Format reaction term with MedDRA PT for display.
    
    Args:
        reaction: Original reaction term
        meddra_pt: MedDRA Preferred Term (optional)
        
    Returns:
        Formatted string: "Reaction (MedDRA PT: Pyrexia)" or just "Reaction" if no mapping
    """
    if pd.isna(reaction) or not reaction:
        return ""
    
    reaction_str = str(reaction).strip()
    
    # If MedDRA PT exists and is different from original, show both
    if meddra_pt and meddra_pt.strip() and normalize_text(meddra_pt) != normalize_text(reaction_str):
        return f"{reaction_str} (MedDRA PT: {meddra_pt})"
    
    return reaction_str


@st.cache_data(show_spinner=False)
def cached_get_summary_stats(filtered_df: pd.DataFrame, normalized_df: pd.DataFrame):
    """
    Cached summary statistics calculation.
    """
    return signal_stats.get_summary_stats(filtered_df, normalized_df)


def render_filter_chips(filters: Dict):
    """Render small filter chips under the interpreted filter text."""
    chips = []

    if "drug" in filters:
        drug = filters["drug"] if isinstance(filters["drug"], str) else ", ".join(filters["drug"])
        chips.append(f"<span class='filter-chip'>💊 {drug}</span>")

    if "reaction" in filters:
        reaction = (
            filters["reaction"]
            if isinstance(filters["reaction"], str)
            else ", ".join(filters["reaction"])
        )
        chips.append(f"<span class='filter-chip'>⚡ {reaction}</span>")

    if "age_min" in filters or "age_max" in filters:
        if "age_min" in filters and "age_max" in filters:
            label = f"{filters['age_min']}–{filters['age_max']}"
        elif "age_min" in filters:
            label = f"≥{filters['age_min']}"
        else:
            label = f"≤{filters['age_max']}"
        chips.append(f"<span class='filter-chip'>👤 Age {label}</span>")

    if "sex" in filters:
        chips.append(f"<span class='filter-chip'>👥 Sex: {filters['sex']}</span>")

    if "country" in filters:
        chips.append(f"<span class='filter-chip'>🌍 {filters['country']}</span>")

    if filters.get("seriousness"):
        chips.append("<span class='filter-chip'>⚠️ Serious cases only</span>")

    if "date_from" in filters or "date_to" in filters:
        txt = []
        if "date_from" in filters:
            txt.append(f"from {filters['date_from']}")
        if "date_to" in filters:
            txt.append(f"to {filters['date_to']}")
        chips.append(f"<span class='filter-chip'>📅 {' '.join(txt)}</span>")

    if "exclude_reaction" in filters:
        excluded = (
            filters["exclude_reaction"]
            if isinstance(filters["exclude_reaction"], str)
            else ", ".join(filters["exclude_reaction"])
        )
        chips.append(f"<span class='filter-chip'>❌ Excluding: {excluded}</span>")

    if chips:
        st.markdown("".join(chips), unsafe_allow_html=True)

