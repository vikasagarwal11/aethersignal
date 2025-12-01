"""
Server Summary Extractor (CHUNK 7.4 Part 1)
Heavy server-side AI summary generation using LLM.
Uses local summary as input to reduce cost and improve accuracy.
"""
from typing import Dict, Any, Optional
import pandas as pd

try:
    from src.ai.medical_llm import call_medical_llm, LLM_AVAILABLE
    MEDICAL_LLM_AVAILABLE = True
except ImportError:
    MEDICAL_LLM_AVAILABLE = False
    LLM_AVAILABLE = False


def extract_server_summary(local_summary: Dict[str, Any], df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Heavy server-side AI summary generation.
    
    Uses local summary as input to reduce LLM token cost and improve accuracy.
    Generates regulatory-grade narrative summaries.
    
    Args:
        local_summary: Local summary dictionary (fast statistics)
        df: Optional DataFrame for additional context
        
    Returns:
        Dictionary with AI-generated narrative and insights
    """
    if not MEDICAL_LLM_AVAILABLE or not LLM_AVAILABLE:
        return {
            "narrative": "AI summary unavailable - LLM not configured.",
            "ai_generated": False,
            "error": "LLM not available"
        }
    
    try:
        # Prepare context from local summary
        dataset_info = {
            "total_cases": local_summary.get("total_cases", 0),
            "serious_cases": local_summary.get("serious_cases", 0),
            "seriousness_pct": local_summary.get("seriousness_pct", 0),
            "fatal_cases": local_summary.get("fatal_cases", 0),
            "top_drugs": list(local_summary.get("top_drugs", {}).keys())[:5],
            "top_reactions": list(local_summary.get("top_reactions", {}).keys())[:5],
            "unique_drugs": local_summary.get("unique_drugs", 0),
            "unique_reactions": local_summary.get("unique_reactions", 0),
            "date_range": local_summary.get("date_range", {})
        }
        
        if df is not None:
            dataset_info["rows"] = len(df)
            dataset_info["columns"] = list(df.columns)[:10]  # Limit columns for context
        
        system_prompt = """You are a senior pharmacovigilance safety surveillance medical reviewer.
You provide concise, regulatory-grade summaries of safety data for signal detection and risk assessment.
Focus on clinical relevance, regulatory implications, and actionable insights.
Keep responses professional and evidence-based."""
        
        prompt = f"""
You are a safety surveillance medical reviewer analyzing safety data.

Local data summary (statistics):
- Total cases: {dataset_info['total_cases']:,}
- Serious cases: {dataset_info['serious_cases']:,} ({dataset_info['seriousness_pct']:.1f}%)
- Fatal cases: {dataset_info.get('fatal_cases', 0):,}
- Unique drugs: {dataset_info['unique_drugs']}
- Unique reactions: {dataset_info['unique_reactions']}
- Top drugs: {', '.join(dataset_info['top_drugs']) if dataset_info['top_drugs'] else 'N/A'}
- Top reactions: {', '.join(dataset_info['top_reactions']) if dataset_info['top_reactions'] else 'N/A'}
- Date range: {dataset_info['date_range'].get('min', 'N/A')} to {dataset_info['date_range'].get('max', 'N/A')}

Provide a concise regulatory-grade summary covering:
1. Overall safety profile summary (2-3 sentences)
2. Key safety concerns or patterns (2-3 bullets)
3. Notable trends or emerging signals (1-2 bullets)
4. Regulatory considerations (1-2 bullets)
5. Recommended next steps (1-2 bullets)

Keep the total response under 300 words. Use professional, evidence-based language suitable for regulatory submission.
"""
        
        response = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="general",
            max_tokens=500,
            temperature=0.3
        )
        
        if not response:
            return {
                "narrative": "AI summary generation failed - no response from LLM.",
                "ai_generated": False,
                "error": "No LLM response"
            }
        
        return {
            "narrative": response.strip(),
            "ai_generated": True,
            "metadata": {
                "model": "medical_llm",
                "local_summary_used": True,
                "timestamp": pd.Timestamp.now().isoformat()
            }
        }
        
    except Exception as e:
        return {
            "narrative": f"AI summary generation failed: {str(e)}",
            "ai_generated": False,
            "error": str(e)
        }

