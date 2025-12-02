"""
System Diagnostics - Comprehensive system diagnostics dashboard
"""

import streamlit as st
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_system_diagnostics() -> Dict[str, Any]:
    """
    Get comprehensive system diagnostics.
    
    Returns:
        Diagnostics dictionary
    """
    diagnostics = {
        "timestamp": datetime.now().isoformat(),
        "system": {},
        "services": {},
        "performance": {},
        "configuration": {},
        "errors": []
    }
    
    # System info
    try:
        import platform
        diagnostics["system"] = {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "architecture": platform.machine()
        }
    except Exception as e:
        diagnostics["errors"].append(f"System info error: {e}")
    
    # Service status
    try:
        from src.system.healthcheck import system_health
        health = system_health()
        diagnostics["services"] = health.get("services", {})
        diagnostics["system"]["overall_status"] = health.get("status", "UNKNOWN")
    except Exception as e:
        diagnostics["errors"].append(f"Health check error: {e}")
    
    # Configuration
    try:
        from src.utils.config_loader import load_config
        config = load_config()
        diagnostics["configuration"] = {
            "system_mode": config.get("system_mode", "Unknown"),
            "features_enabled": {
                k: v for k, v in config.items()
                if k.startswith("enable_") and isinstance(v, bool)
            }
        }
    except Exception as e:
        diagnostics["errors"].append(f"Config load error: {e}")
    
    # Performance metrics
    try:
        from src.mechanism.cache import MechanismCache
        cache = MechanismCache()
        cache_stats = cache.get_stats()
        diagnostics["performance"] = {
            "cache": cache_stats
        }
    except Exception as e:
        diagnostics["errors"].append(f"Performance metrics error: {e}")
    
    # Environment
    try:
        from src.system.env_validator import validate_env
        env_status = validate_env()
        diagnostics["environment"] = {
            "missing_required": env_status.get("missing_required", []),
            "missing_optional_count": len(env_status.get("missing_optional", []))
        }
    except Exception as e:
        diagnostics["errors"].append(f"Environment validation error: {e}")
    
    return diagnostics


def render_diagnostics_dashboard():
    """
    Render system diagnostics dashboard.
    """
    def page_content():
        st.title("🔍 System Diagnostics")
        st.caption("Comprehensive system health and performance monitoring")
        
        # Get diagnostics
        with st.spinner("Collecting diagnostics..."):
            diagnostics = get_system_diagnostics()
        
        # Overall Status
        st.markdown("### 📊 Overall Status")
        overall_status = diagnostics.get("system", {}).get("overall_status", "UNKNOWN")
        
        if overall_status == "OK":
            st.success(f"✅ System Status: {overall_status}")
        elif overall_status == "DEGRADED":
            st.warning(f"⚠️ System Status: {overall_status}")
        else:
            st.error(f"❌ System Status: {overall_status}")
        
        st.markdown("---")
        
        # System Information
        st.markdown("### 💻 System Information")
        system_info = diagnostics.get("system", {})
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Platform", system_info.get("platform", "Unknown"))
        col2.metric("Python", system_info.get("python_version", "Unknown"))
        col3.metric("Architecture", system_info.get("architecture", "Unknown"))
        
        st.markdown("---")
        
        # Service Status
        st.markdown("### 🔧 Service Status")
        services = diagnostics.get("services", {})
        
        service_df = pd.DataFrame([
            {"Service": service, "Status": status}
            for service, status in services.items()
        ])
        
        if not service_df.empty:
            st.dataframe(service_df, use_container_width=True)
        else:
            st.info("No service status available")
        
        st.markdown("---")
        
        # Configuration
        st.markdown("### ⚙️ Configuration")
        config = diagnostics.get("configuration", {})
        
        st.markdown(f"**System Mode:** {config.get('system_mode', 'Unknown')}")
        
        features = config.get("features_enabled", {})
        if features:
            st.markdown("**Features Enabled:**")
            for feature, enabled in features.items():
                status = "✅" if enabled else "❌"
                st.caption(f"{status} {feature.replace('enable_', '').replace('_', ' ').title()}")
        
        st.markdown("---")
        
        # Performance
        st.markdown("### ⚡ Performance Metrics")
        performance = diagnostics.get("performance", {})
        
        cache_info = performance.get("cache", {})
        if cache_info:
            col1, col2 = st.columns(2)
            col1.metric("Local Cache Size", cache_info.get("local_cache_size", 0))
            col2.metric("Redis Available", "Yes" if cache_info.get("redis_available") else "No")
        
        st.markdown("---")
        
        # Environment
        st.markdown("### 🌍 Environment")
        env = diagnostics.get("environment", {})
        
        missing_required = env.get("missing_required", [])
        if missing_required:
            st.warning(f"⚠️ Missing required env vars: {', '.join(missing_required)}")
        else:
            st.success("✅ All required environment variables set")
        
        missing_optional_count = env.get("missing_optional_count", 0)
        st.info(f"ℹ️ {missing_optional_count} optional environment variables not set")
        
        st.markdown("---")
        
        # Errors
        errors = diagnostics.get("errors", [])
        if errors:
            st.markdown("### ⚠️ Errors")
            for error in errors:
                st.error(error)
        
        # Full Diagnostics
        with st.expander("📋 Full Diagnostics JSON"):
            st.json(diagnostics)
        
        # Refresh button
        if st.button("🔄 Refresh Diagnostics"):
            st.rerun()
    
    from src.ui.layout.base_layout import render_base_layout
    render_base_layout(page_content)

