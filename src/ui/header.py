"""
Header component for AetherSignal.
Renders hero section and disclaimer banner.
"""

import streamlit as st


def render_header(page_type="quantum"):
    """
    Render main header with hero section.
    
    Args:
        page_type: "quantum" for Quantum PV Explorer, "social" for Social AE Explorer
    """
    if page_type == "social":
        # Social AE Explorer header
        st.markdown(
            """
            <div class="main-hero">
                <div class="hero-badge">
                    <span class="hero-badge-dot"></span>
                    Live demo · Session-based only
                </div>
                <h1>AetherSignal – Social AE Explorer</h1>
                <p>Pull daily potential adverse events from Reddit, X, and patient forums.
                   Real-time patient-reported signals that official reports may miss.</p>
                <div class="hero-pill-row">
                    <div class="hero-pill pill-session">
                        <span>🟢</span> Session-based only · No data stored
                    </div>
                    <div class="hero-pill pill-faers">
                        <span>🌐</span> Reddit / X / Social platforms
                    </div>
                    <div class="hero-pill pill-quantum">
                        <span>🤖</span> ML-based AE detection
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Quantum PV Explorer header (default)
        st.markdown(
            """
            <div class="main-hero">
                <div class="hero-badge">
                    <span class="hero-badge-dot"></span>
                    Live demo · Session-based only
                </div>
                <h1>AetherSignal – Quantum PV Explorer</h1>
                <p>Upload safety datasets, ask PV questions in natural language,
                   and explore exploratory signals with quantum-inspired ranking.</p>
                <div class="hero-pill-row">
                    <div class="hero-pill pill-session">
                        <span>🟢</span> Session-based only · No data stored
                    </div>
                    <div class="hero-pill pill-faers">
                        <span>📂</span> FAERS / CSV / Excel / PDF exports
                    </div>
                    <div class="hero-pill pill-quantum">
                        <span>⚛️</span> Quantum-inspired ranking (demo)
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_banner():
    """Render disclaimer banner."""
    st.markdown(
        """
        <div class="inline-banner">
            <strong>⚠️ Exploratory use only.</strong>
            Data is processed in-memory within this browser session and is cleared when you reset or close the tab.
            Spontaneous reports are subject to under-reporting and bias; no incidence or causality implied.
        </div>
        """,
        unsafe_allow_html=True,
    )

