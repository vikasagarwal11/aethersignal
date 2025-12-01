"""
Local Subgroup Analysis (CHUNK 7.5.5)
Fast local version of subgroup analysis.
Runs entirely in browser via Pyodide.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base_local_engine import BaseLocalEngine


class LocalSubgroupAnalyzer(BaseLocalEngine):
    """
    Local subgroup analysis engine.
    
    Analyzes:
    - Age groups
    - Sex/gender distributions
    - Year-based patterns
    - Geographic patterns (if available)
    
    Fast, lightweight version for browser execution.
    """
    
    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run subgroup analysis.
        
        Args:
            df: Safety data DataFrame
            
        Returns:
            Dictionary with subgroup analysis results
        """
        if df is None or df.empty:
            return {
                "age_groups": {},
                "sex": {},
                "year": {},
                "geographic": {}
            }
        
        try:
            results: Dict[str, Any] = {}
            
            # Age groups
            age_col = self.find_column(df, ["age", "age_yrs", "age_cod", "patient_age"])
            if age_col:
                try:
                    ages = pd.to_numeric(df[age_col], errors="coerce").dropna()
                    if len(ages) > 0:
                        age_bins = [0, 18, 40, 65, 120]
                        age_labels = ["Pediatric (<18)", "Adult (18-40)", "Middle-age (40-65)", "Elderly (≥65)"]
                        age_grouped = pd.cut(ages, bins=age_bins, labels=age_labels, include_lowest=True)
                        age_counts = age_grouped.value_counts().to_dict()
                        results["age_groups"] = {str(k): int(v) for k, v in age_counts.items()}
                        
                        # Age statistics
                        results["age_stats"] = {
                            "mean": float(ages.mean()),
                            "median": float(ages.median()),
                            "min": float(ages.min()),
                            "max": float(ages.max())
                        }
                except Exception:
                    results["age_groups"] = {}
            
            # Sex/Gender distribution
            sex_col = self.find_column(df, ["sex", "gender", "sex_cod", "patient_sex"])
            if sex_col:
                try:
                    sex_counts = df[sex_col].value_counts().to_dict()
                    results["sex"] = {str(k): int(v) for k, v in sex_counts.items()}
                except Exception:
                    results["sex"] = {}
            
            # Year-based patterns
            year_col = self.find_column(df, ["year", "YEAR", "report_dt", "event_date"])
            if year_col:
                try:
                    if "date" in year_col.lower() or "dt" in year_col.lower():
                        df_year = df.copy()
                        df_year["YEAR"] = pd.to_datetime(df_year[year_col], errors="coerce").dt.year
                        year_counts = df_year["YEAR"].value_counts().sort_index().to_dict()
                        results["year"] = {str(k): int(v) for k, v in year_counts.items()}
                    else:
                        year_counts = df[year_col].value_counts().sort_index().to_dict()
                        results["year"] = {str(k): int(v) for k, v in year_counts.items()}
                except Exception:
                    results["year"] = {}
            
            # Geographic patterns (if available)
            country_col = self.find_column(df, ["country", "country_code", "occr_country"])
            if country_col:
                try:
                    country_counts = self.group_count(df, country_col)
                    country_counts = self.top_n(country_counts, n=10, col="COUNTS")
                    results["geographic"] = country_counts.to_dict("records")
                except Exception:
                    results["geographic"] = []
            else:
                results["geographic"] = []
            
            return results
            
        except Exception as e:
            return {
                "age_groups": {},
                "sex": {},
                "year": {},
                "geographic": {},
                "error": str(e)
            }

