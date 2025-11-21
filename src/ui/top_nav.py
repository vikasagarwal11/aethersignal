"""
Top navigation bar component for AetherSignal.
Provides fixed navigation bar across all pages.
Uses Streamlit native navigation via query params
"""

import streamlit as st


def render_top_nav():
    """Render fixed top navigation bar with page links."""
    
    # Handle navigation via query params - Streamlit native way
    nav_page = st.query_params.get("nav_page", [""])[0] if st.query_params.get("nav_page") else ""
    
    if nav_page:
        st.query_params.clear()
        try:
            if nav_page == "home":
                st.switch_page("app.py")
            elif nav_page == "quantum":
                st.switch_page("pages/1_Quantum_PV_Explorer.py")
            elif nav_page == "social":
                st.switch_page("pages/2_Social_AE_Explorer.py")
        except Exception as e:
            st.error(f"Navigation error: {e}")
    
    st.markdown("""
    <style>
    /* Hide Streamlit header */
    header[data-testid="stHeader"], 
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* Fixed top bar */
    .aether-top-nav {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        height: 70px !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        z-index: 999999 !important;
        padding: 0 3rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        border-bottom: 1px solid #334155 !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
        color: white !important;
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
        gap: 2.8rem !important;
        align-items: center !important;
    }
    
    .nav-link {
        color: #94a3b8 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        border-bottom: 3px solid transparent !important;
        transition: all 0.3s ease !important;
        display: inline-block !important;
        cursor: pointer !important;
        user-select: none !important;
    }
    
    .nav-link:hover {
        color: white !important;
        border-bottom: 3px solid rgba(96, 165, 250, 0.5) !important;
    }
    
    .nav-link.active {
        color: #60a5fa !important;
        border-bottom: 3px solid #60a5fa !important;
    }
    
    /* Push content down */
    .main .block-container {
        padding-top: 90px !important;
    }
    
    /* Sidebar offset so it doesn't hide under nav */
    [data-testid="stSidebar"] {
        margin-top: 70px !important;
        min-height: calc(100vh - 70px) !important;
    }
    
    /* Force sidebar toggle button to ALWAYS be visible and accessible */
    button[kind="header"],
    button[data-testid="baseButton-header"],
    button[aria-label*="sidebar"],
    button[aria-label*="Close"],
    button[aria-label*="Open"] {
        display: block !important;
        visibility: visible !important;
        position: fixed !important;
        top: 16px !important;
        left: 16px !important;
        z-index: 1000001 !important;
        background: rgba(15,23,42,0.9) !important;
        color: white !important;
        border: 1px solid rgba(148,163,184,0.5) !important;
        border-radius: 999px !important;
        padding: 0.4rem 0.7rem !important;
        box-shadow: 0 6px 18px rgba(15,23,42,0.4) !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        cursor: pointer !important;
        min-width: 40px !important;
        min-height: 40px !important;
    }
    
    /* Ensure sidebar toggle is visible even when sidebar is collapsed */
    [data-testid="stSidebar"][aria-expanded="false"] ~ * button[kind="header"],
    [data-testid="stSidebar"][aria-expanded="false"] + * button[kind="header"],
    button[kind="header"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Prevent sidebar from completely disappearing */
    [data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
    }
    
    [data-testid="stSidebar"][aria-expanded="false"] {
        transform: translateX(-100%) !important;
        transition: transform 300ms ease !important;
    }
    
    [data-testid="stSidebar"][aria-expanded="true"] {
        transform: translateX(0) !important;
        transition: transform 300ms ease !important;
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
        <div class="nav-left" id="nav-logo">🔬 <strong>AetherSignal</strong></div>
        <div class="nav-right">
            <span class="nav-link" id="nav-home">🏠 Home</span>
            <span class="nav-link" id="nav-quantum">⚛️ Quantum PV</span>
            <span class="nav-link" id="nav-social">🌐 Social AE</span>
        </div>
    </div>
    
    <script>
    (function() {
        console.log('[AetherSignal Nav] Script starting...');
        console.log('[AetherSignal Nav] Current URL:', window.location.href);
        console.log('[AetherSignal Nav] Current path:', window.location.pathname);
        console.log('[AetherSignal Nav] Current search:', window.location.search);
        
        // Function to navigate using query params (Streamlit native)
        function navigateToPage(page) {
            console.log('[AetherSignal Nav] Navigate called with page:', page);
            
            try {
                const currentUrl = new URL(window.location);
                currentUrl.searchParams.set('nav_page', page);
                console.log('[AetherSignal Nav] Navigating to:', currentUrl.toString());
                window.location.href = currentUrl.toString();
            } catch (e) {
                console.error('[AetherSignal Nav] Navigation error:', e);
                // Fallback: try direct URL
                if (page === 'home') {
                    window.location.href = '/';
                } else if (page === 'quantum') {
                    window.location.href = '/1_Quantum_PV_Explorer';
                } else if (page === 'social') {
                    window.location.href = '/2_Social_AE_Explorer';
                }
            }
        }
        
        // Wait for DOM to be ready
        function initNavigation() {
            console.log('[AetherSignal Nav] Initializing navigation handlers...');
            
            const navLogo = document.getElementById('nav-logo');
            const navHome = document.getElementById('nav-home');
            const navQuantum = document.getElementById('nav-quantum');
            const navSocial = document.getElementById('nav-social');
            
            console.log('[AetherSignal Nav] Elements found:', {
                logo: !!navLogo,
                home: !!navHome,
                quantum: !!navQuantum,
                social: !!navSocial
            });
            
            if (navLogo) {
                navLogo.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('[AetherSignal Nav] Logo clicked - navigating to home');
                    navigateToPage('home');
                });
            }
            
            if (navHome) {
                navHome.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('[AetherSignal Nav] Home clicked - navigating to home');
                    navigateToPage('home');
                });
            }
            
            if (navQuantum) {
                navQuantum.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('[AetherSignal Nav] Quantum PV clicked - navigating to quantum');
                    navigateToPage('quantum');
                });
            }
            
            if (navSocial) {
                navSocial.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('[AetherSignal Nav] Social AE clicked - navigating to social');
                    navigateToPage('social');
                });
            }
            
            // Set active page highlighting
            const path = window.location.pathname;
            const search = window.location.search || "";
            console.log('[AetherSignal Nav] Setting active state - path:', path, 'search:', search);
            
            if (path === '/' || path === '') {
                if (navHome) {
                    navHome.classList.add('active');
                    console.log('[AetherSignal Nav] Home is active');
                }
            } else if (path.includes('1_Quantum') || path.includes('Quantum')) {
                if (navQuantum) {
                    navQuantum.classList.add('active');
                    console.log('[AetherSignal Nav] Quantum PV is active');
                }
            } else if (path.includes('2_Social') || path.includes('Social')) {
                if (navSocial) {
                    navSocial.classList.add('active');
                    console.log('[AetherSignal Nav] Social AE is active');
                }
            }
            
            console.log('[AetherSignal Nav] Navigation initialization complete');
        }
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initNavigation);
        } else {
            initNavigation();
        }
    })();
    </script>
    """, unsafe_allow_html=True)
