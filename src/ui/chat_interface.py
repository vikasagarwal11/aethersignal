"""
Chat Interface Component for AetherSignal.
Provides ChatGPT-style conversational UI with message bubbles, streaming, and multi-turn support.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid


# -----------------------------------------------------------
# CHUNK 6.5: Enhanced Message Rendering
# -----------------------------------------------------------

def render_message(message: Dict):
    """
    Render a single chat message (CHUNK 6.5 - Simple version).
    Compatible with existing _render_message_bubble but simpler API.
    """
    role = message.get("role", "assistant")
    content = message.get("content", "")
    
    if role == "user":
        st.markdown(
            f"""
            <div class="chat-bubble user-bubble">
                <strong>You</strong><br>{content}
            </div>
            """,
            unsafe_allow_html=True
        )
    elif role == "assistant":
        st.markdown(
            f"""
            <div class="chat-bubble assistant-bubble">
                <strong>AetherSignal</strong><br>{content}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="chat-bubble system-bubble">
                {content}
            </div>
            """,
            unsafe_allow_html=True
        )


def show_typing_indicator():
    """
    Show typing indicator (CHUNK 6.5).
    Returns placeholder for dynamic updates.
    """
    return st.markdown(
        """
        <div class="chat-typing-indicator">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
        """,
        unsafe_allow_html=True
    )


# -----------------------------------------------------------
# CHUNK 6.6: Quick Insights Rendering
# -----------------------------------------------------------

def render_quick_insights(quick_results: Dict[str, Any]):
    """
    Render quick insights from follow-up analysis (CHUNK 6.6/6.8).
    Displays structured data as inline chips, metrics, and charts with enterprise styling.
    """
    if not quick_results:
        return
    
    # CHUNK 6.8: Wrap in styled quick insights block
    st.markdown('<div class="quick-insights-block">', unsafe_allow_html=True)
    
    st.markdown("### 🔍 Quick Insights")
    
    # Case count metric
    if "case_count" in quick_results:
        count = quick_results["case_count"]
        st.metric("Filtered Case Count", f"{count:,}")
    
    # Reaction summary with chips
    if "reaction_summary" in quick_results:
        reactions = quick_results["reaction_summary"]
        if reactions:
            st.markdown("**Top Reactions:**")
            # Show as styled chips (CHUNK 6.8)
            chip_html = ""
            for k, v in list(reactions.items())[:5]:
                chip_html += f'<span class="quick-insights-chip">{k}: {v:,}</span>'
            st.markdown(chip_html, unsafe_allow_html=True)
    
    # Gender breakdown
    if "gender_breakdown" in quick_results:
        gender = quick_results["gender_breakdown"]
        if gender:
            st.markdown("**Gender Distribution:**")
            gender_text = ", ".join([f"{k}: {v:,}" for k, v in list(gender.items())[:3]])
            st.caption(gender_text)
    
    # Age breakdown
    if "age_breakdown" in quick_results:
        age = quick_results["age_breakdown"]
        if age:
            st.markdown("**Age Group Distribution:**")
            age_text = ", ".join([f"{k}: {v:,}" for k, v in list(age.items())[:4]])
            st.caption(age_text)
    
    # Trend chart
    if "trend" in quick_results:
        trend = quick_results["trend"]
        if trend and len(trend) > 1:
            st.markdown("**12-Month Trend:**")
            # Convert to DataFrame for line chart
            import pandas as pd
            trend_df = pd.DataFrame(list(trend.items()), columns=["Month", "Cases"])
            trend_df = trend_df.set_index("Month")
            st.line_chart(trend_df)
    
    # Year comparison with chips
    if "compare" in quick_results:
        compare = quick_results["compare"]
        if compare:
            st.markdown("**Year Comparison:**")
            # Show as styled chips (CHUNK 6.8)
            chip_html = ""
            for year, count in sorted(compare.items()):
                chip_html += f'<span class="quick-insights-chip">{year}: {count:,}</span>'
            st.markdown(chip_html, unsafe_allow_html=True)
    
    # Close quick insights block
    st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------------------------------------
# Chat Message Rendering
# -----------------------------------------------------------

def _render_message_bubble(message: Dict, key: str):
    """Render a single chat message bubble."""
    role = message.get("role", "assistant")
    content = message.get("content", "")
    timestamp = message.get("timestamp")
    status = message.get("status", "complete")
    metadata = message.get("metadata", {})

    bubble_class = "chat-bubble-user" if role == "user" else "chat-bubble-ai"
    container_class = "chat-row-user" if role == "user" else "chat-row-ai"
    ts = timestamp.strftime("%H:%M") if timestamp else ""

    with st.container():
        st.markdown(
            f"""
            <div class="{container_class}">
                <div class="{bubble_class}">
                    <div class="chat-content">{content}</div>
                    <div class="chat-timestamp">{ts}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # CHUNK 6.6: Render quick insights for assistant messages
    if role == "assistant" and status == "complete":
        quick_results = metadata.get("quick_results", {})
        if quick_results:
            render_quick_insights(quick_results)
        
        # ============================================================
        # CHUNK 6.11.4 + 6.11.5: Render Trend Alert Cards + LLM Interpretations
        # ============================================================
        trend_alerts = metadata.get("trend_alerts", [])
        if trend_alerts:
            for alert_idx, alert in enumerate(trend_alerts):
                # Render alert card inline
                severity = alert.get("severity", "info")
                severity_colors = {
                    "critical": ("#DC2626", "rgba(220, 38, 38, 0.15)"),  # red
                    "warning": ("#F59E0B", "rgba(245, 158, 11, 0.15)"),  # amber
                    "info": ("#3B82F6", "rgba(59, 130, 246, 0.15)"),  # blue
                    "high": ("#DC2626", "rgba(220, 38, 38, 0.15)"),
                    "medium": ("#F59E0B", "rgba(245, 158, 11, 0.15)")
                }
                border_color, bg_color = severity_colors.get(severity, ("#3B82F6", "rgba(59, 130, 246, 0.15)"))
                
                st.markdown(
                    f"""
                    <div class="alert-card" style="
                        border: 1px solid {border_color};
                        background: {bg_color};
                        padding: 10px 14px;
                        margin-top: 6px;
                        border-radius: 8px;
                        border-left: 4px solid {border_color};">
                        <strong>{alert.get('title', 'Alert')}</strong><br>
                        <small>{alert.get('summary', '')}</small><br>
                        {f'<em>Recommended: {alert.get("action", "")}</em>' if alert.get("action") else ''}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                # CHUNK 6.11.5: Render LLM Interpretation Card if available
                if alert.get("llm_explanation"):
                    expl = alert["llm_explanation"]
                    st.markdown(
                        f"""
                        <div class='alert-interpretation-card' style="
                            border: 1px solid #8B5CF6;
                            background: rgba(139, 92, 246, 0.1);
                            padding: 12px 14px;
                            margin-top: 6px;
                            margin-bottom: 8px;
                            border-radius: 8px;
                            border-left: 4px solid #8B5CF6;">
                            <strong style="color: #6D28D9;">💡 Clinical Interpretation</strong><br>
                            <div style="margin-top: 6px; color: #374151; font-size: 0.9em; line-height: 1.6;">
                                {f'<div style="margin-bottom: 8px;"><strong>Summary:</strong> {expl.get("single_sentence_summary", "")}</div>' if expl.get("single_sentence_summary") else ''}
                                {f'<div style="margin-bottom: 8px;"><strong>Clinical Relevance:</strong> {expl.get("clinical_relevance", "")}</div>' if expl.get("clinical_relevance") else ''}
                                {f'<div style="margin-bottom: 8px;"><strong>Possible Causes:</strong><ul style="margin: 4px 0; padding-left: 20px;">' + ''.join([f'<li style="margin: 2px 0;">{cause}</li>' for cause in expl.get("possible_causes", [])[:3]]) + '</ul></div>' if expl.get("possible_causes") else ''}
                                {f'<div style="margin-top: 8px;"><strong>Recommendations:</strong><ul style="margin: 4px 0; padding-left: 20px;">' + ''.join([f'<li style="margin: 2px 0;">{rec}</li>' for rec in expl.get("recommended_followups", [])[:2]]) + '</ul></div>' if expl.get("recommended_followups") else ''}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                
                # CHUNK 6.11.7: Render Time-Series Insights if available
                if alert.get("time_series"):
                    _render_timeseries_insights(alert, key=f"{key}_ts_{alert_idx}")
                
                # CHUNK 6.11.8: Render Subgroup Insights if available
                if alert.get("subgroup_interpretation"):
                    _render_subgroup_insights(alert, key=f"{key}_subgroup_{alert_idx}")
                
                # CHUNK 6.11.9: Render Dose-Response Insights if available
                if alert.get("dose_response") or alert.get("cumulative_risk"):
                    _render_dose_response_insights(alert, key=f"{key}_dose_response_{alert_idx}")
                
                # CHUNK 6.11.10: Render Risk Dynamics Insights if available
                if alert.get("risk_dynamics"):
                    _render_risk_dynamics_insights(alert, key=f"{key}_risk_dynamics_{alert_idx}")
                
                # CHUNK 6.11.12: Render Narrative Cluster Summary if available
                if alert.get("narrative_clusters"):
                    clusters = alert.get("narrative_clusters", [])
                    if clusters:
                        cluster_summaries = []
                        for c in clusters[:3]:  # Top 3 clusters
                            summary = c.get("summary", {})
                            if summary:
                                label = summary.get("cluster_label", f"Cluster {c.get('cluster_id', 'N/A')}")
                                one_sentence = summary.get("one_sentence_summary", "")
                                cluster_summaries.append(f"**{label}:** {one_sentence}")
                        
                        if cluster_summaries:
                            st.markdown(
                                f"""
                                <div class='narrative-cluster-card' style="
                                    border: 1px solid #10B981;
                                    background: rgba(16, 185, 129, 0.1);
                                    padding: 12px 14px;
                                    margin-top: 6px;
                                    margin-bottom: 8px;
                                    border-radius: 8px;
                                    border-left: 4px solid #10B981;">
                                    <strong style="color: #047857;">🧠 Narrative Pattern Detection</strong><br>
                                    <div style="margin-top: 6px; color: #374151; font-size: 0.9em; line-height: 1.6;">
                                        {chr(10).join([f'• {summary}' for summary in cluster_summaries])}
                                        <br><em style="font-size: 0.85em;">Open Trend Alerts tab for full cluster analysis.</em>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                
                # CHUNK 6.11.13: Render Lot Alert Summary if available
                if alert.get("lot_alerts"):
                    lots = alert.get("lot_alerts", [])
                    if lots:
                        lot_summaries = []
                        for lot in lots[:3]:  # Top 3 lot alerts
                            lot_num = lot.get("lot_number", "N/A")
                            spike_ratio = lot.get("spike_ratio", 0.0)
                            count = lot.get("count", 0)
                            serious = lot.get("serious_count", 0)
                            interpretation = lot.get("interpretation", {})
                            one_sentence = interpretation.get("one_sentence_summary", "") if interpretation else ""
                            
                            if one_sentence:
                                lot_summaries.append(f"**Lot {lot_num}:** {one_sentence}")
                            else:
                                lot_summaries.append(f"**Lot {lot_num}:** {spike_ratio:.1f}× spike ({count} cases, {serious} serious)")
                        
                        if lot_summaries:
                            st.markdown(
                                f"""
                                <div class='lot-alert-card' style="
                                    border: 1px solid #F59E0B;
                                    background: rgba(245, 158, 11, 0.1);
                                    padding: 12px 14px;
                                    margin-top: 6px;
                                    margin-bottom: 8px;
                                    border-radius: 8px;
                                    border-left: 4px solid #F59E0B;">
                                    <strong style="color: #92400E;">🏭 Manufacturing Batch Anomaly</strong><br>
                                    <div style="margin-top: 6px; color: #374151; font-size: 0.9em; line-height: 1.6;">
                                        {chr(10).join([f'• {summary}' for summary in lot_summaries])}
                                        <br><em style="font-size: 0.85em;">Open Trend Alerts tab for detailed batch analysis.</em>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
        
        # CHUNK 6.11.4: Add Deep-Dive CTA button if alerts present
        if trend_alerts:
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(
                    "🔍 Detailed Analysis",
                    key=f"heavy_alert_{key}_{uuid.uuid4().hex[:8]}",
                    use_container_width=True,
                    help="Run comprehensive trend analysis with medium-level statistical alerts"
                ):
                    st.session_state.run_heavy_alerts = True
                    st.session_state.heavy_alerts_requested = True
                    st.rerun()

    # Typing indicator for assistant
    if role == "assistant" and status == "thinking":
        st.markdown(
            """
            <div class="typing-indicator">
                <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------
# Chat Input Box
# -----------------------------------------------------------

def _render_chat_input(on_send_callback):
    """
    Render fixed ChatGPT-style chat input bar (Chunk 5B).
    Supports auto-fill from pill suggestions (Chunk 4 + 6.9).
    Supports Enter-to-send and Shift+Enter for newline (Chunk 5C).
    """
    # CHUNK 6.9: Support chat_input_prefill from suggestions panel
    if st.session_state.get("chat_input_prefill"):
        st.session_state.chat_text_input = st.session_state.chat_input_prefill
        st.session_state.chat_input_prefill = None
    
    # Auto-fill from suggestion panel (Chunk 4B - legacy support)
    if st.session_state.get("pending_user_text"):
        st.session_state.chat_text_input = st.session_state.pending_user_text
        st.session_state.pending_user_text = None
    
    # Initialize input value if not exists
    if "chat_text_input" not in st.session_state:
        st.session_state.chat_text_input = ""
    
    # CHUNK 6.9: Check for JavaScript prefill from suggestions panel
    # This will be detected by the JavaScript in suggestions_panel.py
    # We'll also add a listener to detect when the textarea is prefilled
    
    # Fixed input bar container (Chunk 5A)
    st.markdown("<div class='as-chat-container'>", unsafe_allow_html=True)
    
    # CHUNK 6.9: Add JavaScript listener for pill auto-fill
    st.markdown("""
        <script>
        (function() {
            function setupPillPrefill() {
                const textarea = window.parent.document.querySelector('textarea[placeholder*="Ask about"]');
                if (textarea) {
                    // Check for prefill attribute set by suggestions_panel.py
                    const checkPrefill = () => {
                        if (textarea.getAttribute('data-prefilled') === 'true') {
                            const prefillText = textarea.getAttribute('data-prefill-text');
                            if (prefillText && textarea.value !== prefillText) {
                                textarea.value = prefillText;
                                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                                textarea.dispatchEvent(new Event('change', { bubbles: true }));
                                textarea.focus();
                                // Clear the attribute
                                textarea.removeAttribute('data-prefilled');
                                textarea.removeAttribute('data-prefill-text');
                            }
                        }
                    };
                    
                    // Check periodically for prefill
                    setInterval(checkPrefill, 200);
                    
                    // Also check on focus
                    textarea.addEventListener('focus', checkPrefill);
                } else {
                    setTimeout(setupPillPrefill, 300);
                }
            }
            
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setupPillPrefill);
            } else {
                setTimeout(setupPillPrefill, 300);
            }
        })();
        </script>
    """, unsafe_allow_html=True)
    
    # Use text_area for multi-line support (expands as user types)
    cols = st.columns([10, 1])
    
    with cols[0]:
        user_message = st.text_area(
            label="Chat message",
            value=st.session_state.chat_text_input,
            placeholder="Ask about any drug, reaction, or safety signal...",
            height=46,
            key="chat_text_input",
            label_visibility="collapsed",
        )
    
    with cols[1]:
        send_clicked = st.button(
            "Send",
            key="chat_send_button",
            use_container_width=True,
            type="primary"
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Handle send button click
    if send_clicked and user_message.strip():
        on_send_callback(user_message.strip())
        st.session_state.chat_text_input = ""  # clear input after sending
        st.rerun()  # Refresh to show updated chat


# -----------------------------------------------------------
# Public API: Render the Full Chat Interface
# -----------------------------------------------------------

def render_chat_interface(on_send_callback):
    """
    Render full ChatGPT-style interface with fixed input bar (Chunk 5).
    
    Args:
        on_send_callback: function(message: str) → None
    """
    # Ensure chat history exists
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Enter-to-send JavaScript (Chunk 5C)
    # Captures Enter key in textarea to trigger send button
    st.markdown(
        """
        <script>
        (function() {
            function setupEnterToSend() {
                // Find textarea with our placeholder
                const textareas = window.parent.document.querySelectorAll('textarea');
                let targetTextarea = null;
                for (let ta of textareas) {
                    if (ta.placeholder && ta.placeholder.includes('Ask about any drug')) {
                        targetTextarea = ta;
                        break;
                    }
                }
                
                // Find send button by text content
                const buttons = window.parent.document.querySelectorAll('button');
                let sendButton = null;
                for (let btn of buttons) {
                    const btnText = btn.textContent || btn.innerText || '';
                    if (btnText.trim() === 'Send') {
                        sendButton = btn;
                        break;
                    }
                }
                
                if (targetTextarea && sendButton) {
                    // Remove old listener if exists
                    const oldHandler = targetTextarea._enterHandler;
                    if (oldHandler) {
                        targetTextarea.removeEventListener('keydown', oldHandler);
                    }
                    
                    // Create new handler
                    function handleEnterKey(e) {
                        if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            e.stopPropagation();
                            sendButton.click();
                            return false;
                        }
                    }
                    
                    // Store handler reference
                    targetTextarea._enterHandler = handleEnterKey;
                    targetTextarea.addEventListener("keydown", handleEnterKey, true);
                } else {
                    // Retry if elements not ready
                    setTimeout(setupEnterToSend, 200);
                }
            }
            
            // Setup after page loads
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(setupEnterToSend, 500);
                });
            } else {
                setTimeout(setupEnterToSend, 500);
            }
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )

    # Scroll anchor
    st.markdown("<div id='chat-scroll-anchor'></div>", unsafe_allow_html=True)

    # Chat container with scrollable history (CHUNK 6.8: Enhanced styling)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Render history
    for idx, msg in enumerate(st.session_state.chat_history):
        _render_message_bubble(msg, key=f"chat_msg_{idx}")
    
    # CHUNK 6.11-C: Show trend alerts as system notifications (once per session)
    _maybe_show_trend_alerts_in_chat()

    st.markdown("</div>", unsafe_allow_html=True)

    # Auto-scroll script
    st.markdown(
        """
        <script>
            setTimeout(function() {
                var el = document.getElementById('chat-scroll-anchor');
                if (el) { el.scrollIntoView({behavior: 'smooth'}); }
            }, 100);
        </script>
        """,
        unsafe_allow_html=True,
    )

    # Fixed input bar (Chunk 5B)
    _render_chat_input(on_send_callback)


# -----------------------------------------------------------
# Helper: Add a message to chat history
# -----------------------------------------------------------

def _maybe_show_trend_alerts_in_chat():
    """
    Show trend alerts as system messages in chat (CHUNK 6.11-C: UI Integration).
    Only shows once per session when alerts are detected.
    """
    # Check if we've already shown alerts in this session
    if st.session_state.get("trend_alerts_shown_in_chat", False):
        return
    
    # Get normalized data
    normalized_df = st.session_state.get("normalized_data")
    if normalized_df is None or len(normalized_df) == 0:
        return
    
    try:
        from src.ai.trend_alerts import detect_trend_alerts
        
        # Detect alerts
        alerts_result = detect_trend_alerts(normalized_df)
        if not alerts_result:
            return
        
        alerts = alerts_result.get("alerts", [])
        spikes = alerts_result.get("spikes", [])
        emerging_signals = alerts_result.get("emerging_signals", [])
        
        total_count = len(alerts) + len(spikes) + len(emerging_signals)
        
        if total_count == 0:
            return
        
        # Build alert summary message
        alert_summary_parts = [f"⚠️ I detected **{total_count}** trend alerts in your dataset:"]
        
        if alerts:
            alert_summary_parts.append(f"\n• **{len(alerts)}** high-priority alerts")
        if spikes:
            alert_summary_parts.append(f"• **{len(spikes)}** detected spikes")
        if emerging_signals:
            alert_summary_parts.append(f"• **{len(emerging_signals)}** emerging signals")
        
        alert_summary_parts.append("\n\nCheck the QuickStats panel above for details, or ask me to analyze any specific trend.")
        
        # Add as system message (only if chat history is empty or this is first load)
        if len(st.session_state.get("chat_history", [])) == 0:
            add_chat_message(
                "system",
                "".join(alert_summary_parts),
                status="complete",
                metadata={"type": "trend_alerts_summary", "alert_count": total_count}
            )
        
        # Mark as shown
        st.session_state.trend_alerts_shown_in_chat = True
        
    except Exception:
        # Fail silently if alerts not available
        pass


def _render_timeseries_insights(alert: Dict, key: str):
    """
    Render time-series statistical insights for an alert (CHUNK 6.11.7).
    
    Args:
        alert: Alert dictionary with time_series field
        key: Unique key for Streamlit component
    """
    ts = alert.get("time_series", {})
    
    if not ts:
        return
    
    latest_value = ts.get("latest_value", 0)
    expected_value = ts.get("expected_value", 0)
    delta = ts.get("delta", 0)
    significance = ts.get("significance", 0)
    
    # Determine significance level
    sig_level = "High" if significance > 3 else "Moderate" if significance > 2 else "Low"
    sig_color = "#DC2626" if significance > 3 else "#F59E0B" if significance > 2 else "#3B82F6"
    
    st.markdown(
        f"""
        <div class="ts-insight-card" style="
            border: 1px solid {sig_color};
            background: rgba(59, 130, 246, 0.1);
            padding: 12px 14px;
            margin-top: 6px;
            margin-bottom: 8px;
            border-radius: 8px;
            border-left: 4px solid {sig_color};">
            <strong style="color: #1F2937;">📊 Statistical Summary</strong><br>
            <div style="margin-top: 6px; color: #4B5563; font-size: 0.9em;">
                <strong>Observed:</strong> {int(latest_value) if latest_value else 0}<br>
                <strong>Expected (MA):</strong> {expected_value:.2f if expected_value else 'N/A'}<br>
                <strong>Δ (Observed - Expected):</strong> {delta:+.2f if delta else '0'}<br>
                <strong>Significance:</strong> <span style="color: {sig_color}; font-weight: 600;">{significance:.2f}σ ({sig_level})</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Show anomalies if present
    if ts.get("anomalies") and len(ts["anomalies"]) > 0:
        st.caption(f"⚠️ {len(ts['anomalies'])} anomaly/anomalies detected in time series")
    
    # Show change-points if present
    if ts.get("changepoints") and len(ts["changepoints"]) > 0:
        periods = ts.get("periods", [])
        changepoint_periods = [periods[idx] for idx in ts["changepoints"] if idx < len(periods)][:3]
        if changepoint_periods:
            st.caption(f"🔴 Structural change-point(s) at: {', '.join(changepoint_periods)}")


def _render_subgroup_insights(alert: Dict, key: str):
    """
    Render subgroup analysis insights for an alert (CHUNK 6.11.8).
    
    Args:
        alert: Alert dictionary with subgroups and subgroup_interpretation fields
        key: Unique key for Streamlit component
    """
    interpretation = alert.get("subgroup_interpretation", {})
    subgroups = alert.get("subgroups", {})
    
    if not interpretation:
        return
    
    key_findings = interpretation.get("key_findings", [])
    risk_factors = interpretation.get("possible_risk_factors", [])
    recommendations = interpretation.get("recommendations", [])
    
    st.markdown(
        f"""
        <div class='subgroup-card' style="
            border: 1px solid #8B5CF6;
            background: rgba(139, 92, 246, 0.1);
            padding: 14px 16px;
            margin-top: 6px;
            margin-bottom: 8px;
            border-radius: 8px;
            border-left: 4px solid #8B5CF6;">
            <strong style="color: #6D28D9;">🧬 Population Subgroup Insights</strong><br>
            <div style="margin-top: 8px; color: #374151; font-size: 0.9em; line-height: 1.6;">
                {f'<div style="margin-bottom: 8px;"><strong>Key Findings:</strong><ul style="margin: 4px 0; padding-left: 20px;">' + ''.join([f'<li style="margin: 2px 0;">{finding}</li>' for finding in key_findings[:3]]) + '</ul></div>' if key_findings else ''}
                {f'<div style="margin-bottom: 8px;"><strong>Risk Factors:</strong><ul style="margin: 4px 0; padding-left: 20px;">' + ''.join([f'<li style="margin: 2px 0;">{factor}</li>' for factor in risk_factors[:2]]) + '</ul></div>' if risk_factors else ''}
                {f'<div style="margin-top: 8px;"><strong>Recommendations:</strong><ul style="margin: 4px 0; padding-left: 20px;">' + ''.join([f'<li style="margin: 2px 0;">{rec}</li>' for rec in recommendations[:2]]) + '</ul></div>' if recommendations else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Show top subgroup anomalies if available
    if subgroups:
        anomaly_subgroups = [
            (name, data) for name, data in subgroups.items() 
            if data.get("anomaly_score", 1.0) > 2.0
        ]
        if anomaly_subgroups:
            anomaly_info = []
            for name, data in anomaly_subgroups[:3]:
                top_group = data.get("top_group", "N/A")
                stat_tests = data.get("statistical_tests", {})
                if stat_tests and stat_tests.get("p_value_chi2") and stat_tests["p_value_chi2"] < 0.05:
                    anomaly_info.append(f"{name} ({top_group}, p<0.05)")
                else:
                    anomaly_info.append(f"{name} ({top_group})")
            st.caption(
                f"⚠️ Anomalous patterns detected in: {', '.join(anomaly_info)}"
            )
    
    # CHUNK 6.11.11: Show concomitant drug warning if available
    if alert.get("details") and alert["details"].get("concomitant_drugs"):
        concomitants = alert["details"]["concomitant_drugs"]
        conc_ratio = concomitants.get("concomitant_ratio", 0.0)
        if conc_ratio > 0.3:
            top_conc = list(concomitants.get("top_concomitants", {}).keys())[:3]
            st.caption(
                f"💊 High concomitant drug use ({conc_ratio:.1%}). "
                f"Top concomitants: {', '.join(top_conc)}"
            )


def _render_dose_response_insights(alert: Dict, key: str):
    """
    Render dose-response and cumulative risk insights for an alert (CHUNK 6.11.9).
    
    Args:
        alert: Alert dictionary with dose_response and/or cumulative_risk fields
        key: Unique key for Streamlit component
    """
    dose_response = alert.get("dose_response", {})
    cumulative_risk = alert.get("cumulative_risk", {})
    
    # Build summary message
    summary_parts = []
    
    if dose_response and dose_response.get("significance", 1.0) > 1.5:
        significance = dose_response.get("significance", 1.0)
        trend_dir = dose_response.get("trend_direction", "unknown")
        summary_parts.append(
            f"📈 **Dose-Response Detected:** Higher doses show {significance:.2f}× higher reporting rates ({trend_dir} trend)"
        )
    
    if cumulative_risk and cumulative_risk.get("is_increasing", False):
        total_cases = cumulative_risk.get("total_cases", 0)
        summary_parts.append(
            f"⏱ **Cumulative Risk Increasing:** {total_cases} cases accumulating month-over-month"
        )
    
    if not summary_parts:
        return
    
    st.markdown(
        f"""
        <div class='dose-response-card' style="
            border: 1px solid #6366F1;
            background: rgba(99, 102, 241, 0.1);
            padding: 12px 14px;
            margin-top: 6px;
            margin-bottom: 8px;
            border-radius: 8px;
            border-left: 4px solid #6366F1;">
            <strong style="color: #4F46E5;">📊 Dose-Response & Exposure Analysis</strong><br>
            <div style="margin-top: 6px; color: #374151; font-size: 0.9em; line-height: 1.6;">
                {'<br>'.join([f'• {part}' for part in summary_parts])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Add button to open full analysis if available
    if dose_response or cumulative_risk:
        st.caption("💡 Click 'Detailed Analysis' below to view full dose-response curves and charts")


def _render_risk_dynamics_insights(alert: Dict, key: str):
    """
    Render risk dynamics (velocity, acceleration, change-points) insights for an alert (CHUNK 6.11.10).
    
    Args:
        alert: Alert dictionary with risk_dynamics field
        key: Unique key for Streamlit component
    """
    risk_dynamics = alert.get("risk_dynamics", {})
    if not risk_dynamics:
        return
    
    # Build summary message
    summary_parts = []
    
    # Check velocity/acceleration
    vel_acc = risk_dynamics.get("velocity_acceleration", {})
    if vel_acc:
        acc_score = vel_acc.get("acceleration_score", 0.0)
        trend_class = vel_acc.get("trend_classification", "unknown")
        is_accelerating = vel_acc.get("is_accelerating", False)
        
        if is_accelerating:
            summary_parts.append(
                f"📉 **Accelerating Risk Detected** — acceleration score: {acc_score:.2f} ({trend_class})"
            )
        elif vel_acc.get("is_decelerating", False):
            summary_parts.append(
                f"📊 **Risk Decelerating** — acceleration score: {acc_score:.2f}"
            )
        else:
            summary_parts.append(
                f"📊 **Risk Trend Stable** — acceleration score: {acc_score:.2f}"
            )
    
    # Check change-points
    changepoints = risk_dynamics.get("changepoints", [])
    changepoints_context = risk_dynamics.get("changepoints_with_context", [])
    
    if changepoints_context:
        cp_info = []
        for cp in changepoints_context[:2]:  # Top 2 change-points
            period = cp.get("period", "N/A")
            ratio = cp.get("change_ratio", 1.0)
            cp_info.append(f"{period} ({ratio:.2f}×)")
        
        if cp_info:
            summary_parts.append(
                f"⚡ **Structural Change-Points:** {', '.join(cp_info)}"
            )
    
    if not summary_parts:
        return
    
    # Determine color based on risk level
    if risk_dynamics.get("velocity_acceleration", {}).get("is_accelerating", False) or changepoints:
        border_color = "#EF4444"  # Red for high risk
        bg_color = "rgba(239, 68, 68, 0.1)"
    else:
        border_color = "#6366F1"  # Indigo for informational
        bg_color = "rgba(99, 102, 241, 0.1)"
    
    st.markdown(
        f"""
        <div class='risk-dynamics-card' style="
            border: 1px solid {border_color};
            background: {bg_color};
            padding: 12px 14px;
            margin-top: 6px;
            margin-bottom: 8px;
            border-radius: 8px;
            border-left: 4px solid {border_color};">
            <strong style="color: #1F2937;">📊 Risk Dynamics Analysis</strong><br>
            <div style="margin-top: 6px; color: #374151; font-size: 0.9em; line-height: 1.6;">
                {'<br>'.join([f'• {part}' for part in summary_parts])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def add_chat_message(role: str, content: str, status: str = "complete", metadata: Optional[dict] = None):
    """Append a message to chat history."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.session_state.chat_history.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "status": status,
            "metadata": metadata or {}
        }
    )


# -----------------------------------------------------------
# Helper: Update last assistant message
# -----------------------------------------------------------

def update_last_assistant_message(content: str, status: str = "complete", metadata: Optional[dict] = None):
    """Update the last assistant message in chat history."""
    if "chat_history" not in st.session_state or not st.session_state.chat_history:
        return
    
    # Find last assistant message
    for msg in reversed(st.session_state.chat_history):
        if msg["role"] == "assistant":
            msg["content"] = content
            msg["status"] = status
            if metadata:
                msg["metadata"] = metadata
            msg["timestamp"] = datetime.now()
            break

