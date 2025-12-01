"""
Hybrid Summary Router (CHUNK 7.4 Part 2)
Intelligent router that decides which mode to use (local/server/hybrid) based on dataset and browser capabilities.
"""
from typing import Dict, Any, Optional
import pandas as pd

from .summary_engine import HybridSummaryEngine
from .cache import HybridSummaryCache

try:
    from src.engine.dataset_profiler import DatasetProfiler
    from src.engine.browser_capability_detector import BrowserCapabilityDetector
    PROFILER_AVAILABLE = True
except ImportError:
    PROFILER_AVAILABLE = False

try:
    from src.ai.hybrid_diagnostics import log_routing, log_mode_decision
    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_AVAILABLE = False


class HybridSummaryRouter:
    """
    Intelligent router for hybrid summary generation.
    
    Automatically selects mode based on:
    - Dataset size
    - Browser capabilities
    - User preferences
    - Network availability
    """
    
    def __init__(self):
        """Initialize Hybrid Summary Router."""
        self.engine = HybridSummaryEngine()
        self.cache = HybridSummaryCache()
        
        if PROFILER_AVAILABLE:
            self.profiler = DatasetProfiler()
            self.browser_detector = BrowserCapabilityDetector()
        else:
            self.profiler = None
            self.browser_detector = None
    
    def get_summary(
        self,
        df: pd.DataFrame,
        user_mode: str = "auto"
    ) -> Dict[str, Any]:
        """
        Get summary with automatic mode selection.
        
        Args:
            df: Safety data DataFrame
            user_mode: User preference ("auto", "local", "hybrid", "server")
            
        Returns:
            Complete summary dictionary
        """
        # Generate cache key
        cache_key = self._generate_cache_key(df, user_mode)
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            if DIAGNOSTICS_AVAILABLE:
                log_routing("hybrid_summary_router", "cache", {"cache_hit": True})
            return cached
        
        # Resolve mode
        mode = self.resolve_mode(df, user_mode)
        
        if DIAGNOSTICS_AVAILABLE:
            log_mode_decision(mode, f"User mode: {user_mode}, Dataset: {len(df)} rows")
            log_routing("hybrid_summary_router", mode, {"rows": len(df)})
        
        # Generate summary
        try:
            summary = self.engine.generate_summary(df, mode=mode)
            
            # Add metadata
            if "metadata" not in summary:
                summary["metadata"] = {}
            
            summary["metadata"]["engine"] = mode
            summary["metadata"]["cache_key"] = cache_key
            
            # Cache result
            self.cache.set(cache_key, summary)
            
            return summary
            
        except Exception as e:
            # Fallback to server mode on error
            if DIAGNOSTICS_AVAILABLE:
                log_routing("hybrid_summary_router", "server_fallback", {"error": str(e)})
            
            return self.engine.generate_summary(df, mode="server")
    
    def resolve_mode(
        self,
        df: pd.DataFrame,
        user_mode: str
    ) -> str:
        """
        Resolve processing mode based on user preference and system capabilities.
        
        Args:
            df: Safety data DataFrame
            user_mode: User preference ("auto", "local", "hybrid", "server")
            
        Returns:
            Selected mode: "local", "hybrid", or "server"
        """
        # User override - always respect explicit choice
        if user_mode in ["local", "hybrid", "server"]:
            return user_mode
        
        # Auto mode - intelligent selection
        if not PROFILER_AVAILABLE:
            return "hybrid"  # Safe default
        
        try:
            # Profile dataset
            profile = self.profiler.analyze(df)
            
            # Get browser capabilities
            browser = self.browser_detector.run_detection()
            
            if browser is None:
                return "server"  # Fallback if browser detection fails
            
            # Decision logic
            file_size_mb = profile.get("file_size_mb", 0) or 0
            row_count = profile.get("row_count", 0) or len(df)
            
            # Check browser capabilities
            is_mobile = browser.is_mobile if hasattr(browser, "is_mobile") else False
            device_class = browser.device_class if hasattr(browser, "device_class") else "medium"
            
            # Mobile devices → always server
            if is_mobile:
                return "server"
            
            # Large datasets → server
            if file_size_mb > 200 or row_count > 3_000_000:
                return "server"
            
            # Small datasets → local
            if file_size_mb < 50 and row_count < 500_000:
                return "local"
            
            # Medium datasets + capable browser → hybrid
            if device_class == "high" and file_size_mb < 150 and row_count < 2_000_000:
                return "hybrid"
            
            # Default to hybrid for medium cases
            return "hybrid"
            
        except Exception:
            return "hybrid"  # Safe default
    
    def _generate_cache_key(self, df: pd.DataFrame, user_mode: str) -> str:
        """Generate cache key from DataFrame and mode."""
        try:
            row_count = len(df)
            col_count = len(df.columns)
            
            # Use first few rows as hash seed (lightweight)
            sample_hash = hash(str(df.head(5).values.tobytes())) if not df.empty else 0
            
            return f"{user_mode}-{row_count}-{col_count}-{sample_hash}"
        except Exception:
            return f"{user_mode}-{len(df)}"


# Global singleton
_global_router: Optional[HybridSummaryRouter] = None


def get_hybrid_summary_router() -> HybridSummaryRouter:
    """Get or create global Hybrid Summary Router instance."""
    global _global_router
    
    if _global_router is None:
        _global_router = HybridSummaryRouter()
    
    return _global_router

