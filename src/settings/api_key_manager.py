"""
API Key Manager - Universal API Key Manager
"""

import streamlit as st
from src.utils.config_loader import load_config, save_config
from src.ui.layout.base_layout import render_base_layout

SUPPORTED_KEYS = {
    "OPENAI_API_KEY": {
        "label": "OpenAI API Key",
        "required": False,
        "help": "For LLM-powered features (Copilot, Mechanism AI)"
    },
    "REDDIT_CLIENT_ID": {
        "label": "Reddit Client ID",
        "required": False,
        "help": "For Reddit social media data"
    },
    "REDDIT_SECRET": {
        "label": "Reddit Secret",
        "required": False,
        "help": "Reddit API secret"
    },
    "X_API_KEY": {
        "label": "Twitter/X API Key",
        "required": False,
        "help": "For Twitter/X social media data"
    },
    "PUBMED_API_KEY": {
        "label": "PubMed API Key",
        "required": False,
        "help": "For PubMed literature search (optional, has rate limits without key)"
    },
    "YOUTUBE_API_KEY": {
        "label": "YouTube API Key",
        "required": False,
        "help": "For YouTube comments and video data (free, 10K units/day quota)"
    },
    "EUDRA_API_KEY": {
        "label": "EudraVigilance API Key",
        "required": False,
        "help": "For European regulatory data"
    },
    "HUMAN_API_KEY": {
        "label": "HumanAPI Key",
        "required": False,
        "help": "For HumanAPI integration (paid)"
    },
    "METRIPORT_KEY": {
        "label": "Metriport Key",
        "required": False,
        "help": "For Metriport integration (paid)"
    },
    "DRUGBANK_API_KEY": {
        "label": "DrugBank API Key",
        "required": False,
        "help": "For DrugBank database access (paid)"
    },
    "VIGIBASE_KEY": {
        "label": "VigiBase Key",
        "required": False,
        "help": "For WHO VigiBase access (paid)"
    },
    "REDIS_HOST": {
        "label": "Redis Host",
        "required": False,
        "help": "Redis host for caching (optional)"
    },
    "REDIS_PORT": {
        "label": "Redis Port",
        "required": False,
        "help": "Redis port (default: 6379)"
    }
}


def render_api_key_manager():
    """
    Render the API key manager page.
    """
    def page_content():
        st.title("🔐 API Key Manager")
        st.caption("Manage API keys for external data sources and services")
        
        cfg = load_config()
        if "api_keys" not in cfg:
            cfg["api_keys"] = {}
        
        st.info("""
        **API Key Management**
        
        - Keys are stored securely in configuration
        - Missing keys will automatically disable related features
        - No keys are required for basic functionality
        - Keys are never exposed in logs or UI
        """)
        
        st.markdown("---")
        
        # Free Sources
        st.markdown("### 🆓 Free Data Sources")
        st.caption("These sources work without API keys (may have rate limits)")
        
        free_keys = [
            "PUBMED_API_KEY",
            "YOUTUBE_API_KEY",
            "REDDIT_CLIENT_ID",
            "REDDIT_SECRET"
        ]
        
        for key in free_keys:
            if key in SUPPORTED_KEYS:
                key_info = SUPPORTED_KEYS[key]
                cfg["api_keys"][key] = st.text_input(
                    f"{key_info['label']} ({key})",
                    value=cfg["api_keys"].get(key, ""),
                    type="password",
                    help=key_info.get("help", ""),
                    key=f"api_key_{key}"
                )
        
        st.markdown("---")
        
        # Paid Sources
        st.markdown("### 💳 Paid Data Sources")
        st.caption("These require subscription and API keys")
        
        paid_keys = [
            "OPENAI_API_KEY",
            "HUMAN_API_KEY",
            "METRIPORT_KEY",
            "DRUGBANK_API_KEY",
            "VIGIBASE_KEY",
            "EUDRA_API_KEY",
            "X_API_KEY"
        ]
        
        for key in paid_keys:
            if key in SUPPORTED_KEYS:
                key_info = SUPPORTED_KEYS[key]
                cfg["api_keys"][key] = st.text_input(
                    f"{key_info['label']} ({key})",
                    value=cfg["api_keys"].get(key, ""),
                    type="password",
                    help=key_info.get("help", ""),
                    key=f"api_key_{key}"
                )
        
        st.markdown("---")
        
        # Infrastructure
        st.markdown("### 🏗️ Infrastructure")
        st.caption("Optional infrastructure services")
        
        infra_keys = ["REDIS_HOST", "REDIS_PORT"]
        
        for key in infra_keys:
            if key in SUPPORTED_KEYS:
                key_info = SUPPORTED_KEYS[key]
                if key == "REDIS_PORT":
                    # Port is a number
                    port_value = cfg["api_keys"].get(key, "6379")
                    try:
                        port_int = int(port_value)
                    except:
                        port_int = 6379
                    cfg["api_keys"][key] = str(st.number_input(
                        f"{key_info['label']} ({key})",
                        value=port_int,
                        min_value=1,
                        max_value=65535,
                        help=key_info.get("help", ""),
                        key=f"api_key_{key}"
                    ))
                else:
                    cfg["api_keys"][key] = st.text_input(
                        f"{key_info['label']} ({key})",
                        value=cfg["api_keys"].get(key, ""),
                        help=key_info.get("help", ""),
                        key=f"api_key_{key}"
                    )
        
        st.markdown("---")
        
        # Save Keys
        st.markdown("### 💾 Save API Keys")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("💾 Save Keys", type="primary"):
                try:
                    save_config(cfg)
                    st.success("API keys updated successfully!")
                    st.info("⚠️ Restart the application for changes to take effect")
                except Exception as e:
                    st.error(f"Error saving keys: {e}")
        
        with col2:
            st.caption("💡 Keys are stored in configuration file. Clear keys by leaving fields blank.")
        
        # Key Status
        with st.expander("📊 Key Status"):
            st.markdown("**Configured Keys:**")
            configured = [k for k, v in cfg["api_keys"].items() if v]
            if configured:
                for key in configured:
                    st.success(f"✅ {key}")
            else:
                st.info("No keys configured (system will use free sources only)")
            
            st.markdown("**Missing Keys:**")
            missing = [k for k, v in cfg["api_keys"].items() if not v]
            if missing:
                for key in missing:
                    st.warning(f"⚠️ {key} (feature will be disabled)")
    
    render_base_layout(page_content)

