"""
Knowledge Graph Core - Entity and relation management
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """
    Core KG built for:
    - Drugs
    - Reactions
    - Pathways
    - Mechanisms
    - Literature evidence
    - Social/FAERS co-occurrence edges
    """
    
    def __init__(self):
        self.g = nx.DiGraph()
    
    # ---------------------------
    # Node Adders
    # ---------------------------
    def add_drug(self, name: str, **attrs):
        """Add a drug node to the graph."""
        self.g.add_node(name, type="drug", **attrs)
    
    def add_reaction(self, name: str, **attrs):
        """Add a reaction node to the graph."""
        self.g.add_node(name, type="reaction", **attrs)
    
    def add_pathway(self, name: str, **attrs):
        """Add a pathway node to the graph."""
        self.g.add_node(name, type="pathway", **attrs)
    
    def add_mechanism(self, name: str, **attrs):
        """Add a mechanism node to the graph."""
        self.g.add_node(name, type="mechanism", **attrs)
    
    def add_gene(self, name: str, **attrs):
        """Add a gene node to the graph."""
        self.g.add_node(name, type="gene", **attrs)
    
    def add_target(self, name: str, **attrs):
        """Add a drug target node to the graph."""
        self.g.add_node(name, type="target", **attrs)
    
    # ---------------------------
    # Relation Adders
    # ---------------------------
    def link_drug_reaction(self, drug: str, reaction: str, weight: float = 1.0, **attrs):
        """Link a drug to a reaction with optional weight."""
        self.g.add_edge(drug, reaction, relation="causes", weight=weight, **attrs)
    
    def link_drug_pathway(self, drug: str, pathway: str, **attrs):
        """Link a drug to a pathway."""
        self.g.add_edge(drug, pathway, relation="modulates", **attrs)
    
    def link_pathway_reaction(self, pathway: str, reaction: str, **attrs):
        """Link a pathway to a reaction."""
        self.g.add_edge(pathway, reaction, relation="leads_to", **attrs)
    
    def link_mechanism_pathway(self, mechanism: str, pathway: str, **attrs):
        """Link a mechanism to a pathway."""
        self.g.add_edge(mechanism, pathway, relation="activates", **attrs)
    
    def link_drug_target(self, drug: str, target: str, **attrs):
        """Link a drug to its target."""
        self.g.add_edge(drug, target, relation="binds_to", **attrs)
    
    def link_target_pathway(self, target: str, pathway: str, **attrs):
        """Link a target to a pathway."""
        self.g.add_edge(target, pathway, relation="regulates", **attrs)
    
    # ---------------------------
    # Query
    # ---------------------------
    def get_neighbors(self, node: str) -> List[Any]:
        """Get all neighbors of a node."""
        return list(self.g.neighbors(node))
    
    def get_predecessors(self, node: str) -> List[Any]:
        """Get all predecessors of a node."""
        return list(self.g.predecessors(node))
    
    def get_successors(self, node: str) -> List[Any]:
        """Get all successors of a node."""
        return list(self.g.successors(node))
    
    def shortest_path(self, start: str, end: str) -> Optional[List[str]]:
        """Find shortest path between two nodes."""
        try:
            return nx.shortest_path(self.g, start, end)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def all_paths(self, start: str, end: str, max_length: int = 5) -> List[List[str]]:
        """Find all paths between two nodes up to max_length."""
        try:
            return list(nx.all_simple_paths(self.g, start, end, cutoff=max_length))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def get_node_attributes(self, node: str) -> Dict[str, Any]:
        """Get all attributes of a node."""
        return self.g.nodes[node] if node in self.g else {}
    
    def get_edge_attributes(self, source: str, target: str) -> Dict[str, Any]:
        """Get all attributes of an edge."""
        return self.g.edges[source, target] if self.g.has_edge(source, target) else {}
    
    def export(self) -> Dict:
        """Export graph to dictionary format."""
        return nx.node_link_data(self.g)
    
    def import_graph(self, data: Dict):
        """Import graph from dictionary format."""
        self.g = nx.node_link_graph(data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "nodes": self.g.number_of_nodes(),
            "edges": self.g.number_of_edges(),
            "drugs": len([n for n, d in self.g.nodes(data=True) if d.get("type") == "drug"]),
            "reactions": len([n for n, d in self.g.nodes(data=True) if d.get("type") == "reaction"]),
            "pathways": len([n for n, d in self.g.nodes(data=True) if d.get("type") == "pathway"]),
            "mechanisms": len([n for n, d in self.g.nodes(data=True) if d.get("type") == "mechanism"]),
        }

