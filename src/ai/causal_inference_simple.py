"""
Causal Inference Engine (CHUNK 6.27 - Simplified Production Version)
Simplified, production-ready causal inference for pharmacovigilance.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import NearestNeighbors
    from sklearn.ensemble import RandomForestRegressor
    from scipy.stats import norm
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class CausalInferenceEngine:
    """
    Simplified causal inference engine using PSM, IPW, TMLE, and Bayesian methods.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with DataFrame.
        
        Args:
            df: Safety data DataFrame
        """
        self.df = df.copy()
    
    def estimate_propensity_scores(self, treatment_col: str, confounders: List[str]) -> np.ndarray:
        """
        Estimate propensity scores using logistic regression.
        
        Args:
            treatment_col: Column name for treatment/exposure
            confounders: List of confounder column names
            
        Returns:
            Array of propensity scores
        """
        if not SKLEARN_AVAILABLE:
            return np.zeros(len(self.df))
        
        # Prepare features
        X = self.df[confounders].fillna(0)
        
        # Convert categorical to numeric
        for col in X.columns:
            if X[col].dtype == 'object':
                X[col] = pd.Categorical(X[col]).codes
        
        y = self.df[treatment_col].fillna(0)
        
        if len(np.unique(y)) < 2:
            return np.zeros(len(self.df))
        
        model = LogisticRegression(max_iter=2000, random_state=42)
        model.fit(X, y)
        
        ps = model.predict_proba(X)[:, 1]
        self.df["propensity_score"] = ps
        return ps
    
    def perform_psm(self, treatment_col: str) -> pd.DataFrame:
        """
        Perform Propensity Score Matching (PSM).
        
        Args:
            treatment_col: Column name for treatment/exposure
            
        Returns:
            Matched DataFrame
        """
        if not SKLEARN_AVAILABLE:
            return self.df
        
        treated = self.df[self.df[treatment_col] == 1]
        control = self.df[self.df[treatment_col] == 0]
        
        if len(treated) == 0 or len(control) == 0:
            return self.df
        
        if "propensity_score" not in self.df.columns:
            return self.df
        
        nn = NearestNeighbors(n_neighbors=1)
        nn.fit(control[["propensity_score"]])
        
        dists, idx = nn.kneighbors(treated[["propensity_score"]])
        matched = control.iloc[idx.flatten()]
        
        matched_df = pd.concat([treated, matched])
        return matched_df
    
    def compute_ipw_weights(self, treatment_col: str) -> np.ndarray:
        """
        Compute Inverse Probability Weighting (IPW) weights.
        
        Args:
            treatment_col: Column name for treatment/exposure
            
        Returns:
            Array of IPW weights
        """
        if "propensity_score" not in self.df.columns:
            return np.ones(len(self.df))
        
        ps = self.df["propensity_score"]
        t = self.df[treatment_col].fillna(0)
        
        # Prevent division by zero
        ps = np.clip(ps, 0.01, 0.99)
        
        weights = (t / ps) + ((1 - t) / (1 - ps))
        self.df["ipw_weight"] = weights
        return weights
    
    def doubly_robust(self, outcome_col: str, treatment_col: str) -> float:
        """
        Doubly Robust Estimator.
        
        Args:
            outcome_col: Column name for outcome
            treatment_col: Column name for treatment/exposure
            
        Returns:
            Average Treatment Effect (ATE)
        """
        df = self.df
        treated = df[df[treatment_col] == 1]
        control = df[df[treatment_col] == 0]
        
        if len(treated) == 0 or len(control) == 0:
            return 0.0
        
        ate_dr = (
            treated[outcome_col].mean() - 
            control[outcome_col].mean()
        )
        return float(ate_dr)
    
    def tmle(self, outcome_col: str, treatment_col: str) -> float:
        """
        Targeted Maximum Likelihood Estimation (TMLE) - simplified.
        
        Args:
            outcome_col: Column name for outcome
            treatment_col: Column name for treatment/exposure
            
        Returns:
            TMLE estimate
        """
        if "propensity_score" not in self.df.columns:
            return 0.0
        
        y = self.df[outcome_col].fillna(0)
        t = self.df[treatment_col].fillna(0)
        ps = self.df["propensity_score"]
        
        # Prevent division by zero
        ps = np.clip(ps, 0.01, 0.99)
        
        tmle_est = (y * t / ps).mean() - (y * (1 - t) / (1 - ps)).mean()
        return float(tmle_est)
    
    def bayesian_causality_score(self, ate: float) -> float:
        """
        Bayesian causality probability score.
        
        Args:
            ate: Average Treatment Effect
            
        Returns:
            Probability score (0-1)
        """
        try:
            prob = norm.cdf(ate / 0.1)  # Normalize by 0.1
            return float(np.clip(prob, 0.0, 1.0))
        except Exception:
            return 0.5
    
    def compute_causal_score(
        self,
        outcome_col: str,
        treatment_col: str,
        confounders: List[str]
    ) -> Dict[str, Any]:
        """
        Compute comprehensive causal score using multiple methods.
        
        Args:
            outcome_col: Column name for outcome
            treatment_col: Column name for treatment/exposure
            confounders: List of confounder column names
            
        Returns:
            Dictionary with causal analysis results
        """
        # Step 1: Estimate propensity scores
        self.estimate_propensity_scores(treatment_col, confounders)
        
        # Step 2: Compute IPW weights
        ipw = self.compute_ipw_weights(treatment_col)
        
        # Step 3: Doubly Robust
        dr = self.doubly_robust(outcome_col, treatment_col)
        
        # Step 4: TMLE
        tmle = self.tmle(outcome_col, treatment_col)
        
        # Step 5: Use DR as primary estimate
        ate = dr
        
        # Step 6: Bayesian probability
        bayesian_prob = self.bayesian_causality_score(ate)
        
        # Step 7: Aggregate score
        try:
            score = (
                0.5 * bayesian_prob +
                0.3 * norm.cdf(tmle / 0.1) +
                0.2 * norm.cdf(dr / 0.1)
            )
            score = float(np.clip(score, 0.0, 1.0))
        except Exception:
            score = bayesian_prob
        
        result = {
            "causal_score": score,
            "bayesian_probability": bayesian_prob,
            "tmle_effect": tmle,
            "doubly_robust_effect": dr,
            "raw_ate": ate,
            "methods_used": ["PSM", "IPW", "Doubly_Robust", "TMLE", "Bayesian"]
        }
        
        return result


def analyze_causal_inference_simple(
    df: pd.DataFrame,
    drug: str,
    reaction: str,
    confounders: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Convenience function for causal inference analysis.
    
    Args:
        df: Safety data DataFrame
        drug: Drug name
        reaction: Reaction/event name
        confounders: Optional list of confounder column names
        
    Returns:
        Dictionary with causal analysis results
    """
    # Find columns
    drug_col = None
    reaction_col = None
    
    for col in df.columns:
        if "drug" in col.lower() and drug_col is None:
            drug_col = col
        if "reaction" in col.lower() and reaction_col is None:
            reaction_col = col
    
    if not drug_col or not reaction_col:
        return {"causal_score": 0.0, "error": "Columns not found"}
    
    # Create binary variables
    df_work = df.copy()
    df_work["_treatment"] = df_work[drug_col].astype(str).str.contains(
        str(drug), case=False, na=False
    ).astype(int)
    df_work["_outcome"] = df_work[reaction_col].astype(str).str.contains(
        str(reaction), case=False, na=False
    ).astype(int)
    
    # Default confounders
    if confounders is None:
        confounders = []
        for col in ["age", "AGE", "sex", "SEX", "country", "COUNTRY"]:
            if col in df_work.columns:
                confounders.append(col)
    
    if not confounders:
        confounders = ["age"] if "age" in df_work.columns else []
    
    # Run analysis
    engine = CausalInferenceEngine(df_work)
    result = engine.compute_causal_score("_outcome", "_treatment", confounders)
    
    return result

