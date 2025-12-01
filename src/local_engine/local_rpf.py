"""
Local RPF (Risk Prioritization Framework) (CHUNK 7.5.4)
Lightweight local version of Risk Prioritization Framework.
Runs entirely in browser via Pyodide.
"""
import pandas as pd
from typing import Dict, Any, Optional
from .base_local_engine import BaseLocalEngine


class LocalRPF(BaseLocalEngine):
    """
    Local Risk Prioritization Framework engine.
    
    Computes RPF scores based on:
    - Seriousness percentage
    - Frequency percentage
    - Basic risk indicators
    
    Simplified version for local (browser) execution.
    """
    
    def compute_rpf(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute local RPF score.
        
        Simple local RPF version:
        RPF = Serious % × 0.6 + Frequency % × 0.4
        
        Args:
            df: Safety data DataFrame
            
        Returns:
            Dictionary with RPF scores and metrics
        """
        if df is None or df.empty:
            return {
                "serious_pct": 0.0,
                "frequency_pct": 0.0,
                "rpf": 0.0,
                "table": []
            }
        
        try:
            total = len(df)
            
            # Calculate seriousness percentage
            serious_col = self.find_column(df, ["serious", "seriousness", "serious_flag", "serious_cod"])
            serious_pct = 0.0
            
            if serious_col:
                serious_values = df[serious_col]
                if serious_values.dtype == bool:
                    serious_count = int(serious_values.sum())
                elif serious_values.dtype in [int, float]:
                    serious_count = int((serious_values == 1).sum())
                else:
                    serious_count = int(serious_values.astype(str).str.upper().str.contains("Y|1|TRUE|SERIOUS", na=False).sum())
                
                serious_pct = (serious_count / total) * 100 if total > 0 else 0.0
            
            # Calculate frequency percentage
            reaction_col = self.find_column(df, ["reaction", "reaction_pt", "reaction_normalized", "pt"])
            frequency_pct = 0.0
            freq_table = []
            
            if reaction_col:
                freq_counts = df.groupby(reaction_col).size().reset_index(name="COUNTS")
                freq_counts = self.percentage(freq_counts, "COUNTS")
                freq_counts = self.top_n(freq_counts, n=10, col="COUNTS")
                
                frequency_pct = float(freq_counts["PCT"].mean()) if len(freq_counts) > 0 else 0.0
                freq_table = freq_counts.to_dict("records")
            
            # Compute RPF score (weighted combination)
            rpf = (serious_pct * 0.6) + (frequency_pct * 0.4)
            
            # Classify priority
            if rpf >= 70:
                priority = "High"
            elif rpf >= 40:
                priority = "Medium"
            else:
                priority = "Low"
            
            return {
                "serious_pct": round(serious_pct, 2),
                "frequency_pct": round(frequency_pct, 2),
                "rpf": round(rpf, 2),
                "priority": priority,
                "table": freq_table
            }
            
        except Exception as e:
            return {
                "serious_pct": 0.0,
                "frequency_pct": 0.0,
                "rpf": 0.0,
                "priority": "Unknown",
                "table": [],
                "error": str(e)
            }

