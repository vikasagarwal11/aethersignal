"""
Safety Workflow Dashboard UI (Phase 3H.4)
Interactive dashboard for case bundles, tasks, and review workflows.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from src.workflow.case_bundles import CaseBundlesEngine
from src.workflow.task_manager import TaskManager
from src.workflow.review_workflow import ReviewWorkflow
from src.workflow.audit_trail import AuditTrail

logger = logging.getLogger(__name__)


def render_workflow_dashboard(df: Optional[pd.DataFrame] = None):
    """
    Render safety workflow dashboard.
    
    Args:
        df: Optional DataFrame with AE entries
    """
    st.header("🔄 Safety Workflow Dashboard")
    st.caption("End-to-end workflow automation: Case Bundles → Tasks → Reviews → Approval")
    
    # Initialize engines
    bundles_engine = CaseBundlesEngine()
    task_manager = TaskManager()
    review_workflow = ReviewWorkflow()
    audit_trail = AuditTrail()
    
    # Store in session state
    if "bundles_engine" not in st.session_state:
        st.session_state["bundles_engine"] = bundles_engine
    if "task_manager" not in st.session_state:
        st.session_state["task_manager"] = task_manager
    if "review_workflow" not in st.session_state:
        st.session_state["review_workflow"] = review_workflow
    if "audit_trail" not in st.session_state:
        st.session_state["audit_trail"] = audit_trail
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📦 Case Bundles",
        "✅ Task Console",
        "👥 Review Center",
        "📊 Workflow Status",
        "📋 Audit Log"
    ])
    
    with tab1:
        render_case_bundles_tab(df, bundles_engine)
    
    with tab2:
        render_task_console_tab(task_manager)
    
    with tab3:
        render_review_center_tab(bundles_engine, review_workflow)
    
    with tab4:
        render_workflow_status_tab(bundles_engine)
    
    with tab5:
        render_audit_log_tab(audit_trail)


def render_case_bundles_tab(df: Optional[pd.DataFrame], bundles_engine: CaseBundlesEngine):
    """Render case bundles tab."""
    st.subheader("📦 Case Bundles")
    
    # Auto-create bundles from signals
    if df is not None and not df.empty:
        if st.button("🔍 Auto-Create Bundles from Signals", type="primary"):
            with st.spinner("Prioritizing signals and creating bundles..."):
                from src.risk.global_risk_manager import GlobalRiskManager
                
                risk_manager = GlobalRiskManager()
                prioritized = risk_manager.prioritize_signals(df, limit=20)
                
                bundles = bundles_engine.auto_create_bundles_from_signals(
                    prioritized, df, threshold=0.55
                )
                
                st.success(f"✅ Created {len(bundles)} case bundles")
    
    # List bundles
    status_filter = st.selectbox(
        "Filter by Status",
        options=["all", "draft", "peer_review", "final_review", "approved", "rejected"],
        index=0
    )
    
    bundles = bundles_engine.list_bundles(
        status=status_filter if status_filter != "all" else None,
        limit=50
    )
    
    if bundles:
        # Create DataFrame
        bundles_df = pd.DataFrame([b.to_dict() for b in bundles])
        
        st.dataframe(
            bundles_df[["bundle_id", "drug", "reaction", "status", "evidence_count", "task_count", "gri_score"]],
            use_container_width=True,
            height=400
        )
        
        # Bundle detail view
        selected_bundle_id = st.selectbox(
            "Select Bundle for Details",
            options=[b.bundle_id for b in bundles]
        )
        
        if selected_bundle_id:
            bundle = bundles_engine.get_bundle(selected_bundle_id)
            if bundle:
                render_bundle_detail(bundle)
    else:
        st.info("👆 Create bundles first")


def render_bundle_detail(bundle):
    """Render bundle detail view."""
    st.markdown("### Bundle Details")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Drug", bundle.drug)
    with col2:
        st.metric("Reaction", bundle.reaction)
    with col3:
        st.metric("Status", bundle.status.replace("_", " ").title())
    
    # Tabs for bundle details
    detail_tab1, detail_tab2, detail_tab3, detail_tab4 = st.tabs([
        "Evidence", "Tasks", "Reviews", "Audit Log"
    ])
    
    with detail_tab1:
        st.write(f"**Evidence Count:** {len(bundle.evidence)}")
        if bundle.evidence:
            evidence_df = pd.DataFrame(bundle.evidence[:20])  # Show first 20
            st.dataframe(evidence_df, use_container_width=True)
    
    with detail_tab2:
        st.write(f"**Task Count:** {len(bundle.tasks)}")
        if bundle.tasks:
            tasks_df = pd.DataFrame(bundle.tasks)
            st.dataframe(tasks_df, use_container_width=True)
    
    with detail_tab3:
        st.write(f"**Review Count:** {len(bundle.reviews)}")
        if bundle.reviews:
            reviews_df = pd.DataFrame(bundle.reviews)
            st.dataframe(reviews_df, use_container_width=True)
    
    with detail_tab4:
        st.write(f"**Audit Log Entries:** {len(bundle.audit_log)}")
        if bundle.audit_log:
            audit_df = pd.DataFrame(bundle.audit_log)
            st.dataframe(audit_df, use_container_width=True)


def render_task_console_tab(task_manager: TaskManager):
    """Render task console tab."""
    st.subheader("✅ Task Console")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Status",
            options=["all", "not_started", "in_progress", "blocked", "completed"],
            index=0
        )
    with col2:
        type_filter = st.selectbox(
            "Type",
            options=["all", "mechanism", "regulatory", "review", "documentation", "research"],
            index=0
        )
    
    # List tasks
    tasks = task_manager.list_tasks(
        status=status_filter if status_filter != "all" else None,
        task_type=type_filter if type_filter != "all" else None
    )
    
    if tasks:
        tasks_df = pd.DataFrame([t.to_dict() for t in tasks])
        st.dataframe(tasks_df, use_container_width=True, height=500)
    else:
        st.info("No tasks found")


def render_review_center_tab(bundles_engine: CaseBundlesEngine, review_workflow: ReviewWorkflow):
    """Render review center tab."""
    st.subheader("👥 Review Center")
    
    # List bundles in review
    review_bundles = bundles_engine.list_bundles(status="peer_review", limit=20)
    
    if review_bundles:
        bundle_options = [f"{b.drug} → {b.reaction} ({b.bundle_id[:8]})" for b in review_bundles]
        selected = st.selectbox("Select Bundle to Review", options=bundle_options)
        
        if selected:
            bundle_idx = bundle_options.index(selected)
            bundle = review_bundles[bundle_idx]
            
            st.markdown(f"### Review: {bundle.drug} → {bundle.reaction}")
            
            # Review form
            reviewer = st.text_input("Reviewer ID", "reviewer1")
            decision = st.selectbox("Decision", options=["approve", "reject", "request_changes"])
            comments = st.text_area("Comments")
            
            if st.button("Submit Review"):
                result = review_workflow.submit_review(
                    bundle, reviewer, decision, comments
                )
                st.success(f"✅ Review submitted: {result.get('status')}")
                st.rerun()
    else:
        st.info("No bundles in review")


def render_workflow_status_tab(bundles_engine: CaseBundlesEngine):
    """Render workflow status tab."""
    st.subheader("📊 Workflow Status")
    
    # Statistics
    all_bundles = bundles_engine.list_bundles(limit=1000)
    
    if all_bundles:
        status_counts = {}
        for bundle in all_bundles:
            status_counts[bundle.status] = status_counts.get(bundle.status, 0) + 1
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Draft", status_counts.get("draft", 0))
        with col2:
            st.metric("In Review", status_counts.get("peer_review", 0))
        with col3:
            st.metric("Final Review", status_counts.get("final_review", 0))
        with col4:
            st.metric("Approved", status_counts.get("approved", 0))
        with col5:
            st.metric("Rejected", status_counts.get("rejected", 0))
    else:
        st.info("No bundles created yet")


def render_audit_log_tab(audit_trail: AuditTrail):
    """Render audit log tab."""
    st.subheader("📋 Audit Log")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        entity_type_filter = st.selectbox(
            "Entity Type",
            options=["all", "bundle", "task", "review"],
            index=0
        )
    with col2:
        action_filter = st.text_input("Action Filter", "")
    
    # Get audit log
    logs = audit_trail.get_audit_log(
        entity_type=entity_type_filter if entity_type_filter != "all" else None,
        action=action_filter if action_filter else None,
        limit=100
    )
    
    if logs:
        logs_df = pd.DataFrame(logs)
        st.dataframe(logs_df, use_container_width=True, height=500)
        
        # Export
        if st.button("📥 Export Audit Log"):
            exported = audit_trail.export_audit_log(format="json")
            st.download_button("Download JSON", exported, file_name="audit_log.json")
    else:
        st.info("No audit log entries")

