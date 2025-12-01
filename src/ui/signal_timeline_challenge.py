"""
Signal Timeline Challenge Panel (CHUNK 6.22.6)
UI for timeline-based inspector interrogation with case linking, delay questions, and regulatory action tracking.
"""
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

try:
    from src.ai.timeline_engine import build_signal_timeline, analyze_timeline_gaps
    TIMELINE_AVAILABLE = True
except ImportError:
    TIMELINE_AVAILABLE = False

try:
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from src.ai.inspector_simulation import InspectorSimulator
    SIMULATION_AVAILABLE = True
except ImportError:
    SIMULATION_AVAILABLE = False


def render_signal_timeline_challenge(
    signal: Optional[Dict[str, Any]] = None,
    df: Optional[Any] = None,
    persona: str = "FDA Pharmacovigilance Inspector"
) -> None:
    """
    Render signal timeline inspector challenge UI.
    
    Features:
    - Automatic timeline generation
    - Timeline gap analysis
    - Inspector timeline questions
    - Delay and escalation challenges
    - Regulatory action tracking
    """
    st.header("🕒 Signal Timeline Inspection Challenge")
    st.caption("One of the hardest inspection challenges: timeline interrogation, case linking, and delay questions.")
    
    if not TIMELINE_AVAILABLE:
        st.error("Timeline engine not available. Please install required dependencies.")
        return
    
    # Get signal from session state if not provided
    if not signal:
        signal = st.session_state.get("current_signal", {})
        if not signal:
            st.warning("⚠️ Select a signal to begin timeline challenge. Navigate to a signal from the Trend Alerts or Governance Dashboard.")
            
            with st.expander("ℹ️ How to get a signal"):
                st.markdown("""
                To use the Timeline Challenge:
                
                1. **Upload safety data** - Signals are automatically detected
                2. **Run Trend Alerts** - Select a signal from the alerts
                3. **Open Governance Dashboard** - Click on a signal to view details
                4. **Select Signal** - The system will use that signal for timeline challenge
                """)
            return
    
    # Get DataFrame if available
    if df is None:
        df = st.session_state.get("normalized_data")
    
    # Initialize session state
    if "timeline_challenge" not in st.session_state:
        st.session_state.timeline_challenge = None
        st.session_state.timeline_data = None
        st.session_state.timeline_questions = []
        st.session_state.timeline_transcript = []
        st.session_state.timeline_current_question = 0
    
    # ==========================
    # BUILD TIMELINE
    # ==========================
    if st.button("📅 Build Signal Timeline", type="primary", use_container_width=True):
        with st.spinner("Analyzing signal history and building comprehensive timeline..."):
            # Get trend alerts if available
            trend_alerts = st.session_state.get("last_trend_alerts_result", {}).get("alerts", [])
            
            # Filter alerts for this signal
            signal_alerts = [
                alert for alert in trend_alerts
                if alert.get("drug") == signal.get("drug") and alert.get("reaction") == signal.get("reaction")
            ]
            
            timeline = build_signal_timeline(
                signal=signal,
                df=df,
                trend_alerts=signal_alerts,
                rpf_history=signal.get("rpf_history", []),
                governance_events=signal.get("governance_events", [])
            )
            
            st.session_state.timeline_data = timeline
            st.session_state.timeline_challenge = True
            st.rerun()
    
    # ==========================
    # DISPLAY TIMELINE
    # ==========================
    if st.session_state.get("timeline_data"):
        timeline = st.session_state.timeline_data
        
        st.markdown("---")
        st.markdown("### 📊 Signal Timeline")
        
        # Timeline summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("First Case", timeline.get("first_case_date", "Unknown")[:10] if timeline.get("first_case_date") else "Unknown")
        with col2:
            st.metric("Detection Date", timeline.get("detection_date", "Unknown")[:10] if timeline.get("detection_date") else "Unknown")
        with col3:
            st.metric("Case Spikes", len(timeline.get("case_spikes", [])))
        with col4:
            latest_rpf = timeline.get("rpf_scores", [{}])[-1] if timeline.get("rpf_scores") else {}
            st.metric("Current RPF", f"{latest_rpf.get('rpf_score', 'N/A')}" if latest_rpf.get('rpf_score') else "N/A")
        
        # Expandable full timeline
        with st.expander("📋 Show Full Timeline Details"):
            st.json(timeline)
        
        # Analyze gaps
        gaps = analyze_timeline_gaps(timeline)
        if gaps:
            st.markdown("---")
            st.markdown("### ⚠️ Timeline Gaps & Potential Issues")
            for gap in gaps:
                severity = gap.get("severity", "medium")
                if severity == "high":
                    st.error(f"🔴 **{gap.get('type', 'Unknown').replace('_', ' ').title()}**: {gap.get('description', 'N/A')}")
                elif severity == "medium":
                    st.warning(f"🟡 **{gap.get('type', 'Unknown').replace('_', ' ').title()}**: {gap.get('description', 'N/A')}")
                else:
                    st.info(f"🔵 **{gap.get('type', 'Unknown').replace('_', ' ').title()}**: {gap.get('description', 'N/A')}")
        
        # ==========================
        # GENERATE INSPECTOR QUESTIONS
        # ==========================
        if st.button("❓ Generate Inspector Timeline Questions", type="primary", use_container_width=True):
            with st.spinner("Inspector analyzing timeline and generating challenging questions..."):
                questions = _generate_timeline_questions(timeline, gaps, persona)
                st.session_state.timeline_questions = questions
                st.session_state.timeline_transcript = []
                st.session_state.timeline_current_question = 0
                st.rerun()
        
        # ==========================
        # TIMELINE QUESTIONS
        # ==========================
        if st.session_state.get("timeline_questions"):
            questions = st.session_state.timeline_questions
            current_q_idx = st.session_state.timeline_current_question
            
            st.markdown("---")
            st.markdown(f"### ❓ Timeline Question {current_q_idx + 1} of {len(questions)}")
            
            if current_q_idx < len(questions):
                question_text = questions[current_q_idx]
                
                st.info(f"**{persona} asks:**\n\n{question_text}")
                
                # Answer input
                answer_key = f"timeline_answer_{current_q_idx}"
                user_answer = st.text_area(
                    "**Your Answer:**",
                    height=200,
                    placeholder="Provide a comprehensive response addressing the timeline, dates, and actions taken.",
                    key=answer_key
                )
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    submit_button = st.button("📤 Submit Answer", type="primary", use_container_width=True)
                with col2:
                    if st.button("⏭️ Skip Question", use_container_width=True):
                        st.session_state.timeline_current_question = min(current_q_idx + 1, len(questions))
                        st.rerun()
                
                # Submit answer
                if submit_button and user_answer:
                    with st.spinner("Inspector evaluating your timeline response..."):
                        followup = _generate_timeline_followup(
                            question_text,
                            user_answer,
                            timeline,
                            gaps,
                            persona
                        )
                        
                        # Store in transcript
                        transcript_entry = {
                            "question_index": current_q_idx,
                            "question": question_text,
                            "answer": user_answer,
                            "followup": followup.get("followup", ""),
                            "escalation_level": followup.get("escalation_level", 1),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        if len(st.session_state.timeline_transcript) > current_q_idx:
                            st.session_state.timeline_transcript[current_q_idx] = transcript_entry
                        else:
                            st.session_state.timeline_transcript.append(transcript_entry)
                        
                        # Display follow-up
                        st.markdown("---")
                        st.markdown("### 🔍 Inspector Follow-Up")
                        
                        escalation = followup.get("escalation_level", 1)
                        if escalation >= 4:
                            st.error(f"**Escalation Level {escalation}/5 (Critical)**")
                        elif escalation >= 3:
                            st.warning(f"**Escalation Level {escalation}/5 (High)**")
                        else:
                            st.info(f"**Escalation Level {escalation}/5**")
                        
                        st.write(followup.get("followup", "No follow-up generated."))
                        
                        # Move to next question
                        if current_q_idx + 1 < len(questions):
                            st.session_state.timeline_current_question = current_q_idx + 1
                            st.info("➡️ Moving to next question...")
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.session_state.timeline_challenge_complete = True
                            st.success("🎉 Timeline challenge completed!")


def _generate_timeline_questions(
    timeline: Dict[str, Any],
    gaps: List[Dict[str, Any]],
    persona: str
) -> List[str]:
    """Generate timeline-based inspector questions."""
    questions = []
    
    # First case vs detection delay questions
    if timeline.get("first_case_date") and timeline.get("detection_date"):
        try:
            first = datetime.fromisoformat(timeline["first_case_date"].replace("Z", "+00:00"))
            detected = datetime.fromisoformat(timeline["detection_date"].replace("Z", "+00:00"))
            delay_days = (detected - first).days
            
            if delay_days > 90:
                questions.append(
                    f"Your first case for {timeline.get('drug', 'this drug')} - {timeline.get('reaction', 'this reaction')} "
                    f"was reported on {timeline['first_case_date'][:10]}, but the signal was not detected until "
                    f"{timeline['detection_date'][:10]} - a delay of {delay_days} days. "
                    f"Can you explain this delay? What was your signal detection process during this period? "
                    f"Were there any missed opportunities to detect this signal earlier?"
                )
        except Exception:
            pass
    
    # Case spike questions
    if timeline.get("case_spikes"):
        spike = timeline["case_spikes"][0]
        questions.append(
            f"A case spike was detected on {spike.get('date', 'Unknown')[:10]} with {spike.get('case_count', 0)} cases. "
            f"What actions did you take in response to this spike? Can you show me the documentation "
            f"of your risk assessment and any escalation decisions made at that time?"
        )
    
    # RPF escalation questions
    rpf_scores = timeline.get("rpf_scores", [])
    if rpf_scores:
        high_rpf = [s for s in rpf_scores if s.get("rpf_score", 0) >= 70]
        if high_rpf and not timeline.get("escalation_history"):
            questions.append(
                f"Your RPF score reached {high_rpf[0].get('rpf_score')} on {high_rpf[0].get('date', 'Unknown')[:10]}, "
                f"which indicates high priority. However, I don't see evidence of escalation in your timeline. "
                f"Can you explain why this signal was not escalated? What was the rationale for not "
                f"prioritizing this signal for assessment?"
            )
    
    # Missing governance questions
    if gaps:
        for gap in gaps[:2]:  # Top 2 gaps
            if gap.get("type") == "missing_governance":
                questions.append(
                    f"Your timeline shows no governance review events documented for this signal. "
                    f"Can you explain your governance process? Who was responsible for reviewing this signal, "
                    f"and what documentation exists to support the review?"
                )
    
    # Use LLM for additional questions
    if LLM_AVAILABLE and len(questions) < 5:
        try:
            prompt = f"""
            You are a {persona} conducting a timeline-based inspection.
            
            Signal Timeline:
            {json.dumps(timeline, indent=2, default=str)}
            
            Timeline Gaps Identified:
            {json.dumps(gaps, indent=2, default=str)}
            
            Generate 2-3 additional timeline-focused inspection questions that:
            - Challenge timeline consistency
            - Question delays or gaps
            - Probe regulatory action timelines
            - Test documentation completeness
            
            Be direct and regulatory-focused. Format each question as a standalone string.
            """
            
            ai_questions = call_medical_llm(
                prompt,
                f"You are a {persona} with expertise in timeline-based signal inspections.",
                task_type="general",
                max_tokens=600,
                temperature=0.4
            )
            
            # Parse questions
            for line in ai_questions.split("\n"):
                line = line.strip()
                if line and len(line) > 50 and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                    question = line.lstrip("-•1234567890. ")
                    if question and len(question) > 20:
                        questions.append(question)
        except Exception:
            pass
    
    # Fallback questions
    if not questions:
        questions = [
            "Show me the full history of this signal from first case to present.",
            "When was the first case, and what was your detection timeline?",
            "Which regulatory actions occurred and when?",
            "Match every evidence point to a date in your timeline.",
            "Why did you not escalate this signal earlier?"
        ]
    
    return questions[:5]


def _generate_timeline_followup(
    question: str,
    answer: str,
    timeline: Dict[str, Any],
    gaps: List[Dict[str, Any]],
    persona: str
) -> Dict[str, Any]:
    """Generate inspector follow-up for timeline answers."""
    if not LLM_AVAILABLE:
        return {
            "followup": "Your answer requires further clarification on the timeline. Can you provide specific dates and documentation?",
            "escalation_level": 2
        }
    
    prompt = f"""
    You are a {persona} challenging a sponsor's timeline response.
    
    Original Question:
    {question}
    
    Sponsor's Answer:
    {answer}
    
    Signal Timeline:
    {json.dumps(timeline, indent=2, default=str)}
    
    Timeline Gaps:
    {json.dumps(gaps, indent=2, default=str)}
    
    Generate a follow-up question that:
    - Challenges timeline inconsistencies
    - Points out delays or gaps in the answer
    - Requests specific dates and documentation
    - Questions regulatory action timelines
    
    Maintain professional but firm regulatory tone.
    """
    
    try:
        followup_text = call_medical_llm(
            prompt,
            f"You are a {persona} conducting a thorough timeline-based inspection.",
            task_type="general",
            max_tokens=400,
            temperature=0.3
        )
        
        escalation = 2
        if any(keyword in followup_text.lower() for keyword in ["delay", "missing", "incomplete", "gap"]):
            escalation = 3
        if any(keyword in followup_text.lower() for keyword in ["critical", "deficiency", "violation"]):
            escalation = 4
        
        return {
            "followup": followup_text.strip(),
            "escalation_level": escalation
        }
    except Exception:
        return {
            "followup": "Your answer requires further clarification on the timeline.",
            "escalation_level": 2
        }
