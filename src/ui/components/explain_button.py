"""
Explain Button Component - Wave 5
Global "Explain This" button for signals, trends, and clusters
"""

import streamlit as st
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def explain_button(
    drug: str,
    reaction: str,
    evidence: Optional[Dict[str, Any]] = None,
    severity: Optional[float] = None,
    novelty_flag: bool = False,
    button_label: Optional[str] = None,
    key: Optional[str] = None
) -> None:
    """
    Render an "Explain This" button that generates AI explanation.
    
    Args:
        drug: Drug name
        reaction: Reaction name
        evidence: Optional evidence dictionary
        severity: Optional severity score
        novelty_flag: Whether this is a novel signal
        button_label: Custom button label
        key: Unique key for Streamlit button
    """
    try:
        from src.ai.explainer import AIExplainerEngine
        
        button_text = button_label or f"🧠 Explain {drug} + {reaction}"
        button_key = key or f"explain_{drug}_{reaction}"
        
        if st.button(button_text, key=button_key, use_container_width=True):
            engine = AIExplainerEngine()
            
            with st.spinner("🤖 Generating AI explanation..."):
                # Depth selector
                depth = st.radio(
                    "Explanation Depth",
                    ["Basic", "Intermediate", "Advanced"],
                    horizontal=True,
                    key=f"{button_key}_depth"
                )
                
                explanation = engine.explain_signal(
                    drug=drug,
                    reaction=reaction,
                    evidence=evidence,
                    severity=severity,
                    novelty_flag=novelty_flag,
                    depth=depth.lower()
                )
            
            # Display explanation
            st.markdown("---")
            st.markdown("### 🧠 AI Explanation")
            
            if explanation.get("fallback"):
                st.warning("⚠️ Using fallback explanation (AI service temporarily unavailable)")
            
            st.markdown(explanation.get("explanation", "Explanation not available."))
            
            # Show metadata
            with st.expander("📋 Explanation Details"):
                st.json({
                    "drug": drug,
                    "reaction": reaction,
                    "depth": explanation.get("depth", "intermediate"),
                    "severity": severity,
                    "novel": novelty_flag
                })
                
    except Exception as e:
        logger.error(f"Error rendering explain button: {e}")
        st.error(f"Explanation feature temporarily unavailable: {e}")


def explain_trend_button(
    drug: str,
    reaction: Optional[str],
    trend_data: Dict[str, Any],
    spike_detected: bool = False,
    key: Optional[str] = None
) -> None:
    """
    Render an "Explain Trend" button.
    
    Args:
        drug: Drug name
        reaction: Optional reaction name
        trend_data: Trend data dictionary
        spike_detected: Whether a spike was detected
        key: Unique key for Streamlit button
    """
    try:
        from src.ai.explainer import AIExplainerEngine
        
        button_text = f"📈 Explain Trend: {drug}" + (f" + {reaction}" if reaction else "")
        button_key = key or f"explain_trend_{drug}"
        
        if st.button(button_text, key=button_key, use_container_width=True):
            engine = AIExplainerEngine()
            
            with st.spinner("🤖 Analyzing trend..."):
                explanation = engine.explain_trend(
                    drug=drug,
                    reaction=reaction,
                    trend_data=trend_data,
                    spike_detected=spike_detected
                )
            
            st.markdown("---")
            st.markdown("### 📈 Trend Explanation")
            st.markdown(explanation.get("explanation", "Trend explanation not available."))
            
    except Exception as e:
        logger.error(f"Error explaining trend: {e}")
        st.error(f"Trend explanation unavailable: {e}")


def explain_cluster_button(
    cluster_data: Dict[str, Any],
    drug: Optional[str] = None,
    key: Optional[str] = None
) -> None:
    """
    Render an "Explain Cluster" button.
    
    Args:
        cluster_data: Cluster data dictionary
        drug: Optional drug name
        key: Unique key for Streamlit button
    """
    try:
        from src.ai.explainer import AIExplainerEngine
        
        button_text = f"🧩 Explain Cluster ({cluster_data.get('size', 0)} posts)"
        button_key = key or f"explain_cluster_{drug or 'general'}"
        
        if st.button(button_text, key=button_key, use_container_width=True):
            engine = AIExplainerEngine()
            
            with st.spinner("🤖 Analyzing cluster..."):
                explanation = engine.explain_cluster(
                    cluster_data=cluster_data,
                    drug=drug
                )
            
            st.markdown("---")
            st.markdown("### 🧩 Cluster Explanation")
            st.markdown(explanation.get("explanation", "Cluster explanation not available."))
            
    except Exception as e:
        logger.error(f"Error explaining cluster: {e}")
        st.error(f"Cluster explanation unavailable: {e}")

