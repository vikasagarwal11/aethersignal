"""
Risk Acceleration Engine for Pharmacovigilance (CHUNK 6.11.10)
Computes velocity (rate of change) and acceleration (second derivative) of reporting rates.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union


class RiskAccelerationEngine:
    """
    Risk acceleration analysis engine for PV trend detection.
    Computes velocity (first derivative) and acceleration (second derivative) 
    to detect accelerating, decelerating, or stable risk patterns.
    """
    
    def compute_velocity_acceleration(
        self, 
        monthly_series: Union[Dict[str, Any], pd.Series, List[float]]
    ) -> Optional[Dict[str, Any]]:
        """
        Compute velocity & acceleration for monthly counts (CHUNK 6.11.10).
        
        Velocity = first derivative (month-over-month change)
        Acceleration = second derivative (change in velocity)
        
        Args:
            monthly_series: Dictionary mapping period strings to counts, 
                          pandas Series, or list of numeric values
            
        Returns:
            Dictionary with velocity, acceleration, and scores or None if insufficient data
        """
        # Convert input to numpy array
        if isinstance(monthly_series, dict):
            # Extract values from dictionary (preserve order)
            values = np.array(list(monthly_series.values()), dtype=float)
            periods = list(monthly_series.keys())
        elif isinstance(monthly_series, pd.Series):
            values = monthly_series.fillna(0).values.astype(float)
            periods = monthly_series.index.tolist() if hasattr(monthly_series.index, 'tolist') else []
        elif isinstance(monthly_series, list):
            values = np.array(monthly_series, dtype=float)
            periods = []
        else:
            return None
        
        # Need at least 4 points to compute acceleration
        if len(values) < 4:
            return None
        
        # Compute velocity (first derivative: month-over-month change)
        velocity = np.diff(values)
        
        # Compute acceleration (second derivative: change in velocity)
        acceleration = np.diff(velocity)
        
        # Calculate acceleration score (recent trend)
        if len(acceleration) > 2:
            acceleration_score = float(np.mean(acceleration[-2:]))  # Average of last 2 points
        elif len(acceleration) > 0:
            acceleration_score = float(acceleration[-1])
        else:
            acceleration_score = 0.0
        
        # Determine trend classification
        if acceleration_score > 0.5:
            trend_classification = "accelerating"
        elif acceleration_score < -0.5:
            trend_classification = "decelerating"
        else:
            trend_classification = "stable"
        
        # Calculate velocity trend (is velocity itself increasing?)
        if len(velocity) > 2:
            velocity_trend = float(np.mean(velocity[-2:]) - np.mean(velocity[:2]))
        elif len(velocity) > 1:
            velocity_trend = float(velocity[-1] - velocity[0])
        else:
            velocity_trend = 0.0
        
        # Calculate recent velocity (average of last 2 months)
        recent_velocity = float(np.mean(velocity[-2:])) if len(velocity) >= 2 else float(velocity[-1]) if len(velocity) > 0 else 0.0
        
        # Calculate baseline velocity (average of first 2 months)
        baseline_velocity = float(np.mean(velocity[:2])) if len(velocity) >= 2 else float(velocity[0]) if len(velocity) > 0 else 0.0
        
        # Velocity ratio (recent vs baseline)
        velocity_ratio = recent_velocity / (baseline_velocity + 1e-6) if baseline_velocity != 0 else 0.0
        
        return {
            "velocity": velocity.tolist(),
            "acceleration": acceleration.tolist(),
            "periods": periods[1:] if periods else [],  # Velocity periods (one less than original)
            "acceleration_periods": periods[2:] if periods else [],  # Acceleration periods (two less)
            "acceleration_score": acceleration_score,
            "trend_classification": trend_classification,
            "velocity_trend": velocity_trend,
            "recent_velocity": recent_velocity,
            "baseline_velocity": baseline_velocity,
            "velocity_ratio": velocity_ratio,
            "is_accelerating": acceleration_score > 0.5,
            "is_decelerating": acceleration_score < -0.5
        }
    
    def compute_incident_rate_slope(
        self,
        monthly_series: Union[Dict[str, Any], pd.Series, List[float]],
        exposure_series: Optional[Union[Dict[str, Any], pd.Series, List[float]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Compute incident rate slope analysis (CHUNK 6.11.10).
        
        Measures the slope of raw reporting rate and exposure-adjusted rate.
        
        Args:
            monthly_series: Case counts by period
            exposure_series: Optional exposure data for normalization
            
        Returns:
            Dictionary with slope analysis results or None if insufficient data
        """
        # Convert to arrays
        if isinstance(monthly_series, dict):
            counts = np.array(list(monthly_series.values()), dtype=float)
            periods = list(monthly_series.keys())
        elif isinstance(monthly_series, pd.Series):
            counts = monthly_series.fillna(0).values.astype(float)
            periods = monthly_series.index.tolist()
        elif isinstance(monthly_series, list):
            counts = np.array(monthly_series, dtype=float)
            periods = []
        else:
            return None
        
        if len(counts) < 3:
            return None
        
        # Calculate raw reporting rate slope (linear regression)
        x = np.arange(len(counts))
        slope_raw = float(np.polyfit(x, counts, 1)[0])
        
        # Calculate exposure-adjusted rate if exposure data provided
        slope_exposure_adjusted = None
        if exposure_series is not None:
            if isinstance(exposure_series, dict):
                exposure = np.array(list(exposure_series.values()), dtype=float)
            elif isinstance(exposure_series, pd.Series):
                exposure = exposure_series.fillna(0).values.astype(float)
            elif isinstance(exposure_series, list):
                exposure = np.array(exposure_series, dtype=float)
            else:
                exposure = None
            
            if exposure is not None and len(exposure) == len(counts):
                # Avoid division by zero
                exposure = np.where(exposure == 0, 1.0, exposure)
                rates = counts / exposure
                slope_exposure_adjusted = float(np.polyfit(x, rates, 1)[0])
        
        # Classify slope direction
        if slope_raw > 0.1:
            direction = "rising"
        elif slope_raw < -0.1:
            direction = "declining"
        else:
            direction = "plateaued"
        
        return {
            "slope_raw": slope_raw,
            "slope_exposure_adjusted": slope_exposure_adjusted,
            "direction": direction,
            "is_rising": slope_raw > 0.1,
            "is_declining": slope_raw < -0.1,
            "is_plateaued": abs(slope_raw) <= 0.1
        }
