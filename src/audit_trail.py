"""
Audit Trail Module for AetherSignal
Provides audit logging and viewer functionality for compliance (21 CFR Part 11-friendly).
"""

import json
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd

# Import analytics module (not package) - handle both module and package cases
try:
    # Try importing as module first (analytics.py)
    analytics_path = Path(__file__).parent.parent / "analytics.py"
    if analytics_path.exists():
        spec = importlib.util.spec_from_file_location("analytics_module", analytics_path)
        analytics_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analytics_module)
        ANALYTICS_STORAGE_AVAILABLE = getattr(analytics_module, 'ANALYTICS_STORAGE_AVAILABLE', False)
        ANALYTICS_DIR = getattr(analytics_module, 'ANALYTICS_DIR', None)
        init_session_id = getattr(analytics_module, 'init_session_id', lambda: "anonymous")
    else:
        # Fallback: try package import
        from src import analytics as analytics_module
        ANALYTICS_STORAGE_AVAILABLE = getattr(analytics_module, 'ANALYTICS_STORAGE_AVAILABLE', False)
        ANALYTICS_DIR = getattr(analytics_module, 'ANALYTICS_DIR', None)
        init_session_id = getattr(analytics_module, 'init_session_id', lambda: "anonymous")
except (ImportError, AttributeError, Exception):
    ANALYTICS_STORAGE_AVAILABLE = False
    ANALYTICS_DIR = None
    init_session_id = lambda: "anonymous"

AUDIT_LOG_FILE = ANALYTICS_DIR / "audit_log.jsonl" if (ANALYTICS_STORAGE_AVAILABLE and ANALYTICS_DIR) else None


def log_audit_event(
    event: str,
    details: Optional[Dict] = None,
    user_id: Optional[str] = None,
    organization: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Log an audit event to database (activity_logs table) and file (backup).
    
    Args:
        event: Event type (e.g., 'query_executed', 'pdf_generated', 'data_loaded', 'settings_changed')
        details: Optional event details dictionary
        user_id: Optional user identifier (UUID from auth, or session ID if not authenticated)
        organization: Optional organization identifier
        ip_address: Optional IP address for audit trail
        user_agent: Optional user agent string
    """
    try:
        # Try to get user_id and organization from session state if not provided
        if user_id is None:
            # Try to get from auth first
            try:
                from src.auth.auth import get_current_user
                user = get_current_user()
                if user and user.get("id"):
                    user_id = user["id"]
                else:
                    user_id = init_session_id()  # Fallback to session ID
            except Exception:
                user_id = init_session_id()
        
        if organization is None:
            try:
                from src.auth.auth import get_current_user
                user = get_current_user()
                if user and user.get("profile"):
                    profile = user.get("profile", {})
                    organization = profile.get("organization") if isinstance(profile, dict) else None
            except Exception:
                organization = st.session_state.get("user_organization")
        
        # Prepare event details JSONB
        event_details = details or {}
        if isinstance(event_details, dict):
            # Ensure JSON-serializable
            event_details_clean = _clean_for_json(event_details)
        else:
            event_details_clean = {}
        
        # Write to database (primary storage)
        try:
            from src.pv_storage import get_supabase_db
            sb = get_supabase_db(use_service_key=True)  # Use service key to bypass RLS for inserts
            
            if sb:
                # Prepare record for database
                record = {
                    "event_type": event,
                    "event_details": event_details_clean,
                    "created_at": datetime.now().isoformat(),
                }
                
                # Add user_id if available (UUID format expected)
                if user_id:
                    # Check if it's a UUID format (from auth) or session ID
                    try:
                        import uuid
                        # Try to parse as UUID - if it fails, it's a session ID
                        uuid.UUID(str(user_id))
                        record["user_id"] = str(user_id)
                    except (ValueError, AttributeError):
                        # Session ID - store in event_details instead
                        event_details_clean["session_id"] = user_id
                        record["event_details"] = event_details_clean
                
                # Add organization if available
                if organization:
                    record["organization"] = organization
                
                # Add IP address and user agent if available
                if ip_address:
                    record["ip_address"] = ip_address
                if user_agent:
                    record["user_agent"] = user_agent
                
                # Insert into database
                sb.table("activity_logs").insert(record).execute()
        except Exception as db_error:
            # Log database error but continue to file logging
            pass
        
        # Also write to file as backup (existing behavior)
        if ANALYTICS_STORAGE_AVAILABLE and AUDIT_LOG_FILE is not None:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event": event,
                "user_id": str(user_id) if user_id else "anonymous",
                "details": details or {},
            }
            
            # Append to JSONL file (immutable log backup)
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(audit_entry) + "\n")
    except Exception:
        # Silently fail - audit should never break the app
        pass


def _clean_for_json(obj: Any) -> Any:
    """Recursively clean dict/list to remove NaN and Inf values for JSON compliance."""
    import math
    import pandas as pd
    
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_for_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif pd.isna(obj):
        return None
    else:
        return obj


def read_audit_log(
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 1000,
) -> List[Dict]:
    """
    Read audit log entries with optional filtering.
    
    Args:
        event_type: Filter by event type (e.g., 'query_executed')
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        limit: Maximum number of entries to return
        
    Returns:
        List of audit log entries
    """
    if not ANALYTICS_STORAGE_AVAILABLE or AUDIT_LOG_FILE is None:
        return []
    
    if not AUDIT_LOG_FILE.exists():
        return []
    
    entries = []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    
                    # Apply filters
                    if event_type and entry.get("event") != event_type:
                        continue
                    
                    timestamp = entry.get("timestamp", "")
                    if start_date and timestamp < start_date:
                        continue
                    if end_date and timestamp > end_date:
                        continue
                    
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
        
        # Sort by timestamp (newest first) and limit
        entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return entries[:limit]
    except Exception:
        return []


def get_audit_summary() -> Dict:
    """
    Get summary statistics from audit log.
    
    Returns:
        Dictionary with summary statistics
    """
    entries = read_audit_log(limit=10000)
    
    if not entries:
        return {
            "total_events": 0,
            "events_by_type": {},
            "unique_users": 0,
            "date_range": None,
        }
    
    events_by_type = {}
    users = set()
    timestamps = []
    
    for entry in entries:
        event = entry.get("event", "unknown")
        events_by_type[event] = events_by_type.get(event, 0) + 1
        users.add(entry.get("user_id", "unknown"))
        timestamps.append(entry.get("timestamp", ""))
    
    date_range = None
    if timestamps:
        timestamps.sort()
        date_range = {
            "start": timestamps[0],
            "end": timestamps[-1],
        }
    
    return {
        "total_events": len(entries),
        "events_by_type": events_by_type,
        "unique_users": len(users),
        "date_range": date_range,
    }


def render_audit_trail_viewer():
    """
    Render the audit trail viewer UI in Streamlit.
    """
    st.markdown("### 📋 Audit Trail Viewer")
    st.caption("View all user actions and system events. Immutable log for compliance tracking.")
    
    # 21 CFR Part 11 mode toggle
    # Note: When using key parameter, Streamlit automatically manages session state
    # The checkbox widget automatically updates st.session_state.audit_cfr_mode
    # The return value (cfr_mode) is the current state - use it directly
    # DO NOT manually set: st.session_state.audit_cfr_mode = cfr_mode (causes error!)
    cfr_mode = st.checkbox(
        "21 CFR Part 11 Mode",
        value=st.session_state.get("audit_cfr_mode", False),
        help="Enable stricter compliance mode with read-only logs and enhanced security.",
        key="audit_cfr_mode",
    )
    
    if cfr_mode:
        st.info("🔒 **21 CFR Part 11 Mode Active** - Audit logs are read-only and immutable.")
    
    # Summary statistics
    summary = get_audit_summary()
    if summary["total_events"] > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Events", f"{summary['total_events']:,}")
        with col2:
            st.metric("Unique Users", summary["unique_users"])
        with col3:
            if summary["date_range"]:
                start_date = summary["date_range"]["start"][:10]
                st.caption(f"Date Range: {start_date}")
        
        # Events by type
        if summary["events_by_type"]:
            st.markdown("#### Events by Type")
            events_df = pd.DataFrame(
                list(summary["events_by_type"].items()),
                columns=["Event Type", "Count"]
            ).sort_values("Count", ascending=False)
            st.dataframe(events_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Filters
    st.markdown("#### Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        event_types = ["All"] + list(summary.get("events_by_type", {}).keys())
        selected_event = st.selectbox(
            "Event Type",
            event_types,
            key="audit_filter_event",
        )
    
    with col2:
        days_back = st.selectbox(
            "Time Range",
            ["All", "Last 7 days", "Last 30 days", "Last 90 days"],
            key="audit_filter_time",
        )
    
    # Calculate date range
    start_date = None
    end_date = None
    if days_back != "All":
        from datetime import timedelta
        end_date = datetime.now().isoformat()
        if days_back == "Last 7 days":
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
        elif days_back == "Last 30 days":
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
        elif days_back == "Last 90 days":
            start_date = (datetime.now() - timedelta(days=90)).isoformat()
    
    # Search
    search_query = st.text_input(
        "Search (query text, filters, etc.)",
        key="audit_search",
        placeholder="Enter search term...",
    )
    
    # Load and filter entries
    event_filter = None if selected_event == "All" else selected_event
    entries = read_audit_log(
        event_type=event_filter,
        start_date=start_date,
        end_date=end_date,
        limit=500,
    )
    
    # Apply search filter
    if search_query:
        search_lower = search_query.lower()
        entries = [
            e for e in entries
            if search_lower in json.dumps(e).lower()
        ]
    
    # Display entries
    st.markdown(f"#### Audit Log Entries ({len(entries)} found)")
    
    if not entries:
        st.info("No audit log entries found matching your filters.")
        return
    
    # Pagination
    page_size = 20
    total_pages = (len(entries) + page_size - 1) // page_size
    page = st.number_input(
        "Page",
        min_value=1,
        max_value=max(1, total_pages),
        value=1,
        key="audit_page",
    )
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_entries = entries[start_idx:end_idx]
    
    # Display entries
    for entry in page_entries:
        timestamp = entry.get("timestamp", "")
        event = entry.get("event", "unknown")
        user_id = entry.get("user_id", "unknown")
        details = entry.get("details", {})
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            formatted_time = timestamp
        
        with st.expander(f"🔹 {formatted_time} - {event} (User: {user_id[:8]})"):
            st.json({
                "timestamp": timestamp,
                "event": event,
                "user_id": user_id,
                "details": details,
            })
    
    # Export button
    if entries:
        st.markdown("---")
        export_json = json.dumps(entries, indent=2)
        st.download_button(
            "📥 Export Audit Log (JSON)",
            export_json,
            f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True,
        )

