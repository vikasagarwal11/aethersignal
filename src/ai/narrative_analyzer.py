"""
Case Narrative Analysis for AetherSignal
Extracts structured data from free-text case narratives using LLM.

Features:
- Extract drugs, reactions, dates from narratives
- Summarize case narratives
- Identify missing information
- Flag inconsistencies
"""

from typing import Dict, List, Optional
import json
import pandas as pd
from src.ai.medical_llm import call_medical_llm


def analyze_case_narrative(
    narrative: str,
    existing_data: Optional[Dict] = None,
    use_llm: bool = True
) -> Dict:
    """
    Analyze case narrative and extract structured information.
    
    Args:
        narrative: Free-text case narrative
        existing_data: Optional existing structured data (for comparison)
        use_llm: Whether to use LLM for extraction
        
    Returns:
        Dictionary with extracted information and analysis
    """
    if not narrative or len(narrative.strip()) < 20:
        return {
            'extracted_data': {},
            'summary': None,
            'missing_info': [],
            'inconsistencies': [],
            'confidence': 0.0
        }
    
    result = {
        'extracted_data': {},
        'summary': None,
        'missing_info': [],
        'inconsistencies': [],
        'confidence': 0.0
    }
    
    if use_llm:
        # Extract structured data
        extracted = _extract_structured_data(narrative, existing_data)
        result['extracted_data'] = extracted
        
        # Generate summary
        result['summary'] = _summarize_narrative(narrative)
        
        # Identify missing information
        result['missing_info'] = _identify_missing_info(narrative, existing_data)
        
        # Check for inconsistencies
        if existing_data:
            result['inconsistencies'] = _check_inconsistencies(extracted, existing_data)
        
        # Calculate confidence based on extraction quality
        result['confidence'] = _calculate_extraction_confidence(extracted, narrative)
    
    return result


def _extract_structured_data(narrative: str, existing_data: Optional[Dict]) -> Dict:
    """Extract structured data from narrative."""
    system_prompt = """You are a pharmacovigilance case analyst. Extract structured information 
from case narratives. Return ONLY valid JSON:

{
  "drugs": ["drug1", "drug2"],
  "reactions": ["reaction1", "reaction2"],
  "age": number or null,
  "sex": "M" or "F" or null,
  "dates": {
    "onset": "YYYY-MM-DD" or null,
    "report": "YYYY-MM-DD" or null
  },
  "outcome": "recovered" or "recovering" or "not recovered" or "fatal" or null,
  "seriousness": true or false or null,
  "dose": "dose amount and unit" or null,
  "route": "oral" or "injection" etc. or null
}

Extract only information explicitly mentioned. Use null for missing fields."""
    
    prompt = f"""Extract structured data from this case narrative:

{narrative}

Return JSON only:"""
    
    try:
        response = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="narrative_analysis",
            max_tokens=300,
            temperature=0.1,
        )
        
        if response:
            # Try to parse JSON from response
            # Remove markdown code blocks if present
            response_clean = response.strip()
            if response_clean.startswith("```"):
                response_clean = response_clean.split("```")[1]
                if response_clean.startswith("json"):
                    response_clean = response_clean[4:]
            response_clean = response_clean.strip()
            
            extracted = json.loads(response_clean)
            return extracted
    except Exception:
        pass
    
    return {}


def _summarize_narrative(narrative: str) -> Optional[str]:
    """Generate concise summary of case narrative."""
    system_prompt = """You are a pharmacovigilance expert. Summarize case narratives in 2-3 sentences.
Focus on:
1. Patient demographics (if mentioned)
2. Drug(s) involved
3. Reaction(s) experienced
4. Outcome (if mentioned)
5. Timeline (if clear)

Be concise and factual."""
    
    prompt = f"""Summarize this case narrative:

{narrative}

Provide a 2-3 sentence summary:"""
    
    return call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="narrative_analysis",
        max_tokens=150,
        temperature=0.2
    )


def _identify_missing_info(narrative: str, existing_data: Optional[Dict]) -> List[str]:
    """Identify missing critical information."""
    system_prompt = """You are a pharmacovigilance case reviewer. Identify missing critical information 
in case narratives. Common missing items:
- Drug name
- Reaction details
- Patient age/sex
- Dates (onset, report)
- Outcome
- Dose/route

Return as a simple list, one item per line."""
    
    prompt = f"""Case narrative:
{narrative}

What critical information is missing? List items one per line:"""
    
    response = call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="narrative_analysis",
        max_tokens=200,
        temperature=0.1
    )
    
    if response:
        # Parse list items
        missing = [line.strip("- •").strip() for line in response.split("\n") if line.strip()]
        return missing[:10]  # Limit to 10 items
    
    return []


def _check_inconsistencies(extracted: Dict, existing: Dict) -> List[str]:
    """Check for inconsistencies between extracted and existing data."""
    inconsistencies = []
    
    # Check drugs
    if 'drugs' in extracted and 'drug_name' in existing:
        extracted_drugs = [d.lower() for d in extracted.get('drugs', [])]
        existing_drug = str(existing.get('drug_name', '')).lower()
        if extracted_drugs and existing_drug:
            # Check if drugs match
            if not any(ext_drug in existing_drug or existing_drug in ext_drug for ext_drug in extracted_drugs):
                inconsistencies.append(f"Drug mismatch: narrative mentions {', '.join(extracted['drugs'])}, but structured data has {existing.get('drug_name')}")
    
    # Check reactions
    if 'reactions' in extracted and 'reaction' in existing:
        extracted_reactions = [r.lower() for r in extracted.get('reactions', [])]
        existing_reaction = str(existing.get('reaction', '')).lower()
        if extracted_reactions and existing_reaction:
            if not any(ext_rxn in existing_reaction or existing_reaction in ext_rxn for ext_rxn in extracted_reactions):
                inconsistencies.append(f"Reaction mismatch: narrative mentions {', '.join(extracted['reactions'])}, but structured data has {existing.get('reaction')}")
    
    # Check age
    if 'age' in extracted and 'age' in existing:
        extracted_age = extracted.get('age')
        existing_age = existing.get('age')
        if extracted_age and existing_age:
            try:
                existing_age_num = float(str(existing_age).split()[0]) if isinstance(existing_age, str) else float(existing_age)
                if abs(extracted_age - existing_age_num) > 5:
                    inconsistencies.append(f"Age mismatch: narrative suggests {extracted_age}, structured data has {existing_age}")
            except (ValueError, TypeError):
                pass
    
    return inconsistencies


def _calculate_extraction_confidence(extracted: Dict, narrative: str) -> float:
    """Calculate confidence in extraction (0-1)."""
    confidence = 0.0
    
    # Base confidence from what was extracted
    if extracted.get('drugs'):
        confidence += 0.3
    if extracted.get('reactions'):
        confidence += 0.3
    if extracted.get('age'):
        confidence += 0.1
    if extracted.get('sex'):
        confidence += 0.1
    if extracted.get('dates', {}).get('onset'):
        confidence += 0.1
    if extracted.get('outcome'):
        confidence += 0.1
    
    return min(confidence, 1.0)


def batch_analyze_narratives(
    df: pd.DataFrame,
    narrative_column: str = "narrative",
    use_llm: bool = True,
    limit: int = 100
) -> pd.DataFrame:
    """
    Analyze narratives for multiple cases.
    
    Args:
        df: DataFrame with case data
        narrative_column: Column name containing narratives
        use_llm: Whether to use LLM
        limit: Maximum number of cases to analyze (for cost control)
        
    Returns:
        DataFrame with extracted data added as new columns
    """
    if narrative_column not in df.columns:
        return df
    
    result_df = df.copy()
    
    # Analyze narratives (limit for cost control)
    narratives_to_analyze = df[narrative_column].dropna().head(limit)
    
    extracted_data_list = []
    for idx, narrative in narratives_to_analyze.items():
        existing = df.loc[idx].to_dict() if idx in df.index else {}
        analysis = analyze_case_narrative(str(narrative), existing, use_llm=use_llm)
        extracted_data_list.append((idx, analysis))
    
    # Add extracted data as new columns
    for idx, analysis in extracted_data_list:
        extracted = analysis.get('extracted_data', {})
        if extracted.get('drugs'):
            result_df.loc[idx, 'narrative_drugs'] = '; '.join(extracted['drugs'])
        if extracted.get('reactions'):
            result_df.loc[idx, 'narrative_reactions'] = '; '.join(extracted['reactions'])
        if extracted.get('age'):
            result_df.loc[idx, 'narrative_age'] = extracted['age']
        if extracted.get('sex'):
            result_df.loc[idx, 'narrative_sex'] = extracted['sex']
        if analysis.get('summary'):
            result_df.loc[idx, 'narrative_summary'] = analysis['summary']
        if analysis.get('missing_info'):
            result_df.loc[idx, 'narrative_missing'] = '; '.join(analysis['missing_info'][:5])
    
    return result_df

