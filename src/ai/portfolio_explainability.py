"""
Portfolio Explainability Layer

Given a normalized PV dataframe and (optionally) a product name,
computes drivers of change between a recent period and a baseline period.

Outputs:
- key_metrics: high-level stats for recent vs baseline
- top_reactions: which PTs drove the change
- top_subgroups: which demographics / seriousness / countries contributed most
- driver_summary: bullet-style plain-text summary
- llm_explanation: optional LLM narrative (can be None if LLM disabled)
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

try:
    # Optional: only used if available
    from src.ai.medical_llm import call_medical_llm
except Exception:
    call_medical_llm = None  # type: ignore


def _parse_dates(df: pd.DataFrame) -> pd.Series:
    """
    Try to infer a usable date column and return a datetime Series.
    Prefers: 'event_date', 'receipt_date', 'case_date', then any *date* column.
    """
    candidate_cols = [
        "event_date",
        "event_dt",
        "receipt_date",
        "receipt_dt",
        "case_date",
        "fda_dt",
    ]

    for col in candidate_cols:
        if col in df.columns:
            try:
                return pd.to_datetime(df[col], errors="coerce")
            except Exception:
                continue

    # Fallback: try any column that contains 'date'
    for col in df.columns:
        if "date" in col.lower():
            try:
                return pd.to_datetime(df[col], errors="coerce")
            except Exception:
                continue

    # As last resort, create a dummy constant date
    return pd.to_datetime("2000-01-01").repeat(len(df))


def _filter_by_drug(df: pd.DataFrame, drug_name: Optional[str]) -> pd.DataFrame:
    """
    If a drug_name is provided, filter to that drug.
    Assumes a 'drug_name' or 'product_name' column with '; '-separated values.
    """
    if not drug_name:
        return df

    df = df.copy()
    drug_col = None
    if "drug_name" in df.columns:
        drug_col = "drug_name"
    elif "product_name" in df.columns:
        drug_col = "product_name"

    if not drug_col:
        return df

    # Explode multi-drug cells
    exploded = (
        df.assign(_drug=df[drug_col].astype(str).str.split("; "))
        .explode("_drug")
    )
    mask = exploded["_drug"].str.lower().str.contains(str(drug_name).lower(), na=False)
    return exploded[mask].drop(columns=["_drug"])


def _split_recent_baseline(
    df: pd.DataFrame,
    date_series: pd.Series,
    recent_months: int = 3,
    baseline_months: int = 12,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split into recent window vs baseline window.
    e.g., last 3 months vs previous 12 months before that.
    """
    valid = df.copy()
    valid["_date"] = date_series
    valid = valid[valid["_date"].notna()]

    if valid.empty:
        return valid.copy(), valid.copy()

    max_date = valid["_date"].max()
    recent_start = max_date - pd.DateOffset(months=recent_months)
    baseline_start = recent_start - pd.DateOffset(months=baseline_months)

    recent = valid[valid["_date"] >= recent_start]
    baseline = valid[(valid["_date"] < recent_start) & (valid["_date"] >= baseline_start)]

    return recent.copy(), baseline.copy()


def _compute_rate_delta(
    recent: pd.DataFrame,
    baseline: pd.DataFrame,
    group_col: str,
    min_cases: int = 10,
) -> pd.DataFrame:
    """
    Compute change in proportion for values of group_col between baseline and recent.
    Returns sorted descending by absolute delta.
    """
    if recent.empty or baseline.empty or group_col not in recent.columns:
        return pd.DataFrame()

    def _norm(s: pd.Series) -> pd.Series:
        s = s.astype(str).replace("nan", np.nan)
        return s

    r = _norm(recent[group_col])
    b = _norm(baseline[group_col])

    r_counts = r.value_counts(dropna=True)
    b_counts = b.value_counts(dropna=True)

    if r_counts.empty or b_counts.empty:
        return pd.DataFrame()

    r_total = r_counts.sum()
    b_total = b_counts.sum()

    df = pd.DataFrame({
        "baseline_count": b_counts,
        "recent_count": r_counts
    }).fillna(0)

    df["baseline_prop"] = df["baseline_count"] / max(b_total, 1)
    df["recent_prop"] = df["recent_count"] / max(r_total, 1)
    df["delta_prop"] = df["recent_prop"] - df["baseline_prop"]
    df["delta_abs"] = df["delta_prop"].abs()

    df = df[df["recent_count"] + df["baseline_count"] >= min_cases]
    df = df.sort_values("delta_abs", ascending=False)

    df.index.name = group_col
    return df.reset_index()


def analyze_portfolio_drivers(
    normalized_df: pd.DataFrame,
    product: Optional[str] = None,
    recent_months: int = 3,
    baseline_months: int = 12,
    use_llm: bool = True,
) -> Dict[str, Any]:
    """
    Main entrypoint: analyze drivers of change for a product or entire portfolio.

    Args:
        normalized_df: normalized PV dataframe for current org.
        product: optional drug/product name to focus on.
        recent_months: size of recent window.
        baseline_months: size of baseline window.
        use_llm: if True and LLM configured, generate narrative.

    Returns:
        {
          "key_metrics": {...},
          "top_reactions": [...],
          "top_subgroups": [...],
          "driver_summary": str,
          "llm_explanation": Optional[str],
        }
    """
    if normalized_df is None or len(normalized_df) == 0:
        return {
            "key_metrics": {},
            "top_reactions": [],
            "top_subgroups": [],
            "driver_summary": "No data available for driver analysis.",
            "llm_explanation": None,
        }

    # Optional product filter
    df = _filter_by_drug(normalized_df, product)

    # Dates
    dates = _parse_dates(df)
    recent, baseline = _split_recent_baseline(df, dates, recent_months, baseline_months)

    total_recent = len(recent)
    total_baseline = len(baseline)

    key_metrics: Dict[str, Any] = {
        "recent_cases": int(total_recent),
        "baseline_cases": int(total_baseline),
        "recent_months": recent_months,
        "baseline_months": baseline_months,
    }

    if total_recent == 0 or total_baseline == 0:
        summary = (
            "Not enough temporal coverage to compare recent vs baseline periods. "
            "Driver analysis is not available."
        )
        return {
            "key_metrics": key_metrics,
            "top_reactions": [],
            "top_subgroups": [],
            "driver_summary": summary,
            "llm_explanation": None,
        }

    # --- Reactions driver ---
    reaction_col = None
    for col in ["reaction_pt", "pt", "event_preferred_term", "reaction"]:
        if col in df.columns:
            reaction_col = col
            break

    top_reactions: List[Dict[str, Any]] = []
    if reaction_col:
        reaction_delta = _compute_rate_delta(recent, baseline, reaction_col, min_cases=10)
        for _, row in reaction_delta.head(10).iterrows():
            top_reactions.append({
                "reaction": row[reaction_col],
                "baseline_count": int(row["baseline_count"]),
                "recent_count": int(row["recent_count"]),
                "baseline_prop": float(row["baseline_prop"]),
                "recent_prop": float(row["recent_prop"]),
                "delta_prop": float(row["delta_prop"]),
            })

    # --- Subgroup drivers: seriousness, country, age_group, sex ---
    subgroup_cols = []
    if "seriousness" in df.columns:
        subgroup_cols.append("seriousness")
    if "country" in df.columns:
        subgroup_cols.append("country")
    if "age_group" in df.columns:
        subgroup_cols.append("age_group")
    if "sex" in df.columns:
        subgroup_cols.append("sex")

    top_subgroups: List[Dict[str, Any]] = []

    for col in subgroup_cols:
        delta_df = _compute_rate_delta(recent, baseline, col, min_cases=10)
        for _, row in delta_df.head(5).iterrows():
            top_subgroups.append({
                "dimension": col,
                "value": row[col],
                "baseline_count": int(row["baseline_count"]),
                "recent_count": int(row["recent_count"]),
                "baseline_prop": float(row["baseline_prop"]),
                "recent_prop": float(row["recent_prop"]),
                "delta_prop": float(row["delta_prop"]),
            })

    # --- Plain-text driver summary (non-LLM) ---
    lines: List[str] = []

    product_label = product if product else "overall portfolio"

    lines.append(
        f"For the {product_label}, we compared the last {recent_months} months "
        f"against the previous {baseline_months} months."
    )
    lines.append(
        f"Baseline: {total_baseline} cases. Recent: {total_recent} cases."
    )

    if top_reactions:
        top_reac = top_reactions[0]
        dir_word = "increase" if top_reac["delta_prop"] > 0 else "decrease"
        lines.append(
            f"The reaction **{top_reac['reaction']}** shows the largest {dir_word} "
            f"in relative share between baseline and recent periods."
        )

    # Seriousness example
    serious_entries = [t for t in top_subgroups if t["dimension"] == "seriousness"]
    if serious_entries:
        s = serious_entries[0]
        dir_word = "increase" if s["delta_prop"] > 0 else "decrease"
        lines.append(
            f"Seriousness dimension: cases with seriousness = **{s['value']}** "
            f"show a notable {dir_word} in relative share."
        )

    # Country example
    country_entries = [t for t in top_subgroups if t["dimension"] == "country"]
    if country_entries:
        c = country_entries[0]
        dir_word = "increase" if c["delta_prop"] > 0 else "decrease"
        lines.append(
            f"Geography: reports from **{c['value']}** show a {dir_word} "
            f"in relative contribution."
        )

    driver_summary = "\n".join(lines)

    # --- Optional LLM explanation ---
    llm_explanation: Optional[str] = None
    if use_llm and call_medical_llm is not None:
        # keep prompt compact: send summary, not the full dataframe
        system_prompt = (
            "You are a senior pharmacovigilance expert. "
            "Explain portfolio-level drivers of change (recent vs baseline) "
            "in clear regulatory language. Be concise but specific. "
            "Highlight key reactions, seriousness, demographics, and geographies."
        )

        # Build a compact structured context
        ctx_parts: List[str] = [
            f"Product: {product_label}",
            f"Baseline cases: {total_baseline}",
            f"Recent cases: {total_recent}",
            "Top reactions (recent vs baseline share):",
        ]
        for r in top_reactions[:5]:
            ctx_parts.append(
                f"- {r['reaction']}: baseline={r['baseline_count']} "
                f"({r['baseline_prop']:.3f}), recent={r['recent_count']} "
                f"({r['recent_prop']:.3f}), delta={r['delta_prop']:.3f}"
            )

        if top_subgroups:
            ctx_parts.append("Key subgroup shifts:")
            for t in top_subgroups[:8]:
                ctx_parts.append(
                    f"- {t['dimension']}={t['value']}: "
                    f"baseline={t['baseline_count']} ({t['baseline_prop']:.3f}), "
                    f"recent={t['recent_count']} ({t['recent_prop']:.3f}), "
                    f"delta={t['delta_prop']:.3f}"
                )

        user_prompt = "\n".join(ctx_parts)

        try:
            llm_explanation = call_medical_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model="gpt-4o-mini",
                max_tokens=500,
                temperature=0.2,
            )
        except Exception:
            llm_explanation = None

    return {
        "key_metrics": key_metrics,
        "top_reactions": top_reactions,
        "top_subgroups": top_subgroups,
        "driver_summary": driver_summary,
        "llm_explanation": llm_explanation,
    }

