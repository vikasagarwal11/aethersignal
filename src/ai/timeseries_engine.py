"""
Time-Series Anomaly Detection Engine for Pharmacovigilance (CHUNK 6.11.7)
Provides statistical trend analysis: moving averages, EWMA, change-point detection,
control charts, and anomaly detection.

This module provides the mathematical backbone for real signal detection.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from scipy.stats import zscore

# Optional dependency for change-point detection
try:
    import ruptures as rpt
    RUPTURES_AVAILABLE = True
except ImportError:
    RUPTURES_AVAILABLE = False


class TimeSeriesEngine:
    """
    Statistical time-series analysis engine for PV trend detection.
    Provides moving averages, EWMA, change-point detection, control limits, and anomaly detection.
    """
    
    def compute_ma(self, series: pd.Series, window: int = 3) -> pd.Series:
        """
        Compute moving average (MA) over a rolling window.
        
        Args:
            series: Time series data
            window: Rolling window size (default: 3 months)
            
        Returns:
            Series with moving average values
        """
        return series.rolling(window=window, min_periods=1).mean()
    
    def compute_ewma(self, series: pd.Series, alpha: float = 0.3) -> pd.Series:
        """
        Compute exponentially weighted moving average (EWMA).
        
        Args:
            series: Time series data
            alpha: Smoothing factor (0 < alpha <= 1), higher = more responsive to recent changes
            
        Returns:
            Series with EWMA values
        """
        return series.ewm(alpha=alpha, adjust=False).mean()
    
    def detect_change_points(self, series: pd.Series) -> List[int]:
        """
        Detect structural change-points using ruptures library (PELT algorithm).
        
        Args:
            series: Time series data
            
        Returns:
            List of indices where change-points occur
        """
        if not RUPTURES_AVAILABLE or len(series) < 4:
            return []
        
        try:
            # Convert to numpy array
            values = series.fillna(0).values
            if len(values) < 4:
                return []
            
            # Use PELT (Pruned Exact Linear Time) algorithm with RBF kernel
            algo = rpt.Pelt(model="rbf").fit(values)
            # Penalty parameter - lower = more sensitive to changes
            result = algo.predict(pen=5)
            
            # Return change-point indices (exclude last index which is always series end)
            if result and len(result) > 0:
                return [int(x) for x in result if x < len(series)]
            return []
        except Exception:
            # Fail gracefully if ruptures fails
            return []
    
    def compute_control_limits(self, series: pd.Series) -> Dict[str, float]:
        """
        Compute control chart limits (Shewhart-style).
        
        Args:
            series: Time series data
            
        Returns:
            Dictionary with UCL, LCL, mean, std
        """
        values = series.fillna(0).values
        if len(values) == 0:
            return {"ucl": 0, "lcl": 0, "mean": 0, "std": 0}
        
        mean = float(np.mean(values))
        std = float(np.std(values))
        
        return {
            "ucl": mean + 3 * std,  # Upper Control Limit (3 sigma)
            "lcl": max(0, mean - 3 * std),  # Lower Control Limit (3 sigma), no negative
            "mean": mean,
            "std": std
        }
    
    def detect_anomalies(self, series: pd.Series, threshold: float = 2.5) -> List[int]:
        """
        Detect anomalies using Z-score method.
        
        Args:
            series: Time series data
            threshold: Z-score threshold (default: 2.5 = ~1% of data if normally distributed)
            
        Returns:
            List of indices where anomalies occur
        """
        try:
            values = series.fillna(0).values
            if len(values) < 3:
                return []
            
            # Compute Z-scores
            z_scores = np.abs(zscore(values))
            
            # Find indices where Z-score exceeds threshold
            anomalies = list(np.where(z_scores > threshold)[0])
            
            return [int(x) for x in anomalies]
        except Exception:
            return []
    
    def summarize_timeseries(
        self, 
        df: pd.DataFrame, 
        drug: Optional[str] = None,
        reaction: Optional[str] = None,
        date_col: Optional[str] = None,
        drug_col: str = "drug_name",
        reaction_col: str = "reaction"
    ) -> Optional[Dict[str, Any]]:
        """
        Produce comprehensive time-series analysis for drug/reaction combination.
        
        Returns: MA, EWMA, expected vs observed, anomalies, change points, significance scores.
        
        Args:
            df: DataFrame with PV data
            drug: Drug name to filter (optional)
            reaction: Reaction name to filter (optional)
            date_col: Date column name (auto-detected if None)
            drug_col: Drug column name (default: "drug_name")
            reaction_col: Reaction column name (default: "reaction")
            
        Returns:
            Dictionary with time-series analysis results or None if insufficient data
        """
        if df is None or len(df) == 0:
            return None
        
        # Find date column if not provided
        if date_col is None:
            for col in ["event_date", "report_date", "receipt_date", "receive_date", 
                       "received_date", "onset_date"]:
                if col in df.columns:
                    date_col = col
                    break
        
        if date_col is None or date_col not in df.columns:
            return None
        
        # Filter by drug if specified
        filtered = df.copy()
        if drug:
            if drug_col in filtered.columns:
                # Handle multi-value drug columns (split by "; ")
                filtered = filtered[
                    filtered[drug_col].astype(str).str.contains(str(drug), na=False, regex=False)
                ]
            else:
                return None
        
        # Filter by reaction if specified
        if reaction:
            if reaction_col in filtered.columns:
                # Handle multi-value reaction columns
                filtered = filtered[
                    filtered[reaction_col].astype(str).str.contains(str(reaction), na=False, regex=False)
                ]
            else:
                return None
        
        if len(filtered) == 0:
            return None
        
        try:
            # Parse dates and create time series
            filtered[date_col] = pd.to_datetime(filtered[date_col], errors="coerce")
            filtered = filtered[filtered[date_col].notna()]
            
            if len(filtered) == 0:
                return None
            
            # Group by year-month for time series
            filtered["year_month"] = filtered[date_col].dt.to_period("M")
            ts = filtered.groupby("year_month").size().sort_index()
            
            if len(ts) < 3:
                return None
            
            # Compute moving averages
            ma = self.compute_ma(ts, window=3)
            ewma = self.compute_ewma(ts, alpha=0.3)
            
            # Compute control limits
            limits = self.compute_control_limits(ts)
            
            # Detect anomalies
            anomalies = self.detect_anomalies(ts, threshold=2.5)
            
            # Detect change points
            changepoints = self.detect_change_points(ts)
            
            # Compute latest vs expected
            latest_value = float(ts.iloc[-1])
            expected_value = float(ma.iloc[-1]) if len(ma) > 0 and not pd.isna(ma.iloc[-1]) else latest_value
            
            # Compute delta and significance
            delta = latest_value - expected_value
            std = limits.get("std", 1.0)
            significance = abs(delta / (std + 1e-6))  # Avoid division by zero
            
            # Convert Period indexes to strings for JSON serialization
            raw_dict = {str(period): int(count) for period, count in ts.items()}
            ma_dict = {str(period): float(val) if not pd.isna(val) else 0.0 
                      for period, val in ma.items()}
            ewma_dict = {str(period): float(val) if not pd.isna(val) else 0.0 
                        for period, val in ewma.items()}
            
            return {
                "raw": raw_dict,
                "ma": ma_dict,
                "ewma": ewma_dict,
                "limits": limits,
                "anomalies": anomalies,
                "changepoints": changepoints,
                "latest_value": latest_value,
                "expected_value": expected_value,
                "delta": delta,
                "significance": significance,
                "periods": [str(p) for p in ts.index],  # For plotting
                "data_points": len(ts)
            }
            
        except Exception as e:
            # Fail gracefully
            return None

