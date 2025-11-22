"""
Optional LLM-backed explanations for signals.

This module provides a best-effort integration with external LLM APIs
(e.g., OpenAI) to generate richer, literature-aware narratives for
drug-event signals. It is fully optional and degrades gracefully when
no API key or client library is available.
"""

from __future__ import annotations

from typing import Dict, Optional
import os


def has_llm_configured() -> bool:
    """
    Check whether an external LLM is configured via environment variables.
    Currently looks for OPENAI_API_KEY.
    """
    return bool(os.environ.get("OPENAI_API_KEY"))


def generate_signal_explanation(context: Dict) -> Optional[str]:
    """
    Generate an LLM-backed explanation for a drug-event signal.

    The context dict can include:
        - drug, reaction
        - counts: a, b, c, d
        - prr, ror, ic, bcpnn, ebgm
        - serious_pct, matching_cases
        - median_age, sex_distribution, top_countries
        - trend_summary (optional string)

    Returns:
        Natural language explanation, or None if generation fails or LLM is not configured.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    # Import inside the function so that environments without the client
    # library can still import this module and run other parts of the app.
    try:
        import openai  # type: ignore
    except Exception:
        return None

    drug = context.get("drug", "the drug")
    reaction = context.get("reaction", "the reaction")
    a = context.get("a")
    b = context.get("b")
    c = context.get("c")
    d = context.get("d")
    prr = context.get("prr")
    ror = context.get("ror")
    ic = context.get("ic")
    bcpnn = context.get("bcpnn")
    ebgm = context.get("ebgm")
    serious_pct = context.get("serious_pct")
    matching_cases = context.get("matching_cases")
    median_age = context.get("median_age")
    sex_distribution = context.get("sex_distribution")
    top_countries = context.get("top_countries")
    trend_summary = context.get("trend_summary")

    # Build a compact, structured prompt
    stats_lines = []
    if a is not None:
        stats_lines.append(f"a={a}, b={b}, c={c}, d={d}")
    if prr is not None and ror is not None:
        stats_lines.append(f"PRR={prr}, ROR={ror}")
    if ic is not None:
        stats_lines.append(f"IC={ic}")
    if bcpnn is not None:
        stats_lines.append(f"BCPNN={bcpnn}")
    if ebgm is not None:
        stats_lines.append(f"EBGM={ebgm}")
    if serious_pct is not None and matching_cases is not None:
        stats_lines.append(
            f"{matching_cases} matching cases; ~{serious_pct:.1f}% serious."
        )
    if median_age is not None:
        stats_lines.append(f"Median age ~{median_age:.0f} years.")
    if sex_distribution:
        stats_lines.append(f"Sex distribution: {sex_distribution}.")
    if top_countries:
        stats_lines.append(f"Top countries: {top_countries}.")
    if trend_summary:
        stats_lines.append(f"Trend: {trend_summary}")

    stats_block = "\n".join(stats_lines)

    system_prompt = (
        "You are a pharmacovigilance and drug safety expert. "
        "Given disproportionality metrics and simple cohort stats for a drug–event combination, "
        "write a short, cautious explanation for safety scientists. "
        "Do NOT claim causality. Highlight possible mechanisms only if they are well known, "
        "and always emphasise uncertainties and the need for clinical judgment."
    )

    user_prompt = (
        f"Drug: {drug}\n"
        f"Reaction: {reaction}\n\n"
        f"Summary stats:\n{stats_block}\n\n"
        "Write 1–2 short paragraphs explaining how strong this signal appears, "
        "how it compares to typical thresholds, which populations seem most represented, "
        "and what a safety scientist should consider next. "
        "Mention any well-established literature associations you know, but stay high-level and cautious."
    )

    try:
        # Support both legacy and newer OpenAI client APIs in a best-effort way.
        # 1) Try newer client style
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=400,
                temperature=0.4,
            )
            content = response.choices[0].message.content
            return content.strip() if content else None
        except Exception:
            # 2) Fallback to legacy ChatCompletion interface
            try:
                openai.api_key = api_key
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=400,
                    temperature=0.4,
                )
                content = response.choices[0].message["content"]
                return content.strip() if content else None
            except Exception:
                return None
    except Exception:
        return None

