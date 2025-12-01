"""
Local Trend Detection (CHUNK 7.5.3)
Full trend detection running entirely in browser (Pyodide).
Detects year-over-year changes, spikes, and emerging patterns.
"""
import pandas as pd
from typing import Dict, Any, Optional
from .base_local_engine import BaseLocalEngine


class LocalTrendDetector(BaseLocalEngine):
    """
    Local trend detection engine.
    
    Detects:
    - Year-over-year changes
    - Emerging patterns
    - Spikes and anomalies
    - Time-based trends
    
    All running entirely in browser via Pyodide.
    """
    
    def detect_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect trends in safety data.
        
        Args:
            df: Safety data DataFrame
            
        Returns:
            Dictionary with trend analysis results
        """
        if df is None or df.empty:
            return {
                "yearly": pd.DataFrame(),
                "spikes": pd.DataFrame(),
                "top_spikes": pd.DataFrame(),
                "emerging": []
            }
        
        try:
            # Find relevant columns
            year_col = self.find_column(df, ["year", "YEAR", "report_dt", "event_date"])
            drug_col = self.find_column(df, ["drug", "drug_name", "drug_normalized"])
            reaction_col = self.find_column(df, ["reaction", "reaction_pt", "reaction_normalized", "pt"])
            
            if not year_col or not drug_col or not reaction_col:
                return {
                    "yearly": pd.DataFrame(),
                    "spikes": pd.DataFrame(),
                    "top_spikes": pd.DataFrame(),
                    "emerging": []
                }
            
            # Extract year if date column
            df_work = df.copy()
            if "date" in year_col.lower() or "dt" in year_col.lower():
                df_work["YEAR"] = pd.to_datetime(df_work[year_col], errors="coerce").dt.year
                year_col = "YEAR"
            
            df_work = df_work[df_work[year_col].notna()]
            
            if df_work.empty:
                return {
                    "yearly": pd.DataFrame(),
                    "spikes": pd.DataFrame(),
                    "top_spikes": pd.DataFrame(),
                    "emerging": []
                }
            
            # Group by year + drug + reaction
            yearly = df_work.groupby([year_col, drug_col, reaction_col]).size().reset_index(name="COUNTS")
            
            # Compute year-over-year deltas
            yearly_sorted = yearly.sort_values([drug_col, reaction_col, year_col])
            yearly_sorted["YOY_DELTA"] = yearly_sorted.groupby([drug_col, reaction_col])["COUNTS"].diff()
            yearly_sorted["YOY_PCT"] = (
                (yearly_sorted["YOY_DELTA"] / yearly_sorted["COUNTS"].shift(1)) * 100
            ).fillna(0)
            
            # Identify spikes (significant increases)
            spikes = yearly_sorted[
                (yearly_sorted["YOY_DELTA"] > 0) & 
                (yearly_sorted["YOY_PCT"] > 20)  # >20% increase
            ].copy()
            
            # Top spikes by absolute change
            top_spikes = spikes.sort_values("YOY_DELTA", ascending=False).head(10).copy()
            
            # Emerging patterns (consistent growth)
            emerging = []
            for drug in yearly_sorted[drug_col].unique():
                for reaction in yearly_sorted[reaction_col].unique():
                    subset = yearly_sorted[
                        (yearly_sorted[drug_col] == drug) & 
                        (yearly_sorted[reaction_col] == reaction)
                    ]
                    if len(subset) >= 2:
                        # Check if consistently increasing
                        positive_deltas = (subset["YOY_DELTA"] > 0).sum()
                        if positive_deltas >= len(subset) * 0.6:  # 60%+ years show growth
                            emerging.append({
                                "drug": drug,
                                "reaction": reaction,
                                "growth_years": int(positive_deltas),
                                "total_years": len(subset)
                            })
            
            return {
                "yearly": yearly_sorted.to_dict("records")[:50],  # Limit size
                "spikes": spikes.to_dict("records")[:20],
                "top_spikes": top_spikes.to_dict("records"),
                "emerging": emerging[:10]
            }
            
        except Exception as e:
            return {
                "yearly": [],
                "spikes": [],
                "top_spikes": [],
                "emerging": [],
                "error": str(e)
            }

