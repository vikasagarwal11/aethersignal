"""
Quantum-inspired anomaly detection for AetherSignal.

This module provides heuristic anomaly scoring for time series derived
from safety data (e.g., monthly case counts). It combines classical
z-scores with a curvature-based "quantum potential" term inspired by
wave mechanics. The implementation is deterministic and simulator-based.
"""

from __future__ import annotations

from typing import Dict, Any

import numpy as np
import pandas as pd

from src.utils import safe_divide


def score_time_series(trend_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute anomaly scores for a time series of counts.

    Expects a dataframe with columns:
        - Period: datetime-like
        - Count: numeric

    Returns:
        DataFrame with additional columns:
            - z_score
            - curvature
            - anomaly_score
    """
    if trend_df is None or len(trend_df) < 5:
        return trend_df

    df = trend_df.copy().reset_index(drop=True)
    counts = df["Count"].astype(float).values

    # Rolling mean/std for z-score (window=5)
    series = pd.Series(counts)
    rolling_mean = series.rolling(window=5, min_periods=3, center=True).mean()
    rolling_std = series.rolling(window=5, min_periods=3, center=True).std()

    # Fall back to global mean/std if rolling fails
    global_mean = float(np.mean(counts))
    global_std = float(np.std(counts)) or 1.0

    mean = rolling_mean.fillna(global_mean).values
    std = rolling_std.fillna(global_std).replace(0, global_std).values

    z = safe_divide(counts - mean, std, 0.0)

    # Normalize counts to [0,1] and compute discrete second derivative
    min_c = float(np.min(counts))
    max_c = float(np.max(counts))
    if max_c > min_c:
        norm = (counts - min_c) / (max_c - min_c)
    else:
        norm = np.zeros_like(counts)

    curvature = np.zeros_like(norm)
    # Discrete Laplacian-like operator
    for i in range(1, len(norm) - 1):
        curvature[i] = norm[i + 1] - 2 * norm[i] + norm[i - 1]

    # Combine into anomaly score (higher = more anomalous)
    # 70% from |z|, 30% from curvature magnitude
    anomaly_score = 0.7 * np.abs(z) + 0.3 * np.abs(curvature) * 10.0

    df["z_score"] = z
    df["curvature"] = curvature
    df["anomaly_score"] = anomaly_score
    return df


def detect_time_anomalies(
    trend_df: pd.DataFrame,
    score_threshold: float = 2.5,
) -> pd.DataFrame:
    """
    Detect anomalous periods in a time trend using the quantum-inspired score.

    Args:
        trend_df: DataFrame with Period and Count
        score_threshold: Minimum anomaly_score to flag an anomaly

    Returns:
        DataFrame of anomalous periods sorted by anomaly_score descending
    """
    if trend_df is None or len(trend_df) < 5:
        return pd.DataFrame(columns=["Period", "Count", "z_score", "curvature", "anomaly_score"])

    scored = score_time_series(trend_df)
    anomalies = scored[scored["anomaly_score"] >= score_threshold].copy()
    if anomalies.empty:
        return anomalies

    anomalies = anomalies.sort_values("anomaly_score", ascending=False)
    return anomalies

