"""
Safety Copilot Chat Interface (Phase 3G.4)
Interactive chat UI for Safety Copilot.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import logging

from src.copilot.safety_copilot import SafetyCopilot

logger = logging.getLogger(__name__)


def render_copilot_interface():
    """Render Safety Copilot chat interface."""
    st.header("🤖 Safety Copilot")
    st.caption("AI assistant for pharmacovigilance - Ask questions, get insights, generate reports")
    
    # Initialize copilot
    if "copilot" not in st.session_state:
        st.session_state["copilot"] = SafetyCopilot()
    
    copilot = st.session_state["copilot"]
    
    # Initialize chat history
    if "copilot_history" not in st.session_state:
        st.session_state["copilot_history"] = []
    
    # Display chat history
    for message in st.session_state["copilot_history"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "metadata" in message:
                with st.expander("Details"):
                    st.json(message["metadata"])
    
    # Chat input
    user_query = st.chat_input("Ask Safety Copilot...")
    
    if user_query:
        # Add user message to history
        st.session_state["copilot_history"].append({
            "role": "user",
            "content": user_query
        })
        
        # Get copilot response
        with st.spinner("Safety Copilot is thinking..."):
            response = copilot.chat(user_query)
        
        # Add assistant response to history
        st.session_state["copilot_history"].append({
            "role": "assistant",
            "content": response.get("response", "I couldn't process your query."),
            "metadata": {
                "agents_used": response.get("agents_used", []),
                "tools_called": response.get("tools_called", [])
            }
        })
        
        # Rerun to show new messages
        st.rerun()
    
    # Sidebar with templates
    with st.sidebar:
        st.markdown("### 📋 Quick Templates")
        
        templates = [
            "Investigate a signal",
            "Explain mechanism",
            "Check label gaps",
            "Prioritize risks",
            "Summarize literature",
            "Generate RMP section"
        ]
        
        for template in templates:
            if st.button(template, use_container_width=True):
                # Auto-fill query
                st.session_state["copilot_query"] = template
                st.rerun()
        
        # Clear history
        if st.button("🗑️ Clear History"):
            st.session_state["copilot_history"] = []
            st.rerun()

