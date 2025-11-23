"""
Top navigation bar component for AetherSignal.
Provides a fixed navigation bar across all pages.
FIXED: Navigation positioning and click handling
"""

import streamlit as st


def render_top_nav() -> None:
    """Render fixed top navigation bar with page links."""
    
    st.markdown("""
    <style>
    /* 1. Ensure Streamlit header is visible and positioned correctly */
    header[data-testid="stHeader"] {
        display: block !important;
        visibility: visible !important;
        z-index: 999990 !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 60px !important;
    }
    
    /* 2. Fixed top nav BELOW Streamlit header */
    .aether-top-nav {
        position: fixed !important;
        top: 60px !important;
        left: 0 !important;
        right: 0 !important;
        height: 70px !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        z-index: 999980 !important;
        padding: 0 3rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        border-bottom: 1px solid #334155 !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
        color: white !important;
        pointer-events: auto !important;
    }
    
    /* 3. Sidebar toggle button - ALWAYS visible */
    button[kind="header"],
    button[data-testid="baseButton-header"] {
        display: block !important;
        visibility: visible !important;
        z-index: 999991 !important;
        position: fixed !important;
        top: 16px !important;
        left: 16px !important;
    }
    
    /* 4. Push main content down to account for both headers */
    .main .block-container {
        padding-top: 150px !important;
    }
    
    /* 5. Sidebar positioning below both headers */
    [data-testid="stSidebar"] {
        top: 130px !important;
        height: calc(100vh - 130px) !important;
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
        <div class="nav-left" onclick="window.location.href='/'">
            ⚛️ <strong>AetherSignal</strong>
        </div>
        <div class="nav-right">
            <span class="nav-link" onclick="window.location.href='/'">🏠 Home</span>
            <span class="nav-link" onclick="window.location.href='/1_Quantum_PV_Explorer'">⚛️ Quantum PV</span>
            <span class="nav-link" onclick="window.location.href='/2_Social_AE_Explorer'">🌐 Social AE</span>
        </div>
    </div>

    <script>
    (function() {
        // Highlight active page
        function highlightActivePage() {
            const path = window.location.pathname;
            const links = document.querySelectorAll('.nav-link');
            
            links.forEach(link => {
                link.classList.remove('active');
            });
            
            if (path === '/' || path === '' || path.includes('app.py')) {
                const homeLink = Array.from(links).find(l => l.textContent.includes('Home'));
                if (homeLink) homeLink.classList.add('active');
            } else if (path.includes('1_Quantum_PV_Explorer')) {
                const quantumLink = Array.from(links).find(l => l.textContent.includes('Quantum PV'));
                if (quantumLink) quantumLink.classList.add('active');
            } else if (path.includes('2_Social_AE_Explorer')) {
                const socialLink = Array.from(links).find(l => l.textContent.includes('Social AE'));
                if (socialLink) socialLink.classList.add('active');
            }
        }
        
        // Run on load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', highlightActivePage);
        } else {
            highlightActivePage();
        }
        
        // Re-run after Streamlit updates
        setTimeout(highlightActivePage, 100);
        
        // Watch for DOM changes
        const observer = new MutationObserver(highlightActivePage);
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    """, unsafe_allow_html=True)
