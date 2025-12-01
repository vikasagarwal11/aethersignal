"""
RPF Weight Configuration Panel (CHUNK A - Part 2)
Allows users to adjust RPF component weights dynamically.
"""
import streamlit as st
from typing import Dict


def render_rpf_weights_panel() -> Dict[str, float]:
    """
    Render RPF weight configuration panel.
    
    Returns:
        Dictionary with normalized weights
    """
    st.subheader("⚖️ RPF Weight Configuration")
    st.caption("Adjust the relative importance of each RPF component. Weights will auto-normalize to sum to 1.0.")
    
    # Initialize default weights if not set
    if "rpf_weights" not in st.session_state:
        st.session_state.rpf_weights = {
            "cases": 0.30,
            "serious": 0.30,
            "reporting_slope": 0.20,
            "disproportionality": 0.20
        }
    
    w = st.session_state.rpf_weights
    
    # Create sliders
    col1, col2 = st.columns(2)
    
    with col1:
        cases = st.slider(
            "📊 Case Volume Weight",
            0.0, 1.0,
            w.get("cases", 0.30),
            0.05,
            help="Weight for total case count in RPF calculation"
        )
        
        serious = st.slider(
            "⚠️ Seriousness Weight",
            0.0, 1.0,
            w.get("serious", 0.30),
            0.05,
            help="Weight for serious case count in RPF calculation"
        )
    
    with col2:
        slope = st.slider(
            "📈 Reporting Trend Weight",
            0.0, 1.0,
            w.get("reporting_slope", 0.20),
            0.05,
            help="Weight for reporting trend slope in RPF calculation"
        )
        
        dispro = st.slider(
            "🔍 Disproportionality Weight",
            0.0, 1.0,
            w.get("disproportionality", 0.20),
            0.05,
            help="Weight for disproportionality (PRR-lite) in RPF calculation"
        )
    
    # Calculate total
    total = cases + serious + slope + dispro
    
    # Auto-normalize if needed
    if abs(total - 1.0) > 0.01:
        st.warning(f"⚠️ Weights sum to {total:.2f} — auto-normalizing to 1.0.")
        cases, serious, slope, dispro = [
            v / total for v in [cases, serious, slope, dispro]
        ]
    
    # Update session state
    st.session_state.rpf_weights = {
        "cases": round(cases, 3),
        "serious": round(serious, 3),
        "reporting_slope": round(slope, 3),
        "disproportionality": round(dispro, 3)
    }
    
    # Display current weights
    st.markdown("---")
    st.markdown("#### Current Weights:")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Cases", f"{st.session_state.rpf_weights['cases']:.1%}")
    with col2:
        st.metric("Serious", f"{st.session_state.rpf_weights['serious']:.1%}")
    with col3:
        st.metric("Trend", f"{st.session_state.rpf_weights['reporting_slope']:.1%}")
    with col4:
        st.metric("Dispro", f"{st.session_state.rpf_weights['disproportionality']:.1%}")
    
    # Reset button
    if st.button("🔄 Reset to Defaults"):
        st.session_state.rpf_weights = {
            "cases": 0.30,
            "serious": 0.30,
            "reporting_slope": 0.20,
            "disproportionality": 0.20
        }
        st.rerun()
    
    return st.session_state.rpf_weights

