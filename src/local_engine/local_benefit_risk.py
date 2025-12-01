"""
Local Benefit-Risk Summary (CHUNK 7.5.7)
Placeholder benefit-risk summary for local engine.
Will be enhanced by server LLM when available.
"""
import pandas as pd
from typing import Dict, Any
from .base_local_engine import BaseLocalEngine


class LocalBenefitRisk(BaseLocalEngine):
    """
    Local benefit-risk summary engine.
    
    Provides basic benefit-risk metrics locally.
    Full narrative requires server LLM enhancement.
    """
    
    def draft_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Draft basic benefit-risk summary.
        
        Args:
            df: Safety data DataFrame
            
        Returns:
            Dictionary with basic benefit-risk metrics
        """
        if df is None or df.empty:
            return {
                "benefits": "No data available for benefit assessment.",
                "risks": "No data available for risk assessment.",
                "initial_br_flag": "Insufficient data"
            }
        
        try:
            total = len(df)
            
            # Calculate seriousness percentage
            serious_col = self.find_column(df, ["serious", "seriousness", "serious_flag"])
            serious_pct = 0.0
            fatal_count = 0
            
            if serious_col:
                serious_values = df[serious_col]
                if serious_values.dtype == bool:
                    serious_count = int(serious_values.sum())
                elif serious_values.dtype in [int, float]:
                    serious_count = int((serious_values == 1).sum())
                else:
                    serious_count = int(serious_values.astype(str).str.upper().str.contains("Y|1|TRUE|SERIOUS", na=False).sum())
                
                serious_pct = (serious_count / total) * 100 if total > 0 else 0.0
            
            # Check for fatal outcomes
            outcome_col = self.find_column(df, ["outcome", "outc_cod", "fatal"])
            if outcome_col:
                fatal_keywords = ["DEATH", "FATAL", "1"]
                fatal_count = int(df[outcome_col].astype(str).str.upper().str.contains("|".join(fatal_keywords), na=False).sum())
            
            # Generate basic risk summary
            risk_summary = f"Dataset contains {total:,} cases. "
            risk_summary += f"Approximately {serious_pct:.1f}% were serious cases. "
            if fatal_count > 0:
                risk_summary += f"{fatal_count} fatal outcomes reported. "
            risk_summary += "Full benefit-risk assessment requires server AI enhancement."
            
            return {
                "benefits": "Efficacy and therapeutic benefit assessment requires clinical context and server AI analysis.",
                "risks": risk_summary,
                "metrics": {
                    "total_cases": total,
                    "serious_pct": round(serious_pct, 2),
                    "fatal_cases": fatal_count
                },
                "initial_br_flag": "Needs LLM refinement"
            }
            
        except Exception as e:
            return {
                "benefits": "Error generating benefit summary.",
                "risks": f"Error generating risk summary: {str(e)}",
                "initial_br_flag": "Error"
            }

