"""
Local Signal Strength Scoring (CHUNK 7.5.6)
Computes signal strength scores locally in browser.
"""
import pandas as pd
from typing import Dict, Any
from .base_local_engine import BaseLocalEngine


class LocalSignalStrength(BaseLocalEngine):
    """
    Local signal strength scoring engine.
    
    Computes signal strength based on:
    - Seriousness percentage
    - Disproportionality
    - Case frequency
    """
    
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute signal strength score.
        
        Score = (Serious % × 0.5) + (Disproportionality × 0.5)
        
        Args:
            df: Safety data DataFrame
            
        Returns:
            Dictionary with signal strength score and components
        """
        if df is None or df.empty:
            return {
                "score": 0.0,
                "serious_pct": 0.0,
                "max_disproportion": 0.0,
                "strength": "Weak"
            }
        
        try:
            total = len(df)
            
            # Calculate seriousness percentage
            serious_col = self.find_column(df, ["serious", "seriousness", "serious_flag"])
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
            
            # Calculate max disproportion (most frequent reaction percentage)
            reaction_col = self.find_column(df, ["reaction", "reaction_pt", "reaction_normalized", "pt"])
            max_disproportion = 0.0
            
            if reaction_col:
                reaction_counts = df.groupby(reaction_col).size()
                if len(reaction_counts) > 0:
                    max_count = reaction_counts.max()
                    max_disproportion = (max_count / total) * 100 if total > 0 else 0.0
            
            # Compute signal strength score
            score = (serious_pct * 0.5) + (max_disproportion * 0.5)
            
            # Classify strength
            if score >= 60:
                strength = "Strong"
            elif score >= 30:
                strength = "Moderate"
            else:
                strength = "Weak"
            
            return {
                "score": round(score, 2),
                "serious_pct": round(serious_pct, 2),
                "max_disproportion": round(max_disproportion, 2),
                "strength": strength
            }
            
        except Exception as e:
            return {
                "score": 0.0,
                "serious_pct": 0.0,
                "max_disproportion": 0.0,
                "strength": "Unknown",
                "error": str(e)
            }

