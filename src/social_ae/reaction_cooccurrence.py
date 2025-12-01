"""
Reaction Co-Occurrence Engine
Analyzes which reactions occur together (Drug × Reaction × Reaction networks).
"""

import itertools
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class ReactionCoOccurrenceEngine:
    """
    Analyzes co-occurrence patterns between reactions.
    """
    
    def __init__(self):
        """Initialize co-occurrence engine."""
        pass
    
    def analyze_cooccurrence(
        self,
        reactions_list: List[List[str]],
        drug: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Analyze co-occurrence patterns.
        
        Args:
            reactions_list: List of reaction lists (one per post/case)
            drug: Optional drug name for filtering
        
        Returns:
            Dictionary with:
            - pairs: Counter of reaction pairs
            - triplets: Counter of reaction triplets
            - network_data: Network graph data
        """
        if not reactions_list:
            return {
                "pairs": Counter(),
                "triplets": Counter(),
                "network_data": []
            }
        
        pairs = []
        triplets = []
        
        for reactions in reactions_list:
            # Filter out empty and normalize
            reactions = [r.strip().lower() for r in reactions if r and r.strip()]
            reactions = list(set(reactions))  # Deduplicate
            
            if len(reactions) < 2:
                continue
            
            # Extract pairs
            for pair in itertools.combinations(sorted(reactions), 2):
                pairs.append(pair)
            
            # Extract triplets
            if len(reactions) >= 3:
                for triplet in itertools.combinations(sorted(reactions), 3):
                    triplets.append(triplet)
        
        pair_counter = Counter(pairs)
        triplet_counter = Counter(triplets)
        
        # Build network data
        network_data = self._build_network_data(pair_counter)
        
        return {
            "pairs": pair_counter,
            "triplets": triplet_counter,
            "network_data": network_data
        }
    
    def _build_network_data(self, pair_counter: Counter) -> List[Dict]:
        """
        Build network graph data from pair counter.
        
        Args:
            pair_counter: Counter of reaction pairs
        
        Returns:
            List of network edges
        """
        network_data = []
        
        for (reaction1, reaction2), count in pair_counter.most_common(100):  # Top 100
            network_data.append({
                "source": reaction1,
                "target": reaction2,
                "weight": count,
                "strength": min(count / 10.0, 1.0)  # Normalize to 0-1
            })
        
        return network_data
    
    def get_top_pairs(self, pair_counter: Counter, top_n: int = 20) -> pd.DataFrame:
        """
        Get top co-occurring reaction pairs.
        
        Args:
            pair_counter: Counter of reaction pairs
            top_n: Number of top pairs to return
        
        Returns:
            DataFrame with top pairs
        """
        rows = []
        for (reaction1, reaction2), count in pair_counter.most_common(top_n):
            rows.append({
                "reaction1": reaction1,
                "reaction2": reaction2,
                "cooccurrence_count": count
            })
        
        return pd.DataFrame(rows)
    
    def get_reaction_clusters(self, pair_counter: Counter, min_weight: int = 3) -> Dict[str, List[str]]:
        """
        Identify reaction clusters based on co-occurrence.
        
        Args:
            pair_counter: Counter of reaction pairs
            min_weight: Minimum co-occurrence count to form cluster
        
        Returns:
            Dictionary mapping cluster names to reaction lists
        """
        # Build graph
        graph = defaultdict(set)
        for (r1, r2), count in pair_counter.items():
            if count >= min_weight:
                graph[r1].add(r2)
                graph[r2].add(r1)
        
        # Find connected components (clusters)
        visited = set()
        clusters = []
        
        for reaction in graph:
            if reaction not in visited:
                cluster = []
                stack = [reaction]
                
                while stack:
                    node = stack.pop()
                    if node not in visited:
                        visited.add(node)
                        cluster.append(node)
                        stack.extend(graph[node] - visited)
                
                if len(cluster) > 1:
                    clusters.append(cluster)
        
        # Name clusters by most common reaction
        cluster_dict = {}
        for i, cluster in enumerate(clusters):
            cluster_name = f"Cluster_{i+1}"
            cluster_dict[cluster_name] = cluster
        
        return cluster_dict

