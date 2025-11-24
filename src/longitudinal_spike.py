"""
Longitudinal spike detection for AetherSignal.
Detects sudden increases in case counts over time periods.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from scipy import stats

from src.utils import safe_divide


def detect_spikes(
    trend_data: Dict[str, int],
    window_size: int = 3,
    threshold_multiplier: float = 2.0,
    min_cases: int = 5
) -> List[Dict]:
    """
    Detect spikes in longitudinal case counts.
    
    Args:
        trend_data: Dictionary mapping period strings to case counts
        window_size: Number of periods to use for baseline calculation
        threshold_multiplier: Multiplier for standard deviation threshold
        min_cases: Minimum cases required to flag a spike
        
    Returns:
        List of spike dictionaries with period, count, baseline, z_score, spike_ratio
    """
    if not trend_data or len(trend_data) < window_size + 1:
        return []
    
    # Convert to sorted DataFrame
    trend_df = pd.DataFrame(list(trend_data.items()), columns=["Period", "Count"])
    trend_df["Period"] = pd.to_datetime(trend_df["Period"], errors='coerce')
    trend_df = trend_df.sort_values("Period").reset_index(drop=True)
    trend_df = trend_df[trend_df["Count"] >= min_cases]  # Filter low counts
    
    if len(trend_df) < window_size + 1:
        return []
    
    spikes = []
    
    # Calculate rolling baseline (mean and std) for each point
    for i in range(window_size, len(trend_df)):
        window = trend_df.iloc[i - window_size:i]
        current = trend_df.iloc[i]
        
        baseline_mean = window["Count"].mean()
        baseline_std = window["Count"].std()
        
        if baseline_std == 0:
            baseline_std = 1.0  # Avoid division by zero
        
        current_count = current["Count"]
        
        # Z-score
        z_score = safe_divide(current_count - baseline_mean, baseline_std, 0.0)
        
        # Spike ratio (current / baseline mean)
        spike_ratio = safe_divide(current_count, baseline_mean, 0.0) if baseline_mean > 0 else 0.0
        
        # Threshold: mean + (multiplier * std)
        threshold = baseline_mean + (threshold_multiplier * baseline_std)
        
        # Flag as spike if exceeds threshold
        if current_count > threshold and current_count >= min_cases:
            spikes.append({
                "period": current["Period"],
                "period_str": current["Period"].strftime("%Y-%m") if pd.notna(current["Period"]) else str(current["Period"]),
                "count": int(current_count),
                "baseline_mean": float(baseline_mean),
                "baseline_std": float(baseline_std),
                "z_score": float(z_score),
                "spike_ratio": float(spike_ratio),
                "threshold": float(threshold),
                "excess_cases": int(current_count - baseline_mean),
            })
    
    # Sort by spike ratio (highest first)
    spikes.sort(key=lambda x: x["spike_ratio"], reverse=True)
    
    return spikes


def detect_statistical_spikes(
    trend_data: Dict[str, int],
    method: str = "poisson",
    alpha: float = 0.05
) -> List[Dict]:
    """
    Detect spikes using statistical tests (Poisson or Normal).
    
    Args:
        trend_data: Dictionary mapping period strings to case counts
        method: "poisson" or "normal"
        alpha: Significance level
        
    Returns:
        List of statistically significant spikes
    """
    if not trend_data or len(trend_data) < 3:
        return []
    
    trend_df = pd.DataFrame(list(trend_data.items()), columns=["Period", "Count"])
    trend_df["Period"] = pd.to_datetime(trend_df["Period"], errors='coerce')
    trend_df = trend_df.sort_values("Period").reset_index(drop=True)
    
    spikes = []
    
    if method == "poisson":
        # Poisson test: compare each period to historical mean
        historical_mean = trend_df["Count"].mean()
        
        for _, row in trend_df.iterrows():
            count = row["Count"]
            if count > historical_mean:
                # One-sided Poisson test
                p_value = 1 - stats.poisson.cdf(count - 1, historical_mean)
                
                if p_value < alpha:
                    spikes.append({
                        "period": row["Period"],
                        "period_str": row["Period"].strftime("%Y-%m") if pd.notna(row["Period"]) else str(row["Period"]),
                        "count": int(count),
                        "expected": float(historical_mean),
                        "p_value": float(p_value),
                        "method": "poisson",
                    })
    
    elif method == "normal":
        # Normal test: z-test
        historical_mean = trend_df["Count"].mean()
        historical_std = trend_df["Count"].std()
        
        if historical_std == 0:
            return []
        
        for _, row in trend_df.iterrows():
            count = row["Count"]
            z_score = safe_divide(count - historical_mean, historical_std, 0.0)
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-sided
            
            if p_value < alpha and count > historical_mean:
                spikes.append({
                    "period": row["Period"],
                    "period_str": row["Period"].strftime("%Y-%m") if pd.notna(row["Period"]) else str(row["Period"]),
                    "count": int(count),
                    "expected": float(historical_mean),
                    "z_score": float(z_score),
                    "p_value": float(p_value),
                    "method": "normal",
                })
    
    # Sort by p-value (most significant first)
    spikes.sort(key=lambda x: x.get("p_value", 1.0))
    
    return spikes


def analyze_trend_changepoint(
    trend_data: Dict[str, int]
) -> Optional[Dict]:
    """
    Detect changepoint in trend (sudden shift in baseline).
    
    Args:
        trend_data: Dictionary mapping period strings to case counts
        
    Returns:
        Dictionary with changepoint information or None
    """
    if not trend_data or len(trend_data) < 6:
        return None
    
    trend_df = pd.DataFrame(list(trend_data.items()), columns=["Period", "Count"])
    trend_df["Period"] = pd.to_datetime(trend_df["Period"], errors='coerce')
    trend_df = trend_df.sort_values("Period").reset_index(drop=True)
    
    # Simple two-segment changepoint detection
    # Try each possible split point
    best_split = None
    best_score = float('inf')
    
    for split_idx in range(2, len(trend_df) - 2):
        segment1 = trend_df.iloc[:split_idx]["Count"]
        segment2 = trend_df.iloc[split_idx:]["Count"]
        
        mean1 = segment1.mean()
        mean2 = segment2.mean()
        std1 = segment1.std() if len(segment1) > 1 else 0
        std2 = segment2.std() if len(segment2) > 1 else 0
        
        # Score: difference in means relative to combined variance
        combined_std = np.sqrt((std1**2 + std2**2) / 2) if (std1 > 0 or std2 > 0) else 1.0
        score = abs(mean2 - mean1) / combined_std if combined_std > 0 else 0
        
        if score > best_score:
            best_score = score
            best_split = {
                "split_period": trend_df.iloc[split_idx]["Period"],
                "split_period_str": trend_df.iloc[split_idx]["Period"].strftime("%Y-%m") if pd.notna(trend_df.iloc[split_idx]["Period"]) else str(trend_df.iloc[split_idx]["Period"]),
                "before_mean": float(mean1),
                "after_mean": float(mean2),
                "change_ratio": float(safe_divide(mean2, mean1, 0.0)),
                "score": float(score),
            }
    
    return best_split

