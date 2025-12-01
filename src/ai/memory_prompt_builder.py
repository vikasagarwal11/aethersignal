"""
Memory Prompt Builder for AetherSignal (Chunk 6.3)
Converts memory state into compressed system prompts for LLM context.

Provides ChatGPT-like multi-turn context without heavy token usage.
"""

from typing import Dict, Any, List


# -------------------------------------------------------------------
# 🔵 Utility: Clean empty and None values (safer, shorter prompt)
# -------------------------------------------------------------------
def _clean_memory(memory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove empty/None values from memory to create compact prompts.
    
    Args:
        memory: Raw memory state dictionary
        
    Returns:
        Cleaned memory dictionary with only non-empty values
    """
    cleaned = {}
    
    for k, v in memory.items():
        # Skip None values
        if v is None:
            continue
        
        # Skip empty lists
        if isinstance(v, list) and len(v) == 0:
            continue
        
        # Skip empty strings
        if isinstance(v, str) and v.strip() == "":
            continue
        
        # Skip empty dictionaries
        if isinstance(v, dict) and len(v.keys()) == 0:
            continue
        
        cleaned[k] = v
    
    return cleaned


# -------------------------------------------------------------------
# 🔵 Convert memory_state into a compressed system prompt
# -------------------------------------------------------------------
def build_memory_prompt(memory_state: Dict[str, Any]) -> str:
    """
    Build a compressed system prompt from memory state.
    
    Creates a structured, concise prompt that gives the LLM context
    about the current conversation without excessive token usage.
    
    Args:
        memory_state: Current memory state dictionary
        
    Returns:
        Formatted system prompt string (typically 200-500 tokens)
    """
    # Clean memory to remove empty values
    memory = _clean_memory(memory_state)
    
    # If memory is empty, return basic prompt
    if not memory:
        return """You are an expert Pharmacovigilance analyst AI assistant.
Always use factual reasoning and rely ONLY on provided data.
Respond concisely unless the user asks for details."""
    
    parts: List[str] = []
    
    # Header
    parts.append("You are an expert Pharmacovigilance analyst AI assistant.")
    parts.append("Always use factual reasoning and rely ONLY on provided data.")
    
    # Add context variables dynamically
    parts.append("\nCurrent conversation context:")
    
    # Drug of interest
    if "drug" in memory and memory["drug"]:
        parts.append(f"- Drug of interest: {memory['drug']}")
    
    # Reactions of interest
    if "reactions" in memory and memory["reactions"]:
        rx = ", ".join(memory["reactions"])
        parts.append(f"- Reactions of interest: {rx}")
    
    # Active filters
    if "filters" in memory and memory["filters"]:
        filter_items = []
        for k, v in memory["filters"].items():
            if v is not None:
                filter_items.append(f"{k}={v}")
        if filter_items:
            fl = ", ".join(filter_items)
            parts.append(f"- Active filters: {fl}")
    
    # Time window
    if "time_window" in memory and memory["time_window"]:
        parts.append(f"- Time window: {memory['time_window']}")
    
    # User goals
    if "user_goals" in memory and memory["user_goals"]:
        goals = ", ".join(memory["user_goals"])
        parts.append(f"- User goals: {goals}")
    
    # Conversation summary (truncated for compactness)
    if "conversation_summary" in memory and memory["conversation_summary"]:
        # Keep only the last 500 chars for compactness
        short_summary = memory["conversation_summary"][-500:]
        # Try to start at a complete line
        first_newline = short_summary.find('\n')
        if first_newline > 0:
            short_summary = short_summary[first_newline + 1:]
        parts.append(f"\nSummary of recent conversation:")
        parts.append(short_summary)
    
    # Instructions for multi-turn behavior
    parts.append("\nInstructions:")
    parts.append("- Use the context above when interpreting follow-up questions.")
    parts.append("- If the user references 'continue', 'filter more', 'only those', 'only serious', 'what about', etc., use stored memory.")
    parts.append("- Do NOT hallucinate drug names or reactions - only use what's in the context or dataset.")
    parts.append("- Base your reasoning ONLY on provided filters and dataset summaries.")
    parts.append("- When the user asks follow-up questions like 'only serious ones', merge filters with existing context.")
    parts.append("- Respond concisely unless the user asks for detailed explanations.")
    parts.append("- For time-based queries (e.g., 'last year', 'compare with 2023'), use the time_window context if available.")
    
    return "\n".join(parts)


# -------------------------------------------------------------------
# 🔵 Helper: Build prompt with last N messages (optional enhancement)
# -------------------------------------------------------------------
def build_context_messages(
    memory_state: Dict[str, Any],
    chat_history: List[Dict[str, Any]],
    last_n: int = 4
) -> List[Dict[str, str]]:
    """
    Build message list with system prompt and last N conversation turns.
    
    Args:
        memory_state: Current memory state
        chat_history: Full chat history
        last_n: Number of recent messages to include (default: 4)
        
    Returns:
        List of message dictionaries for LLM API
    """
    messages = []
    
    # Add system prompt with memory context
    system_prompt = build_memory_prompt(memory_state)
    messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # Add last N messages from chat history
    recent_messages = chat_history[-last_n:] if len(chat_history) > last_n else chat_history
    
    for msg in recent_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        status = msg.get("status", "complete")
        
        # Skip "thinking" messages
        if status == "thinking":
            continue
        
        # Only include complete messages
        if content and status == "complete":
            messages.append({
                "role": role,
                "content": content
            })
    
    return messages

