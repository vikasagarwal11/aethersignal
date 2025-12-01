"""
Tool Router - Routes tool calls for Safety Copilot
"""

import logging
from typing import Dict, Any, Optional
from .tools import (
    FAERSTool,
    SocialTool,
    LiteratureTool,
    MechanismAITool,
    CausalityTool,
    LabelGapTool,
    NoveltyTool,
    TrendTool
)

logger = logging.getLogger(__name__)


class ToolRouter:
    """Routes tool calls to appropriate tool implementations."""
    
    def __init__(self):
        self.tools = {
            "faers_query": FAERSTool(),
            "social_query": SocialTool(),
            "literature_query": LiteratureTool(),
            "mechanism_ai": MechanismAITool(),
            "causality": CausalityTool(),
            "label_gap": LabelGapTool(),
            "novelty": NoveltyTool(),
            "trend": TrendTool()
        }
    
    def handle(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a tool call.
        
        Args:
            tool_name: Name of the tool to call
            params: Tool parameters
        
        Returns:
            Tool result dictionary
        """
        tool = self.tools.get(tool_name)
        
        if not tool:
            logger.warning(f"Unknown tool: {tool_name}")
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        try:
            result = tool.run(**params)
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} error: {e}")
            return {
                "error": str(e),
                "tool": tool_name
            }
    
    def list_tools(self) -> Dict[str, str]:
        """
        List all available tools and their descriptions.
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {
            tool_name: tool.description
            for tool_name, tool in self.tools.items()
        }

