"""
LLM Query Interpreter for AetherSignal
Converts natural language queries to structured filters using LLM APIs.

Supports:
- OpenAI (GPT-4, GPT-4o-mini)
- Groq (LLaMA-3 70B, Mixtral 8x7B)
- Fallback chain for reliability

Option 3: Hybrid with strict privacy controls
- Only called when user explicitly opts in
- Clear privacy warnings
- Degrades gracefully if API unavailable
"""

from typing import Dict, Optional, List
import os
import json
import pandas as pd
from src.utils import normalize_text


def interpret_query_with_llm(
    query: str,
    normalized_df: Optional[pd.DataFrame] = None,
    provider: str = "openai"
) -> Optional[Dict]:
    """
    Interpret natural language query using LLM and return structured filters.
    
    Args:
        query: Natural language query string
        normalized_df: Optional DataFrame for context (drug/reaction names)
        provider: "openai" or "groq"
        
    Returns:
        Filter dictionary or None if interpretation fails
    """
    # Get available drugs/reactions for context
    context = _build_dataset_context(normalized_df)
    
    # Try provider in order: specified -> OpenAI -> Groq
    providers = [provider]
    if provider == "openai":
        providers.extend(["groq"])
    else:
        providers.extend(["openai"])
    
    for prov in providers:
        try:
            if prov == "openai":
                result = _interpret_with_openai(query, context)
            elif prov == "groq":
                result = _interpret_with_groq(query, context)
            else:
                continue
                
            if result:
                return result
        except Exception:
            continue
    
    return None


def _build_dataset_context(normalized_df: Optional[pd.DataFrame]) -> Dict:
    """Build context from dataset (top drugs/reactions) for LLM."""
    context = {"drugs": [], "reactions": []}
    
    if normalized_df is None or normalized_df.empty:
        return context
    
    # Get top 20 drugs for context
    if 'drug_name' in normalized_df.columns:
        drug_series = normalized_df['drug_name'].astype(str).str.split('; ').explode()
        top_drugs = drug_series.value_counts().head(20).index.tolist()
        context["drugs"] = [str(d) for d in top_drugs]
    
    # Get top 20 reactions for context
    if 'reaction' in normalized_df.columns:
        reaction_series = normalized_df['reaction'].astype(str).str.split('; ').explode()
        top_reactions = reaction_series.value_counts().head(20).index.tolist()
        context["reactions"] = [str(r) for r in top_reactions]
    
    return context


def _interpret_with_openai(query: str, context: Dict) -> Optional[Dict]:
    """Interpret query using OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=10.0)
    except Exception:
        return None
    
    # Build prompt with context
    context_text = ""
    if context.get("drugs"):
        context_text += f"Available drugs in dataset: {', '.join(context['drugs'][:10])}\n"
    if context.get("reactions"):
        context_text += f"Available reactions in dataset: {', '.join(context['reactions'][:10])}\n"
    
    system_prompt = """You are a pharmacovigilance query parser. Convert natural language safety queries into structured JSON filters.

Return ONLY valid JSON with this structure:
{
  "drug": "drug_name" or ["drug1", "drug2"] for multiple,
  "reaction": "reaction_name" or ["reaction1", "reaction2"] for multiple,
  "reaction_logic": "OR" or "AND",
  "age_min": number or null,
  "age_max": number or null,
  "sex": "M" or "F" or null,
  "country": "country_name" or null,
  "seriousness": true or false or null,
  "date_from": "YYYY-MM-DD" or null,
  "date_to": "YYYY-MM-DD" or null,
  "exclude_reaction": ["reaction"] or null
}

Rules:
- Extract drug names (brand or generic)
- Extract reactions/adverse events
- Parse age ranges (e.g., "age 30-60" → age_min: 30, age_max: 60)
- Parse dates (e.g., "since 2022" → date_from: "2022-01-01")
- Multiple reactions default to OR unless "and" is explicit
- Return null for missing fields
- Use dataset context to match drug/reaction names accurately"""

    user_prompt = f"""Query: {query}

{context_text if context_text else ""}

Extract filters and return JSON only (no explanation):"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective, fast
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.1,  # Low temperature for deterministic parsing
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        content = response.choices[0].message.content
        if content:
            filters = json.loads(content)
            # Clean and validate filters
            return _clean_llm_filters(filters)
    except Exception:
        pass
    
    return None


def _interpret_with_groq(query: str, context: Dict) -> Optional[Dict]:
    """Interpret query using Groq API (fast, cheap)."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key, timeout=10.0)
    except Exception:
        return None
    
    # Same prompt structure as OpenAI
    context_text = ""
    if context.get("drugs"):
        context_text += f"Available drugs: {', '.join(context['drugs'][:10])}\n"
    if context.get("reactions"):
        context_text += f"Available reactions: {', '.join(context['reactions'][:10])}\n"
    
    system_prompt = """You are a pharmacovigilance query parser. Convert queries to JSON filters.

Return ONLY JSON:
{
  "drug": "name" or ["name1", "name2"],
  "reaction": "name" or ["name1", "name2"],
  "reaction_logic": "OR" or "AND",
  "age_min": number or null,
  "age_max": number or null,
  "sex": "M" or "F" or null,
  "country": "name" or null,
  "seriousness": true or false or null,
  "date_from": "YYYY-MM-DD" or null,
  "date_to": "YYYY-MM-DD" or null,
  "exclude_reaction": ["name"] or null
}"""

    user_prompt = f"Query: {query}\n{context_text if context_text else ''}\n\nExtract filters as JSON:"

    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # Fast, capable
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            filters = json.loads(content)
            return _clean_llm_filters(filters)
    except Exception:
        pass
    
    return None


def _clean_llm_filters(filters: Dict) -> Dict:
    """Clean and validate LLM-generated filters."""
    cleaned = {}
    
    # Valid filter keys
    valid_keys = [
        'drug', 'reaction', 'reaction_logic', 'age_min', 'age_max',
        'sex', 'country', 'seriousness', 'date_from', 'date_to', 'exclude_reaction'
    ]
    
    for key in valid_keys:
        if key in filters:
            value = filters[key]
            # Convert null/None to None
            if value is None or value == "null" or value == "":
                continue
            
            # Type validation
            if key in ['age_min', 'age_max']:
                try:
                    cleaned[key] = int(value)
                except (ValueError, TypeError):
                    continue
            elif key == 'seriousness':
                cleaned[key] = bool(value) if value else None
            elif key == 'sex':
                if value in ['M', 'F', 'm', 'f']:
                    cleaned[key] = value.upper()
            elif key == 'reaction_logic':
                if value in ['OR', 'AND', 'or', 'and']:
                    cleaned[key] = value.upper()
            else:
                # String or list
                if isinstance(value, list):
                    cleaned[key] = [str(v) for v in value if v]
                else:
                    cleaned[key] = str(value) if value else None
    
    return cleaned

