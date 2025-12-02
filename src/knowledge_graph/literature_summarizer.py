"""
Literature Summarizer - Summarizes evidence from PubMed/Literature
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LiteratureSummarizer:
    """
    Summarizes:
    - PubMed abstracts
    - Mechanistic articles
    - Case reports
    into mechanistic explanations.
    """
    
    def __init__(self):
        pass
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM for summarization."""
        try:
            from src.local_llm.model_router import ModelRouter
            router = ModelRouter()
            return router.run(prompt, mode="summary")
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
            return "Literature summarization unavailable."
    
    def summarize(self, drug: str, reaction: str, papers: List[str]) -> Dict[str, Any]:
        """
        Summarize mechanistic evidence from literature.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            papers: List of paper abstracts/texts
        
        Returns:
            Summary dictionary
        """
        if not papers:
            return {
                "summary": None,
                "papers_used": 0
            }
        
        # Cap to 10 papers for performance
        combined = "\n\n".join(papers[:10])
        
        llm_prompt = f"""
Summarize mechanistic evidence for:

Drug: {drug}
Reaction: {reaction}

Use ONLY the following papers:

{combined}

Provide a structured summary including:
- Mechanism
- Key pathways
- Strength of evidence
- Consistency across papers

Keep it concise (300-400 words) and scientifically accurate.
        """
        
        try:
            llm_output = self._call_llm(llm_prompt)
            return {
                "summary": llm_output,
                "papers_used": min(len(papers), 10)
            }
        except Exception as e:
            logger.error(f"Literature summarization error: {e}")
            return {
                "summary": f"Error summarizing literature: {str(e)}",
                "papers_used": 0
            }

