"""
Hybrid Summary Merger (CHUNK 7.4 Part 1)
Combines local and server summaries into a unified view.
"""
from typing import Dict, Any, Optional
from datetime import datetime


def merge_summaries(
    local: Dict[str, Any],
    server: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge local and server summaries into unified view.
    
    Args:
        local: Local summary dictionary (statistics, counts)
        server: Optional server summary dictionary (AI narrative)
        
    Returns:
        Merged summary dictionary with unified view
    """
    merged: Dict[str, Any] = {}
    
    # Always include local summary
    merged["local"] = local
    
    # Include server summary if available
    if server:
        merged["server"] = server
    
    # Build unified view
    merged["unified"] = {
        "total_cases": local.get("total_cases", 0),
        "serious_cases": local.get("serious_cases", 0),
        "seriousness_pct": local.get("seriousness_pct", 0.0),
        "fatal_cases": local.get("fatal_cases", 0),
        "narrative": server.get("narrative", "Local summary only - AI enhancement unavailable.") if server else "Local summary only.",
        "ai_enhanced": server.get("ai_generated", False) if server else False,
        "top_drugs": local.get("top_drugs", {}),
        "top_reactions": local.get("top_reactions", {}),
        "timeline": local.get("recent_timeline", {}),
        "demographics": {
            "age_stats": local.get("age_stats"),
            "age_groups": local.get("age_groups"),
            "sex_ratio": local.get("sex_ratio")
        },
        "outcomes": local.get("outcome_distribution", {})
    }
    
    # Metadata
    merged["metadata"] = {
        "merged_at": datetime.utcnow().isoformat(),
        "engine": "hybrid" if server else "local",
        "has_local": True,
        "has_server": server is not None,
        "local_keys": list(local.keys()),
        "server_keys": list(server.keys()) if server else []
    }
    
    return merged

