"""
Enhanced Literature Integration for AetherSignal
Uses LLM to intelligently summarize and extract insights from PubMed abstracts.

Features:
- Abstract summarization
- Key findings extraction
- Mechanism identification
- Cross-paper comparison
"""

from typing import Dict, List, Optional
from src.literature_integration import search_pubmed, search_clinical_trials
from src.ai.medical_llm import call_medical_llm


def enrich_signal_with_enhanced_literature(
    drug: str,
    reaction: str,
    use_llm: bool = True
) -> Dict:
    """
    Enrich signal with literature evidence + LLM-powered insights.
    
    Args:
        drug: Drug name
        reaction: Reaction/adverse event
        use_llm: Whether to use LLM for summarization
        
    Returns:
        Dictionary with literature evidence and LLM insights
    """
    # Get raw literature results
    pubmed_results = search_pubmed(drug, reaction, max_results=10)
    clinical_trials = search_clinical_trials(drug, reaction, max_results=5)
    
    result = {
        'pubmed_articles': pubmed_results,
        'clinical_trials': clinical_trials,
        'total_pubmed': len(pubmed_results),
        'total_trials': len(clinical_trials),
        'llm_summaries': [],
        'key_findings': None,
        'mechanisms': None,
        'consensus': None,
    }
    
    # If LLM enabled and we have articles, generate insights
    if use_llm and pubmed_results:
        # Summarize abstracts
        summaries = []
        for article in pubmed_results[:5]:  # Limit to top 5 for cost
            if article.get('abstract'):
                summary = _summarize_abstract(article, drug, reaction)
                if summary:
                    summaries.append({
                        'pmid': article.get('pmid'),
                        'title': article.get('title'),
                        'summary': summary
                    })
        
        result['llm_summaries'] = summaries
        
        # Extract key findings across all papers
        if len(pubmed_results) >= 2:
            result['key_findings'] = _extract_key_findings(pubmed_results, drug, reaction)
            result['mechanisms'] = _extract_mechanisms(pubmed_results, drug, reaction)
            result['consensus'] = _generate_consensus(pubmed_results, drug, reaction)
    
    return result


def _summarize_abstract(article: Dict, drug: str, reaction: str) -> Optional[str]:
    """Summarize a single PubMed abstract."""
    abstract = article.get('abstract', '')
    if not abstract or len(abstract) < 50:
        return None
    
    system_prompt = """You are a pharmacovigilance expert. Summarize PubMed abstracts focusing on:
1. Key findings about the drug-reaction relationship
2. Study design and sample size
3. Clinical significance
4. Limitations

Keep summary to 2-3 sentences. Be concise and factual."""
    
    prompt = f"""Abstract from: {article.get('title', 'Unknown')}

{abstract}

Summarize the key findings about {drug} and {reaction}:"""
    
    return call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="literature",
        max_tokens=200,
        temperature=0.2
    )


def _extract_key_findings(articles: List[Dict], drug: str, reaction: str) -> Optional[str]:
    """Extract key findings across multiple papers."""
    if len(articles) < 2:
        return None
    
    # Build context from top 5 articles
    articles_text = []
    for i, article in enumerate(articles[:5], 1):
        articles_text.append(
            f"Paper {i}: {article.get('title', 'Unknown')}\n"
            f"Abstract: {article.get('abstract', 'N/A')[:300]}..."
        )
    
    system_prompt = """You are a pharmacovigilance expert. Analyze multiple research papers and extract:
1. Common findings across papers
2. Conflicting evidence (if any)
3. Strength of evidence
4. Clinical implications

Format as a structured summary."""
    
    prompt = f"""Analyze these papers about {drug} and {reaction}:

{chr(10).join(articles_text)}

Extract key findings across all papers:"""
    
    return call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="literature",
        max_tokens=400,
        temperature=0.2
    )


def _extract_mechanisms(articles: List[Dict], drug: str, reaction: str) -> Optional[str]:
    """Extract proposed mechanisms from literature."""
    if len(articles) < 1:
        return None
    
    articles_text = []
    for i, article in enumerate(articles[:5], 1):
        abstract = article.get('abstract', '')
        if abstract:
            articles_text.append(f"Paper {i}: {abstract[:400]}...")
    
    system_prompt = """You are a pharmacovigilance expert. Extract proposed biological mechanisms 
for drug-reaction relationships from research papers. Focus on:
1. Pharmacological mechanisms
2. Pathophysiological pathways
3. Risk factors mentioned
4. Dose-response relationships

Be cautious - only mention mechanisms explicitly discussed in the papers."""
    
    prompt = f"""Extract mechanisms for {drug} causing {reaction} from these papers:

{chr(10).join(articles_text)}

What mechanisms are proposed? (Only mention if explicitly discussed):"""
    
    return call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="causal_reasoning",  # Use Claude Opus if available for better reasoning
        max_tokens=300,
        temperature=0.2
    )


def _generate_consensus(articles: List[Dict], drug: str, reaction: str) -> Optional[str]:
    """Generate consensus view across papers."""
    if len(articles) < 2:
        return None
    
    articles_text = []
    for i, article in enumerate(articles[:5], 1):
        articles_text.append(
            f"{i}. {article.get('title', 'Unknown')} ({article.get('year', 'N/A')})\n"
            f"   {article.get('abstract', '')[:200]}..."
        )
    
    system_prompt = """You are a pharmacovigilance expert. Synthesize findings across multiple papers 
to provide a consensus view. Include:
1. Overall strength of evidence
2. Agreement/disagreement across studies
3. Clinical recommendations
4. Gaps in knowledge

Be cautious and evidence-based."""
    
    prompt = f"""Synthesize a consensus view about {drug} and {reaction} from these papers:

{chr(10).join(articles_text)}

Provide a consensus summary:"""
    
    return call_medical_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type="causal_reasoning",
        max_tokens=400,
        temperature=0.2
    )

