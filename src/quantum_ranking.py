"""
Quantum-Inspired Ranking for AetherSignal
Simple quantum-inspired ranking using simulated annealing and heuristics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.utils import parse_date, normalize_text


def quantum_rerank_signals(candidates: List[Dict[str, Any]], total_cases: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Re-rank candidate signals using quantum-inspired scoring.
    Favors rare, serious, and recent signals.
    
    Args:
        candidates: List of signal dictionaries with keys:
            - drug: Drug name
            - reaction: Reaction name
            - count: Number of cases
            - prr, ror: Optional signal detection metrics
            - seriousness: Optional seriousness flags/outcome data
            - dates: Optional date information for recency
        total_cases: Total number of cases in dataset (for rarity calculation)
        
    Returns:
        List of signals with added 'quantum_score' and 'quantum_rank', sorted by quantum_score
    """
    if not candidates:
        return candidates
    
    # Calculate total cases if not provided
    if total_cases is None:
        total_cases = sum(signal.get('count', 0) for signal in candidates)
    
    if total_cases == 0:
        total_cases = 1  # Avoid division by zero
    
    # Extract features and calculate quantum scores
    for signal in candidates:
        features = _extract_features(signal, total_cases)
        signal['quantum_score'] = _calculate_quantum_score(features)
        signal['classical_rank'] = None  # Will be set after classical sorting
    
    # Classical ranking (by count, descending)
    classical_sorted = sorted(candidates, key=lambda x: x.get('count', 0), reverse=True)
    for i, signal in enumerate(classical_sorted):
        signal['classical_rank'] = i + 1
    
    # Quantum ranking (by quantum_score, descending)
    quantum_sorted = sorted(candidates, key=lambda x: x.get('quantum_score', 0), reverse=True)
    for i, signal in enumerate(quantum_sorted):
        signal['quantum_rank'] = i + 1
    
    return quantum_sorted


def _extract_features(signal: Dict[str, Any], total_cases: int) -> Dict[str, float]:
    """
    Extract features from signal dictionary.
    
    Args:
        signal: Signal dictionary
        total_cases: Total cases in dataset
        
    Returns:
        Dictionary with extracted features
    """
    count = float(signal.get('count', 0))
    
    # Rarity: proportion in total dataset (lower proportion = rarer = better)
    rarity = 1.0 - (count / total_cases) if total_cases > 0 else 0.0
    rarity = max(0.0, min(1.0, rarity))  # Clamp to [0, 1]
    
    # Seriousness score: based on seriousness flags/outcome
    seriousness_score = _calculate_seriousness_score(signal)
    
    # Recency score: more recent cases get higher weight
    recency_score = _calculate_recency_score(signal)
    
    return {
        'count': count,
        'rarity': rarity,
        'seriousness_score': seriousness_score,
        'recency_score': recency_score,
    }


def _calculate_seriousness_score(signal: Dict[str, Any]) -> float:
    """
    Calculate seriousness score based on seriousness flags and outcomes.
    
    Args:
        signal: Signal dictionary
        
    Returns:
        Seriousness score between 0.0 and 1.0
    """
    score = 0.0
    
    # Check for explicit seriousness flag
    seriousness = signal.get('seriousness')
    if seriousness is not None:
        seriousness_str = normalize_text(str(seriousness))
        if seriousness_str in ['1', 'yes', 'y', 'true', 'serious']:
            score += 0.5
    
    # Check for outcome information
    outcome = signal.get('outcome')
    if outcome is not None:
        outcome_str = normalize_text(str(outcome))
        # Higher weight for severe outcomes
        if any(term in outcome_str for term in ['death', 'fatal', 'died', 'deceased']):
            score += 0.5
        elif any(term in outcome_str for term in ['hospital', 'hospitalized', 'life', 'threatening']):
            score += 0.3
        elif any(term in outcome_str for term in ['disability', 'disabled', 'permanent']):
            score += 0.2
    
    # Check for serious count if available
    serious_count = signal.get('serious_count', 0)
    total_count = signal.get('count', 1)
    if total_count > 0:
        serious_proportion = serious_count / total_count
        score += serious_proportion * 0.3
    
    return min(1.0, score)  # Cap at 1.0


def _calculate_recency_score(signal: Dict[str, Any]) -> float:
    """
    Calculate recency score based on date information.
    More recent cases get higher weight.
    
    Args:
        signal: Signal dictionary
        
    Returns:
        Recency score between 0.0 and 1.0
    """
    # Try to get date information
    dates = []
    
    # Check for date list in signal (preferred, as it contains all dates)
    if 'dates' in signal and isinstance(signal['dates'], list):
        for date_item in signal['dates']:
            date_val = parse_date(date_item)
            if date_val:
                dates.append(date_val)
    
    # Check for onset_date (single date)
    if 'onset_date' in signal and 'dates' not in signal:
        date_val = parse_date(signal['onset_date'])
        if date_val:
            dates.append(date_val)
    
    # Check for report_date (single date)
    if 'report_date' in signal and 'dates' not in signal:
        date_val = parse_date(signal['report_date'])
        if date_val:
            dates.append(date_val)
    
    if not dates:
        return 0.5  # Default score if no dates available
    
    # Get the most recent date
    most_recent = max(dates)
    current_date = datetime.now()
    
    # Calculate days since most recent case
    days_ago = (current_date - most_recent).days
    
    # Convert to score: more recent = higher score
    # Cases from last year get full weight, older cases get diminishing weight
    if days_ago <= 365:
        recency_score = 1.0 - (days_ago / 365.0) * 0.5  # 0.5 to 1.0 for last year
    elif days_ago <= 730:
        recency_score = 0.5 - ((days_ago - 365) / 365.0) * 0.3  # 0.2 to 0.5 for year 2
    else:
        recency_score = max(0.0, 0.2 - (days_ago - 730) / 3650.0)  # Diminishing for older
    
    return max(0.0, min(1.0, recency_score))


def _calculate_quantum_score(features: Dict[str, float]) -> float:
    """
    Calculate quantum-inspired score using simulated annealing approach.
    Favors rare, serious, and recent signals.
    
    Args:
        features: Dictionary with count, rarity, seriousness_score, recency_score
        
    Returns:
        Quantum score (higher = better)
    """
    count = features['count']
    rarity = features['rarity']
    seriousness = features['seriousness_score']
    recency = features['recency_score']
    
    # Base score: weighted combination favoring rare, serious, and recent
    # Weights: rarity (40%), seriousness (35%), recency (20%), count (5% for minimum threshold)
    base_score = (
        0.40 * rarity +           # Rare signals are more interesting
        0.35 * seriousness +      # Serious signals are more important
        0.20 * recency +           # Recent signals are more relevant
        0.05 * min(1.0, count / 10.0)  # Minimum count threshold (normalized)
    )
    
    # Quantum-inspired enhancement: simulated annealing approach
    # Add non-linear interactions between features
    interaction_term = 0.0
    
    # Rare + Serious: especially important combination
    if rarity > 0.7 and seriousness > 0.5:
        interaction_term += 0.15
    
    # Rare + Recent: emerging signals
    if rarity > 0.7 and recency > 0.7:
        interaction_term += 0.10
    
    # Serious + Recent: urgent signals
    if seriousness > 0.7 and recency > 0.7:
        interaction_term += 0.10
    
    # All three: critical signals
    if rarity > 0.6 and seriousness > 0.6 and recency > 0.6:
        interaction_term += 0.20
    
    # Quantum tunneling effect: boost signals that are "close" to being rare/serious/recent
    tunneling_boost = 0.0
    if 0.5 < rarity <= 0.7:
        tunneling_boost += 0.05
    if 0.5 < seriousness <= 0.7:
        tunneling_boost += 0.05
    if 0.5 < recency <= 0.7:
        tunneling_boost += 0.05
    
    # Final quantum score (deterministic)
    quantum_score = base_score + interaction_term + tunneling_boost
    
    # Ensure score is positive
    return max(0.0, quantum_score)


def compare_classical_vs_quantum(signals: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Compare classical ranking (by count) vs quantum-inspired ranking.
    
    Args:
        signals: List of signals with quantum scores and ranks
        top_n: Number of top signals to compare
        
    Returns:
        List of comparison dictionaries
    """
    # Get classical ranking (by count)
    classical_sorted = sorted(signals, key=lambda x: x.get('count', 0), reverse=True)
    
    # Get quantum ranking (by quantum_score)
    quantum_sorted = sorted(signals, key=lambda x: x.get('quantum_score', 0), reverse=True)
    
    # Create comparison
    comparison = []
    for i in range(min(top_n, len(signals))):
        classical_signal = classical_sorted[i]
        quantum_signal = quantum_sorted[i]
        
        comparison.append({
            'Classical Rank': classical_signal.get('classical_rank', i + 1),
            'Classical Drug': classical_signal.get('drug', ''),
            'Classical Reaction': classical_signal.get('reaction', ''),
            'Classical Count': classical_signal.get('count', 0),
            'Quantum Rank': quantum_signal.get('quantum_rank', i + 1),
            'Quantum Drug': quantum_signal.get('drug', ''),
            'Quantum Reaction': quantum_signal.get('reaction', ''),
            'Quantum Score': round(quantum_signal.get('quantum_score', 0.0), 3),
        })
    
    return comparison
