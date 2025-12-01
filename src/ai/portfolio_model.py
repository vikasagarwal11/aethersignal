"""
Portfolio Data Model (CHUNK A9.1)
Aggregates all signal intelligence across products into a single normalized structure.
This is the backbone for the Portfolio Overview Panel (A9).
"""
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime


class PortfolioModel:
    """
    Portfolio-level signal aggregation model.
    Creates standardized JSON schema that aggregates all signals across:
    - All products
    - All reactions
    - All therapeutic areas
    - All geographies
    - All governance artifacts (RPF, SCS, SHMI, Trend Alerts, Label Impact, CAPA)
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize Portfolio Model.
        
        Args:
            df: Normalized DataFrame with case data
        """
        self.df = df.copy() if df is not None else pd.DataFrame()
    
    def extract_products(self) -> List[str]:
        """Return list of distinct products/drugs in dataset."""
        if self.df.empty:
            return []
        
        # Try different column names for drug
        drug_col = next(
            (col for col in ["drug", "drug_name", "drug_normalized", "drug_concept_name"] 
             if col in self.df.columns),
            None
        )
        
        if drug_col:
            return sorted(self.df[drug_col].dropna().unique().tolist())
        
        return []
    
    def signals_by_product(self, signals: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Build portfolio structure with signals aggregated by product.
        
        Args:
            signals: Optional list of signal dictionaries from governance engine
            
        Returns:
            Dictionary mapping product names to portfolio data
        """
        products = self.extract_products()
        
        if not products:
            return {}
        
        portfolio = {}
        
        for product in products:
            # Filter DataFrame for this product
            drug_col = next(
                (col for col in ["drug", "drug_name", "drug_normalized", "drug_concept_name"] 
                 if col in self.df.columns),
                None
            )
            
            if not drug_col:
                continue
            
            product_df = self.df[self.df[drug_col].astype(str).str.lower() == product.lower()].copy()
            
            if product_df.empty:
                continue
            
            # Extract reaction column
            reaction_col = next(
                (col for col in ["reaction", "reaction_pt", "reaction_normalized", "pt", "adverse_reaction", "event"]
                 if col in product_df.columns),
                None
            )
            
            # Get signal count (unique reactions)
            signal_count = len(product_df[reaction_col].unique()) if reaction_col else 0
            
            # Get matching signals from governance
            product_signals = []
            if signals:
                for sig in signals:
                    sig_drug = sig.get("drug", "").lower()
                    if product.lower() in sig_drug or sig_drug in product.lower():
                        product_signals.append(sig)
            
            portfolio[product] = {
                "signal_count": signal_count,
                "case_count": len(product_df),
                "serious_case_rate": self._compute_serious_rate(product_df),
                "top_reactions": self._get_top_reactions(product_df, reaction_col),
                "trend_summary": self._placeholder_trend(),  # filled in A9.2
                "rpf_priority": self._extract_rpf_priority(product_signals),
                "confidence_score": self._extract_confidence_score(product_signals),
                "label_impact": self._extract_label_impact(product_signals),
                "shmi": self._extract_shmi(product_signals),
                "governance_gaps": self._extract_governance_gaps(product_signals),
                "therapeutic_area": self._extract_therapeutic_area(product_df, product_signals),
                "region_distribution": self._compute_region_distribution(product_df),
                "date_range": self._get_date_range(product_df)
            }
        
        return portfolio
    
    def _compute_serious_rate(self, df: pd.DataFrame) -> Optional[float]:
        """Compute serious case rate for a product."""
        if df.empty:
            return None
        
        serious_col = next(
            (col for col in ["serious", "seriousness", "serious_flag", "seriousness_flag"]
             if col in df.columns),
            None
        )
        
        if not serious_col:
            return None
        
        total = len(df)
        serious = df[serious_col].astype(str).str.lower().isin(["1", "yes", "y", "true", "serious"])
        serious_count = serious.sum()
        
        return round(serious_count / total, 3) if total > 0 else None
    
    def _get_top_reactions(self, df: pd.DataFrame, reaction_col: Optional[str]) -> Dict[str, int]:
        """Get top 5 reactions for a product."""
        if df.empty or not reaction_col or reaction_col not in df.columns:
            return {}
        
        top_reactions = df[reaction_col].value_counts().head(5).to_dict()
        return {str(k): int(v) for k, v in top_reactions.items()}
    
    def _placeholder_trend(self) -> Dict[str, Any]:
        """Temporary placeholder until Trend Alerts feed data (A9.2)."""
        return {
            "current_spike": None,
            "velocity": None,
            "severity": None,
            "quarterly_change": None,
            "trend_direction": None
        }
    
    def _extract_rpf_priority(self, product_signals: List[Dict[str, Any]]) -> Optional[str]:
        """Extract highest RPF priority from product signals."""
        if not product_signals:
            return None
        
        priorities = []
        for sig in product_signals:
            priority = sig.get("priority") or sig.get("qsp_priority") or sig.get("rpf_priority")
            if priority:
                priorities.append(priority)
        
        # Return highest priority
        priority_order = ["Critical", "High", "Medium", "Low"]
        for p in priority_order:
            if p in priorities:
                return p
        
        return priorities[0] if priorities else None
    
    def _extract_confidence_score(self, product_signals: List[Dict[str, Any]]) -> Optional[float]:
        """Extract average confidence score from product signals."""
        if not product_signals:
            return None
        
        scores = []
        for sig in product_signals:
            scs = sig.get("confidence_score") or sig.get("signal_confidence") or sig.get("scs")
            if scs is not None:
                scs_float = float(scs)
                # Normalize if > 1 (assume 0-100 scale)
                if scs_float > 1:
                    scs_float = scs_float / 100.0
                scores.append(scs_float)
        
        return round(sum(scores) / len(scores), 3) if scores else None
    
    def _extract_label_impact(self, product_signals: List[Dict[str, Any]]) -> Optional[str]:
        """Extract label impact status from product signals."""
        if not product_signals:
            return None
        
        for sig in product_signals:
            label_impact = sig.get("label_impact")
            if isinstance(label_impact, dict):
                if label_impact.get("should_update_label"):
                    return "High"
            elif isinstance(label_impact, str):
                if "high" in label_impact.lower() or "critical" in label_impact.lower():
                    return "High"
                elif "medium" in label_impact.lower():
                    return "Medium"
        
        return None
    
    def _extract_shmi(self, product_signals: List[Dict[str, Any]]) -> Optional[float]:
        """Extract SHMI score from product signals."""
        if not product_signals:
            return None
        
        shmi_scores = []
        for sig in product_signals:
            shmi = sig.get("shmi_score") or sig.get("shmi")
            if shmi is not None:
                shmi_scores.append(float(shmi))
        
        return round(sum(shmi_scores) / len(shmi_scores), 2) if shmi_scores else None
    
    def _extract_governance_gaps(self, product_signals: List[Dict[str, Any]]) -> Optional[int]:
        """Extract governance gap count from product signals."""
        if not product_signals:
            return None
        
        total_gaps = 0
        for sig in product_signals:
            gaps = sig.get("governance_gaps", {})
            if isinstance(gaps, dict):
                total_gaps += gaps.get("gaps_count", 0) or gaps.get("major_gaps", 0) or 0
            elif isinstance(gaps, int):
                total_gaps += gaps
        
        return total_gaps if total_gaps > 0 else None
    
    def _extract_therapeutic_area(self, df: pd.DataFrame, product_signals: List[Dict[str, Any]]) -> Optional[str]:
        """Extract therapeutic area from product data."""
        # Check signals first
        for sig in product_signals:
            ta = sig.get("therapeutic_area") or sig.get("indication")
            if ta:
                return str(ta)
        
        # Check DataFrame
        ta_col = next(
            (col for col in ["therapeutic_area", "indication", "ta"]
             if col in df.columns),
            None
        )
        
        if ta_col and not df.empty:
            tas = df[ta_col].dropna().unique()
            if len(tas) > 0:
                return str(tas[0])
        
        return None
    
    def _compute_region_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """Compute case distribution by region/country."""
        if df.empty:
            return {}
        
        region_col = next(
            (col for col in ["country", "region", "country_code", "reporting_country"]
             if col in df.columns),
            None
        )
        
        if not region_col or region_col not in df.columns:
            return {}
        
        region_counts = df[region_col].value_counts().head(10).to_dict()
        return {str(k): int(v) for k, v in region_counts.items()}
    
    def _get_date_range(self, df: pd.DataFrame) -> Optional[Dict[str, str]]:
        """Get date range for product cases."""
        if df.empty:
            return None
        
        date_col = next(
            (col for col in ["event_date", "report_date", "date", "received_date"]
             if col in df.columns),
            None
        )
        
        if not date_col or date_col not in df.columns:
            return None
        
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df_clean = df.dropna(subset=[date_col])
            
            if df_clean.empty:
                return None
            
            min_date = df_clean[date_col].min()
            max_date = df_clean[date_col].max()
            
            return {
                "start": min_date.strftime("%Y-%m-%d"),
                "end": max_date.strftime("%Y-%m-%d")
            }
        except Exception:
            return None
    
    def build_portfolio_summary(self, signals: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Build complete portfolio summary.
        
        Args:
            signals: Optional list of signal dictionaries
            
        Returns:
            Complete portfolio summary dictionary
        """
        portfolio = self.signals_by_product(signals)
        
        # Aggregate portfolio-level metrics
        total_signals = sum(p.get("signal_count", 0) for p in portfolio.values())
        total_cases = sum(p.get("case_count", 0) for p in portfolio.values())
        
        # Count products by priority
        priority_counts = {}
        for product_data in portfolio.values():
            priority = product_data.get("rpf_priority")
            if priority:
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            "portfolio": portfolio,
            "summary": {
                "total_products": len(portfolio),
                "total_signals": total_signals,
                "total_cases": total_cases,
                "priority_distribution": priority_counts,
                "generated_at": datetime.now().isoformat()
            }
        }

