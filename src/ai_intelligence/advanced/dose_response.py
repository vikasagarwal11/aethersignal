"""
Dose-Response Estimator
Detects dose-response relationships and duration effects
"""

import logging
from typing import Dict, Optional, List, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DoseResponseEstimator:
    """Estimates dose-response relationships from data."""
    
    def estimate(
        self,
        df: pd.DataFrame,
        dose_col: str = "dose",
        reaction_col: str = "reaction",
        count_col: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate dose-response relationship.
        
        Args:
            df: DataFrame with dose and reaction data
            dose_col: Name of dose column
            reaction_col: Name of reaction column
            count_col: Optional count column (if None, counts reactions)
        
        Returns:
            Dictionary with dose-response analysis or None
        """
        if df.empty:
            return None
        
        if dose_col not in df.columns:
            logger.warning(f"Dose column '{dose_col}' not found")
            return None
        
        if reaction_col not in df.columns:
            logger.warning(f"Reaction column '{reaction_col}' not found")
            return None
        
        try:
            # Group by dose
            if count_col and count_col in df.columns:
                grouped = df.groupby(dose_col)[count_col].sum()
            else:
                grouped = df.groupby(dose_col)[reaction_col].count()
            
            dose_response = grouped.sort_index().to_dict()
            
            # Calculate correlation
            doses = sorted(dose_response.keys())
            counts = [dose_response[dose] for dose in doses]
            
            if len(doses) >= 2:
                correlation = np.corrcoef(doses, counts)[0, 1] if len(doses) > 1 else 0.0
                
                # Determine relationship type
                if correlation > 0.5:
                    relationship = "POSITIVE"
                elif correlation < -0.5:
                    relationship = "NEGATIVE"
                else:
                    relationship = "NONE"
                
                return {
                    "dose_response": dose_response,
                    "correlation": round(float(correlation), 3),
                    "relationship": relationship,
                    "doses": doses,
                    "counts": counts
                }
            
            return {
                "dose_response": dose_response,
                "correlation": 0.0,
                "relationship": "INSUFFICIENT_DATA",
                "doses": doses,
                "counts": counts
            }
            
        except Exception as e:
            logger.error(f"Error estimating dose-response: {e}")
            return None
    
    def estimate_duration_response(
        self,
        df: pd.DataFrame,
        duration_col: str = "duration",
        reaction_col: str = "reaction"
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate duration-response relationship.
        
        Args:
            df: DataFrame with duration and reaction data
            duration_col: Name of duration column
            reaction_col: Name of reaction column
        
        Returns:
            Dictionary with duration-response analysis or None
        """
        if df.empty or duration_col not in df.columns:
            return None
        
        try:
            # Group by duration bins
            df["duration_bin"] = pd.cut(
                df[duration_col],
                bins=[0, 7, 30, 90, 365, float('inf')],
                labels=["<1 week", "1-4 weeks", "1-3 months", "3-12 months", ">1 year"]
            )
            
            grouped = df.groupby("duration_bin")[reaction_col].count()
            
            return {
                "duration_response": grouped.to_dict(),
                "total_observations": len(df)
            }
            
        except Exception as e:
            logger.error(f"Error estimating duration-response: {e}")
            return None

