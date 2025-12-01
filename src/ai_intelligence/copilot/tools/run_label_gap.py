"""
Label Gap Tool - Detect label gaps
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LabelGapTool:
    """Tool for label gap detection."""
    
    name = "label_gap"
    description = "Detect if AE is missing from FDA label"
    
    def run(self, drug: str, reaction: str) -> Dict[str, Any]:
        """
        Run label gap detection.
        
        Args:
            drug: Drug name
            reaction: Adverse event
        
        Returns:
            Label gap analysis dictionary
        """
        try:
            # Try to get label data
            try:
                from src.data_sources.sources.dailymed import DailyMedClient
                client = DailyMedClient()
                label_data = client.fetch({"drug": drug})
                
                # Check if reaction is in label
                label_reactions = []
                if label_data:
                    for item in label_data:
                        if "reaction" in item:
                            label_reactions.append(item["reaction"].lower())
                
                is_in_label = reaction.lower() in " ".join(label_reactions)
                
            except Exception:
                is_in_label = None
                label_reactions = []
            
            # Check if reaction appears in other sources
            try:
                from src.ai_intelligence.copilot.tools.query_faers import FAERSTool
                from src.ai_intelligence.copilot.tools.query_social import SocialTool
                
                faers_tool = FAERSTool()
                social_tool = SocialTool()
                
                faers_result = faers_tool.run(drug=drug, reaction=reaction)
                social_result = social_tool.run(drug=drug, reaction=reaction)
                
                has_faers = faers_result.get("count", 0) > 0
                has_social = social_result.get("count", 0) > 0
                
            except Exception:
                has_faers = False
                has_social = False
            
            # Determine gap status
            if is_in_label is False and (has_faers or has_social):
                gap_status = "LABEL_GAP_DETECTED"
            elif is_in_label is True:
                gap_status = "IN_LABEL"
            else:
                gap_status = "UNKNOWN"
            
            return {
                "tool": self.name,
                "drug": drug,
                "reaction": reaction,
                "is_in_label": is_in_label,
                "has_faers": has_faers,
                "has_social": has_social,
                "gap_status": gap_status,
                "summary": f"Label gap analysis: {gap_status}"
            }
            
        except Exception as e:
            logger.error(f"Label gap tool error: {e}")
            return {
                "tool": self.name,
                "error": str(e),
                "drug": drug,
                "reaction": reaction
            }

