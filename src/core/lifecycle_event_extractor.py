"""
Lifecycle Event Extractor (CHUNK H1.9 Part 2)
Extracts signal lifecycle events from data, metadata, alerts, and AI inference.
Works in hybrid mode: can run client-side (Pyodide) OR server-side.

This engine populates SignalLifecycleTimeline objects with:
- Direct events from data/metadata
- Inferred events from trend alerts and analytics
- AI-enhanced events with confidence scoring
"""
from datetime import datetime
from typing import Dict, Optional, Any, List
import pandas as pd

try:
    from src.core.timeline_model import SignalLifecycleTimeline, TimelineEvent
    TIMELINE_MODEL_AVAILABLE = True
except ImportError:
    TIMELINE_MODEL_AVAILABLE = False

try:
    from src.ai.trend_alerts import detect_trend_alerts_light, get_trend_alerts
    TREND_ALERTS_AVAILABLE = True
except ImportError:
    TREND_ALERTS_AVAILABLE = False

try:
    from src.ai.signal_summarizer import generate_comprehensive_summary
    SIGNAL_SUMMARIZER_AVAILABLE = True
except ImportError:
    SIGNAL_SUMMARIZER_AVAILABLE = False

try:
    from src.ai.medical_llm import call_medical_llm, LLM_AVAILABLE
    MEDICAL_LLM_AVAILABLE = True
except ImportError:
    MEDICAL_LLM_AVAILABLE = False
    LLM_AVAILABLE = False

try:
    from src.ai.subgroup_engine import analyze_subgroups
    SUBGROUP_ENGINE_AVAILABLE = True
except ImportError:
    SUBGROUP_ENGINE_AVAILABLE = False

try:
    from src.ai.risk_prioritization import RiskPrioritizationEngine
    RPF_AVAILABLE = True
except ImportError:
    RPF_AVAILABLE = False


class LifecycleEventExtractor:
    """
    Extracts lifecycle events from multiple data sources.
    
    Three-layer extraction system:
    1. Layer A - Data-driven: Direct extraction from metadata/FAERS fields
    2. Layer B - Inference-driven: Event inference from trend alerts/analytics
    3. Layer C - AI-enhanced: LLM-based event enhancement and confidence scoring
    """
    
    @staticmethod
    def extract_from_data(
        drug: str,
        reaction: str,
        df_cases: Optional[pd.DataFrame] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mode: str = "hybrid"
    ) -> Optional[SignalLifecycleTimeline]:
        """
        Main entry point for lifecycle event extraction.
        
        Extracts lifecycle events from data, metadata, alerts, and AI inference.
        Works in hybrid mode: can run client-side (Pyodide) OR server-side.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            df_cases: Safety data DataFrame (optional)
            metadata: Additional metadata dictionary (optional)
            mode: Processing mode ("exact", "hybrid", "approx")
            
        Returns:
            SignalLifecycleTimeline object with all extracted events
        """
        if not TIMELINE_MODEL_AVAILABLE:
            return None
        
        metadata = metadata or {}
        
        # Create base timeline
        signal_id = metadata.get("signal_id") or f"{drug}_{reaction}".replace(" ", "_").lower()
        timeline = SignalLifecycleTimeline(
            signal_id=signal_id,
            drug_name=drug,
            reaction_name=reaction
        )
        
        # ---- Layer A: Data-driven extraction ----
        LifecycleEventExtractor._extract_direct_events(timeline, df_cases, metadata)
        
        # ---- Layer B: Inference-driven extraction (local analytics) ----
        if mode in ["exact", "hybrid"]:
            LifecycleEventExtractor._extract_inferred_events(timeline, df_cases, drug, reaction)
        
        # ---- Layer C: AI enhancement (optional server-side) ----
        if mode == "exact" and MEDICAL_LLM_AVAILABLE and LLM_AVAILABLE:
            LifecycleEventExtractor._enhance_with_ai(timeline)
        
        # Update timestamp
        timeline.update_timestamp()
        
        return timeline
    
    # ---------------------------------------------------------
    # Layer A — Direct extraction (pure data-driven)
    # ---------------------------------------------------------
    
    @staticmethod
    def _extract_direct_events(
        timeline: SignalLifecycleTimeline,
        df_cases: Optional[pd.DataFrame],
        metadata: Dict[str, Any]
    ):
        """
        Directly detect triage, assessment, evaluation, decision events.
        Works from FAERS fields or user-provided metadata.
        """
        # 1. TRIAGE EVENT
        first_received = metadata.get("first_received") or metadata.get("first_case_date")
        if first_received:
            timeline.triage_event = TimelineEvent(
                name="Signal Triage",
                timestamp=LifecycleEventExtractor._to_dt(first_received),
                source=metadata.get("source", "metadata"),
                details={
                    "note": "First case received",
                    "case_count": metadata.get("initial_case_count", 0)
                },
                confidence=1.0,
                sla_target_days=30  # Typical triage SLA
            )
        elif df_cases is not None:
            # Try to infer from case dates
            date_col = LifecycleEventExtractor._find_date_column(df_cases)
            if date_col:
                first_date = pd.to_datetime(df_cases[date_col], errors="coerce").min()
                if pd.notna(first_date):
                    timeline.triage_event = TimelineEvent(
                        name="Signal Triage (Inferred)",
                        timestamp=first_date.to_pydatetime(),
                        source="case_data",
                        details={"note": "Inferred from first case date"},
                        confidence=0.8,
                        sla_target_days=30
                    )
        
        # 2. ASSESSMENT EVENT
        signal_detected = metadata.get("signal_detected_on") or metadata.get("detection_date")
        if signal_detected:
            timeline.assessment_event = TimelineEvent(
                name="Signal Assessment",
                timestamp=LifecycleEventExtractor._to_dt(signal_detected),
                source=metadata.get("source", "metadata"),
                details={
                    "note": "Signal detected date",
                    "detection_method": metadata.get("detection_method", "unknown")
                },
                confidence=1.0,
                sla_target_days=90  # Typical assessment SLA
            )
        
        # 3. EVALUATION EVENT — if FAERS or internal evaluations exist
        eval_date = metadata.get("evaluation_date") or metadata.get("eval_date")
        if eval_date:
            timeline.evaluation_event = TimelineEvent(
                name="Signal Evaluation",
                timestamp=LifecycleEventExtractor._to_dt(eval_date),
                source=metadata.get("source", "metadata"),
                details={"note": "Evaluation activity recorded"},
                confidence=1.0,
                sla_target_days=120  # Typical evaluation SLA
            )
        elif df_cases is not None:
            # Try to find evaluation-related columns
            eval_col = LifecycleEventExtractor._find_date_column(df_cases, keywords=["eval", "review", "assess"])
            if eval_col:
                eval_dates = pd.to_datetime(df_cases[eval_col], errors="coerce").dropna()
                if len(eval_dates) > 0:
                    timeline.evaluation_event = TimelineEvent(
                        name="Signal Evaluation (Inferred)",
                        timestamp=eval_dates.min().to_pydatetime(),
                        source="case_data",
                        details={"note": "Inferred from evaluation dates"},
                        confidence=0.7,
                        sla_target_days=120
                    )
        
        # 4. DECISION EVENT
        decision_date = metadata.get("decision_date") or metadata.get("decision_on")
        if decision_date:
            timeline.decision_event = TimelineEvent(
                name="Signal Decision",
                timestamp=LifecycleEventExtractor._to_dt(decision_date),
                source=metadata.get("source", "metadata"),
                details={
                    "note": "Signal decision recorded",
                    "decision": metadata.get("decision", "unknown"),
                    "status": metadata.get("status", "unknown")
                },
                confidence=1.0
            )
        
        # 5. CAPA EVENT
        capa_date = metadata.get("capa_date") or metadata.get("capa_initiated")
        if capa_date:
            timeline.capa_event = TimelineEvent(
                name="CAPA Initiated",
                timestamp=LifecycleEventExtractor._to_dt(capa_date),
                source=metadata.get("source", "metadata"),
                details={
                    "note": "CAPA actions initiated",
                    "capa_type": metadata.get("capa_type", "unknown")
                },
                confidence=1.0
            )
        
        # 6. LABEL EVENT
        label_date = metadata.get("label_update_date") or metadata.get("label_changed")
        if label_date:
            timeline.label_event = TimelineEvent(
                name="Label Update",
                timestamp=LifecycleEventExtractor._to_dt(label_date),
                source=metadata.get("source", "metadata"),
                details={
                    "note": "Label update completed",
                    "label_section": metadata.get("label_section", "unknown")
                },
                confidence=1.0
            )
        
        # 7. CLOSE EVENT
        close_date = metadata.get("close_date") or metadata.get("closed_on")
        if close_date:
            timeline.close_event = TimelineEvent(
                name="Signal Closed",
                timestamp=LifecycleEventExtractor._to_dt(close_date),
                source=metadata.get("source", "metadata"),
                details={
                    "note": "Signal closed",
                    "close_reason": metadata.get("close_reason", "unknown")
                },
                confidence=1.0
            )
    
    # ---------------------------------------------------------
    # Layer B — Inference-driven extraction (local analytics)
    # ---------------------------------------------------------
    
    @staticmethod
    def _extract_inferred_events(
        timeline: SignalLifecycleTimeline,
        df_cases: Optional[pd.DataFrame],
        drug: str,
        reaction: str
    ):
        """
        Use trend alerts and subgroup patterns to infer missing lifecycle steps.
        Runs fully client-side in hybrid mode.
        """
        if df_cases is None or df_cases.empty:
            return
        
        # Extract trend alerts
        if TREND_ALERTS_AVAILABLE:
            try:
                # Try light mode trend alerts
                alerts = detect_trend_alerts_light(df_cases)
                
                # Filter alerts for this specific drug-reaction pair if possible
                relevant_alerts = []
                if isinstance(alerts, list):
                    for alert in alerts:
                        if hasattr(alert, 'drug') and hasattr(alert, 'reaction'):
                            if alert.drug == drug and alert.reaction == reaction:
                                relevant_alerts.append(alert)
                        elif isinstance(alert, dict):
                            if alert.get("drug") == drug and alert.get("reaction") == reaction:
                                relevant_alerts.append(alert)
                
                # Store trend alerts
                timeline.trend_alerts = [
                    {
                        "type": getattr(a, "type", a.get("type", "unknown")),
                        "summary": getattr(a, "summary", a.get("summary", "")),
                        "severity": getattr(a, "severity", a.get("severity", "medium")),
                        "timestamp": getattr(a, "timestamp", a.get("timestamp", None))
                    }
                    if hasattr(a, "summary") or isinstance(a, dict)
                    else str(a)
                    for a in (relevant_alerts if relevant_alerts else alerts[:5])
                ]
                
                # Emerging risks → implies evaluation event if missing
                if relevant_alerts and not timeline.evaluation_event:
                    high_severity = [
                        a for a in relevant_alerts
                        if (hasattr(a, "severity") and a.severity in ["high", "critical"]) or
                           (isinstance(a, dict) and a.get("severity") in ["high", "critical"])
                    ]
                    if high_severity:
                        timeline.evaluation_event = TimelineEvent(
                            name="Signal Evaluation (Inferred from Trend Alerts)",
                            timestamp=datetime.now(),
                            source="trend_alerts",
                            details={
                                "auto_inferred": True,
                                "trigger": "High-severity trend alerts detected",
                                "alert_count": len(high_severity)
                            },
                            confidence=0.7
                        )
                
            except Exception:
                # Fail gracefully if trend alerts unavailable
                pass
        
        # Extract subgroup findings
        try:
            subgroup_findings = LifecycleEventExtractor._infer_subgroup_findings(df_cases, drug, reaction)
            if subgroup_findings:
                timeline.subgroup_findings = subgroup_findings
                
                # Subgroup patterns often imply evaluation in real PV practice
                if subgroup_findings and not timeline.evaluation_event:
                    timeline.evaluation_event = TimelineEvent(
                        name="Signal Evaluation (Inferred from Subgroup Analysis)",
                        timestamp=datetime.now(),
                        source="subgroup_analysis",
                        details={
                            "auto_inferred": True,
                            "trigger": "Subgroup patterns detected",
                            "subgroup_count": len(subgroup_findings)
                        },
                        confidence=0.6
                    )
        except Exception:
            pass
        
        # Extract clustering findings (if available)
        try:
            clustering_findings = LifecycleEventExtractor._infer_clustering_findings(df_cases)
            if clustering_findings:
                timeline.clustering_findings = clustering_findings
        except Exception:
            pass
    
    @staticmethod
    def _infer_subgroup_findings(
        df_cases: pd.DataFrame,
        drug: str,
        reaction: str
    ) -> List[Dict[str, Any]]:
        """Infer subgroup findings from case data."""
        results = []
        
        try:
            # Age-based subgroups
            age_col = LifecycleEventExtractor._find_column(df_cases, ["age", "age_yrs", "patient_age"])
            if age_col:
                ages = pd.to_numeric(df_cases[age_col], errors="coerce").dropna()
                if len(ages) > 0:
                    seniors = ages[ages >= 65]
                    if len(seniors) > 5:
                        results.append({
                            "subgroup": "Elderly (≥65 years)",
                            "count": int(len(seniors)),
                            "percentage": round((len(seniors) / len(ages)) * 100, 1),
                            "note": "High reporting in elderly subgroup"
                        })
                    
                    pediatric = ages[ages < 18]
                    if len(pediatric) > 3:
                        results.append({
                            "subgroup": "Pediatric (<18 years)",
                            "count": int(len(pediatric)),
                            "percentage": round((len(pediatric) / len(ages)) * 100, 1),
                            "note": "Pediatric cases detected"
                        })
            
            # Sex-based subgroups
            sex_col = LifecycleEventExtractor._find_column(df_cases, ["sex", "gender", "patient_sex"])
            if sex_col:
                sex_counts = df_cases[sex_col].value_counts()
                if len(sex_counts) > 0:
                    dominant_sex = sex_counts.index[0]
                    dominant_count = int(sex_counts.iloc[0])
                    total = len(df_cases[df_cases[sex_col].notna()])
                    if total > 0:
                        percentage = round((dominant_count / total) * 100, 1)
                        if percentage > 60:  # Significant imbalance
                            results.append({
                                "subgroup": f"Sex: {dominant_sex}",
                                "count": dominant_count,
                                "percentage": percentage,
                                "note": f"Dominant reporting in {dominant_sex} patients"
                            })
        except Exception:
            pass
        
        return results
    
    @staticmethod
    def _infer_clustering_findings(df_cases: pd.DataFrame) -> List[Dict[str, Any]]:
        """Infer clustering findings from case data."""
        results = []
        
        try:
            # Simple clustering inference based on case patterns
            # More sophisticated clustering would use NarrativeClusteringEngine
            if len(df_cases) > 10:
                # Group by outcome if available
                outcome_col = LifecycleEventExtractor._find_column(df_cases, ["outcome", "outc_cod", "seriousness"])
                if outcome_col:
                    outcome_counts = df_cases[outcome_col].value_counts()
                    if len(outcome_counts) > 1:
                        results.append({
                            "cluster_type": "outcome_pattern",
                            "patterns": outcome_counts.head(3).to_dict(),
                            "note": "Multiple outcome patterns detected"
                        })
        except Exception:
            pass
        
        return results
    
    # ---------------------------------------------------------
    # Layer C — AI Enhancement (optional server-side)
    # ---------------------------------------------------------
    
    @staticmethod
    def _enhance_with_ai(timeline: SignalLifecycleTimeline):
        """
        Ask the LLM to enhance gaps, estimate timestamps,
        and produce confidence scoring.
        
        Only runs in EXACT mode when LLM is available.
        """
        if not MEDICAL_LLM_AVAILABLE or not LLM_AVAILABLE:
            return
        
        try:
            timeline_dict = timeline.as_dict()
            
            system_prompt = """You are a pharmacovigilance signal governance AI assistant specializing in signal lifecycle management.
You analyze signal timelines to fill gaps, estimate timestamps, assign confidence scores, and identify regulatory compliance issues.
Always return valid JSON responses."""
            
            prompt = f"""
Given this signal lifecycle timeline:
{timeline_dict}

Analyze the timeline and:
1. Fill in missing lifecycle events if they can be reasonably inferred
2. Estimate timestamps for inferred events based on event sequence
3. Assign confidence scores (0.0-1.0) for auto-inferred events
4. Suggest SLA target days for each event based on regulatory guidelines (FDA, EMA, ICH GVP)
5. Identify any timeline gaps or inconsistencies

Return your analysis as JSON with this structure:
{{
    "events": {{
        "triage": {{"name": "...", "timestamp": "...", "confidence": 0.8, "sla_target_days": 30, "details": {{}}}},
        "assessment": {{"name": "...", "timestamp": "...", "confidence": 0.8, "sla_target_days": 90, "details": {{}}}},
        "evaluation": {{"name": "...", "timestamp": "...", "confidence": 0.8, "sla_target_days": 120, "details": {{}}}},
        "decision": {{"name": "...", "timestamp": "...", "confidence": 0.8, "details": {{}}}}
    }},
    "gaps": ["missing_event1", "missing_event2"],
    "recommendations": ["recommendation1", "recommendation2"]
}}

Return ONLY valid JSON, no other text or markdown formatting.
"""
            
            response = call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=1000
            )
            
            if not response:
                return
            
            # Try to parse JSON response
            import json
            if isinstance(response, str):
                try:
                    enhanced = json.loads(response)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code blocks
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
                    if json_match:
                        enhanced = json.loads(json_match.group(1))
                    else:
                        return
            elif isinstance(response, dict):
                enhanced = response
            else:
                return
            
            # Apply LLM enhancements (only fill gaps, don't overwrite existing events)
            events = enhanced.get("events", {})
            
            if "triage" in events and not timeline.triage_event:
                event_data = events["triage"]
                timeline.triage_event = TimelineEvent(
                    name=event_data.get("name", "Signal Triage"),
                    timestamp=LifecycleEventExtractor._to_dt(event_data.get("timestamp")),
                    source="LLM-enhanced",
                    details=event_data.get("details", {}),
                    confidence=event_data.get("confidence", 0.5),
                    sla_target_days=event_data.get("sla_target_days")
                )
            
            if "assessment" in events and not timeline.assessment_event:
                event_data = events["assessment"]
                timeline.assessment_event = TimelineEvent(
                    name=event_data.get("name", "Signal Assessment"),
                    timestamp=LifecycleEventExtractor._to_dt(event_data.get("timestamp")),
                    source="LLM-enhanced",
                    details=event_data.get("details", {}),
                    confidence=event_data.get("confidence", 0.5),
                    sla_target_days=event_data.get("sla_target_days")
                )
            
            if "evaluation" in events and not timeline.evaluation_event:
                event_data = events["evaluation"]
                timeline.evaluation_event = TimelineEvent(
                    name=event_data.get("name", "Signal Evaluation"),
                    timestamp=LifecycleEventExtractor._to_dt(event_data.get("timestamp")),
                    source="LLM-enhanced",
                    details=event_data.get("details", {}),
                    confidence=event_data.get("confidence", 0.5),
                    sla_target_days=event_data.get("sla_target_days")
                )
            
            if "decision" in events and not timeline.decision_event:
                event_data = events["decision"]
                timeline.decision_event = TimelineEvent(
                    name=event_data.get("name", "Signal Decision"),
                    timestamp=LifecycleEventExtractor._to_dt(event_data.get("timestamp")),
                    source="LLM-enhanced",
                    details=event_data.get("details", {}),
                    confidence=event_data.get("confidence", 0.5),
                    sla_target_days=event_data.get("sla_target_days")
                )
            
            # Store LLM recommendations
            if "recommendations" in enhanced:
                timeline.governance_flags.append({
                    "type": "llm_recommendations",
                    "recommendations": enhanced["recommendations"]
                })
        
        except Exception:
            # Fail gracefully - AI enhancement is optional
            pass
    
    # ---------------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------------
    
    @staticmethod
    def _to_dt(val: Optional[Any]) -> Optional[datetime]:
        """Convert value to datetime object."""
        if not val:
            return None
        
        if isinstance(val, datetime):
            return val
        
        if isinstance(val, pd.Timestamp):
            return val.to_pydatetime()
        
        try:
            # Try ISO format
            if isinstance(val, str):
                # Handle ISO format with timezone
                val = val.replace("Z", "+00:00")
                return datetime.fromisoformat(val)
        except Exception:
            pass
        
        try:
            # Try pandas to_datetime
            dt = pd.to_datetime(val, errors="coerce")
            if pd.notna(dt):
                return dt.to_pydatetime()
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def _find_date_column(df: pd.DataFrame, keywords: Optional[List[str]] = None) -> Optional[str]:
        """Find date column in DataFrame."""
        if df is None or df.empty:
            return None
        
        keywords = keywords or ["date", "dt", "time", "received", "report"]
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in keywords):
                # Check if column looks like dates
                sample = df[col].dropna().head(5)
                if len(sample) > 0:
                    try:
                        pd.to_datetime(sample, errors="raise")
                        return col
                    except Exception:
                        continue
        
        return None
    
    @staticmethod
    def _find_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
        """Find column in DataFrame by keywords."""
        if df is None or df.empty:
            return None
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword.lower() in col_lower for keyword in keywords):
                return col
        
        return None

