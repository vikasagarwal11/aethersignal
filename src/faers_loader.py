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
FAERS_FILES = {
    'DEMO': {
        'filename_pattern': r'DEMO\d{2}[A-Z]\.txt',
        'description': 'Demographics',
        'key_column': 'ISR'  # or 'CASE' depending on format
    },
    'DRUG': {
        'filename_pattern': r'DRUG\d{2}[A-Z]\.txt',
        'description': 'Drug information',
        'key_column': 'ISR'
    },
    'REAC': {
        'filename_pattern': r'REAC\d{2}[A-Z]\.txt',
        'description': 'Reactions/Adverse events',
        'key_column': 'ISR'
    },
    'OUTC': {
        'filename_pattern': r'OUTC\d{2}[A-Z]\.txt',
        'description': 'Patient outcomes',
        'key_column': 'ISR'
    },
    'RPSR': {
        'filename_pattern': r'RPSR\d{2}[A-Z]\.txt',
        'description': 'Report sources',
        'key_column': 'ISR'
    },
    'THER': {
        'filename_pattern': r'THER\d{2}[A-Z]\.txt',
        'description': 'Therapy dates',
        'key_column': 'ISR'
    },
    'INDI': {
        'filename_pattern': r'INDI\d{2}[A-Z]\.txt',
        'description': 'Indications',
        'key_column': 'ISR'
    }
}


def load_faers_folder(folder_path: str) -> Optional[pd.DataFrame]:
    """
    Load FAERS data from a folder containing ASCII files.
    
    Args:
        folder_path: Path to folder containing FAERS ASCII files
        
    Returns:
        Combined DataFrame with all FAERS data joined on CASE/ISR
    """
    files_found = {}
    folder = Path(folder_path)
    
    # Find all FAERS files
    for file_type, config in FAERS_FILES.items():
        pattern = re.compile(config['filename_pattern'], re.IGNORECASE)
        for file_path in folder.glob('*.txt'):
            if pattern.match(file_path.name):
                files_found[file_type] = file_path
                break
    
    if not files_found:
        return None
    
    # Load DEMO first (base table)
    if 'DEMO' not in files_found:
        return None
    
    demo_df = load_faers_file(files_found['DEMO'], 'DEMO')
    if demo_df is None or len(demo_df) == 0:
        return None
    
    # Determine the key column (ISR or CASE)
    key_column = 'ISR'
    if 'ISR' not in demo_df.columns and 'CASE' in demo_df.columns:
        key_column = 'CASE'
    elif 'ISR' not in demo_df.columns and 'caseid' in demo_df.columns:
        key_column = 'caseid'
    
    if key_column not in demo_df.columns:
        return None
    
    # Start with DEMO
    combined_df = demo_df.copy()
    
    # Join other files
    for file_type in ['DRUG', 'REAC', 'OUTC', 'THER', 'INDI', 'RPSR']:
        if file_type in files_found:
            df = load_faers_file(files_found[file_type], file_type)
            if df is not None and len(df) > 0 and key_column in df.columns:
                # For files that can have multiple rows per case, we'll aggregate
                if file_type == 'DRUG':
                    # Aggregate drug names
                    drug_agg = df.groupby(key_column).agg({
                        'drug': lambda x: '; '.join(str(v) for v in x.dropna().unique()),
                        'drug_seq': 'count'
                    }).reset_index()
                    drug_agg.columns = [key_column, 'drug_name', 'drug_count']
                    combined_df = combined_df.merge(drug_agg, on=key_column, how='left')
                elif file_type == 'REAC':
                    # Aggregate reactions
                    reac_agg = df.groupby(key_column).agg({
                        'pt': lambda x: '; '.join(str(v) for v in x.dropna().unique()),
                        'drug_seq': 'count'
                    }).reset_index()
                    reac_agg.columns = [key_column, 'reaction', 'reaction_count']
                    combined_df = combined_df.merge(reac_agg, on=key_column, how='left')
                elif file_type == 'OUTC':
                    # Take first outcome per case
                    outcome_df = df.groupby(key_column).first().reset_index()
                    combined_df = combined_df.merge(outcome_df, on=key_column, how='left', suffixes=('', '_outc'))
                else:
                    # For other files, merge on first occurrence
                    other_df = df.groupby(key_column).first().reset_index()
                    combined_df = combined_df.merge(other_df, on=key_column, how='left', suffixes=('', f'_{file_type.lower()}'))
    
    return combined_df


def load_faers_file(file_path: Path, file_type: str) -> Optional[pd.DataFrame]:
    """
    Load a single FAERS ASCII file.
    
    Args:
        file_path: Path to the FAERS file
        file_type: Type of FAERS file (DEMO, DRUG, REAC, etc.)
        
    Returns:
        DataFrame with the file data
    """
    try:
        df = _read_with_delimiters(file_path, ['|', '$'])
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Standardize key column names
        if 'ISR' in df.columns:
            df.rename(columns={'ISR': 'ISR'}, inplace=True)
        elif 'CASE' in df.columns:
            df.rename(columns={'CASE': 'ISR'}, inplace=True)
        elif 'caseid' in df.columns:
            df.rename(columns={'caseid': 'ISR'}, inplace=True)
        
        return df
    except Exception:
        return None


def _read_with_delimiters(file_path: Path, delimiters: List[str]) -> pd.DataFrame:
    """
    Attempt to read a FAERS file with a prioritized list of delimiters.
    """
    last_error = None
    for sep in delimiters:
        try:
            df = pd.read_csv(file_path, sep=sep, low_memory=False, encoding='latin-1')
            return df
        except Exception as exc:
            last_error = exc
            continue
    # Fall back to pandas delimiter inference if explicit delimiters fail
    try:
        return pd.read_csv(file_path, low_memory=False, encoding='latin-1')
    except Exception:
        if last_error:
            raise last_error
        raise


def load_faers_zip(zip_path: str) -> Optional[pd.DataFrame]:
    """
    Load FAERS data from a ZIP file containing ASCII files.
    
    Args:
        zip_path: Path to ZIP file
        
    Returns:
        Combined DataFrame with all FAERS data joined on CASE/ISR
    """
    import tempfile
    import shutil
    
    temp_dir = None
    try:
        # Extract to temporary directory
        temp_dir = tempfile.mkdtemp()
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp_dir)
        
        return load_faers_folder(temp_dir)
    except Exception as e:
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

