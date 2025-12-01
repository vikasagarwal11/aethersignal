"""
Change-Point Detection Engine for Pharmacovigilance (CHUNK 6.11.10)
Detects structural breaks in time series using multiple statistical methods.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from scipy import stats

# Optional dependency for advanced change-point detection
try:
    import ruptures as rpt
    RUPTURES_AVAILABLE = True
except ImportError:
    RUPTURES_AVAILABLE = False


class ChangePointEngine:
    """
    Change-point detection engine for PV trend analysis.
    Detects structural breaks in reporting patterns using multiple methods:
    - PELT algorithm (ruptures library)
    - CUSUM (Cumulative Sum)
    - Rolling Z-score vs baseline
    """
    
    def detect_changepoints(
        self, 
        monthly_series: Union[Dict[str, Any], pd.Series, List[float]],
        method: str = "pelt",
        penalty: float = 3.0
    ) -> List[int]:
        """
        Detect structural shifts in trend using multiple methods (CHUNK 6.11.10).
        
        Args:
            monthly_series: Dictionary mapping period strings to counts,
                          pandas Series, or list of numeric values
            method: Detection method ("pelt", "cusum", "zscore", or "all")
            penalty: Penalty parameter for PELT (lower = more sensitive)
            
        Returns:
            List of indices where change-points occur (sorted)
        """
        # Convert input to numpy array
        if isinstance(monthly_series, dict):
            values = np.array(list(monthly_series.values()), dtype=float)
            periods = list(monthly_series.keys())
        elif isinstance(monthly_series, pd.Series):
            values = monthly_series.fillna(0).values.astype(float)
            periods = monthly_series.index.tolist()
        elif isinstance(monthly_series, list):
            values = np.array(monthly_series, dtype=float)
            periods = []
        else:
            return []
        
        if len(values) < 6:
            return []
        
        all_changepoints = set()
        
        # Method 1: PELT (Pruned Exact Linear Time) - if ruptures available
        if method in ["pelt", "all"] and RUPTURES_AVAILABLE:
            try:
                algo = rpt.Pelt(model="rbf").fit(values.reshape(-1, 1))
                result = algo.predict(pen=penalty)
                # Drop final point (algorithm always returns endpoint)
                pelt_points = [int(x) for x in result[:-1] if x < len(values)]
                all_changepoints.update(pelt_points)
            except Exception:
                pass
        
        # Method 2: CUSUM (Cumulative Sum)
        if method in ["cusum", "all"]:
            try:
                cusum_points = self._detect_cusum_changepoints(values)
                all_changepoints.update(cusum_points)
            except Exception:
                pass
        
        # Method 3: Rolling Z-score vs baseline
        if method in ["zscore", "all"]:
            try:
                zscore_points = self._detect_zscore_changepoints(values)
                all_changepoints.update(zscore_points)
            except Exception:
                pass
        
        # Return sorted list of unique change-points
        return sorted(list(all_changepoints))
    
    def _detect_cusum_changepoints(self, values: np.ndarray, threshold: float = 2.0) -> List[int]:
        """
        Detect change-points using CUSUM (Cumulative Sum) method.
        
        Args:
            values: Time series values
            threshold: Threshold for change detection (multiple of std)
            
        Returns:
            List of change-point indices
        """
        if len(values) < 6:
            return []
        
        # Calculate mean of first half as baseline
        baseline_mean = np.mean(values[:len(values)//2])
        std = np.std(values)
        
        # CUSUM calculation
        cusum = np.cumsum(values - baseline_mean)
        
        # Detect when CUSUM exceeds threshold
        changepoints = []
        threshold_value = threshold * std * np.sqrt(len(values))
        
        for i in range(1, len(cusum)):
            if abs(cusum[i]) > threshold_value and i > 2:  # Skip first few points
                changepoints.append(i)
        
        return changepoints
    
    def _detect_zscore_changepoints(
        self, 
        values: np.ndarray, 
        window: int = 3,
        z_threshold: float = 2.5
    ) -> List[int]:
        """
        Detect change-points using rolling Z-score method.
        
        Args:
            values: Time series values
            window: Window size for baseline calculation
            z_threshold: Z-score threshold for detection
            
        Returns:
            List of change-point indices
        """
        if len(values) < window * 2:
            return []
        
        changepoints = []
        baseline = np.mean(values[:window])
        baseline_std = np.std(values[:window])
        
        if baseline_std == 0:
            baseline_std = 1.0
        
        # Check each point after baseline window
        for i in range(window, len(values)):
            z_score = abs((values[i] - baseline) / baseline_std)
            if z_score > z_threshold:
                changepoints.append(i)
        
        return changepoints
    
    def detect_changepoints_with_context(
        self,
        monthly_series: Union[Dict[str, Any], pd.Series, List[float]],
        periods: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect change-points with additional context (period labels, before/after means).
        
        Args:
            monthly_series: Time series data
            periods: Optional list of period labels (strings)
            
        Returns:
            List of dictionaries with change-point details
        """
        changepoints = self.detect_changepoints(monthly_series, method="all")
        
        # Convert to arrays
        if isinstance(monthly_series, dict):
            values = np.array(list(monthly_series.values()), dtype=float)
            if periods is None:
                periods = list(monthly_series.keys())
        elif isinstance(monthly_series, pd.Series):
            values = monthly_series.fillna(0).values.astype(float)
            if periods is None:
                periods = [str(p) for p in monthly_series.index]
        else:
            values = np.array(monthly_series, dtype=float)
            if periods is None:
                periods = [f"Period_{i}" for i in range(len(values))]
        
        result = []
        for cp_idx in changepoints:
            if cp_idx < 1 or cp_idx >= len(values):
                continue
            
            before_mean = float(np.mean(values[:cp_idx]))
            after_mean = float(np.mean(values[cp_idx:]))
            change_ratio = after_mean / (before_mean + 1e-6)
            
            result.append({
                "index": int(cp_idx),
                "period": periods[cp_idx] if cp_idx < len(periods) else f"Period_{cp_idx}",
                "before_mean": before_mean,
                "after_mean": after_mean,
                "change_ratio": float(change_ratio),
                "change_magnitude": float(abs(after_mean - before_mean))
            })
        
        return result
