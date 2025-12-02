"""
Safety Copilot Workspace UI - AI assistant for safety scientists
"""

import streamlit as st
from src.ui.layout.base_layout import render_base_layout
from src.ai_intelligence.copilot.copilot_engine import CopilotEngine


def render_copilot_workspace():
    """
    Render the Safety Copilot chat interface.
    """
    def page_content():
        st.title("🤖 Safety Copilot")
        st.caption("Real-time AI assistant for pharmacovigilance analysis")
        
        st.info(
            """
            **Safety Copilot** provides:
            
            - Conversational safety insights
            - Signal explanations
            - Mechanism reasoning
            - Label gap detection
            - Trend analysis
            - Evidence retrieval
            
            Powered by hybrid AI (local + cloud models) with tool-based reasoning.
            """
        )
        
        # Initialize chat history
        if "copilot_history" not in st.session_state:
            st.session_state.copilot_history = []
        
        # Initialize copilot engine
        if "copilot_engine" not in st.session_state:
            st.session_state.copilot_engine = CopilotEngine()
        
        # Display chat history
        for message in st.session_state.copilot_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        prompt = st.chat_input("Ask about a drug, AE, trend, mechanism...")
        
        if prompt:
            # Add user message
            st.session_state.copilot_history.append({
                "role": "user",
                "content": prompt
            })
            
            # Get response from copilot engine (with streaming support)
            engine = st.session_state.copilot_engine
            
            # Check if streaming is enabled
            use_streaming = st.session_state.get("copilot_streaming", True)
            
            if use_streaming:
                # Stream response
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    response_stream = engine.ask(prompt, stream=True)
                    
                    for chunk in response_stream:
                        full_response += chunk
                        response_placeholder.write(full_response)
                    
                    # Add complete response to history
                    st.session_state.copilot_history.append({
                        "role": "assistant",
                        "content": full_response
                    })
                except Exception:
                    # Fallback to non-streaming
                    with st.spinner("Thinking..."):
                        response = engine.ask(prompt, stream=False)
                    
                    st.session_state.copilot_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    st.rerun()
            else:
                # Non-streaming mode
                with st.spinner("Thinking..."):
                    response = engine.ask(prompt, stream=False)
                
                # Add assistant response
                st.session_state.copilot_history.append({
                    "role": "assistant",
                    "content": response
                })
                
                st.rerun()
        
        # Tool information sidebar
        with st.sidebar:
            st.markdown("### 🛠️ Available Tools")
            st.caption("Copilot can use these tools:")
            
            tools_info = [
                ("🔍 FAERS Query", "Query FAERS database"),
                ("🌐 Social Query", "Query social media AEs"),
                ("📚 Literature Query", "Query PubMed/literature"),
                ("🧬 Mechanism AI", "Explain drug-AE mechanisms"),
                ("⚖️ Causality", "Assess causality"),
                ("📑 Label Gap", "Check FDA label gaps"),
                ("🆕 Novelty", "Detect novel signals"),
                ("📈 Trend", "Analyze trends")
            ]
            
            for tool_name, tool_desc in tools_info:
                st.markdown(f"**{tool_name}**")
                st.caption(tool_desc)
    
    render_base_layout(page_content)

