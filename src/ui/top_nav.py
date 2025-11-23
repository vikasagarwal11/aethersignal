"""
Top navigation bar component for AetherSignal.
Provides a fixed navigation bar across all pages.
Uses native HTML links for Streamlit-compatible navigation.
"""

import streamlit as st


def render_top_nav() -> None:
    """Render fixed top navigation bar with page links."""
    
    st.markdown("""
    <style>
    /* 1. Keep Streamlit header visible */
    header[data-testid="stHeader"] {
        display: block !important;
        z-index: 10000 !important;
    }
    
    /* 2. Fixed top nav — BELOW Streamlit header */
    .aether-top-nav {
        position: fixed !important;
        top: 60px !important;      /* ← Critical: below Streamlit header */
        left: 0 !important;
        right: 0 !important;
        height: 70px !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        z-index: 10002 !important;  /* ← Above header (10000) and toggle (10001) */
        padding: 0 3rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        border-bottom: 1px solid #334155 !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
        color: white !important;
        pointer-events: auto !important;
    }
    
    /* 3. Never hide sidebar toggle */
    button[kind="header"] {
        display: block !important;
        visibility: visible !important;
        z-index: 10001 !important;
    }
    
    /* 4. Push main content down */
    .main .block-container {
        padding-top: 150px !important;  /* 60px header + 70px nav + margin */
    }
    
    .nav-left {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: white !important;
        cursor: pointer !important;
        pointer-events: auto !important;
        user-select: none !important;
    }
    
    .nav-right {
        display: flex !important;
        gap: 2.5rem !important;
        pointer-events: auto !important;
    }
    
    .nav-link {
        color: #94a3b8 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        border-bottom: 3px solid transparent !important;
        transition: all 0.3s !important;
        cursor: pointer !important;
        pointer-events: auto !important;
        user-select: none !important;
        display: inline-block !important;
    }
    
    .nav-link:hover {
        color: white !important;
    }
    
    .nav-link.active {
        color: #60a5fa !important;
        border-bottom: 3px solid #60a5fa !important;
    }
    
    @media (max-width: 768px) {
        .aether-top-nav {
            padding: 0 1rem;
        }
        .nav-right {
            gap: 1rem;
        }
        .nav-link {
            font-size: 0.9rem;
        }
        .nav-left {
            font-size: 1.4rem;
        }
    }
    </style>

    <div class="aether-top-nav">
        <div class="nav-left" id="nav-logo" style="cursor:pointer">
            ⚛️ <strong>AetherSignal</strong>
        </div>
        <div class="nav-right">
            <span class="nav-link" id="nav-home" data-page="home">🏠 Home</span>
            <span class="nav-link" id="nav-quantum" data-page="quantum">⚛️ Quantum PV</span>
            <span class="nav-link" id="nav-social" data-page="social">🌐 Social AE</span>
        </div>
    </div>

    <script>
    (function() {
        // Streamlit-compatible navigation function
        function navigateToPage(page) {
            const base = window.location.origin;
            let targetPath = '';
            
            if (page === 'home') {
                targetPath = base + '/';
            } else if (page === 'quantum') {
                targetPath = base + '/1_Quantum_PV_Explorer';
            } else if (page === 'social') {
                targetPath = base + '/2_Social_AE_Explorer';
            }
            
            if (targetPath) {
                // Direct navigation - Streamlit will handle routing
                window.location.href = targetPath;
            }
        }
        
        // Set up click handlers with immediate execution
        function initNavigation() {
            const logo = document.getElementById('nav-logo');
            const home = document.getElementById('nav-home');
            const quantum = document.getElementById('nav-quantum');
            const social = document.getElementById('nav-social');
            
            // Use event delegation on the nav container for reliability
            const navContainer = document.querySelector('.aether-top-nav');
            
            if (navContainer) {
                navContainer.addEventListener('click', function(e) {
                    const target = e.target;
                    const clickedId = target.id || target.closest('[id]')?.id;
                    
                    if (clickedId === 'nav-logo' || clickedId === 'nav-home') {
                        e.preventDefault();
                        e.stopPropagation();
                        navigateToPage('home');
                    } else if (clickedId === 'nav-quantum') {
                        e.preventDefault();
                        e.stopPropagation();
                        navigateToPage('quantum');
                    } else if (clickedId === 'nav-social') {
                        e.preventDefault();
                        e.stopPropagation();
                        navigateToPage('social');
                    }
                }, true); // Use capture phase for better reliability
            }
            
            // Also attach direct handlers as backup
            if (logo) {
                logo.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    navigateToPage('home');
                    return false;
                };
            }
            
            if (home) {
                home.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    navigateToPage('home');
                    return false;
                };
            }
            
            if (quantum) {
                quantum.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    navigateToPage('quantum');
                    return false;
                };
            }
            
            if (social) {
                social.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    navigateToPage('social');
                    return false;
                };
            }
            
            // Active page highlighting
            setTimeout(function() {
                const path = window.location.pathname;
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                    
                    if ((path === '/' || path === '' || path.endsWith('/app.py')) && link.id === 'nav-home') {
                        link.classList.add('active');
                    } else if (path.includes('1_Quantum_PV_Explorer') && link.id === 'nav-quantum') {
                        link.classList.add('active');
                    } else if (path.includes('2_Social_AE_Explorer') && link.id === 'nav-social') {
                        link.classList.add('active');
                    }
                });
            }, 50);
        }
        
        // Initialize immediately
        initNavigation();
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initNavigation);
        } else {
            setTimeout(initNavigation, 50);
        }
        
        // Re-initialize after Streamlit reruns
        window.addEventListener('load', function() {
            setTimeout(initNavigation, 100);
        });
        
        // Watch for Streamlit reruns
        const observer = new MutationObserver(function(mutations) {
            const nav = document.querySelector('.aether-top-nav');
            if (nav) {
                setTimeout(initNavigation, 100);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    })();
    </script>
    """, unsafe_allow_html=True)
