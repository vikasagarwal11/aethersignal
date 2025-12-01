"""
Balanced Telemetry Events (CHUNK H1.10 - Option B)
Central telemetry logger with zero PII, zero sensitive content.
Logs only events and performance metrics - never user data, queries, or case content.
"""
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# In-memory telemetry store (session-scoped)
_telemetry_events: List[Dict[str, Any]] = []
_telemetry_timings: List[Dict[str, Any]] = []
_telemetry_errors: List[Dict[str, Any]] = []


def safe_log(event_type: str, payload: Optional[Dict[str, Any]] = None):
    """
    Central telemetry logger – zero PII, zero sensitive content.
    
    Logs events like:
    - Mode selections
    - Performance metrics
    - Routing decisions
    - Error patterns
    - Worker status
    
    Never logs:
    - User queries
    - Drug names
    - Reaction names
    - Case narratives
    - Patient data
    - Any PII
    
    Args:
        event_type: Type of event (e.g., "mode_selected", "trend_alerts_complete")
        payload: Event payload dictionary (will be sanitized)
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        sanitized = sanitize_payload(payload or {})
        
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "payload": sanitized
        }
        
        # Store in session state if available
        if STREAMLIT_AVAILABLE:
            if "telemetry_events" not in st.session_state:
                st.session_state.telemetry_events = []
            st.session_state.telemetry_events.append(log_entry)
        
        # Also store in-memory for diagnostics
        _telemetry_events.append(log_entry)
        
        # Keep only last 1000 events in memory
        if len(_telemetry_events) > 1000:
            _telemetry_events.pop(0)
            
    except Exception:
        # Telemetry should NEVER break the app
        pass


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove anything that could contain PII or user-sensitive content.
    
    Args:
        payload: Raw payload dictionary
        
    Returns:
        Sanitized payload with all sensitive content removed/replaced
    """
    if not payload:
        return {}
    
    safe = {}
    sensitive_keywords = [
        "query", "text", "content", "narrative", "description",
        "drug", "reaction", "patient", "case", "report",
        "name", "identifier", "id", "email", "address"
    ]
    
    for k, v in payload.items():
        key_lower = k.lower()
        
        # Skip sensitive keys entirely
        if any(keyword in key_lower for keyword in sensitive_keywords):
            continue
        
        # Truncate long strings
        if isinstance(v, str) and len(v) > 80:
            safe[k] = f"[STRING_LEN_{len(v)}]"
        
        # Replace long lists/arrays with counts
        elif isinstance(v, (list, tuple)) and len(v) > 10:
            safe[k] = f"[ARRAY_LEN_{len(v)}]"
        
        # Safe numeric types
        elif isinstance(v, (int, float, bool)):
            safe[k] = v
        
        # Safe small strings
        elif isinstance(v, str) and len(v) <= 80:
            # Double-check it doesn't look like PII
            if "@" not in v and "://" not in v:
                safe[k] = v
            else:
                safe[k] = "[REDACTED]"
        
        # Nested dictionaries - recursively sanitize
        elif isinstance(v, dict):
            safe[k] = sanitize_payload(v)
        
        # Other types - convert to string and truncate
        else:
            safe[k] = f"[{type(v).__name__}]"
    
    return safe


@contextmanager
def time_event(event_type: str, payload: Optional[Dict[str, Any]] = None):
    """
    Context manager for timing events.
    
    Usage:
        with time_event("trend_alerts_light", {"mode": "hybrid"}):
            result = detect_trend_alerts_light(df)
    
    Args:
        event_type: Type of event being timed
        payload: Optional payload to include with timing
    """
    start = time.time()
    try:
        yield
    finally:
        duration_ms = int((time.time() - start) * 1000)
        timing_payload = (payload or {}).copy()
        timing_payload["duration_ms"] = duration_ms
        
        safe_log(f"{event_type}_timing", timing_payload)
        
        # Also store in timings list
        if STREAMLIT_AVAILABLE:
            if "telemetry_timings" not in st.session_state:
                st.session_state.telemetry_timings = []
            st.session_state.telemetry_timings.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "duration_ms": duration_ms,
                "payload": sanitize_payload(payload or {})
            })


def log_error(module: str, error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Log error events (error type, module, no sensitive data).
    
    Args:
        module: Module where error occurred
        error: Exception object
        context: Optional context dictionary (will be sanitized)
    """
    try:
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module,
            "error_type": type(error).__name__,
            "error_message": str(error)[:200],  # Truncate long messages
            "context": sanitize_payload(context or {})
        }
        
        if STREAMLIT_AVAILABLE:
            if "telemetry_errors" not in st.session_state:
                st.session_state.telemetry_errors = []
            st.session_state.telemetry_errors.append(error_entry)
        
        _telemetry_errors.append(error_entry)
        
        # Keep only last 100 errors
        if len(_telemetry_errors) > 100:
            _telemetry_errors.pop(0)
            
        # Also log as regular event
        safe_log("error_occurred", {
            "module": module,
            "error_type": type(error).__name__
        })
        
    except Exception:
        pass  # Never break on telemetry


def get_telemetry_summary() -> Dict[str, Any]:
    """
    Get summary of telemetry events.
    
    Returns:
        Dictionary with event counts, recent events, timing stats
    """
    try:
        events = _telemetry_events.copy()
        if STREAMLIT_AVAILABLE and "telemetry_events" in st.session_state:
            events = st.session_state.telemetry_events.copy()
        
        timings = []
        if STREAMLIT_AVAILABLE and "telemetry_timings" in st.session_state:
            timings = st.session_state.telemetry_timings.copy()
        
        errors = _telemetry_errors.copy()
        if STREAMLIT_AVAILABLE and "telemetry_errors" in st.session_state:
            errors = st.session_state.telemetry_errors.copy()
        
        # Count events by type
        event_counts = {}
        for event in events:
            event_type = event.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Calculate timing statistics
        timing_stats = {}
        for timing in timings:
            event_type = timing.get("event_type", "unknown")
            duration = timing.get("duration_ms", 0)
            if event_type not in timing_stats:
                timing_stats[event_type] = {"count": 0, "total_ms": 0, "avg_ms": 0, "min_ms": float('inf'), "max_ms": 0}
            stats = timing_stats[event_type]
            stats["count"] += 1
            stats["total_ms"] += duration
            stats["min_ms"] = min(stats["min_ms"], duration)
            stats["max_ms"] = max(stats["max_ms"], duration)
        
        # Calculate averages
        for event_type, stats in timing_stats.items():
            if stats["count"] > 0:
                stats["avg_ms"] = round(stats["total_ms"] / stats["count"], 2)
        
        return {
            "total_events": len(events),
            "total_timings": len(timings),
            "total_errors": len(errors),
            "event_counts": event_counts,
            "timing_stats": timing_stats,
            "recent_events": events[-10:] if events else [],
            "recent_errors": errors[-5:] if errors else []
        }
    except Exception:
        return {
            "total_events": 0,
            "total_timings": 0,
            "total_errors": 0,
            "event_counts": {},
            "timing_stats": {},
            "recent_events": [],
            "recent_errors": []
        }


def clear_telemetry():
    """Clear all telemetry data (useful for testing or privacy)."""
    global _telemetry_events, _telemetry_timings, _telemetry_errors
    
    _telemetry_events.clear()
    _telemetry_timings.clear()
    _telemetry_errors.clear()
    
    if STREAMLIT_AVAILABLE:
        if "telemetry_events" in st.session_state:
            st.session_state.telemetry_events.clear()
        if "telemetry_timings" in st.session_state:
            st.session_state.telemetry_timings.clear()
        if "telemetry_errors" in st.session_state:
            st.session_state.telemetry_errors.clear()

