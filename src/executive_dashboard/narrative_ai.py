"""
AI Narrative Engine - Phase 3J Step 4
Generates executive-level safety summaries using LLM.
"""

import os
from typing import Dict, List, Any, Optional
import pandas as pd
import logging

from .prompts import (
    EXECUTIVE_SUMMARY_PROMPT,
    RISK_ALERT_PROMPT,
    TRENDING_RISKS_PROMPT,
    MECHANISM_INSIGHT_PROMPT,
    NOVELTY_ANALYSIS_PROMPT,
    SOURCE_DIVERGENCE_PROMPT
)

logger = logging.getLogger(__name__)

# Try to import OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# Try to use medical_llm as fallback
try:
    from src.ai.medical_llm import call_medical_llm
    MEDICAL_LLM_AVAILABLE = True
except ImportError:
    MEDICAL_LLM_AVAILABLE = False


def build_context(
    kpis: Dict[str, Any],
    top_signals: pd.DataFrame,
    novelty_df: pd.DataFrame,
    trend_df: pd.DataFrame,
    mechanism_labels: Optional[List[str]] = None,
    source_breakdown: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Build context dictionary for AI narrative generation.
    
    Args:
        kpis: KPI metrics dictionary
        top_signals: Top ranked signals DataFrame
        novelty_df: Novel signals DataFrame
        trend_df: Trend DataFrame
        mechanism_labels: Optional mechanism labels
        source_breakdown: Optional source breakdown dictionary
    
    Returns:
        Context dictionary for AI prompts
    """
    context = {
        "kpis": kpis,
        "signals": top_signals.head(5).to_dict(orient="records") if not top_signals.empty else [],
        "novel_signals": novelty_df.head(5).to_dict(orient="records") if not novelty_df.empty else [],
        "trend": trend_df.tail(6).to_dict(orient="records") if not trend_df.empty else [],
        "mechanism": mechanism_labels or [],
        "source_breakdown": source_breakdown or {}
    }
    
    return context


def generate_executive_summary(context: Dict[str, Any]) -> str:
    """
    Generate executive-level safety summary.
    
    Args:
        context: Context dictionary with metrics and signals
    
    Returns:
        Executive summary text
    """
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if not api_key and OPENAI_AVAILABLE:
        return _fallback_executive_summary(context)
    
    # Try OpenAI first
    if OPENAI_AVAILABLE and api_key:
        try:
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=400,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You are a senior pharmacovigilance expert writing executive summaries."},
                    {"role": "user", "content": EXECUTIVE_SUMMARY_PROMPT},
                    {"role": "user", "content": f"Input Data:\n{_format_context(context)}"}
                ]
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI API error: {e}, trying fallback")
    
    # Try medical_llm as fallback
    if MEDICAL_LLM_AVAILABLE:
        try:
            prompt = f"{EXECUTIVE_SUMMARY_PROMPT}\n\nInput Data:\n{_format_context(context)}"
            
            narrative = call_medical_llm(
                prompt=prompt,
                system_prompt="You are a senior pharmacovigilance expert writing executive summaries.",
                task_type="general"
            )
            
            if narrative:
                return narrative
        except Exception as e:
            logger.warning(f"Medical LLM error: {e}")
    
    # Final fallback
    return _fallback_executive_summary(context)


def generate_risk_alert(context: Dict[str, Any]) -> str:
    """
    Generate risk alert summary.
    
    Args:
        context: Context dictionary
    
    Returns:
        Risk alert text
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if not api_key and OPENAI_AVAILABLE:
        return _fallback_risk_alert(context)
    
    if OPENAI_AVAILABLE and api_key:
        try:
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=200,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": "You summarize safety signals for internal review teams."},
                    {"role": "user", "content": RISK_ALERT_PROMPT},
                    {"role": "user", "content": f"Input Data:\n{_format_context(context)}"}
                ]
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI API error: {e}")
    
    return _fallback_risk_alert(context)


def generate_trending_risks(context: Dict[str, Any]) -> str:
    """Generate trending risks summary."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if OPENAI_AVAILABLE and api_key:
        try:
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=250,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You analyze trending safety risks."},
                    {"role": "user", "content": TRENDING_RISKS_PROMPT},
                    {"role": "user", "content": f"Input Data:\n{_format_context(context)}"}
                ]
            )
            
            return response.choices[0].message.content.strip()
        except Exception:
            pass
    
    return "Trending risks analysis unavailable (AI disabled)."


def generate_mechanism_insight(context: Dict[str, Any]) -> str:
    """Generate mechanism-of-action insight."""
    if not context.get("mechanism"):
        return "No mechanism data available."
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if OPENAI_AVAILABLE and api_key:
        try:
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=200,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You provide mechanistic insights for drug safety."},
                    {"role": "user", "content": MECHANISM_INSIGHT_PROMPT},
                    {"role": "user", "content": f"Mechanism Data:\n{context.get('mechanism', [])}"}
                ]
            )
            
            return response.choices[0].message.content.strip()
        except Exception:
            pass
    
    return "Mechanism insight unavailable (AI disabled)."


def _format_context(context: Dict[str, Any]) -> str:
    """Format context for AI prompts."""
    lines = []
    
    if "kpis" in context:
        lines.append("KPIs:")
        for key, value in context["kpis"].items():
            lines.append(f"  - {key}: {value}")
    
    if "signals" in context and context["signals"]:
        lines.append("\nTop Signals:")
        for signal in context["signals"][:5]:
            lines.append(f"  - {signal.get('reaction', 'Unknown')} (Quantum: {signal.get('quantum_score', 0):.2f})")
    
    if "novel_signals" in context and context["novel_signals"]:
        lines.append("\nNovel Signals:")
        for signal in context["novel_signals"][:5]:
            lines.append(f"  - {signal.get('reaction', 'Unknown')}")
    
    if "trend" in context and context["trend"]:
        lines.append("\nRecent Trends:")
        for trend in context["trend"][-3:]:
            lines.append(f"  - {trend.get('period_str', 'Unknown')}: {trend.get('count', 0)}")
    
    return "\n".join(lines)


def _fallback_executive_summary(context: Dict[str, Any]) -> str:
    """Generate fallback executive summary without AI."""
    kpis = context.get("kpis", {})
    signals = context.get("signals", [])
    
    summary = f"Safety Summary: Total AEs: {kpis.get('total_ae', 0):,}. "
    summary += f"Last 30 days: {kpis.get('recent_count', 0):,} "
    summary += f"({kpis.get('change_pct', 0):+.1f}% change). "
    
    if signals:
        top_signal = signals[0]
        summary += f"Top signal: {top_signal.get('reaction', 'Unknown')} "
        summary += f"(Quantum Score: {top_signal.get('quantum_score', 0):.2f}). "
    
    if kpis.get('novel_signal_count', 0) > 0:
        summary += f"Novel signals detected: {kpis.get('novel_signal_count', 0)}. "
    
    summary += "AI narrative unavailable - showing fallback summary."
    
    return summary


def _fallback_risk_alert(context: Dict[str, Any]) -> str:
    """Generate fallback risk alert without AI."""
    kpis = context.get("kpis", {})
    signals = context.get("signals", [])
    
    alert = "Risk Alert: "
    
    if kpis.get('severe_count', 0) > 0:
        alert += f"High-severity cases detected: {kpis.get('severe_count', 0)}. "
    
    if signals:
        top_signal = signals[0]
        if top_signal.get('quantum_score', 0) > 0.7:
            alert += f"High-priority signal: {top_signal.get('reaction', 'Unknown')}. "
    
    alert += "Review recommended."
    
    return alert

