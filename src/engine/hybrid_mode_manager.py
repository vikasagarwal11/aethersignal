"""
Hybrid Mode Manager (CHUNK H1.1)
Central controller for hybrid local computation precision modes.
Selects EXACT / APPROX / HYBRID mode based on dataset size, memory availability,
browser capability, regulatory context, and user preferences.
"""
from typing import Dict, Optional, Any
from enum import Enum

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


class ComputationMode(Enum):
    """Computation precision modes."""
    EXACT = "exact"        # Full precision, regulatory-grade calculations
    HYBRID = "hybrid"      # Mix of exact and approximate based on feature
    APPROX = "approx"      # Fast approximate calculations for large datasets


class HybridModeManager:
    """
    Central controller for hybrid local computation precision modes.
    
    Selects EXACT / APPROX / HYBRID mode based on:
    - Dataset size (file size, row count)
    - Memory availability
    - Browser capability (Pyodide vs server)
    - Regulatory context (forces EXACT for SAR/DSUR/PBRER)
    - User UI toggle preference
    
    This is separate from SERVER/LOCAL/HYBRID processing modes (where computation runs).
    This manages computation PRECISION (how accurate calculations are).
    """
    
    def __init__(self):
        """Initialize Hybrid Mode Manager."""
        self.user_mode_choice: Optional[str] = None  # "exact", "hybrid", "approx", or None
        self.regulatory_override: bool = False       # SAR/DSUR/PBRER forces exact
        self.dataset_profile: Optional[Dict[str, Any]] = None
        self.browser_capability_score: Optional[float] = None  # 0.0-1.0
        
        # Load from session state if available
        if STREAMLIT_AVAILABLE:
            self.user_mode_choice = st.session_state.get("computation_mode_preference", None)
            self.regulatory_override = st.session_state.get("computation_regulatory_override", False)
            self.dataset_profile = st.session_state.get("dataset_profile", None)
            self.browser_capability_score = st.session_state.get("browser_capability_score", None)
    
    # ---------------------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------------------
    
    def set_user_preference(self, mode: Optional[str]) -> None:
        """
        Set user's preferred computation mode.
        
        Args:
            mode: "exact", "approx", "hybrid", or None (auto-detect)
        """
        if mode not in [None, "exact", "hybrid", "approx"]:
            raise ValueError(f"Invalid computation mode: {mode}. Must be 'exact', 'hybrid', 'approx', or None")
        
        self.user_mode_choice = mode
        
        if STREAMLIT_AVAILABLE:
            st.session_state.computation_mode_preference = mode
    
    def set_regulatory_override(self, value: bool = True) -> None:
        """
        Enable regulatory override (forces EXACT mode).
        
        Use this before generating regulatory reports like SAR, DSUR, PBRER,
        Signal Files, Governance Packets, or Inspector Bindings.
        
        Args:
            value: True to force exact mode, False to allow auto-detection
        """
        self.regulatory_override = value
        
        if STREAMLIT_AVAILABLE:
            st.session_state.computation_regulatory_override = value
    
    def set_dataset_profile(self, profile: Dict[str, Any]) -> None:
        """
        Set dataset profile for mode selection.
        
        Args:
            profile: Dictionary with keys:
                - file_size_mb: float (file size in megabytes)
                - row_count: int (number of rows)
                - drug_count: int (number of unique drugs)
                - reaction_count: int (number of unique reactions)
                - date_range_years: float (time span in years)
                - column_count: int (number of columns)
                - memory_footprint_mb: float (estimated memory usage)
        """
        self.dataset_profile = profile
        
        if STREAMLIT_AVAILABLE:
            st.session_state.dataset_profile = profile
    
    def set_browser_capability(self, score: float) -> None:
        """
        Set browser capability score.
        
        Args:
            score: Float between 0.0 (very weak device) and 1.0 (strong machine)
        """
        if not (0.0 <= score <= 1.0):
            raise ValueError(f"Browser capability score must be between 0.0 and 1.0, got {score}")
        
        self.browser_capability_score = score
        
        if STREAMLIT_AVAILABLE:
            st.session_state.browser_capability_score = score
    
    # ---------------------------------------------------------------------
    # CORE DECISION LOGIC
    # ---------------------------------------------------------------------
    
    def get_processing_mode(self) -> str:
        """
        Get the recommended computation precision mode.
        
        Priority order:
        1) Regulatory override → EXACT
        2) User preference
        3) Dataset size logic (75MB, 150MB thresholds)
        4) Browser capability logic
        5) Final fallback → HYBRID
        
        Returns:
            "exact", "hybrid", or "approx"
        """
        # 1) Regulatory override → EXACT (highest priority)
        if self.regulatory_override:
            return ComputationMode.EXACT.value
        
        # 2) User preference (if explicitly set)
        if self.user_mode_choice in ["exact", "hybrid", "approx"]:
            return self.user_mode_choice
        
        # 3) Dataset-aware auto-selection
        if self.dataset_profile:
            size_mb = self.dataset_profile.get("file_size_mb", 0)
            row_count = self.dataset_profile.get("row_count", 0)
            memory_footprint = self.dataset_profile.get("memory_footprint_mb", 0)
            
            # Use memory footprint if available, otherwise file size
            effective_size = memory_footprint if memory_footprint > 0 else size_mb
            
            # < 75MB or < 2M rows → EXACT (fast enough, fully accurate)
            if effective_size < 75 and row_count < 2_000_000:
                return ComputationMode.EXACT.value
            
            # 75-150MB or 2M-4M rows → HYBRID (balance accuracy and speed)
            if (75 <= effective_size <= 150) or (2_000_000 <= row_count <= 4_000_000):
                return ComputationMode.HYBRID.value
            
            # > 150MB or > 4M rows → APPROX (prevent browser freeze)
            if effective_size > 150 or row_count > 4_000_000:
                return ComputationMode.APPROX.value
        
        # 4) Browser capability fallback
        if self.browser_capability_score is not None:
            if self.browser_capability_score < 0.3:
                return ComputationMode.APPROX.value
            elif 0.3 <= self.browser_capability_score < 0.7:
                return ComputationMode.HYBRID.value
            elif self.browser_capability_score >= 0.7:
                return ComputationMode.EXACT.value
        
        # 5) Final fallback → HYBRID (safest default)
        return ComputationMode.HYBRID.value
    
    def force_exact_mode(self) -> None:
        """
        Force exact mode (convenience method for regulatory contexts).
        
        Equivalent to set_regulatory_override(True).
        """
        self.set_regulatory_override(True)
    
    def force_hybrid_mode(self) -> None:
        """
        Force hybrid mode.
        """
        self.set_user_preference("hybrid")
    
    def force_approx_mode(self) -> None:
        """
        Force approximate mode.
        """
        self.set_user_preference("approx")
    
    def clear_overrides(self) -> None:
        """
        Clear all overrides and return to auto-detection.
        """
        self.regulatory_override = False
        self.user_mode_choice = None
        
        if STREAMLIT_AVAILABLE:
            st.session_state.computation_regulatory_override = False
            st.session_state.computation_mode_preference = None
    
    # ---------------------------------------------------------------------
    # INFORMATION & UTILITIES
    # ---------------------------------------------------------------------
    
    def describe_reasoning(self) -> str:
        """
        Get human-readable explanation of why a mode was selected.
        
        Returns:
            Multi-line explanation string
        """
        mode = self.get_processing_mode()
        
        explanation_parts = [f"**Computation Mode: {mode.upper()}**\n"]
        
        if self.regulatory_override:
            explanation_parts.append("- ✅ Regulatory override active → EXACT mode (required for regulatory reports)\n")
        
        if self.user_mode_choice:
            explanation_parts.append(f"- 👤 User preference: {self.user_mode_choice.upper()} mode\n")
        
        if self.dataset_profile:
            size = self.dataset_profile.get("file_size_mb", 0)
            rows = self.dataset_profile.get("row_count", 0)
            memory = self.dataset_profile.get("memory_footprint_mb", 0)
            
            explanation_parts.append(f"- 📊 Dataset profile:\n")
            explanation_parts.append(f"  • File size: {size:.1f} MB\n")
            explanation_parts.append(f"  • Row count: {rows:,}\n")
            if memory > 0:
                explanation_parts.append(f"  • Memory footprint: {memory:.1f} MB\n")
        
        if self.browser_capability_score is not None:
            explanation_parts.append(f"- 💻 Browser capability score: {self.browser_capability_score:.2f}/1.0\n")
        
        # Add mode-specific notes
        if mode == ComputationMode.EXACT.value:
            explanation_parts.append("\n**Mode Characteristics:**\n")
            explanation_parts.append("- Full precision calculations\n")
            explanation_parts.append("- Regulatory-grade accuracy\n")
            explanation_parts.append("- Suitable for official reports\n")
        elif mode == ComputationMode.HYBRID.value:
            explanation_parts.append("\n**Mode Characteristics:**\n")
            explanation_parts.append("- Mix of exact and approximate calculations\n")
            explanation_parts.append("- Balanced accuracy and performance\n")
            explanation_parts.append("- Critical stats use exact, exploratory uses approximate\n")
        elif mode == ComputationMode.APPROX.value:
            explanation_parts.append("\n**Mode Characteristics:**\n")
            explanation_parts.append("- Fast approximate calculations\n")
            explanation_parts.append("- Optimized for large datasets\n")
            explanation_parts.append("- May sacrifice some precision for speed\n")
        
        return "".join(explanation_parts)
    
    def get_mode_characteristics(self) -> Dict[str, Any]:
        """
        Get detailed characteristics of the selected mode.
        
        Returns:
            Dictionary with mode characteristics
        """
        mode = self.get_processing_mode()
        
        characteristics = {
            "mode": mode,
            "precision_level": "high" if mode == "exact" else "medium" if mode == "hybrid" else "low",
            "speed": "slow" if mode == "exact" else "medium" if mode == "hybrid" else "fast",
            "regulatory_grade": mode == "exact",
            "best_for": []
        }
        
        if mode == ComputationMode.EXACT.value:
            characteristics["best_for"] = [
                "Regulatory reports (SAR, DSUR, PBRER)",
                "Signal Files",
                "Inspection bindings",
                "Small to medium datasets",
                "Final decision-making"
            ]
        elif mode == ComputationMode.HYBRID.value:
            characteristics["best_for"] = [
                "Medium-sized datasets",
                "Exploratory analysis",
                "Dashboard visualizations",
                "Balanced accuracy and performance"
            ]
        elif mode == ComputationMode.APPROX.value:
            characteristics["best_for"] = [
                "Large datasets (>150MB)",
                "Real-time dashboards",
                "Quick insights",
                "Initial exploratory analysis"
            ]
        
        return characteristics


# Global singleton instance (can be accessed across modules)
_global_mode_manager: Optional[HybridModeManager] = None


def get_hybrid_mode_manager() -> HybridModeManager:
    """
    Get or create the global Hybrid Mode Manager instance.
    
    Returns:
        HybridModeManager singleton
    """
    global _global_mode_manager
    
    if _global_mode_manager is None:
        _global_mode_manager = HybridModeManager()
    
    return _global_mode_manager


def get_current_computation_mode() -> str:
    """
    Convenience function to get current computation mode.
    
    Returns:
        Current computation mode ("exact", "hybrid", or "approx")
    """
    manager = get_hybrid_mode_manager()
    return manager.get_processing_mode()

