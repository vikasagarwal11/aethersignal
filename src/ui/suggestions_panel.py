"""
Enterprise Suggestions Panel (Chunk 6.9)
Unified, clean, flat-pill suggestions UI for AetherSignal.
"""
import streamlit as st
from typing import List, Tuple, Dict, Callable, Optional


def _pill_html(label: str, query_text: str) -> str:
    """
    Generate HTML for a suggestion pill that auto-fills the chat input.
    
    Args:
        label: Display text for the pill
        query_text: Text to auto-fill into chat input when clicked
    """
    # Escape quotes for JavaScript
    escaped_query = query_text.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
    escaped_label = label.replace("'", "\\'").replace('"', '\\"')
    
    return f"""
    <span class="suggestion-pill" onclick="suggest_prefill('{escaped_query}')" title="{escaped_query}">
        {escaped_label}
    </span>
    """


def render_suggestions_panel(
    top_drugs: List[str],
    top_reactions: List[str],
    starter_questions: List[Tuple[str, str, str]],  # (title, query, icon)
    recent_queries: List[Dict],
    saved_queries: Optional[List] = None,
    on_select: Optional[Callable[[str], None]] = None,
):
    """
    Fully unified suggestions UI (Chunk 6.9).
    Enterprise-grade layout:
    - Two-column for wide screens
    - All pills flat + outlined + blue-accent
    - Auto-fill on click
    
    Args:
        top_drugs: List of top drug names
        top_reactions: List of top reaction names
        starter_questions: List of (title, query, icon) tuples
        recent_queries: List of recent query dictionaries from query_history
        saved_queries: Optional list of saved queries
        on_select: Optional callback when a suggestion is selected (not used with HTML pills)
    """
    st.markdown("### 🔍 Quick Suggestions")
    st.markdown('<div class="suggestions-container">', unsafe_allow_html=True)

    # CATEGORY: Starter Questions
    if starter_questions:
        st.markdown("#### 🧠 Starter Questions")
        pills_html = ""
        for title, query, icon in starter_questions[:6]:  # Limit to 6 for cleaner layout
            pills_html += _pill_html(f"{icon} {title}", query)
        st.markdown(pills_html, unsafe_allow_html=True)

    # CATEGORY: Top Drugs
    if top_drugs:
        st.markdown("#### 💊 Most Reported Drugs")
        pills_html = ""
        for drug in top_drugs[:8]:  # Limit to top 8
            query_text = f"Show me safety information for {drug}"
            pills_html += _pill_html(drug, query_text)
        st.markdown(pills_html, unsafe_allow_html=True)

    # CATEGORY: Top Reactions
    if top_reactions:
        st.markdown("#### ⚠️ Most Reported Reactions")
        pills_html = ""
        for reaction in top_reactions[:8]:  # Limit to top 8
            query_text = f"Cases involving {reaction}"
            pills_html += _pill_html(reaction, query_text)
        st.markdown(pills_html, unsafe_allow_html=True)

    # CATEGORY: Recent Queries
    if recent_queries:
        st.markdown("#### 🕘 Recent Searches")
        pills_html = ""
        # Show most recent queries (reversed to show newest first)
        display_recent = list(reversed(recent_queries[-8:]))  # Last 8, newest first
        for rq in display_recent:
            if isinstance(rq, dict):
                query_text = rq.get("query_text", "")
            else:
                query_text = str(rq)
            
            if query_text:
                # Truncate display label if too long
                display_label = query_text[:50] + "..." if len(query_text) > 50 else query_text
                pills_html += _pill_html(display_label, query_text)
        st.markdown(pills_html, unsafe_allow_html=True)

    # CATEGORY: Saved Queries (if provided)
    if saved_queries:
        st.markdown("#### 📌 Saved Queries")
        pills_html = ""
        for sq in saved_queries[:8]:  # Limit to 8
            if isinstance(sq, dict):
                query_text = sq.get("query_text", sq.get("name", ""))
                name = sq.get("name", f"Query") if "name" in sq else query_text[:40]
            else:
                query_text = str(sq)
                name = query_text[:40]
            
            if query_text:
                pills_html += _pill_html(f"📌 {name}", query_text)
        st.markdown(pills_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # JavaScript callback → auto-fill chat input via direct DOM manipulation
    # This approach works by directly setting the textarea value and triggering events
    st.markdown("""
        <script>
        function suggest_prefill(text) {
            // Find the chat input textarea
            const textareas = window.parent.document.querySelectorAll('textarea');
            let streamlitInput = null;
            
            for (let ta of textareas) {
                if (ta.placeholder && ta.placeholder.includes('Ask about')) {
                    streamlitInput = ta;
                    break;
                }
            }
            
            if (streamlitInput) {
                // Store the prefill text in a way that persists across reruns
                // Use sessionStorage as a bridge
                sessionStorage.setItem('aether_chat_prefill', text);
                
                // Fill the textarea immediately
                streamlitInput.value = text;
                
                // Trigger input events to notify Streamlit
                streamlitInput.dispatchEvent(new Event('input', { bubbles: true }));
                streamlitInput.dispatchEvent(new Event('change', { bubbles: true }));
                streamlitInput.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
                
                // Focus the input
                streamlitInput.focus();
                
                // Set cursor to end
                if (streamlitInput.setSelectionRange) {
                    streamlitInput.setSelectionRange(text.length, text.length);
                }
                
                // Mark as prefilled for visual feedback
                streamlitInput.setAttribute('data-prefilled', 'true');
                
                // Small visual feedback - highlight briefly
                streamlitInput.style.backgroundColor = '#EFF6FF';
                setTimeout(() => {
                    streamlitInput.style.backgroundColor = '';
                }, 500);
            }
        }
        
        // Check for prefilled text on load (for persistence across reruns)
        setTimeout(function() {
            const prefillText = sessionStorage.getItem('aether_chat_prefill');
            if (prefillText) {
                const textareas = window.parent.document.querySelectorAll('textarea');
                for (let ta of textareas) {
                    if (ta.placeholder && ta.placeholder.includes('Ask about')) {
                        if (ta.value !== prefillText) {
                            ta.value = prefillText;
                            ta.dispatchEvent(new Event('input', { bubbles: true }));
                            ta.dispatchEvent(new Event('change', { bubbles: true }));
                            ta.focus();
                        }
                        sessionStorage.removeItem('aether_chat_prefill');
                        break;
                    }
                }
            }
        }, 300);
        </script>
    """, unsafe_allow_html=True)

