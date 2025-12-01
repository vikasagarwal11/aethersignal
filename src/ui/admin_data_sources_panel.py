"""
Super Admin Data Source Control Panel.
Provides full visibility and control over all data sources.
"""

import os
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from src.data_sources import DataSourceManager, FallbackMode


def render_admin_data_sources_panel(manager: Optional[DataSourceManager] = None):
    """
    Render the Super Admin Data Source Control Center.
    
    Args:
        manager: DataSourceManager instance (creates new if None)
    """
    if manager is None:
        manager = DataSourceManager()
    
    st.markdown("## 🔐 Data Source Control Center (Super Admin Only)")
    st.caption("Manage all data sources, API keys, fallback modes, and system diagnostics")
    
    # Get all source statuses
    all_statuses = manager.get_all_sources_status()
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "⚙️ Configuration",
        "🔍 Diagnostics",
        "🧪 Test Sources"
    ])
    
    with tab1:
        render_overview_tab(manager, all_statuses)
    
    with tab2:
        render_configuration_tab(manager, all_statuses)
    
    with tab3:
        render_diagnostics_tab(manager, all_statuses)
    
    with tab4:
        render_test_tab(manager, all_statuses)


def render_overview_tab(manager: DataSourceManager, statuses: Dict[str, Dict[str, Any]]):
    """Render overview tab with source status table."""
    st.markdown("### 📊 All Data Sources Status")
    
    # Prepare data for table
    table_data = []
    for source_name, status in statuses.items():
        table_data.append({
            "Source": source_name.replace("_", " ").title(),
            "Status": "✅ Active" if status["enabled"] else "❌ Disabled",
            "Fallback": status["fallback_mode"].title(),
            "API Key": "✅ Present" if status["api_key_present"] else ("⚠️ Missing" if status["api_key_env"] else "N/A"),
            "Priority": status["priority"],
            "Last Pull": status["last_fetch"] or "-",
            "Fetch Count": status["fetch_count"],
            "Error Count": status["error_count"],
            "Last Error": status["last_error"][:50] + "..." if status["last_error"] and len(status["last_error"]) > 50 else (status["last_error"] or "-")
        })
    
    df = pd.DataFrame(table_data)
    
    # Sort by priority (higher first), then by name
    df = df.sort_values(["Priority", "Source"], ascending=[False, True])
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Summary metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    enabled_count = sum(1 for s in statuses.values() if s["enabled"])
    total_count = len(statuses)
    with_key_count = sum(1 for s in statuses.values() if s["api_key_present"])
    total_errors = sum(s["error_count"] for s in statuses.values())
    
    with col1:
        st.metric("Total Sources", total_count)
    with col2:
        st.metric("Enabled", enabled_count, delta=f"{enabled_count}/{total_count}")
    with col3:
        st.metric("With API Keys", with_key_count)
    with col4:
        st.metric("Total Errors", total_errors)


def render_configuration_tab(manager: DataSourceManager, statuses: Dict[str, Dict[str, Any]]):
    """Render configuration tab for editing sources."""
    st.markdown("### ⚙️ Source Configuration")
    st.caption("Enable/disable sources, change fallback modes, and manage API keys")
    
    # Group sources by category
    free_sources = []
    paid_sources = []
    
    for source_name, status in statuses.items():
        metadata = status.get("metadata", {})
        
        if metadata.get("requires_payment"):
            paid_sources.append((source_name, status))
        else:
            free_sources.append((source_name, status))
    
    # Track changes
    if "config_changes" not in st.session_state:
        st.session_state.config_changes = {}
    
    # Free sources section
    st.markdown("#### 🌐 Free Sources")
    with st.expander("Free Data Sources", expanded=True):
        for source_name, status in sorted(free_sources, key=lambda x: x[1]["priority"], reverse=True):
            render_source_config_row(manager, source_name, status)
    
    # Paid sources section
    st.markdown("#### 💎 Paid Sources")
    st.caption("Add API keys to enable paid sources. Keys are stored securely in .env file.")
    
    with st.expander("Paid Data Sources", expanded=False):
        for source_name, status in sorted(paid_sources, key=lambda x: x[1]["priority"], reverse=True):
            render_source_config_row_with_key(manager, source_name, status)
    
    # Save button
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("💾 Save Configuration", type="primary", use_container_width=True):
            save_configuration(manager)
            st.success("✅ Configuration saved!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Reload from Files", use_container_width=True):
            # Reload manager
            from src.data_sources import DataSourceManager
            st.session_state.data_source_manager = DataSourceManager()
            st.success("✅ Configuration reloaded!")
            st.rerun()


def render_source_config_row(manager: DataSourceManager, source_name: str, status: Dict[str, Any]):
    """Render a single source configuration row."""
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        metadata = status.get("metadata", {})
        description = metadata.get("description", source_name)
        st.markdown(f"**{source_name.replace('_', ' ').title()}**")
        st.caption(description)
    
    with col2:
        enabled = st.checkbox(
            "Enabled",
            value=status["enabled"],
            key=f"config_enabled_{source_name}",
            help="Enable or disable this data source"
        )
        # Store change in session state
        if enabled != status["enabled"]:
            if "config_changes" not in st.session_state:
                st.session_state.config_changes = {}
            st.session_state.config_changes[f"{source_name}_enabled"] = enabled
    
    with col3:
        fallback_options = [mode.value for mode in FallbackMode]
        current_fallback = status["fallback_mode"]
        fallback_index = fallback_options.index(current_fallback) if current_fallback in fallback_options else 0
        
        new_fallback = st.selectbox(
            "Fallback Mode",
            options=fallback_options,
            index=fallback_index,
            key=f"config_fallback_{source_name}",
            help="Behavior when source is unavailable"
        )
        if new_fallback != current_fallback:
            if "config_changes" not in st.session_state:
                st.session_state.config_changes = {}
            st.session_state.config_changes[f"{source_name}_fallback"] = new_fallback
    
    with col4:
        priority = st.number_input(
            "Priority",
            min_value=0,
            max_value=10,
            value=status["priority"],
            key=f"config_priority_{source_name}",
            help="Higher priority = tried first"
        )
        if priority != status["priority"]:
            if "config_changes" not in st.session_state:
                st.session_state.config_changes = {}
            st.session_state.config_changes[f"{source_name}_priority"] = priority


def render_source_config_row_with_key(manager: DataSourceManager, source_name: str, status: Dict[str, Any]):
    """Render a paid source configuration row with API key input."""
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        metadata = status.get("metadata", {})
        description = metadata.get("description", source_name)
        st.markdown(f"**{source_name.replace('_', ' ').title()}**")
        st.caption(description)
        
        # API key input
        api_key_env = status.get("api_key_env")
        if api_key_env:
            current_key = os.getenv(api_key_env, "")
            key_display = "•" * 20 if current_key else ""
            
            new_key = st.text_input(
                f"API Key ({api_key_env})",
                value=key_display if current_key else "",
                type="password",
                key=f"api_key_{source_name}",
                help=f"Enter API key for {source_name}. Will be saved to .env file."
            )
            
            if new_key and new_key != key_display:
                if "config_changes" not in st.session_state:
                    st.session_state.config_changes = {}
                st.session_state.config_changes[f"{api_key_env}_value"] = new_key
    
    with col2:
        # Status indicator
        if status["api_key_present"]:
            st.success("✅ Key Present")
        else:
            st.warning("⚠️ Missing Key")
        
        # Enable/disable
        enabled = st.checkbox(
            "Enabled",
            value=status["enabled"],
            key=f"config_enabled_{source_name}",
            help="Enable or disable this data source"
        )
        if enabled != status["enabled"]:
            if "config_changes" not in st.session_state:
                st.session_state.config_changes = {}
            st.session_state.config_changes[f"{source_name}_enabled"] = enabled
        
        # Fallback mode
        fallback_options = [mode.value for mode in FallbackMode]
        current_fallback = status["fallback_mode"]
        fallback_index = fallback_options.index(current_fallback) if current_fallback in fallback_options else 0
        
        new_fallback = st.selectbox(
            "Fallback",
            options=fallback_options,
            index=fallback_index,
            key=f"config_fallback_{source_name}",
            help="Behavior when unavailable"
        )
        if new_fallback != current_fallback:
            if "config_changes" not in st.session_state:
                st.session_state.config_changes = {}
            st.session_state.config_changes[f"{source_name}_fallback"] = new_fallback


def save_configuration(manager: DataSourceManager):
    """Save configuration changes to YAML and .env files."""
    import os
    from pathlib import Path
    
    changes = st.session_state.get("config_changes", {})
    if not changes:
        return
    
    # Update YAML config
    config_path = Path("data_source_config.yaml")
    if config_path.exists():
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {"sources": {}}
        
        # Apply changes
        for key, value in changes.items():
            if key.endswith("_enabled"):
                source_name = key.replace("_enabled", "")
                if source_name in config.get("sources", {}):
                    config["sources"][source_name]["enabled"] = value
            elif key.endswith("_fallback"):
                source_name = key.replace("_fallback", "")
                if source_name in config.get("sources", {}):
                    config["sources"][source_name]["fallback"] = value
            elif key.endswith("_priority"):
                source_name = key.replace("_priority", "")
                if source_name in config.get("sources", {}):
                    config["sources"][source_name]["priority"] = value
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    # Update .env file
    env_path = Path(".env")
    env_lines = []
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_lines = f.readlines()
    
    # Update or add API keys
    for key, value in changes.items():
        if key.endswith("_value"):
            env_var = key.replace("_value", "")
            # Find and update existing line, or add new
            found = False
            for i, line in enumerate(env_lines):
                if line.startswith(f"{env_var}="):
                    env_lines[i] = f"{env_var}={value}\n"
                    found = True
                    break
            if not found:
                env_lines.append(f"{env_var}={value}\n")
    
    # Write .env file
    if env_lines:
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
    
    # Clear changes
    st.session_state.config_changes = {}
    
    # Reload manager
    from src.data_sources import DataSourceManager
    st.session_state.data_source_manager = DataSourceManager()


def render_diagnostics_tab(manager: DataSourceManager, statuses: Dict[str, Dict[str, Any]]):
    """Render diagnostics tab with detailed source information."""
    st.markdown("### 🔍 Source Diagnostics")
    
    # Source selector
    source_names = sorted(statuses.keys())
    selected_source = st.selectbox(
        "Select Source",
        options=source_names,
        format_func=lambda x: x.replace("_", " ").title()
    )
    
    if selected_source:
        status = statuses[selected_source]
        
        st.markdown("---")
        st.markdown(f"#### {selected_source.replace('_', ' ').title()} Details")
        
        # Basic info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Configuration:**")
            st.json({
                "Enabled": status["enabled"],
                "Fallback Mode": status["fallback_mode"],
                "Priority": status["priority"],
                "API Key Required": bool(status["api_key_env"]),
                "API Key Present": status["api_key_present"],
                "API Key Env Var": status["api_key_env"] or "N/A"
            })
        
        with col2:
            st.markdown("**Statistics:**")
            st.json({
                "Fetch Count": status["fetch_count"],
                "Error Count": status["error_count"],
                "Last Fetch": status["last_fetch"] or "Never",
                "Last Error": status["last_error"] or "None"
            })
        
        # Metadata
        if status.get("metadata"):
            st.markdown("**Metadata:**")
            st.json(status["metadata"])
        
        # Error log
        if status["last_error"]:
            st.markdown("---")
            st.markdown("**Last Error:**")
            st.code(status["last_error"], language="text")


def render_test_tab(manager: DataSourceManager, statuses: Dict[str, Dict[str, Any]]):
    """Render test tab for testing source connections."""
    st.markdown("### 🧪 Test Data Sources")
    st.caption("Test connections and fetch sample data from sources")
    
    # Source selector
    enabled_sources = [name for name, status in statuses.items() if status["enabled"]]
    
    if not enabled_sources:
        st.warning("⚠️ No sources are currently enabled. Enable sources in the Configuration tab.")
        return
    
    selected_source = st.selectbox(
        "Select Source to Test",
        options=enabled_sources,
        format_func=lambda x: x.replace("_", " ").title()
    )
    
    # Test parameters
    st.markdown("---")
    st.markdown("**Test Parameters:**")
    
    test_col1, test_col2 = st.columns(2)
    with test_col1:
        test_drug = st.text_input(
            "Test Drug Name",
            value="ozempic",
            key="test_drug",
            help="Drug name to search for"
        )
    with test_col2:
        test_limit = st.number_input(
            "Result Limit",
            min_value=1,
            max_value=100,
            value=10,
            key="test_limit"
        )
    
    # Test button
    if st.button("▶️ Run Test", type="primary", use_container_width=True):
        with st.spinner(f"Testing {selected_source}..."):
            # Check source status
            source_status = manager.get_source_status(selected_source)
            
            if not source_status["enabled"]:
                st.error(f"❌ Source {selected_source} is disabled")
            elif source_status["api_key_env"] and not source_status["api_key_present"]:
                st.warning(f"⚠️ API key missing for {selected_source}. Add {source_status['api_key_env']} to .env")
            else:
                # Actually test the source
                try:
                    query = {
                        "drug_name": test_drug,
                        "limit": test_limit
                    }
                    
                    results = manager.fetch_by_source(selected_source, query)
                    
                    if results:
                        st.success(f"✅ Test successful! Retrieved {len(results)} results")
                        
                        # Show sample results
                        with st.expander("📋 View Sample Results", expanded=False):
                            if len(results) > 0:
                                sample_df = pd.DataFrame(results[:5])
                                st.dataframe(sample_df, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"ℹ️ Test completed but no results returned (source may be unavailable or no data found)")
                        
                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)}")
                    st.code(str(e), language="text")
    
    # Bulk test
    st.markdown("---")
    st.markdown("**Bulk Test:**")
    if st.button("▶️ Test All Enabled Sources", use_container_width=True):
        test_results = []
        
        for source_name in enabled_sources:
            source_status = manager.get_source_status(source_name)
            test_results.append({
                "Source": source_name.replace("_", " ").title(),
                "Status": "✅ Ready" if (not source_status["api_key_env"] or source_status["api_key_present"]) else "⚠️ Missing Key",
                "Enabled": source_status["enabled"],
                "API Key": "✅" if source_status["api_key_present"] else ("⚠️" if source_status["api_key_env"] else "N/A")
            })
        
        results_df = pd.DataFrame(test_results)
        st.dataframe(results_df, use_container_width=True, hide_index=True)


def render_api_key_management(manager: DataSourceManager):
    """Render API key management section (for future implementation)."""
    st.markdown("### 🔑 API Key Management")
    st.caption("Manage API keys for data sources")
    
    st.info("💡 API keys are managed via `.env` file. Edit `.env` file directly or use environment variables.")
    
    # Show which keys are needed
    sources_needing_keys = [
        (name, status)
        for name, status in manager.get_all_sources_status().items()
        if status["api_key_env"] and not status["api_key_present"]
    ]
    
    if sources_needing_keys:
        st.markdown("**Sources Requiring API Keys:**")
        for source_name, status in sources_needing_keys:
            st.markdown(f"- **{source_name.replace('_', ' ').title()}**: `{status['api_key_env']}`")
    
    # Instructions
    with st.expander("📝 How to Add API Keys"):
        st.markdown("""
        1. Open `.env` file in project root
        2. Add your API key: `{ENV_VAR_NAME}=your_key_here`
        3. Restart the application
        4. Keys are automatically detected
        
        See `ENV_TEMPLATE.md` for all available environment variables.
        """)


