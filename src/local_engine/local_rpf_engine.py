"""
Local RPF Engine (CHUNK A - Part 1)
Offline Risk Prioritization Framework running fully in-browser via Pyodide.
Computes weighted RPF scores without server round-trips.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from .base_local_engine import BaseLocalEngine


class LocalRPFEngine(BaseLocalEngine):
    """
    Offline Risk Prioritization Framework Engine.
    
    Computes weighted RPF fully in-browser using Pyodide.
    
    RPF Score = weighted combination of:
    - Case volume (30%)
    - Seriousness (30%)
    - Reporting trend slope (20%)
    - Disproportionality (20%)
    """
    
    DEFAULT_WEIGHTS = {
        "cases": 0.30,
        "serious": 0.30,
        "reporting_slope": 0.20,
        "disproportionality": 0.20
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize Local RPF Engine.
        
        Args:
            weights: Custom weight dictionary (optional)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def compute(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Compute RPF scores for all drug-reaction combinations.
        
        Args:
            df: Safety data DataFrame with columns:
                - CASE_ID (or similar)
                - SERIOUS (or seriousness flag)
                - YEAR (or date column)
                - DRUG (or drug_name)
                - REACTION (or reaction_pt)
        
        Returns:
            List of RPF results sorted by RPF score (descending)
        """
        if df is None or df.empty:
            return []
        
        try:
            # Find relevant columns
            drug_col = self.find_column(df, ["drug", "drug_name", "drug_normalized", "prod_ai", "drugname"])
            reaction_col = self.find_column(df, ["reaction", "reaction_pt", "reaction_normalized", "pt", "pt_name"])
            serious_col = self.find_column(df, ["serious", "seriousness", "serious_flag", "serious_cod"])
            year_col = self.find_column(df, ["year", "YEAR", "report_dt", "event_date", "fda_dt"])
            
            if not drug_col or not reaction_col:
                return []
            
            # Prepare working DataFrame
            df_work = df.copy()
            
            # Extract year if date column
            if year_col and ("date" in year_col.lower() or "dt" in year_col.lower()):
                df_work["YEAR"] = pd.to_datetime(df_work[year_col], errors="coerce").dt.year
                year_col = "YEAR"
            
            df_work = df_work[df_work[drug_col].notna() & df_work[reaction_col].notna()]
            
            if df_work.empty:
                return []
            
            result = []
            
            # 1. Group by drug-reaction combination
            by_combo = df_work.groupby([drug_col, reaction_col])
            case_counts = by_combo.size()
            
            # 2. Calculate seriousness counts
            serious_counts = {}
            if serious_col:
                serious_values = df_work[serious_col]
                if serious_values.dtype == bool:
                    serious_counts = by_combo[serious_col].sum().to_dict()
                elif serious_values.dtype in [int, float]:
                    serious_counts = by_combo[serious_col].apply(lambda x: (x == 1).sum()).to_dict()
                else:
                    serious_counts = by_combo[serious_col].apply(
                        lambda x: x.astype(str).str.upper().str.contains("Y|1|TRUE|SERIOUS", na=False).sum()
                    ).to_dict()
            
            # 3. Calculate reporting slope (trend)
            slopes = {}
            if year_col:
                for (drug, reaction), group in by_combo:
                    yearly = group.groupby(year_col).size().sort_index()
                    if len(yearly) >= 2:
                        try:
                            slope = float(np.polyfit(range(len(yearly)), yearly.values, 1)[0])
                        except Exception:
                            slope = 0.0
                    else:
                        slope = 0.0
                    slopes[(drug, reaction)] = slope
            
            # 4. Baseline disproportionality (PRR-lite)
            background = df_work.groupby(reaction_col).size()
            total_cases = len(df_work)
            dispro = {}
            
            for combo, count in case_counts.items():
                drug, reaction = combo
                reaction_total = background.get(reaction, 0)
                if total_cases > 0 and reaction_total > 0:
                    # Simple disproportionality: observed vs expected
                    expected = (reaction_total / total_cases) * count
                    if expected > 0:
                        score = (count - expected) / expected
                    else:
                        score = 0.0
                else:
                    score = 0.0
                dispro[combo] = score
            
            # 5. Combine with weights to compute RPF
            max_cases = case_counts.max() if len(case_counts) > 0 else 1
            max_serious = max(serious_counts.values()) if serious_counts else 1
            max_slope = max(abs(s) for s in slopes.values()) if slopes else 1
            max_dispro = max(abs(d) for d in dispro.values()) if dispro else 1
            
            # Normalize components to 0-100 scale
            for combo, count in case_counts.items():
                drug, reaction = combo
                serious = serious_counts.get(combo, 0)
                slope = slopes.get(combo, 0.0)
                prr = dispro.get(combo, 0.0)
                
                # Normalize each component
                cases_norm = (count / max_cases * 100) if max_cases > 0 else 0
                serious_norm = (serious / max_serious * 100) if max_serious > 0 else 0
                slope_norm = (abs(slope) / max_slope * 100) if max_slope > 0 else 0
                prr_norm = (abs(prr) / max_dispro * 100) if max_dispro > 0 else 0
                
                # Weighted RPF score
                rpf = (
                    cases_norm * self.weights.get("cases", 0.30) +
                    serious_norm * self.weights.get("serious", 0.30) +
                    slope_norm * self.weights.get("reporting_slope", 0.20) +
                    prr_norm * self.weights.get("disproportionality", 0.20)
                )
                
                # Classify priority
                if rpf >= 70:
                    priority = "High"
                elif rpf >= 40:
                    priority = "Medium"
                else:
                    priority = "Low"
                
                result.append({
                    "drug": str(drug),
                    "reaction": str(reaction),
                    "cases": int(count),
                    "serious": int(serious),
                    "slope": round(float(slope), 2),
                    "disproportionality": round(float(prr), 3),
                    "rpf": round(float(rpf), 2),
                    "priority": priority
                })
            
            # Sort by RPF score (descending)
            result = sorted(result, key=lambda x: x["rpf"], reverse=True)
            
            return result
            
        except Exception as e:
            return [{
                "error": str(e),
                "drug": "Error",
                "reaction": "Error",
                "rpf": 0.0
            }]

