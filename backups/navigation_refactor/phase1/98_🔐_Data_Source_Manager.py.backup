"""
AetherSignal – Data Source Manager (SuperAdmin)
Enterprise-grade control panel for managing all data sources.
"""

# Load environment variables from .env file (must be first!)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import yaml
from pathlib import Path

# Restore authentication session first, before anything else
try:
    from src.auth.auth import restore_session
    restore_session()
except Exception:
    pass

from src.styles import apply_theme
from src.ui.top_nav import render_top_nav
from src.auth.auth import is_authenticated
from src.data_sources import DataSourceManager

# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="AetherSignal – Data Source Manager",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# Apply centralized theme stylesheet
# -------------------------------------------------------------------
apply_theme()

# -------------------------------------------------------------------
# TOP NAVIGATION
# -------------------------------------------------------------------
render_top_nav()

# -------------------------------------------------------------------
# AUTHENTICATION CHECK
# -------------------------------------------------------------------
if not is_authenticated():
    st.warning("⚠️ Please log in to access the Data Source Manager")
    if st.button("Go to Login"):
        st.switch_page("pages/Login.py")
    st.stop()

# -------------------------------------------------------------------
# CONFIGURATION PATHS
# -------------------------------------------------------------------
CONFIG_PATH = Path("data_source_config.yaml")
ENV_PATH = Path(".env")

# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------

def load_yaml():
    """Load YAML configuration."""
    if not CONFIG_PATH.exists():
        return {"sources": {}}
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {"sources": {}}
    except Exception as e:
        st.error(f"Error loading config: {str(e)}")
        return {"sources": {}}

def save_yaml(data):
    """Save YAML configuration."""
    try:
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        st.error(f"Error saving config: {str(e)}")
        return False

def load_env():
    """Load .env file into dictionary."""
    env_dict = {}
    if ENV_PATH.exists():
        try:
            with open(ENV_PATH, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        env_dict[key.strip()] = val.strip().strip('"').strip("'")
        except Exception as e:
            st.error(f"Error loading .env: {str(e)}")
    return env_dict

def save_env(env_dict):
    """Save dictionary to .env file."""
    try:
        with open(ENV_PATH, "w") as f:
            for k, v in env_dict.items():
                f.write(f"{k}={v}\n")
        return True
    except Exception as e:
        st.error(f"Error saving .env: {str(e)}")
        return False

# -------------------------------------------------------------------
# PAGE CONTENT
# -------------------------------------------------------------------

st.title("🔐 Data Source Manager (SuperAdmin)")

st.markdown("""
Configure all **free** and **paid** data sources.

This panel controls how AetherSignal pulls Adverse Events.

- **Free sources** always work out of the box  
- **Paid sources** are auto-disabled until an API key is added  
- System **NEVER breaks** if a source is missing a key  
""")

# Load current configuration
config = load_yaml()
env_vars = load_env()

if "sources" not in config:
    st.error("Missing sources configuration in data_source_config.yaml")
    st.stop()

datasources = config["sources"]

# Initialize manager for status checks
if 'data_source_manager' not in st.session_state:
    st.session_state.data_source_manager = DataSourceManager()

manager = st.session_state.data_source_manager

# -------------------------------------------------------------------
# FREE SOURCES SECTION
# -------------------------------------------------------------------

st.header("🟢 Free Public Sources (Always On)")

free_sources = ["openfda", "pubmed", "clinicaltrials", "dailymed", "ema_prac"]

for name in free_sources:
    src_cfg = datasources.get(name, {})
    enabled = src_cfg.get("enabled", True)
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        metadata = src_cfg.get("metadata", {})
        description = metadata.get("description", f"{name} data source")
        st.write(f"**{name.upper().replace('_', ' ')}**")
        st.caption(description)
    
    with col2:
        new_enabled = st.checkbox(
            "Enabled",
            value=enabled,
            key=f"toggle_{name}",
            help="Enable or disable this source"
        )
        if new_enabled != enabled:
            datasources[name]["enabled"] = new_enabled
    
    with col3:
        # Show status
        status = manager.get_source_status(name)
        if status.get("enabled"):
            st.success("✓ Active")
        else:
            st.warning("✗ Disabled")

# -------------------------------------------------------------------
# PAID SOURCES SECTION
# -------------------------------------------------------------------

st.header("🟡 Paid Sources (Auto-Off Without Key)")

paid_sources = [
    "human_api", "metriport", "drugbank", "vigibase", 
    "epic_fhir", "cerner_fhir", "ohdsi"
]

for name in paid_sources:
    src_cfg = datasources.get(name, {})
    enabled_mode = src_cfg.get("enabled", "auto")
    key_env = src_cfg.get("api_key_env") or src_cfg.get("key_env")
    
    if not key_env:
        # Try to infer from common patterns
        key_env = f"{name.upper().replace('_', '_')}_KEY"
        if name == "human_api":
            key_env = "HUMAN_API_KEY"
        elif name == "epic_fhir":
            key_env = "EPIC_FHIR_KEY"
        elif name == "cerner_fhir":
            key_env = "CERNER_FHIR_KEY"
    
    key_val = env_vars.get(key_env, "")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        metadata = src_cfg.get("metadata", {})
        description = metadata.get("description", f"{name} data source")
        st.write(f"**{name.upper().replace('_', ' ')}**")
        st.caption(description)
        
        # API Key input
        if key_env:
            current_display = "•" * 20 if key_val else ""
            new_key = st.text_input(
                label=f"API Key ({key_env})",
                value=current_display if key_val else "",
                key=f"apikey_{name}",
                type="password",
                placeholder="Enter API key...",
                help=f"API key will be saved to .env as {key_env}"
            )
            
            if new_key and new_key != current_display:
                env_vars[key_env] = new_key
            elif not new_key and key_val:
                # Key was cleared
                env_vars.pop(key_env, None)
    
    with col2:
        # Status indicator
        if key_val:
            st.success(f"✅ Key Present")
        else:
            st.warning("⚠️ Missing Key")
        
        # Mode selector
        mode_options = ["auto", "true", "false"]
        mode_index = mode_options.index(str(enabled_mode)) if str(enabled_mode) in mode_options else 0
        
        new_mode = st.selectbox(
            "Mode",
            options=mode_options,
            index=mode_index,
            key=f"mode_{name}",
            help="auto = enabled if key present, true = always enabled, false = disabled"
        )
        
        if new_mode != str(enabled_mode):
            datasources[name]["enabled"] = new_mode

# -------------------------------------------------------------------
# SAVE BUTTON
# -------------------------------------------------------------------

st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("💾 Save Configuration", type="primary", use_container_width=True):
        # Save YAML
        config["sources"] = datasources
        if save_yaml(config):
            # Save .env
            if save_env(env_vars):
                st.success("✅ Configuration saved successfully! 🎉")
                st.info("🔄 Reloading manager... Changes take effect immediately.")
                
                # Reload manager
                st.session_state.data_source_manager = DataSourceManager()
                st.rerun()
            else:
                st.error("❌ Failed to save .env file")
        else:
            st.error("❌ Failed to save YAML configuration")

with col2:
    if st.button("🔄 Reload from Files", use_container_width=True):
        st.session_state.data_source_manager = DataSourceManager()
        st.success("✅ Configuration reloaded from files!")
        st.rerun()

# -------------------------------------------------------------------
# LIVE STATUS CHECK
# -------------------------------------------------------------------

st.markdown("---")
st.markdown("### 🔍 Live Status Check")
st.caption("See which sources are active, disabled, or missing keys.")

# Get status for all sources
status_data = []
all_source_names = list(set(free_sources + paid_sources))

for src_name in all_source_names:
    status = manager.get_source_status(src_name)
    if status:
        status_data.append({
            "Source": src_name.replace("_", " ").title(),
            "Enabled": "✓" if status.get("enabled") else "✗",
            "Has Key": "✓" if status.get("api_key_present") else "✗",
            "Status": "Active" if (status.get("enabled") and (not status.get("api_key_env") or status.get("api_key_present"))) else "Inactive",
            "Priority": status.get("priority", 0),
            "Last Fetch": status.get("last_fetch", "Never")[:19] if status.get("last_fetch") else "Never"
        })

if status_data:
    import pandas as pd
    df = pd.DataFrame(status_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No sources configured yet.")

