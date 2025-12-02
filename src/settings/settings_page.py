"""
Global Settings Page - Streamlit Global Settings UI
"""

import streamlit as st
from src.utils.config_loader import load_config, save_config
from src.ui.layout.base_layout import render_base_layout
from src.auth.admin_helpers import is_super_admin


def render_settings_page():
    """
    Render the global settings page.
    """
    def page_content():
        st.title("⚙️ Global Settings & Feature Toggles")
        st.caption("Configure AetherSignal system-wide settings")
        
        config = load_config()
        
        # System Mode
        st.markdown("### 🎯 System Mode")
        system_modes = ["MVP", "Research", "Enterprise"]
        current_mode = config.get("system_mode", "MVP")
        mode_index = system_modes.index(current_mode) if current_mode in system_modes else 0
        
        config["system_mode"] = st.selectbox(
            "Select System Mode",
            system_modes,
            index=mode_index,
            help="MVP: Basic features only | Research: Full features | Enterprise: Production-ready"
        )
        
        st.markdown("---")
        
        # Feature Toggles
        st.markdown("### 🔧 Feature Toggles")
        st.caption("Enable or disable major features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Core Features")
            config["enable_social"] = st.checkbox(
                "Social Data Integration",
                value=config.get("enable_social", True),
                help="Enable social media AE detection"
            )
            config["enable_faers"] = st.checkbox(
                "FAERS Pipeline",
                value=config.get("enable_faers", True),
                help="Enable FAERS data integration"
            )
            config["enable_literature"] = st.checkbox(
                "Literature Integration",
                value=config.get("enable_literature", True),
                help="Enable PubMed/literature analysis"
            )
            config["enable_analytics"] = st.checkbox(
                "Executive Dashboard",
                value=config.get("enable_analytics", True),
                help="Enable executive-level analytics"
            )
        
        with col2:
            st.markdown("#### Advanced Features")
            config["enable_mechanism_ai"] = st.checkbox(
                "Mechanism AI",
                value=config.get("enable_mechanism_ai", True),
                help="Enable mechanistic reasoning engine"
            )
            config["enable_quantum_scoring"] = st.checkbox(
                "Quantum Scoring",
                value=config.get("enable_quantum_scoring", False),
                help="Enable quantum signal scoring (experimental)"
            )
            config["enable_copilot"] = st.checkbox(
                "Safety Copilot",
                value=config.get("enable_copilot", True),
                help="Enable AI safety assistant"
            )
            config["enable_workflow"] = st.checkbox(
                "Workflow Automation",
                value=config.get("enable_workflow", True),
                help="Enable case bundles and review workflows"
            )
            config["enable_evidence_governance"] = st.checkbox(
                "Evidence Governance",
                value=config.get("enable_evidence_governance", True),
                help="Enable lineage tracking and data quality scoring"
            )
        
        st.markdown("---")
        
        # Pricing Toggle (Super Admin Only)
        if is_super_admin():
            st.markdown("### 💰 Pricing System (Super Admin Only)")
            st.caption("Enable or disable the pricing/subscription system. When disabled, all features are free.")
            
            pricing_enabled = config.get("enable_pricing", False)
            config["enable_pricing"] = st.checkbox(
                "Enable Pricing System",
                value=pricing_enabled,
                help="When enabled, users see pricing tiers and subscription options. When disabled, all features are free."
            )
            
            if pricing_enabled != config["enable_pricing"]:
                st.info("💡 Pricing system status will be updated after saving. All users will see the new status on next page load.")
            
            st.markdown("---")
        
        # Performance Settings
        st.markdown("### ⚡ Performance Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            config["cache_enabled"] = st.checkbox(
                "Enable Caching",
                value=config.get("cache_enabled", True),
                help="Enable result caching for faster responses"
            )
        
        with col2:
            config["gpu_enabled"] = st.checkbox(
                "Enable GPU Acceleration",
                value=config.get("gpu_enabled", False),
                help="Use GPU for batch processing (requires CUDA)"
            )
        
        # Logging
        st.markdown("### 📝 Logging")
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        current_level = config.get("log_level", "INFO")
        level_index = log_levels.index(current_level) if current_level in log_levels else 1
        
        config["log_level"] = st.selectbox(
            "Log Level",
            log_levels,
            index=level_index
        )
        
        st.markdown("---")
        
        # Save Configuration
        st.markdown("### 💾 Save Configuration")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("💾 Save Configuration", type="primary"):
                try:
                    save_config(config)
                    st.success("Configuration saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving configuration: {e}")
        
        with col2:
            if st.button("🔄 Reset to Defaults"):
                from src.utils.config_loader import DEFAULT_CONFIG
                if st.session_state.get("confirm_reset", False):
                    save_config(DEFAULT_CONFIG)
                    st.success("Configuration reset to defaults!")
                    st.session_state.confirm_reset = False
                    st.rerun()
                else:
                    st.session_state.confirm_reset = True
                    st.warning("Click again to confirm reset")
        
        with col3:
            st.caption("💡 Changes take effect after saving and reloading the page")
        
        # Configuration Preview
        with st.expander("📋 Configuration Preview"):
            st.json(config)
    
    render_base_layout(page_content)

