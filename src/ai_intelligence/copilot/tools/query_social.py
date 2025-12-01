"""
Social Query Tool - Retrieve social media AE data
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SocialTool:
    """Tool for querying social media AE data."""
    
    name = "social_query"
    description = "Retrieve social media AE matches for a drug/reaction"
    
    def run(self, drug: Optional[str] = None, reaction: Optional[str] = None) -> Dict[str, Any]:
        """
        Run social media query.
        
        Args:
            drug: Drug name (optional)
            reaction: Reaction name (optional)
        
        Returns:
            Query results dictionary
        """
        try:
            from src.storage.federated_query_engine import FederatedQueryEngine
            from src.storage.unified_storage import UnifiedStorageEngine
            
            storage = UnifiedStorageEngine()
            query_engine = FederatedQueryEngine(storage)
            
            # Build query with source filter
            query_parts = ["source:social"]
            if drug:
                query_parts.append(f"drug:{drug}")
            if reaction:
                query_parts.append(f"reaction:{reaction}")
            
            query = " ".join(query_parts)
            results = query_engine.query(query, limit=50)
            
            return {
                "tool": self.name,
                "drug": drug,
                "reaction": reaction,
                "count": len(results) if results else 0,
                "results": results[:10] if results else [],
                "summary": f"Found {len(results) if results else 0} social media mentions"
            }
            
        except Exception as e:
            logger.error(f"Social query error: {e}")
            return {
                "tool": self.name,
                "error": str(e),
                "count": 0,
                "results": []
            }

