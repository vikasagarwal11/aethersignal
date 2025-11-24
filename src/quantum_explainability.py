"""
Explainable Quantum AI (XQI) for AetherSignal.
Provides transparent explanations for quantum-inspired decisions.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from src.quantum_ranking import _extract_features, _calculate_quantum_score
from src.quantum_clustering import cluster_cases_for_signal
from src.utils import safe_divide


def explain_quantum_ranking(signal: Dict[str, Any], total_cases: int) -> Dict:
    """
    Explain why a signal received its quantum ranking score.
    
    Args:
        signal: Signal dictionary with quantum_score
        total_cases: Total cases in dataset
        
    Returns:
        Dictionary with explanation components
    """
    features = _extract_features(signal, total_cases)
    quantum_score = _calculate_quantum_score(features)
    
    # Calculate component contributions
    count = features['count']
    rarity = features['rarity']
    seriousness = features['seriousness_score']
    recency = features['recency_score']
    
    # Base contributions
    rarity_contribution = 0.40 * rarity
    seriousness_contribution = 0.35 * seriousness
    recency_contribution = 0.20 * recency
    count_contribution = 0.05 * min(1.0, count / 10.0)
    
    # Interaction terms
    interaction_terms = []
    interaction_value = 0.0
    
    if rarity > 0.7 and seriousness > 0.5:
        interaction_value += 0.15
        interaction_terms.append({
            'type': 'Rare + Serious',
            'description': 'Rare signals with serious outcomes are especially important',
            'contribution': 0.15
        })
    
    if rarity > 0.7 and recency > 0.7:
        interaction_value += 0.10
        interaction_terms.append({
            'type': 'Rare + Recent',
            'description': 'Emerging rare signals require immediate attention',
            'contribution': 0.10
        })
    
    if seriousness > 0.7 and recency > 0.7:
        interaction_value += 0.10
        interaction_terms.append({
            'type': 'Serious + Recent',
            'description': 'Urgent serious signals need rapid investigation',
            'contribution': 0.10
        })
    
    if rarity > 0.6 and seriousness > 0.6 and recency > 0.6:
        interaction_value += 0.20
        interaction_terms.append({
            'type': 'Rare + Serious + Recent',
            'description': 'Critical signal: rare, serious, and recent - highest priority',
            'contribution': 0.20
        })
    
    # Tunneling boost
    tunneling_terms = []
    tunneling_value = 0.0
    
    if 0.5 < rarity <= 0.7:
        tunneling_value += 0.05
        tunneling_terms.append({
            'type': 'Rarity Tunneling',
            'description': 'Signal is approaching rare threshold (quantum tunneling effect)',
            'contribution': 0.05
        })
    
    if 0.5 < seriousness <= 0.7:
        tunneling_value += 0.05
        tunneling_terms.append({
            'type': 'Seriousness Tunneling',
            'description': 'Signal is approaching serious threshold',
            'contribution': 0.05
        })
    
    if 0.5 < recency <= 0.7:
        tunneling_value += 0.05
        tunneling_terms.append({
            'type': 'Recency Tunneling',
            'description': 'Signal is approaching recent threshold',
            'contribution': 0.05
        })
    
    # Generate natural language explanation
    explanation_parts = []
    
    if quantum_score > 0.8:
        explanation_parts.append("**High Priority Signal** - This signal scored highly due to:")
    elif quantum_score > 0.5:
        explanation_parts.append("**Moderate Priority Signal** - This signal scored moderately due to:")
    else:
        explanation_parts.append("**Lower Priority Signal** - This signal scored lower due to:")
    
    # Add feature explanations
    if rarity > 0.7:
        explanation_parts.append(f"- **Rarity**: High ({rarity:.1%}) - This is a rare signal in the dataset")
    elif rarity > 0.5:
        explanation_parts.append(f"- **Rarity**: Moderate ({rarity:.1%}) - This signal is somewhat rare")
    else:
        explanation_parts.append(f"- **Rarity**: Low ({rarity:.1%}) - This is a common signal")
    
    if seriousness > 0.7:
        explanation_parts.append(f"- **Seriousness**: High ({seriousness:.1%}) - Many serious outcomes reported")
    elif seriousness > 0.5:
        explanation_parts.append(f"- **Seriousness**: Moderate ({seriousness:.1%}) - Some serious outcomes")
    else:
        explanation_parts.append(f"- **Seriousness**: Low ({seriousness:.1%}) - Few serious outcomes")
    
    if recency > 0.7:
        explanation_parts.append(f"- **Recency**: High ({recency:.1%}) - Very recent cases")
    elif recency > 0.5:
        explanation_parts.append(f"- **Recency**: Moderate ({recency:.1%}) - Moderately recent cases")
    else:
        explanation_parts.append(f"- **Recency**: Low ({recency:.1%}) - Older cases")
    
    if interaction_terms:
        explanation_parts.append(f"- **Quantum Interactions**: {len(interaction_terms)} interaction(s) detected")
    
    if tunneling_terms:
        explanation_parts.append(f"- **Quantum Tunneling**: {len(tunneling_terms)} tunneling effect(s) applied")
    
    explanation_text = "\n".join(explanation_parts)
    
    return {
        'quantum_score': float(quantum_score),
        'base_score': float(rarity_contribution + seriousness_contribution + recency_contribution + count_contribution),
        'interaction_score': float(interaction_value),
        'tunneling_score': float(tunneling_value),
        'components': {
            'rarity': {
                'value': float(rarity),
                'contribution': float(rarity_contribution),
                'weight': 0.40,
                'description': 'Rarity score (higher = rarer signal)'
            },
            'seriousness': {
                'value': float(seriousness),
                'contribution': float(seriousness_contribution),
                'weight': 0.35,
                'description': 'Seriousness score (higher = more serious)'
            },
            'recency': {
                'value': float(recency),
                'contribution': float(recency_contribution),
                'weight': 0.20,
                'description': 'Recency score (higher = more recent)'
            },
            'count': {
                'value': float(count),
                'contribution': float(count_contribution),
                'weight': 0.05,
                'description': 'Case count (minimum threshold)'
            }
        },
        'interactions': interaction_terms,
        'tunneling_effects': tunneling_terms,
        'explanation': explanation_text,
        'regulatory_summary': _generate_regulatory_summary(quantum_score, rarity, seriousness, recency, interaction_terms)
    }


def _generate_regulatory_summary(score: float, rarity: float, seriousness: float, recency: float, interactions: List) -> str:
    """
    Generate regulatory-friendly summary for audit purposes.
    """
    summary = f"Quantum-inspired ranking score: {score:.3f}. "
    summary += f"Components: Rarity ({rarity:.1%}), Seriousness ({seriousness:.1%}), Recency ({recency:.1%}). "
    
    if interactions:
        summary += f"Quantum interactions detected: {len(interactions)}. "
    
    summary += "Algorithm: Quantum-inspired simulated annealing with interaction terms and tunneling effects."
    
    return summary


def explain_quantum_clustering(clusters: List[Dict], signal_drug: str, signal_reaction: str) -> Dict:
    """
    Explain quantum clustering results for a signal.
    
    Args:
        clusters: List of cluster dictionaries from quantum_clustering
        signal_drug: Drug name
        signal_reaction: Reaction name
        
    Returns:
        Dictionary with clustering explanation
    """
    if not clusters:
        return {
            'explanation': 'No clusters detected. Insufficient cases or data for clustering.',
            'clusters': [],
            'highest_risk_cluster': None
        }
    
    # Find highest risk cluster
    highest_risk = max(clusters, key=lambda c: c.get('serious_pct', 0))
    
    explanation_parts = [
        f"**Quantum Clustering Analysis** for {signal_drug} → {signal_reaction}",
        f"",
        f"**Total Clusters Discovered:** {len(clusters)}",
        f"",
        f"**Highest Risk Cluster:** Cluster {highest_risk.get('cluster_id', 'N/A')}",
        f"- Cases: {highest_risk.get('size', 0)}",
        f"- Mean Age: {highest_risk.get('mean_age', 'N/A'):.1f} years" if highest_risk.get('mean_age') else "- Mean Age: N/A",
        f"- Serious Cases: {highest_risk.get('serious_pct', 0):.1f}%",
        f"- Risk Profile: {'High' if highest_risk.get('serious_pct', 0) > 50 else 'Moderate' if highest_risk.get('serious_pct', 0) > 20 else 'Low'}",
        f"",
        f"**Method:** Quantum-inspired k-means clustering with non-linear distance weighting.",
        f"**Purpose:** Automatically discover hidden patient subgroups with distinct risk profiles."
    ]
    
    explanation_text = "\n".join(explanation_parts)
    
    return {
        'explanation': explanation_text,
        'clusters': clusters,
        'highest_risk_cluster': highest_risk,
        'method': 'Quantum-inspired k-means with distance weighting',
        'regulatory_summary': f"Quantum clustering identified {len(clusters)} patient subgroups. Highest risk: Cluster {highest_risk.get('cluster_id')} with {highest_risk.get('serious_pct', 0):.1f}% serious cases."
    }


def generate_quantum_circuit_diagram(signal: Dict[str, Any], total_cases: int) -> Dict:
    """
    Generate a simplified quantum circuit representation for visualization.
    
    This is a conceptual representation, not a true quantum circuit.
    Shows the decision path through quantum-inspired scoring.
    
    Args:
        signal: Signal dictionary
        total_cases: Total cases
        
    Returns:
        Dictionary with circuit representation
    """
    features = _extract_features(signal, total_cases)
    
    # Represent as a decision tree/circuit
    circuit_steps = [
        {
            'step': 1,
            'gate': 'Feature Extraction',
            'inputs': ['Case Count', 'Seriousness', 'Dates'],
            'outputs': ['Rarity', 'Seriousness Score', 'Recency Score']
        },
        {
            'step': 2,
            'gate': 'Base Score Calculation',
            'inputs': ['Rarity (40%)', 'Seriousness (35%)', 'Recency (20%)', 'Count (5%)'],
            'outputs': ['Base Score']
        },
        {
            'step': 3,
            'gate': 'Interaction Detection',
            'inputs': ['Rarity', 'Seriousness', 'Recency'],
            'outputs': ['Interaction Terms']
        },
        {
            'step': 4,
            'gate': 'Tunneling Effect',
            'inputs': ['Near-Threshold Features'],
            'outputs': ['Tunneling Boost']
        },
        {
            'step': 5,
            'gate': 'Final Score',
            'inputs': ['Base Score', 'Interactions', 'Tunneling'],
            'outputs': ['Quantum Score']
        }
    ]
    
    return {
        'circuit_steps': circuit_steps,
        'visualization_type': 'decision_path',
        'description': 'Quantum-inspired scoring decision path (conceptual representation)'
    }

