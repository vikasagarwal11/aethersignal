"""
Biological Pathway Graph (Phase 3D.4A)
Knowledge graph connecting drugs → targets → pathways → physiological effects → AEs.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PathwayNode:
    """Node in biological pathway graph."""
    node_id: str
    node_type: str  # drug, target, pathway, tissue, physiological_effect, symptom, ae
    name: str
    metadata: Dict[str, Any]


@dataclass
class PathwayEdge:
    """Edge in biological pathway graph."""
    source_id: str
    target_id: str
    edge_type: str  # activates, inhibits, modulates, affects, causes, leads_to
    weight: float  # 0-1 confidence/strength
    metadata: Dict[str, Any]


class BiologicalPathwayGraph:
    """
    Biological pathway knowledge graph.
    Connects drugs → targets → pathways → physiological effects → AEs.
    """
    
    def __init__(self):
        """Initialize pathway graph."""
        self.nodes: Dict[str, PathwayNode] = {}
        self.edges: List[PathwayEdge] = []
        self._load_initial_data()
    
    def _load_initial_data(self):
        """Load initial pathway data from free sources."""
        # This would load from DrugBank, ChEMBL, KEGG, Reactome
        # For now, we'll use a simplified structure
        pass
    
    def add_node(self, node: PathwayNode):
        """Add node to graph."""
        self.nodes[node.node_id] = node
    
    def add_edge(self, edge: PathwayEdge):
        """Add edge to graph."""
        self.edges.append(edge)
    
    def find_path(
        self,
        drug_id: str,
        ae_id: str,
        max_depth: int = 5
    ) -> List[List[str]]:
        """
        Find paths from drug to AE.
        
        Args:
            drug_id: Drug node ID
            ae_id: AE node ID
            max_depth: Maximum path depth
        
        Returns:
            List of paths (each path is a list of node IDs)
        """
        paths = []
        
        def dfs(current_id: str, target_id: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            if current_id == target_id:
                paths.append(path.copy())
                return
            
            # Find outgoing edges
            for edge in self.edges:
                if edge.source_id == current_id and edge.target_id not in path:
                    path.append(edge.target_id)
                    dfs(edge.target_id, target_id, path, depth + 1)
                    path.pop()
        
        dfs(drug_id, ae_id, [drug_id], 0)
        return paths
    
    def get_mechanism_chain(
        self,
        drug_name: str,
        reaction_name: str
    ) -> List[str]:
        """
        Get mechanistic chain from drug to reaction.
        
        Args:
            drug_name: Drug name
            reaction_name: Reaction name
        
        Returns:
            List of mechanism steps (human-readable)
        """
        # Find drug and reaction nodes
        drug_node = None
        reaction_node = None
        
        for node in self.nodes.values():
            if node.node_type == "drug" and drug_name.lower() in node.name.lower():
                drug_node = node
            if node.node_type == "ae" and reaction_name.lower() in node.name.lower():
                reaction_node = node
        
        if not drug_node or not reaction_node:
            return []
        
        # Find paths
        paths = self.find_path(drug_node.node_id, reaction_node.node_id)
        
        if not paths:
            return []
        
        # Convert shortest path to human-readable chain
        shortest_path = min(paths, key=len)
        chain = []
        
        for i, node_id in enumerate(shortest_path):
            node = self.nodes.get(node_id)
            if node:
                if i == 0:
                    chain.append(f"{node.name} activates")
                elif i < len(shortest_path) - 1:
                    # Find edge type
                    for edge in self.edges:
                        if edge.source_id == shortest_path[i-1] and edge.target_id == node_id:
                            if edge.edge_type == "activates":
                                chain.append(f"{node.name}")
                            elif edge.edge_type == "inhibits":
                                chain.append(f"{node.name} (inhibited)")
                            elif edge.edge_type == "causes":
                                chain.append(f"which causes {node.name}")
                            else:
                                chain.append(f"→ {node.name}")
                            break
                else:
                    chain.append(f"leading to {node.name}")
        
        return chain
    
    def get_targets(self, drug_name: str) -> List[str]:
        """Get drug targets."""
        targets = []
        
        drug_node = None
        for node in self.nodes.values():
            if node.node_type == "drug" and drug_name.lower() in node.name.lower():
                drug_node = node
                break
        
        if drug_node:
            for edge in self.edges:
                if edge.source_id == drug_node.node_id:
                    target_node = self.nodes.get(edge.target_id)
                    if target_node and target_node.node_type == "target":
                        targets.append(target_node.name)
        
        return targets
    
    def get_pathways(self, target_name: str) -> List[str]:
        """Get pathways associated with target."""
        pathways = []
        
        target_node = None
        for node in self.nodes.values():
            if node.node_type == "target" and target_name.lower() in node.name.lower():
                target_node = node
                break
        
        if target_node:
            for edge in self.edges:
                if edge.source_id == target_node.node_id:
                    pathway_node = self.nodes.get(edge.target_id)
                    if pathway_node and pathway_node.node_type == "pathway":
                        pathways.append(pathway_node.name)
        
        return pathways

