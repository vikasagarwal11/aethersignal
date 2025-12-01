"""
Hybrid Summary Diagnostics (CHUNK 7.4 Part 1)
Builds diagnostics information for summary generation.
"""
from typing import Dict, Any
import time


def build_diagnostics(local: Dict[str, Any], final: Dict[str, Any], duration_ms: Optional[float] = None) -> Dict[str, Any]:
    """
    Build diagnostics information for summary generation.
    
    Args:
        local: Local summary dictionary
        final: Final merged summary dictionary
        duration_ms: Optional duration in milliseconds
        
    Returns:
        Diagnostics dictionary
    """
    diagnostics: Dict[str, Any] = {
        "local_keys": list(local.keys()) if local else [],
        "final_keys": list(final.keys()) if final else [],
        "has_local": local is not None and len(local) > 0,
        "has_server": "server" in final if final else False,
        "has_ai_narrative": final.get("unified", {}).get("ai_enhanced", False) if final else False,
        "top_drug": local.get("feature_vector", {}).get("TopDrug") if local else None,
        "top_reaction": local.get("feature_vector", {}).get("TopReaction") if local else None,
    }
    
    if duration_ms is not None:
        diagnostics["duration_ms"] = round(duration_ms, 2)
        diagnostics["performance"] = (
            "fast" if duration_ms < 1000 else
            "moderate" if duration_ms < 3000 else
            "slow"
        )
    
    return diagnostics

