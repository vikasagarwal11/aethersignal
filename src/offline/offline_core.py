"""
Offline Core Engine (CHUNK 7.7 - Part A)
Core offline processing engine using Pyodide for browser-based computation.
"""
from typing import Dict, Any, Optional
import json

# Pyodide imports will be available when running in browser
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class OfflineCore:
    """
    Core offline processing engine.
    
    Handles:
    - Dataset loading in browser
    - Local computation
    - Result caching
    - Offline mode detection
    """
    
    def __init__(self):
        """Initialize Offline Core."""
        self.ready = False
        self.df = None
        self.cache = {}
    
    def load_dataset(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load dataset from dictionary (converted from CSV/FAERS).
        
        Args:
            data_dict: Dictionary containing data (from JSON or direct dict)
            
        Returns:
            Dictionary with load status
        """
        try:
            if not PANDAS_AVAILABLE:
                return {
                    "success": False,
                    "error": "Pandas not available in offline mode"
                }
            
            # Convert dict to DataFrame
            self.df = pd.DataFrame(data_dict)
            
            return {
                "success": True,
                "rows": len(self.df),
                "cols": len(self.df.columns),
                "columns": list(self.df.columns)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_dataframe(self) -> Optional[Any]:
        """Get loaded DataFrame."""
        return self.df
    
    def is_ready(self) -> bool:
        """Check if offline core is ready."""
        return self.ready and self.df is not None
    
    def compute_risk_metrics(self, drug: str, reaction: str) -> Dict[str, Any]:
        """
        Compute basic risk metrics offline.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            
        Returns:
            Dictionary with risk metrics
        """
        if not self.is_ready():
            return {"error": "Data not loaded"}
        
        try:
            # Find columns
            drug_col = self._find_column(self.df, ["drug", "drug_name"])
            reaction_col = self._find_column(self.df, ["reaction", "reaction_pt"])
            
            if not drug_col or not reaction_col:
                return {"error": "Columns not found"}
            
            # Filter data
            drug_mask = self.df[drug_col].astype(str).str.contains(drug, case=False, na=False)
            reaction_mask = self.df[reaction_col].astype(str).str.contains(reaction, case=False, na=False)
            
            exposed_cases = self.df[drug_mask & reaction_mask]
            total_exposed = self.df[drug_mask]
            total_reaction = self.df[reaction_mask]
            
            # Compute metrics
            risk_exposed = len(exposed_cases) / len(total_exposed) if len(total_exposed) > 0 else 0
            risk_unexposed = len(total_reaction) - len(exposed_cases)
            risk_unexposed = risk_unexposed / (len(self.df) - len(total_exposed)) if len(total_exposed) < len(self.df) else 0
            
            risk_ratio = risk_exposed / risk_unexposed if risk_unexposed > 0 else 0
            
            return {
                "exposed_cases": len(exposed_cases),
                "total_exposed": len(total_exposed),
                "risk_exposed": float(risk_exposed),
                "risk_unexposed": float(risk_unexposed),
                "risk_ratio": float(risk_ratio),
                "odds_ratio": self._compute_odds_ratio(exposed_cases, total_exposed, total_reaction)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _compute_odds_ratio(
        self,
        exposed_cases: Any,
        total_exposed: Any,
        total_reaction: Any
    ) -> float:
        """Compute odds ratio."""
        try:
            a = len(exposed_cases)
            b = len(total_exposed) - a
            c = len(total_reaction) - a
            d = len(self.df) - len(total_exposed) - c
            
            if b == 0 or c == 0:
                return 0.0
            
            odds_ratio = (a * d) / (b * c) if (b * c) > 0 else 0.0
            return float(odds_ratio)
        except Exception:
            return 0.0
    
    def _find_column(self, df: Any, candidates: list) -> Optional[str]:
        """Find column in DataFrame."""
        for candidate in candidates:
            if hasattr(df, 'columns') and candidate in df.columns:
                return candidate
        return None
    
    def cache_result(self, key: str, value: Any) -> None:
        """Cache computation result."""
        # Convert to JSON-serializable format
        try:
            if hasattr(value, 'to_dict'):
                self.cache[key] = value.to_dict()
            elif isinstance(value, dict):
                self.cache[key] = value
            else:
                self.cache[key] = str(value)
        except Exception:
            self.cache[key] = str(value)
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached result."""
        return self.cache.get(key)


def create_offline_core() -> OfflineCore:
    """Factory function to create OfflineCore instance."""
    return OfflineCore()

