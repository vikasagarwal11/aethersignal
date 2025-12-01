"""
Base Local Engine (CHUNK 7.5.2)
Base class for local (Pyodide) execution.
Provides helper utilities for trend detection, grouping, missing value handling, and lightweight calculations.
"""
import pandas as pd
from typing import Dict, Any, Optional, List


class BaseLocalEngine:
    """
    Base class for local (Pyodide) execution.
    
    Provides helper utilities that work entirely client-side:
    - Grouping and counting
    - Percentage calculations
    - Top-N selections
    - Missing value handling
    - Lightweight statistical operations
    """
    
    @staticmethod
    def group_count(df: pd.DataFrame, col: str, ascending: bool = False) -> pd.DataFrame:
        """
        Group by column and count occurrences.
        
        Args:
            df: DataFrame
            col: Column to group by
            ascending: Sort order
            
        Returns:
            DataFrame with counts
        """
        if df is None or df.empty or col not in df.columns:
            return pd.DataFrame()
        
        result = df.groupby(col).size().reset_index(name="COUNTS")
        result = result.sort_values("COUNTS", ascending=ascending)
        return result
    
    @staticmethod
    def percentage(df: pd.DataFrame, col: str = "COUNTS") -> pd.DataFrame:
        """
        Calculate percentages for counts.
        
        Args:
            df: DataFrame with count column
            col: Column containing counts
            
        Returns:
            DataFrame with added PCT column
        """
        if df is None or df.empty or col not in df.columns:
            return df.copy() if df is not None else pd.DataFrame()
        
        result = df.copy()
        total = result[col].sum()
        
        if total > 0:
            result["PCT"] = (result[col] / total) * 100
        else:
            result["PCT"] = 0.0
        
        return result
    
    @staticmethod
    def top_n(df: pd.DataFrame, n: int = 5, col: str = "COUNTS") -> pd.DataFrame:
        """
        Get top N rows by column.
        
        Args:
            df: DataFrame
            n: Number of rows to return
            col: Column to sort by
            
        Returns:
            Top N rows DataFrame
        """
        if df is None or df.empty:
            return pd.DataFrame()
        
        if col not in df.columns:
            return df.head(n)
        
        return df.sort_values(col, ascending=False).head(n)
    
    @staticmethod
    def find_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
        """
        Find column in DataFrame by keywords.
        
        Args:
            df: DataFrame
            keywords: List of keywords to search for
            
        Returns:
            Column name if found, None otherwise
        """
        if df is None or df.empty:
            return None
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword.lower() in col_lower for keyword in keywords):
                return col
        
        return None
    
    @staticmethod
    def safe_numeric_mean(series: pd.Series) -> float:
        """
        Safely calculate mean of numeric series.
        
        Args:
            series: Pandas Series
            
        Returns:
            Mean value or 0.0 if calculation fails
        """
        try:
            numeric = pd.to_numeric(series, errors="coerce").dropna()
            if len(numeric) > 0:
                return float(numeric.mean())
        except Exception:
            pass
        return 0.0

