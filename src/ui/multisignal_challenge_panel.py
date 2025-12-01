"""
Multi-Signal Inspector Challenge Panel (CHUNK 6.22.5)
UI for multi-signal inspector interrogation with cross-signal questions, class effects, and consistency challenges.
"""
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import time

try:
    from src.ai.inspector_multisignal_engine import MultiSignalInspectorChallenge, generate_cross_signal_questions, generate_cross_link_followups
    MULTISIGNAL_AVAILABLE = True
except ImportError:
    MULTISIGNAL_AVAILABLE = False

try:
    from src.ai.inspector_observation_engine import generate_observation_letter
    OBSERVATION_AVAILABLE = True
except ImportError:
    OBSERVATION_AVAILABLE = False


def render_multisignal_challenge_panel(
    signals: Optional[List[Dict[str, Any]]] = None,
    df: Optional[Any] = None,
    persona: str = "FDA Pharmacovigilance Inspector"
) -> None:
    """
    Render multi-signal inspector challenge UI panel.
    
    Features:
    - Signal selection
    - Cross-signal questions
    - Class effect interrogation
    - Consistency challenges
    - Answer evaluation
    - Final challenge report
    """
    st.header("🕵️ Multi-Signal Inspector Challenge")
    st.caption("Experience the hardest real FDA/EMA inspection scenario: cross-signal interrogation, class effects, and consistency challenges.")
    
    if not MULTISIGNAL_AVAILABLE:
        st.error("Multi-signal inspector challenge engine not available. Please install required dependencies.")
        return
    
    # Get signals from session state if not provided
    if not signals:
        signals = st.session_state.get("governance_signals", [])
        if not signals:
            # Try extracting from DataFrame
            if df is not None and not df.empty:
                signals = _extract_signals_from_df(df)
    
    if not signals or len(signals) < 2:
        st.warning("⚠️ You need at least 2 signals to run a multi-signal challenge. Upload data or load signals first.")
        
        # Show how to get signals
        with st.expander("ℹ️ How to get signals"):
            st.markdown("""
            Multi-signal challenges require multiple active signals. You can:
            
            1. **Upload safety data** - The system will detect signals automatically
            2. **Run Trend Alerts** - Detected signals appear in the Trend Alerts tab
            3. **View Governance Dashboard** - Active signals are listed there
            4. **Generate RPF Analysis** - Signals are automatically extracted from RPF results
            """)
        return
    
    # Initialize session state
    if "multisignal_challenge" not in st.session_state:
        st.session_state.multisignal_challenge = None
        st.session_state.multisignal_questions = []
        st.session_state.multisignal_transcript = []
        st.session_state.multisignal_current_question = 0
    
    # ==========================
    # SIGNAL SELECTION
    # ==========================
    st.markdown("### 📋 Select Signals for Challenge")
    
    # Display available signals
    signal_options = {}
    for i, signal in enumerate(signals):
        drug = signal.get("drug", signal.get("drug_name", "Unknown"))
        reaction = signal.get("reaction", signal.get("event", signal.get("reaction_pt", "Unknown")))
        priority = signal.get("priority", signal.get("risk_level", "Unknown"))
        rpf_score = signal.get("rpf_score", signal.get("rpf", 0))
        
        signal_label = f"{drug} - {reaction} (Priority: {priority}, RPF: {rpf_score})"
        signal_options[signal_label] = i
    
    selected_labels = st.multiselect(
        "Choose signals to include in the challenge (minimum 2):",
        options=list(signal_options.keys()),
        default=list(signal_options.keys())[:min(5, len(signal_options))],
        key="multisignal_selection"
    )
    
    selected_signals = [signals[signal_options[label]] for label in selected_labels]
    
    if len(selected_signals) < 2:
        st.info("Select at least 2 signals to start the challenge.")
        return
    
    st.info(f"✅ {len(selected_signals)} signal(s) selected for challenge")
    
    # Persona selection
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_persona = st.selectbox(
            "Inspector Persona:",
            options=[
                "FDA Pharmacovigilance Inspector",
                "FDA Clinical Reviewer",
                "EMA Signal Assessor",
                "EMA Pharmacovigilance Inspector",
                "MHRA Safety Auditor",
                "PMDA Reviewer"
            ],
            index=0,
            key="multisignal_persona"
        )
    with col2:
        challenge_intensity = st.selectbox(
            "Challenge Intensity:",
            options=["Standard", "Aggressive", "Formal Audit"],
            index=0,
            key="multisignal_intensity"
        )
    
    # ==========================
    # START CHALLENGE
    # ==========================
    if st.button("🚀 Start Multi-Signal Challenge", type="primary", use_container_width=True):
        with st.spinner("Analyzing signals and generating challenge questions..."):
            challenge = MultiSignalInspectorChallenge(selected_signals, selected_persona)
            challenge_result = challenge.run_multi_signal_challenge()
            
            st.session_state.multisignal_challenge = challenge
            st.session_state.multisignal_questions = challenge_result.get("questions", [])
            st.session_state.multisignal_transcript = []
            st.session_state.multisignal_current_question = 0
            st.session_state.multisignal_patterns = challenge_result.get("detected_patterns", {})
            st.rerun()
    
    # ==========================
    # CHALLENGE IN PROGRESS
    # ==========================
    if st.session_state.multisignal_challenge and st.session_state.multisignal_questions:
        challenge: MultiSignalInspectorChallenge = st.session_state.multisignal_challenge
        questions = st.session_state.multisignal_questions
        current_q_idx = st.session_state.multisignal_current_question
        
        st.markdown("---")
        
        # Progress
        st.markdown(f"### 📊 Challenge Progress: Question {current_q_idx + 1} of {len(questions)}")
        progress = (current_q_idx + 1) / len(questions) if questions else 0
        st.progress(progress)
        
        # Show detected patterns
        if st.session_state.get("multisignal_patterns"):
            patterns = st.session_state.multisignal_patterns
            with st.expander("🔍 Detected Patterns (Inspector's Focus Areas)"):
                if patterns.get("class_effects"):
                    st.warning(f"⚠️ {len(patterns['class_effects'])} potential class effect(s) detected")
                    for ce in patterns["class_effects"][:3]:
                        st.caption(f"- {ce.get('drug_class', 'Unknown')}: {len(ce.get('signals', []))} signals")
                
                if patterns.get("priority_discrepancies"):
                    st.warning(f"⚠️ {len(patterns['priority_discrepancies'])} priority discrepancy/ies found")
                    for pd in patterns["priority_discrepancies"][:3]:
                        signal = pd.get("signal", {})
                        st.caption(f"- {signal.get('drug', 'Unknown')} - {signal.get('reaction', 'Unknown')}: {pd.get('issue', 'N/A')}")
        
        # Current question
        if current_q_idx < len(questions):
            question_text = questions[current_q_idx]
            
            st.markdown("---")
            st.markdown(f"### ❓ Question {current_q_idx + 1}")
            st.info(f"**{selected_persona} asks:**\n\n{question_text}")
            
            # Answer input
            answer_key = f"multisignal_answer_{current_q_idx}"
            user_answer = st.text_area(
                "**Your Answer:**",
                height=200,
                placeholder="Provide a comprehensive, evidence-based response. Address all aspects of the question.",
                key=answer_key
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                submit_button = st.button("📤 Submit Answer", type="primary", use_container_width=True)
            with col2:
                if st.button("⏭️ Skip Question", use_container_width=True):
                    st.session_state.multisignal_current_question = min(current_q_idx + 1, len(questions))
                    st.rerun()
            
            # Submit answer
            if submit_button and user_answer:
                with st.spinner("Inspector evaluating your answer and preparing follow-up..."):
                    # Generate follow-up challenge
                    followup_result = challenge.generate_cross_link_followup(
                        user_answer,
                        question_text,
                        challenge_type="consistency"
                    )
                    
                    # Store in transcript
                    transcript_entry = {
                        "question_index": current_q_idx,
                        "question": question_text,
                        "answer": user_answer,
                        "followup": followup_result.get("followup", ""),
                        "escalation_level": followup_result.get("escalation_level", 1),
                        "challenge_type": followup_result.get("challenge_type", "consistency"),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if len(st.session_state.multisignal_transcript) > current_q_idx:
                        st.session_state.multisignal_transcript[current_q_idx] = transcript_entry
                    else:
                        st.session_state.multisignal_transcript.append(transcript_entry)
                    
                    # Display follow-up
                    st.markdown("---")
                    st.markdown("### 🔍 Inspector Follow-Up")
                    
                    escalation_level = followup_result.get("escalation_level", 1)
                    if escalation_level >= 4:
                        st.error(f"**Escalation Level {escalation_level}/5 (Critical)**")
                    elif escalation_level >= 3:
                        st.warning(f"**Escalation Level {escalation_level}/5 (High)**")
                    else:
                        st.info(f"**Escalation Level {escalation_level}/5**")
                    
                    st.write(followup_result.get("followup", "No follow-up generated."))
                    
                    # Move to next question or complete
                    if current_q_idx + 1 < len(questions):
                        st.session_state.multisignal_current_question = current_q_idx + 1
                        st.info("➡️ Moving to next question...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.multisignal_challenge_complete = True
                        st.success("🎉 Challenge completed! Generate final report below.")
        
        # ==========================
        # GENERATE FINAL REPORT
        # ==========================
        if st.session_state.get("multisignal_challenge_complete", False) or current_q_idx >= len(questions):
            st.markdown("---")
            st.markdown("### 📄 Final Multi-Signal Challenge Report")
            
            if st.button("📋 Generate Final Challenge Report", type="primary", use_container_width=True):
                with st.spinner("Generating comprehensive challenge report..."):
                    final_report = _generate_final_challenge_report(
                        challenge,
                        st.session_state.multisignal_transcript,
                        selected_signals
                    )
                    
                    st.session_state.multisignal_final_report = final_report
                    st.rerun()
            
            # Display final report
            if "multisignal_final_report" in st.session_state:
                report = st.session_state.multisignal_final_report
                
                st.markdown("---")
                st.markdown("#### 📊 Challenge Summary")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Questions Answered", len(st.session_state.multisignal_transcript))
                with col2:
                    avg_escalation = sum([t.get("escalation_level", 1) for t in st.session_state.multisignal_transcript]) / len(st.session_state.multisignal_transcript) if st.session_state.multisignal_transcript else 0
                    st.metric("Avg Escalation Level", f"{avg_escalation:.1f}/5")
                with col3:
                    high_escalation = len([t for t in st.session_state.multisignal_transcript if t.get("escalation_level", 1) >= 4])
                    st.metric("Critical Challenges", high_escalation)
                
                # Full report
                st.markdown("---")
                st.markdown("#### 📄 Full Challenge Report")
                st.markdown(report.get("summary", "Report not available."))
                
                # Export
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    json_str = json.dumps(report, indent=2, default=str)
                    st.download_button(
                        "📥 Download JSON",
                        json_str,
                        file_name=f"multisignal_challenge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                with col2:
                    if st.button("🔄 Start New Challenge", use_container_width=True):
                        st.session_state.multisignal_challenge = None
                        st.session_state.multisignal_questions = []
                        st.session_state.multisignal_transcript = []
                        st.session_state.multisignal_current_question = 0
                        st.session_state.multisignal_final_report = None
                        st.session_state.multisignal_challenge_complete = False
                        st.rerun()


def _extract_signals_from_df(df) -> List[Dict[str, Any]]:
    """Extract signals from DataFrame."""
    signals = []
    
    drug_col = next((col for col in ["drug_normalized", "drug_name", "drug"] if col in df.columns), None)
    reaction_col = next((col for col in ["reaction_normalized", "reaction_pt", "reaction"] if col in df.columns), None)
    
    if not drug_col or not reaction_col:
        return signals
    
    grouped = df.groupby([drug_col, reaction_col])
    for (drug, reaction), group_df in grouped:
        signals.append({
            "drug": drug,
            "reaction": reaction,
            "cases": len(group_df),
            "priority": "Medium",
            "rpf_score": 50
        })
    
    return signals


def _generate_final_challenge_report(
    challenge: MultiSignalInspectorChallenge,
    transcript: List[Dict[str, Any]],
    signals: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate final challenge report."""
    patterns = challenge.analyze_signal_patterns()
    
    high_escalation = [t for t in transcript if t.get("escalation_level", 1) >= 4]
    avg_escalation = sum([t.get("escalation_level", 1) for t in transcript]) / len(transcript) if transcript else 0
    
    summary = f"""
    # Multi-Signal Inspector Challenge Report
    
    **Challenge Date:** {datetime.now().strftime('%Y-%m-%d')}
    **Inspector Persona:** {challenge.persona}
    **Signals Evaluated:** {len(signals)}
    **Questions Answered:** {len(transcript)}
    
    ## Key Findings
    
    - **Average Escalation Level:** {avg_escalation:.1f}/5
    - **Critical Challenges:** {len(high_escalation)}
    - **Class Effects Detected:** {len(patterns.get('class_effects', []))}
    - **Priority Discrepancies:** {len(patterns.get('priority_discrepancies', []))}
    
    ## Areas Requiring Attention
    
    {', '.join([t.get('challenge_type', 'consistency') for t in high_escalation[:5]]) if high_escalation else 'None'}
    
    ## Recommendations
    
    - Review and align signal prioritization criteria
    - Strengthen cross-signal consistency documentation
    - Enhance class effect identification process
    - Improve rationale documentation for escalation decisions
    """
    
    return {
        "summary": summary,
        "signals": signals,
        "transcript": transcript,
        "patterns": patterns,
        "metrics": {
            "avg_escalation": avg_escalation,
            "critical_challenges": len(high_escalation),
            "class_effects": len(patterns.get('class_effects', [])),
            "discrepancies": len(patterns.get('priority_discrepancies', []))
        },
        "timestamp": datetime.now().isoformat()
    }



