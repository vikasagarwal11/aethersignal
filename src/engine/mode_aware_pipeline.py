"""
Mode-Aware Query Pipeline (CHUNK H1.5)
Central query dispatcher that routes queries based on Hybrid Mode Manager decisions.
Automatically selects EXACT/HYBRID/APPROX computation paths for optimal performance and accuracy.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import pandas as pd

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    from src.engine.hybrid_mode_manager import HybridModeManager, get_hybrid_mode_manager, get_current_computation_mode
    MODE_MANAGER_AVAILABLE = True
except ImportError:
    MODE_MANAGER_AVAILABLE = False

try:
    from src.ai.conversational_engine import process_conversational_query
    CONVERSATIONAL_AVAILABLE = True
except ImportError:
    CONVERSATIONAL_AVAILABLE = False

try:
    from src import signal_stats
    SIGNAL_STATS_AVAILABLE = True
except ImportError:
    SIGNAL_STATS_AVAILABLE = False

try:
    from src.ai.trend_alerts import detect_trend_alerts_light, detect_trend_alerts_heavy, get_trend_alerts
    TREND_ALERTS_AVAILABLE = True
except ImportError:
    TREND_ALERTS_AVAILABLE = False

try:
    from src.ai.narrative_clustering_engine import NarrativeClusteringEngine
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False


@dataclass
class PipelineResult:
    """
    Unified response object returned by mode-aware pipeline.
    
    Contains all results from query processing, including:
    - Chat response
    - Data results
    - Trend alerts
    - Mode information
    - Feature flags
    """
    answer: str                       # Chat response text
    results: Dict[str, Any]           # Data results (filtered data, stats, etc.)
    alerts: Optional[Dict[str, Any]] = None  # Trend alerts (light or heavy)
    mode_used: str = "exact"          # EXACT / HYBRID / APPROX
    reason: str = ""                  # Reason from HybridModeManager
    features_enabled: Dict[str, bool] = None  # Feature-level permissions
    filtered_df: Optional[pd.DataFrame] = None  # Filtered DataFrame (if applicable)
    execution_time_ms: Optional[float] = None  # Execution time in milliseconds


class ModeAwarePipeline:
    """
    Central query dispatcher for Hybrid Engine.
    
    Uses Hybrid Mode Manager to decide computation path and routes queries accordingly.
    Automatically adapts to:
    - Dataset size
    - Browser capability
    - Regulatory context
    - User preferences
    """
    
    def __init__(self, hybrid_manager: Optional[HybridModeManager] = None):
        """
        Initialize Mode-Aware Pipeline.
        
        Args:
            hybrid_manager: Hybrid Mode Manager instance (optional, will create if None)
        """
        if hybrid_manager:
            self.hybrid_manager = hybrid_manager
        elif MODE_MANAGER_AVAILABLE:
            self.hybrid_manager = get_hybrid_mode_manager()
        else:
            self.hybrid_manager = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize optional components safely."""
        self.clustering = None
        if CLUSTERING_AVAILABLE:
            try:
                self.clustering = NarrativeClusteringEngine()
            except Exception:
                pass
    
    # ---------------------------------------------------------------
    # MAIN ENTRY POINT
    # ---------------------------------------------------------------
    
    def run(
        self,
        query: str,
        df: pd.DataFrame,
        use_llm: bool = False,
        related_files: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        Execute query through mode-aware pipeline.
        
        This is the main entry point for all queries. It:
        1. Gets mode decision from Hybrid Mode Manager
        2. Routes query based on mode
        3. Executes appropriate computation path
        4. Returns unified PipelineResult
        
        Args:
            query: User's natural language query
            df: Safety data DataFrame
            use_llm: Whether to use LLM for enhanced responses
            related_files: Additional files (for FAERS multi-file processing)
            
        Returns:
            PipelineResult with answer, results, alerts, and mode info
        """
        import time
        start_time = time.time()
        
        # Get mode decision
        mode = self._get_processing_mode()
        mode_characteristics = self._get_mode_characteristics(mode)
        features_enabled = mode_characteristics.get("features", {})
        reason = mode_characteristics.get("reason", f"Mode: {mode}")
        
        # PHASE 1: Chat Response (always first, mode-aware)
        answer = self._generate_chat_response(query, df, mode, use_llm)
        
        # PHASE 2: Data Results (mode-dependent)
        results = {}
        filtered_df = None
        
        if mode == "exact":
            results, filtered_df = self._execute_exact_mode(query, df, features_enabled)
        elif mode == "hybrid":
            results, filtered_df = self._execute_hybrid_mode(query, df, features_enabled, use_llm)
        elif mode == "approx":
            results, filtered_df = self._execute_approx_mode(query, df, features_enabled)
        else:
            # Fallback to exact
            results, filtered_df = self._execute_exact_mode(query, df, features_enabled)
        
        # PHASE 3: Trend Alerts (mode-dependent)
        alerts = self._get_trend_alerts(df, mode, related_files)
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        return PipelineResult(
            answer=answer,
            results=results,
            alerts=alerts,
            mode_used=mode,
            reason=reason,
            features_enabled=features_enabled,
            filtered_df=filtered_df,
            execution_time_ms=execution_time_ms
        )
    
    # ---------------------------------------------------------------
    # MODE DECISION
    # ---------------------------------------------------------------
    
    def _get_processing_mode(self) -> str:
        """Get current processing mode from Hybrid Mode Manager."""
        if self.hybrid_manager:
            return self.hybrid_manager.get_processing_mode()
        elif MODE_MANAGER_AVAILABLE:
            return get_current_computation_mode()
        else:
            return "exact"  # Safe fallback
    
    def _get_mode_characteristics(self, mode: str) -> Dict[str, Any]:
        """Get mode characteristics and enabled features."""
        if self.hybrid_manager:
            return self.hybrid_manager.get_mode_characteristics()
        
        # Fallback characteristics
        features = {
            "local_filters": mode in ["hybrid", "approx"],
            "local_trends": mode in ["hybrid", "approx"],
            "local_clustering": mode == "hybrid",
            "local_previews": mode in ["hybrid", "approx"],
            "server_analysis": mode in ["exact", "hybrid"],
            "full_rpf": mode in ["exact", "hybrid"],
            "full_benefit_risk": mode in ["exact", "hybrid"],
            "full_governance": mode in ["exact", "hybrid"],
            "approximations_ok": mode in ["hybrid", "approx"]
        }
        
        return {
            "mode": mode,
            "features": features,
            "reason": f"Mode: {mode} (fallback)"
        }
    
    # ---------------------------------------------------------------
    # CHAT RESPONSE GENERATION (Mode-Aware)
    # ---------------------------------------------------------------
    
    def _generate_chat_response(
        self,
        query: str,
        df: pd.DataFrame,
        mode: str,
        use_llm: bool
    ) -> str:
        """
        Generate chat response based on mode.
        
        - EXACT: Full conversational engine with LLM
        - HYBRID: Full conversational engine with optional LLM
        - APPROX: Fast preview response (limited LLM usage)
        """
        if not CONVERSATIONAL_AVAILABLE:
            return f"Query received. Processing in {mode.upper()} mode."
        
        try:
            # For approximate mode, use lighter processing
            if mode == "approx":
                # Quick preview response
                return self._generate_preview_response(query, df)
            else:
                # Full conversational processing
                if use_llm or mode == "exact":
                    # Full LLM-powered response
                    result = process_conversational_query(query, df, use_llm=True)
                    if isinstance(result, dict):
                        return result.get("response", result.get("answer", "Query processed."))
                    return str(result) if result else "Query processed."
                else:
                    # Rule-based response
                    result = process_conversational_query(query, df, use_llm=False)
                    if isinstance(result, dict):
                        return result.get("response", result.get("answer", "Query processed."))
                    return str(result) if result else "Query processed."
        except Exception as e:
            return f"Query processed in {mode.upper()} mode. (Error: {str(e)})"
    
    def _generate_preview_response(self, query: str, df: pd.DataFrame) -> str:
        """Generate fast preview response for APPROX mode."""
        if df is None or df.empty:
            return "No data available for preview."
        
        # Quick stats
        row_count = len(df)
        
        # Quick drug/reaction counts
        drug_col = next((col for col in ["drug_normalized", "drug_name", "drug"] if col in df.columns), None)
        reaction_col = next((col for col in ["reaction_normalized", "reaction_pt", "reaction"] if col in df.columns), None)
        
        drug_count = df[drug_col].nunique() if drug_col else 0
        reaction_count = df[reaction_col].nunique() if reaction_col else 0
        
        return f"Preview: {row_count:,} cases, {drug_count} drugs, {reaction_count} reactions. Full analysis available in EXACT mode."
    
    # ---------------------------------------------------------------
    # MODE-SPECIFIC EXECUTION
    # ---------------------------------------------------------------
    
    def _execute_exact_mode(
        self,
        query: str,
        df: pd.DataFrame,
        features: Dict[str, bool]
    ) -> tuple[Dict[str, Any], Optional[pd.DataFrame]]:
        """
        Execute query in EXACT mode.
        
        - Full server-side processing
        - Complete filtering and analysis
        - Full RPF, governance, etc.
        """
        results = {}
        filtered_df = df.copy()
        
        if not SIGNAL_STATS_AVAILABLE:
            return results, filtered_df
        
        try:
            # Full filtering
            if CONVERSATIONAL_AVAILABLE:
                # Use conversational engine for query parsing and filtering
                result = process_conversational_query(query, df, use_llm=False)
                if isinstance(result, dict):
                    filtered_df = result.get("filtered_df", df)
                    results = {
                        "filters": result.get("filters", {}),
                        "summary": result.get("summary", {}),
                        "prr_ror": result.get("prr_ror"),
                        "trends": result.get("trends", {})
                    }
            else:
                # Basic filtering
                results = {"row_count": len(df), "mode": "exact"}
        except Exception:
            results = {"error": "Processing failed", "mode": "exact"}
        
        return results, filtered_df
    
    def _execute_hybrid_mode(
        self,
        query: str,
        df: pd.DataFrame,
        features: Dict[str, bool],
        use_llm: bool
    ) -> tuple[Dict[str, Any], Optional[pd.DataFrame]]:
        """
        Execute query in HYBRID mode.
        
        - Local filtering and trends
        - Optional local clustering
        - Server-side heavy analysis (RPF, governance)
        """
        results = {}
        filtered_df = df.copy()
        
        try:
            # Local filtering (if enabled)
            if features.get("local_filters", False) and SIGNAL_STATS_AVAILABLE:
                if CONVERSATIONAL_AVAILABLE:
                    result = process_conversational_query(query, df, use_llm=False)
                    if isinstance(result, dict):
                        filtered_df = result.get("filtered_df", df)
                        results["filters"] = result.get("filters", {})
                        results["summary"] = result.get("summary", {})
            
            # Local clustering (if enabled)
            if features.get("local_clustering", False) and self.clustering:
                try:
                    # Sample for clustering (performance)
                    sample_size = min(5000, len(df))
                    sample_df = df.sample(n=sample_size, random_state=42) if len(df) > sample_size else df
                    clusters = self.clustering.cluster_narratives(sample_df, max_clusters=10)
                    results["clusters"] = {
                        "count": len(clusters) if clusters else 0,
                        "mode": "local_hybrid"
                    }
                except Exception:
                    pass
            
            # Local trends (if enabled)
            if features.get("local_trends", False):
                results["trends"] = {"mode": "hybrid", "local": True}
            
            results["mode"] = "hybrid"
        except Exception:
            results = {"error": "Hybrid processing failed", "mode": "hybrid"}
        
        return results, filtered_df
    
    def _execute_approx_mode(
        self,
        query: str,
        df: pd.DataFrame,
        features: Dict[str, bool]
    ) -> tuple[Dict[str, Any], Optional[pd.DataFrame]]:
        """
        Execute query in APPROX mode.
        
        - Fast local previews only
        - Top-N sampling
        - No heavy computations
        """
        results = {}
        filtered_df = None
        
        try:
            # Quick top-N preview
            preview_size = min(100, len(df))
            preview_df = df.head(preview_size)
            
            # Quick stats
            results["approx_preview"] = {
                "preview_rows": preview_size,
                "total_rows": len(df),
                "sampling": "top_n"
            }
            
            # Quick drug/reaction counts (if columns exist)
            drug_col = next((col for col in ["drug_normalized", "drug_name", "drug"] if col in df.columns), None)
            reaction_col = next((col for col in ["reaction_normalized", "reaction_pt", "reaction"] if col in df.columns), None)
            
            if drug_col:
                top_drugs = df[drug_col].value_counts().head(5).to_dict()
                results["top_drugs"] = top_drugs
            
            if reaction_col:
                top_reactions = df[reaction_col].value_counts().head(5).to_dict()
                results["top_reactions"] = top_reactions
            
            results["mode"] = "approx"
            filtered_df = preview_df
        except Exception:
            results = {"error": "Approx processing failed", "mode": "approx"}
        
        return results, filtered_df
    
    # ---------------------------------------------------------------
    # TREND ALERTS (Mode-Dependent)
    # ---------------------------------------------------------------
    
    def _get_trend_alerts(
        self,
        df: pd.DataFrame,
        mode: str,
        related_files: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Get trend alerts based on mode.
        
        - EXACT: Full heavy trend alerts
        - HYBRID: Light trend alerts
        - APPROX: Ultra-light preview alerts
        """
        if not TREND_ALERTS_AVAILABLE or df is None or df.empty:
            return None
        
        try:
            if mode == "exact":
                # Full heavy mode
                alerts = detect_trend_alerts_heavy(df)
                return {
                    "mode": "heavy",
                    "alerts": alerts,
                    "count": len(alerts.get("alerts", [])) if isinstance(alerts, dict) else 0
                }
            elif mode == "hybrid":
                # Light mode
                alerts = detect_trend_alerts_light(df)
                return {
                    "mode": "light",
                    "alerts": alerts,
                    "count": len(alerts) if isinstance(alerts, list) else 0
                }
            else:
                # Ultra-light preview
                alerts = self._get_ultralight_alerts(df)
                return {
                    "mode": "ultralight",
                    "alerts": alerts,
                    "count": len(alerts) if isinstance(alerts, list) else 0
                }
        except Exception:
            return None
    
    def _get_ultralight_alerts(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get ultra-light trend alerts for APPROX mode."""
        alerts = []
        
        try:
            # Quick top changes
            reaction_col = next((col for col in ["reaction_normalized", "reaction_pt", "reaction"] if col in df.columns), None)
            if reaction_col:
                top_reactions = df[reaction_col].value_counts().head(3)
                for reaction, count in top_reactions.items():
                    alerts.append({
                        "type": "top_reaction",
                        "reaction": reaction,
                        "count": int(count),
                        "mode": "ultralight"
                    })
        except Exception:
            pass
        
        return alerts


# Global singleton instance
_global_pipeline: Optional[ModeAwarePipeline] = None


def get_mode_aware_pipeline() -> ModeAwarePipeline:
    """
    Get or create the global Mode-Aware Pipeline instance.
    
    Returns:
        ModeAwarePipeline singleton
    """
    global _global_pipeline
    
    if _global_pipeline is None:
        _global_pipeline = ModeAwarePipeline()
    
    return _global_pipeline


def execute_mode_aware_query(
    query: str,
    df: pd.DataFrame,
    use_llm: bool = False,
    related_files: Optional[Dict[str, Any]] = None
) -> PipelineResult:
    """
    Convenience function to execute a query through mode-aware pipeline.
    
    Args:
        query: User's natural language query
        df: Safety data DataFrame
        use_llm: Whether to use LLM
        related_files: Additional files (optional)
        
    Returns:
        PipelineResult with all query results
    """
    pipeline = get_mode_aware_pipeline()
    return pipeline.run(query, df, use_llm=use_llm, related_files=related_files)
