"""
FAERS Query Tool - Retrieve FAERS reports
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FAERSTool:
    """Tool for querying FAERS data."""
    
    name = "faers_query"
    description = "Retrieve FAERS reports for a given drug or reaction"
    
    def run(self, drug: Optional[str] = None, reaction: Optional[str] = None) -> Dict[str, Any]:
        """
        Run FAERS query.
        
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
            
            # Build query
            query_parts = []
            if drug:
                query_parts.append(f"drug:{drug}")
            if reaction:
                query_parts.append(f"reaction:{reaction}")
            
            query = " ".join(query_parts) if query_parts else "all"
            
            results = query_engine.query(query, limit=50)
            
            return {
                "tool": self.name,
                "drug": drug,
                "reaction": reaction,
                "count": len(results) if results else 0,
                "results": results[:10] if results else [],  # Return top 10
                "summary": f"Found {len(results) if results else 0} FAERS reports"
            }
            
        except Exception as e:
            logger.error(f"FAERS query error: {e}")
            return {
                "tool": self.name,
                "error": str(e),
                "count": 0,
                "results": []
            }

