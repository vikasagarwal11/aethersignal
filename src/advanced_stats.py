"""
Advanced Statistical Methods for Pharmacovigilance Signal Detection
IC (Information Component), BCPNN, Chi-square, Fisher's exact test,
and simplified EBGM-style shrinkage
"""
import numpy as np
from scipy.stats import chi2_contingency, fisher_exact
from typing import Dict, Optional, Tuple

from src.utils import safe_divide


def calculate_ic(
    a: int, b: int, c: int, d: int, lambda_param: float = 0.5
) -> Dict[str, float]:
    """
    Calculate Information Component (IC) with credibility interval
    
    IC = log2((a + lambda) / ((a + b + lambda) * (a + c + lambda) / (n + lambda)))
    where n = a + b + c + d
    
    Args:
        a: Drug + Reaction cases
        b: Drug, no Reaction cases
        c: No Drug, Reaction cases
        d: No Drug, no Reaction cases
        lambda_param: Bayesian shrinkage parameter (default 0.5)
        
    Returns:
        Dict with IC, IC025, IC975 (credibility intervals)
    """
    n = a + b + c + d
    
    if n == 0:
        return {"ic": 0.0, "ic_025": 0.0, "ic_975": 0.0}
    
    # Apply Haldane-Anscombe correction if needed
    if a == 0 or b == 0 or c == 0 or d == 0:
        lambda_param = 0.5
    
    expected = safe_divide((a + b + lambda_param) * (a + c + lambda_param), n + lambda_param)
    
    if expected <= 0:
        return {"ic": 0.0, "ic_025": 0.0, "ic_975": 0.0}
    
    observed = a + lambda_param
    ic = np.log2(safe_divide(observed, expected))
    
    # Credibility interval (approximate)
    variance = safe_divide(1, observed) - safe_divide(1, n + lambda_param)
    if variance <= 0:
        variance = 0.01
    
    std_error = np.sqrt(variance)
    ic_025 = ic - 1.96 * std_error
    ic_975 = ic + 1.96 * std_error
    
    return {
        "ic": round(ic, 3),
        "ic_025": round(ic_025, 3),
        "ic_975": round(ic_975, 3),
    }


def calculate_bcpnn(a: int, b: int, c: int, d: int) -> Dict[str, float]:
    """
    Calculate Bayesian Confidence Propagation Neural Network (BCPNN) metric
    
    BCPNN uses same IC calculation with Bayesian prior
    
    Returns:
        Dict with BCPNN score (same as IC)
    """
    return calculate_ic(a, b, c, d, lambda_param=0.5)


def calculate_ebgm(a: int, b: int, c: int, d: int) -> Dict[str, float]:
    """
    Calculate a simplified Empirical Bayes Geometric Mean (EBGM) with EB05/EB95.

    This is an approximate, self-contained implementation inspired by MGPS:
    it uses the observed vs expected ratio with a small prior and a log-normal
    approximation for the posterior distribution. It is intended for
    exploratory signal assessment – not as a validated implementation for
    regulatory use.

    Args:
        a, b, c, d: 2x2 contingency table cells

    Returns:
        Dict with EBGM, EB05, EB95
    """
    n = a + b + c + d
    if n <= 0:
        return {"ebgm": 0.0, "eb05": 0.0, "eb95": 0.0}

    # Expected count under independence
    # E[a] = (row_total * col_total) / n
    row_total = a + b
    col_total = a + c
    expected = safe_divide(row_total * col_total, n)

    # Apply small prior to stabilize estimates
    obs = a + 0.5
    exp_adj = expected + 0.5

    if exp_adj <= 0:
        return {"ebgm": 0.0, "eb05": 0.0, "eb95": 0.0}

    rr = safe_divide(obs, exp_adj)
    if rr <= 0:
        return {"ebgm": 0.0, "eb05": 0.0, "eb95": 0.0}

    # Log-normal approximation for the posterior of the relative risk
    # Variance roughly inversely proportional to observed count
    var_log_rr = safe_divide(1.0, obs) + safe_divide(1.0, exp_adj)
    if var_log_rr <= 0:
        var_log_rr = 0.01

    se_log_rr = float(np.sqrt(var_log_rr))
    log_rr = float(np.log(rr))

    # EBGM ~ exp(log_rr)
    ebgm = float(np.exp(log_rr))
    # 90% interval equivalents (EB05 / EB95); for simplicity use 1.645
    z = 1.645
    eb05 = float(np.exp(log_rr - z * se_log_rr))
    eb95 = float(np.exp(log_rr + z * se_log_rr))

    return {
        "ebgm": round(ebgm, 3),
        "eb05": round(eb05, 3),
        "eb95": round(eb95, 3),
    }


def chi_square_test(a: int, b: int, c: int, d: int) -> Dict[str, float]:
    """
    Perform Chi-square test of independence
    
    Args:
        a, b, c, d: 2x2 contingency table cells
        
    Returns:
        Dict with chi-square statistic, p-value, degrees of freedom
    """
    try:
        contingency_table = np.array([[a, b], [c, d]])
        
        # Check if table is valid
        if np.any(contingency_table < 0):
            return {"chi2": 0.0, "p_value": 1.0, "df": 1, "significant": False}
        
        # If any expected frequency < 5, warn (but still compute)
        chi2, p_value, df, expected = chi2_contingency(contingency_table, correction=True)
        
        return {
            "chi2": round(chi2, 4),
            "p_value": round(p_value, 6),
            "df": int(df),
            "significant": p_value < 0.05,
        }
    except Exception:
        return {"chi2": 0.0, "p_value": 1.0, "df": 1, "significant": False}


def fisher_exact_test(a: int, b: int, c: int, d: int) -> Dict[str, float]:
    """
    Perform Fisher's exact test (better for small samples)
    
    Args:
        a, b, c, d: 2x2 contingency table cells
        
    Returns:
        Dict with odds ratio, p-value
    """
    try:
        contingency_table = np.array([[a, b], [c, d]])
        
        # Check if table is valid
        if np.any(contingency_table < 0):
            return {"odds_ratio": 1.0, "p_value": 1.0, "significant": False}
        
        odds_ratio, p_value = fisher_exact(contingency_table)
        
        return {
            "odds_ratio": round(odds_ratio, 4),
            "p_value": round(p_value, 6),
            "significant": p_value < 0.05,
        }
    except Exception:
        return {"odds_ratio": 1.0, "p_value": 1.0, "significant": False}


def calculate_prr_ror_ci(
    a: int, b: int, c: int, d: int, confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Calculate PRR and ROR with customizable confidence interval
    
    Args:
        a, b, c, d: 2x2 contingency table cells
        confidence_level: Confidence level (0.90, 0.95, 0.99)
        
    Returns:
        Dict with PRR, ROR, and their confidence intervals
    """
    # Calculate z-score for confidence level
    z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_scores.get(confidence_level, 1.96)
    
    # Apply Haldane-Anscombe correction if needed
    if a == 0 or b == 0 or c == 0 or d == 0:
        a += 0.5
        b += 0.5
        c += 0.5
        d += 0.5
    
    # PRR
    prr_num = safe_divide(a, a + b)
    prr_den = safe_divide(c, c + d)
    prr = safe_divide(prr_num, prr_den) if prr_den > 0 else 0.0
    
    if prr > 0:
        se_log_prr = np.sqrt(safe_divide(1, a) - safe_divide(1, a + b) + safe_divide(1, c) - safe_divide(1, c + d))
        prr_lower = np.exp(np.log(prr) - z * se_log_prr)
        prr_upper = np.exp(np.log(prr) + z * se_log_prr)
    else:
        prr_lower = prr_upper = 0.0
    
    # ROR
    ror = safe_divide(a * d, b * c) if (b * c) > 0 else 0.0
    
    if ror > 0:
        se_log_ror = np.sqrt(safe_divide(1, a) + safe_divide(1, b) + safe_divide(1, c) + safe_divide(1, d))
        ror_lower = np.exp(np.log(ror) - z * se_log_ror)
        ror_upper = np.exp(np.log(ror) + z * se_log_ror)
    else:
        ror_lower = ror_upper = 0.0
    
    ci_label = f"{int(confidence_level * 100)}%"
    
    return {
        "prr": round(prr, 3),
        f"prr_ci_lower_{ci_label}": round(prr_lower, 3),
        f"prr_ci_upper_{ci_label}": round(prr_upper, 3),
        "ror": round(ror, 3),
        f"ror_ci_lower_{ci_label}": round(ror_lower, 3),
        f"ror_ci_upper_{ci_label}": round(ror_upper, 3),
    }


def get_signal_strength(
    prr: float, ic: float, p_value: float, min_cases: int = 3
) -> Tuple[str, str]:
    """
    Classify signal strength based on multiple metrics
    
    Args:
        prr: Proportional Reporting Ratio
        ic: Information Component
        p_value: Statistical p-value
        min_cases: Minimum cases required
        
    Returns:
        Tuple of (strength_label, color_code)
    """
    if prr < 1.0 or ic < 0 or p_value > 0.05:
        return "Weak", "#fbbf24"  # Yellow
    
    if prr >= 2.0 and ic >= 1.0 and p_value < 0.01:
        return "Strong", "#ef4444"  # Red
    elif prr >= 1.5 and ic >= 0.5 and p_value < 0.05:
        return "Moderate", "#f97316"  # Orange
    else:
        return "Weak", "#fbbf24"  # Yellow

