"""
Streaming helpers for progressive UI updates during query processing.
Provides milestone updates, token streaming, and chat message updates.
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Callable


# -----------------------------------------------------------
# STEP 1: Stream milestone updates into UI (parsing / filtering / stats)
# -----------------------------------------------------------

def send_stream_step(container, text: str, status: str = "info"):
    """
    Display a streaming milestone update inside a Streamlit placeholder.
    
    Example:
        send_stream_step(parsing_box, "Parsing your query…")
    """
    if status == "info":
        container.info(text)
    elif status == "success":
        container.success(text)
    elif status == "warning":
        container.warning(text)
    elif status == "error":
        container.error(text)
    else:
        container.write(text)


# -----------------------------------------------------------
# STEP 2: Token-by-token LLM streaming (optional)
# -----------------------------------------------------------

def stream_llm_tokens(
    client,
    model: str,
    prompt: str,
    on_token: Callable[[str], None],
    temperature: float = 0.0
):
    """
    Streams tokens from OpenAI/Groq API.
    Each token is passed to on_token(token).
    """
    stream = client.chat.completions.create(
        model=model,
        stream=True,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )

    for chunk in stream:
        if not chunk:
            continue
        delta = chunk.choices[0].delta
        if hasattr(delta, "content") and delta.content:
            on_token(delta.content)


# -----------------------------------------------------------
# STEP 3: Append streamed text to last assistant message
# -----------------------------------------------------------

def append_assistant_stream_chunk(chunk: str):
    """
    Adds streamed text into the last assistant message in history.
    Used while LLM is streaming tokens.
    """
    if "chat_history" not in st.session_state:
        return
    
    # Find last assistant message
    for msg in reversed(st.session_state.chat_history):
        if msg["role"] == "assistant":
            msg["content"] += chunk
            break


# -----------------------------------------------------------
# STEP 4: Replace temporary "thinking" bubble with final content
# -----------------------------------------------------------

def finalize_assistant_message(final_text: str, metadata: Optional[dict] = None):
    """
    Replaces the last assistant message (thinking bubble) with final summary.
    """
    if "chat_history" not in st.session_state:
        return

    # Get last assistant message
    for msg in reversed(st.session_state.chat_history):
        if msg["role"] == "assistant":
            msg["content"] = final_text
            msg["status"] = "complete"
            if metadata:
                msg["metadata"] = metadata
            msg["timestamp"] = datetime.now()
            break

