"""
Pathway Graph Builder - Auto-builds mechanistic knowledge graphs for visualization
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PathwayGraphBuilder:
    """
    Builds a mini knowledge-graph:
    drug → mechanism → pathway → symptom (reaction)
    """
    
    def __init__(self):
        pass
    
    def build(
        self,
        drug: str,
        reaction: str,
        pathways: Optional[List[Dict]] = None,
        mechanisms: Optional[List[str]] = None,
        targets: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build pathway graph structure.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            pathways: Optional list of pathway dictionaries
            mechanisms: Optional list of mechanism descriptions
            targets: Optional list of drug targets
        
        Returns:
            Graph structure with nodes and edges
        """
        nodes = []
        edges = []
        
        # Drug node
        nodes.append({
            "id": drug,
            "type": "drug",
            "label": drug
        })
        
        # Reaction node
        nodes.append({
            "id": reaction,
            "type": "reaction",
            "label": reaction
        })
        
        # Direct drug → reaction edge
        edges.append({
            "source": drug,
            "target": reaction,
            "type": "causal",
            "weight": 1.0
        })
        
        # Add targets if provided
        if targets:
            for target in targets:
                target_id = f"target_{target}"
                nodes.append({
                    "id": target_id,
                    "type": "target",
                    "label": target
                })
                edges.append({
                    "source": drug,
                    "target": target_id,
                    "type": "binds_to",
                    "weight": 1.0
                })
                edges.append({
                    "source": target_id,
                    "target": reaction,
                    "type": "leads_to",
                    "weight": 0.8
                })
        
        # Add pathways if provided
        if pathways:
            for idx, p in enumerate(pathways):
                pid = f"pathway_{idx}"
                pathway_text = p.get("text", p.get("name", f"Pathway {idx}"))
                
                nodes.append({
                    "id": pid,
                    "type": "pathway",
                    "label": pathway_text,
                    "distance": p.get("distance", 0.0)
                })
                
                # Connect drug → pathway
                edges.append({
                    "source": drug,
                    "target": pid,
                    "type": "modulates",
                    "weight": 0.9
                })
                
                # Connect pathway → reaction
                edges.append({
                    "source": pid,
                    "target": reaction,
                    "type": "evidence",
                    "weight": 0.8
                })
        
        # Add mechanisms if provided
        if mechanisms:
            for idx, mech in enumerate(mechanisms):
                mech_id = f"mechanism_{idx}"
                nodes.append({
                    "id": mech_id,
                    "type": "mechanism",
                    "label": mech[:50] + "..." if len(mech) > 50 else mech
                })
                edges.append({
                    "source": drug,
                    "target": mech_id,
                    "type": "activates",
                    "weight": 0.7
                })
                edges.append({
                    "source": mech_id,
                    "target": reaction,
                    "type": "causes",
                    "weight": 0.7
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    
    def build_from_kg_path(self, kg_path: List[str], kg) -> Dict[str, Any]:
        """
        Build graph from KG path.
        
        Args:
            kg_path: List of node names from KG
            kg: KnowledgeGraph instance
        
        Returns:
            Graph structure
        """
        if not kg_path or len(kg_path) < 2:
            return {"nodes": [], "edges": []}
        
        nodes = []
        edges = []
        
        for i, node_name in enumerate(kg_path):
            node_attrs = kg.get_node_attributes(node_name)
            node_type = node_attrs.get("type", "unknown")
            
            nodes.append({
                "id": node_name,
                "type": node_type,
                "label": node_name
            })
            
            # Add edge to next node
            if i < len(kg_path) - 1:
                next_node = kg_path[i + 1]
                edge_attrs = kg.get_edge_attributes(node_name, next_node)
                
                edges.append({
                    "source": node_name,
                    "target": next_node,
                    "type": edge_attrs.get("relation", "related_to"),
                    "weight": edge_attrs.get("weight", 1.0)
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }

