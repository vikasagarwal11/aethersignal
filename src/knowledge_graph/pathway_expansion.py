"""
Pathway Expansion Engine - Expands biological pathways in KG
Enhanced with embedding-based similarity search
"""

import numpy as np
from typing import Dict, Any, List, Optional
from .kg_core import KnowledgeGraph
from .embeddings_gpu import GPUEmbeddingEngine
import logging

logger = logging.getLogger(__name__)


class PathwayExpansionEngine:
    """
    Expands pathways in the knowledge graph using:
    - Literature data
    - Biological databases
    - Mechanism inference
    """
    
    def __init__(self, kg: KnowledgeGraph, embedding_engine: Optional[GPUEmbeddingEngine] = None):
        self.kg = kg
        self.emb = embedding_engine
        self.corpus = []
        self.embeddings = None
    
    def expand_drug_pathway(self, drug: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Expand pathways for a drug.
        
        Args:
            drug: Drug name
            max_depth: Maximum expansion depth
        
        Returns:
            Expanded pathway information
        """
        if drug not in self.kg.g:
            return {"error": "Drug not in knowledge graph"}
        
        expanded = {
            "drug": drug,
            "targets": [],
            "pathways": [],
            "reactions": [],
            "depth": 0
        }
        
        # Get direct neighbors
        neighbors = self.kg.get_neighbors(drug)
        
        for neighbor in neighbors:
            node_attrs = self.kg.get_node_attributes(neighbor)
            node_type = node_attrs.get("type")
            
            if node_type == "target":
                expanded["targets"].append(neighbor)
            elif node_type == "pathway":
                expanded["pathways"].append(neighbor)
            elif node_type == "reaction":
                expanded["reactions"].append(neighbor)
        
        # Expand pathways
        for pathway in expanded["pathways"]:
            pathway_reactions = self.kg.get_successors(pathway)
            expanded["reactions"].extend([r for r in pathway_reactions if r not in expanded["reactions"]])
        
        return expanded
    
    def infer_pathway_from_literature(self, drug: str, reaction: str) -> Optional[str]:
        """
        Infer pathway from literature data.
        
        Args:
            drug: Drug name
            reaction: Reaction name
        
        Returns:
            Inferred pathway name or None
        """
        # Try to find intermediate pathway nodes
        drug_neighbors = self.kg.get_neighbors(drug)
        reaction_predecessors = self.kg.get_predecessors(reaction)
        
        # Find common pathways
        common = set(drug_neighbors) & set(reaction_predecessors)
        
        pathway_nodes = [n for n in common if self.kg.get_node_attributes(n).get("type") == "pathway"]
        
        if pathway_nodes:
            return pathway_nodes[0]  # Return first pathway
        
        return None
    
    def add_pathway_from_mechanism(self, drug: str, target: str, pathway: str, reaction: str):
        """
        Add pathway chain from mechanism data.
        
        Args:
            drug: Drug name
            target: Drug target
            pathway: Biological pathway
            reaction: Adverse reaction
        """
        # Add nodes
        self.kg.add_drug(drug)
        self.kg.add_target(target)
        self.kg.add_pathway(pathway)
        self.kg.add_reaction(reaction)
        
        # Link chain
        self.kg.link_drug_target(drug, target, source="mechanism")
        self.kg.link_target_pathway(target, pathway, source="mechanism")
        self.kg.link_pathway_reaction(pathway, reaction, source="mechanism")
        
        logger.info(f"Added pathway chain: {drug} → {target} → {pathway} → {reaction}")
    
    def load_corpus(self, texts: List[str]):
        """
        Load pathway corpus for similarity search.
        
        Args:
            texts: List of pathway/mechanism text descriptions
        """
        if not self.emb:
            logger.warning("Embedding engine not available, corpus loading skipped")
            return
        
        self.corpus = texts
        self.embeddings = self.emb.encode(texts)
        self.emb.build_index(texts, self.embeddings)
        logger.info(f"Loaded {len(texts)} pathway texts into corpus")
    
    def find_related(self, query: str, k: int = 5) -> List[Dict[str, float]]:
        """
        Find related pathways using embedding similarity.
        
        Args:
            query: Query pathway/mechanism text
            k: Number of results
        
        Returns:
            List of related pathways with distances
        """
        if not self.emb or not self.corpus:
            return []
        
        try:
            distances, indices = self.emb.query(query, k)
            
            out = []
            for d, idx in zip(distances, indices):
                if idx < len(self.corpus):
                    out.append({
                        "text": self.corpus[idx],
                        "distance": float(d)
                    })
            return out
        except Exception as e:
            logger.error(f"Pathway similarity search error: {e}")
            return []

