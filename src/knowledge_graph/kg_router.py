"""
KG Router - Selects best mechanism paths
"""

from typing import Dict, Any, Optional, List
from .kg_core import KnowledgeGraph
import logging

logger = logging.getLogger(__name__)


class KGRouter:
    """
    Determines:
    - Drug → Reaction path
    - Most probable mechanism
    - Biological pathway chains
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def find_mechanistic_path(self, drug: str, reaction: str) -> Optional[List[str]]:
        """Return best mechanistic explanation chain."""
        return self.kg.shortest_path(drug, reaction)
    
    def find_all_paths(self, drug: str, reaction: str, max_length: int = 5) -> List[List[str]]:
        """Find all possible paths between drug and reaction."""
        return self.kg.all_paths(drug, reaction, max_length)
    
    def explain(self, drug: str, reaction: str) -> Dict[str, Any]:
        """
        Generate mechanistic explanation.
        
        Args:
            drug: Drug name
            reaction: Reaction name
        
        Returns:
            Explanation dictionary
        """
        # Find shortest path
        path = self.find_mechanistic_path(drug, reaction)
        
        # Find all paths
        all_paths = self.find_all_paths(drug, reaction)
        
        # Get path details
        path_details = []
        if path:
            for i in range(len(path) - 1):
                source = path[i]
                target = path[i + 1]
                edge_attrs = self.kg.get_edge_attributes(source, target)
                path_details.append({
                    "from": source,
                    "to": target,
                    "relation": edge_attrs.get("relation", "unknown"),
                    "weight": edge_attrs.get("weight", 1.0),
                    "source": edge_attrs.get("source", "unknown")
                })
        
        return {
            "drug": drug,
            "reaction": reaction,
            "path_found": path is not None,
            "mechanistic_path": path,
            "path_details": path_details,
            "all_paths_count": len(all_paths),
            "all_paths": all_paths[:5]  # Top 5 paths
        }
    
    def get_drug_neighbors(self, drug: str) -> Dict[str, List[str]]:
        """Get all neighbors of a drug (reactions, pathways, targets)."""
        neighbors = self.kg.get_neighbors(drug)
        
        result = {
            "reactions": [],
            "pathways": [],
            "targets": [],
            "other": []
        }
        
        for neighbor in neighbors:
            node_attrs = self.kg.get_node_attributes(neighbor)
            node_type = node_attrs.get("type", "unknown")
            
            if node_type == "reaction":
                result["reactions"].append(neighbor)
            elif node_type == "pathway":
                result["pathways"].append(neighbor)
            elif node_type == "target":
                result["targets"].append(neighbor)
            else:
                result["other"].append(neighbor)
        
        return result

