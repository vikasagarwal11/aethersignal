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
    /* Fixed top nav below the Streamlit header */
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
    
    .nav-left {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: white !important;
        cursor: pointer !important;
        pointer-events: auto !important;
        user-select: none !important;
        text-decoration: none !important;
    }
    
    .nav-left:hover {
        text-decoration: none !important;
    }
    
    .nav-left .nav-icon {
        text-decoration: none !important;
        display: inline-block;
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

    /* Always-visible sidebar reopen helper */
    #aether-sidebar-reopen {
        position: fixed;
        top: 12px;
        left: 12px;
        z-index: 100000;
        background: rgba(15,23,42,0.95);
        color: #e2e8f0;
        border: 1px solid rgba(148,163,184,0.5);
        border-radius: 8px;
        padding: 8px 10px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
        font-weight: 600;
    }
    #aether-sidebar-reopen:hover {
        color: #fff;
        box-shadow: 0 6px 16px rgba(0,0,0,0.45);
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

    <button id="aether-sidebar-reopen" title="Toggle navigation">☰</button>

    <div class="aether-top-nav">
        <a class="nav-left" href="/" data-nav="home" target="_self"><span class="nav-icon">⚛️</span> <strong>AetherSignal</strong></a>
        <div class="nav-right">
            <a class="nav-link" href="/" data-nav="home" target="_self">🏠 Home</a>
            <a class="nav-link" href="/Quantum_PV_Explorer" data-nav="quantum" target="_self">⚛️ Quantum PV</a>
            <a class="nav-link" href="/Social_AE_Explorer" data-nav="social" target="_self">🌐 Social AE</a>
        </div>
    </div>

    <script>
    (function() {
        'use strict';
        
        // Highlight active page with error handling
        function highlightActivePage() {
            try {
            const path = window.location.pathname;
            const links = document.querySelectorAll('.nav-link');
                
                if (!links || links.length === 0) return;
            
            links.forEach(link => {
                    if (link && link.classList) {
                link.classList.remove('active');
                    }
            });
            
            if (path === '/' || path === '' || path.includes('app.py')) {
                    const homeLink = Array.from(links).find(l => l && l.textContent && l.textContent.includes('Home'));
                    if (homeLink && homeLink.classList) homeLink.classList.add('active');
            } else if (path.includes('Quantum_PV_Explorer')) {
                    const quantumLink = Array.from(links).find(l => l && l.textContent && l.textContent.includes('Quantum PV'));
                    if (quantumLink && quantumLink.classList) quantumLink.classList.add('active');
            } else if (path.includes('Social_AE_Explorer')) {
                    const socialLink = Array.from(links).find(l => l && l.textContent && l.textContent.includes('Social AE'));
                    if (socialLink && socialLink.classList) socialLink.classList.add('active');
            }
            } catch (e) {
                // Gracefully handle errors without cluttering console
                if (window.console && console.warn) {
                    console.warn('Navigation highlight error (non-critical):', e.message);
                }
            }
        }
        
        // Initialize on page load
        function initNavigation() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', highlightActivePage);
        } else {
            highlightActivePage();
        }
        }
        
        initNavigation();
        
        // Debounced highlight function to prevent excessive calls
        let highlightTimeout;
        const debouncedHighlight = () => {
            clearTimeout(highlightTimeout);
            highlightTimeout = setTimeout(highlightActivePage, 200);
        };
        
        // Optimized MutationObserver - only watch navigation container
        let observer;
        function setupObserver() {
            try {
                const navContainer = document.querySelector('.aether-top-nav');
                if (navContainer && window.MutationObserver) {
                    observer = new MutationObserver((mutations) => {
                        // Only react to changes in navigation links
                        const hasNavChange = mutations.some(mutation => {
                            if (mutation.type !== 'childList') return false;
                            const target = mutation.target;
                            return target && (
                                target.classList?.contains('nav-link') ||
                                target.classList?.contains('nav-right') ||
                                target.closest?.('.aether-top-nav')
                            );
                        });
                        if (hasNavChange) {
                            debouncedHighlight();
                        }
                    });
                    observer.observe(navContainer, { 
                        childList: true, 
                        subtree: true,
                        attributes: false 
                    });
                }
            } catch (e) {
                // Observer setup failed - non-critical
            }
        }
        
        // Setup observer after a short delay to ensure DOM is ready
        setTimeout(setupObserver, 100);
        
        // Re-highlight after Streamlit reruns (with debouncing)
        if (window.parent && window.parent.postMessage) {
            const originalRerun = window.parent.postMessage;
            // Note: We can't intercept Streamlit's rerun, so we use the observer instead
        }

        // Wire the sidebar toggle button
        function setupSidebarToggle() {
            try {
                const helperBtn = document.getElementById('aether-sidebar-reopen');
        if (helperBtn) {
                    helperBtn.addEventListener('click', function() {
                        try {
                            const toggler = document.querySelector(
                                'button[aria-label*="sidebar"], ' +
                                'button[aria-label*="menu"], ' +
                                'button[kind="header"]'
                            );
                            if (toggler && toggler.click) {
                                toggler.click();
                            }
                        } catch (e) {
                            // Non-critical error
                        }
                    });
                }
            } catch (e) {
                // Non-critical error
            }
        }
        
        // Setup sidebar toggle after DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupSidebarToggle);
        } else {
            setupSidebarToggle();
        }
        
        // Handle navigation clicks - use Streamlit's page routing
        // Note: Streamlit pages are accessed via their filename (without .py) in the URL
        function setupNavigationClicks() {
            try {
                const navLinks = document.querySelectorAll('.nav-link, .nav-left');
                navLinks.forEach(link => {
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        const dataNav = this.getAttribute('data-nav');
                        const href = this.getAttribute('href');
                        
                        // Map to Streamlit page paths (without numeric prefixes)
                        let targetUrl = href || '/';
                        if (dataNav === 'quantum') {
                            targetUrl = '/Quantum_PV_Explorer';
                        } else if (dataNav === 'social') {
                            targetUrl = '/Social_AE_Explorer';
                        } else if (dataNav === 'home') {
                            targetUrl = '/';
                        }
                        
                        // Navigate in the same window using Streamlit's routing
                        window.location.href = targetUrl;
                        return false;
                    });
                });
            } catch (e) {
                console.warn('Navigation setup error:', e);
            }
        }
        
        // Setup navigation clicks
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupNavigationClicks);
        } else {
            setupNavigationClicks();
        }
    })();
    </script>
    """, unsafe_allow_html=True)
