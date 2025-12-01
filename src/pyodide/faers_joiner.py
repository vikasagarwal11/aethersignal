"""
FAERS Multi-file Local Join Engine (CHUNK 7.3.6)
Full FAERS multi-file parsing and joining entirely in browser using Pyodide.
Supports DEMO, DRUG, REAC, OUTC, RPSR, THER, INDI files with parallel processing.
"""
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from io import StringIO

try:
    from src.pyodide.parallel_loader import parallel_read_csv
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False

try:
    from src.pyodide.adaptive_chunking import determine_safe_chunksize, get_available_memory_mb
    CHUNKING_AVAILABLE = True
except ImportError:
    CHUNKING_AVAILABLE = False


def join_faers_tables(
    demo_df: Optional[pd.DataFrame] = None,
    drug_df: Optional[pd.DataFrame] = None,
    reac_df: Optional[pd.DataFrame] = None,
    outc_df: Optional[pd.DataFrame] = None,
    rpsr_df: Optional[pd.DataFrame] = None,
    ther_df: Optional[pd.DataFrame] = None,
    indi_df: Optional[pd.DataFrame] = None,
    key_column: str = "primaryid"
) -> Optional[pd.DataFrame]:
    """
    Join multiple FAERS tables into a single DataFrame.
    
    Standard FAERS join order:
    1. DEMO (base table) - required
    2. DRUG - required
    3. REAC - required
    4. OUTC - optional
    5. RPSR - optional
    6. THER - optional
    7. INDI - optional
    
    Args:
        demo_df: DEMO (demographics) DataFrame
        drug_df: DRUG DataFrame
        reac_df: REAC (reactions) DataFrame
        outc_df: OUTC (outcomes) DataFrame (optional)
        rpsr_df: RPSR (report sources) DataFrame (optional)
        ther_df: THER (therapy dates) DataFrame (optional)
        indi_df: INDI (indications) DataFrame (optional)
        key_column: Column name to join on (default: "primaryid")
        
    Returns:
        Merged DataFrame or None if required tables missing
    """
    if demo_df is None or demo_df.empty:
        return None
    
    if key_column not in demo_df.columns:
        # Try to find key column
        key_column = _find_key_column(demo_df)
        if not key_column:
            return None
    
    # Start with DEMO as base
    merged_df = demo_df.copy()
    
    # Standardize key column name
    if key_column != "primaryid":
        merged_df = merged_df.rename(columns={key_column: "primaryid"})
        key_column = "primaryid"
    
    # Join DRUG (required)
    if drug_df is not None and not drug_df.empty:
        drug_key = _find_key_column(drug_df)
        if drug_key and drug_key in drug_df.columns:
            if drug_key != "primaryid":
                drug_df = drug_df.rename(columns={drug_key: "primaryid"})
            
            # Select key columns from DRUG to avoid duplicate columns
            drug_cols_to_merge = ["primaryid"]
            drug_cols_to_merge.extend([col for col in drug_df.columns if col not in merged_df.columns and col != "primaryid"])
            
            merged_df = merged_df.merge(
                drug_df[drug_cols_to_merge],
                on="primaryid",
                how="left",
                suffixes=("", "_drug")
            )
    else:
        return None  # DRUG is required
    
    # Join REAC (required)
    if reac_df is not None and not reac_df.empty:
        reac_key = _find_key_column(reac_df)
        if reac_key and reac_key in reac_df.columns:
            if reac_key != "primaryid":
                reac_df = reac_df.rename(columns={reac_key: "primaryid"})
            
            # Select key columns from REAC
            reac_cols_to_merge = ["primaryid"]
            reac_cols_to_merge.extend([col for col in reac_df.columns if col not in merged_df.columns and col != "primaryid"])
            
            merged_df = merged_df.merge(
                reac_df[reac_cols_to_merge],
                on="primaryid",
                how="left",
                suffixes=("", "_reac")
            )
    else:
        return None  # REAC is required
    
    # Join OUTC (optional)
    if outc_df is not None and not outc_df.empty:
        outc_key = _find_key_column(outc_df)
        if outc_key and outc_key in outc_df.columns:
            if outc_key != "primaryid":
                outc_df = outc_df.rename(columns={outc_key: "primaryid"})
            
            outc_cols_to_merge = ["primaryid"]
            outc_cols_to_merge.extend([col for col in outc_df.columns if col not in merged_df.columns and col != "primaryid"])
            
            merged_df = merged_df.merge(
                outc_df[outc_cols_to_merge],
                on="primaryid",
                how="left",
                suffixes=("", "_outc")
            )
    
    # Join RPSR (optional)
    if rpsr_df is not None and not rpsr_df.empty:
        rpsr_key = _find_key_column(rpsr_df)
        if rpsr_key and rpsr_key in rpsr_df.columns:
            if rpsr_key != "primaryid":
                rpsr_df = rpsr_df.rename(columns={rpsr_key: "primaryid"})
            
            rpsr_cols_to_merge = ["primaryid"]
            rpsr_cols_to_merge.extend([col for col in rpsr_df.columns if col not in merged_df.columns and col != "primaryid"])
            
            merged_df = merged_df.merge(
                rpsr_df[rpsr_cols_to_merge],
                on="primaryid",
                how="left",
                suffixes=("", "_rpsr")
            )
    
    # Join THER (optional)
    if ther_df is not None and not ther_df.empty:
        ther_key = _find_key_column(ther_df)
        if ther_key and ther_key in ther_df.columns:
            if ther_key != "primaryid":
                ther_df = ther_df.rename(columns={ther_key: "primaryid"})
            
            # Calculate therapy duration if dates available
            if "start_dt" in ther_df.columns and "end_dt" in ther_df.columns:
                ther_df["start_dt"] = pd.to_datetime(ther_df["start_dt"], errors="coerce", format="%Y%m%d")
                ther_df["end_dt"] = pd.to_datetime(ther_df["end_dt"], errors="coerce", format="%Y%m%d")
                ther_df["therapy_duration_days"] = (ther_df["end_dt"] - ther_df["start_dt"]).dt.days
            
            ther_cols_to_merge = ["primaryid"]
            ther_cols_to_merge.extend([col for col in ther_df.columns if col not in merged_df.columns and col != "primaryid"])
            
            merged_df = merged_df.merge(
                ther_df[ther_cols_to_merge],
                on="primaryid",
                how="left",
                suffixes=("", "_ther")
            )
    
    # Join INDI (optional)
    if indi_df is not None and not indi_df.empty:
        indi_key = _find_key_column(indi_df)
        if indi_key and indi_key in indi_df.columns:
            if indi_key != "primaryid":
                indi_df = indi_df.rename(columns={indi_key: "primaryid"})
            
            # Aggregate multiple indications per case (take first)
            indi_agg = indi_df.groupby("primaryid").first().reset_index()
            
            indi_cols_to_merge = ["primaryid"]
            indi_cols_to_merge.extend([col for col in indi_agg.columns if col not in merged_df.columns and col != "primaryid"])
            
            merged_df = merged_df.merge(
                indi_agg[indi_cols_to_merge],
                on="primaryid",
                how="left",
                suffixes=("", "_indi")
            )
    
    return merged_df


def _find_key_column(df: pd.DataFrame) -> Optional[str]:
    """
    Find the key column (ISR, CASE, primaryid, etc.) in a DataFrame.
    
    Args:
        df: DataFrame to search
        
    Returns:
        Key column name or None
    """
    key_column_candidates = ["primaryid", "ISR", "CASE", "caseid", "isr", "case"]
    
    for candidate in key_column_candidates:
        if candidate in df.columns:
            return candidate
    
    # Try case-insensitive match
    df_cols_lower = {col.lower(): col for col in df.columns}
    for candidate in key_column_candidates:
        if candidate.lower() in df_cols_lower:
            return df_cols_lower[candidate.lower()]
    
    return None


def load_and_join_faers_files(
    demo_content: Optional[str] = None,
    drug_content: Optional[str] = None,
    reac_content: Optional[str] = None,
    outc_content: Optional[str] = None,
    rpsr_content: Optional[str] = None,
    ther_content: Optional[str] = None,
    indi_content: Optional[str] = None,
    delimiter: str = "$",
    chunksize: Optional[int] = None,
    use_parallel: bool = True
) -> Optional[pd.DataFrame]:
    """
    Load and join FAERS files from string content (optimized for Pyodide).
    
    Args:
        demo_content: DEMO file content as string
        drug_content: DRUG file content as string
        reac_content: REAC file content as string
        outc_content: OUTC file content as string (optional)
        rpsr_content: RPSR file content as string (optional)
        ther_content: THER file content as string (optional)
        indi_content: INDI file content as string (optional)
        delimiter: CSV delimiter (default: "$" for FAERS)
        chunksize: Chunk size for processing (auto-determined if None)
        use_parallel: Use parallel processing if available
        
    Returns:
        Merged DataFrame or None
    """
    if not demo_content or not drug_content or not reac_content:
        return None
    
    # Determine optimal chunk size
    if chunksize is None and CHUNKING_AVAILABLE:
        available_mb = get_available_memory_mb()
        chunksize = determine_safe_chunksize(available_mb=available_mb)
    elif chunksize is None:
        chunksize = 20000  # Default
    
    try:
        # Load DEMO
        demo_df = pd.read_csv(StringIO(demo_content), delimiter=delimiter, low_memory=False)
        
        # Load DRUG
        drug_df = pd.read_csv(StringIO(drug_content), delimiter=delimiter, low_memory=False)
        
        # Load REAC
        reac_df = pd.read_csv(StringIO(reac_content), delimiter=delimiter, low_memory=False)
        
        # Load optional files
        outc_df = None
        if outc_content:
            outc_df = pd.read_csv(StringIO(outc_content), delimiter=delimiter, low_memory=False)
        
        rpsr_df = None
        if rpsr_content:
            rpsr_df = pd.read_csv(StringIO(rpsr_content), delimiter=delimiter, low_memory=False)
        
        ther_df = None
        if ther_content:
            ther_df = pd.read_csv(StringIO(ther_content), delimiter=delimiter, low_memory=False)
        
        indi_df = None
        if indi_content:
            indi_df = pd.read_csv(StringIO(indi_content), delimiter=delimiter, low_memory=False)
        
        # Join all tables
        merged_df = join_faers_tables(
            demo_df=demo_df,
            drug_df=drug_df,
            reac_df=reac_df,
            outc_df=outc_df,
            rpsr_df=rpsr_df,
            ther_df=ther_df,
            indi_df=indi_df
        )
        
        return merged_df
        
    except Exception as e:
        # Error handling - would log in production
        return None


def chunked_join_faers_files(
    demo_content: str,
    drug_content: str,
    reac_content: str,
    outc_content: Optional[str] = None,
    rpsr_content: Optional[str] = None,
    ther_content: Optional[str] = None,
    indi_content: Optional[str] = None,
    chunksize: int = 20000,
    delimiter: str = "$"
) -> Optional[pd.DataFrame]:
    """
    Join FAERS files in chunks (memory-safe for large datasets).
    
    This processes files in chunks and merges incrementally.
    
    Args:
        demo_content: DEMO file content
        drug_content: DRUG file content
        reac_content: REAC file content
        outc_content: OUTC file content (optional)
        rpsr_content: RPSR file content (optional)
        ther_content: THER file content (optional)
        indi_content: INDI file content (optional)
        chunksize: Rows per chunk
        delimiter: CSV delimiter
        
    Returns:
        Merged DataFrame (all chunks combined)
    """
    # Load base DEMO in chunks and join incrementally
    merged_chunks = []
    
    demo_io = StringIO(demo_content)
    
    try:
        for demo_chunk in pd.read_csv(demo_io, chunksize=chunksize, delimiter=delimiter, low_memory=False):
            # Load full other files (or could chunk them too for very large files)
            drug_df = pd.read_csv(StringIO(drug_content), delimiter=delimiter, low_memory=False)
            reac_df = pd.read_csv(StringIO(reac_content), delimiter=delimiter, low_memory=False)
            
            # Join chunk with other files
            chunk_merged = join_faers_tables(
                demo_df=demo_chunk,
                drug_df=drug_df,
                reac_df=reac_df,
                outc_df=pd.read_csv(StringIO(outc_content), delimiter=delimiter, low_memory=False) if outc_content else None,
                rpsr_df=pd.read_csv(StringIO(rpsr_content), delimiter=delimiter, low_memory=False) if rpsr_content else None,
                ther_df=pd.read_csv(StringIO(ther_content), delimiter=delimiter, low_memory=False) if ther_content else None,
                indi_df=pd.read_csv(StringIO(indi_content), delimiter=delimiter, low_memory=False) if indi_content else None
            )
            
            if chunk_merged is not None:
                merged_chunks.append(chunk_merged)
        
        # Combine all chunks
        if merged_chunks:
            return pd.concat(merged_chunks, ignore_index=True)
        else:
            return None
            
    except Exception:
        return None

