"""
FAERS Data Loader for AetherSignal
Handles the 7 standard FAERS ASCII files and joins them on CASE id.
Also supports PDF files via pdfplumber with regex fallback.
"""

import pandas as pd
import zipfile
import os
from typing import Dict, List, Optional, Tuple
import re
from pathlib import Path

# Try to import pdfplumber for PDF support
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


# Standard FAERS file types and their expected columns
# Pattern matches: DEMO25Q3.txt, DEMO24Q4.txt, DEMO25Q.txt, etc.
# Format: [TYPE][YY][Q][optional_digit].txt
FAERS_FILES = {
    'DEMO': {
        'filename_pattern': r'DEMO\d{2}[A-Z]\d?\.txt',  # Updated: optional digit after quarter letter
        'description': 'Demographics',
        'key_column': 'ISR'  # or 'CASE' depending on format
    },
    'DRUG': {
        'filename_pattern': r'DRUG\d{2}[A-Z]\d?\.txt',  # Updated: optional digit after quarter letter
        'description': 'Drug information',
        'key_column': 'ISR'
    },
    'REAC': {
        'filename_pattern': r'REAC\d{2}[A-Z]\d?\.txt',  # Updated: optional digit after quarter letter
        'description': 'Reactions/Adverse events',
        'key_column': 'ISR'
    },
    'OUTC': {
        'filename_pattern': r'OUTC\d{2}[A-Z]\d?\.txt',  # Updated: optional digit after quarter letter
        'description': 'Patient outcomes',
        'key_column': 'ISR'
    },
    'RPSR': {
        'filename_pattern': r'RPSR\d{2}[A-Z]\d?\.txt',  # Updated: optional digit after quarter letter
        'description': 'Report sources',
        'key_column': 'ISR'
    },
    'THER': {
        'filename_pattern': r'THER\d{2}[A-Z]\d?\.txt',  # Updated: optional digit after quarter letter
        'description': 'Therapy dates',
        'key_column': 'ISR'
    },
    'INDI': {
        'filename_pattern': r'INDI\d{2}[A-Z]\d?\.txt',  # Updated: optional digit after quarter letter
        'description': 'Indications',
        'key_column': 'ISR'
    }
}

ESSENTIAL_COLUMNS = {
    'isr',
    'case',
    'caseid',
    'drug_name',
    'drug_count',
    'reaction',
    'reaction_count',
    'age',
    'age_yrs',
    'age_years',
    'sex',
    'gender',
    'country',
    'serious',
    'seriousness',
    'onset_date',
    'event_date',
    'report_date',
    'receive_date',
    'outcome',
    'outc_cod',
}

LOAD_WARNINGS: List[str] = []


def get_loader_warnings() -> List[str]:
    return LOAD_WARNINGS.copy()


def clear_loader_warnings() -> None:
    LOAD_WARNINGS.clear()


def _record_warning(message: str) -> None:
    LOAD_WARNINGS.append(message)
    try:
        import streamlit as st
        st.warning(message)
    except Exception:
        pass

def load_faers_folder(folder_path: str, progress_callback=None) -> Optional[pd.DataFrame]:
    """
    Load FAERS data from a folder containing ASCII files.
    Supports nested folder structures (e.g., ASCII/ subfolder).
    
    Args:
        folder_path: Path to folder containing FAERS ASCII files
        progress_callback: Optional callback function(step_name, progress_percent, file_num, total_files)
        
    Returns:
        Combined DataFrame with all FAERS data joined on CASE/ISR
    """
    files_found = {}
    folder = Path(folder_path)
    
    # Find all FAERS files (recursively search subfolders)
    for file_type, config in FAERS_FILES.items():
        pattern = re.compile(config['filename_pattern'], re.IGNORECASE)
        # Use rglob for recursive search (handles nested folders like ASCII/)
        for file_path in folder.rglob('*.txt'):
            if pattern.match(file_path.name):
                files_found[file_type] = file_path
                break
    
    if not files_found:
        return None
    
    # Load DEMO first (base table)
    if 'DEMO' not in files_found:
        _record_warning(
            "⚠️ **DEMO file not found** in FAERS data.\n\n"
            f"**Files found:** {', '.join([Path(f).name for f in files_found.values()][:5])}{'...' if len(files_found) > 5 else ''}\n\n"
            "The DEMO file (e.g., `DEMO25Q3.txt`) is required to join the dataset."
        )
        return None
    
    total_files = len(files_found)
    files_processed = 0
    
    # Report progress: Finding files
    if progress_callback:
        progress_callback("Scanning for FAERS files...", 5, 0, total_files)
    
    demo_df = None
    demo_error = None
    try:
        # Report progress: Loading DEMO
        if progress_callback:
            progress_callback(f"Reading DEMO file ({Path(files_found['DEMO']).name})...", 10, files_processed, total_files)
        demo_df = load_faers_file(files_found['DEMO'], 'DEMO')
        files_processed += 1
    except Exception as e:
        demo_error = str(e)
    
    if demo_df is None or len(demo_df) == 0:
        import streamlit as st
        demo_file = files_found.get('DEMO', 'Not found')
        error_msg = (
            f"❌ **Could not parse DEMO file**: `{Path(demo_file).name if demo_file else 'Not found'}`\n\n"
            f"**This could mean:**\n"
            f"- The file format is incorrect (expected pipe-delimited `|` or dollar-delimited `$`)\n"
            f"- The file encoding is not compatible (tried: latin-1, cp1252, iso-8859-1, utf-8)\n"
            f"- The file is corrupted or empty\n\n"
        )
        
        if demo_error:
            error_msg += f"**Error details:**\n"
            error_msg += f"```\n{demo_error[:500]}\n```\n\n"
        
        error_msg += f"**Files found in folder:** {len(files_found)} file(s): {', '.join([Path(f).name for f in files_found.values()][:5])}{'...' if len(files_found) > 5 else ''}"
        
        st.error(error_msg)
        return None
    
    # Determine the key column (primaryid, caseid, ISR, or CASE)
    # FAERS 2024+ uses primaryid/caseid, older files use ISR/CASE
    # Prefer caseid over primaryid for joins (caseid is more commonly used)
    key_column = None
    for col_name in ['caseid', 'primaryid', 'isr', 'case', 'CASE']:
        if col_name in demo_df.columns:
            key_column = col_name
            break
    
    if key_column is None:
        # Try case-insensitive match (columns are already lowercased)
        for col in demo_df.columns:
            col_lower = col.lower()
            if col_lower in ['caseid', 'primaryid', 'isr', 'case']:
                key_column = col
                break
    
    if key_column is None:
        return None
    
    # Start with DEMO
    combined_df = demo_df.copy()
    
    # Join other files
    file_types = ['DRUG', 'REAC', 'OUTC', 'THER', 'INDI', 'RPSR']
    for idx, file_type in enumerate(file_types):
        if file_type in files_found:
            # Calculate progress: 10% for DEMO, 70% for other files (10% each), 20% for merging
            progress_pct = 10 + int((idx + 1) / len(file_types) * 70)
            
            # Report progress: Loading this file type
            file_name = Path(files_found[file_type]).name
            if progress_callback:
                progress_callback(f"Reading {file_type} file ({file_name})...", progress_pct, files_processed, total_files)
            
            df = load_faers_file(files_found[file_type], file_type)
            if df is not None and len(df) > 0 and key_column in df.columns:
                # For files that can have multiple rows per case, we'll aggregate
                if file_type == 'DRUG':
                    # Aggregate drug names
                    # Check if required columns exist
                    if 'drug' not in df.columns:
                        # Skip if drug column doesn't exist after standardization
                        continue
                    
                    # Aggregate drug names and count rows
                    # Don't try to use drug_seq in aggregation - just count rows directly
                    drug_agg = df.groupby(key_column).agg({
                        'drug': lambda x: '; '.join(str(v) for v in x.dropna().unique())
                    }).reset_index()
                    
                    # Add count column (size of each group) - this always works
                    drug_agg['drug_count'] = df.groupby(key_column).size().values
                    drug_agg.columns = [key_column, 'drug_name', 'drug_count']
                    
                    combined_df = combined_df.merge(drug_agg, on=key_column, how='left')
                    files_processed += 1
                elif file_type == 'REAC':
                    # Aggregate reactions
                    # REAC file has NO drug_seq column - just count rows directly
                    if 'pt' not in df.columns:
                        continue
                    
                    # Count rows per case and aggregate reactions
                    reac_agg = df.groupby(key_column).agg({
                        'pt': lambda x: '; '.join(str(v) for v in x.dropna().unique())
                    }).reset_index()
                    
                    # Add count column (size of each group)
                    reac_agg['reaction_count'] = df.groupby(key_column).size().values
                    reac_agg.columns = [key_column, 'reaction', 'reaction_count']
                    combined_df = combined_df.merge(reac_agg, on=key_column, how='left')
                    files_processed += 1
                elif file_type == 'OUTC':
                    # Take first outcome per case
                    outcome_df = df.groupby(key_column).first().reset_index()
                    combined_df = combined_df.merge(outcome_df, on=key_column, how='left', suffixes=('', '_outc'))
                    files_processed += 1
                else:
                    # For other files, merge on first occurrence
                    other_df = df.groupby(key_column).first().reset_index()
                    combined_df = combined_df.merge(other_df, on=key_column, how='left', suffixes=('', f'_{file_type.lower()}'))
                    files_processed += 1
    
    # Report progress: Merging files
    if progress_callback:
        progress_callback("Merging all FAERS files...", 85, files_processed, total_files)
    
    # Report progress: Finalizing
    if progress_callback:
        progress_callback("Finalizing dataset...", 95, files_processed, total_files)
    
    result = _trim_to_essential_columns(combined_df, key_column)
    
    # Report progress: Complete
    if progress_callback:
        progress_callback("Processing complete!", 100, files_processed, total_files)
    
    return result


def load_faers_file(file_path, file_type: str) -> Optional[pd.DataFrame]:
    """
    Load a single FAERS ASCII file.
    
    Args:
        file_path: Path to the FAERS file (Path object or string)
        file_type: Type of FAERS file (DEMO, DRUG, REAC, etc.)
        
    Returns:
        DataFrame with the file data, or None if loading fails
        
    Raises:
        Exception: If file cannot be read (to allow caller to see detailed error)
    """
    # Convert to Path if needed
    if isinstance(file_path, str):
        file_path = Path(file_path)
    elif not isinstance(file_path, Path):
        file_path = Path(str(file_path))
    
    try:
        # FAERS files use $ delimiter (not |)
        # Try $ first since that's the standard FAERS format
        df = _read_with_delimiters(file_path, ['$', '|'])
        
        if df is None or len(df) == 0:
            return None
        
        # Clean column names (lowercase everything for consistency)
        df.columns = df.columns.str.strip().str.lower()
        _standardize_faers_columns(df, file_type)
        
        # Standardize key column names - preserve primaryid/caseid for newer format
        # Don't rename if primaryid or caseid exist (newer FAERS format)
        # Only standardize if we have ISR/CASE (older format)
        if 'primaryid' in df.columns and 'caseid' in df.columns:
            # Use caseid as the standard key (primaryid is also available)
            pass  # Keep both, use caseid for joins
        elif 'caseid' in df.columns:
            pass  # Keep caseid as key
        elif 'primaryid' in df.columns:
            pass  # Keep primaryid as key
        elif 'isr' in df.columns:
            # Older format - standardize to uppercase ISR
            df.rename(columns={'isr': 'ISR'}, inplace=True)
        elif 'case' in df.columns:
            # Older format - rename to ISR for consistency
            df.rename(columns={'case': 'ISR'}, inplace=True)
        
        return df
    except Exception as e:
        # Log error for debugging, but also re-raise so caller can see details
        error_msg = str(e)
        _record_warning(
            f"⚠️ **Error loading {file_type} file**: `{file_path.name if hasattr(file_path, 'name') else str(file_path)}` — {error_msg[:150]}{'...' if len(error_msg) > 150 else ''}"
        )
        # Re-raise so caller can see full error details
        raise


def _read_with_delimiters(file_path: Path, delimiters: List[str]) -> pd.DataFrame:
    """
    Attempt to read a FAERS file with a prioritized list of delimiters.
    Handles variable field counts by using on_bad_lines='warn' (pandas >= 1.3)
    or error_bad_lines=False (pandas < 1.3).
    Also tries different encodings if latin-1 fails.
    """
    # Convert to Path if it's a string
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Ensure file exists and is readable
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.stat().st_size == 0:
        raise ValueError(f"File is empty: {file_path}")
    
    # Try to peek at first few lines to detect delimiter
    try:
        with open(file_path, 'rb') as f:
            first_bytes = f.read(1024)
            first_lines = first_bytes.decode('latin-1', errors='ignore').split('\n')[:3]
            
        # Count delimiters in first line
        delimiter_counts = {}
        if first_lines:
            first_line = first_lines[0]
            for delim in delimiters:
                delimiter_counts[delim] = first_line.count(delim)
        
        # Sort delimiters by count (highest first)
        sorted_delimiters = sorted(delimiter_counts.items(), key=lambda x: x[1], reverse=True)
        if sorted_delimiters and sorted_delimiters[0][1] > 0:
            # Prefer delimiter that appears most often
            preferred_delimiter = sorted_delimiters[0][0]
            if preferred_delimiter in delimiters:
                delimiters = [preferred_delimiter] + [d for d in delimiters if d != preferred_delimiter]
    except Exception:
        pass  # If peeking fails, use original order
    
    last_error = None
    last_error_msg = None
    encodings = ['latin-1', 'cp1252', 'iso-8859-1', 'utf-8']
    
    for sep in delimiters:
        for encoding in encodings:
            try:
                read_kwargs = {
                    "sep": sep,
                    "encoding": encoding,
                    "engine": "python",  # python engine tolerates variable columns
                    "quotechar": '"',
                    "escapechar": "\\",
                }
                try:
                    # pandas >= 1.3
                    df = pd.read_csv(file_path, on_bad_lines="warn", **read_kwargs)
                except TypeError:
                    # pandas < 1.3 (fallback params)
                    df = pd.read_csv(
                        file_path,
                        error_bad_lines=False,
                        warn_bad_lines=True,
                        **read_kwargs,
                    )
                
                if df is not None and len(df) > 0:
                    # Verify delimiter actually split columns
                    if df.shape[1] == 1 and sep != '$':
                        first_col = str(df.columns[0])
                        sample_val = str(df.iloc[0, 0]) if len(df) > 0 else ""
                        # If only one column and it contains the other delimiter, try next
                        if '$' in first_col or (sep == '|' and '$' in sample_val):
                            continue
                    # Success - return the dataframe
                    if df.shape[1] > 1:  # Must have multiple columns
                        return df
            except Exception as exc:
                last_error = exc
                last_error_msg = f"Delimiter '{sep}' with encoding '{encoding}': {str(exc)}"
                continue
    
    # Fall back to pandas delimiter inference if explicit delimiters fail
    for encoding in encodings:
        try:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    engine="python",
                    on_bad_lines="warn",
                    quotechar='"',
                    escapechar="\\",
                )
            except TypeError:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    engine="python",
                    error_bad_lines=False,
                    warn_bad_lines=True,
                    quotechar='"',
                    escapechar="\\",
                )
            
            if df is not None and len(df) > 0:
                if df.shape[1] > 1:  # Must have multiple columns
                    return df
        except Exception as exc:
            last_error = exc
            last_error_msg = f"Auto-detect with encoding '{encoding}': {str(exc)}"
            continue
    
    # If all else fails, provide detailed error
    error_details = []
    if last_error_msg:
        error_details.append(f"Last attempt: {last_error_msg}")
    
    # Try to get file info for debugging
    try:
        file_size = file_path.stat().st_size
        error_details.append(f"File size: {file_size:,} bytes")
        
        # Try to read first line
        with open(file_path, 'rb') as f:
            first_bytes = f.read(200)
            first_line = first_bytes.decode('latin-1', errors='ignore').split('\n')[0]
            error_details.append(f"First line preview: {first_line[:100]}...")
            
            # Check what delimiters are present
            found_delimiters = []
            for delim in ['|', '$', '\t', ',']:
                if delim in first_line:
                    count = first_line.count(delim)
                    found_delimiters.append(f"{delim}: {count} occurrences")
            if found_delimiters:
                error_details.append(f"Delimiters in first line: {', '.join(found_delimiters)}")
    except Exception:
        pass
    
    error_msg = f"Could not read file {file_path.name} with any delimiter or encoding"
    if error_details:
        error_msg += f"\nDetails: {'; '.join(error_details)}"
    
    if last_error:
        raise ValueError(error_msg) from last_error
    raise ValueError(error_msg)


def _standardize_faers_columns(df: pd.DataFrame, file_type: str) -> None:
    """
    Normalize FAERS columns to names expected by downstream aggregation.
    """
    def ensure_column(target: str, candidates: List[str]):
        if target in df.columns:
            return
        for candidate in candidates:
            if candidate in df.columns:
                df[target] = df[candidate]
                return
    
    ft = (file_type or "").upper()
    if ft == 'DRUG':
        # DRUG files have: primaryid, caseid, drug_seq, drugname, prod_ai, etc.
        ensure_column('drug', ['drugname', 'medicinalproduct', 'prod_ai', 'drug_name'])
        # drug_seq should already exist in DRUG files - no need to create it
        # If it doesn't exist, we'll use key_column for counting
    elif ft == 'REAC':
        # REAC files have: primaryid, caseid, pt, drug_rec_act (NO drug_seq column!)
        ensure_column('pt', ['preferred_term', 'reaction', 'reaction_pt', 'pt_name'])
        # REAC files do NOT have drug_seq - we'll count rows directly
    elif ft == 'INDI':
        # INDI files have: primaryid, caseid, indi_drug_seq, indi_pt
        ensure_column('indi_pt', ['indication', 'indi_pt', 'indication_pt'])
    elif ft == 'OUTC':
        # OUTC files have: primaryid, caseid, outc_cod
        ensure_column('outc_cod', ['outcome', 'outcome_code', 'outc_cod', 'outcome_cod'])
    elif ft == 'THER':
        # THER files have: primaryid, caseid, dsg_drug_seq, start_dt, end_dt, dur, dur_cod
        # dsg_drug_seq is different from drug_seq - that's OK
        pass
    elif ft == 'RPSR':
        # RPSR files have: primaryid, caseid, rpsr_cod
        ensure_column('rpsr_cod', ['source', 'report_source', 'rpsr_cod', 'rpsr_code'])


def _trim_to_essential_columns(df: pd.DataFrame, key_column: str) -> pd.DataFrame:
    """
    Reduce FAERS dataframe to key analysis columns to save memory.
    """
    essential_lower = {col.lower() for col in ESSENTIAL_COLUMNS}
    keep_cols = []
    for col in df.columns:
        if col == key_column or col.lower() in essential_lower:
            keep_cols.append(col)
    # Always include at least the key column
    if key_column not in keep_cols and key_column in df.columns:
        keep_cols.insert(0, key_column)
    if keep_cols:
        return df[keep_cols].copy()
    return df


def load_faers_zip(zip_path: str, progress_callback=None) -> Optional[pd.DataFrame]:
    """
    Load FAERS data from a ZIP file containing ASCII files.
    Supports nested folder structures (e.g., ASCII/ subfolder).
    
    Args:
        zip_path: Path to ZIP file
        progress_callback: Optional callback function(step_name, progress_percent, file_num, total_files)
        
    Returns:
        Combined DataFrame with all FAERS data joined on CASE/ISR
    """
    import tempfile
    import shutil
    
    temp_dir = None
    try:
        # Report progress: Checking ZIP
        if progress_callback:
            progress_callback("Checking ZIP archive...", 2, 0, 1)
        
        # Check ZIP contents first
        with zipfile.ZipFile(zip_path, 'r') as z:
            zip_contents = z.namelist()
            
            # Check for XML files
            xml_files = [fn for fn in zip_contents if fn.lower().endswith('.xml')]
            if xml_files:
                # Return None - XML not supported (error will be shown by caller)
                return None
            
            # Check for expected FAERS ASCII files (can be in subfolders like ASCII/)
            txt_files = [fn for fn in zip_contents if fn.lower().endswith('.txt')]
            if not txt_files:
                # No .txt files found - might be wrong format
                return None
        
        # Report progress: Extracting ZIP
        if progress_callback:
            progress_callback("Extracting ZIP archive...", 5, 0, 1)
        
        # Extract to temporary directory
        temp_dir = tempfile.mkdtemp()
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp_dir)
        
        # Report progress: Processing FAERS files (delegate to load_faers_folder for detailed progress)
        if progress_callback:
            # Create a wrapper callback that adjusts progress percentage
            def wrapper_callback(step_name, progress_pct, file_num, total_files):
                # Adjust progress: 5% for extraction, 90% for file processing, 5% buffer
                adjusted_pct = 5 + int(progress_pct * 0.90)
                progress_callback(step_name, adjusted_pct, file_num, total_files)
            
            faers_progress_callback = wrapper_callback
        else:
            faers_progress_callback = None
        
        # load_faers_folder now uses rglob to search recursively
        result = load_faers_folder(temp_dir, progress_callback=faers_progress_callback)
        
        if result is None or len(result) == 0:
            txt_files_in_zip = [f for f in zip_contents if f.lower().endswith('.txt')]
            _record_warning(
                "⚠️ **Could not parse FAERS files from ZIP**:\n"
                f"- Found {len(txt_files_in_zip)} .txt file(s) in ZIP\n"
                f"- Files: {', '.join([Path(f).name for f in txt_files_in_zip[:5]])}{'...' if len(txt_files_in_zip) > 5 else ''}\n"
                "- Files may be nested inside folders or use unexpected formats."
            )
        
        return result
    except Exception as e:
        import streamlit as st
        import traceback
        _record_warning(f"❌ Error loading FAERS ZIP: {str(e)}")
        st.error(f"❌ Error loading FAERS ZIP: {str(e)}\n\n```{traceback.format_exc()[:200]}```")
        return None
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def load_pdf_files(pdf_files: List) -> Optional[pd.DataFrame]:
    """
    Load data from PDF files using pdfplumber with regex fallback.
    
    Args:
        pdf_files: List of uploaded PDF file objects
        
    Returns:
        Combined DataFrame with extracted data
    """
    if not PDFPLUMBER_AVAILABLE:
        return None
    
    all_data = []
    
    for pdf_file in pdf_files:
        try:
            # Try pdfplumber first
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    # Try to extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            # First row as header
                            df = pd.DataFrame(table[1:], columns=table[0])
                            all_data.append(df)
                    
                    # If no tables, try regex extraction
                    if not tables:
                        text = page.extract_text()
                        if text:
                            # Try to extract structured data using regex
                            extracted = extract_data_from_text(text)
                            if extracted:
                                all_data.append(pd.DataFrame([extracted]))
        except Exception as e:
            continue
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None


def extract_data_from_text(text: str) -> Optional[Dict]:
    """
    Extract structured data from text using regex patterns.
    
    Args:
        text: Text content from PDF
        
    Returns:
        Dictionary with extracted fields
    """
    extracted = {}
    
    # Common patterns for PV data
    patterns = {
        'case_id': r'(?:case|report|id)[\s:]+([A-Z0-9\-]+)',
        'drug': r'(?:drug|medication|product)[\s:]+([A-Za-z0-9\s\-]+)',
        'reaction': r'(?:reaction|adverse|event|ae)[\s:]+([A-Za-z0-9\s\-]+)',
        'age': r'age[\s:]+(\d+)',
        'sex': r'(?:sex|gender)[\s:]+([MF])',
        'country': r'country[\s:]+([A-Za-z\s]+)',
        'date': r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted[key] = match.group(1).strip()
    
    return extracted if extracted else None


def detect_and_load_faers(uploaded_files: List) -> Optional[pd.DataFrame]:
    """
    Detect and load FAERS data from uploaded files (folder, ZIP, or individual files).
    
    Args:
        uploaded_files: List of uploaded file objects from Streamlit
        
    Returns:
        Combined DataFrame or None
    """
    if not uploaded_files:
        return None
    
    import tempfile
    import shutil
    
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        
        # Check if it's a ZIP file
        zip_files = [f for f in uploaded_files if f.name.lower().endswith('.zip')]
        if zip_files:
            zip_path = os.path.join(temp_dir, zip_files[0].name)
            
            # Write ZIP file to temp directory
            with open(zip_path, 'wb') as f:
                f.write(zip_files[0].getbuffer())
            
            # Try FAERS ZIP first
            result = load_faers_zip(zip_path)
            if result is not None and len(result) > 0:
                return result
            
            # Try extracting and loading as folder
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(temp_dir)
                
                result = load_faers_folder(temp_dir)
                if result is not None and len(result) > 0:
                    return result
            except:
                pass
        
        # Check for individual FAERS ASCII files
        txt_files = [f for f in uploaded_files if f.name.lower().endswith('.txt')]
        if txt_files:
            # Write all text files to temp directory
            for txt_file in txt_files:
                file_path = os.path.join(temp_dir, txt_file.name)
                with open(file_path, 'wb') as f:
                    f.write(txt_file.getbuffer())
            
            result = load_faers_folder(temp_dir)
            if result is not None and len(result) > 0:
                return result
    except Exception as e:
        pass
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    return None

