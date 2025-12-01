"""
Lot/Batch Spike Detection Engine for Pharmacovigilance (CHUNK 6.11.13)
Detects manufacturing defects, contaminated lots, storage issues, and temperature excursion patterns.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from scipy.stats import poisson


class LotDetectionEngine:
    """
    Lot/Batch detection engine for manufacturing signal detection.
    Detects anomalies in specific lot numbers indicating potential manufacturing issues.
    """
    
    def __init__(self, min_cases: int = 5, spike_factor: float = 2.0):
        """
        Initialize the lot detection engine.
        
        Args:
            min_cases: Minimum number of cases required to flag a lot
            spike_factor: Multiplier above average to consider a spike
        """
        self.min_cases = min_cases
        self.spike_factor = spike_factor
    
    def _find_lot_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find lot number column by checking common names."""
        lot_cols = ["lot_number", "lot_num", "batch_number", "batch_num", "lot", "batch", "lot_id"]
        for col in lot_cols:
            if col in df.columns:
                return col
        return None
    
    def detect_lot_spikes(
        self,
        df: pd.DataFrame,
        drug: Optional[str] = None,
        reaction: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect lot/batch spikes indicating potential manufacturing issues (CHUNK 6.11.13).
        
        Args:
            df: DataFrame with case data
            drug: Optional drug name to filter
            reaction: Optional reaction name to filter
            
        Returns:
            List of lot alert dictionaries
        """
        if df is None or len(df) == 0:
            return []
        
        # Find lot column
        lot_col = self._find_lot_column(df)
        if not lot_col:
            return []
        
        # Filter out missing lot numbers
        filtered = df[df[lot_col].notna()].copy()
        filtered[lot_col] = filtered[lot_col].astype(str).str.strip()
        filtered = filtered[filtered[lot_col] != ""]
        filtered = filtered[filtered[lot_col].str.lower() != "nan"]
        
        if filtered.empty:
            return []
        
        # Additional filtering by drug/reaction if provided
        if drug:
            drug_col = None
            for col in ["drug_name", "drug", "drug_concept_name"]:
                if col in filtered.columns:
                    drug_col = col
                    break
            
            if drug_col:
                filtered = filtered[
                    filtered[drug_col].astype(str).str.contains(str(drug), na=False, case=False)
                ]
        
        if reaction:
            reaction_col = None
            for col in ["reaction", "reaction_pt", "reaction_name"]:
                if col in filtered.columns:
                    reaction_col = col
                    break
            
            if reaction_col:
                filtered = filtered[
                    filtered[reaction_col].astype(str).str.contains(str(reaction), na=False, case=False)
                ]
        
        if filtered.empty:
            return []
        
        # Count cases per lot
        lot_counts = filtered.groupby(lot_col).size().sort_values(ascending=False)
        
        if len(lot_counts) < 2:
            return []  # Need at least 2 lots to compare
        
        # Global average cases per lot
        avg = float(lot_counts.mean())
        std = float(lot_counts.std())
        
        alerts = []
        
        for lot, count in lot_counts.items():
            if count < self.min_cases:
                continue
            
            # Poisson anomaly test
            expected = max(avg, 0.1)  # Avoid division by zero
            try:
                prob = 1.0 - poisson.cdf(count - 1, expected)  # P(X >= count)
            except Exception:
                prob = 1.0
            
            # Spike factor test
            spike_ratio = count / (avg + 1e-6)
            
            # Flag if spike is significant
            if spike_ratio >= self.spike_factor or (prob < 0.01 and spike_ratio > 1.5):
                lot_df = filtered[filtered[lot_col] == lot]
                
                # Get drug
                drug_mode = None
                for col in ["drug_name", "drug", "drug_concept_name"]:
                    if col in lot_df.columns:
                        drug_series = lot_df[col].dropna()
                        if not drug_series.empty:
                            drug_mode = str(drug_series.mode().iloc[0] if len(drug_series.mode()) > 0 else drug_series.iloc[0])
                            break
                
                # Get top reactions
                reactions = []
                for col in ["reaction", "reaction_pt", "reaction_name"]:
                    if col in lot_df.columns:
                        reaction_series = lot_df[col].dropna()
                        if not reaction_series.empty:
                            # Handle multi-value reactions (split by ";")
                            all_reactions = []
                            for rxn in reaction_series:
                                all_reactions.extend(str(rxn).split(";"))
                            reaction_counts = pd.Series(all_reactions).value_counts().head(5)
                            reactions = reaction_counts.index.tolist()
                            break
                
                # Count serious cases
                serious_count = 0
                if "serious" in lot_df.columns:
                    serious_count = int(lot_df["serious"].astype(str).str.contains("true|1|yes", case=False, na=False).sum())
                elif "seriousness" in lot_df.columns:
                    serious_count = int(lot_df["seriousness"].astype(str).str.contains("serious", case=False, na=False).sum())
                
                # Calculate serious case ratio
                serious_ratio = serious_count / count if count > 0 else 0.0
                
                alerts.append({
                    "lot_number": str(lot),
                    "count": int(count),
                    "spike_ratio": float(spike_ratio),
                    "p_value": float(prob),
                    "drug": drug_mode,
                    "top_reactions": [str(r) for r in reactions],
                    "serious_count": serious_count,
                    "serious_ratio": float(serious_ratio),
                    "expected_count": float(avg),
                    "z_score": float((count - avg) / (std + 1e-6)) if std > 0 else 0.0
                })
        
        # Sort by spike ratio (highest first)
        alerts.sort(key=lambda x: x["spike_ratio"], reverse=True)
        
        return alerts
