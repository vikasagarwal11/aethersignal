"""
Memory Extraction Engine for AetherSignal (Chunk 6.2)
Extracts conversation context from user messages for multi-turn conversations.

Lightweight, rule-based extraction - no heavy NLP or LLM calls.
Integrates with existing query parsing infrastructure.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


# ------------------------------------------------------------
# 🔵 Utility: Common PV reaction keywords
# (Enrichable later using MedDRA or dataset-driven extraction)
# ------------------------------------------------------------
REACTION_KEYWORDS = [
    "rash", "anaphylaxis", "anaphylactic", "fever", "pain",
    "headache", "conjunctivitis", "pneumonia", "urticaria",
    "dyspnea", "cough", "itching", "swelling", "nausea",
    "vomiting", "diarrhea", "dizziness", "fatigue", "asthma",
    "bronchitis", "myocarditis", "thrombosis", "stroke",
    "cardiac arrest", "liver failure", "kidney failure"
]


# ------------------------------------------------------------
# 🔵 Utility: Time expressions
# ------------------------------------------------------------
TIME_PATTERNS = {
    "last 6 months": "6m",
    "last six months": "6m",
    "last 12 months": "12m",
    "last year": "12m",
    "past year": "12m",
    "past 6 months": "6m",
    "last quarter": "3m",
    "past quarter": "3m",
    "last 3 months": "3m",
    "last month": "1m",
    "past month": "1m",
    "this year": "ytd",
    "year to date": "ytd",
    "since 2020": "2020",
    "from 2020": "2020",
    "2023": "2023",
    "2024": "2024",
}


# ------------------------------------------------------------
# 🔵 Utility: PV Filter keywords
# ------------------------------------------------------------
FILTER_KEYWORDS = {
    "serious": ("seriousness", True),
    "non-serious": ("seriousness", False),
    "non serious": ("seriousness", False),
    "female": ("gender", "female"),
    "male": ("gender", "male"),
    "women": ("gender", "female"),
    "men": ("gender", "male"),
    "fatal": ("outcome", "fatal"),
    "death": ("outcome", "fatal"),
    "died": ("outcome", "fatal"),
    "hospitalized": ("outcome", "hospitalized"),
    "hospitalization": ("outcome", "hospitalized"),
    "elderly": ("age_group", "elderly"),
    "pediatric": ("age_group", "pediatric"),
    "pediatric": ("age_group", "pediatric"),
    "children": ("age_group", "pediatric"),
    "kids": ("age_group", "pediatric"),
}


# ------------------------------------------------------------
# 🔵 Utility: User goals/intentions
# ------------------------------------------------------------
GOAL_KEYWORDS = {
    "trend": "trend_analysis",
    "trends": "trend_analysis",
    "trending": "trend_analysis",
    "increase": "trend_analysis",
    "increasing": "trend_analysis",
    "decrease": "trend_analysis",
    "decreasing": "trend_analysis",
    "compare": "comparison",
    "comparison": "comparison",
    "compared": "comparison",
    "vs": "comparison",
    "versus": "comparison",
    "summary": "summary",
    "summarize": "summary",
    "summaries": "summary",
    "cases": "case_count",
    "how many": "case_count",
    "count": "case_count",
    "number": "case_count",
}


# ------------------------------------------------------------
# 🔵 Extract drug name from user query
# Integrates with existing query parser for dataset-aware detection
# ------------------------------------------------------------
def extract_drug(
    message: str,
    current_memory: Dict[str, Any],
    normalized_df: Optional[Any] = None
) -> Optional[str]:
    """
    Extract drug name from message, using existing memory or dataset detection.
    
    Args:
        message: User query text
        current_memory: Current memory state
        normalized_df: Optional DataFrame for dataset-aware detection
        
    Returns:
        Drug name (normalized) or None
    """
    # Quick keyword check first
    text = message.lower()
    
    # Common drug mentions (can be expanded)
    drug_aliases = {
        "dupixent": "Dupixent",
        "dupilumab": "Dupixent",
        "paxlovid": "Paxlovid",
        "nirmatrelvir": "Paxlovid",
        "ozempic": "Ozempic",
        "semaglutide": "Ozempic",
        "wegovy": "Wegovy",
    }
    
    for alias, normalized in drug_aliases.items():
        if alias in text:
            return normalized
    
    # Try to use existing query parser to extract drug
    if normalized_df is not None:
        try:
            from src.nl_query_parser import parse_query_to_filters
            filters = parse_query_to_filters(message, normalized_df)
            if filters.get("drug"):
                drug = filters["drug"]
                if isinstance(drug, list):
                    drug = drug[0] if drug else None
                if drug:
                    return str(drug).strip()
        except Exception:
            pass  # Fall back to memory
    
    # Fallback: keep existing memory if nothing new detected
    return current_memory.get("drug")


# ------------------------------------------------------------
# 🔵 Extract reactions (keyword spotting + dataset-aware)
# ------------------------------------------------------------
def extract_reactions(
    message: str,
    current_memory: Dict[str, Any],
    normalized_df: Optional[Any] = None
) -> List[str]:
    """
    Extract reactions from message, merging with existing memory.
    
    Args:
        message: User query text
        current_memory: Current memory state
        normalized_df: Optional DataFrame for dataset-aware detection
        
    Returns:
        List of reactions (deduplicated, merged with memory)
    """
    text = message.lower()
    results = []
    
    # Keyword-based detection
    for r in REACTION_KEYWORDS:
        if r in text:
            results.append(r.capitalize())
    
    # Dataset-aware extraction using existing parser
    if normalized_df is not None:
        try:
            from src.nl_query_parser import parse_query_to_filters
            filters = parse_query_to_filters(message, normalized_df)
            if filters.get("reaction"):
                reaction = filters["reaction"]
                if isinstance(reaction, list):
                    results.extend([str(r).strip() for r in reaction])
                else:
                    results.append(str(reaction).strip())
        except Exception:
            pass
    
    # Merge with existing memory, no duplicates (case-insensitive)
    existing = current_memory.get("reactions", [])
    all_reactions = [r.lower() for r in existing + results]
    
    # Deduplicate while preserving original case from first occurrence
    seen = set()
    final = []
    for r in existing + results:
        r_lower = r.lower()
        if r_lower not in seen:
            seen.add(r_lower)
            final.append(r)
    
    return final


# ------------------------------------------------------------
# 🔵 Extract time window
# ------------------------------------------------------------
def extract_time_window(
    message: str,
    current_memory: Dict[str, Any]
) -> Optional[str]:
    """
    Extract time window from message.
    
    Args:
        message: User query text
        current_memory: Current memory state
        
    Returns:
        Time window code or None
    """
    text = message.lower()
    
    # Check against known patterns
    for phrase, code in TIME_PATTERNS.items():
        if phrase in text:
            return code
    
    # Try to extract year mentions
    year_pattern = r'\b(20\d{2})\b'
    years = re.findall(year_pattern, text)
    if years:
        # Use most recent year mentioned
        return max(years)
    
    # Try relative date patterns
    if "last" in text or "past" in text:
        # Try to extract number + unit
        relative_pattern = r'(?:last|past)\s+(\d+)\s+(month|months|year|years|week|weeks|day|days)'
        match = re.search(relative_pattern, text)
        if match:
            num, unit = match.groups()
            num = int(num)
            if unit.startswith("month"):
                return f"{num}m"
            elif unit.startswith("year"):
                return f"{num * 12}m"
            elif unit.startswith("week"):
                return f"{num}w"
    
    # Fallback: keep existing
    return current_memory.get("time_window")


# ------------------------------------------------------------
# 🔵 Extract filters (serious, gender, age group, outcomes)
# ------------------------------------------------------------
def extract_filters(
    message: str,
    current_memory: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract filter preferences from message, merging with existing filters.
    
    Args:
        message: User query text
        current_memory: Current memory state
        
    Returns:
        Updated filters dictionary
    """
    text = message.lower()
    filters = current_memory.get("filters", {}).copy()
    
    # Check against filter keywords
    for keyword, (field, value) in FILTER_KEYWORDS.items():
        if keyword in text:
            filters[field] = value
    
    # Extract age ranges
    age_pattern = r'age\s+(\d+)[\s\-]+(\d+)'
    age_match = re.search(age_pattern, text)
    if age_match:
        filters["age_min"] = int(age_match.group(1))
        filters["age_max"] = int(age_match.group(2))
    
    # Extract single age threshold
    age_threshold_pattern = r'(?:age|age\s+)(\d+)\+'
    age_threshold = re.search(age_threshold_pattern, text)
    if age_threshold:
        filters["age_min"] = int(age_threshold.group(1))
    
    # Extract country mentions (simple - can be enhanced)
    country_patterns = [
        r'\b(usa|united states|us)\b',
        r'\b(uk|united kingdom|britain)\b',
        r'\b(canada)\b',
        r'\b(japan)\b',
    ]
    for pattern in country_patterns:
        if re.search(pattern, text):
            country_name = re.search(pattern, text).group(1).lower()
            filters["country"] = country_name
            break
    
    return filters


# ------------------------------------------------------------
# 🔵 Extract user intent/goals (trend, comparison, summary)
# ------------------------------------------------------------
def extract_goals(
    message: str,
    current_memory: Dict[str, Any]
) -> List[str]:
    """
    Extract user goals/intentions from message.
    
    Args:
        message: User query text
        current_memory: Current memory state
        
    Returns:
        List of goal strings (deduplicated, merged with memory)
    """
    text = message.lower()
    goals = current_memory.get("user_goals", []).copy()
    
    # Check against goal keywords
    for keyword, goal in GOAL_KEYWORDS.items():
        if keyword in text:
            if goal not in goals:
                goals.append(goal)
    
    # Special patterns for explicit goals
    if "show me" in text or "find" in text or "get" in text:
        if "summary" not in goals:
            goals.append("summary")
    
    if "compare" in text or "vs" in text or "versus" in text:
        if "comparison" not in goals:
            goals.append("comparison")
    
    if "trend" in text or "increasing" in text or "decreasing" in text:
        if "trend_analysis" not in goals:
            goals.append("trend_analysis")
    
    # Deduplicate
    return list(set(goals))


# ------------------------------------------------------------
# 🔵 Extract entities (optional - for future expansion)
# ------------------------------------------------------------
def extract_entities(
    message: str,
    current_memory: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract named entities from message (optional, reserved for future expansion).
    
    Args:
        message: User query text
        current_memory: Current memory state
        
    Returns:
        Entities dictionary (currently empty, extensible)
    """
    # Reserved for future NER or LLM-based entity extraction
    return current_memory.get("entities", {}).copy()


# ------------------------------------------------------------
# 🔵 Build/update conversation summary (rolling)
# ------------------------------------------------------------
def update_summary(
    message: str,
    memory: Dict[str, Any],
    max_length: int = 2000
) -> str:
    """
    Update rolling conversation summary.
    
    Args:
        message: User query text
        memory: Current memory state
        max_length: Maximum summary length (chars)
        
    Returns:
        Updated summary string
    """
    old = memory.get("conversation_summary", "")
    timestamp = datetime.now().strftime("%H:%M")
    
    # Append new message
    new_entry = f"[{timestamp}] User: {message}"
    new_summary = f"{old}\n{new_entry}".strip()
    
    # Truncate if too long (keep most recent)
    if len(new_summary) > max_length:
        # Keep last max_length characters
        new_summary = new_summary[-max_length:]
        # Try to start at a newline
        first_newline = new_summary.find('\n')
        if first_newline > 0:
            new_summary = new_summary[first_newline + 1:]
    
    return new_summary


# ------------------------------------------------------------
# 🔵 Main function: Update memory_state
# ------------------------------------------------------------
def update_memory_state(
    message: str,
    memory: Dict[str, Any],
    normalized_df: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Main function to update memory state from user message.
    
    Args:
        message: User query text
        memory: Current memory state dictionary
        normalized_df: Optional DataFrame for dataset-aware extraction
        
    Returns:
        Updated memory state dictionary
    """
    return {
        "drug": extract_drug(message, memory, normalized_df),
        "reactions": extract_reactions(message, memory, normalized_df),
        "time_window": extract_time_window(message, memory),
        "filters": extract_filters(message, memory),
        "user_goals": extract_goals(message, memory),
        "entities": extract_entities(message, memory),
        "conversation_summary": update_summary(message, memory)
    }

