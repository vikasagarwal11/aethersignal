"""
Helper functions for AetherSignal app.
Extracted from app.py for better modularity.
"""

import json
import os
import tempfile
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Set

import pandas as pd
import streamlit as st

from src import faers_loader
from src import pv_schema
from src import signal_stats
from src.utils import normalize_text


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
        "saved_queries": [],
        "loading_in_progress": False,
    }

    for key, default in DEFAULT_SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def load_all_files(uploaded_files, progress_callback=None) -> Optional[pd.DataFrame]:
    """
    Best-effort loader: tries FAERS helpers, PDF extraction, and CSV/Excel.
    
    Args:
        uploaded_files: List of uploaded file objects
        progress_callback: Optional callback function(current_file, total_files, file_name, file_size_bytes)
    """
    if not uploaded_files:
        return None

    frames: List[pd.DataFrame] = []
    processed_files: Set[int] = set()
    total_files = len(uploaded_files)
    current_file = 0
    faers_loader.clear_loader_warnings()

    def _reset_file_pointer(file_obj):
        try:
            file_obj.seek(0)
        except Exception:
            pass

    # 1) Try FAERS ZIP / ASCII detection via faers_loader
    faers_like_files = [f for f in uploaded_files if f.name.lower().endswith((".zip", ".txt"))]
    if faers_like_files:
        for f in faers_like_files:
            current_file += 1
            if progress_callback:
                progress_callback(current_file, total_files, f.name, f.size)
            
            try:
                # Check for XML files in ZIP before attempting to load
                if f.name.lower().endswith(".zip"):
                    # Peek into ZIP to check for XML files
                    _reset_file_pointer(f)
                    try:
                        with zipfile.ZipFile(f, "r") as z:
                            zip_contents = z.namelist()
                            xml_files = [fn for fn in zip_contents if fn.lower().endswith(".xml")]
                            if xml_files:
                                # XML detected - provide specific error
                                st.warning(
                                    f"⚠️ **XML format detected**: The file `{f.name}` contains XML files, which are not currently supported. "
                                    f"Found: {', '.join(xml_files[:3])}{'...' if len(xml_files) > 3 else ''}\n\n"
                                    "**Supported formats:**\n"
                                    "- FAERS ASCII files (DEMO, DRUG, REAC, OUTC, THER, INDI, RPSR as `.txt`)\n"
                                    "- CSV files\n"
                                    "- Excel files (.xlsx, .xls)\n"
                                    "- PDF files (tabular only)\n\n"
                                    "**To use FAERS data:** Download the ASCII format (not XML) from FDA's website."
                                )
                                processed_files.add(id(f))
                                continue  # Skip this file
                    except Exception:
                        pass  # If ZIP check fails, continue to try loading
                    
                    # Try to load as FAERS ZIP
                    # load_faers_zip expects a file path, so we need to write the UploadedFile to temp first
                    _reset_file_pointer(f)
                    temp_zip = None
                    try:
                        # Write UploadedFile to temporary file
                        if progress_callback:
                            progress_callback(current_file, total_files, f"Preparing {f.name}...", f.size)
                        
                        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                        temp_zip.write(f.getbuffer())
                        temp_zip.close()
                        
                        # Create wrapper callback for FAERS loader
                        def faers_progress_wrapper(step_name, step_progress, file_num, total_internal_files):
                            # Map internal progress to overall file progress
                            # For ZIP files, we show step-level progress
                            if progress_callback:
                                # Use a more detailed message format
                                detailed_msg = f"{f.name}: {step_name}"
                                # Calculate overall progress: current_file is started, step_progress is internal
                                overall_progress = ((current_file - 1) / total_files) + (step_progress / 100 / total_files)
                                # Update callback with step info
                                progress_callback(
                                    current_file, 
                                    total_files, 
                                    detailed_msg, 
                                    f.size,
                                    step_info={
                                        'step': step_name,
                                        'step_progress': step_progress,
                                        'internal_file': file_num,
                                        'total_internal': total_internal_files
                                    }
                                )
                        
                        df = faers_loader.load_faers_zip(temp_zip.name, progress_callback=faers_progress_wrapper)
                    except Exception:
                        df = None
                    finally:
                        if temp_zip and os.path.exists(temp_zip.name):
                            try:
                                os.unlink(temp_zip.name)
                            except:
                                pass
                else:
                    # For individual .txt files, write to temp file first (load_faers_file expects Path)
                    _reset_file_pointer(f)
                    temp_txt = None
                    try:
                        temp_txt = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
                        temp_txt.write(f.getbuffer())
                        temp_txt.close()
                        df = faers_loader.load_faers_file(temp_txt.name)
                    except Exception as e:
                        df = None
                        # Show detailed error for individual files
                        st.error(f"❌ Error loading FAERS file `{f.name}`: {str(e)[:300]}")
                    finally:
                        if temp_txt and os.path.exists(temp_txt.name):
                            try:
                                os.unlink(temp_txt.name)
                            except:
                                pass
                
                if df is not None and not df.empty:
                    frames.append(df)
                    processed_files.add(id(f))
                    continue
                else:
                    # File was processed but returned None or empty - log it
                    if f.name.lower().endswith(".zip"):
                        st.warning(f"⚠️ Could not parse FAERS data from `{f.name}`. Check if it contains valid FAERS ASCII files.")
            except Exception as e:
                # Log the error for debugging
                import traceback
                error_msg = str(e)
                if "xml" in error_msg.lower() or "xml" in f.name.lower():
                    st.warning(f"⚠️ XML format detected in `{f.name}`. XML files are not supported. Please use FAERS ASCII format (.txt files).")
                else:
                    # Show actual error for debugging
                    st.error(f"❌ Error loading `{f.name}`: {error_msg[:200]}")
                pass  # will fall back to generic parsing

    # 2) PDFs via faers_loader.load_pdf_files
    pdf_files = [f for f in uploaded_files if f.name.lower().endswith(".pdf") and id(f) not in processed_files]
    if pdf_files:
        # Track progress for all PDF files at once
        for f in pdf_files:
            current_file += 1
            if progress_callback:
                progress_callback(current_file, total_files, f.name, f.size)
            processed_files.add(id(f))
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
        
        current_file += 1
        if progress_callback:
            progress_callback(current_file, total_files, file.name, file.size)
        
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
            error_msg = str(e)
            # Only show error for files that couldn't be processed at all
            # (skip warnings for files that were already processed by FAERS loader)
            if id(file) not in processed_files:
                # Truncate long error messages
                if len(error_msg) > 200:
                    error_msg = error_msg[:200] + "..."
                st.error(f"❌ Error loading {file.name}: {error_msg}")

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
