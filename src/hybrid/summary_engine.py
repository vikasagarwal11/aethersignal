"""
Hybrid Summary Engine (CHUNK 7.4 Part 1)
Main orchestrator for hybrid (local + server) summary generation.
"""
from typing import Dict, Any, Optional
import pandas as pd
import time

from .local_summary_extractor import extract_local_summary
from .server_summary_extractor import extract_server_summary
from .merger import merge_summaries
from .diagnostics import build_diagnostics


class HybridSummaryEngine:
    """
    Main orchestrator for hybrid summary generation.
    
    Supports three modes:
    - local: Pyodide only (fast, offline)
    - server: AI-only (powerful, requires server)
    - hybrid: Local + Server (recommended - best of both)
    """
    
    def __init__(self):
        """Initialize Hybrid Summary Engine."""
        self.cache: Dict[str, Any] = {}
    
    def generate_summary(
        self,
        df: pd.DataFrame,
        mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Generate summary based on selected mode.
        
        Args:
            df: Safety data DataFrame
            mode: Processing mode ("local", "server", or "hybrid")
            
        Returns:
            Complete summary dictionary with local, server (if applicable), and unified views
        """
        start_time = time.time()
        
        try:
            # Step 1: Fast local summary (always done first)
            local = extract_local_summary(df)
            
            # Step 2: Server summary only if needed
            if mode == "local":
                final = merge_summaries(local, None)
            elif mode == "server":
                # Server-only mode: generate server summary without local
                server = extract_server_summary(local, df)
                final = merge_summaries(local, server)
            else:  # hybrid (default)
                # Generate both local and server, then merge
                server = extract_server_summary(local, df)
                final = merge_summaries(local, server)
            
            # Step 3: Add diagnostics
            duration_ms = (time.time() - start_time) * 1000
            diagnostics = build_diagnostics(local, final, duration_ms)
            final["diagnostics"] = diagnostics
            
            # Step 4: Store in cache
            self.cache["latest_summary"] = final
            
            return final
            
        except Exception as e:
            # Fallback to local-only on any error
            duration_ms = (time.time() - start_time) * 1000
            local = extract_local_summary(df)
            final = merge_summaries(local, None)
            diagnostics = build_diagnostics(local, final, duration_ms)
            diagnostics["error"] = str(e)
            diagnostics["fallback"] = True
            final["diagnostics"] = diagnostics
            return final

