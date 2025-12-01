"""
Reaction Clustering Engine
Groups similar reactions using HDBSCAN clustering on embeddings.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import HDBSCAN
try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    logger.warning("HDBSCAN not available, clustering disabled")


class ReactionClusterEngine:
    """
    Clusters reaction embeddings to discover reaction families.
    """
    
    def __init__(self, min_cluster_size: int = 10, min_samples: int = 5):
        """
        Initialize cluster engine.
        
        Args:
            min_cluster_size: Minimum size for a cluster
            min_samples: Minimum samples for core point
        """
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.clusterer = None
    
    def build_clusters(
        self,
        embeddings: List[np.ndarray],
        reactions: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Build clusters from reaction embeddings.
        
        Args:
            embeddings: List of embedding vectors
            reactions: Optional list of reaction terms (for labeling)
        
        Returns:
            Dictionary with:
            - labels: Cluster labels (-1 = noise)
            - probabilities: Cluster membership probabilities
            - cluster_info: Information about each cluster
        """
        if not HDBSCAN_AVAILABLE:
            logger.warning("HDBSCAN not available, returning empty clusters")
            return {
                "labels": [-1] * len(embeddings),
                "probabilities": [0.0] * len(embeddings),
                "cluster_info": {}
            }
        
        if not embeddings or len(embeddings) < self.min_cluster_size:
            return {
                "labels": [-1] * len(embeddings),
                "probabilities": [0.0] * len(embeddings),
                "cluster_info": {}
            }
        
        try:
            # Convert to numpy array
            embedding_array = np.array(embeddings)
            
            # Build clusters
            self.clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric='euclidean'
            )
            
            labels = self.clusterer.fit_predict(embedding_array)
            probabilities = self.clusterer.probabilities_ if hasattr(self.clusterer, 'probabilities_') else [0.0] * len(labels)
            
            # Build cluster info
            cluster_info = {}
            unique_labels = set(labels)
            unique_labels.discard(-1)  # Remove noise
            
            for cluster_id in unique_labels:
                cluster_indices = [i for i, label in enumerate(labels) if label == cluster_id]
                cluster_reactions = [reactions[i] for i in cluster_indices] if reactions else []
                
                cluster_info[cluster_id] = {
                    "size": len(cluster_indices),
                    "reactions": cluster_reactions[:10],  # Top 10
                    "probability_mean": np.mean([probabilities[i] for i in cluster_indices]) if probabilities else 0.0
                }
            
            return {
                "labels": labels.tolist(),
                "probabilities": probabilities.tolist() if isinstance(probabilities, np.ndarray) else probabilities,
                "cluster_info": cluster_info
            }
        except Exception as e:
            logger.error(f"Clustering error: {str(e)}")
            return {
                "labels": [-1] * len(embeddings),
                "probabilities": [0.0] * len(embeddings),
                "cluster_info": {}
            }
    
    def get_cluster_summary(self, cluster_info: Dict) -> pd.DataFrame:
        """
        Get summary of clusters as DataFrame.
        
        Args:
            cluster_info: Cluster info from build_clusters
        
        Returns:
            DataFrame with cluster summaries
        """
        if not cluster_info:
            return pd.DataFrame()
        
        rows = []
        for cluster_id, info in cluster_info.items():
            rows.append({
                "cluster_id": cluster_id,
                "size": info["size"],
                "sample_reactions": ", ".join(info["reactions"][:5]),
                "avg_probability": info["probability_mean"]
            })
        
        return pd.DataFrame(rows)

