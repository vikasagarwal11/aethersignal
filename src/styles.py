"""
Enterprise Style Definitions (CHUNK A5.1)
Badge styles and color schemes for governance visualization.
"""
import streamlit as st

def apply_theme():
    """
    Apply centralized theme stylesheet to Streamlit app.
    This function applies the enterprise theme CSS across all pages.
    """
    # Check authentication status for hiding sidebar links
    try:
        from src.auth.auth import is_authenticated
        is_auth = is_authenticated()
    except Exception:
        is_auth = st.session_state.get("authenticated", False)
    
    # Build CSS with proper string formatting
    # Use f-string with {{}} to output single braces in CSS
    st.markdown(f"""
    <style>
    /* ===================================================================
       AETHER SIGNAL — FINAL LAYOUT FIX (100% WORKING)
       Removes 736px constraint, makes nav and content full-width
       =================================================================== */
    
    /* 1. Remove 736px max-width constraint */
    section[data-testid="stAppViewContainer"] {{
        max-width: none !important;
    }}
    
    div[data-testid="block-container"] {{
        max-width: none !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    
    /* 2. Full-width top nav — nuclear option */
    .aether-top-nav-outer {{
        width: 100vw !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999999 !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 0.9rem 2rem !important;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.35);
        border-bottom: 1px solid rgba(148, 163, 184, 0.18);
        box-sizing: border-box;
        max-width: none !important;
        min-width: 100vw !important;
    }}
    
    /* 3. Push content down when nav is fixed */
    div[data-testid="stAppViewContainer"] {{
        padding-top: 70px !important;
    }}
    
    section[data-testid="stSidebar"] {{
        padding-top: 70px !important;
        z-index: 999998 !important;
    }}
    
    /* 4. Ensure parent containers allow overflow (for nav bar break-out) */
    section[data-testid="stAppViewContainer"] > div {{
        padding-top: 0rem !important;
    }}
    
    div[data-testid="stVerticalBlock"]:first-child > div:first-child {{
        padding: 0 !important;
        margin: 0 !important;
    }}
    
    /* 5. Ensure all containers allow overflow for nav bar */
    .stMainBlockContainer,
    [data-testid="stVerticalBlock"] {{
        overflow: visible !important;
    }}
    
    /* 6. KILL DEV TOOLBAR FOREVER - Multiple selectors for maximum compatibility */
    section[data-testid="stDecoration"],
    .css-1d391kg,
    .css-1cpxl2t,
    div[data-testid="stDecoration"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }}
    
    /* Enterprise Theme Styles */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* Hide Login/Register from Streamlit auto-generated sidebar when authenticated */
    {"/* User is authenticated - hide Login/Register links */" if is_auth else "/* User not authenticated - show Login/Register links */"}
    {"a[href*='/Login'], a[href*='/Register'] {{ display: none !important; }}" if is_auth else ""}
    
    /* ============================================
       PHASE 2.4: Hide Streamlit Auto-Generated Sidebar
       ============================================
       We use custom navigation in src/ui/sidebar.py instead.
       This CSS is a fallback - primary method is .streamlit/config.toml
    */
    /* Hide Streamlit's auto-generated page navigation sidebar (CSS fallback) */
    section[data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* Alternative selector if above doesn't work */
    .css-1d391kg {{
        display: none !important;
    }}
    
    /* Additional fallback selectors for Streamlit auto-sidebar */
    [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* Add any additional theme styles here */
    </style>
    
    <script>
    (function() {{
        'use strict';
        
        // Function to hide Login/Register links in sidebar when authenticated
        function hideAuthLinksIfAuthenticated() {{
            try {{
                // Check if user is authenticated by looking for user email in sidebar or session
                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) return;
                
                // Check for authenticated indicators
                const hasUserEmail = sidebar.textContent.includes('@') || 
                                    sidebar.textContent.includes('vikasagarwal11@gmail.com') ||
                                    sidebar.textContent.includes('Signed in as') ||
                                    sidebar.textContent.includes('Profile & settings');
                
                // Also check if profile dropdown exists in top nav (indicates auth)
                const topNav = document.querySelector('.aether-top-nav');
                const hasProfileDropdown = topNav && topNav.querySelector('.nav-profile-dropdown');
                
                const isAuthenticated = hasUserEmail || hasProfileDropdown;
                
                if (isAuthenticated) {{
                    // Hide Login and Register links
                    const links = sidebar.querySelectorAll('a');
                    links.forEach(link => {{
                        const href = link.getAttribute('href') || '';
                        const text = link.textContent || '';
                        if ((href.includes('/Login') || text.includes('Login')) ||
                            (href.includes('/Register') || text.includes('Register'))) {{
                            link.style.display = 'none';
                            // Also hide parent list item if it exists
                            const parent = link.closest('li, div[data-testid*="stSidebarNav"]');
                            if (parent) parent.style.display = 'none';
                        }}
                    }});
                }}
            }} catch (e) {{
                // Silently fail - non-critical
            }}
        }}
        
        // Run immediately
        hideAuthLinksIfAuthenticated();
        
        // Run after DOM is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', hideAuthLinksIfAuthenticated);
        }} else {{
            hideAuthLinksIfAuthenticated();
        }}
        
        // Watch for sidebar changes (Streamlit reruns)
        const observer = new MutationObserver(() => {{
            hideAuthLinksIfAuthenticated();
        }});
        
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {{
            observer.observe(sidebar, {{
                childList: true,
                subtree: true
            }});
        }}
        
        // Also run periodically as backup
        setInterval(hideAuthLinksIfAuthenticated, 2000);
    }})();
    </script>
    """, unsafe_allow_html=True)

BADGE_STYLES = {
    "lifecycle": {
        "Triage": "#6B7280",
        "Validation": "#2563EB",
        "Assessment": "#1D4ED8",
        "Evaluation": "#0EA5E9",
        "Recommendation": "#F59E0B",
        "CAPA": "#DC2626",
        "Closed": "#059669",
        "Under Assessment": "#1D4ED8",
        "Signal Evaluation": "#0EA5E9",
        "Corrective/Preventive Action (CAPA)": "#DC2626"
    },
    "severity": {
        "low": "#10B981",
        "medium": "#FBBF24",
        "high": "#EF4444",
        "Low": "#10B981",
        "Medium": "#FBBF24",
        "High": "#EF4444",
        "Critical": "#DC2626"
    },
    "trend": {
        "stable": "#2563EB",
        "increasing": "#F59E0B",
        "spiking": "#EF4444",
        "Low": "#2563EB",
        "Medium": "#F59E0B",
        "High": "#EF4444",
        "N/A": "#6B7280"
    }
}


def load_modern_blue_styles():
    """
    Backwards-compatible wrapper used by legacy components.
    The modern theme already applies the blue palette, so we
    simply invoke apply_theme() to keep imports working.
    """
    apply_theme()
