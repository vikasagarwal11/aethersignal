"""
Top navigation bar for AetherSignal.
The component now consumes the shared route map, renders dropdowns,
and automatically injects the global sidebar unless a page opts out.
"""

from typing import Dict, List, Optional, Tuple

import streamlit as st

from src.auth.admin_helpers import is_admin, is_super_admin
from src.auth.auth import get_current_user, is_authenticated
from src.ui.layout.routes import get_admin_routes, get_primary_routes, page_exists
from src.ui.nav_handler import handle_nav_actions

SIDEBAR_FLAG = "_aether_sidebar_drawn"


def _is_allowed(route_config: Dict, is_auth: bool, user_roles: List[str]) -> bool:
    requires_auth = route_config.get("requires_auth", True)
    route_roles = route_config.get("roles", [])
    role_ok = not route_roles or (user_roles and any(role in user_roles for role in route_roles))
    return (not requires_auth or is_auth) and role_ok


def render_top_nav(auto_render_sidebar: bool = True) -> None:
    """Render the top navigation bar and (optionally) the sidebar."""
    # Reset sidebar flag each rerun so we can re-render
    st.session_state[SIDEBAR_FLAG] = False
    
    # Handle any pending nav actions first
    try:
        handle_nav_actions()
    except Exception:
        pass

    current_page = st.session_state.get("current_page", "")

    # Authentication context
    try:
        is_auth = is_authenticated()
        user = get_current_user() if is_auth else None
        user_email = user.get("email", "User") if isinstance(user, dict) else "User"
        user_roles: List[str] = []
        if is_auth:
            if is_super_admin():
                user_roles.append("super_admin")
            if is_admin():
                user_roles.append("admin")
    except Exception:
        is_auth = False
        user = None
        user_email = "User"
        user_roles = []

    # Load routes
    try:
        filtered_routes = get_primary_routes(require_auth=None, user_roles=user_roles or None)
        admin_routes = get_admin_routes(user_roles=user_roles or None)
    except Exception as exc:
        st.error(f"Navigation error: {exc}")
        filtered_routes = {}
        admin_routes = {}

    _render_nav_styles()

    # CRITICAL: Wrap entire nav in aether-top-nav-outer div for full-width CSS to work
    st.markdown('<div class="aether-top-nav-outer">', unsafe_allow_html=True)
    home_col, nav_col, profile_col = st.columns([1.5, 9, 2.5])

    with home_col:
        if st.button("🏠 AetherSignal", use_container_width=True, key="top_nav_home"):
            st.switch_page("app.py")

    with nav_col:
        route_entries = _collect_top_routes(filtered_routes)
        if not route_entries:
            st.caption("No routes available for this account.")
        else:
            weights = _compute_column_weights([name for name, _ in route_entries])
            nav_cols = st.columns(weights)
            for idx, (route_name, route_config) in enumerate(route_entries):
                with nav_cols[idx]:
                    _render_route_entry(
                        route_name=route_name,
                        route_config=route_config,
                        is_auth=is_auth,
                        user_roles=user_roles,
                        current_page=current_page,
                    )

    with profile_col:
        _render_profile_area(is_auth, user, user_email, admin_routes)

    # Close the wrapper div
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    if auto_render_sidebar:
        _render_global_sidebar()


def _render_nav_styles() -> None:
    """Inject CSS for the nav layout."""
    st.markdown(
        """
    <style>
    /* Fixed navigation bar - spans full viewport width, never disappears */
    /* Uses both fixed position AND container break-out for maximum compatibility */
    /* TOP NAVIGATION BAR: Full viewport width on ALL pages */
    /* Fixed positioning breaks out of all containers */
    .aether-top-nav-outer {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100vw !important;
        z-index: 999999 !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 0.9rem 2rem !important;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.35);
        border-bottom: 1px solid rgba(148, 163, 184, 0.18);
        box-sizing: border-box;
        max-width: none !important;
        min-width: 100vw !important;
    }
    
    /* Add space for fixed nav bar - prevents content from hiding behind it */
    div[data-testid="stAppViewContainer"] {
        padding-top: 70px !important;
    }
    
    /* Ensure sidebar appears above content but below nav bar */
    section[data-testid="stSidebar"] {
        z-index: 999998 !important;
        padding-top: 70px !important;
    }
    
    /* Ensure parent containers don't clip */
    .aether-top-nav-outer,
    .aether-top-nav-outer * {
        box-sizing: border-box;
    }
    
    /* Navigation columns container - prevent wrapping and enable horizontal scroll */
    .aether-top-nav-outer div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        -webkit-overflow-scrolling: touch;
        gap: 0.5rem !important;
        max-width: 100% !important;
    }
    
    /* Hide scrollbar but keep functionality */
    .aether-top-nav-outer div[data-testid="stHorizontalBlock"]::-webkit-scrollbar {
        height: 4px;
    }
    
    .aether-top-nav-outer div[data-testid="stHorizontalBlock"]::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.3);
        border-radius: 2px;
    }
    
    /* Ensure columns don't shrink and buttons stay visible */
    .aether-top-nav-outer div[data-testid="column"] {
        min-width: fit-content !important;
        flex-shrink: 0 !important;
        /* Don't stretch columns - prevents blank space below buttons */
        align-items: flex-start !important;
        display: block !important;
    }
    
    /* Remove flex stretching that creates blank space */
    .aether-top-nav-outer div[data-testid="column"] > div {
        width: 100% !important;
        height: auto !important;
        display: block !important;
        /* Prevent any stretching that creates blank space */
        flex-grow: 0 !important;
    }
    
    /* Ensure nested columns (Login/Register buttons) stay horizontal */
    .aether-top-nav-outer div[data-testid="column"] div[data-testid="stHorizontalBlock"] {
        height: auto !important;
        min-height: auto !important;
        /* Prevent vertical stacking */
        flex-wrap: nowrap !important;
    }
    
    /* Remove blank space from nested column containers (Login/Register buttons) */
    .aether-top-nav-outer div[data-testid="column"] div[data-testid="column"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        height: auto !important;
        /* Prevent vertical stacking - ensure horizontal layout */
        flex-wrap: nowrap !important;
        display: inline-block !important;
        vertical-align: top !important;
    }
    
    /* Remove blank space from button containers */
    .aether-top-nav-outer div[data-testid="column"] div[data-testid="stButton"],
    .aether-top-nav-outer div[data-testid="stButton"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        height: auto !important;
        display: inline-block !important;
    }
    
    /* Ensure Login/Register button columns container doesn't wrap */
    .aether-top-nav-outer div[data-testid="column"]:last-child div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        height: auto !important;
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* FIX: Prevent Register button double-height bug - force equal column heights */
    .aether-top-nav-outer div[data-testid="column"]:last-child div[data-testid="stHorizontalBlock"] > div {
        height: auto !important;
        min-height: auto !important;
        max-height: fit-content !important;
        align-items: flex-start !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Ensure Login/Register button columns don't stretch beyond button height */
    .aether-top-nav-outer div[data-testid="column"]:last-child div[data-testid="column"] {
        height: auto !important;
        max-height: 2.5rem !important;
        overflow: hidden !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Ensure buttons inside columns don't create extra space */
    .aether-top-nav-outer div[data-testid="column"]:last-child div[data-testid="column"] > div {
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Main nav column should take available space */
    .aether-top-nav-outer div[data-testid="column"]:nth-child(2) {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        overflow: visible !important;
    }

    .aether-top-nav-outer div[data-testid="column"] button {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: clip !important;
        padding: 0.45rem 0.75rem !important;
        font-size: 0.9rem !important;
        min-width: fit-content !important;
        width: auto !important;
        /* Ensure consistent height for all buttons (primary and secondary) */
        height: auto !important;
        min-height: 2.5rem !important;
        max-height: 2.5rem !important;
        line-height: 1.5 !important;
        box-sizing: border-box !important;
        /* Remove any extra space below buttons */
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Override Streamlit's default primary button styling to match secondary */
    .aether-top-nav-outer div[data-testid="column"] button[kind="primary"],
    .aether-top-nav-outer div[data-testid="column"] button[data-baseweb="button"][kind="primary"] {
        height: auto !important;
        min-height: 2.5rem !important;
        max-height: 2.5rem !important;
        padding: 0.45rem 0.75rem !important;
        line-height: 1.5 !important;
        margin-bottom: 0 !important;
    }

    .aether-top-nav-outer div[data-testid="column"] button:hover {
        background: rgba(255, 255, 255, 0.16) !important;
        border-color: rgba(255, 255, 255, 0.28) !important;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.45) !important;
    }

    .aether-top-nav-outer .stPopover {
        width: 260px !important;
    }

    /* Sidebar toggle helper */
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
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div id="aether-sidebar-reopen-container"></div>
    <script>
    (function() {
        const container = document.getElementById('aether-sidebar-reopen-container');
        if (!container || document.getElementById('aether-sidebar-reopen')) {
            return;
        }
        const button = document.createElement('button');
        button.id = 'aether-sidebar-reopen';
        button.title = 'Toggle navigation';
        button.innerHTML = '☰';
        button.onclick = function() {
            try {
                const toggler = document.querySelector('button[aria-label*="sidebar"], button[aria-label*="menu"]');
                if (toggler) toggler.click();
            } catch(e) {}
        };
        container.appendChild(button);
    })();
    </script>
    """,
        unsafe_allow_html=True,
    )


def _collect_top_routes(filtered_routes: Dict[str, Dict]) -> List[Tuple[str, Dict]]:
    routes: List[Tuple[str, Dict]] = []
    for route_name, route_config in filtered_routes.items():
        nav_location = route_config.get("nav_location", "both")
        if nav_location not in {"top", "both"}:
            continue
        if not route_config.get("visible_in_nav", True):
            continue
        routes.append((route_name, route_config))
    return routes


def _compute_column_weights(route_names: List[str]) -> List[int]:
    weights: List[int] = []
    for name in route_names:
        weights.append(max(4, len(name) // 2 + 2))
    return weights


def _render_route_entry(
    route_name: str,
    route_config: Dict,
    is_auth: bool,
    user_roles: List[str],
    current_page: str,
) -> None:
    icon = route_config.get("icon", "•")
    label = f"{icon} {route_name}"
    subpages = route_config.get("subpages", {})
    page = route_config.get("page")
    page_valid = page_exists(page)
    allowed = _is_allowed(route_config, is_auth, user_roles) and (page_valid or bool(subpages))

    if subpages:
        visible_subpages = [
            (name, config) for name, config in subpages.items() if config.get("visible_in_nav", True)
        ]
        if not visible_subpages:
            st.button(label, use_container_width=True, disabled=True, key=f"top_nav_no_sub_{route_name.lower().replace(' ', '_')}")
            return

        with st.popover(label, use_container_width=True):
            for subpage_name, subpage_config in visible_subpages:
                _render_subpage_button(
                    route_name=route_name,
                    subpage_name=subpage_name,
                    subpage_config=subpage_config,
                    is_auth=is_auth,
                    user_roles=user_roles,
                    current_page=current_page,
                )
    else:
        if not page_valid:
            st.button(f"{label} · coming soon", use_container_width=True, disabled=True, key=f"top_nav_soon_{page}")
            return

        is_active = current_page == page
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, use_container_width=True, type=btn_type, disabled=not allowed, key=f"top_nav_{page}"):
            st.switch_page(f"pages/{page}.py")


def _render_subpage_button(
    route_name: str,
    subpage_name: str,
    subpage_config: Dict,
    is_auth: bool,
    user_roles: List[str],
    current_page: str,
) -> None:
    sub_page = subpage_config.get("page")
    sub_route = subpage_config.get("route", subpage_name.lower().replace(" ", "_"))
    sub_icon = subpage_config.get("icon", "•")
    sub_exists = page_exists(sub_page)
    coming_soon = subpage_config.get("coming_soon", False) or not sub_exists
    allowed = _is_allowed(subpage_config, is_auth, user_roles) and sub_exists
    is_active = current_page == sub_page
    btn_type = "primary" if is_active else "secondary"
    label = f"{sub_icon} {subpage_name}"
    if coming_soon:
        label += " · coming soon"
    
    # Use route_name + sub_route for unique key (works even when sub_page is None)
    unique_key = f"top_nav_{route_name.lower().replace(' ', '_')}_{sub_route}"

    if st.button(label, use_container_width=True, disabled=not allowed or coming_soon, type=btn_type, key=unique_key):
        if sub_page:
            st.switch_page(f"pages/{sub_page}.py")


def _render_profile_area(is_auth: bool, user: Optional[Dict], user_email: str, admin_routes: Dict[str, Dict]) -> None:
    if is_auth and user:
        profile_label = f"👤 {user_email[:24]}"
        with st.popover(profile_label, use_container_width=True):
            st.markdown("**Account**")
            if st.button("👤 Profile", use_container_width=True, key="top_nav_profile"):
                st.switch_page("pages/Profile.py")
            st.divider()

            if admin_routes:
                st.markdown("**Admin Tools**")
                for idx, (admin_name, admin_config) in enumerate(admin_routes.items()):
                    admin_page = admin_config.get("page")
                    if not page_exists(admin_page):
                        continue
                    admin_label = f"{admin_config.get('icon', '🛠️')} {admin_name}"
                    if st.button(admin_label, use_container_width=True, key=f"top_nav_admin_{idx}"):
                        st.switch_page(f"pages/{admin_page}.py")
                st.divider()

            if st.button("🚪 Logout", use_container_width=True, type="secondary", key="top_nav_logout"):
                st.session_state.nav_action = "logout"
    else:
        # Use a more compact layout to prevent vertical stacking
        login_col, register_col = st.columns([1, 1], gap="small")
        with login_col:
            if st.button("🔐 Login", use_container_width=True, key="top_nav_login"):
                st.switch_page("pages/Login.py")
        with register_col:
            if st.button("📝 Register", use_container_width=True, type="primary", key="top_nav_register"):
                st.switch_page("pages/Register.py")


def _render_global_sidebar() -> None:
    """Render the sidebar exactly once per rerun."""
    if st.session_state.get(SIDEBAR_FLAG):
        return

    try:
        from src.ui import sidebar as sidebar_module

        with st.sidebar:
            sidebar_module.render_sidebar()
    except Exception as err:
        st.sidebar.error(f"Sidebar error: {err}")
    finally:
        st.session_state[SIDEBAR_FLAG] = True
