"""
Portfolio Trends Engine (CHUNK A9.2 - Step 1)
Detects portfolio-level rising reactions, class-effect spikes, and multi-product emerging risks.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime

try:
    from scipy.stats import linregress
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class PortfolioTrendEngine:
    """
    Portfolio-level trend detection engine.
    
    Detects:
    - Portfolio-wide volume trends
    - Cross-product reaction spikes
    - Class-effect emerging risks
    - Multi-product reaction emergence
    - Top rising reactions across portfolio
    """
    
    def __init__(self):
        """Initialize Portfolio Trend Engine."""
        pass
    
    def combine_all_products(self, product_data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Merge all uploaded product datasets into one portfolio dataframe.
        
        Args:
            product_data_dict: Dictionary mapping product names to DataFrames
                Example: {"ProductA": pd.DataFrame, "ProductB": pd.DataFrame, ...}
        
        Returns:
            Combined portfolio DataFrame with 'product' column added
        """
        merged = []
        
        for product_name, df in product_data_dict.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                temp = df.copy()
                temp["product"] = product_name
                merged.append(temp)
        
        if not merged:
            return pd.DataFrame()
        
        return pd.concat(merged, ignore_index=True)
    
    def compute_cross_product_trends(self, portfolio_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect portfolio-level rising reactions, class-effect spikes, and multi-product emerging risks.
        
        Args:
            portfolio_df: Combined portfolio DataFrame with 'product' column
        
        Returns:
            Dictionary with portfolio trend analysis results
        """
        results = {
            "portfolio_volume": {},
            "top_rising_reactions": [],
            "cross_product_spikes": [],
            "class_effect_emerging": [],
            "multi_product_emerging": []
        }
        
        if portfolio_df.empty:
            return results
        
        # Extract date column
        date_col = next(
            (col for col in ["event_date", "event_dt", "report_date", "date", "received_date"]
             if col in portfolio_df.columns),
            None
        )
        
        if not date_col:
            return results
        
        # Extract reaction column
        reaction_col = next(
            (col for col in ["reaction", "reaction_pt", "pt", "reaction_normalized", "adverse_reaction", "event"]
             if col in portfolio_df.columns),
            None
        )
        
        if not reaction_col:
            return results
        
        try:
            # Convert date column to datetime
            portfolio_df[date_col] = pd.to_datetime(portfolio_df[date_col], errors='coerce')
            portfolio_df = portfolio_df.dropna(subset=[date_col])
            
            if portfolio_df.empty:
                return results
            
            # Create year-quarter column
            portfolio_df["year_quarter"] = portfolio_df[date_col].dt.to_period("Q").astype(str)
            
            # ----------------------------------------------------------
            # 1) Portfolio-level case volume trend per quarter
            # ----------------------------------------------------------
            vol = portfolio_df.groupby("year_quarter").size()
            results["portfolio_volume"] = {str(k): int(v) for k, v in vol.to_dict().items()}
            
            # ----------------------------------------------------------
            # 2) Top rising reactions (slope in last N quarters)
            # ----------------------------------------------------------
            if SCIPY_AVAILABLE:
                reac_trend = (
                    portfolio_df.groupby(["year_quarter", reaction_col])
                    .size()
                    .reset_index(name="count")
                )
                
                reactions = []
                
                for reaction in reac_trend[reaction_col].unique():
                    temp = reac_trend[reac_trend[reaction_col] == reaction].copy()
                    
                    if len(temp) >= 2:
                        temp = temp.sort_values("year_quarter")
                        x = np.arange(len(temp))
                        y = temp["count"].values
                        
                        try:
                            slope, intercept, r, p, stderr = linregress(x, y)
                            reactions.append({
                                "reaction": str(reaction),
                                "slope": float(slope),
                                "r_squared": float(r**2),
                                "p_value": float(p),
                                "trend_direction": "rising" if slope > 0 else "declining"
                            })
                        except Exception:
                            pass
                
                # Sort by slope (descending)
                reactions_sorted = sorted(reactions, key=lambda x: x["slope"], reverse=True)
                results["top_rising_reactions"] = reactions_sorted[:10]
            else:
                # Fallback: simple count-based ranking
                reaction_counts = portfolio_df[reaction_col].value_counts().head(10)
                results["top_rising_reactions"] = [
                    {"reaction": str(r), "slope": float(c), "trend_direction": "unknown"}
                    for r, c in reaction_counts.items()
                ]
            
            # ----------------------------------------------------------
            # 3) Cross-product spikes (same reaction in ≥3 products)
            # ----------------------------------------------------------
            spike_map = defaultdict(lambda: defaultdict(int))
            
            for _, row in portfolio_df.iterrows():
                reaction = str(row[reaction_col])
                product = str(row.get("product", "Unknown"))
                spike_map[reaction][product] += 1
            
            cross_spikes = []
            for reaction, product_map in spike_map.items():
                if len(product_map) >= 3:
                    cross_spikes.append({
                        "reaction": reaction,
                        "product_count": len(product_map),
                        "products": list(product_map.keys()),
                        "total_cases": sum(product_map.values())
                    })
            
            # Sort by product_count and total_cases
            cross_spikes_sorted = sorted(
                cross_spikes,
                key=lambda x: (x["product_count"], x["total_cases"]),
                reverse=True
            )
            results["cross_product_spikes"] = cross_spikes_sorted[:10]
            
            # ----------------------------------------------------------
            # 4) Class-effect emerging trends (rising across a class)
            # ----------------------------------------------------------
            class_col = next(
                (col for col in ["drug_class", "class", "therapeutic_class"]
                 if col in portfolio_df.columns),
                None
            )
            
            if class_col and SCIPY_AVAILABLE:
                class_trend = (
                    portfolio_df.groupby(["year_quarter", class_col])
                    .size()
                    .reset_index(name="count")
                )
                
                class_results = []
                
                for drug_class in class_trend[class_col].unique():
                    temp = class_trend[class_trend[class_col] == drug_class].copy()
                    
                    if len(temp) >= 3:
                        temp = temp.sort_values("year_quarter")
                        x = np.arange(len(temp))
                        y = temp["count"].values
                        
                        try:
                            slope, _, _, _, _ = linregress(x, y)
                            class_results.append({
                                "drug_class": str(drug_class),
                                "slope": float(slope),
                                "trend_direction": "rising" if slope > 0 else "declining"
                            })
                        except Exception:
                            pass
                
                # Sort by slope
                rising_classes = sorted(class_results, key=lambda x: x["slope"], reverse=True)
                results["class_effect_emerging"] = rising_classes[:10]
            
            # ----------------------------------------------------------
            # 5) Multi-product emerging risks (same PT in exactly 2 products)
            # ----------------------------------------------------------
            multi_product = []
            
            for reaction, product_map in spike_map.items():
                if len(product_map) == 2:
                    multi_product.append({
                        "reaction": reaction,
                        "products": list(product_map.keys()),
                        "total_cases": sum(product_map.values())
                    })
            
            # Sort by total_cases
            multi_product_sorted = sorted(multi_product, key=lambda x: x["total_cases"], reverse=True)
            results["multi_product_emerging"] = multi_product_sorted[:10]
            
        except Exception as e:
            # Return partial results if error occurs
            results["error"] = str(e)
        
        return results
    
    def detect_portfolio_spikes(
        self,
        portfolio_df: pd.DataFrame,
        window_months: int = 3,
        threshold_multiplier: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect sudden spikes in portfolio-level signals.
        
        Args:
            portfolio_df: Combined portfolio DataFrame
            window_months: Time window in months for spike detection
            threshold_multiplier: Multiplier for baseline (e.g., 2.0 = 2× baseline)
        
        Returns:
            List of detected spikes
        """
        spikes = []
        
        if portfolio_df.empty:
            return spikes
        
        # Extract date and reaction columns
        date_col = next(
            (col for col in ["event_date", "event_dt", "report_date", "date"]
             if col in portfolio_df.columns),
            None
        )
        reaction_col = next(
            (col for col in ["reaction", "reaction_pt", "pt", "adverse_reaction"]
             if col in portfolio_df.columns),
            None
        )
        
        if not date_col or not reaction_col:
            return spikes
        
        try:
            portfolio_df[date_col] = pd.to_datetime(portfolio_df[date_col], errors='coerce')
            portfolio_df = portfolio_df.dropna(subset=[date_col])
            
            # Group by month and reaction
            portfolio_df["year_month"] = portfolio_df[date_col].dt.to_period("M").astype(str)
            
            monthly_reaction_counts = (
                portfolio_df.groupby(["year_month", reaction_col])
                .size()
                .reset_index(name="count")
            )
            
            for reaction in monthly_reaction_counts[reaction_col].unique():
                reaction_data = monthly_reaction_counts[
                    monthly_reaction_counts[reaction_col] == reaction
                ].sort_values("year_month")
                
                if len(reaction_data) >= window_months + 1:
                    # Calculate baseline (average of previous months)
                    baseline = reaction_data.iloc[:-1]["count"].mean()
                    
                    # Check latest month
                    latest_count = reaction_data.iloc[-1]["count"]
                    
                    if baseline > 0 and latest_count >= baseline * threshold_multiplier:
                        spikes.append({
                            "reaction": str(reaction),
                            "baseline_avg": float(baseline),
                            "spike_count": int(latest_count),
                            "spike_factor": float(latest_count / baseline),
                            "month": reaction_data.iloc[-1]["year_month"]
                        })
            
            # Sort by spike factor
            spikes_sorted = sorted(spikes, key=lambda x: x["spike_factor"], reverse=True)
            return spikes_sorted[:20]  # Top 20 spikes
            
        except Exception:
            return spikes

