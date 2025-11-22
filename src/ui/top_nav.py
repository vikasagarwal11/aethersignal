"""
Top navigation bar component for AetherSignal.
Provides a fixed navigation bar across all pages.
Uses simple front-end navigation via native Streamlit multipage URLs.
Does NOT interfere with Streamlit's native header, sidebar, or toolbar.
"""

import streamlit as st


def render_top_nav() -> None:
    """Render fixed top navigation bar with page links."""
    
    # Pure front-end navigation using known multipage paths.
    # This avoids Streamlit-version-specific query param APIs and keeps things stable.
    # Does NOT hide or interfere with Streamlit's native header/sidebar/toolbar.

    st.markdown(
        """
    <style>
    /* Fixed top bar - positioned below Streamlit's native header */
    .aether-top-nav {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        height: 70px !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        z-index: 999 !important;
        padding: 0 3rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        border-bottom: 1px solid #334155 !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
        color: white !important;
    }

    /* Ensure Streamlit header is visible and above our nav */
    header[data-testid="stHeader"] {
        visibility: visible !important;
        display: block !important;
        z-index: 10000 !important;
        position: relative !important;
    }
    
    /* Ensure sidebar toggle is visible and functional */
    button[kind="header"] {
        visibility: visible !important;
        display: block !important;
        z-index: 10001 !important;
    }
    
    [data-testid="stSidebar"] {
        visibility: visible !important;
    }

    .nav-left {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: white !important;
        cursor: pointer !important;
        user-select: none !important;
    }

    .nav-right {
        display: flex !important;
        gap: 2.0rem !important;
        align-items: center !important;
    }

    .nav-link {
        color: #94a3b8 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        border-bottom: 3px solid transparent !important;
        transition: all 0.2s ease !important;
        display: inline-block !important;
        cursor: pointer !important;
        user-select: none !important;
        font-size: 0.98rem !important;
    }

    .nav-link:hover {
        color: #e5e7eb !important;
        border-bottom: 3px solid rgba(96, 165, 250, 0.6) !important;
    }

    .nav-link.active {
        color: #60a5fa !important;
        border-bottom: 3px solid #60a5fa !important;
    }

    /* Push main content down so it isn't hidden behind the nav */
    .main .block-container {
        padding-top: 90px !important;
    }

    @media (max-width: 768px) {
        .aether-top-nav {
            padding: 0 1rem !important;
        }
        .nav-right {
            gap: 1rem !important;
        }
        .nav-link {
            font-size: 0.9rem !important;
        }
        .nav-left {
            font-size: 1.4rem !important;
        }
    }
    </style>

    <div class="aether-top-nav">
        <div class="nav-left" id="nav-logo">⚛️ <strong>AetherSignal</strong></div>
        <div class="nav-right">
            <span class="nav-link" id="nav-home">🏠 Home</span>
            <span class="nav-link" id="nav-quantum">⚛️ Quantum PV</span>
            <span class="nav-link" id="nav-social">🌐 Social AE</span>
        </div>
    </div>

    <script>
    (function() {
        function navigateTo(page) {
            try {
                const base = window.location.origin;
                if (page === "home") {
                    window.location.href = base + "/";
                } else if (page === "quantum") {
                    window.location.href = base + "/1_Quantum_PV_Explorer";
                } else if (page === "social") {
                    window.location.href = base + "/2_Social_AE_Explorer";
                }
            } catch (e) {
                console.error("[AetherSignal Nav] Navigation error:", e);
            }
        }

        function initNav() {
            const logo = document.getElementById("nav-logo");
            const home = document.getElementById("nav-home");
            const quantum = document.getElementById("nav-quantum");
            const social = document.getElementById("nav-social");

            if (logo) {
                logo.addEventListener("click", function(e) {
                    e.preventDefault();
                    navigateTo("home");
                });
            }
            if (home) {
                home.addEventListener("click", function(e) {
                    e.preventDefault();
                    navigateTo("home");
                });
            }
            if (quantum) {
                quantum.addEventListener("click", function(e) {
                    e.preventDefault();
                    navigateTo("quantum");
                });
            }
            if (social) {
                social.addEventListener("click", function(e) {
                    e.preventDefault();
                    navigateTo("social");
                });
            }

            // Mark active link based on current pathname
            const path = window.location.pathname || "/";
            if (path === "/" || path === "") {
                home && home.classList.add("active");
            } else if (path.indexOf("1_Quantum_PV_Explorer") !== -1) {
                quantum && quantum.classList.add("active");
            } else if (path.indexOf("2_Social_AE_Explorer") !== -1) {
                social && social.classList.add("active");
            }
        }

        // Initialize navigation when DOM is ready
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", initNav);
        } else {
            initNav();
        }
        
        // Also re-run initNav after Streamlit reruns (in case elements are recreated)
        window.addEventListener("load", function() {
            setTimeout(initNav, 100);
        });
    })();
    </script>
    """,
        unsafe_allow_html=True,
    )
