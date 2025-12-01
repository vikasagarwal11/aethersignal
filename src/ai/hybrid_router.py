"""
Hybrid Query Router for AetherSignal
Routes queries between rule-based parser and LLM interpreter with privacy controls.

Option 3: Hybrid with strict privacy controls
- Rule-based parser is primary (always runs first)
- LLM only used as fallback when confidence is low
- User must explicitly opt-in to LLM features
- Clear privacy warnings
"""

from typing import Dict, Optional, Tuple
import pandas as pd
from src import nl_query_parser


def route_query(
    query: str,
    normalized_df: Optional[pd.DataFrame],
    use_llm: bool = False,
    llm_confidence_threshold: float = 0.6
) -> Tuple[Dict, str, float]:
    """
    Route query through rule-based parser first, optionally fallback to LLM.
    
    Args:
        query: Natural language query string
        normalized_df: Normalized DataFrame for context-aware detection
        use_llm: Whether LLM fallback is enabled (user opt-in)
        llm_confidence_threshold: Minimum confidence to skip LLM (0-1)
        
    Returns:
        Tuple of (filters_dict, method_used, confidence_score)
        - filters_dict: Parsed filter dictionary
        - method_used: "rule_based" or "llm_fallback"
        - confidence_score: Confidence in parsing (0-1)
    """
    # Always try rule-based first
    filters = nl_query_parser.parse_query_to_filters(query, normalized_df)
    
    # Calculate confidence based on what was extracted
    confidence = _calculate_confidence(filters, query, normalized_df)
    
    # If confidence is high enough, return rule-based result
    if confidence >= llm_confidence_threshold:
        return filters, "rule_based", confidence
    
    # If confidence is low AND user opted in to LLM, try LLM fallback
    if use_llm and confidence < llm_confidence_threshold:
        try:
            from src.ai.llm_interpreter import interpret_query_with_llm
            llm_filters = interpret_query_with_llm(query, normalized_df)
            if llm_filters and _has_valid_filters(llm_filters):
                return llm_filters, "llm_fallback", 0.8  # LLM gets higher confidence
        except Exception:
            # If LLM fails, return rule-based result anyway
            pass
    
    # Return rule-based result (even if low confidence)
    return filters, "rule_based", confidence


def _calculate_confidence(filters: Dict, query: str, normalized_df: Optional[pd.DataFrame]) -> float:
    """
    Calculate confidence score for rule-based parsing (0-1).
    
    Higher confidence if:
    - Explicit keywords found ("drug", "reaction")
    - Multiple filters extracted
    - Terms found in dataset
    - Query structure is clear
    """
    confidence = 0.0
    
    # Base confidence from explicit keywords
    query_lower = query.lower()
    has_explicit_drug = any(kw in query_lower for kw in ['drug', 'medication', 'product', 'substance'])
    has_explicit_reaction = any(kw in query_lower for kw in ['reaction', 'adverse event', 'ae', 'event', 'adr', 'side effect'])
    
    if has_explicit_drug:
        confidence += 0.3
    if has_explicit_reaction:
        confidence += 0.3
    
    # Confidence from extracted filters
    if 'drug' in filters:
        confidence += 0.2
    if 'reaction' in filters:
        confidence += 0.2
    
    # Bonus if multiple filters extracted (shows parser understood query well)
    filter_count = len([k for k in filters.keys() if k not in ['reaction_logic']])
    if filter_count >= 3:
        confidence += 0.1
    
    # Bonus if terms found in dataset (context-aware detection worked)
    if normalized_df is not None and not normalized_df.empty:
        if 'drug' in filters:
            drug = filters['drug'] if isinstance(filters['drug'], str) else filters['drug'][0]
            if _term_in_dataset(drug, normalized_df, 'drug_name'):
                confidence += 0.1
        if 'reaction' in filters:
            reaction = filters['reaction'] if isinstance(filters['reaction'], str) else filters['reaction'][0]
            if _term_in_dataset(reaction, normalized_df, 'reaction'):
                confidence += 0.1
    
    return min(confidence, 1.0)


def _term_in_dataset(term: str, df: pd.DataFrame, column: str) -> bool:
    """Check if term exists in dataset column."""
    if column not in df.columns:
        return False
    series = df[column].astype(str).str.split('; ').explode()
    normalized_series = series.apply(lambda x: x.lower() if pd.notna(x) else '')
    term_lower = term.lower()
    return any(term_lower in val for val in normalized_series if val)


def _has_valid_filters(filters: Dict) -> bool:
    """Check if filters dictionary has meaningful content."""
    if not filters:
        return False
    # Check if at least one meaningful filter exists
    meaningful_keys = ['drug', 'reaction', 'age_min', 'age_max', 'sex', 'country', 'seriousness', 'date_from', 'date_to']
    return any(k in filters for k in meaningful_keys)


def run_hybrid_rpf(
    df: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
    mode: str = "auto"
) -> List[Dict[str, Any]]:
    """
    Run hybrid RPF (Risk Prioritization Framework) calculation.
    
    Automatically selects local or server engine based on:
    - Dataset size
    - Browser capabilities
    - User preference
    
    Args:
        df: Safety data DataFrame
        weights: RPF component weights (optional)
        mode: Processing mode ("auto", "local", "server")
        
    Returns:
        List of RPF results sorted by score
    """
    try:
        # Local engine
        if mode == "local":
            from src.local_engine.local_rpf_engine import LocalRPFEngine
            engine = LocalRPFEngine(weights)
            return engine.compute(df)
        
        # Server engine
        if mode == "server":
            try:
                from src.ai.risk_prioritization import RiskPrioritizationEngine
                engine = RiskPrioritizationEngine()
                # Convert server engine format if needed
                return engine.compute_rpf_scores(df, weights)
            except Exception:
                # Fallback to local if server unavailable
                from src.local_engine.local_rpf_engine import LocalRPFEngine
                engine = LocalRPFEngine(weights)
                return engine.compute(df)
        
        # AUTO MODE - intelligent selection
        try:
            import streamlit as st
            
            # Check browser capabilities
            browser_caps = st.session_state.get("browser_capabilities", {})
            wasm_available = browser_caps.get("wasm_supported", False) if isinstance(browser_caps, dict) else False
            
            # Check dataset profile
            dataset_profile = st.session_state.get("dataset_profile", {})
            size_mb = dataset_profile.get("file_size_mb", 0) if isinstance(dataset_profile, dict) else 0
            
            # Decision: use local if WASM available and dataset < 150MB
            if wasm_available and size_mb <= 150 and len(df) < 2_000_000:
                from src.local_engine.local_rpf_engine import LocalRPFEngine
                engine = LocalRPFEngine(weights)
                return engine.compute(df)
            else:
                # Use server engine
                try:
                    from src.ai.risk_prioritization import RiskPrioritizationEngine
                    engine = RiskPrioritizationEngine()
                    return engine.compute_rpf_scores(df, weights)
                except Exception:
                    # Fallback to local
                    from src.local_engine.local_rpf_engine import LocalRPFEngine
                    engine = LocalRPFEngine(weights)
                    return engine.compute(df)
        except Exception:
            # Safe fallback to local
            from src.local_engine.local_rpf_engine import LocalRPFEngine
            engine = LocalRPFEngine(weights)
            return engine.compute(df)
            
    except Exception as e:
        # Ultimate fallback
        return [{
            "error": str(e),
            "drug": "Error",
            "reaction": "Error",
            "rpf": 0.0,
            "priority": "Unknown"
        }]
