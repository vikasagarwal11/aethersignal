"""
Unified Governance Dashboard (CHUNK A3)
Complete governance view combining heatmap, checklist, metrics, signal file, and AI interpretation.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

try:
    from src.ai.heatmap_builder import build_heatmap_levels
    from src.ai.hybrid_summary_engine import HybridSummaryEngine
    from src.ui.oversight_metrics import render_oversight_metrics
    from src.ui.heatmap_renderer import render_enterprise_heatmap
    from src.ai.lifecycle_inference import infer_lifecycle_stage
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False


def render_unified_governance_dashboard(
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    rpf_scores: Optional[List[Dict[str, Any]]] = None,
    confidence_scores: Optional[List[Dict[str, Any]]] = None,
    label_impact_scores: Optional[List[Dict[str, Any]]] = None,
    subgroup_scores: Optional[List[Dict[str, Any]]] = None,
    shmi_score: Optional[Dict[str, Any]] = None,
    governance_gaps: Optional[Dict[str, Any]] = None,
    timing_deviations: Optional[Dict[str, Any]] = None,
    lifecycle_stage: Optional[Dict[str, Any]] = None,
    capa_findings: Optional[List[Dict[str, Any]]] = None,
    summary: Optional[Dict[str, Any]] = None,
    signals: Optional[List[Dict[str, Any]]] = None,
    medical_llm = None
) -> None:
    """
    Render unified governance dashboard with all integrated components (CHUNK A3).
    
    Args:
        trend_alerts: List of trend alert dictionaries
        rpf_scores: Risk Prioritization Framework scores
        confidence_scores: Signal Confidence Scores
        label_impact_scores: Label impact assessments
        subgroup_scores: Subgroup analysis results
        shmi_score: Signal Health Maturity Index
        governance_gaps: Governance gap findings
        timing_deviations: Timing compliance deviations
        lifecycle_stage: Lifecycle stage information
        capa_findings: CAPA findings
        summary: Hybrid summary dictionary
        signals: List of signal dictionaries
        medical_llm: LLM instance for AI interpretation
    """
    if not COMPONENTS_AVAILABLE:
        st.error("Governance dashboard components not available. Please install required dependencies.")
        return
    
    st.header("📊 Unified Governance Dashboard")
    
    # Infer lifecycle stage if not provided (CHUNK B4)
    if lifecycle_stage is None or not isinstance(lifecycle_stage, dict):
        lifecycle_stage = infer_lifecycle_stage(
            trend_alerts=trend_alerts,
            rpf_scores=rpf_scores[0] if rpf_scores else {},
            confidence_scores=confidence_scores[0] if confidence_scores else {},
            label_impact_scores=label_impact_scores[0] if label_impact_scores else {},
            capa_findings={"open_major": len([c for c in capa_findings if isinstance(c, dict) and c.get("urgency") in ["High", "high"]])} if capa_findings else {},
            governance_gaps=governance_gaps or {},
            summary=summary,
            medical_llm=medical_llm
        )
    
    # Build hybrid summary if not provided
    if summary is None:
        hybrid_engine = HybridSummaryEngine()
        summary = hybrid_engine.build_local_summary(
            normalized_df_count=0,
            trend_alerts=trend_alerts,
            rpf_scores=rpf_scores,
            confidence_scores=confidence_scores,
            subgroups={"at_risk_count": len(subgroup_scores)} if subgroup_scores else {},
            label_impact=label_impact_scores,
            governance=governance_gaps,
            timing=timing_deviations,
            lifecycle=[],
            capa=capa_findings,
            shmi=shmi_score,
            signals=signals
        )
    
    # Tabs
    tabs = st.tabs([
        "🔥 Overview Heatmap",
        "✅ Compliance Checklist",
        "📋 Signal File",
        "📈 Oversight Metrics",
        "👥 Reviewer Workload",
        "🧠 AI Interpretation",
        "📄 Signal File Builder"
    ])
    
    # ----------------------
    # 1. OVERVIEW TAB (Heatmap)
    # ----------------------
    with tabs[0]:
        st.subheader("🔥 Signal Governance Overview")
        
        if signals:
            # Build heatmap for each signal
            heatmap_rows = []
            for signal in signals[:20]:  # Top 20
                drug = signal.get("drug", "Unknown")
                reaction = signal.get("reaction", signal.get("event", "Unknown"))
                signal_name = f"{drug} - {reaction}"
                
                levels_df = build_heatmap_levels(
                    trend_alerts=[a for a in (trend_alerts or []) if isinstance(a, dict) and 
                                 (drug.lower() in str(a.get("drug", "")).lower() or
                                  reaction.lower() in str(a.get("reaction", "")).lower())],
                    rpf_scores=signal,
                    confidence_scores=signal.get("confidence_score", {}),
                    label_impact_scores=signal.get("label_impact", {}),
                    subgroup_scores=signal.get("subgroups", {}),
                    shmi_score=shmi_score or {},
                    governance_gaps=governance_gaps or {},
                    timing_deviations=signal.get("timeline_status", {}),
                    lifecycle_stage=lifecycle_stage,
                    capa_findings={"open_major": 1 if signal.get("capa_required") else 0},
                    signal_name=signal_name
                )
                heatmap_rows.append(levels_df)
            
            if heatmap_rows:
                import pandas as pd
                combined_heatmap = pd.concat(heatmap_rows, ignore_index=False)
                render_enterprise_heatmap(combined_heatmap, title="Pre-Inspection Risk & Compliance Heatmap")
        else:
            st.info("No signals available for heatmap. Generate signals first.")
        
        st.markdown("### 📌 Summary")
        st.write(f"**Signal Stage:** {lifecycle_stage.get('stage', 'Unknown')}")
        if isinstance(lifecycle_stage, dict):
            st.caption(f"Evidence: {lifecycle_stage.get('evidence', 'N/A')}")
        
        if confidence_scores and len(confidence_scores) > 0:
            avg_confidence = sum(c.get("score", 0) for c in confidence_scores if isinstance(c, dict)) / len(confidence_scores)
            st.write(f"**Overall Confidence:** {avg_confidence:.2f}")
    
    # ----------------------
    # 2. COMPLIANCE CHECKLIST TAB
    # ----------------------
    with tabs[1]:
        try:
            from src.ui.compliance_checklist_panel import render_compliance_checklist
            render_compliance_checklist(governance_gaps, timing_deviations)
        except ImportError:
            st.subheader("✅ Compliance Checklist")
            st.info("Compliance checklist panel not yet implemented. Coming in future update.")
            
            # Simple placeholder
            if governance_gaps:
                gaps_count = governance_gaps.get("gaps_count", 0) or governance_gaps.get("major_gaps", 0)
                st.metric("Identified Gaps", gaps_count)
    
    # ----------------------
    # 3. SIGNAL FILE TAB
    # ----------------------
    with tabs[2]:
        try:
            from src.ui.signal_file_panel import render_signal_file
            render_signal_file(
                trend_alerts,
                rpf_scores,
                label_impact_scores,
                shmi_score,
                lifecycle_stage,
                capa_findings
            )
        except ImportError:
            st.subheader("📋 Signal File")
            st.info("Signal file panel not yet implemented. Coming in future update.")
    
    # ----------------------
    # 4. OVERSIGHT METRICS TAB
    # ----------------------
    with tabs[3]:
        render_oversight_metrics(
            trend_alerts=trend_alerts,
            governance_gaps=governance_gaps,
            capa_findings={"open_major": len([c for c in capa_findings if isinstance(c, dict) and c.get("urgency") in ["High", "high"]]) if capa_findings else 0,
                          "open_minor": len([c for c in capa_findings if isinstance(c, dict) and c.get("urgency") not in ["High", "high"]]) if capa_findings else 0,
                          "total_capa": len(capa_findings) if capa_findings else 0} if capa_findings else {},
            timing_deviations=timing_deviations,
            lifecycle_stage=lifecycle_stage
        )
    
    # ----------------------
    # 5. REVIEWER WORKLOAD TAB (CHUNK B6)
    # ----------------------
    with tabs[4]:
        try:
            from src.ui.reviewer_workload_panel import render_reviewer_workload_panel
            
            # Get reviewers from governance engine
            reviewers_df = None
            try:
                from src.ai.governance_engine import GovernanceEngine
                governance_engine = GovernanceEngine()
                reviewer_profiles = governance_engine.load_reviewer_profiles()
                
                # Convert to DataFrame
                if reviewer_profiles:
                    reviewers_data = []
                    for profile in reviewer_profiles:
                        reviewers_data.append({
                            "name": profile.get("name", "Unknown"),
                            "expertise": ", ".join(profile.get("expertise", [])) if isinstance(profile.get("expertise"), list) else str(profile.get("expertise", "General")),
                            "open_reviews": profile.get("current_workload", 0),
                            "max_workload": profile.get("max_workload", 10)
                        })
                    reviewers_df = pd.DataFrame(reviewers_data)
            except Exception:
                pass
            
            # Fallback to placeholder if needed
            if reviewers_df is None or reviewers_df.empty:
                reviewers_df = pd.DataFrame([
                    {"name": "Dr. Smith", "expertise": "Oncology", "open_reviews": 0, "max_workload": 10},
                    {"name": "Dr. Johnson", "expertise": "Cardiovascular", "open_reviews": 0, "max_workload": 10},
                    {"name": "Dr. Williams", "expertise": "Dermatology", "open_reviews": 0, "max_workload": 10}
                ])
            
            render_reviewer_workload_panel(
                reviewers_df=reviewers_df,
                signals=signals or [],
                forecast_days=30
            )
        except ImportError:
            st.info("Reviewer workload panel not yet available. Coming in future update.")
        except Exception as e:
                    st.error(f"Error loading reviewer workload: {str(e)}")
    # Note: This can be shown when a signal is selected
    if signals and len(signals) > 0:
        st.markdown("---")
        st.markdown("### 🧠 Recommended Reviewer (Expertise Matching)")
        
        try:
            from src.ai.reviewer_expertise_engine import get_recommended_reviewers, rank_reviewers_by_expertise
            from src.ai.governance_engine import GovernanceEngine
            
            # Select first signal for demonstration (or allow selection)
            selected_signal = signals[0]
            
            governance_engine = GovernanceEngine()
            reviewers = governance_engine.load_reviewer_profiles()
            
            # Get recommended reviewers
            recommended = get_recommended_reviewers(selected_signal, reviewers, top_n=5)
            
            if recommended:
                st.info(f"Top recommended reviewers for: {selected_signal.get('drug', 'Unknown')} → {selected_signal.get('reaction', 'Unknown')}")
                
                # Show rankings
                rankings_df = rank_reviewers_by_expertise(selected_signal, reviewers)
                if not rankings_df.empty:
                    st.dataframe(rankings_df.head(5), use_container_width=True, hide_index=True)
            else:
                st.info("No reviewers available for expertise matching.")
        except ImportError:
            st.info("Reviewer expertise matching not yet available.")
        except Exception as e:
            st.caption(f"Expertise matching unavailable: {str(e)}")
    
    # ----------------------
    # 6. AI INTERPRETATION TAB
    # ----------------------
    with tabs[5]:
        try:
            from src.ui.reviewer_workload_panel import render_reviewer_workload_panel
            
            # Get reviewers from governance engine
            reviewers_df = None
            try:
                from src.ai.governance_engine import GovernanceEngine
                governance_engine = GovernanceEngine()
                reviewer_profiles = governance_engine.load_reviewer_profiles()
                
                # Convert to DataFrame
                if reviewer_profiles:
                    import pandas as pd
                    reviewers_data = []
                    for profile in reviewer_profiles:
                        reviewers_data.append({
                            "name": profile.get("name", "Unknown"),
                            "expertise": ", ".join(profile.get("expertise", [])) if isinstance(profile.get("expertise"), list) else str(profile.get("expertise", "General")),
                            "open_reviews": profile.get("current_workload", 0),
                            "max_workload": profile.get("max_workload", 10)
                        })
                    reviewers_df = pd.DataFrame(reviewers_data)
            except Exception:
                pass
            
            # Fallback to placeholder if needed
            if reviewers_df is None or reviewers_df.empty:
                import pandas as pd
                reviewers_df = pd.DataFrame([
                    {"name": "Dr. Smith", "expertise": "Oncology", "open_reviews": 0, "max_workload": 10},
                    {"name": "Dr. Johnson", "expertise": "Cardiovascular", "open_reviews": 0, "max_workload": 10},
                    {"name": "Dr. Williams", "expertise": "Dermatology", "open_reviews": 0, "max_workload": 10}
                ])
            
            render_reviewer_workload_panel(
                reviewers_df=reviewers_df,
                signals=signals or [],
                forecast_days=30
            )
        except ImportError:
            st.info("Reviewer workload panel not yet available. Coming in future update.")
        except Exception as e:
            st.error(f"Error loading reviewer workload: {str(e)}")
    
    # ----------------------
    # 6. AI INTERPRETATION TAB
    # ----------------------
    with tabs[5]:
        st.subheader("🧠 AI Interpretation")
        
        hybrid_engine = HybridSummaryEngine()
        
        # Check if we have a cached interpretation first (CHUNK B3)
        try:
            from src.ai.interpretation_cache import hash_summary, get_cached_interpretation
            summary_hash = hash_summary(summary)
            cached = get_cached_interpretation(summary_hash)
            
            if cached:
                st.success("✅ Using cached interpretation (instant load)")
                st.markdown(cached)
            else:
                with st.spinner("Generating AI interpretation (this may take a moment)..."):
                    # Use streaming interpretation (CHUNK B2 + B3)
                    interpretation_container = st.empty()
                    full_text = ""
                    
                    for chunk in hybrid_engine.interpret_summary_stream(summary, medical_llm=medical_llm):
                        full_text += chunk
                        interpretation_container.markdown(full_text)
                    
                    if not full_text:
                        st.info("AI interpretation unavailable. Using fallback summary.")
                        st.markdown(hybrid_engine._generate_fallback_summary(summary))
        except ImportError:
            # Fallback without caching
            with st.spinner("Generating AI interpretation..."):
                interpretation_container = st.empty()
                full_text = ""
                
                for chunk in hybrid_engine.interpret_summary_stream(summary, medical_llm=medical_llm):
                    full_text += chunk
                    interpretation_container.markdown(full_text)
                
                if not full_text:
                    st.info("AI interpretation unavailable. Using fallback summary.")
                    st.markdown(hybrid_engine._generate_fallback_summary(summary))

