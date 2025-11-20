"""
Usage Analytics for AetherSignal
Anonymous session tracking and usage statistics (no PII stored)
"""
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    ANALYTICS_DIR = Path("analytics")
    ANALYTICS_DIR.mkdir(exist_ok=True)
    ANALYTICS_STORAGE_AVAILABLE = True
except Exception:
    ANALYTICS_DIR = None
    ANALYTICS_STORAGE_AVAILABLE = False

USAGE_LOG_FILE = ANALYTICS_DIR / "usage_log.csv" if ANALYTICS_STORAGE_AVAILABLE else None
STATS_FILE = ANALYTICS_DIR / "usage_stats.json" if ANALYTICS_STORAGE_AVAILABLE else None
MAX_USAGE_EVENTS = 5000


def init_session_id() -> str:
    """Generate or retrieve anonymous session ID"""
    import streamlit as st
    
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())[:8]
    
    return st.session_state.session_id


def log_event(event_type: str, metadata: Optional[Dict] = None) -> None:
    """
    Log anonymous usage event to CSV file
    
    Args:
        event_type: Type of event (upload, query, pdf_download, etc.)
        metadata: Optional metadata dict (no PII)
    """
    if not ANALYTICS_STORAGE_AVAILABLE or USAGE_LOG_FILE is None:
        return
    try:
        session_id = init_session_id()
        timestamp = datetime.now().isoformat()
        
        row = {
            "timestamp": timestamp,
            "session_id": session_id,
            "event_type": event_type,
            "metadata": json.dumps(metadata or {}),
        }
        
        # Append to CSV
        file_exists = USAGE_LOG_FILE.exists()
        with open(USAGE_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        _truncate_usage_log()
    except Exception:
        # Silently fail - analytics should never break the app
        pass


def get_usage_stats() -> Dict:
    """
    Get aggregated usage statistics from log file
    
    Returns:
        Dict with usage statistics
    """
    if not ANALYTICS_STORAGE_AVAILABLE or USAGE_LOG_FILE is None:
        return {
            "total_sessions": 0,
            "total_events": 0,
            "events_by_type": {},
            "recent_activity": [],
        }
    try:
        if not USAGE_LOG_FILE.exists():
            return {
                "total_sessions": 0,
                "total_events": 0,
                "events_by_type": {},
                "recent_activity": [],
            }
        
        events = []
        sessions = set()
        
        with open(USAGE_LOG_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append(row)
                sessions.add(row["session_id"])
        
        # Aggregate by event type
        events_by_type = {}
        for event in events:
            event_type = event["event_type"]
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        # Recent activity (last 100 events)
        recent = events[-100:] if len(events) > 100 else events
        
        return {
            "total_sessions": len(sessions),
            "total_events": len(events),
            "events_by_type": events_by_type,
            "recent_activity": recent[-20:],  # Last 20 events
        }
    except Exception:
        return {
            "total_sessions": 0,
            "total_events": 0,
            "events_by_type": {},
            "recent_activity": [],
        }


def _truncate_usage_log(max_events: int = MAX_USAGE_EVENTS) -> None:
    """
    Keep usage log to a manageable size by retaining only the most recent events.
    """
    if not ANALYTICS_STORAGE_AVAILABLE or USAGE_LOG_FILE is None:
        return
    try:
        if not USAGE_LOG_FILE.exists():
            return
        with open(USAGE_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= max_events + 1:  # +1 for header
            return
        header, entries = lines[0], lines[1:]
        trimmed = entries[-max_events:]
        with open(USAGE_LOG_FILE, "w", encoding="utf-8") as f:
            f.write(header)
            f.writelines(trimmed)
    except Exception:
        pass

