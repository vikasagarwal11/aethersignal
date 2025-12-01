"""
Signal Governance Dashboard for AetherSignal (CHUNK 6.20)
Manage detected signals, timelines, ownership, status, and audit readiness.
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import uuid


def render_signal_governance_dashboard():
    """
    Render Signal Governance Dashboard (CHUNK 6.20).
    
    Provides complete signal lifecycle management:
    - View all detected signals
    - Track their status
    - Assign owners
    - Track timelines
    - Attach evidence
    - View AI-proposed next steps
    - Maintain audit trails
    - Generate inspection-ready summaries
    """
    
    st.title("🛡️ Signal Governance Dashboard")
    st.caption("Manage detected signals, timelines, ownership, status, and audit readiness")
    
    # --------------------------------------
    # Initialize state
    # --------------------------------------
    if "governance_signals" not in st.session_state:
        st.session_state.governance_signals = []
    
    if "selected_signal_id" not in st.session_state:
        st.session_state.selected_signal_id = None
    
    # Auto-populate from trend alerts if available
    _auto_populate_from_trend_alerts()
    
    # --------------------------------------
    # Summary Metrics
    # --------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    
    signals_df = pd.DataFrame(st.session_state.governance_signals) if st.session_state.governance_signals else pd.DataFrame()
    
    if not signals_df.empty:
        new_count = len(signals_df[signals_df["status"] == "New"])
        review_count = len(signals_df[signals_df["status"].isin(["In Review", "Under Assessment"])])
        critical_count = len(signals_df[signals_df["priority"] == "Critical"])
        overdue_count = len([s for s in st.session_state.governance_signals if _is_overdue(s)])
        
        with col1:
            st.metric("📋 Total Signals", len(signals_df))
        with col2:
            st.metric("🆕 New Signals", new_count, delta=None if new_count == 0 else f"+{new_count}")
        with col3:
            st.metric("⚠️ Critical Priority", critical_count)
        with col4:
            st.metric("⏰ Overdue", overdue_count, delta=None if overdue_count == 0 else "Action Required", delta_color="inverse")
    else:
        with col1:
            st.metric("📋 Total Signals", 0)
        with col2:
            st.metric("🆕 New Signals", 0)
        with col3:
            st.metric("⚠️ Critical Priority", 0)
        with col4:
            st.metric("⏰ Overdue", 0)
    
    st.markdown("---")
    
    # --------------------------------------
    # Main Tabs: Signals Management, Pre-Inspection Heatmap
    # --------------------------------------
    main_tabs = st.tabs(["📋 Signals Management", "🛡️ Pre-Inspection Heatmap"])
    
    with main_tabs[0]:
        # --------------------------------------
        # Layout: List (left) and Details (right)
        # --------------------------------------
        col1, col2 = st.columns([1, 2])
        
        # -------------------------------
        # LEFT PANEL: SIGNAL LIST
        # -------------------------------
        with col1:
        st.subheader("📋 Active Signals")
        
        if not signals_df.empty:
            # Filter options
            filter_status = st.selectbox(
                "Filter by Status",
                options=["All"] + list(signals_df["status"].unique()),
                key="gov_filter_status"
            )
            filter_priority = st.selectbox(
                "Filter by Priority",
                options=["All"] + list(signals_df["priority"].unique()) if "priority" in signals_df.columns else ["All"],
                key="gov_filter_priority"
            )
            
            # Apply filters
            filtered_df = signals_df.copy()
            if filter_status != "All":
                filtered_df = filtered_df[filtered_df["status"] == filter_status]
            if filter_priority != "All" and "priority" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["priority"] == filter_priority]
            
            # Display signals
            if not filtered_df.empty:
                # Color-code by priority and overdue status
                display_data = filtered_df[["id", "drug", "event", "status", "priority", "owner", "detected_on"]].copy()
                display_data["display"] = display_data.apply(
                    lambda row: _format_signal_display(row, st.session_state.governance_signals),
                    axis=1
                )
                
                # Selectbox for signal selection
                selected = st.selectbox(
                    "Select a signal",
                    options=filtered_df["id"].tolist(),
                    format_func=lambda sid: _get_signal_display_name(sid, filtered_df),
                    key="gov_signal_selector"
                )
                
                st.session_state.selected_signal_id = selected
                
                # Quick actions
                st.markdown("**Quick Actions:**")
                if st.button("🔄 Refresh from Trend Alerts", use_container_width=True, key="gov_refresh"):
                    _auto_populate_from_trend_alerts()
                    st.rerun()
                
                if st.button("📊 Export Signal List", use_container_width=True, key="gov_export"):
                    _export_signal_list(filtered_df)
            else:
                st.info("No signals match the selected filters.")
                st.session_state.selected_signal_id = None
        else:
            st.info("No signals in governance dashboard yet.")
            st.markdown("**Options:**")
            if st.button("🔄 Import from Trend Alerts", use_container_width=True, key="gov_import"):
                _auto_populate_from_trend_alerts()
                st.rerun()
            if st.button("➕ Add New Signal Manually", use_container_width=True, key="gov_add_manual"):
                st.session_state.governance_signals.append({
                    "id": str(uuid.uuid4()),
                    "drug": "Unknown",
                    "event": "Unknown",
                    "detected_on": datetime.utcnow().isoformat(),
                    "status": "New",
                    "priority": "Medium",
                    "owner": None,
                    "due_date": None,
                    "history": [],
                    "evidence": [],
                    "ai_summary": "",
                    "rpf_score": None,
                    "risk_level": None,
                })
                st.rerun()
        
        st.markdown("---")
        
        # Overdue alerts
        overdue_signals = [s for s in st.session_state.governance_signals if _is_overdue(s)]
        if overdue_signals:
            st.warning(f"⚠️ **{len(overdue_signals)} overdue signal(s)** require attention!")
            for sig in overdue_signals[:3]:
                st.write(f"• {sig.get('drug', 'Unknown')} → {sig.get('event', 'Unknown')}")
    
    # -------------------------------
    # RIGHT PANEL: SIGNAL DETAILS
    # -------------------------------
    with col2:
        if st.session_state.selected_signal_id:
            signal = next((s for s in st.session_state.governance_signals if s["id"] == st.session_state.selected_signal_id), None)
            
            if signal:
                # Signal name with badges (CHUNK A5)
                signal_name = f"{signal.get('drug', 'Unknown')} → {signal.get('event', 'Unknown')}"
                st.subheader(f"🔍 Signal Details: {signal_name}")
                
                # Render badges inline (CHUNK A5)
                try:
                    from src.ui.badge_renderer import render_badge_row
                    
                    lifecycle = signal.get("lifecycle", signal.get("status", "Unknown"))
                    priority = signal.get("priority", "Medium")
                    
                    render_badge_row([lifecycle, priority], ["lifecycle", "severity"])
                except ImportError:
                    pass
                
                # Tabs for different views
                tab1, tab2, tab3, tab4 = st.tabs(["📝 Details", "📎 Evidence", "🕒 Timeline", "🤖 AI Recommendations"])
                
                # Tab 1: Details
                with tab1:
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        signal["drug"] = st.text_input("Drug", signal.get("drug", ""), key=f"drug_{signal['id']}")
                        signal["event"] = st.text_input("Event / Adverse Event", signal.get("event", ""), key=f"event_{signal['id']}")
                        signal["status"] = st.selectbox(
                            "Status",
                            ["New", "In Review", "Under Assessment", "Escalated", "Closed", "Archived"],
                            index=["New", "In Review", "Under Assessment", "Escalated", "Closed", "Archived"].index(signal.get("status", "New")),
                            key=f"status_{signal['id']}"
                        )
                    
                    with col_b:
                        signal["priority"] = st.selectbox(
                            "Priority",
                            ["Low", "Medium", "High", "Critical"],
                            index=["Low", "Medium", "High", "Critical"].index(signal.get("priority", "Medium")),
                            key=f"priority_{signal['id']}"
                        )
                        signal["owner"] = st.text_input("Owner (PV Lead / QPPV)", signal.get("owner") or "", key=f"owner_{signal['id']}")
                        
                        # Due date
                        due_date_str = signal.get("due_date")
                        if due_date_str:
                            try:
                                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                                due_date_display = due_date.date()
                            except:
                                due_date_display = None
                        else:
                            due_date_display = None
                        
                        new_due_date = st.date_input(
                            "Due Date",
                            value=due_date_display,
                            key=f"due_date_{signal['id']}"
                        )
                        if new_due_date:
                            signal["due_date"] = new_due_date.isoformat()
                    
                    # Metadata
                    st.markdown("---")
                    st.markdown("### Metadata")
                    col_meta1, col_meta2 = st.columns(2)
                    with col_meta1:
                        detected_on = signal.get("detected_on")
                        if detected_on:
                            try:
                                if isinstance(detected_on, str):
                                    detected_date = datetime.fromisoformat(detected_on.replace('Z', '+00:00'))
                                else:
                                    detected_date = detected_on
                                st.write(f"**Detected On:** {detected_date.strftime('%Y-%m-%d %H:%M')}")
                            except:
                                st.write(f"**Detected On:** {detected_on}")
                        
                        rpf_score = signal.get("rpf_score")
                        if rpf_score:
                            st.write(f"**RPF Score:** {rpf_score:.1f}")
                        
                        risk_level = signal.get("risk_level")
                        if risk_level:
                            st.write(f"**Risk Level:** {risk_level}")
                    
                    with col_meta2:
                        days_open = _get_days_open(signal)
                        if days_open is not None:
                            st.write(f"**Days Open:** {days_open} days")
                            if days_open > 90:
                                st.warning("⚠️ Signal open for more than 90 days")
                        
                        if _is_overdue(signal):
                            st.error("🔴 **OVERDUE**")
                
                # Tab 2: Evidence & Attachments
                with tab2:
                    st.subheader("📎 Evidence & Attachments")
                    
                    uploaded = st.file_uploader(
                        "Upload evidence (PDFs, documents, reports)",
                        accept_multiple_files=True,
                        key=f"upload_{signal['id']}"
                    )
                    
                    if uploaded:
                        for f in uploaded:
                            if "evidence" not in signal:
                                signal["evidence"] = []
                            signal["evidence"].append({
                                "name": f.name,
                                "uploaded_on": datetime.utcnow().isoformat(),
                                "size": f.size
                            })
                        st.success(f"✅ {len(uploaded)} file(s) added")
                    
                    if signal.get("evidence"):
                        st.markdown("**Uploaded Evidence:**")
                        for idx, ev in enumerate(signal["evidence"]):
                            col_ev1, col_ev2 = st.columns([3, 1])
                            with col_ev1:
                                st.write(f"📄 {ev.get('name', 'Unknown')}")
                            with col_ev2:
                                if st.button("🗑️", key=f"del_ev_{signal['id']}_{idx}"):
                                    signal["evidence"].pop(idx)
                                    st.rerun()
                            
                            upload_date = ev.get("uploaded_on")
                            if upload_date:
                                try:
                                    if isinstance(upload_date, str):
                                        up_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                                    else:
                                        up_date = upload_date
                                    st.caption(f"Uploaded: {up_date.strftime('%Y-%m-%d %H:%M')}")
                                except:
                                    st.caption(f"Uploaded: {upload_date}")
                    else:
                        st.info("No evidence attached yet.")
                
                # Tab 3: History & Timeline
                with tab3:
                    st.subheader("🕒 History & Timeline")
                    
                    new_entry = st.text_area("Add timeline entry", key=f"timeline_entry_{signal['id']}")
                    if st.button("➕ Add Entry", key=f"add_timeline_{signal['id']}"):
                        if "history" not in signal:
                            signal["history"] = []
                        signal["history"].append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "user": st.session_state.get("user_email", "System"),
                            "entry": new_entry or "Status updated or note added"
                        })
                        st.rerun()
                    
                    if signal.get("history"):
                        st.markdown("**Timeline:**")
                        for h in reversed(signal["history"]):  # Most recent first
                            timestamp = h.get("timestamp")
                            try:
                                if isinstance(timestamp, str):
                                    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                else:
                                    ts = timestamp
                                timestamp_str = ts.strftime('%Y-%m-%d %H:%M')
                            except:
                                timestamp_str = str(timestamp)
                            
                            user = h.get("user", "System")
                            entry = h.get("entry", "")
                            st.markdown(f"**{timestamp_str}** ({user})")
                            st.write(entry)
                            st.markdown("---")
                    else:
                        st.info("No timeline entries yet.")
                
                # Tab 4: AI Recommendations
                with tab4:
                    st.subheader("🤖 AI Recommendations")
                    
                    ai_summary = signal.get("ai_summary", "")
                    if ai_summary:
                        st.markdown("**AI Summary:**")
                        st.markdown(ai_summary)
                    else:
                        st.info("No AI summary available. Generate from Trend Alerts to populate.")
                    
                    if st.button("🔄 Generate AI Recommendations", key=f"ai_rec_{signal['id']}"):
                        _generate_ai_recommendations(signal)
                        st.rerun()
                
                # Save button
                st.markdown("---")
                if st.button("💾 Save Changes", type="primary", use_container_width=True, key=f"save_{signal['id']}"):
                    # Add history entry for status changes
                    old_status = signal.get("previous_status")
                    if old_status and old_status != signal["status"]:
                        if "history" not in signal:
                            signal["history"] = []
                        signal["history"].append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "user": st.session_state.get("user_email", "System"),
                            "entry": f"Status changed from '{old_status}' to '{signal['status']}'"
                        })
                        signal["previous_status"] = signal["status"]
                    
                    st.success("✅ Changes saved!")
                    st.rerun()
            else:
                st.error("Signal not found.")
        else:
            st.info("👈 Select a signal from the list to view details.")
    
    # Audit trail logging
    if st.session_state.governance_signals:
        from src.audit_trail import log_audit_event
        log_audit_event(
            "governance_dashboard_viewed",
            {"signal_count": len(st.session_state.governance_signals)}
        )


def _auto_populate_from_trend_alerts():
    """Auto-populate governance signals from trend alerts (CHUNK 6.20)."""
    try:
        alerts_result = st.session_state.get("last_trend_alerts_result")
        if not alerts_result:
            return
        
        if "governance_signals" not in st.session_state:
            st.session_state.governance_signals = []
        
        existing_ids = {s["id"] for s in st.session_state.governance_signals}
        
        # Import from emerging signals
        emerging_signals = alerts_result.get("emerging_signals", [])
        for signal in emerging_signals:
            signal_id = signal.get("id") or str(uuid.uuid4())
            
            # Check if already exists
            if signal_id not in existing_ids:
                st.session_state.governance_signals.append({
                    "id": signal_id,
                    "drug": signal.get("drug", "Unknown"),
                    "event": signal.get("reaction", "Unknown"),
                    "detected_on": datetime.utcnow().isoformat(),
                    "status": "New",
                    "priority": _map_severity_to_priority(signal.get("severity", "medium")),
                    "owner": None,
                    "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),  # Default 30 days
                    "history": [{
                        "timestamp": datetime.utcnow().isoformat(),
                        "user": "System",
                        "entry": "Signal detected from Trend Alerts engine"
                    }],
                    "evidence": [],
                    "ai_summary": signal.get("summary", ""),
                    "rpf_score": signal.get("rpf_score"),
                    "risk_level": signal.get("risk_level"),
                })
                existing_ids.add(signal_id)
        
        # Import from RPF-ranked signals
        rpf_ranked = alerts_result.get("rpf_ranked", [])
        for entry in rpf_ranked:
            sig = entry.get("signal", {})
            signal_id = sig.get("id") or str(uuid.uuid4())
            
            if signal_id not in existing_ids:
                risk_level = entry.get("risk_level", "Medium")
                st.session_state.governance_signals.append({
                    "id": signal_id,
                    "drug": sig.get("drug", "Unknown"),
                    "event": sig.get("reaction", "Unknown"),
                    "detected_on": datetime.utcnow().isoformat(),
                    "status": "New",
                    "priority": _map_risk_level_to_priority(risk_level),
                    "owner": None,
                    "due_date": (datetime.utcnow() + timedelta(days=15 if risk_level in ["Critical", "High"] else 30)).isoformat(),
                    "history": [{
                        "timestamp": datetime.utcnow().isoformat(),
                        "user": "System",
                        "entry": f"High-priority signal detected (RPF Score: {entry.get('rpf_score', 0):.1f})"
                    }],
                    "evidence": [],
                    "ai_summary": f"RPF-ranked signal with {risk_level} risk level",
                    "rpf_score": entry.get("rpf_score"),
                    "risk_level": risk_level,
                })
                existing_ids.add(signal_id)
    
    except Exception:
        # Fail silently
        pass


def _map_severity_to_priority(severity: str) -> str:
    """Map alert severity to governance priority."""
    mapping = {
        "critical": "Critical",
        "high": "High",
        "warning": "Medium",
        "medium": "Medium",
        "info": "Low",
        "low": "Low"
    }
    return mapping.get(severity.lower(), "Medium")


def _map_risk_level_to_priority(risk_level: str) -> str:
    """Map RPF risk level to governance priority."""
    mapping = {
        "Critical": "Critical",
        "High": "High",
        "Medium": "Medium",
        "Low": "Low"
    }
    return mapping.get(risk_level, "Medium")


def _is_overdue(signal: Dict) -> bool:
    """Check if signal is overdue."""
    due_date_str = signal.get("due_date")
    if not due_date_str:
        return False
    
    try:
        if isinstance(due_date_str, str):
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        else:
            due_date = due_date_str
        
        return datetime.utcnow() > due_date and signal.get("status") not in ["Closed", "Archived"]
    except:
        return False


def _get_days_open(signal: Dict) -> Optional[int]:
    """Get number of days signal has been open."""
    detected_on = signal.get("detected_on")
    if not detected_on:
        return None
    
    try:
        if isinstance(detected_on, str):
            detected_date = datetime.fromisoformat(detected_on.replace('Z', '+00:00'))
        else:
            detected_date = detected_on
        
        delta = datetime.utcnow() - detected_date
        return delta.days
    except:
        return None


def _format_signal_display(row: pd.Series, signals: List[Dict]) -> str:
    """Format signal for display in list."""
    signal = next((s for s in signals if s["id"] == row["id"]), None)
    if not signal:
        return f"{row.get('drug', 'Unknown')} → {row.get('event', 'Unknown')}"
    
    overdue_marker = "⏰ " if _is_overdue(signal) else ""
    priority_marker = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(row.get("priority", "Medium"), "")
    
    return f"{overdue_marker}{priority_marker} {row.get('drug', 'Unknown')} → {row.get('event', 'Unknown')}"


def _get_signal_display_name(signal_id: str, df: pd.DataFrame) -> str:
    """Get display name for signal."""
    row = df[df["id"] == signal_id]
    if row.empty:
        return signal_id[:8]
    
    drug = row.iloc[0].get("drug", "Unknown")
    event = row.iloc[0].get("event", "Unknown")
    status = row.iloc[0].get("status", "Unknown")
    priority = row.iloc[0].get("priority", "Medium")
    
    return f"{drug} → {event} [{status}] ({priority})"


def _export_signal_list(df: pd.DataFrame):
    """Export signal list to CSV."""
    try:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"signal_governance_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error exporting: {str(e)}")


def _generate_ai_recommendations(signal: Dict):
    """Generate AI recommendations for a signal (CHUNK 6.20)."""
    try:
        from src.ai.medical_llm import call_medical_llm
        
        prompt = f"""
You are a senior pharmacovigilance expert. Provide recommendations for this signal:

Drug: {signal.get('drug', 'Unknown')}
Event: {signal.get('event', 'Unknown')}
Status: {signal.get('status', 'New')}
Priority: {signal.get('priority', 'Medium')}
RPF Score: {signal.get('rpf_score', 'N/A')}
Risk Level: {signal.get('risk_level', 'N/A')}

Provide:
1. Recommended next steps
2. Suggested review timeline
3. Key evidence to collect
4. Regulatory considerations

Format as a concise, actionable summary.
"""
        
        response = call_medical_llm(
            prompt=prompt,
            system_prompt="You are a pharmacovigilance expert providing signal management recommendations.",
            task_type="regulatory_writing",
            max_tokens=500,
            temperature=0.3
        )
        
        if response:
            signal["ai_summary"] = response
    
    except Exception:
        # Fail gracefully
        pass

