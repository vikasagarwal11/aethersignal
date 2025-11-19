"""
Sidebar component for AetherSignal.
Handles advanced filters, quantum toggle, and controls.
"""

from typing import Dict
import streamlit as st

import analytics
import nl_query_parser


def render_sidebar():
    """Render sidebar with filters and controls."""
    st.markdown("### ⚙️ Controls")
    
    # Reset session button
    st.markdown(
        "<div class='reset-session-hint'>Session</div>",
        unsafe_allow_html=True,
    )
    if st.button("↺ Reset session", key="reset_session_sidebar", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    
    st.markdown("---")

    st.markdown(
        "### 🔍 Advanced search <span class='beta-badge'>BETA</span>",
        unsafe_allow_html=True,
    )
    st.caption("Use structured filters for precise slicing. Applies to the next results view.")

    if st.session_state.normalized_data is not None:
        # Structured filters
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
            sex_filter = st.selectbox(
                "Sex", ["All", "M", "F"], key="sidebar_sex"
            )
            country_filter = st.text_input("Country", key="sidebar_country")

        with st.expander("Date & seriousness", expanded=False):
            seriousness_filter = st.checkbox("Serious cases only", key="sidebar_serious")

            enable_date = st.checkbox(
                "Filter by date range", key="sidebar_enable_date"
            )
            date_from = None
            date_to = None
            if enable_date:
                c1, c2 = st.columns(2)
                with c1:
                    date_from = st.date_input("From", key="sidebar_date_from")
                with c2:
                    date_to = st.date_input("To", key="sidebar_date_to")

        apply_adv = st.button("Apply advanced filters", use_container_width=True)
        clear_adv = st.button("Clear filters", use_container_width=True)

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
                # Build a friendly text to show in main query box
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
        st.info("Upload and load data to enable advanced search.")

    st.markdown("---")
    st.markdown("### ⚛️ Quantum ranking")
    quantum_enabled = st.checkbox(
        "Enable quantum-inspired ranking",
        value=st.session_state.get("quantum_enabled", False),
        help=(
            "Re-rank drug–event pairs using a heuristic inspired by quantum search. "
            "Deterministic, simulator-only in this demo."
        ),
    )
    st.session_state.quantum_enabled = quantum_enabled

    st.markdown("---")
    
    # Usage statistics (admin view)
    if st.checkbox("📊 Show usage statistics", key="show_stats"):
        try:
            stats = analytics.get_usage_stats()
            st.markdown("#### Usage Statistics")
            st.caption(f"Total sessions: {stats['total_sessions']}")
            st.caption(f"Total events: {stats['total_events']}")
            
            if stats.get("events_by_type"):
                st.markdown("**Events by type:**")
                for event_type, count in stats["events_by_type"].items():
                    st.caption(f"  • {event_type}: {count}")
        except Exception:
            st.info("Usage statistics not available")
    
    st.markdown("---")
    st.caption("AetherSignal – Quantum PV Explorer (demo build)")
    st.caption("Exploratory only – not for regulatory decision-making.")

