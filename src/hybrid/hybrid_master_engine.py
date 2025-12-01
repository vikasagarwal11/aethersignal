"""
Hybrid Master Engine (CHUNK 1 - Part 1.1)
Unified coordinator for all hybrid processing modes.

This engine ties together:
- Dataset profiling
- Browser capability detection
- Mode decision (local/server/hybrid)
- Query routing
- Result caching
- Error handling and fallback
"""
import streamlit as st
from typing import Dict, Any, Optional
import pandas as pd

try:
    from src.engine.dataset_profiler import DatasetProfiler
    from src.engine.browser_capability_detector import BrowserCapabilityDetector
    from src.engine.hybrid_mode_manager import HybridModeManager, ComputationMode
    PROFILER_AVAILABLE = True
except ImportError:
    PROFILER_AVAILABLE = False

try:
    from src.hybrid.router import HybridSummaryRouter
    from src.ai.hybrid_router import run_hybrid_rpf, run_hybrid_query
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False

try:
    from src.utils.safe_executor import safe_execute
    SAFE_EXECUTE_AVAILABLE = True
except ImportError:
    SAFE_EXECUTE_AVAILABLE = False

try:
    from src.hybrid.hybrid_cache import get_from_cache, save_to_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


class HybridMasterEngine:
    """
    Master coordinator for hybrid processing.
    
    Handles:
    - Initialization (profiling, browser detection, mode selection)
    - Query routing (local/server/hybrid)
    - Result caching
    - Error handling and automatic fallback
    """
    
    def __init__(self):
        """Initialize Hybrid Master Engine."""
        self.mode = None
        self.profile = None
        self.browser = None
        self.computation_mode = None
        self._initialized = False
        
        # Initialize routers
        if ROUTER_AVAILABLE:
            self.summary_router = HybridSummaryRouter()
        else:
            self.summary_router = None
    
    def initialize(self, df: Optional[pd.DataFrame] = None) -> str:
        """
        Initialize hybrid engine with dataset profiling and browser detection.
        
        Args:
            df: Optional DataFrame to profile. If None, uses session state.
            
        Returns:
            Selected processing mode ("local", "server", or "hybrid")
        """
        if self._initialized and df is None:
            # Use cached initialization
            self.mode = st.session_state.get("processing_mode", "server")
            return self.mode
        
        # Step 1: Profile dataset
        if PROFILER_AVAILABLE:
            profiler = DatasetProfiler()
            if df is not None:
                self.profile = profiler.profile(df)
            else:
                self.profile = st.session_state.get("dataset_profile")
            
            if self.profile:
                st.session_state["dataset_profile"] = self.profile
        
        # Step 2: Detect browser capabilities
        if PROFILER_AVAILABLE:
            detector = BrowserCapabilityDetector()
            self.browser = detector.detect()
            st.session_state["browser_capabilities"] = self.browser
        
        # Step 3: Decide processing mode
        self.mode = self._decide_mode()
        st.session_state["processing_mode"] = self.mode
        
        # Step 4: Initialize computation mode manager
        if PROFILER_AVAILABLE:
            mode_manager = HybridModeManager()
            if self.profile:
                mode_manager.set_dataset_profile(self.profile)
            if self.browser:
                mode_manager.set_browser_capability_score(
                    self.browser.get("capability_score", 0.5)
                )
            self.computation_mode = mode_manager.get_mode()
            st.session_state["computation_mode"] = self.computation_mode.value if hasattr(self.computation_mode, 'value') else str(self.computation_mode)
        
        self._initialized = True
        return self.mode
    
    def _decide_mode(self) -> str:
        """
        Decide processing mode based on dataset and browser capabilities.
        
        Returns:
            "local", "server", or "hybrid"
        """
        # Check user preference first (from sidebar - supports "auto", "server", "local")
        user_preference = st.session_state.get("processing_mode", "auto")
        
        # Handle sidebar values: "auto", "server", "local"
        # Map "local" to "local", "server" to "server", "auto" to auto-detection
        if user_preference == "local":
            return "local"
        elif user_preference == "server":
            return "server"
        elif user_preference in ["hybrid", "auto"]:
            # For "auto" or "hybrid", proceed with auto-detection below
            pass
        # Otherwise fall through to auto-detection
        
        # Auto-decide based on capabilities
        if not self.profile or not self.browser:
            return "server"  # Safe fallback
        
        # Check browser capabilities
        wasm_available = self.browser.get("wasm_supported", False)
        capability_score = self.browser.get("capability_score", 0.0)
        
        # Check dataset profile
        size_mb = self.profile.get("file_size_mb", 0)
        row_count = self.profile.get("row_count", 0)
        
        # Decision logic
        if wasm_available and capability_score >= 0.6:
            # Good browser - can handle local processing
            if size_mb <= 150 and row_count < 2_000_000:
                return "local"
            elif size_mb <= 300 and row_count < 5_000_000:
                return "hybrid"
            else:
                return "server"
        else:
            # Weak browser or no WASM - use server
            return "server"
    
    @safe_execute if SAFE_EXECUTE_AVAILABLE else (lambda f: f)
    def run_query(
        self,
        query: str,
        df: Optional[pd.DataFrame] = None,
        query_type: str = "conversational"
    ) -> Dict[str, Any]:
        """
        Run query using appropriate processing mode.
        
        Args:
            query: User query string
            df: Optional DataFrame. If None, uses session state.
            query_type: Type of query ("conversational", "summary", "rpf", etc.)
            
        Returns:
            Query result dictionary
        """
        # Ensure initialized
        if not self._initialized:
            if df is None:
                df = st.session_state.get("normalized_data")
            self.initialize(df)
        
        # Get current mode
        mode = st.session_state.get("processing_mode", self.mode or "server")
        
        # Get DataFrame
        if df is None:
            df = st.session_state.get("normalized_data")
        
        if df is None or df.empty:
            return {
                "error": "No data available",
                "text": "Please upload data first.",
                "mode": mode
            }
        
        # Check cache first (Part 1.5 - Caching Layer)
        df_profile = self.profile or {}
        if CACHE_AVAILABLE and query_type == "conversational":
            cached = get_from_cache(query, df_profile)
            if cached:
                cached["mode"] = mode
                return cached.get("result", cached)
        
        # Route based on query type
        try:
            if query_type == "summary":
                return self._run_summary_query(df, mode)
            elif query_type == "rpf":
                return self._run_rpf_query(df, mode)
            elif query_type == "conversational":
                return self._run_conversational_query(query, df, mode)
            else:
                # Default to conversational
                return self._run_conversational_query(query, df, mode)
        except Exception as e:
            # Automatic fallback (Part 1.6 - Fallback Handling)
            st.warning(f"⚠️ {mode.title()} mode failed. Falling back to server mode.")
            try:
                fallback_result = self._run_conversational_query(query, df, "server")
                # Save to cache even on fallback
                if CACHE_AVAILABLE:
                    save_to_cache(query, df_profile, fallback_result)
                return fallback_result
            except Exception as fallback_error:
                return {
                    "error": str(fallback_error),
                    "text": "Query processing failed. Please try again.",
                    "mode": "error"
                }
    
    def _run_summary_query(self, df: pd.DataFrame, mode: str) -> Dict[str, Any]:
        """Run summary query."""
        if self.summary_router:
            return self.summary_router.get_summary(df, user_mode=mode)
        else:
            # Fallback
            return {"summary": "Summary not available", "mode": mode}
    
    def _run_rpf_query(self, df: pd.DataFrame, mode: str) -> Dict[str, Any]:
        """Run RPF query."""
        if ROUTER_AVAILABLE:
            weights = st.session_state.get("rpf_weights")
            result = run_hybrid_rpf(df, weights, mode=mode)
            return {"rpf_results": result, "mode": mode}
        else:
            return {"error": "RPF not available", "mode": mode}
    
    def _run_conversational_query(
        self,
        query: str,
        df: pd.DataFrame,
        mode: str
    ) -> Dict[str, Any]:
        """Run conversational query."""
        df_profile = self.profile or {}
        
        if ROUTER_AVAILABLE:
            try:
                result = run_hybrid_query(query, df, mode=mode)
                result["mode"] = mode
                
                # Save to cache (Part 1.5)
                if CACHE_AVAILABLE:
                    save_to_cache(query, df_profile, result)
                
                return result
            except Exception:
                # Fallback to server
                from src.ai.conversational_engine import process_conversational_query
                result = process_conversational_query(query, df)
                result["mode"] = "server"
                
                # Save to cache (Part 1.5)
                if CACHE_AVAILABLE:
                    save_to_cache(query, df_profile, result)
                
                return result
        else:
            # Use existing conversational engine
            from src.ai.conversational_engine import process_conversational_query
            result = process_conversational_query(query, df)
            result["mode"] = mode
            
            # Save to cache (Part 1.5)
            if CACHE_AVAILABLE:
                save_to_cache(query, df_profile, result)
            
            return result
    
    def get_mode(self) -> str:
        """Get current processing mode."""
        return st.session_state.get("processing_mode", self.mode or "server")
    
    def is_ready(self) -> bool:
        """Check if engine is ready."""
        return self._initialized


def get_hybrid_engine() -> HybridMasterEngine:
    """
    Get or create Hybrid Master Engine instance.
    
    Returns:
        HybridMasterEngine instance (singleton in session state)
    """
    if "hybrid_master_engine" not in st.session_state:
        st.session_state["hybrid_master_engine"] = HybridMasterEngine()
    
    return st.session_state["hybrid_master_engine"]

