"""
Offline State Manager (CHUNK 7.9)
Manages offline mode state and auto-detection.
"""
import streamlit as st
from typing import Dict, Any, Optional
import json


class OfflineStateManager:
    """
    Manages offline mode state and detection.
    
    Features:
    - Auto-detection of offline state
    - Manual offline toggle
    - Offline capabilities tracking
    - UI badge management
    """
    
    def __init__(self):
        """Initialize offline state manager."""
        self._initialize_state()
    
    def _initialize_state(self) -> None:
        """Initialize session state for offline mode."""
        if "offline_mode" not in st.session_state:
            st.session_state.offline_mode = False
        
        if "offline_detected" not in st.session_state:
            st.session_state.offline_detected = False
        
        if "offline_capabilities" not in st.session_state:
            st.session_state.offline_capabilities = {
                "faers_join": True,
                "trend_analysis": True,
                "clustering": True,
                "duplicate_detection": True,
                "rpf": True,
                "summaries": True,
                "pdf_generation": True,
                "llm_interpretation": False,  # Requires local model
            }
    
    def detect_offline(self) -> bool:
        """
        Detect if system is currently offline.
        
        Returns:
            True if offline, False if online
        """
        try:
            # Check if we can access server capabilities
            # This is a placeholder - in real implementation would ping server
            offline_detected = st.session_state.get("offline_detected", False)
            
            # Manual override
            if st.session_state.get("force_offline", False):
                return True
            
            return offline_detected
        except Exception:
            return True  # Assume offline on error
    
    def enable_offline_mode(self) -> None:
        """Enable offline mode manually."""
        st.session_state.offline_mode = True
        st.session_state.force_offline = True
    
    def disable_offline_mode(self) -> None:
        """Disable offline mode."""
        st.session_state.offline_mode = False
        st.session_state.force_offline = False
    
    def is_offline(self) -> bool:
        """Check if currently in offline mode."""
        return st.session_state.get("offline_mode", False) or self.detect_offline()
    
    def get_offline_capabilities(self) -> Dict[str, bool]:
        """Get available offline capabilities."""
        return st.session_state.get("offline_capabilities", {})
    
    def can_perform_offline(self, capability: str) -> bool:
        """
        Check if a specific capability is available offline.
        
        Args:
            capability: Capability name (e.g., "faers_join", "trend_analysis")
            
        Returns:
            True if capability available offline
        """
        capabilities = self.get_offline_capabilities()
        return capabilities.get(capability, False)
    
    def get_status_badge(self) -> Dict[str, Any]:
        """
        Get status badge information for UI.
        
        Returns:
            Dictionary with badge text, color, and icon
        """
        if self.is_offline():
            return {
                "text": "Working Offline • Local Compute Active",
                "color": "orange",
                "icon": "🟡",
                "status": "offline"
            }
        else:
            return {
                "text": "Online • Server Mode",
                "color": "green",
                "icon": "🟢",
                "status": "online"
            }


def get_offline_manager() -> OfflineStateManager:
    """
    Get or create offline state manager instance.
    
    Returns:
        OfflineStateManager instance
    """
    if "offline_state_manager" not in st.session_state:
        st.session_state.offline_state_manager = OfflineStateManager()
    
    return st.session_state.offline_state_manager

