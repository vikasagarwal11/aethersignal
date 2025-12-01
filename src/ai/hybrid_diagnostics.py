"""
Hybrid Engine Diagnostics (CHUNK H1.10)
Collects non-PII telemetry from across the Hybrid Engine for performance monitoring and debugging.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback

from src.telemetry.telemetry_events import safe_log, time_event, log_error


class HybridDiagnostics:
    """
    Central diagnostics collector for Hybrid Engine.
    
    Collects:
    - Mode decisions
    - Performance timings
    - Routing decisions
    - Worker status
    - Errors
    - Memory estimates
    - Token usage (if applicable)
    """
    
    def __init__(self):
        """Initialize diagnostics collector."""
        self._reset()
    
    def _reset(self):
        """Reset all diagnostic data."""
        self.mode_decisions: List[Dict[str, Any]] = []
        self.routing: List[Dict[str, Any]] = []
        self.worker_status: List[Dict[str, Any]] = []
        self.memory: List[Dict[str, Any]] = []
        self.tokens: List[Dict[str, Any]] = []
    
    def log_mode_decision(
        self,
        mode: str,
        reason: str,
        meta: Optional[Dict[str, Any]] = None
    ):
        """
        Log a mode selection decision.
        
        Args:
            mode: Selected mode ("exact", "hybrid", "approx")
            reason: Reason for mode selection
            meta: Additional metadata (will be sanitized)
        """
        decision = {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": mode,
            "reason": reason,
            "meta": meta or {}
        }
        
        self.mode_decisions.append(decision)
        log_payload = {"mode": mode, "reason": reason}
        if meta:
            log_payload.update(meta)
        safe_log("mode_selected", log_payload)
        
        # Keep only last 100 decisions
        if len(self.mode_decisions) > 100:
            self.mode_decisions.pop(0)
    
    def log_routing(
        self,
        module: str,
        routed_to: str,
        meta: Optional[Dict[str, Any]] = None
    ):
        """
        Log a routing decision.
        
        Args:
            module: Source module (e.g., "query_pipeline", "trend_alerts")
            routed_to: Destination (e.g., "local", "server", "hybrid")
            meta: Additional metadata
        """
        routing_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module,
            "routed_to": routed_to,
            "meta": meta or {}
        }
        
        self.routing.append(routing_entry)
        log_payload = {"module": module, "routed_to": routed_to}
        if meta:
            log_payload.update(meta)
        safe_log("routing_decision", log_payload)
        
        # Keep only last 200 routing decisions
        if len(self.routing) > 200:
            self.routing.pop(0)
    
    def log_worker_status(
        self,
        status: str,
        meta: Optional[Dict[str, Any]] = None
    ):
        """
        Log Pyodide worker status.
        
        Args:
            status: Worker status (e.g., "initialized", "processing", "complete", "error")
            meta: Additional metadata
        """
        status_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "meta": meta or {}
        }
        
        self.worker_status.append(status_entry)
        log_payload = {"status": status}
        if meta:
            log_payload.update(meta)
        safe_log("worker_status", log_payload)
        
        # Keep only last 100 status updates
        if len(self.worker_status) > 100:
            self.worker_status.pop(0)
    
    def log_memory_estimate(
        self,
        where: str,
        mb: float,
        context: Optional[str] = None
    ):
        """
        Log memory usage estimate.
        
        Args:
            where: Location (e.g., "browser", "pyodide", "server")
            mb: Estimated memory in MB
            context: Optional context
        """
        memory_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "location": where,
            "mb": round(mb, 2),
            "context": context
        }
        
        self.memory.append(memory_entry)
        safe_log("memory_estimate", {
            "location": where,
            "mb": round(mb, 2),
            "context": context
        })
        
        # Keep only last 100 memory estimates
        if len(self.memory) > 100:
            self.memory.pop(0)
    
    def log_token_usage(
        self,
        module: str,
        tokens: int,
        model: Optional[str] = None
    ):
        """
        Log LLM token usage.
        
        Args:
            module: Module using tokens (e.g., "trend_alerts_llm", "governance_summary")
            tokens: Number of tokens used
            model: Model name (optional)
        """
        token_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module,
            "tokens": tokens,
            "model": model
        }
        
        self.tokens.append(token_entry)
        safe_log("token_usage", {
            "module": module,
            "tokens": tokens,
            "model": model
        })
        
        # Keep only last 200 token usage entries
        if len(self.tokens) > 200:
            self.tokens.pop(0)
    
    def log_error(
        self,
        module: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log an error.
        
        Args:
            module: Module where error occurred
            error: Exception object
            context: Optional context
        """
        log_error(module, error, context)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get diagnostics summary.
        
        Returns:
            Dictionary with counts and statistics
        """
        return {
            "mode_decisions": len(self.mode_decisions),
            "routing_decisions": len(self.routing),
            "worker_status_updates": len(self.worker_status),
            "memory_estimates": len(self.memory),
            "token_usage_entries": len(self.tokens),
            "recent_mode": self.mode_decisions[-1] if self.mode_decisions else None,
            "recent_routing": self.routing[-5:] if self.routing else [],
            "recent_worker_status": self.worker_status[-5:] if self.worker_status else []
        }
    
    def get_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all diagnostic data.
        
        Returns:
            Dictionary with all diagnostic lists
        """
        return {
            "mode_decisions": self.mode_decisions.copy(),
            "routing": self.routing.copy(),
            "worker_status": self.worker_status.copy(),
            "memory": self.memory.copy(),
            "tokens": self.tokens.copy()
        }


# Global singleton instance
_diagnostics_instance: Optional[HybridDiagnostics] = None


def get_diagnostics() -> HybridDiagnostics:
    """
    Get or create the global diagnostics instance.
    
    Returns:
        HybridDiagnostics singleton
    """
    global _diagnostics_instance
    
    if _diagnostics_instance is None:
        _diagnostics_instance = HybridDiagnostics()
    
    return _diagnostics_instance


# Convenience functions
def log_mode_decision(mode: str, reason: str, meta: Optional[Dict[str, Any]] = None):
    """Convenience function to log mode decision."""
    get_diagnostics().log_mode_decision(mode, reason, meta)


def log_routing(module: str, routed_to: str, meta: Optional[Dict[str, Any]] = None):
    """Convenience function to log routing decision."""
    get_diagnostics().log_routing(module, routed_to, meta)


def log_worker_status(status: str, meta: Optional[Dict[str, Any]] = None):
    """Convenience function to log worker status."""
    get_diagnostics().log_worker_status(status, meta)

