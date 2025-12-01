"""
Local CAPA Starter (CHUNK 7.5.8)
Generates initial CAPA recommendations locally.
Full CAPA requires server LLM enhancement.
"""
import pandas as pd
from typing import List, Dict, Any
from .base_local_engine import BaseLocalEngine


class LocalCAPAStarter(BaseLocalEngine):
    """
    Local CAPA (Corrective and Preventive Actions) starter engine.
    
    Generates initial CAPA triggers based on data patterns.
    Full CAPA requires server LLM enhancement.
    """
    
    def generate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generate initial CAPA recommendations.
        
        Args:
            df: Safety data DataFrame
            
        Returns:
            List of CAPA recommendations
        """
        if df is None or df.empty:
            return [{"action": "No data available for CAPA analysis", "priority": "Low"}]
        
        capa_items = []
        
        try:
            total = len(df)
            
            # Check serious case rate
            serious_col = self.find_column(df, ["serious", "seriousness", "serious_flag"])
            if serious_col:
                serious_values = df[serious_col]
                if serious_values.dtype == bool:
                    serious_count = int(serious_values.sum())
                elif serious_values.dtype in [int, float]:
                    serious_count = int((serious_values == 1).sum())
                else:
                    serious_count = int(serious_values.astype(str).str.upper().str.contains("Y|1|TRUE|SERIOUS", na=False).sum())
                
                serious_rate = serious_count / total if total > 0 else 0.0
                
                if serious_rate > 0.20:  # >20% serious cases
                    capa_items.append({
                        "action": "Investigate elevated serious case rate (>20%)",
                        "priority": "High",
                        "metric": f"{serious_rate*100:.1f}% serious cases"
                    })
            
            # Check geriatric population
            age_col = self.find_column(df, ["age", "age_yrs", "patient_age"])
            if age_col:
                try:
                    ages = pd.to_numeric(df[age_col], errors="coerce").dropna()
                    if len(ages) > 0:
                        mean_age = ages.mean()
                        elderly_count = int((ages >= 65).sum())
                        elderly_pct = (elderly_count / len(ages)) * 100 if len(ages) > 0 else 0.0
                        
                        if mean_age > 60 or elderly_pct > 30:
                            capa_items.append({
                                "action": "Evaluate geriatric safety impact",
                                "priority": "Medium",
                                "metric": f"Mean age: {mean_age:.1f} years, {elderly_pct:.1f}% elderly"
                            })
                except Exception:
                    pass
            
            # Check fatal outcomes
            outcome_col = self.find_column(df, ["outcome", "outc_cod", "fatal"])
            if outcome_col:
                fatal_count = int(df[outcome_col].astype(str).str.upper().str.contains("DEATH|FATAL|1", na=False).sum())
                if fatal_count > 0:
                    fatal_rate = (fatal_count / total) * 100 if total > 0 else 0.0
                    if fatal_rate > 5.0:  # >5% fatal
                        capa_items.append({
                            "action": "Review fatal outcomes - consider safety committee",
                            "priority": "High",
                            "metric": f"{fatal_count} fatal cases ({fatal_rate:.1f}%)"
                        })
            
            # Default if no triggers
            if len(capa_items) == 0:
                capa_items.append({
                    "action": "No immediate CAPA triggers detected",
                    "priority": "Low",
                    "metric": "Routine monitoring"
                })
            
        except Exception as e:
            capa_items.append({
                "action": f"Error generating CAPA: {str(e)}",
                "priority": "Low",
                "error": True
            })
        
        return capa_items

