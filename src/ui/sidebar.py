"""
Sidebar component for AetherSignal.
V2: Adds navigation + processing mode while keeping all existing controls.

CORRECTED VERSION - Includes missing "Usage Statistics" section.
"""

from typing import Dict, List

import streamlit as st

from src import analytics
from src import nl_query_parser
from src.ui.layout.routes import get_admin_routes, get_primary_routes, page_exists

SIDEBAR_FLAG = "_aether_sidebar_drawn"


def _set_if_not_exists(key: str, value):
    """Helper to set session state key only if it doesn't exist."""
    if key not in st.session_state:
        st.session_state[key] = value


def render_sidebar():
    """Render sidebar with navigation, filters, and controls."""
    if st.session_state.get(SIDEBAR_FLAG):
        return
    st.session_state[SIDEBAR_FLAG] = True

    # ------------------------------------------------------------------
    # 0. Initialize shared session keys (safe, idempotent)
    # ------------------------------------------------------------------
    _set_if_not_exists("active_workspace", "explorer")  # explorer | governance | inspector | executive | quantum | processing
    _set_if_not_exists("processing_mode", "auto")       # auto | server | local
    _set_if_not_exists("debug_mode", False)

    # ------------------------------------------------------------------
    # PHASE 2.3: Navigation Section (from route map)
    # ------------------------------------------------------------------
    try:
        from src.auth.auth import is_authenticated
        from src.auth.admin_helpers import is_admin, is_super_admin

        is_authed = is_authenticated()
        user_roles = []
        if is_authed:
            try:
                if is_super_admin():
                    user_roles.append("super_admin")
                if is_admin():
                    user_roles.append("admin")
            except Exception:
                pass

        filtered_routes = get_primary_routes(
            require_auth=None if is_authed else False,
            user_roles=user_roles if user_roles else None,
        )
        admin_routes = get_admin_routes(user_roles=user_roles if user_roles else None)

        st.markdown("### Navigation")

        for route_name, route_config in filtered_routes.items():
            nav_location = route_config.get("nav_location", "both")
            if nav_location not in {"sidebar", "both"}:
                continue
            if not route_config.get("visible_in_nav", True):
                continue

            icon = route_config.get("icon", "•")
            route_label = f"{icon} {route_name}"
            subpages = route_config.get("subpages", {})

            if subpages:
                default_expanded = route_name == "Data Explorer"
                with st.expander(route_label, expanded=default_expanded):
                    for subpage_name, subpage_config in subpages.items():
                        if not subpage_config.get("visible_in_nav", True):
                            continue

                        subpage_page = subpage_config.get("page")
                        sub_icon = subpage_config.get("icon", "•")
                        sub_label = f"{sub_icon} {subpage_name}"
                        sub_roles = subpage_config.get("roles", [])
                        sub_allowed = (
                            (not subpage_config.get("requires_auth", True) or is_authed)
                            and (not sub_roles or (user_roles and any(role in user_roles for role in sub_roles)))
                            and page_exists(subpage_page)
                        )
                        coming_soon = subpage_config.get("coming_soon", False) or not page_exists(subpage_page)

                        if coming_soon:
                            st.button(
                                f"{sub_label} - coming soon",
                                key=f"sidebar_{subpage_config.get('route')}_soon",
                                use_container_width=True,
                                disabled=True,
                            )
                            continue

                        if st.button(
                            sub_label,
                            key=f"sidebar_{subpage_config.get('route')}",
                            use_container_width=True,
                            disabled=not sub_allowed,
                        ):
                            st.switch_page(f"pages/{subpage_page}.py")
            else:
                page = route_config.get("page")
                route_roles = route_config.get("roles", [])
                route_allowed = (
                    (not route_config.get("requires_auth", True) or is_authed)
                    and (not route_roles or (user_roles and any(role in user_roles for role in route_roles)))
                )

                if not page_exists(page):
                    st.button(
                        f"{route_label} - coming soon",
                        key=f"sidebar_{route_config.get('route')}_soon",
                        use_container_width=True,
                        disabled=True,
                    )
                    continue

                if st.button(
                    route_label,
                    key=f"sidebar_{route_config.get('route')}",
                    use_container_width=True,
                    disabled=not route_allowed,
                ):
                    st.switch_page(f"pages/{page}.py")

        if is_authed and admin_routes:
            st.markdown("---")
            st.markdown("### Admin")
            for admin_name, admin_config in admin_routes.items():
                admin_page = admin_config.get("page")
                if not page_exists(admin_page):
                    continue
                admin_icon = admin_config.get("icon", "🛠️")
                if st.button(
                    f"{admin_icon} {admin_name}",
                    key=f"sidebar_{admin_config.get('route')}",
                    use_container_width=True,
                ):
                    st.switch_page(f"pages/{admin_page}.py")

        st.markdown("---")
    except Exception as e:
        st.markdown("### Navigation")
        st.error(f"Navigation error: {e}")
        import traceback

        st.code(traceback.format_exc())
        st.markdown("---")

    # ------------------------------------------------------------------
    # Filters & Controls Section (existing functionality preserved)
    # ------------------------------------------------------------------
    st.markdown("### Controls")

    # ------------------------------------------------------------------
    # 1. User Info (if authenticated) - Profile/Login moved to top nav
    # ------------------------------------------------------------------
    try:
        from src.auth.auth import is_authenticated, get_current_user
        is_authed = is_authenticated()
        user = get_current_user() if is_authed else None
    except Exception:
        # Fallback to session state if auth module not available
        is_authed = st.session_state.get("authenticated", False)
        user = None

    if is_authed and user:
        # Show signed-in user info (optional - profile is in top nav now)
        user_email = user.get("email", "") if user else st.session_state.get("user_email", "Unknown")
        st.caption(f"👤 {user_email}")
        st.caption("💡 Profile & settings in the top-right menu")

    # Note: Login/Register/Profile buttons removed - now in top nav profile dropdown

    # ------------------------------------------------------------------
    # 2. Session reset (unchanged functionality, slightly tidied)
    # ------------------------------------------------------------------
    st.markdown(
        "<div class='reset-session-hint'>Session</div>",
        unsafe_allow_html=True,
    )

    reset_confirmed = st.session_state.get("reset_session_confirmed", False)

    if not reset_confirmed:
        if st.button("🧹 Clear Filters & Results", key="reset_session_sidebar", use_container_width=True):
            st.session_state.reset_session_confirmed = True
            st.rerun()
    else:
        st.warning(
            "⚠️ This will clear all filters, query results, and in-memory data. "
            "Your saved data in the database will NOT be affected."
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Clear", key="confirm_reset", use_container_width=True, type="primary"):
                # PHASE 1: Expanded session reset preserve list
                # Preserves auth, navigation, workspace, engine, and UX state
                preserve_keys = [
                    # Authentication
                    "user_id",
                    "user_email",
                    "user_session",
                    "authenticated",
                    "user_profile",
                    "user_organization",
                    "user_role",
                    # Navigation & Workspace
                    "active_workspace",
                    "processing_mode",
                    "processing_mode_reason",
                    "processing_mode_override",
                    "sidebar_mode",
                    "current_page",
                    # UX & Theme
                    "theme_mode",
                    "debug_mode",
                    "quantum_enabled",
                    "include_social_ae",
                    # Engine & Heavy Objects
                    "hybrid_master_engine",
                    "browser_capabilities",
                    # Transient Navigation
                    "nav_action",
                    "show_login",
                    "show_register",
                    "show_profile",
                    # Memory & Conversation
                    "memory_state",
                ]

                preserved_state = {}
                for key in preserve_keys:
                    if key in st.session_state:
                        preserved_state[key] = st.session_state[key]

                # Clear all session state
                for k in list(st.session_state.keys()):
                    del st.session_state[k]

                # Restore preserved state
                for key, value in preserved_state.items():
                    st.session_state[key] = value

                # Try to reload data from database if authenticated
                if preserved_state.get("authenticated") and preserved_state.get("user_id"):
                    try:
                        from src.pv_storage import load_pv_data

                        user_id = preserved_state.get("user_id")
                        user_profile = preserved_state.get("user_profile", {})
                        organization = (
                            user_profile.get("organization", "") if isinstance(user_profile, dict) else ""
                        )

                        df_from_db = load_pv_data(user_id, organization)
                        if df_from_db is not None and not df_from_db.empty:
                            st.session_state.normalized_data = df_from_db
                            st.session_state.data = df_from_db
                            st.session_state.data_reloaded_from_db = True
                    except Exception:
                        # Continue without database reload if it fails
                        pass

                st.session_state.reset_session_confirmed = False
                st.rerun()

        with col2:
            if st.button("❌ Cancel", key="cancel_reset", use_container_width=True):
                st.session_state.reset_session_confirmed = False
                st.rerun()

    st.markdown("---")

    # ------------------------------------------------------------------
    # 3. Workspace Navigation (NEW in Sidebar V2)
    # ------------------------------------------------------------------
    st.markdown("### Workspace")

    workspace_label_map = {
        "explorer": "Signal Explorer",
        "governance": "Governance & Audit",
        "inspector": "Inspector Simulation",
        "executive": "Executive Dashboard",
        "quantum": "Quantum / Advanced",
        "processing": "Processing & Offline Mode",
    }

    # Map current key -> human label
    current_workspace = st.session_state.get("active_workspace", "explorer")
    current_label = workspace_label_map.get(current_workspace, "Signal Explorer")

    workspace_choice = st.radio(
        "Workspace",
        list(workspace_label_map.values()),
        index=list(workspace_label_map.values()).index(current_label),
        label_visibility="collapsed",
        key="workspace_radio",
    )

    # Reverse map label -> key
    inverse_map = {v: k for k, v in workspace_label_map.items()}
    chosen_workspace_key = inverse_map.get(workspace_choice, "explorer")
    st.session_state.active_workspace = chosen_workspace_key

    st.caption(
        {
            "explorer": "Core PV exploration: chat, signals, trends, cases.",
            "governance": "Governance dashboard, audit readiness, signal files.",
            "inspector": "Run mock inspections and Q&A simulations.",
            "executive": "Portfolio view, KPIs, and forecasting.",
            "quantum": "Quantum-inspired ranking and experimental analytics.",
            "processing": "Control where compute runs: server, local, or hybrid.",
        }[chosen_workspace_key]
    )

    st.markdown("---")

    # ------------------------------------------------------------------
    # 4. Processing Mode (ties into Hybrid Engine / 7.x roadmap)
    # ------------------------------------------------------------------
    st.markdown("### Processing Mode")

    mode_label_map = {
        "auto": "Auto (recommended)",
        "server": "Server only",
        "local": "Local / Browser",
    }

    current_mode = st.session_state.get("processing_mode", "auto")
    current_mode_label = mode_label_map.get(current_mode, "Auto (recommended)")

    mode_choice = st.radio(
        "Processing mode",
        list(mode_label_map.values()),
        index=list(mode_label_map.values()).index(current_mode_label),
        key="processing_mode_radio",
    )

    inverse_mode_map = {v: k for k, v in mode_label_map.items()}
    chosen_mode_key = inverse_mode_map.get(mode_choice, "auto")
    st.session_state.processing_mode = chosen_mode_key

    if chosen_mode_key == "auto":
        st.caption("Let AetherSignal route to server or local engine based on data size and browser capability.")
    elif chosen_mode_key == "server":
        st.caption("All heavy workloads stay on the server. Safest for regulated or very large datasets.")
    else:
        st.caption("Use local browser compute when possible. Great for offline/secure exploratory analysis.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # 4.5. Analytics Tools (NEW - Missing panels integration)
    # ------------------------------------------------------------------
    data_loaded = (
        st.session_state.get("data") is not None and 
        st.session_state.get("normalized_data") is not None
    )
    
    if data_loaded:
        st.markdown("### Analytics Tools")
        st.caption("Advanced analytics and visualization panels")
        
        analytics_col1, analytics_col2 = st.columns(2)
        
        with analytics_col1:
            if st.button("📈 Local Trends", key="sidebar_local_trends", use_container_width=True):
                st.session_state.show_local_trends = True
                st.session_state.active_tab = "local_trends"
                st.rerun()
            
            if st.button("📊 Case Clustering", key="sidebar_case_clustering", use_container_width=True):
                st.session_state.show_clustering = True
                st.session_state.active_tab = "case_clustering"
                st.rerun()
            
            if st.button("🔍 Duplicate Signals", key="sidebar_duplicates", use_container_width=True):
                st.session_state.show_duplicates = True
                st.session_state.active_tab = "duplicates"
                st.rerun()
        
        with analytics_col2:
            if st.button("⚖️ Benefit-Risk", key="sidebar_benefit_risk", use_container_width=True):
                st.session_state.show_benefit_risk = True
                st.session_state.active_tab = "benefit_risk"
                st.rerun()
            
            if st.button("🔥 Portfolio Trends", key="sidebar_portfolio_trends", use_container_width=True):
                st.session_state.show_portfolio_trends = True
                st.session_state.active_tab = "portfolio_trends"
                st.rerun()
            
            if st.button("🛠️ CAPA", key="sidebar_capa", use_container_width=True):
                st.session_state.show_capa = True
                st.session_state.active_tab = "capa"
                st.rerun()
        
        if st.button("📊 Executive Dashboard", key="sidebar_executive", use_container_width=True, type="primary"):
            st.session_state.show_executive_dashboard = True
            st.session_state.active_tab = "executive"
            st.rerun()
        
        st.markdown("---")

    # ------------------------------------------------------------------
    # 5. Advanced search (existing filters)
    # ------------------------------------------------------------------
    st.markdown(
        "### Advanced search <span class='beta-badge'>BETA</span>",
        unsafe_allow_html=True,
    )
    st.caption("Use structured filters for precise slicing. Applies to the next results view.")

    data_loaded = (
        st.session_state.get("data") is not None and 
        st.session_state.get("normalized_data") is not None
    )
    loading_in_progress = st.session_state.get("loading_in_progress", False)

    if data_loaded:
        drug_filter = st.text_input("Drug name", key="sidebar_drug")
        reaction_filter = st.text_input("Reaction / event", key="sidebar_reaction")

        with st.expander("Demographics", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                age_min = st.number_input(
                    "Min age",
                    min_value=0,
                    max_value=150,
                    value=0,
                    key="sidebar_age_min",
                )
            with c2:
                age_max = st.number_input(
                    "Max age",
                    min_value=0,
                    max_value=150,
                    value=150,
                    key="sidebar_age_max",
                )
            sex_filter = st.selectbox("Sex", ["All", "M", "F"], key="sidebar_sex")
            country_filter = st.text_input("Country", key="sidebar_country")

        with st.expander("Date & seriousness", expanded=True):
            seriousness_filter = st.checkbox("Serious cases only", key="sidebar_serious")

            st.markdown("**📅 Date Range Filter**")
            enable_date = st.checkbox("Filter by date range", key="sidebar_enable_date", value=False)
            date_from = None
            date_to = None
            if enable_date:
                c1, c2 = st.columns(2)
                with c1:
                    date_from = st.date_input("From date", key="sidebar_date_from", value=None)
                with c2:
                    date_to = st.date_input("To date", key="sidebar_date_to", value=None)

        apply_adv = st.button("Apply advanced filters", use_container_width=True, key="sidebar_apply_filters")
        clear_adv = st.button("Clear filters", use_container_width=True, key="sidebar_clear_filters")

        if apply_adv:
            filters: Dict = {}
            if drug_filter:
                filters["drug"] = drug_filter
            if reaction_filter:
                filters["reaction"] = reaction_filter
            if age_min > 0:
                filters["age_min"] = age_min
            if age_max < 150:
                filters["age_max"] = age_max
            if sex_filter != "All":
                filters["sex"] = sex_filter
            if country_filter:
                filters["country"] = country_filter
            if seriousness_filter:
                filters["seriousness"] = True
            if enable_date:
                if date_from:
                    filters["date_from"] = date_from.strftime("%Y-%m-%d")
                if date_to:
                    filters["date_to"] = date_to.strftime("%Y-%m-%d")

            is_valid, error_msg = nl_query_parser.validate_filters(filters)
            if not is_valid:
                st.error(error_msg or "Invalid filter combination.")
            elif not filters:
                st.warning("Select at least one filter to apply advanced search.")
            else:
                parts = []
                if "drug" in filters:
                    parts.append(f"drug {filters['drug']}")
                if "reaction" in filters:
                    parts.append(f"reaction {filters['reaction']}")
                if "sex" in filters:
                    parts.append("women" if filters["sex"] == "F" else "men")
                if "age_min" in filters or "age_max" in filters:
                    if "age_min" in filters and "age_max" in filters:
                        parts.append(f"age {filters['age_min']}-{filters['age_max']}")
                    elif "age_min" in filters:
                        parts.append(f"age {filters['age_min']}+")
                    elif "age_max" in filters:
                        parts.append(f"age up to {filters['age_max']}")
                if "country" in filters:
                    parts.append(f"in {filters['country']}")
                if "date_from" in filters:
                    parts.append(f"since {filters['date_from']}")
                if "date_to" in filters and "date_from" not in filters:
                    parts.append(f"until {filters['date_to']}")
                if filters.get("seriousness"):
                    parts.append("serious cases")

                query_text = (
                    "Show " + " ".join(parts)
                    if parts
                    else nl_query_parser.filters_to_natural_language(filters)
                )

                st.session_state.last_query_text = query_text
                st.session_state.last_filters = filters
                st.session_state.last_query_source = "advanced"
                st.session_state.show_results = True
                st.rerun()

        if clear_adv:
            for k in [
                "sidebar_drug",
                "sidebar_reaction",
                "sidebar_age_min",
                "sidebar_age_max",
                "sidebar_sex",
                "sidebar_country",
                "sidebar_serious",
                "sidebar_date_from",
                "sidebar_date_to",
                "sidebar_enable_date",
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state.last_filters = None
            st.session_state.show_results = False
            st.rerun()
    else:
        if st.session_state.get("data") is None or st.session_state.get("normalized_data") is None:
            if loading_in_progress:
                st.info("Data is loading. Advanced search will unlock once processing completes.")
            else:
                st.info("Upload and load data to enable advanced search.")
        else:
            st.warning("⚠️ Data loaded but filters are temporarily unavailable. Please reload the page.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # 6. ⚛️ Quantum + 🌐 Social AE (unchanged behaviour)
    # ------------------------------------------------------------------
    st.markdown("### Quantum ranking")
    quantum_disabled = (not data_loaded) or loading_in_progress
    quantum_enabled = st.checkbox(
        "Enable quantum-inspired ranking",
        value=st.session_state.get("quantum_enabled", False),
        help=(
            "Re-rank drug-event pairs using a heuristic inspired by quantum search. "
            "Deterministic, simulator-only in this demo."
        ),
        key="quantum_toggle",
        disabled=quantum_disabled,
    )
    if quantum_disabled:
        if loading_in_progress:
            st.caption("Finish loading your dataset before toggling quantum ranking.")
        else:
            st.caption("Upload and load data to enable quantum ranking.")
    st.session_state.quantum_enabled = quantum_enabled

    st.markdown("---")
    st.markdown("### Social AE signals")
    social_disabled = (not data_loaded) or loading_in_progress
    include_social_ae = st.checkbox(
        "Include Social AE signals",
        value=st.session_state.get("include_social_ae", False),
        help=(
            "Merge social media adverse event signals with FAERS data. "
            "Social signals are weighted at 40% (observational, not validated)."
        ),
        disabled=social_disabled,
    )
    if social_disabled:
        if loading_in_progress:
            st.caption("Please wait for loading to finish before merging Social AE signals.")
        else:
            st.caption("Upload and load data to include Social AE signals.")
    st.session_state.include_social_ae = include_social_ae

    st.markdown("---")

    # ------------------------------------------------------------------
    # 7. ⚡ Performance Stats & 📋 Audit Trail (unchanged)
    # ------------------------------------------------------------------
    if st.checkbox("⚡ Performance Stats", key="show_perf_stats"):
        try:
            from src.app_helpers import get_performance_stats

            perf_stats = get_performance_stats()

            st.markdown("#### Performance Metrics")
            if perf_stats.get("recent_queries"):
                st.caption(f"Recent queries: {len(perf_stats['recent_queries'])}")
                avg_time = perf_stats.get("avg_query_time_ms", 0)
                st.metric("Avg Query Time", f"{avg_time:.0f} ms")

            if st.session_state.get("normalized_data") is not None:
                df = st.session_state.normalized_data
                st.metric("Dataset Size", f"{len(df):,} rows")
                st.metric("Columns", len(df.columns))

            if perf_stats.get("recent_queries"):
                import pandas as pd

                with st.expander("Recent Query Times", expanded=False):
                    perf_df = pd.DataFrame(perf_stats["recent_queries"])
                    if not perf_df.empty:
                        st.dataframe(perf_df, use_container_width=True, hide_index=True)
        except Exception:
            st.info("Performance stats not available")

    st.markdown("---")

    if st.checkbox("📋 Audit Trail", key="show_audit_trail"):
        try:
            from src.audit_trail import render_audit_trail_viewer

            render_audit_trail_viewer()
        except Exception as e:
            st.error(f"Audit trail viewer unavailable: {e}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # 8. Usage statistics (FIXED - was missing in original proposal)
    # ------------------------------------------------------------------
    if st.checkbox("📊 Show usage statistics", key="show_stats"):
        try:
            from src import analytics
            stats = analytics.get_usage_stats()
            st.markdown("#### Usage Statistics")
            st.caption(f"Total sessions: {stats.get('total_sessions', 0)}")
            st.caption(f"Total events: {stats.get('total_events', 0)}")

            if stats.get("events_by_type"):
                st.markdown("**Events by type:**")
                for event_type, count in stats["events_by_type"].items():
                    st.caption(f"  • {event_type}: {count}")
        except Exception as e:
            st.info(f"Usage statistics not available: {e}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # 9. Developer Tools Panel (existing behaviour)
    # ------------------------------------------------------------------
    with st.expander("Developer Tools"):
        debug_mode = st.checkbox(
            "Enable Debug Mode",
            value=st.session_state.get("debug_mode", False),
            help="Show memory inspector and debug panels. Hidden from regular users.",
            key="debug_mode_toggle",
        )
        st.session_state.debug_mode = debug_mode
        if debug_mode:
            st.info("Debug mode enabled. Check the NL Query tab for the Memory Inspector panel.")

    st.markdown("---")
    st.caption("AetherSignal – Quantum PV Explorer (demo build)")
    st.caption("Exploratory only – not for regulatory decision-making.")

