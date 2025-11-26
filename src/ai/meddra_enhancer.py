"""
Enhanced MedDRA Mapping for AetherSignal
Uses LLM to improve reaction term mapping to MedDRA Preferred Terms.

Enhances existing hand-crafted dictionary with:
- Context-aware mapping
- Synonym expansion
- Colloquial term mapping
"""

from typing import Optional, List
import json
from src.utils import map_to_meddra_pt, normalize_text
from src.ai.medical_llm import call_medical_llm


def map_to_meddra_enhanced(
    term: str,
    context: Optional[str] = None,
    use_llm: bool = True
) -> str:
    """
    Map reaction term to MedDRA PT with LLM enhancement.
    
    Args:
        term: Reaction term to map
        context: Optional context (e.g., "eye problems with Dupixent")
        use_llm: Whether to use LLM for mapping
        
    Returns:
        MedDRA Preferred Term
    """
    # First try existing dictionary mapping
    meddra_pt = map_to_meddra_pt(term)
    
    # If we got a good match (not just title-cased original), return it
    if meddra_pt.lower() != normalize_text(term):
        return meddra_pt
    
    # If dictionary didn't find a good match and LLM is enabled, try LLM
    if use_llm and len(term) >= 4:
        llm_mapping = _map_with_llm(term, context)
        if llm_mapping and llm_mapping.lower() != normalize_text(term):
            return llm_mapping
    
    # Fallback to dictionary result
    return meddra_pt


def _map_with_llm(term: str, context: Optional[str]) -> Optional[str]:
    """Map term using LLM."""
    system_prompt = """You are a pharmacovigilance expert mapping reaction terms to MedDRA Preferred Terms (PTs).

Common MedDRA PTs include:
- Pyrexia (fever)
- Alopecia (hair loss)
- Nausea, Vomiting
- Diarrhoea
- Headache
- Fatigue
- Rash
- Conjunctivitis (eye inflammation)
- Pancreatitis
- Suicidal ideation
- Depression, Anxiety
- And thousands more...

Return ONLY the MedDRA Preferred Term (standard medical term), not the colloquial term.
If unsure, return the term in proper medical format (title case)."""
    
    prompt = f"""Map this reaction term to MedDRA Preferred Term:

Term: "{term}"
"""
    
    if context:
        prompt += f"Context: {context}\n"
    
    prompt += "\nReturn the MedDRA Preferred Term only (no explanation):"
    
    response = call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="meddra_mapping",  # Uses GPT-4o-mini (cost-effective)
        max_tokens=50,
        temperature=0.1
    )
    
    if response:
        # Clean response - remove quotes, extra text
        cleaned = response.strip().strip('"').strip("'")
        # Take first line if multiple lines
        cleaned = cleaned.split("\n")[0].strip()
        # Remove common prefixes
        for prefix in ["MedDRA PT:", "Preferred Term:", "PT:", "Term:"]:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        if len(cleaned) > 2:
            return cleaned.title()  # Title case for consistency
    
    return None


def expand_reaction_synonyms(term: str, use_llm: bool = True) -> List[str]:
    """
    Get synonyms/variations for a reaction term.
    Useful for finding related terms in queries.
    
    Args:
        term: Reaction term
        use_llm: Whether to use LLM
        
    Returns:
        List of synonyms/variations
    """
    # First check if we have it in dictionary
    meddra_pt = map_to_meddra_pt(term)
    
    if not use_llm:
        return [meddra_pt] if meddra_pt else [term]
    
    system_prompt = """You are a pharmacovigilance expert. Generate synonyms and variations 
for medical reaction terms. Return a JSON array of related terms."""
    
    prompt = f"""Generate synonyms and variations for this reaction term: "{term}"

Include:
- Medical synonyms
- Common variations
- Related terms
- Abbreviations (if common)

Return as JSON array: ["term1", "term2", ...]"""
    
    response = call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="meddra_mapping",
        max_tokens=200,
        temperature=0.2
    )
    
    if response:
        try:
            # Try to parse JSON array
            response_clean = response.strip()
            if response_clean.startswith("```"):
                response_clean = response_clean.split("```")[1]
                if response_clean.startswith("json"):
                    response_clean = response_clean[4:]
            response_clean = response_clean.strip()
            
            synonyms = json.loads(response_clean)
            if isinstance(synonyms, list):
                # Add original term and MedDRA PT
                result = [term, meddra_pt] if meddra_pt != term else [term]
                result.extend([s for s in synonyms if s and s not in result])
                return result[:10]  # Limit to 10
        except Exception:
            pass
    
    return [meddra_pt] if meddra_pt else [term]

