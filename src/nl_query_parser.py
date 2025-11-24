"""
Natural Language Query Parser for AetherSignal
Converts natural language queries to filter dictionaries.
"""

import re
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from src.utils import parse_date, extract_age, normalize_text


def detect_negations(query: str) -> List[str]:
    """
    Detect negated reactions in natural language query.
    
    Args:
        query: Natural language query string
        
    Returns:
        List of negated reaction terms to exclude
    """
    query_lower = query.lower()
    negated_reactions = []
    
    # Negation patterns - look for "no X", "not X", "without X", "excluding X"
    negation_patterns = [
        # "no X" or "no reaction X"
        r'(?:no|not)[\s]+(?:reaction|adverse event|ae|event|adr|side effect)[\s:]+([a-z0-9\s\-]+?)(?:\.|,|$|\s+and|\s+or)',
        r'(?:no|not)[\s]+([a-z0-9\s\-]+?)(?:\s+reaction|\s+event|\s+ae|\.|,|$)',
        # "without X" or "excluding X"
        r'(?:without|excluding|except|exclude)[\s]+([a-z0-9\s\-]+?)(?:\.|,|$|\s+and|\s+or)',
        r'(?:without|excluding)[\s]+(?:reaction|adverse event|ae|event)[\s:]+([a-z0-9\s\-]+?)(?:\.|,|$|\s+and|\s+or)',
        # "but no X" or "but not X"
        r'but[\s]+(?:no|not)[\s]+([a-z0-9\s\-]+?)(?:\.|,|$|\s+and|\s+or)',
    ]
    
    for pattern in negation_patterns:
        matches = re.findall(pattern, query_lower, re.IGNORECASE)
        for match in matches:
            reaction = match.strip()
            # Filter out common stop words and short terms
            if len(reaction) > 2 and reaction not in ['the', 'all', 'any', 'for', 'with', 'but', 'and', 'or']:
                # Clean up trailing location words (e.g., "in Japan")
                reaction = re.sub(r'\s+in\s+[a-z\s]+$', '', reaction).strip()
                if reaction and reaction not in negated_reactions:
                    negated_reactions.append(reaction)
    
    return negated_reactions


def parse_query_to_filters(query: str) -> Dict:
    """
    Parse natural language query to filter dictionary.
    
    Args:
        query: Natural language query string
        
    Returns:
        Dictionary with filter keys: drug, reaction, age_min, age_max, 
        sex, country, seriousness, date_from, date_to, exclude_reaction
    """
    query_lower = query.lower()
    filters = {}
    
    # Extract drug names
    drug_patterns = [
        r'(?:drug|medication|product|substance)[\s:]+([a-z0-9\s\-]+?)(?:\.|,|$|\s+and|\s+or)',
        r'(?:show|find|search|filter|cases with|reports for)[\s]+([a-z0-9\s\-]+?)(?:\s+and|\s+or|\.|,|$)',
        r'^([a-z0-9\s\-]+?)(?:\s+and|\s+or|\s+reaction|\s+event)',
    ]
    
    drugs = []
    for pattern in drug_patterns:
        matches = re.findall(pattern, query_lower, re.IGNORECASE)
        for match in matches:
            drug = match.strip()
            if len(drug) > 2 and drug not in ['the', 'all', 'any', 'for', 'with']:
                drugs.append(drug)
    
    if drugs:
        filters['drug'] = drugs[0] if len(drugs) == 1 else drugs
    
    # Extract reactions/adverse events
    # Strategy: Find all "reaction X" patterns, then extract the reaction term
    # Use lookahead to stop at next keyword, but be smart about "drug" in reaction names
    reactions = []
    
    # Find all positions where "reaction" keyword appears
    reaction_keyword_pattern = r'\b(?:reaction|adverse event|ae|event|adr|side effect)\b'
    reaction_positions = []
    for match in re.finditer(reaction_keyword_pattern, query_lower, re.IGNORECASE):
        reaction_positions.append(match.end())
    
    # Extract reaction terms after each "reaction" keyword
    for pos in reaction_positions:
        # Get text after "reaction" keyword
        remaining_text = query_lower[pos:]
        # Find where the next keyword starts
        # Look for "reaction", "drug" (as keyword, not part of reaction name), "and", "or", or end
        # Pattern: word boundary before "drug" to avoid matching "Drug ineffective"
        next_keyword_match = re.search(r'\s+(?:reaction|adverse event|ae|event|adr|side effect)\b|\s+\bdrug\b(?!\s+[a-z])|\s+(?:and|or)\b|\.|,|$', remaining_text, re.IGNORECASE)
        if next_keyword_match:
            reaction_text = remaining_text[:next_keyword_match.start()].strip()
            # Clean up the reaction text
            reaction_text = re.sub(r'^[\s:]+', '', reaction_text)  # Remove leading colons/spaces
            reaction_text = re.sub(r'\s+$', '', reaction_text)  # Remove trailing spaces
            # Filter out empty or very short terms
            if len(reaction_text) > 2 and reaction_text not in ['the', 'all', 'any', 'for', 'with']:
                reactions.append(reaction_text)
    
    # Deduplicate reactions (case-insensitive)
    seen = set()
    unique_reactions = []
    for r in reactions:
        r_lower = r.lower()
        if r_lower not in seen:
            seen.add(r_lower)
            unique_reactions.append(r)
    
    # Detect AND vs OR logic for multiple reactions
    # Default to OR (matches any), but check for explicit AND
    reaction_logic = "OR"  # Default
    if unique_reactions and len(unique_reactions) > 1:
        # Check if query explicitly uses "and" between reactions
        # Look for pattern like "reaction X and reaction Y" or "reaction X, reaction Y" (comma often implies AND)
        reaction_section = query_lower
        # Find the section with reactions
        reaction_indices = []
        for r in unique_reactions:
            idx = reaction_section.find(r.lower())
            if idx != -1:
                reaction_indices.append((idx, r))
        
        if len(reaction_indices) >= 2:
            # Check text between reactions
            reaction_indices.sort()
            between_text = reaction_section[reaction_indices[0][0] + len(reaction_indices[0][1]):reaction_indices[1][0]]
            # If "and" is found between reactions (not "or"), use AND logic
            if re.search(r'\band\b', between_text, re.IGNORECASE) and not re.search(r'\bor\b', between_text, re.IGNORECASE):
                reaction_logic = "AND"
    
    if unique_reactions:
        filters['reaction'] = unique_reactions[0] if len(unique_reactions) == 1 else unique_reactions
        if len(unique_reactions) > 1:
            filters['reaction_logic'] = reaction_logic  # Store AND/OR logic
    
    # Extract negated reactions (exclusions)
    negated_reactions = detect_negations(query)
    if negated_reactions:
        filters['exclude_reaction'] = negated_reactions
    
    # Extract age range
    age_patterns = [
        r'age[\s:]+(\d+)[\s-]+(\d+)',
        r'age[\s:]+(\d+)',
        r'(\d+)[\s-]+(\d+)[\s]+years?',
        r'(\d+)[\s]+years?',
        r'age[\s]+(?:between|from)[\s]+(\d+)[\s]+(?:and|to)[\s]+(\d+)',
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, query_lower)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                filters['age_min'] = int(groups[0])
                filters['age_max'] = int(groups[1])
            elif len(groups) == 1:
                age_val = int(groups[0])
                if age_val < 18:
                    filters['age_max'] = age_val
                else:
                    filters['age_min'] = age_val
            break
    
    # Extract sex/gender
    if re.search(r'\b(male|man|men|m\b)', query_lower):
        filters['sex'] = 'M'
    elif re.search(r'\b(female|woman|women|f\b)', query_lower):
        filters['sex'] = 'F'
    
    # Extract country
    country_patterns = [
        r'country[\s:]+([a-z\s]+?)(?:\.|,|$|\s+and)',
        r'in[\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    ]
    
    for pattern in country_patterns:
        match = re.search(pattern, query_lower)
        if match:
            country = match.group(1).strip()
            if len(country) > 2:
                filters['country'] = country
            break
    
    # Extract seriousness
    if re.search(r'\b(serious|severe|life.?threatening|death|fatal)\b', query_lower):
        filters['seriousness'] = True
    
    # Extract date ranges
    date_patterns = [
        r'(?:from|since|after)[\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'(?:before|until|by)[\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})[\s]+(?:to|until)[\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'(\d{4})',
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            if isinstance(matches[0], tuple):
                filters['date_from'] = matches[0][0]
                filters['date_to'] = matches[0][1]
            else:
                date_str = matches[0]
                parsed_date = parse_date(date_str)
                if parsed_date:
                    if 'from' in query_lower or 'since' in query_lower or 'after' in query_lower:
                        filters['date_from'] = date_str
                    elif 'before' in query_lower or 'until' in query_lower or 'by' in query_lower:
                        filters['date_to'] = date_str
            break
    
    # Year-only patterns
    year_match = re.search(r'\b(19|20)\d{2}\b', query_lower)
    if year_match and 'date_from' not in filters and 'date_to' not in filters:
        year = int(year_match.group(0))
        filters['date_from'] = f'{year}-01-01'
        filters['date_to'] = f'{year}-12-31'
    
    return filters


def filters_to_natural_language(filters: Dict) -> str:
    """
    Convert filter dictionary back to natural language query.
    
    Args:
        filters: Filter dictionary
        
    Returns:
        Natural language query string
    """
    parts = []
    
    if 'drug' in filters:
        drug = filters['drug']
        if isinstance(drug, list):
            parts.append(f"drugs: {', '.join(drug)}")
        else:
            parts.append(f"drug: {drug}")
    
    if 'reaction' in filters:
        reaction = filters['reaction']
        if isinstance(reaction, list):
            parts.append(f"reactions: {', '.join(reaction)}")
        else:
            parts.append(f"reaction: {reaction}")
    
    if 'age_min' in filters or 'age_max' in filters:
        if 'age_min' in filters and 'age_max' in filters:
            parts.append(f"age: {filters['age_min']}-{filters['age_max']} years")
        elif 'age_min' in filters:
            parts.append(f"age: >= {filters['age_min']} years")
        elif 'age_max' in filters:
            parts.append(f"age: <= {filters['age_max']} years")
    
    if 'sex' in filters:
        parts.append(f"sex: {filters['sex']}")
    
    if 'country' in filters:
        parts.append(f"country: {filters['country']}")
    
    if 'seriousness' in filters and filters['seriousness']:
        parts.append("serious cases only")
    
    if 'exclude_reaction' in filters:
        excluded = filters['exclude_reaction']
        if isinstance(excluded, list):
            parts.append(f"excluding: {', '.join(excluded)}")
        else:
            parts.append(f"excluding: {excluded}")
    
    if 'date_from' in filters or 'date_to' in filters:
        date_range = []
        if 'date_from' in filters:
            date_range.append(f"from {filters['date_from']}")
        if 'date_to' in filters:
            date_range.append(f"until {filters['date_to']}")
        parts.append(" ".join(date_range))
    
    if not parts:
        return "No filters applied"
    
    return " | ".join(parts)


def validate_filters(filters: Dict) -> Tuple[bool, Optional[str]]:
    """
    Validate filter dictionary.
    
    Args:
        filters: Filter dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if 'age_min' in filters and 'age_max' in filters:
        if filters['age_min'] > filters['age_max']:
            return False, "Minimum age cannot be greater than maximum age"
    
    if 'date_from' in filters and 'date_to' in filters:
        date_from = parse_date(filters['date_from'])
        date_to = parse_date(filters['date_to'])
        if date_from and date_to and date_from > date_to:
            return False, "Start date cannot be after end date"
    
    return True, None

