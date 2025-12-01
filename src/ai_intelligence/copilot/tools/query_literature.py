"""
Literature Query Tool - Retrieve literature evidence
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LiteratureTool:
    """Tool for querying literature (PubMed) evidence."""
    
    name = "literature_query"
    description = "Retrieve literature (PubMed) evidence for a drug/reaction"
    
    def run(self, drug: Optional[str] = None, reaction: Optional[str] = None) -> Dict[str, Any]:
        """
        Run literature query.
        
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
            query_parts = ["source:literature"]
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
                "summary": f"Found {len(results) if results else 0} literature references"
            }
            
        except Exception as e:
            logger.error(f"Literature query error: {e}")
            return {
                "tool": self.name,
                "error": str(e),
                "count": 0,
                "results": []
            }

