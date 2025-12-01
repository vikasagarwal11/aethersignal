"""
Mock Inspection Day Panel (CHUNK 6.22.4)
Full UI for mock inspection simulation with multi-step progression, scoring, and final report.
"""
import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
import time

try:
    from src.ai.mock_inspection_day import MockInspectionDay, run_mock_inspection, compile_mock_inspection_report
    INSPECTION_AVAILABLE = True
except ImportError:
    INSPECTION_AVAILABLE = False

try:
    from src.ai.inspector_observation_engine import generate_observation_letter
    OBSERVATION_AVAILABLE = True
except ImportError:
    OBSERVATION_AVAILABLE = False


def render_mock_inspection_day(df: Optional[Any] = None, signal_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Render complete Mock Inspection Day UI panel.
    
    Features:
    - Start/stop inspection
    - Multi-step progression
    - Answer submission with scoring
    - Real-time feedback
    - Final report generation
    - Observation letter generation
    """
    st.header("🕵️ Mock Inspection Day — Full Audit Simulation")
    st.caption("Experience a complete FDA/EMA/MHRA inspection simulation with multi-step questioning, answer scoring, and final regulatory report generation.")
    
    if df is None:
        # Try to get from session state
        df = st.session_state.get("normalized_data")
    
    if df is None or df.empty:
        st.info("⚠️ Upload safety data to begin mock inspection. Load data from the main upload section.")
        return
    
    if not INSPECTION_AVAILABLE:
        st.error("Mock inspection engine not available. Please install required dependencies.")
        return
    
    # Initialize or retrieve inspection session
    if "mock_inspection" not in st.session_state:
        st.session_state.mock_inspection = None
        st.session_state.inspection_started = False
        st.session_state.current_step = 0
        st.session_state.inspection_transcript = []
    
    # Get signal data if available
    if not signal_data:
        signal_data = st.session_state.get("current_signal", {})
    
    # ==========================
    # START INSPECTION
    # ==========================
    if not st.session_state.inspection_started:
        st.markdown("### 🚀 Start Mock Inspection")
        st.info("This simulation will walk you through a complete regulatory inspection with multiple steps and inspectors.")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("▶️ Start Mock Inspection", type="primary", use_container_width=True):
                with st.spinner("Initializing inspection..."):
                    inspection = run_mock_inspection(df=df, signal_data=signal_data)
                    start_result = inspection.start_inspection()
                    
                    st.session_state.mock_inspection = inspection
                    st.session_state.inspection_started = True
                    st.session_state.current_step = 0
                    st.session_state.inspection_transcript = []
                    st.session_state.step_start_time = time.time()
                    st.rerun()
    
    # ==========================
    # INSPECTION IN PROGRESS
    # ==========================
    if st.session_state.inspection_started and st.session_state.mock_inspection:
        inspection: MockInspectionDay = st.session_state.mock_inspection
        
        # Progress indicator
        total_steps = len(inspection.steps) - 1  # Exclude final summary
        current_step_idx = st.session_state.current_step
        
        st.markdown("---")
        st.markdown(f"### 📊 Inspection Progress: Step {current_step_idx + 1} of {total_steps}")
        progress = (current_step_idx + 1) / total_steps if total_steps > 0 else 0
        st.progress(progress)
        
        # Overall score display
        if inspection.total_score > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Score", f"{inspection.total_score:.1f}/100")
            with col2:
                avg_time = sum([t.get("time_taken_seconds", 0) for t in inspection.transcript]) / len(inspection.transcript) if inspection.transcript else 0
                st.metric("Avg Time/Step", f"{avg_time:.1f}s")
            with col3:
                elapsed = (datetime.now() - inspection.start_time).total_seconds() / 60 if inspection.start_time else 0
                st.metric("Elapsed Time", f"{elapsed:.1f} min")
        
        # Current step
        if current_step_idx < len(inspection.steps) - 1:
            current_step = inspection.steps[current_step_idx]
            
            st.markdown("---")
            st.markdown(f"### Step {current_step_idx + 1}: {current_step['step']}")
            st.caption(f"**Inspector:** {current_step['persona']} | **Focus:** {current_step['focus']}")
            
            # Display question (from transcript if available, or generate)
            question_text = None
            if inspection.transcript and len(inspection.transcript) > current_step_idx:
                question_text = inspection.transcript[current_step_idx].get("question", "")
            
            if not question_text:
                # Generate question for display
                try:
                    from src.ai.inspector_simulation import InspectorSimulator
                    inspector = InspectorSimulator(current_step["persona"])
                    question_data = inspector.generate_inspector_question(df=df, signal_data=signal_data)
                    question_text = question_data.get("question", "")
                    
                    # Store in transcript
                    if len(inspection.transcript) <= current_step_idx:
                        inspection.transcript.append({
                            "step_index": current_step_idx,
                            "step_name": current_step["step"],
                            "persona": current_step["persona"],
                            "question": question_text,
                            "timestamp": datetime.now().isoformat()
                        })
                except Exception:
                    question_text = f"[Generate question for: {current_step['step']}]"
            
            if question_text:
                st.info(f"**Inspector Question:**\n\n{question_text}")
            
            # Answer input
            answer_key = f"answer_step_{current_step_idx}"
            user_answer = st.text_area(
                "**Your Answer:**",
                height=200,
                placeholder="Type your response to the inspector's question here. Be comprehensive and provide evidence-based justifications.",
                key=answer_key
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                submit_button = st.button("📤 Submit Answer", type="primary", use_container_width=True)
            
            with col2:
                if st.button("⏭️ Skip Step", use_container_width=True):
                    # Skip with empty answer
                    time_taken = time.time() - st.session_state.get("step_start_time", time.time())
                    result = inspection.process_step_answer(current_step_idx, "", time_taken)
                    st.session_state.current_step = current_step_idx + 1
                    st.session_state.step_start_time = time.time()
                    st.rerun()
            
            # Submit answer
            if submit_button and user_answer:
                with st.spinner("Inspector evaluating your answer..."):
                    time_taken = time.time() - st.session_state.get("step_start_time", time.time())
                    result = inspection.process_step_answer(current_step_idx, user_answer, time_taken)
                    
                    # Display evaluation
                    evaluation = result.get("current_step_evaluation", {})
                    score = evaluation.get("score", 0)
                    
                    st.markdown("---")
                    st.markdown("### 📋 Inspector Evaluation")
                    
                    # Score visualization
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        score_color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
                        st.metric("Score", f"{score_color} {score}/100")
                    with col2:
                        escalation = evaluation.get("escalation_level", 1)
                        st.metric("Escalation Level", f"{escalation}/5")
                    with col3:
                        next_action = evaluation.get("next_action", "continue")
                        st.metric("Status", next_action.replace("_", " ").title())
                    
                    # Feedback
                    feedback = evaluation.get("feedback", "")
                    if feedback:
                        if score >= 80:
                            st.success(f"✅ **Feedback:** {feedback}")
                        elif score >= 60:
                            st.warning(f"⚠️ **Feedback:** {feedback}")
                        else:
                            st.error(f"❌ **Feedback:** {feedback}")
                    
                    # Score breakdown
                    breakdown = evaluation.get("score_breakdown", {})
                    if breakdown:
                        st.markdown("#### Score Breakdown")
                        st.json(breakdown)
                    
                    # Move to next step
                    if not result.get("inspection_complete", False):
                        st.session_state.current_step = current_step_idx + 1
                        st.session_state.step_start_time = time.time()
                        st.info("➡️ Moving to next step...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.inspection_complete = True
                        st.success("🎉 Inspection completed! Generate final report below.")
        
        # ==========================
        # GENERATE FINAL REPORT
        # ==========================
        if st.session_state.get("inspection_complete", False) or current_step_idx >= total_steps:
            st.markdown("---")
            st.markdown("### 📄 Final Inspection Report")
            
            if st.button("📋 Generate Final Inspection Report", type="primary", use_container_width=True):
                with st.spinner("Generating comprehensive inspection report... This may take a moment."):
                    final_report = compile_mock_inspection_report(inspection)
                    
                    st.session_state.final_inspection_report = final_report
                    st.rerun()
            
            # Display final report if generated
            if "final_inspection_report" in st.session_state:
                report = st.session_state.final_inspection_report
                
                # Report summary
                st.markdown("---")
                st.markdown("#### 📊 Inspection Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Overall Score", f"{report.get('overall_score', 0):.1f}/100")
                with col2:
                    st.metric("Major Observations", report.get("major_observations_count", 0))
                with col3:
                    st.metric("Minor Observations", report.get("minor_observations_count", 0))
                with col4:
                    st.metric("Duration", f"{report.get('inspection_duration_minutes', 0):.1f} min")
                
                # Full report content
                st.markdown("---")
                st.markdown("#### 📄 Full Inspection Report")
                st.markdown(report.get("full_report", "Report not available."))
                
                # Observations
                if report.get("major_observations"):
                    st.markdown("---")
                    st.markdown("#### 🚨 Major Observations")
                    for i, obs in enumerate(report["major_observations"], 1):
                        with st.expander(f"Major Observation {i}: {obs.get('step', 'Unknown')}"):
                            st.write(f"**Issue:** {obs.get('issue', 'N/A')}")
                            st.write(f"**Score:** {obs.get('score', 0)}/100")
                
                if report.get("minor_observations"):
                    st.markdown("---")
                    st.markdown("#### ⚠️ Minor Observations")
                    for i, obs in enumerate(report["minor_observations"], 1):
                        with st.expander(f"Minor Observation {i}: {obs.get('step', 'Unknown')}"):
                            st.write(f"**Issue:** {obs.get('issue', 'N/A')}")
                            st.write(f"**Score:** {obs.get('score', 0)}/100")
                
                # Observation letter
                if report.get("observation_letter") and OBSERVATION_AVAILABLE:
                    st.markdown("---")
                    st.markdown("#### 📜 Observation Letter")
                    obs_letter = report["observation_letter"]
                    with st.expander(f"{obs_letter.get('letter_type', 'Observation Letter')} ({obs_letter.get('agency', 'FDA')})"):
                        st.markdown(obs_letter.get("content", "Letter not available."))
                        st.caption(f"**Severity:** {obs_letter.get('severity', 'N/A')}")
                        st.caption(f"**Response Required:** {obs_letter.get('response_required_days', 30)} days")
                
                # Recommended actions
                if report.get("recommended_actions"):
                    st.markdown("---")
                    st.markdown("#### ✅ Recommended Actions")
                    for action in report["recommended_actions"]:
                        st.markdown(f"- {action}")
                
                # Export options
                st.markdown("---")
                st.markdown("#### 📥 Export Report")
                col1, col2 = st.columns(2)
                with col1:
                    import json
                    json_str = json.dumps(report, indent=2, default=str)
                    st.download_button(
                        "📥 Download JSON",
                        json_str,
                        file_name=f"mock_inspection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                with col2:
                    if st.button("🔄 Start New Inspection", use_container_width=True):
                        st.session_state.mock_inspection = None
                        st.session_state.inspection_started = False
                        st.session_state.current_step = 0
                        st.session_state.inspection_transcript = []
                        st.session_state.final_inspection_report = None
                        st.rerun()
        
        # Sidebar: Inspection status
        with st.sidebar:
            st.markdown("### 🕵️ Inspection Status")
            if inspection.start_time:
                elapsed = (datetime.now() - inspection.start_time).total_seconds() / 60
                st.caption(f"Duration: {elapsed:.1f} minutes")
            
            st.caption(f"Steps Completed: {len(inspection.transcript)}/{total_steps}")
            
            if inspection.inspectors_used:
                st.markdown("#### Inspectors")
                for inspector in inspection.inspectors_used:
                    st.caption(f"✓ {inspector}")
            
            if inspection.total_score > 0:
                st.markdown("#### Performance")
                st.caption(f"Overall Score: {inspection.total_score:.1f}/100")
                
                if inspection.step_scores:
                    st.caption("Step Scores:")
                    for i, score in enumerate(inspection.step_scores, 1):
                        score_icon = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
                        st.caption(f"{score_icon} Step {i}: {score:.1f}/100")
