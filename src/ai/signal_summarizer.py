"""
Enhanced Signal Summarization for AetherSignal
Generates comprehensive, medically-aligned summaries of safety signals.

Builds on llm_explain.py with:
- Comprehensive summaries (not just explanations)
- Conversational responses
- Trend interpretation
- Risk assessment
"""

from typing import Dict, Optional, List
import os
import json
from src.llm_explain import has_llm_configured, generate_signal_explanation
from src.ai.medical_llm import call_medical_llm


def generate_comprehensive_summary(
    drug: str,
    reaction: str,
    summary: Dict,
    prr_ror: Optional[Dict],
    trends: Optional[Dict] = None,
    use_llm: bool = True
) -> str:
    """
    Generate comprehensive signal summary with interpretation.
    
    Example output:
    "Dupixent — Serious Conjunctivitis Cases (2019–2024)
    
    • 134 total cases (0.9% of all Dupixent reports)
    • PRR: 3.4 (CI 2.8–4.2) → consistent disproportionality
    • Increasing trend since mid-2022
    • Most cases in adults 30–55
    • No strong demographic concentration
    
    Interpretation:
    There is a persistent, moderate signal for conjunctivitis with Dupixent 
    consistent with clinical literature. Monitoring recommended."
    """
    if not use_llm or not has_llm_configured():
        return _generate_rule_based_summary(drug, reaction, summary, prr_ror, trends)
    
    # Use LLM for comprehensive summary
    try:
        context = _build_summary_context(drug, reaction, summary, prr_ror, trends)
        return _generate_llm_summary(context)
    except Exception:
        # Fallback to rule-based
        return _generate_rule_based_summary(drug, reaction, summary, prr_ror, trends)


def generate_conversational_response(
    query: str,
    filters: Dict,
    summary: Dict,
    prr_ror: Optional[Dict],
    trends: Dict,
    red_flags: List[str]
) -> str:
    """Generate conversational response to user query using LLM."""
    if not has_llm_configured():
        return "LLM not configured. Please enable in settings."
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "LLM API key not found."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=15.0)
    except Exception:
        return "LLM client unavailable."
    
    # Build context
    context_text = f"""User Query: {query}

Extracted Filters: {json.dumps(filters, indent=2)}

Results:
- Matching Cases: {summary.get('matching_cases', 0):,}
- Total Cases: {summary.get('total_cases', 0):,}
- Serious Cases: {summary.get('serious_count', 0):,} ({summary.get('serious_percentage', 0):.1f}%)

"""
    
    if prr_ror:
        context_text += f"""Disproportionality:
- PRR: {prr_ror.get('prr', 0):.2f} (CI: {prr_ror.get('prr_ci_lower', 0):.2f} - {prr_ror.get('prr_ci_upper', 0):.2f})
- ROR: {prr_ror.get('ror', 0):.2f} (CI: {prr_ror.get('ror_ci_lower', 0):.2f} - {prr_ror.get('ror_ci_upper', 0):.2f})

"""
    
    if trends.get("has_trend"):
        context_text += f"""Trends:
- Direction: {trends.get('direction', 'stable')}
- Spikes: {len(trends.get('spikes', []))}

"""
    
    if red_flags:
        context_text += f"Red Flags: {', '.join(red_flags)}\n"
    
    system_prompt = """You are a pharmacovigilance expert assistant. Answer user queries about drug safety data in a clear, conversational, and medically appropriate way.

Guidelines:
- Be concise but informative
- Use plain language (avoid excessive jargon)
- Highlight important findings (red flags, trends, high PRR/ROR)
- Be cautious about causality (these are associations, not proof)
- If asked about "red flags" or "signals", focus on PRR/ROR, trends, and seriousness
- If asked about trends, explain what the trend means
- Always mention limitations (spontaneous reports, not validated for regulatory decisions)

Format your response as a natural conversation, not a bullet list."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context_text + "\nAnswer the user's query in a conversational way:"}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        return content.strip() if content else "Unable to generate response."
    except Exception:
        return "Error generating conversational response."


def _build_summary_context(
    drug: str,
    reaction: str,
    summary: Dict,
    prr_ror: Optional[Dict],
    trends: Optional[Dict]
) -> Dict:
    """Build context dictionary for LLM summary generation."""
    context = {
        "drug": drug,
        "reaction": reaction,
        "matching_cases": summary.get("matching_cases", 0),
        "total_cases": summary.get("total_cases", 0),
        "percentage": summary.get("percentage", 0),
        "serious_count": summary.get("serious_count", 0),
        "serious_percentage": summary.get("serious_percentage", 0),
    }
    
    if prr_ror:
        context.update({
            "prr": prr_ror.get("prr"),
            "prr_ci_lower": prr_ror.get("prr_ci_lower"),
            "prr_ci_upper": prr_ror.get("prr_ci_upper"),
            "ror": prr_ror.get("ror"),
            "ror_ci_lower": prr_ror.get("ror_ci_lower"),
            "ror_ci_upper": prr_ror.get("ror_ci_upper"),
        })
    
    if trends:
        context["trend_direction"] = trends.get("direction")
        context["has_spikes"] = len(trends.get("spikes", [])) > 0
        context["spike_count"] = len(trends.get("spikes", []))
    
    age_stats = summary.get("age_stats", {})
    if age_stats.get("mean"):
        context["median_age"] = age_stats.get("mean")
        context["age_range"] = f"{age_stats.get('min', 0):.0f}-{age_stats.get('max', 0):.0f}"
    
    if summary.get("sex_distribution"):
        context["sex_distribution"] = summary["sex_distribution"]
    
    return context


def _generate_llm_summary(context: Dict) -> str:
    """Generate summary using LLM (with causal reasoning for mechanisms)."""
    system_prompt = """You are a pharmacovigilance expert writing signal summaries. 
Provide comprehensive summaries including:
1. Statistical strength (PRR/ROR interpretation)
2. Clinical context
3. Known mechanisms (if well-established)
4. Population characteristics
5. Recommendations

Be cautious about causality - these are associations, not proof."""
    
    prompt = f"""Generate a comprehensive pharmacovigilance signal summary.

Drug: {context['drug']}
Reaction: {context['reaction']}
Cases: {context['matching_cases']:,} ({context['percentage']:.1f}% of {context['total_cases']:,} total)
Serious: {context['serious_count']:,} ({context['serious_percentage']:.1f}%)

"""
    
    if context.get("prr"):
        prompt += f"""Disproportionality:
PRR: {context['prr']:.2f} (95% CI: {context['prr_ci_lower']:.2f} - {context['prr_ci_upper']:.2f})
ROR: {context['ror']:.2f} (95% CI: {context['ror_ci_lower']:.2f} - {context['ror_ci_upper']:.2f})

"""
    
    if context.get("trend_direction"):
        prompt += f"Trend: {context['trend_direction']}\n"
        if context.get("has_spikes"):
            prompt += f"Detected {context['spike_count']} significant spike(s)\n"
    
    if context.get("median_age"):
        prompt += f"Demographics: Median age {context['median_age']:.0f} years"
        if context.get("age_range"):
            prompt += f" (range: {context['age_range']})"
        prompt += "\n"
    
    prompt += """
Format as:
1. Header: "Drug — Reaction (Time Period)"
2. Bullet points with key findings
3. Interpretation paragraph with mechanisms (if known) and clinical context

Be concise, medically appropriate, and emphasize that these are exploratory metrics."""
    
    # Use causal_reasoning task type to prefer Claude Opus if available
    response = call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="causal_reasoning",  # Prefers Claude Opus for better reasoning
        max_tokens=600,
        temperature=0.3
    )
    
    if response:
        return response.strip()
    
    # Fallback to rule-based
    return _generate_rule_based_summary(
        context["drug"], context["reaction"], context, None, None
    )


def generate_causal_explanation(
    drug: str,
    reaction: str,
    prr_ror: Optional[Dict],
    summary: Dict
) -> Optional[str]:
    """
    Generate causal reasoning explanation for signal.
    Uses Claude Opus if available (best for reasoning), otherwise GPT-4o.
    
    Args:
        drug: Drug name
        reaction: Reaction name
        prr_ror: PRR/ROR metrics
        summary: Summary statistics
        
    Returns:
        Causal explanation or None
    """
    system_prompt = """You are a pharmacovigilance expert specializing in causal reasoning. 
Explain potential mechanisms for drug-reaction relationships. Include:
1. Known pharmacological mechanisms (if established)
2. Pathophysiological pathways
3. Risk factors
4. Clinical context
5. Limitations and uncertainties

Be cautious - only mention mechanisms if they are well-established in literature."""
    
    prompt = f"""Drug: {drug}
Reaction: {reaction}
PRR: {prr_ror.get('prr', 0):.2f} (CI: {prr_ror.get('prr_ci_lower', 0):.2f} - {prr_ror.get('prr_ci_upper', 0):.2f})
Cases: {summary.get('matching_cases', 0):,}
Serious: {summary.get('serious_percentage', 0):.1f}%

Explain potential mechanisms for this signal. What biological pathways might be involved?
What is the clinical significance? What should safety scientists consider?"""
    
    return call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="causal_reasoning",  # Prefers Claude Opus
        max_tokens=500,
        temperature=0.3
    )


def _generate_rule_based_summary(
    drug: str,
    reaction: str,
    summary: Dict,
    prr_ror: Optional[Dict],
    trends: Optional[Dict]
) -> str:
    """Generate summary using rule-based approach (fallback)."""
    parts = [f"**{drug} — {reaction}**\n"]
    
    matching = summary.get("matching_cases", 0)
    total = summary.get("total_cases", 0)
    pct = summary.get("percentage", 0)
    parts.append(f"• {matching:,} total cases ({pct:.1f}% of {total:,} reports)")
    
    if prr_ror:
        prr = prr_ror.get("prr", 0)
        parts.append(f"• PRR: {prr:.2f} (CI {prr_ror.get('prr_ci_lower', 0):.2f}–{prr_ror.get('prr_ci_upper', 0):.2f})")
    
    if trends and trends.get("direction"):
        parts.append(f"• Trend: {trends['direction']}")
    
    serious_pct = summary.get("serious_percentage", 0)
    if serious_pct > 0:
        parts.append(f"• Serious cases: {summary.get('serious_count', 0):,} ({serious_pct:.1f}%)")
    
    parts.append("\n**Interpretation:**")
    parts.append("Exploratory disproportionality analysis based on spontaneous reports. Not validated for regulatory decision-making.")
    
    return "\n".join(parts)

