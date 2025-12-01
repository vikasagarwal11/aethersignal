"""
Dose-Response and Exposure Modeling Engine for Pharmacovigilance (CHUNK 6.11.9)
Provides dose-response curve analysis, exposure normalization, and cumulative risk analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class DoseResponseEngine:
    """
    Dose-response and exposure modeling engine for PV trend detection.
    Analyzes dose-response relationships, exposure-adjusted risks, and cumulative risk patterns.
    """
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column by possible names (case-insensitive)."""
        df_cols_lower = {col.lower(): col for col in df.columns}
        for name in possible_names:
            if name.lower() in df_cols_lower:
                return df_cols_lower[name.lower()]
        return None
    
    def _extract_dose_value(self, dose_str: str) -> Optional[float]:
        """Extract numeric dose value from string (handles units, ranges, etc.)."""
        if pd.isna(dose_str):
            return None
        
        try:
            # Try direct conversion first
            return float(dose_str)
        except (ValueError, TypeError):
            # Try to extract number from string
            import re
            numbers = re.findall(r'\d+\.?\d*', str(dose_str))
            if numbers:
                return float(numbers[0])
            return None

    def compute_dose_response(
        self, 
        df: pd.DataFrame, 
        drug: Optional[str] = None,
        reaction: Optional[str] = None,
        drug_col: str = "drug_name",
        reaction_col: str = "reaction"
    ) -> Optional[Dict[str, Any]]:
        """
        Compute dose-response analysis (CHUNK 6.11.9).
        
        Returns dose buckets, case counts, normalized exposure-adjusted trends,
        and a significance score for dose escalation risk.
        
        Args:
            df: DataFrame with PV data
            drug: Drug name to filter (optional)
            reaction: Reaction name to filter (optional)
            drug_col: Drug column name
            reaction_col: Reaction column name
            
        Returns:
            Dictionary with dose-response analysis results or None if insufficient data
        """
        if df is None or len(df) == 0:
            return None

        filtered = df.copy()
        
        # Filter by drug if specified
        if drug:
            drug_col_actual = self._find_column(filtered, [drug_col, "drug_name", "drug"])
            if drug_col_actual:
                filtered = filtered[
                    filtered[drug_col_actual].astype(str).str.contains(str(drug), na=False, regex=False)
                ]
            else:
                return None
        
        # Filter by reaction if specified
        if reaction:
            reaction_col_actual = self._find_column(filtered, [reaction_col, "reaction", "reaction_pt"])
            if reaction_col_actual:
                filtered = filtered[
                    filtered[reaction_col_actual].astype(str).str.contains(str(reaction), na=False, regex=False)
                ]
            else:
                return None

        if filtered.empty:
            return None

        # Find dose column
        dose_col = self._find_column(filtered, ["dose_mg", "dose_amt", "dose", "dose_amount", "dose_strength"])
        if not dose_col:
            return None
        
        # Clean dose - extract numeric values
        filtered = filtered.copy()
        dose_series = filtered[dose_col].apply(self._extract_dose_value)
        filtered["dose_numeric"] = dose_series
        
        # Filter out invalid doses
        filtered = filtered[filtered["dose_numeric"].notna() & (filtered["dose_numeric"] > 0)]
        
        if filtered.empty:
            return None

        # Bucket doses (adaptive bins based on data range)
        max_dose = filtered["dose_numeric"].max()
        min_dose = filtered["dose_numeric"].min()
        
        # Use adaptive binning based on data range
        if max_dose <= 100:
            bins = [-1, 25, 50, 75, 100, 10000]
            labels = ["≤25mg", "26-50mg", "51-75mg", "76-100mg", "100mg+"]
        elif max_dose <= 300:
            bins = [-1, 50, 100, 150, 200, 300, 10000]
            labels = ["≤50mg", "51-100mg", "101-150mg", "151-200mg", "201-300mg", "300mg+"]
        else:
            bins = [-1, 50, 150, 300, 450, 600, 10000]
            labels = ["≤50mg", "51-150mg", "151-300mg", "301-450mg", "451-600mg", "600mg+"]

        try:
            filtered["dose_bucket"] = pd.cut(
                filtered["dose_numeric"], 
                bins=bins, 
                labels=labels,
                include_lowest=True
            )
        except Exception:
            return None

        # Count per dose bucket
        dose_counts_series = filtered.groupby("dose_bucket").size()
        dose_counts = {str(k): int(v) for k, v in dose_counts_series.items()}

        # Exposure normalization (proxy: sum of doses per bucket)
        exposure_series = filtered.groupby("dose_bucket")["dose_numeric"].sum()
        exposure = {str(k): float(v) for k, v in exposure_series.items()}

        # Exposure-adjusted rates (cases per unit exposure)
        exposure_adjusted = {}
        for bucket in labels:
            bucket_str = str(bucket)
            count = dose_counts.get(bucket_str, 0)
            exp = exposure.get(bucket_str, 1.0)
            if exp > 0:
                exposure_adjusted[bucket_str] = count / exp
            else:
                exposure_adjusted[bucket_str] = 0.0

        # Significance score: highest dose rate / lowest dose rate
        non_zero_rates = [v for v in exposure_adjusted.values() if v > 0]
        if len(non_zero_rates) > 1:
            significance = max(non_zero_rates) / (min(non_zero_rates) + 1e-6)
        else:
            significance = 1.0

        # Dose-response trend (positive if increasing)
        sorted_buckets = sorted([k for k in exposure_adjusted.keys() if exposure_adjusted[k] > 0])
        if len(sorted_buckets) >= 2:
            first_rate = exposure_adjusted[sorted_buckets[0]]
            last_rate = exposure_adjusted[sorted_buckets[-1]]
            trend_direction = "increasing" if last_rate > first_rate * 1.2 else "decreasing" if last_rate < first_rate * 0.8 else "stable"
        else:
            trend_direction = "insufficient_data"

        return {
            "dose_counts": dose_counts,
            "exposure_adjusted": exposure_adjusted,
            "significance": float(significance),
            "dose_order": [str(l) for l in labels],
            "trend_direction": trend_direction,
            "total_cases": int(len(filtered)),
            "dose_range": {"min": float(min_dose), "max": float(max_dose)}
        }

    def compute_cumulative_risk(
        self, 
        df: pd.DataFrame, 
        drug: Optional[str] = None,
        reaction: Optional[str] = None,
        date_col: Optional[str] = None,
        drug_col: str = "drug_name",
        reaction_col: str = "reaction"
    ) -> Optional[Dict[str, Any]]:
        """
        Compute cumulative risk over time (CHUNK 6.11.9).
        
        Args:
            df: DataFrame with PV data
            drug: Drug name to filter (optional)
            reaction: Reaction name to filter (optional)
            date_col: Date column name (auto-detected if None)
            drug_col: Drug column name
            reaction_col: Reaction column name
            
        Returns:
            Dictionary with cumulative risk analysis results or None if insufficient data
        """
        if df is None or len(df) == 0:
            return None

        filtered = df.copy()
        
        # Filter by drug if specified
        if drug:
            drug_col_actual = self._find_column(filtered, [drug_col, "drug_name", "drug"])
            if drug_col_actual:
                filtered = filtered[
                    filtered[drug_col_actual].astype(str).str.contains(str(drug), na=False, regex=False)
                ]
            else:
                return None
        
        # Filter by reaction if specified
        if reaction:
            reaction_col_actual = self._find_column(filtered, [reaction_col, "reaction", "reaction_pt"])
            if reaction_col_actual:
                filtered = filtered[
                    filtered[reaction_col_actual].astype(str).str.contains(str(reaction), na=False, regex=False)
                ]
            else:
                return None

        if filtered.empty:
            return None

        # Find date column if not provided
        if date_col is None:
            for col in ["event_date", "report_date", "receipt_date", "receive_date", 
                       "received_date", "onset_date"]:
                if col in filtered.columns:
                    date_col = col
                    break
        
        if not date_col or date_col not in filtered.columns:
            return None

        try:
            filtered = filtered.copy()
            filtered[date_col] = pd.to_datetime(filtered[date_col], errors="coerce")
            filtered = filtered[filtered[date_col].notna()]
            
            if filtered.empty:
                return None
            
            # Group by month
            filtered["event_month"] = filtered[date_col].dt.to_period("M")
            monthly_counts = filtered.groupby("event_month").size().sort_index()
            
            if len(monthly_counts) < 2:
                return None
            
            # Cumulative sum
            cumulative_counts = monthly_counts.cumsum()
            
            # Calculate rate of change (slope)
            if len(monthly_counts) >= 3:
                recent_slope = (monthly_counts.iloc[-3:].mean() - monthly_counts.iloc[:3].mean()) / len(monthly_counts)
            else:
                recent_slope = 0.0
            
            # Convert Period to strings for JSON serialization
            monthly_dict = {str(period): int(count) for period, count in monthly_counts.items()}
            cumulative_dict = {str(period): int(count) for period, count in cumulative_counts.items()}
            
            return {
                "monthly": monthly_dict,
                "cumulative": cumulative_dict,
                "periods": [str(p) for p in monthly_counts.index],
                "total_cases": int(cumulative_counts.iloc[-1]),
                "recent_slope": float(recent_slope),
                "is_increasing": recent_slope > 0
            }
        except Exception:
            return None
