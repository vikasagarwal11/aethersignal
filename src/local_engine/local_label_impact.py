"""
Local Label Impact Detection (CHUNK 7.5.9)
Detects potential label impact signals locally.
Full label impact requires server LLM enhancement.
"""
import pandas as pd
from typing import List, Dict, Any
from .base_local_engine import BaseLocalEngine


class LocalLabelImpact(BaseLocalEngine):
    """
    Local label impact detection engine.
    
    Detects potential label update triggers based on:
    - Seriousness rates
    - Fatal outcomes
    - Frequency patterns
    
    Full label impact assessment requires server LLM enhancement.
    """
    
    def detect(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect potential label impact signals.
        
        Args:
            df: Safety data DataFrame
            
        Returns:
            List of label impact recommendations
        """
        if df is None or df.empty:
            return [{"impact": "No data available for label impact assessment", "severity": "Low"}]
        
        impacts = []
        
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
                
                if serious_pct > 25:
                    impacts.append({
                        "impact": "Potential need to strengthen Warnings section",
                        "severity": "High",
                        "reason": f"High serious case rate ({serious_pct:.1f}%)"
                    })
                elif serious_pct > 15:
                    impacts.append({
                        "impact": "Consider updating Adverse Reactions section",
                        "severity": "Medium",
                        "reason": f"Moderate serious case rate ({serious_pct:.1f}%)"
                    })
            
            # Check fatal outcomes
            outcome_col = self.find_column(df, ["outcome", "outc_cod", "fatal"])
            if outcome_col:
                fatal_count = int(df[outcome_col].astype(str).str.upper().str.contains("DEATH|FATAL|1", na=False).sum())
                if fatal_count > 0:
                    fatal_rate = (fatal_count / total) * 100 if total > 0 else 0.0
                    if fatal_rate > 2.0:  # >2% fatal
                        impacts.append({
                            "impact": "Review for potential Boxed Warning consideration",
                            "severity": "High",
                            "reason": f"Fatal outcomes detected ({fatal_count} cases, {fatal_rate:.1f}%)"
                        })
            
            # Default if no signals
            if len(impacts) == 0:
                impacts.append({
                    "impact": "No major label signals detected",
                    "severity": "Low",
                    "reason": "Routine monitoring"
                })
            
        except Exception as e:
            impacts.append({
                "impact": f"Error detecting label impact: {str(e)}",
                "severity": "Low",
                "error": True
            })
        
        return impacts

