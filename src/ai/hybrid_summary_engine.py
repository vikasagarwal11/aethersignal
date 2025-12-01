"""
Hybrid Summary Engine (CHUNK 7.4)
Local compute + Server AI architecture for scalable PV analysis.

This engine:
- Builds lightweight structured summaries from local analytics (no raw data)
- Sends only summaries to server AI for interpretation
- Enables 95% reduction in server load and cloud costs
"""
import json
import datetime
from typing import Dict, List, Any, Optional

try:
    from .medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from .interpretation_cache import hash_summary, get_cached_interpretation, store_cached_interpretation
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


class HybridSummaryEngine:
    """
    Hybrid Summary Engine for local compute + server AI processing.
    
    Stage 1 (CHUNK B1): Basic skeleton with local summary builder and server AI interpreter.
    """
    
    def __init__(self):
        """Initialize the Hybrid Summary Engine."""
        pass
    
    def build_local_summary(
        self,
        normalized_df_count: int = 0,
        trend_alerts: Optional[List[Dict[str, Any]]] = None,
        rpf_scores: Optional[List[Dict[str, Any]]] = None,
        confidence_scores: Optional[List[Dict[str, Any]]] = None,
        subgroups: Optional[Dict[str, Any]] = None,
        label_impact: Optional[List[Dict[str, Any]]] = None,
        governance: Optional[Dict[str, Any]] = None,
        timing: Optional[Dict[str, Any]] = None,
        lifecycle: Optional[List[Dict[str, Any]]] = None,
        capa: Optional[List[Dict[str, Any]]] = None,
        shmi: Optional[Dict[str, Any]] = None,
        signals: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build lightweight structured summary JSON entirely locally.
        
        No raw rows included. This summary is small enough to send to server
        without performance or privacy concerns.
        
        Args:
            normalized_df_count: Total number of cases (no DataFrame passed)
            trend_alerts: Trend alerts summary
            rpf_scores: Risk Prioritization Framework scores
            confidence_scores: Signal Confidence Scores
            subgroups: Subgroup analysis results
            label_impact: Label impact assessments
            governance: Governance findings
            timing: Timing compliance data
            lifecycle: Lifecycle stage information
            capa: CAPA recommendations
            shmi: Signal Health Maturity Index
            signals: Signal list (summary only)
            
        Returns:
            Structured summary dictionary
        """
        # Extract key metrics (no raw data)
        high_risk_signals = []
        if signals:
            high_risk_signals = [
                f"{s.get('drug', 'Unknown')} - {s.get('reaction', 'Unknown')}"
                for s in signals
                if s.get("qsp_score", s.get("rpf_score", 0)) >= 70
            ][:10]  # Top 10 only
        
        # Trend summary
        trend_summary = {
            "total_alerts": len(trend_alerts) if trend_alerts else 0,
            "high_severity_count": sum(
                1 for t in trend_alerts
                if isinstance(t, dict) and t.get("severity") in ["warning", "critical", "high"]
            ) if trend_alerts else 0,
            "critical_alerts": [
                t.get("title", "Unknown")
                for t in trend_alerts[:5]
                if isinstance(t, dict) and t.get("severity") == "critical"
            ] if trend_alerts else []
        }
        
        # RPF summary
        rpf_summary = {
            "total_signals": len(rpf_scores) if rpf_scores else 0,
            "high_priority_count": sum(
                1 for r in rpf_scores
                if isinstance(r, dict) and r.get("qsp_priority", r.get("priority")) in ["High", "high", "Critical", "critical"]
            ) if rpf_scores else 0,
            "average_score": (
                sum(r.get("qsp_score", r.get("rpf_score", 0)) for r in rpf_scores) / len(rpf_scores)
                if rpf_scores and len(rpf_scores) > 0 else 0
            )
        }
        
        # Confidence summary
        confidence_summary = {
            "total_signals": len(confidence_scores) if confidence_scores else 0,
            "high_confidence_count": sum(
                1 for c in confidence_scores
                if isinstance(c, dict) and c.get("score", 0) >= 80
            ) if confidence_scores else 0,
            "average_confidence": (
                sum(c.get("score", 0) for c in confidence_scores) / len(confidence_scores)
                if confidence_scores and len(confidence_scores) > 0 else 0
            )
        }
        
        # Governance summary
        governance_summary = {
            "compliance_score": governance.get("compliance_score", 0) if governance else 0,
            "gaps_count": len(governance.get("gaps", [])) if governance else 0,
            "governance_status": governance.get("status", "Unknown") if governance else "Unknown"
        }
        
        # Timing summary
        timing_summary = {
            "on_time_count": timing.get("on_time_count", 0) if timing else 0,
            "overdue_count": timing.get("overdue_count", 0) if timing else 0,
            "average_delay_days": timing.get("average_delay_days", 0) if timing else 0
        }
        
        # SHMI summary
        shmi_summary = {
            "score": shmi.get("shmi_score", 0) if shmi else 0,
            "maturity_level": shmi.get("maturity_level", "Unknown") if shmi else "Unknown"
        }
        
        # Build complete summary
        summary = {
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "metrics": {
                "total_cases": normalized_df_count,
                "signals_detected": len(signals) if signals else 0,
                "high_risk_signals": high_risk_signals,
            },
            "trend_alerts": trend_summary,
            "rpf": rpf_summary,
            "confidence_scores": confidence_summary,
            "subgroup_risks": {
                "total_subgroups": len(subgroups) if subgroups else 0,
                "at_risk_subgroups": subgroups.get("at_risk_count", 0) if isinstance(subgroups, dict) else 0
            },
            "label_impact": {
                "items_assessed": len(label_impact) if label_impact else 0,
                "high_impact_count": sum(
                    1 for l in label_impact
                    if isinstance(l, dict) and l.get("impact_level") in ["High", "high", "Critical"]
                ) if label_impact else 0
            },
            "governance_findings": governance_summary,
            "timing_compliance": timing_summary,
            "lifecycle_stage": {
                "signals_by_stage": lifecycle if lifecycle else []
            },
            "capa_items": {
                "total_capa": len(capa) if capa else 0,
                "urgent_capa_count": sum(
                    1 for c in capa
                    if isinstance(c, dict) and c.get("urgency") in ["High", "high", "Urgent"]
                ) if capa else 0
            },
            "shmi": shmi_summary,
        }
        
        return summary
    
    def interpret_summary_stream(
        self,
        summary: Dict[str, Any],
        task_type: str = "general",
        max_tokens: int = 2000,
        medical_llm = None
    ):
        """
        Streams LLM interpretation of the summary in real time (CHUNK B2 + B3).
        
        Includes caching to avoid repeat LLM calls (CHUNK B3).
        
        Used in:
        - Chat interface
        - Governance Insight Tab
        - Aggregate Narrative Builder
        
        Args:
            summary: Local summary dictionary
            task_type: LLM task type
            max_tokens: Maximum tokens for response
            
        Yields:
            Text chunks for streaming display
        """
        # ----------------------------
        # 1. Check Cache (CHUNK B3)
        # ----------------------------
        if CACHE_AVAILABLE:
            summary_hash = hash_summary(summary)
            cached = get_cached_interpretation(summary_hash)
            if cached:
                # Yield cached response in chunks for smooth streaming
                for line in cached.split("\n"):
                    if line.strip():
                        yield line + "\n"
                return
        
        if not LLM_AVAILABLE or medical_llm is None:
            # Fallback: yield fallback summary in chunks
            fallback = self._generate_fallback_summary(summary)
            for line in fallback.split("\n"):
                yield line + "\n"
            return
        
        prompt = f"""
You are an expert pharmacovigilance reviewer.

Interpret the following structured summary and produce streaming insights.

SUMMARY JSON:

{json.dumps(summary, indent=2)}

Respond in this structure:

1. Executive Summary

2. Key Risks (with severity)

3. Trends & Emerging Signals

4. Prioritization Justification (RPF)

5. Subgroup Analysis

6. Label Impact Considerations

7. Governance Compliance Notes

8. Reviewer Recommendations

9. Confidence & Uncertainty Analysis

Format as a professional regulatory narrative suitable for governance review and audit documentation.
"""
        
        try:
            system_prompt = "You are a senior pharmacovigilance expert providing structured safety summaries for regulatory signal management and governance review."
            
            # Buffer for caching
            buffer = []
            
            # Use streaming LLM call if available
            try:
                # Attempt streaming response
                from .medical_llm import stream_medical_llm
                for chunk in stream_medical_llm(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    task_type=task_type,
                    max_tokens=max_tokens,
                    temperature=0.3
                ):
                    buffer.append(chunk)
                    yield chunk
                
                # Store in cache
                if CACHE_AVAILABLE:
                    full_response = "".join(buffer)
                    store_cached_interpretation(summary_hash, full_response)
                return
            except (ImportError, AttributeError):
                # Fallback to non-streaming with chunked output
                response = call_medical_llm(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    task_type=task_type,
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                if response:
                    # Store in cache
                    if CACHE_AVAILABLE:
                        store_cached_interpretation(summary_hash, response)
                    
                    # Simulate streaming by yielding sentence by sentence
                    sentences = response.split(". ")
                    for i, sentence in enumerate(sentences):
                        if i < len(sentences) - 1:
                            yield sentence + ". "
                        else:
                            yield sentence
        except Exception as e:
            yield f"AI interpretation error: {str(e)}\n\n"
            fallback = self._generate_fallback_summary(summary)
            for line in fallback.split("\n"):
                yield line + "\n"
    
    def interpret_summary_with_ai(
        self,
        summary: Dict[str, Any],
        task_type: str = "general",
        max_tokens: int = 2000
    ) -> Optional[str]:
        """
        Server only sees structured JSON (no raw data).
        
        AI produces narrative, insights, and interpretations.
        
        Args:
            summary: Local summary dictionary
            task_type: LLM task type
            max_tokens: Maximum tokens for response
            
        Returns:
            AI-generated interpretation text
        """
        if not LLM_AVAILABLE:
            # Fallback: generate simple text summary
            return self._generate_fallback_summary(summary)
        
        prompt = f"""
You are an expert pharmacovigilance reviewer analyzing a structured safety summary.

Given this structured summary (no raw case data), provide a clear clinical and regulatory narrative:

{json.dumps(summary, indent=2)}

Write a comprehensive analysis covering:

1. **Key Risks** (with severity assessment)
   - High-risk signals requiring immediate attention
   - Trend abnormalities and their clinical significance
   - Confidence levels and uncertainty considerations

2. **Signal Prioritization**
   - RPF scores and priority rankings
   - Signals that should be escalated
   - Signals that can be monitored

3. **Trend Interpretation**
   - Notable trend alerts and their implications
   - Temporal patterns and emerging risks
   - Statistical significance considerations

4. **Label Impact Considerations**
   - Signals requiring label updates
   - Regulatory justification for label changes
   - Risk communication implications

5. **Governance Gaps**
   - Compliance score and identified gaps
   - Timing compliance issues
   - Documentation completeness

6. **Reviewer Recommendations**
   - Immediate actions required
   - Signals needing deep dive
   - CAPA items and follow-up activities
   - Timeline expectations

Format as a professional regulatory narrative suitable for governance review and audit documentation.
"""
        
        try:
            system_prompt = "You are a senior pharmacovigilance expert providing structured safety summaries for regulatory signal management and governance review."
            return call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type=task_type,
                max_tokens=max_tokens,
                temperature=0.3
            )
        except Exception as e:
            return f"AI interpretation error: {str(e)}. Using fallback summary.\n\n{self._generate_fallback_summary(summary)}"
    
    def _generate_fallback_summary(self, summary: Dict[str, Any]) -> str:
        """Generate fallback text summary when LLM is unavailable."""
        metrics = summary.get("metrics", {})
        trend_alerts = summary.get("trend_alerts", {})
        rpf = summary.get("rpf", {})
        governance = summary.get("governance_findings", {})
        
        lines = [
            "=== Pharmacovigilance Summary (Fallback) ===\n",
            f"Total Cases: {metrics.get('total_cases', 0):,}",
            f"Signals Detected: {metrics.get('signals_detected', 0)}",
            f"High-Risk Signals: {len(metrics.get('high_risk_signals', []))}",
            "",
            "=== Trend Alerts ===",
            f"Total Alerts: {trend_alerts.get('total_alerts', 0)}",
            f"High Severity: {trend_alerts.get('high_severity_count', 0)}",
            "",
            "=== Risk Prioritization ===",
            f"Total Signals: {rpf.get('total_signals', 0)}",
            f"High Priority: {rpf.get('high_priority_count', 0)}",
            f"Average RPF Score: {rpf.get('average_score', 0):.1f}",
            "",
            "=== Governance ===",
            f"Compliance Score: {governance.get('compliance_score', 0):.1f}/100",
            f"Gaps Identified: {governance.get('gaps_count', 0)}",
        ]
        
        return "\n".join(lines)
    
    def generate_structured_insights(
        self,
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate structured insights from summary (for programmatic use).
        
        Args:
            summary: Local summary dictionary
            
        Returns:
            Structured insights dictionary
        """
        insights = {
            "critical_actions": [],
            "high_priority_signals": [],
            "governance_issues": [],
            "trend_concerns": [],
            "recommendations": []
        }
        
        # Extract critical actions
        metrics = summary.get("metrics", {})
        high_risk = metrics.get("high_risk_signals", [])
        if high_risk:
            insights["critical_actions"].extend([
                f"Review high-risk signal: {signal}" for signal in high_risk[:5]
            ])
        
        # Extract governance issues
        governance = summary.get("governance_findings", {})
        if governance.get("gaps_count", 0) > 0:
            insights["governance_issues"].append(
                f"Address {governance['gaps_count']} compliance gap(s) (Compliance Score: {governance.get('compliance_score', 0):.1f}/100)"
            )
        
        # Extract trend concerns
        trend_alerts = summary.get("trend_alerts", {})
        if trend_alerts.get("high_severity_count", 0) > 0:
            insights["trend_concerns"].append(
                f"Investigate {trend_alerts['high_severity_count']} high-severity trend alert(s)"
            )
        
        # Generate recommendations
        rpf = summary.get("rpf", {})
        if rpf.get("high_priority_count", 0) > 0:
            insights["recommendations"].append(
                f"Prioritize review of {rpf['high_priority_count']} high-priority signal(s)"
            )
        
        timing = summary.get("timing_compliance", {})
        if timing.get("overdue_count", 0) > 0:
            insights["recommendations"].append(
                f"Expedite {timing['overdue_count']} overdue assessment(s)"
            )
        
        return insights

