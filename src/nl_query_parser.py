"""
Natural Language Query Parser for AetherSignal
Converts natural language queries to filter dictionaries.
"""

import re
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import pandas as pd
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


def _detect_concepts(query_lower: str, filters: Dict) -> None:
    """
    Detect conceptual terms and convert them to specific filters.
    
    Handles:
    - Population groups: "seniors", "elderly", "pediatrics", "children", "adults"
    - Temporal concepts: "recently", "lately", "in the last X months/years"
    - Special populations: "pregnant women", "women of childbearing age"
    - Severity concepts: "life-threatening", "hospitalization"
    - Emerging signals: "new", "emerging", "novel"
    
    Args:
        query_lower: Lowercase query string
        filters: Filter dictionary to update (modified in place)
    """
    # Population groups - Age-based
    if re.search(r'\b(seniors?|elderly|older adults?|geriatric)\b', query_lower):
        # Seniors typically 65+
        if 'age_min' not in filters:
            filters['age_min'] = 65
        elif filters.get('age_min', 0) < 65:
            filters['age_min'] = 65
    
    if re.search(r'\b(pediatric|pediatrics|children|kids?|infants?|neonates?|toddlers?)\b', query_lower):
        # Pediatrics typically < 18
        if 'age_max' not in filters:
            filters['age_max'] = 17
        elif filters.get('age_max', 999) > 17:
            filters['age_max'] = 17
    
    if re.search(r'\b(adults?|adult patients?)\b', query_lower):
        # Adults typically 18-64 (if not conflicting with seniors/pediatrics)
        if 'age_min' not in filters and 'age_max' not in filters:
            filters['age_min'] = 18
            filters['age_max'] = 64
    
    # Temporal concepts - "recently", "lately", "in the last X"
    if re.search(r'\b(recently|lately|recent|current|latest)\b', query_lower):
        # Default to last 12 months if no date specified
        if 'date_from' not in filters:
            twelve_months_ago = datetime.now() - timedelta(days=365)
            filters['date_from'] = twelve_months_ago.strftime('%Y-%m-%d')
    
    # "In the last X months/years"
    last_pattern = re.search(r'\b(?:in|over|during|for)\s+(?:the\s+)?last\s+(\d+)\s+(month|months|year|years)\b', query_lower)
    if last_pattern:
        amount = int(last_pattern.group(1))
        unit = last_pattern.group(2).lower()
        if 'date_from' not in filters:
            if 'month' in unit:
                days_ago = amount * 30
            else:  # years
                days_ago = amount * 365
            start_date = datetime.now() - timedelta(days=days_ago)
            filters['date_from'] = start_date.strftime('%Y-%m-%d')
    
    # "Past X months/years"
    past_pattern = re.search(r'\b(?:past|previous|prior)\s+(\d+)\s+(month|months|year|years)\b', query_lower)
    if past_pattern:
        amount = int(past_pattern.group(1))
        unit = past_pattern.group(2).lower()
        if 'date_from' not in filters:
            if 'month' in unit:
                days_ago = amount * 30
            else:  # years
                days_ago = amount * 365
            start_date = datetime.now() - timedelta(days=days_ago)
            filters['date_from'] = start_date.strftime('%Y-%m-%d')
    
    # Special populations
    if re.search(r'\b(pregnant\s+women?|pregnancy|expecting\s+mothers?)\b', query_lower):
        filters['sex'] = 'F'
        # Note: We don't have pregnancy status in standard schema, but we can filter by sex
    
    if re.search(r'\b(women?\s+of\s+childbearing\s+age|reproductive\s+age)\b', query_lower):
        filters['sex'] = 'F'
        # Typically 15-49 years
        if 'age_min' not in filters:
            filters['age_min'] = 15
        if 'age_max' not in filters:
            filters['age_max'] = 49
    
    # Severity concepts (enhance existing seriousness detection)
    if re.search(r'\b(life.?threatening|fatal|death|mortality|lethal)\b', query_lower):
        filters['seriousness'] = True
    
    if re.search(r'\b(hospitalization|hospitalized|hospital\s+admission)\b', query_lower):
        filters['seriousness'] = True
    
    # "New" or "emerging" - typically means recent
    if re.search(r'\b(new|emerging|novel|recent\s+signals?)\b', query_lower):
        if 'date_from' not in filters:
            # Default to last 18 months for "new" signals
            eighteen_months_ago = datetime.now() - timedelta(days=545)
            filters['date_from'] = eighteen_months_ago.strftime('%Y-%m-%d')


def _detect_term_in_dataset(term: str, normalized_df: Optional[pd.DataFrame]) -> Tuple[Optional[str], bool, bool]:
    """
    Check if a term exists in the dataset as a drug or reaction.
    
    Args:
        term: Term to check
        normalized_df: Normalized DataFrame with drug_name and reaction columns
        
    Returns:
        Tuple of (matched_term, is_drug, is_reaction)
        - matched_term: The actual matched term from dataset (normalized), or None
        - is_drug: True if term matches a drug in the dataset
        - is_reaction: True if term matches a reaction in the dataset
    """
    if normalized_df is None or normalized_df.empty:
        return None, False, False
    
    term_normalized = normalize_text(term)
    if len(term_normalized) < 3:  # Too short to be meaningful
        return None, False, False
    
    is_drug = False
    is_reaction = False
    matched_term = None
    
    # Check drugs
    if 'drug_name' in normalized_df.columns:
        drug_series = normalized_df['drug_name'].astype(str).str.split('; ').explode()
        drug_normalized = drug_series.apply(normalize_text)
        # Check for exact or partial match
        matches = drug_normalized[drug_normalized.str.contains(re.escape(term_normalized), na=False, case=False)]
        if not matches.empty:
            is_drug = True
            # Get the most common match
            matched_term = matches.value_counts().index[0] if len(matches) > 0 else term
    
    # Check reactions
    if 'reaction' in normalized_df.columns:
        reaction_series = normalized_df['reaction'].astype(str).str.split('; ').explode()
        reaction_normalized = reaction_series.apply(normalize_text)
        # Check for exact or partial match
        matches = reaction_normalized[reaction_normalized.str.contains(re.escape(term_normalized), na=False, case=False)]
        if not matches.empty:
            is_reaction = True
            # If we haven't found a drug match, use reaction match
            if not is_drug:
                matched_term = matches.value_counts().index[0] if len(matches) > 0 else term
    
    return matched_term, is_drug, is_reaction


def parse_query_to_filters(query: str, normalized_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Parse natural language query to filter dictionary.
    
    Args:
        query: Natural language query string
        normalized_df: Optional normalized DataFrame to use for context-aware detection
        
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
    
    # Concept detection: Population groups and temporal concepts
    _detect_concepts(query_lower, filters)
    
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
    
    # Context-aware detection: If no drugs/reactions found with explicit keywords,
    # try to detect them from the dataset
    if normalized_df is not None and not normalized_df.empty:
        # Extract potential terms that weren't matched by explicit patterns
        # Look for words after context phrases (case-insensitive)
        if 'drug' not in filters and 'reaction' not in filters:
            # Common stop words to exclude
            stop_words = {'all', 'any', 'some', 'the', 'and', 'or', 'for', 'with', 'cases', 'reports', 
                         'events', 'show', 'find', 'search', 'filter', 'get', 'related', 'to', 'about', 
                         'involving', 'containing', 'including', 'from', 'since', 'until', 'before', 'after'}
            
            # Pattern 1: Extract terms after context phrases (case-insensitive)
            # "related to X", "with X", "for X", "about X", "involving X"
            context_patterns = [
                r'(?:related\s+to|with|for|about|involving|containing|including)[\s]+([a-z0-9]+(?:\s+[a-z0-9]+)*)',
                r'(?:find|show|search|filter|get)[\s]+(?:all|any|some)?[\s]*(?:cases|reports|events)?[\s]*(?:related\s+to|with|for|about|involving)?[\s]+([a-z0-9]+(?:\s+[a-z0-9]+)*)',
            ]
            
            potential_terms = []
            for pattern in context_patterns:
                matches = re.findall(pattern, query_lower, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else (match[1] if len(match) > 1 else "")
                    term = match.strip()
                    # Extract words from the term
                    words = term.split()
                    for word in words:
                        # Filter out stop words, short words, numbers only
                        if (len(word) >= 4 and  # At least 4 characters (e.g., "dupixent")
                            word.lower() not in stop_words and
                            not re.match(r'^\d+$', word) and
                            word.lower() not in [d.lower() if isinstance(d, str) else str(d).lower() for d in (drugs if 'drug' in filters else [])] and
                            word.lower() not in [r.lower() if isinstance(r, str) else str(r).lower() for r in (unique_reactions if 'reaction' in filters else [])]):
                            potential_terms.append(word)
            
            # Pattern 2: Also catch standalone capitalized terms (likely drug/reaction names)
            # This helps with queries like "Dupixent cases" or "Show Aspirin"
            capitalized_matches = re.findall(r'\b([A-Z][a-z]{3,}(?:\s+[A-Z][a-z]+)*)\b', query)
            for match in capitalized_matches:
                words = match.split()
                for word in words:
                    if (len(word) >= 4 and
                        word.lower() not in stop_words and
                        word.lower() not in [t.lower() for t in potential_terms]):
                        potential_terms.append(word)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_potential_terms = []
            for term in potential_terms:
                term_lower = term.lower()
                if term_lower not in seen:
                    seen.add(term_lower)
                    unique_potential_terms.append(term)
            
            # Check each potential term against the dataset
            for term in unique_potential_terms[:5]:  # Limit to first 5 to avoid performance issues
                matched_term, is_drug, is_reaction = _detect_term_in_dataset(term, normalized_df)
                if matched_term:
                    if is_drug and 'drug' not in filters:
                        # Prefer drug over reaction if both match
                        filters['drug'] = matched_term
                        break  # Found a drug, stop searching
                    elif is_reaction and 'reaction' not in filters and not is_drug:
                        filters['reaction'] = matched_term
                        break  # Found a reaction, stop searching
                    # If both match, we already set drug above, so skip reaction
            
            # Fallback: If still no drugs/reactions found, check ALL remaining words in query
            # This catches standalone lowercase words like "dupixent" or "aspirin"
            if 'drug' not in filters and 'reaction' not in filters:
                # Extract all words from the query (excluding already processed terms and stop words)
                all_words = re.findall(r'\b([a-z]{4,})\b', query_lower)  # Words with 4+ lowercase letters
                for word in all_words:
                    if (word not in stop_words and
                        word not in [t.lower() for t in unique_potential_terms] and
                        not re.match(r'^\d+$', word)):
                        matched_term, is_drug, is_reaction = _detect_term_in_dataset(word, normalized_df)
                        if matched_term:
                            if is_drug:
                                filters['drug'] = matched_term
                                break  # Found a drug, stop searching
                            elif is_reaction:
                                filters['reaction'] = matched_term
                                break  # Found a reaction, stop searching
                        # Limit fallback to first 10 words to avoid performance issues
                        if all_words.index(word) >= 9:
                            break
    
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

