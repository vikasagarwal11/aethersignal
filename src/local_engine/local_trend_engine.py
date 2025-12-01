"""
Local Trend Engine (CHUNK 7.10)
Browser-based trend analysis for offline/local processing.

Runs entirely in browser when in Local Mode, providing:
- Cross-sectional trend deltas
- Moving averages
- 12-month change detection
- Spike detection
- Emerging pattern detection
- Stability scoring
"""
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import math


# Check for pandas availability
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class LocalTrendEngine:
    """
    Local trend analysis engine for browser-based processing.
    
    Provides FDA-grade trend detection without server dependencies.
    """
    
    def __init__(self, window_months: int = 12):
        """
        Initialize local trend engine.
        
        Args:
            window_months: Moving average window in months
        """
        self.window_months = window_months
    
    def analyze_trends(
        self,
        data: Any,
        date_column: str = "fda_dt",
        count_column: str = "count"
    ) -> Dict[str, Any]:
        """
        Analyze trends in case data.
        
        Args:
            data: DataFrame or list of dicts with case records
            date_column: Column name for dates
            count_column: Column name for case counts (if aggregated)
            
        Returns:
            Dictionary with trend analysis results
        """
        # Convert to DataFrame if needed
        if not PANDAS_AVAILABLE:
            return self._analyze_lightweight(data, date_column)
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            return {"error": "Unsupported data type"}
        
        if df.empty:
            return {"error": "Empty dataset"}
        
        # Find date column
        date_col = self._find_column(df, [date_column, "FDA_DT", "fda_dt", "date", "DATE"])
        
        if not date_col:
            return {"error": "Date column not found"}
        
        # Convert dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        
        # Group by month
        df['year_month'] = df[date_col].dt.to_period('M')
        monthly = df.groupby('year_month').size().reset_index(name='count')
        monthly['year_month'] = monthly['year_month'].astype(str)
        
        # Calculate trends
        results = {
            "monthly_counts": monthly.to_dict('records'),
            "moving_average": self._calculate_moving_average(monthly['count'].values),
            "month_over_month": self._calculate_mom_change(monthly['count'].values),
            "year_over_year": self._calculate_yoy_change(monthly),
            "spikes": self._detect_spikes(monthly['count'].values, monthly['year_month'].values),
            "emerging_patterns": self._detect_emerging_patterns(monthly),
            "stability_score": self._calculate_stability_score(monthly['count'].values),
            "trend_direction": self._calculate_trend_direction(monthly['count'].values),
        }
        
        return results
    
    def _calculate_moving_average(self, values: List[float], window: int = 3) -> List[float]:
        """Calculate moving average."""
        if not PANDAS_AVAILABLE:
            # Lightweight implementation
            ma = []
            for i in range(len(values)):
                window_values = values[max(0, i - window + 1):i + 1]
                ma.append(sum(window_values) / len(window_values))
            return ma
        
        series = pd.Series(values)
        return series.rolling(window=window, min_periods=1).mean().tolist()
    
    def _calculate_mom_change(self, values: List[float]) -> List[Optional[float]]:
        """Calculate month-over-month percentage change."""
        changes = [None]
        for i in range(1, len(values)):
            if values[i-1] > 0:
                change = ((values[i] - values[i-1]) / values[i-1]) * 100
                changes.append(change)
            else:
                changes.append(None)
        return changes
    
    def _calculate_yoy_change(self, monthly: pd.DataFrame) -> List[Optional[float]]:
        """Calculate year-over-year percentage change."""
        yoy = []
        for idx, row in monthly.iterrows():
            year_ago = monthly[
                monthly['year_month'] == self._get_year_ago_period(row['year_month'])
            ]
            if not year_ago.empty:
                current = row['count']
                past = year_ago.iloc[0]['count']
                if past > 0:
                    change = ((current - past) / past) * 100
                    yoy.append(change)
                else:
                    yoy.append(None)
            else:
                yoy.append(None)
        return yoy
    
    def _detect_spikes(
        self,
        values: List[float],
        periods: List[str],
        threshold: float = 1.5
    ) -> List[Dict[str, Any]]:
        """Detect spikes (sudden increases)."""
        spikes = []
        
        if len(values) < 2:
            return spikes
        
        ma = self._calculate_moving_average(values, window=3)
        
        for i in range(1, len(values)):
            if ma[i-1] > 0:
                ratio = values[i] / ma[i-1]
                if ratio >= threshold:
                    spikes.append({
                        "period": periods[i],
                        "value": values[i],
                        "moving_avg": ma[i-1],
                        "spike_factor": ratio,
                        "severity": "high" if ratio >= 2.0 else "medium"
                    })
        
        return spikes
    
    def _detect_emerging_patterns(self, monthly: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect emerging patterns (sustained increases)."""
        patterns = []
        
        if len(monthly) < 3:
            return patterns
        
        values = monthly['count'].values
        
        # Check for 3+ consecutive increases
        consecutive_increases = 0
        start_period = None
        
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                consecutive_increases += 1
                if start_period is None:
                    start_period = monthly.iloc[i-1]['year_month']
            else:
                if consecutive_increases >= 3:
                    patterns.append({
                        "type": "emerging_increase",
                        "start_period": str(start_period),
                        "end_period": str(monthly.iloc[i-1]['year_month']),
                        "consecutive_months": consecutive_increases,
                        "total_increase": ((values[i-1] - values[i-consecutive_increases-1]) / values[i-consecutive_increases-1]) * 100 if i-consecutive_increases-1 >= 0 else 0
                    })
                consecutive_increases = 0
                start_period = None
        
        return patterns
    
    def _calculate_stability_score(self, values: List[float]) -> float:
        """Calculate stability score (0-1, higher = more stable)."""
        if len(values) < 2:
            return 1.0
        
        if not PANDAS_AVAILABLE:
            # Lightweight: use coefficient of variation
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = math.sqrt(variance)
            cv = std_dev / mean if mean > 0 else 0
            return max(0.0, 1.0 - min(1.0, cv))
        
        series = pd.Series(values)
        cv = series.std() / series.mean() if series.mean() > 0 else 0
        return max(0.0, 1.0 - min(1.0, cv))
    
    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate overall trend direction."""
        if len(values) < 2:
            return "stable"
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _get_year_ago_period(self, period: str) -> str:
        """Get period from one year ago."""
        try:
            year, month = period.split('-')
            year_ago = int(year) - 1
            return f"{year_ago}-{month}"
        except Exception:
            return period
    
    def _find_column(self, df: Any, possible_names: List[str]) -> Optional[str]:
        """Find column by possible names."""
        if not PANDAS_AVAILABLE or not isinstance(df, pd.DataFrame):
            return None
        
        for name in possible_names:
            if name in df.columns:
                return name
        return None
    
    def _analyze_lightweight(self, data: List[Dict[str, Any]], date_column: str) -> Dict[str, Any]:
        """Lightweight trend analysis for list-of-dicts."""
        # Group by month (lightweight)
        monthly_counts = defaultdict(int)
        
        for record in data:
            date_val = record.get(date_column) or record.get("fda_dt") or record.get("FDA_DT")
            if date_val:
                try:
                    # Extract year-month
                    if isinstance(date_val, str):
                        year_month = date_val[:7]  # YYYY-MM
                        monthly_counts[year_month] += 1
                except Exception:
                    continue
        
        # Convert to sorted list
        sorted_months = sorted(monthly_counts.keys())
        values = [monthly_counts[m] for m in sorted_months]
        
        return {
            "monthly_counts": [{"year_month": m, "count": monthly_counts[m]} for m in sorted_months],
            "moving_average": self._calculate_moving_average(values),
            "spikes": self._detect_spikes(values, sorted_months),
            "stability_score": self._calculate_stability_score(values),
            "trend_direction": self._calculate_trend_direction(values),
        }

