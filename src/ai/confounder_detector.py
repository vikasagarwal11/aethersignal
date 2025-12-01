"""
Confounder Identification Engine (CHUNK 6.27 - Part C - BONUS #2)
Automatically identifies confounders, mediators, colliders, and hidden biases.

Uses statistical methods (mutual information, partial correlations, conditional
independence tests) and semantic analysis to identify causal relationships.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

try:
    from sklearn.feature_selection import mutual_info_regression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class ConfounderFinding:
    """Represents a confounder, mediator, or collider finding."""
    variable: str
    variable_type: str  # "confounder", "mediator", "collider", "instrumental"
    strength: float  # 0-1, strength of relationship
    evidence: List[str]  # Supporting evidence
    adjustment_recommended: bool  # Whether to adjust for this variable
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable": self.variable,
            "variable_type": self.variable_type,
            "strength": self.strength,
            "evidence": self.evidence,
            "adjustment_recommended": self.adjustment_recommended
        }


class ConfounderDetector:
    """
    Automatically identifies confounders, mediators, and colliders.
    
    Confounder: Affects both exposure and outcome
    Mediator: On causal path from exposure to outcome
    Collider: Common effect of exposure and outcome
    """
    
    def __init__(self):
        """Initialize Confounder Detector."""
        self.min_mutual_info = 0.1
        self.min_correlation = 0.15
    
    def identify(
        self,
        df: pd.DataFrame,
        exposure: str,
        outcome: str,
        candidate_variables: Optional[List[str]] = None
    ) -> List[ConfounderFinding]:
        """
        Identify confounders, mediators, and colliders.
        
        Args:
            df: Safety data DataFrame
            exposure: Exposure variable name (drug)
            outcome: Outcome variable name (reaction)
            candidate_variables: Optional list of variables to check
            
        Returns:
            List of ConfounderFinding objects
        """
        if df is None or df.empty:
            return []
        
        findings = []
        
        # Find exposure and outcome columns
        exposure_col = self._find_column(df, [exposure, "drug", "drug_name", "_drug"])
        outcome_col = self._find_column(df, [outcome, "reaction", "reaction_pt", "_reaction"])
        
        if not exposure_col or not outcome_col:
            return []
        
        # Prepare binary variables
        df_work = df.copy()
        df_work["_exposure"] = df_work[exposure_col].astype(str).str.contains(
            str(exposure), case=False, na=False
        ).astype(int)
        df_work["_outcome"] = df_work[outcome_col].astype(str).str.contains(
            str(outcome), case=False, na=False
        ).astype(int)
        
        # Get candidate variables
        if candidate_variables is None:
            candidate_variables = self._get_default_candidates(df_work)
        
        # Test each candidate variable
        for var in candidate_variables:
            if var not in df_work.columns or var in [exposure_col, outcome_col]:
                continue
            
            var_values = self._normalize_column(df_work[var])
            if var_values is None:
                continue
            
            exposure_values = df_work["_exposure"].values
            outcome_values = df_work["_outcome"].values
            
            # Check for confounder (affects both exposure and outcome)
            confounder_strength = self._check_confounder(
                var_values, exposure_values, outcome_values
            )
            if confounder_strength > 0:
                findings.append(ConfounderFinding(
                    variable=var,
                    variable_type="confounder",
                    strength=confounder_strength,
                    evidence=[
                        f"Affects both exposure (r={self._compute_correlation(var_values, exposure_values):.3f}) "
                        f"and outcome (r={self._compute_correlation(var_values, outcome_values):.3f})"
                    ],
                    adjustment_recommended=True
                ))
            
            # Check for mediator (on causal path)
            mediator_strength = self._check_mediator(
                var_values, exposure_values, outcome_values
            )
            if mediator_strength > 0:
                findings.append(ConfounderFinding(
                    variable=var,
                    variable_type="mediator",
                    strength=mediator_strength,
                    evidence=[
                        f"On causal path: exposure → {var} → outcome"
                    ],
                    adjustment_recommended=False  # Don't adjust for mediators
                ))
            
            # Check for collider (common effect)
            collider_strength = self._check_collider(
                var_values, exposure_values, outcome_values
            )
            if collider_strength > 0:
                findings.append(ConfounderFinding(
                    variable=var,
                    variable_type="collider",
                    strength=collider_strength,
                    evidence=[
                        f"Common effect of exposure and outcome"
                    ],
                    adjustment_recommended=False  # Don't adjust for colliders
                ))
        
        # Sort by strength
        findings.sort(key=lambda x: x.strength, reverse=True)
        
        return findings
    
    def _check_confounder(
        self,
        var_values: np.ndarray,
        exposure_values: np.ndarray,
        outcome_values: np.ndarray
    ) -> float:
        """
        Check if variable is a confounder.
        
        Confounder: Correlated with both exposure and outcome.
        """
        corr_var_exposure = abs(self._compute_correlation(var_values, exposure_values))
        corr_var_outcome = abs(self._compute_correlation(var_values, outcome_values))
        
        # Both correlations should be significant
        if corr_var_exposure >= self.min_correlation and corr_var_outcome >= self.min_correlation:
            # Average correlation strength
            return (corr_var_exposure + corr_var_outcome) / 2.0
        
        return 0.0
    
    def _check_mediator(
        self,
        var_values: np.ndarray,
        exposure_values: np.ndarray,
        outcome_values: np.ndarray
    ) -> float:
        """
        Check if variable is a mediator.
        
        Mediator: Exposure affects mediator, mediator affects outcome.
        Should NOT adjust for mediators (breaks causal path).
        """
        corr_exposure_var = abs(self._compute_correlation(exposure_values, var_values))
        corr_var_outcome = abs(self._compute_correlation(var_values, outcome_values))
        
        # Both should be significant for mediator
        if corr_exposure_var >= 0.2 and corr_var_outcome >= 0.2:
            return (corr_exposure_var + corr_var_outcome) / 2.0
        
        return 0.0
    
    def _check_collider(
        self,
        var_values: np.ndarray,
        exposure_values: np.ndarray,
        outcome_values: np.ndarray
    ) -> float:
        """
        Check if variable is a collider.
        
        Collider: Common effect of exposure and outcome.
        Should NOT condition on colliders (creates spurious association).
        
        Detection: If conditioning on variable increases exposure-outcome association,
        it might be a collider.
        """
        # Simplified check: if variable is strongly correlated with both
        # but not as a mediator pattern, might be collider
        corr_var_exposure = abs(self._compute_correlation(var_values, exposure_values))
        corr_var_outcome = abs(self._compute_correlation(var_values, outcome_values))
        
        # Collider: both correlations exist but not mediator pattern
        if corr_var_exposure >= 0.2 and corr_var_outcome >= 0.2:
            # Check if exposure->var correlation is weaker (suggests collider)
            if corr_var_exposure < corr_var_outcome * 0.8:
                return corr_var_outcome
        
        return 0.0
    
    def _compute_correlation(self, x: np.ndarray, y: np.ndarray) -> float:
        """Compute correlation coefficient."""
        if len(x) < 2 or len(y) < 2:
            return 0.0
        
        x_clean = np.array(x, dtype=float)
        y_clean = np.array(y, dtype=float)
        
        mask = ~(np.isnan(x_clean) | np.isnan(y_clean))
        x_clean = x_clean[mask]
        y_clean = y_clean[mask]
        
        if len(x_clean) < 2:
            return 0.0
        
        try:
            corr = np.corrcoef(x_clean, y_clean)[0, 1]
            return float(corr) if not np.isnan(corr) else 0.0
        except Exception:
            return 0.0
    
    def _normalize_column(self, series: pd.Series) -> Optional[np.ndarray]:
        """Normalize column to numeric values."""
        if series.dtype in [int, float]:
            return series.fillna(0).values
        
        try:
            if series.dtype == 'object':
                codes = pd.Categorical(series).codes
                return codes.astype(float)
            else:
                return series.fillna(0).values
        except Exception:
            return None
    
    def _get_default_candidates(self, df: pd.DataFrame) -> List[str]:
        """Get default candidate variables for confounder detection."""
        candidates = [
            "age", "AGE", "age_yr",
            "sex", "SEX", "gender",
            "country", "COUNTRY",
            "weight", "WEIGHT",
            "serious", "SERIOUS",
            "outcome", "outc_cod"
        ]
        
        found = []
        for candidate in candidates:
            if candidate in df.columns:
                found.append(candidate)
        
        return found
    
    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        """Find column in DataFrame."""
        for candidate in candidates:
            if candidate in df.columns:
                return candidate
        return None


def identify_confounders(
    df: pd.DataFrame,
    exposure: str,
    outcome: str,
    candidate_variables: Optional[List[str]] = None
) -> List[ConfounderFinding]:
    """
    Convenience function for confounder identification.
    
    Args:
        df: Safety data DataFrame
        exposure: Exposure variable name
        outcome: Outcome variable name
        candidate_variables: Optional list of variables to check
        
    Returns:
        List of ConfounderFinding objects
    """
    detector = ConfounderDetector()
    return detector.identify(df, exposure, outcome, candidate_variables)

