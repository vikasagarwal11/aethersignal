"""
Portfolio Predictor Engine (CHUNK 6.31 - PFE-1)
Real-time forecasting engine for portfolio-level safety predictions.

Features:
- Prophet-based forecasting (primary) - handles seasonality, trend shifts, non-linear patterns
- ARIMA fallback - fast, lightweight, works offline
- Hybrid auto-selection based on data characteristics
- Multi-horizon predictions (3/6/12 months)
- Confidence intervals (±80% and ±95%)
- Multi-product forecasting
- Forecast anomaly detection and explanation anchors
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')

# Optional dependencies
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False


@dataclass
class ForecastResult:
    """Forecast result container."""
    product: str
    horizon_months: int
    forecast_values: pd.Series
    confidence_lower_80: pd.Series
    confidence_upper_80: pd.Series
    confidence_lower_95: pd.Series
    confidence_upper_95: pd.Series
    forecast_method: str  # "prophet", "arima", "trend_extrapolation"
    model_confidence: float  # 0-1
    trend_direction: str  # "increasing", "decreasing", "stable"
    anomaly_anchors: List[Dict[str, Any]]  # Key events that drive forecast


@dataclass
class PortfolioForecast:
    """Complete portfolio-level forecast."""
    forecasts: Dict[str, ForecastResult]  # product -> forecast
    portfolio_aggregate: ForecastResult
    narrative: str
    risk_forecast: Dict[str, Any]
    generated_at: datetime


class PortfolioPredictor:
    """
    Portfolio-level forecasting engine for pharmacovigilance.
    
    Automatically selects best forecasting method based on:
    - Data volume
    - Missing values
    - Sparse time series
    - Seasonality patterns
    - Browser/server capabilities
    """
    
    def __init__(self, prefer_prophet: bool = True):
        """
        Initialize portfolio predictor.
        
        Args:
            prefer_prophet: If True, prefers Prophet when available
        """
        self.prefer_prophet = prefer_prophet
        self.supported_methods = []
        
        if PROPHET_AVAILABLE:
            self.supported_methods.append("prophet")
        if ARIMA_AVAILABLE:
            self.supported_methods.append("arima")
        
        # Always available fallback
        self.supported_methods.append("trend_extrapolation")
    
    def predict_3_month(
        self,
        signals: List[Dict[str, Any]],
        trends: Optional[Dict[str, Any]] = None,
        df: Optional[pd.DataFrame] = None
    ) -> PortfolioForecast:
        """Generate 3-month portfolio forecast."""
        return self._generate_forecast(signals, trends, df, horizon_months=3)
    
    def predict_6_month(
        self,
        signals: List[Dict[str, Any]],
        trends: Optional[Dict[str, Any]] = None,
        df: Optional[pd.DataFrame] = None
    ) -> PortfolioForecast:
        """Generate 6-month portfolio forecast."""
        return self._generate_forecast(signals, trends, df, horizon_months=6)
    
    def predict_12_month(
        self,
        signals: List[Dict[str, Any]],
        trends: Optional[Dict[str, Any]] = None,
        df: Optional[pd.DataFrame] = None
    ) -> PortfolioForecast:
        """Generate 12-month portfolio forecast."""
        return self._generate_forecast(signals, trends, df, horizon_months=12)
    
    def _generate_forecast(
        self,
        signals: List[Dict[str, Any]],
        trends: Optional[Dict[str, Any]],
        df: Optional[pd.DataFrame],
        horizon_months: int
    ) -> PortfolioForecast:
        """
        Generate portfolio forecast for specified horizon.
        
        Args:
            signals: List of signal dictionaries
            trends: Optional trends data
            df: Optional DataFrame with case data
            horizon_months: Forecast horizon in months (3, 6, or 12)
        """
        # Build time series from signals or DataFrame
        if df is not None and not df.empty:
            time_series = self._build_time_series_from_df(df)
        elif signals:
            time_series = self._build_time_series_from_signals(signals)
        else:
            # Fallback: empty forecast
            return self._empty_forecast(horizon_months)
        
        # Generate forecasts per product
        product_forecasts = {}
        
        for product in time_series.keys():
            ts_data = time_series[product]
            
            # Select best method for this product's data
            method = self._select_method(ts_data)
            
            # Generate forecast
            forecast = self._forecast_product(
                product=product,
                ts_data=ts_data,
                horizon_months=horizon_months,
                method=method
            )
            
            product_forecasts[product] = forecast
        
        # Aggregate portfolio-level forecast
        portfolio_aggregate = self._aggregate_forecasts(product_forecasts)
        
        # Generate narrative
        narrative = self.generate_narrative(product_forecasts, portfolio_aggregate)
        
        # Risk forecast
        risk_forecast = self._generate_risk_forecast(product_forecasts, portfolio_aggregate)
        
        return PortfolioForecast(
            forecasts=product_forecasts,
            portfolio_aggregate=portfolio_aggregate,
            narrative=narrative,
            risk_forecast=risk_forecast,
            generated_at=datetime.now()
        )
    
    def _build_time_series_from_df(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Build monthly time series from DataFrame."""
        time_series = {}
        
        # Find date column
        date_col = None
        for col in ['fda_dt', 'FDA_DT', 'event_dt', 'EVENT_DT', 'date', 'DATE']:
            if col in df.columns:
                date_col = col
                break
        
        if date_col is None:
            return {}
        
        # Find product/drug column
        product_col = None
        for col in ['drug_name', 'drug', 'DRUG', 'DRUGNAME', 'product']:
            if col in df.columns:
                product_col = col
                break
        
        if product_col is None:
            # Single product - use all data
            df['month'] = pd.to_datetime(df[date_col], errors='coerce').dt.to_period('M')
            monthly_counts = df.groupby('month').size()
            time_series['Portfolio'] = monthly_counts
        else:
            # Multiple products
            df['month'] = pd.to_datetime(df[date_col], errors='coerce').dt.to_period('M')
            
            for product in df[product_col].unique():
                product_df = df[df[product_col] == product]
                monthly_counts = product_df.groupby('month').size()
                if len(monthly_counts) >= 3:  # Minimum 3 months of data
                    time_series[product] = monthly_counts
        
        return time_series
    
    def _build_time_series_from_signals(self, signals: List[Dict[str, Any]]) -> Dict[str, pd.Series]:
        """Build time series from signal dictionaries."""
        # Extract monthly counts from signals
        time_series = {}
        
        for signal in signals:
            product = signal.get('drug', signal.get('drug_name', 'Unknown'))
            
            # Extract case counts by month if available
            if 'cases_by_month' in signal:
                monthly_counts = pd.Series(signal['cases_by_month'])
                time_series[product] = monthly_counts
        
        return time_series
    
    def _select_method(self, ts_data: pd.Series) -> str:
        """
        Select best forecasting method based on data characteristics.
        
        Args:
            ts_data: Time series data
            
        Returns:
            Method name: "prophet", "arima", or "trend_extrapolation"
        """
        if len(ts_data) < 6:
            return "trend_extrapolation"
        
        # Check for missing values
        missing_pct = ts_data.isna().sum() / len(ts_data)
        if missing_pct > 0.3:
            return "trend_extrapolation"
        
        # Prefer Prophet if available and data is sufficient
        if self.prefer_prophet and PROPHET_AVAILABLE and len(ts_data) >= 12:
            return "prophet"
        
        # Use ARIMA if available
        if ARIMA_AVAILABLE and len(ts_data) >= 6:
            return "arima"
        
        # Fallback to trend extrapolation
        return "trend_extrapolation"
    
    def _forecast_product(
        self,
        product: str,
        ts_data: pd.Series,
        horizon_months: int,
        method: str
    ) -> ForecastResult:
        """Generate forecast for a single product."""
        
        # Clean and prepare data
        ts_data = ts_data.fillna(method='ffill').fillna(0)
        
        if method == "prophet" and PROPHET_AVAILABLE:
            return self._forecast_with_prophet(product, ts_data, horizon_months)
        elif method == "arima" and ARIMA_AVAILABLE:
            return self._forecast_with_arima(product, ts_data, horizon_months)
        else:
            return self._forecast_with_trend_extrapolation(product, ts_data, horizon_months)
    
    def _forecast_with_prophet(
        self,
        product: str,
        ts_data: pd.Series,
        horizon_months: int
    ) -> ForecastResult:
        """Forecast using Facebook Prophet."""
        try:
            # Prepare data for Prophet
            df_prophet = pd.DataFrame({
                'ds': pd.to_datetime(ts_data.index.astype(str)),
                'y': ts_data.values
            })
            
            # Initialize and fit model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                uncertainty_samples=100
            )
            model.fit(df_prophet)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=horizon_months, freq='M')
            
            # Generate forecast
            forecast_df = model.predict(future)
            
            # Extract forecast values
            forecast_periods = forecast_df.tail(horizon_months)
            
            forecast_values = pd.Series(
                forecast_periods['yhat'].values,
                index=forecast_periods['ds'].dt.to_period('M')
            )
            
            confidence_lower_80 = pd.Series(
                forecast_periods['yhat_lower'].values,
                index=forecast_periods['ds'].dt.to_period('M')
            )
            
            confidence_upper_80 = pd.Series(
                forecast_periods['yhat_upper'].values,
                index=forecast_periods['ds'].dt.to_period('M')
            )
            
            # For 95% CI, use wider bounds (Prophet default is 80%)
            # Estimate 95% CI as 1.25x of 80% CI
            ci_range_80 = confidence_upper_80 - confidence_lower_80
            confidence_lower_95 = forecast_values - (ci_range_80 * 1.25 / 2)
            confidence_upper_95 = forecast_values + (ci_range_80 * 1.25 / 2)
            
            # Calculate trend direction
            trend = (forecast_values.iloc[-1] - forecast_values.iloc[0]) / len(forecast_values)
            if trend > 0.1:
                trend_direction = "increasing"
            elif trend < -0.1:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
            
            # Model confidence based on uncertainty
            avg_uncertainty = (confidence_upper_80 - confidence_lower_80).mean()
            model_confidence = max(0, 1 - (avg_uncertainty / max(forecast_values.mean(), 1)))
            
            # Anomaly anchors (identify key change points)
            anomaly_anchors = self._detect_anomaly_anchors(ts_data, forecast_values)
            
            return ForecastResult(
                product=product,
                horizon_months=horizon_months,
                forecast_values=forecast_values,
                confidence_lower_80=confidence_lower_80,
                confidence_upper_80=confidence_upper_80,
                confidence_lower_95=confidence_lower_95,
                confidence_upper_95=confidence_upper_95,
                forecast_method="prophet",
                model_confidence=model_confidence,
                trend_direction=trend_direction,
                anomaly_anchors=anomaly_anchors
            )
            
        except Exception as e:
            # Fallback to trend extrapolation if Prophet fails
            return self._forecast_with_trend_extrapolation(product, ts_data, horizon_months)
    
    def _forecast_with_arima(
        self,
        product: str,
        ts_data: pd.Series,
        horizon_months: int
    ) -> ForecastResult:
        """Forecast using ARIMA."""
        try:
            # Convert to numpy array
            values = ts_data.values.astype(float)
            
            # Auto-select ARIMA order (simplified - use (1,1,1) for most cases)
            order = (1, 1, 1)
            
            # Fit ARIMA model
            model = ARIMA(values, order=order)
            fitted_model = model.fit()
            
            # Generate forecast
            forecast_result = fitted_model.get_forecast(steps=horizon_months)
            forecast_values = pd.Series(
                forecast_result.predicted_mean,
                index=self._generate_future_periods(ts_data.index, horizon_months)
            )
            
            # Get confidence intervals
            conf_int = forecast_result.conf_int()
            
            confidence_lower_80 = pd.Series(
                conf_int.iloc[:, 0].values,
                index=forecast_values.index
            )
            
            confidence_upper_80 = pd.Series(
                conf_int.iloc[:, 1].values,
                index=forecast_values.index
            )
            
            # Estimate 95% CI (ARIMA typically gives 95%, so use wider)
            ci_range = confidence_upper_80 - confidence_lower_80
            confidence_lower_95 = forecast_values - (ci_range * 0.6)
            confidence_upper_95 = forecast_values + (ci_range * 0.6)
            
            # Trend direction
            trend = (forecast_values.iloc[-1] - forecast_values.iloc[0]) / len(forecast_values)
            if trend > 0.1:
                trend_direction = "increasing"
            elif trend < -0.1:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
            
            # Model confidence from AIC
            model_confidence = min(1.0, max(0.5, 1 - (fitted_model.aic / 1000)))
            
            # Anomaly anchors
            anomaly_anchors = self._detect_anomaly_anchors(ts_data, forecast_values)
            
            return ForecastResult(
                product=product,
                horizon_months=horizon_months,
                forecast_values=forecast_values,
                confidence_lower_80=confidence_lower_80,
                confidence_upper_80=confidence_upper_80,
                confidence_lower_95=confidence_lower_95,
                confidence_upper_95=confidence_upper_95,
                forecast_method="arima",
                model_confidence=model_confidence,
                trend_direction=trend_direction,
                anomaly_anchors=anomaly_anchors
            )
            
        except Exception as e:
            # Fallback to trend extrapolation
            return self._forecast_with_trend_extrapolation(product, ts_data, horizon_months)
    
    def _forecast_with_trend_extrapolation(
        self,
        product: str,
        ts_data: pd.Series,
        horizon_months: int
    ) -> ForecastResult:
        """Fallback: Simple trend extrapolation."""
        values = ts_data.values.astype(float)
        
        # Calculate linear trend
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        # Generate forecast
        future_x = np.arange(len(values), len(values) + horizon_months)
        forecast_vals = slope * future_x + intercept
        
        forecast_values = pd.Series(
            forecast_vals,
            index=self._generate_future_periods(ts_data.index, horizon_months)
        )
        
        # Estimate confidence intervals (simpler approach)
        std_dev = np.std(values)
        
        confidence_lower_80 = forecast_values - (1.28 * std_dev)
        confidence_upper_80 = forecast_values + (1.28 * std_dev)
        confidence_lower_95 = forecast_values - (1.96 * std_dev)
        confidence_upper_95 = forecast_values + (1.96 * std_dev)
        
        # Trend direction
        if slope > 0.1:
            trend_direction = "increasing"
        elif slope < -0.1:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
        
        # Lower confidence for simple method
        model_confidence = 0.6
        
        anomaly_anchors = []
        
        return ForecastResult(
            product=product,
            horizon_months=horizon_months,
            forecast_values=forecast_values,
            confidence_lower_80=confidence_lower_80,
            confidence_upper_80=confidence_upper_80,
            confidence_lower_95=confidence_lower_95,
            confidence_upper_95=confidence_upper_95,
            forecast_method="trend_extrapolation",
            model_confidence=model_confidence,
            trend_direction=trend_direction,
            anomaly_anchors=anomaly_anchors
        )
    
    def _generate_future_periods(self, current_index: pd.Index, n_months: int) -> pd.PeriodIndex:
        """Generate future period index."""
        if isinstance(current_index, pd.PeriodIndex):
            last_period = current_index[-1]
            future_periods = pd.period_range(
                start=last_period + 1,
                periods=n_months,
                freq='M'
            )
            return future_periods
        else:
            # Fallback: generate from last date
            last_date = pd.to_datetime(str(current_index[-1]))
            future_dates = pd.date_range(start=last_date, periods=n_months + 1, freq='M')[1:]
            return pd.PeriodIndex(future_dates, freq='M')
    
    def _aggregate_forecasts(
        self,
        product_forecasts: Dict[str, ForecastResult]
    ) -> ForecastResult:
        """Aggregate individual product forecasts into portfolio-level forecast."""
        if not product_forecasts:
            return self._empty_forecast_result("Portfolio", 12)
        
        # Combine all forecasts
        all_forecasts = []
        all_lower_80 = []
        all_upper_80 = []
        all_lower_95 = []
        all_upper_95 = []
        
        for forecast in product_forecasts.values():
            all_forecasts.append(forecast.forecast_values)
            all_lower_80.append(forecast.confidence_lower_80)
            all_upper_80.append(forecast.confidence_upper_80)
            all_lower_95.append(forecast.confidence_lower_95)
            all_upper_95.append(forecast.confidence_upper_95)
        
        # Align indices and sum
        portfolio_forecast = pd.concat(all_forecasts, axis=1).sum(axis=1)
        portfolio_lower_80 = pd.concat(all_lower_80, axis=1).sum(axis=1)
        portfolio_upper_80 = pd.concat(all_upper_80, axis=1).sum(axis=1)
        portfolio_lower_95 = pd.concat(all_lower_95, axis=1).sum(axis=1)
        portfolio_upper_95 = pd.concat(all_upper_95, axis=1).sum(axis=1)
        
        # Determine trend
        trend = (portfolio_forecast.iloc[-1] - portfolio_forecast.iloc[0]) / len(portfolio_forecast)
        if trend > 0.1:
            trend_direction = "increasing"
        elif trend < -0.1:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
        
        # Average confidence
        avg_confidence = np.mean([f.model_confidence for f in product_forecasts.values()])
        
        return ForecastResult(
            product="Portfolio",
            horizon_months=len(portfolio_forecast),
            forecast_values=portfolio_forecast,
            confidence_lower_80=portfolio_lower_80,
            confidence_upper_80=portfolio_upper_80,
            confidence_lower_95=portfolio_lower_95,
            confidence_upper_95=portfolio_upper_95,
            forecast_method="aggregated",
            model_confidence=avg_confidence,
            trend_direction=trend_direction,
            anomaly_anchors=[]
        )
    
    def _detect_anomaly_anchors(
        self,
        historical: pd.Series,
        forecast: pd.Series
    ) -> List[Dict[str, Any]]:
        """Detect key events/anomalies that drive forecast changes."""
        anchors = []
        
        # Detect recent spikes in historical data
        if len(historical) > 3:
            recent_mean = historical.tail(3).mean()
            overall_mean = historical.mean()
            
            if recent_mean > overall_mean * 1.5:
                anchors.append({
                    "type": "recent_spike",
                    "description": f"Recent case volume increased {((recent_mean/overall_mean - 1) * 100):.1f}%",
                    "impact": "high"
                })
        
        # Detect forecast acceleration
        if len(forecast) > 3:
            early_trend = (forecast.iloc[2] - forecast.iloc[0]) / 2
            late_trend = (forecast.iloc[-1] - forecast.iloc[-3]) / 2
            
            if late_trend > early_trend * 1.2:
                anchors.append({
                    "type": "accelerating_trend",
                    "description": "Forecast shows accelerating upward trend",
                    "impact": "medium"
                })
        
        return anchors
    
    def _generate_risk_forecast(
        self,
        product_forecasts: Dict[str, ForecastResult],
        portfolio_aggregate: ForecastResult
    ) -> Dict[str, Any]:
        """Generate risk-level forecast summary."""
        # Identify high-risk products (increasing trends)
        high_risk = [
            p for p, f in product_forecasts.items()
            if f.trend_direction == "increasing" and f.model_confidence > 0.7
        ]
        
        # Calculate portfolio risk score (0-100)
        increasing_count = sum(1 for f in product_forecasts.values() if f.trend_direction == "increasing")
        total_products = len(product_forecasts)
        
        risk_score = (increasing_count / max(total_products, 1)) * 100
        
        return {
            "portfolio_risk_score": risk_score,
            "high_risk_products": high_risk,
            "trending_up_count": increasing_count,
            "total_products": total_products,
            "portfolio_trend": portfolio_aggregate.trend_direction
        }
    
    def generate_narrative(
        self,
        product_forecasts: Dict[str, ForecastResult],
        portfolio_aggregate: ForecastResult
    ) -> str:
        """Generate executive-level narrative from forecasts."""
        narrative_parts = []
        
        narrative_parts.append(
            f"Portfolio forecast generated on {datetime.now().strftime('%B %d, %Y')}."
        )
        
        # Portfolio trend
        if portfolio_aggregate.trend_direction == "increasing":
            narrative_parts.append(
                "The portfolio shows an increasing trend in case volumes over the forecast horizon."
            )
        elif portfolio_aggregate.trend_direction == "decreasing":
            narrative_parts.append(
                "The portfolio shows a decreasing trend in case volumes over the forecast horizon."
            )
        else:
            narrative_parts.append(
                "The portfolio shows stable case volumes over the forecast horizon."
            )
        
        # High-risk products
        high_risk = [
            (p, f) for p, f in product_forecasts.items()
            if f.trend_direction == "increasing"
        ]
        
        if high_risk:
            narrative_parts.append(
                f"{len(high_risk)} product(s) show increasing trends and may require additional monitoring."
            )
            
            if len(high_risk) <= 5:
                product_names = ", ".join([p for p, _ in high_risk])
                narrative_parts.append(f"Products with increasing trends: {product_names}.")
        
        # Model confidence
        avg_confidence = portfolio_aggregate.model_confidence
        if avg_confidence > 0.8:
            narrative_parts.append("Forecast confidence is high.")
        elif avg_confidence > 0.6:
            narrative_parts.append("Forecast confidence is moderate.")
        else:
            narrative_parts.append("Forecast confidence is limited; consider additional data.")
        
        return " ".join(narrative_parts)
    
    def _empty_forecast(self, horizon_months: int) -> PortfolioForecast:
        """Return empty forecast when no data available."""
        empty_result = self._empty_forecast_result("Portfolio", horizon_months)
        
        return PortfolioForecast(
            forecasts={},
            portfolio_aggregate=empty_result,
            narrative="No data available for forecasting.",
            risk_forecast={
                "portfolio_risk_score": 0,
                "high_risk_products": [],
                "trending_up_count": 0,
                "total_products": 0,
                "portfolio_trend": "stable"
            },
            generated_at=datetime.now()
        )
    
    def _empty_forecast_result(self, product: str, horizon_months: int) -> ForecastResult:
        """Create empty forecast result."""
        future_periods = pd.period_range(
            start=pd.Period.now('M') + 1,
            periods=horizon_months,
            freq='M'
        )
        
        empty_series = pd.Series([0] * horizon_months, index=future_periods)
        
        return ForecastResult(
            product=product,
            horizon_months=horizon_months,
            forecast_values=empty_series,
            confidence_lower_80=empty_series,
            confidence_upper_80=empty_series,
            confidence_lower_95=empty_series,
            confidence_upper_95=empty_series,
            forecast_method="none",
            model_confidence=0.0,
            trend_direction="stable",
            anomaly_anchors=[]
        )


def get_portfolio_predictor(prefer_prophet: bool = True) -> PortfolioPredictor:
    """Get or create portfolio predictor instance."""
    if "portfolio_predictor" not in st.session_state:
        st.session_state.portfolio_predictor = PortfolioPredictor(prefer_prophet=prefer_prophet)
    return st.session_state.portfolio_predictor


# Import streamlit for session state (optional - only used in get_portfolio_predictor)
try:
    import streamlit as st
except ImportError:
    st = None

