"""
Reaction Intelligence Core - Unified orchestrator for all reaction processing.
Combines extraction, normalization, embeddings, clustering, and co-occurrence.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
import logging

from .extraction_engine import extract_all_reactions
from .reaction_embeddings import ReactionEmbeddingEngine
from .reaction_clusters import ReactionClusterEngine
from .reaction_cooccurrence import ReactionCoOccurrenceEngine
from .reaction_discovery import ReactionDiscoveryEngine
from .reaction_similarity import ReactionSimilarityEngine
from src.normalization.reaction_normalizer import ReactionNormalizer

logger = logging.getLogger(__name__)


class ReactionIntelligenceCore:
    """
    Master orchestrator for reaction intelligence.
    Combines all reaction processing capabilities.
    """
    
    def __init__(
        self,
        embedding_engine: Optional[ReactionEmbeddingEngine] = None,
        normalizer: Optional[ReactionNormalizer] = None,
        supabase_client=None
    ):
        """
        Initialize reaction intelligence core.
        
        Args:
            embedding_engine: Optional embedding engine
            normalizer: Optional reaction normalizer
            supabase_client: Optional Supabase client
        """
        self.embedding_engine = embedding_engine or ReactionEmbeddingEngine()
        self.normalizer = normalizer or ReactionNormalizer(
            embedding_engine=self.embedding_engine,
            use_llm=False
        )
        self.cluster_engine = ReactionClusterEngine()
        self.cooccur_engine = ReactionCoOccurrenceEngine()
        self.discovery_engine = ReactionDiscoveryEngine(self.normalizer)
        self.similarity_engine = ReactionSimilarityEngine(supabase_client)
    
    def process_posts(
        self,
        posts: List[Dict],
        drug: Optional[str] = None,
        generate_embeddings: bool = True,
        cluster_reactions: bool = False
    ) -> pd.DataFrame:
        """
        Process social media posts through full intelligence pipeline.
        
        Args:
            posts: List of post dictionaries
            drug: Drug name
            generate_embeddings: Whether to generate embeddings
            cluster_reactions: Whether to cluster reactions
        
        Returns:
            DataFrame with processed reactions
        """
        all_rows = []
        all_reactions = []
        all_embeddings = []
        
        for post in posts:
            text = post.get("text", "")
            post_id = post.get("post_id", "")
            timestamp = post.get("created_date") or post.get("created_utc")
            
            # Extract reactions
            result = extract_all_reactions(text, drug, use_llm=True)
            
            reactions = result.get("reactions", [])
            if not reactions:
                continue
            
            # Process each reaction
            for reaction in reactions:
                # Normalize reaction
                normalized = self.normalizer.normalize(reaction, drug)
                
                # Generate embedding if requested
                embedding = None
                if generate_embeddings:
                    embedding = self.embedding_engine.embed(reaction)
                    if embedding is not None:
                        all_embeddings.append(embedding)
                        # Add to vector store
                        self.similarity_engine.add_to_store(
                            reaction_raw=reaction,
                            reaction_norm=normalized["pt"],
                            embedding=embedding,
                            drug=drug,
                            source="social"
                        )
                
                # Create row
                row = {
                    "post_id": post_id,
                    "timestamp": timestamp,
                    "drug": drug or "",
                    "reaction_raw": reaction,
                    "reaction": normalized["pt"],
                    "reaction_category": normalized["category"],
                    "normalization_method": normalized["method"],
                    "normalization_confidence": normalized["confidence"],
                    "severity_label": result.get("severity_label", "unknown"),
                    "severity_score": result.get("severity_score", 0.1),
                    "confidence": result.get("confidence", 0.0),
                    "text": text[:500],  # Truncate
                    "source": "social",
                    "has_embedding": embedding is not None
                }
                
                all_rows.append(row)
                all_reactions.append(reaction)
        
        df = pd.DataFrame(all_rows)
        
        # Add clustering if requested
        if cluster_reactions and all_embeddings:
            cluster_result = self.cluster_engine.build_clusters(all_embeddings, all_reactions)
            if "labels" in cluster_result:
                df["cluster_id"] = cluster_result["labels"][:len(df)]
        
        return df
    
    def analyze_cooccurrence(
        self,
        df: pd.DataFrame,
        drug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze co-occurrence patterns in reactions.
        
        Args:
            df: DataFrame with reactions
            drug: Optional drug filter
        
        Returns:
            Co-occurrence analysis results
        """
        if df.empty or "reaction" not in df.columns:
            return {"pairs": {}, "triplets": {}, "network_data": []}
        
        # Group by post_id to get reaction lists
        if "post_id" in df.columns:
            reaction_groups = df.groupby("post_id")["reaction"].apply(list).tolist()
        else:
            # Fallback: group by timestamp
            reaction_groups = df.groupby("timestamp")["reaction"].apply(list).tolist()
        
        return self.cooccur_engine.analyze_cooccurrence(reaction_groups, drug)
    
    def discover_emerging(
        self,
        df: pd.DataFrame,
        drug: Optional[str] = None,
        min_count: int = 5
    ) -> pd.DataFrame:
        """
        Discover emerging reactions not in dictionary.
        
        Args:
            df: DataFrame with reactions
            drug: Optional drug filter
            min_count: Minimum occurrence count
        
        Returns:
            DataFrame with emerging reactions
        """
        return self.discovery_engine.discover_emerging_reactions(
            df,
            reaction_col="reaction_raw",
            min_count=min_count,
            drug=drug
        )
    
    def find_similar_reactions(
        self,
        reaction: str,
        k: int = 5,
        drug: Optional[str] = None
    ) -> List[Dict]:
        """
        Find similar reactions using semantic similarity.
        
        Args:
            reaction: Reaction term
            k: Number of results
            drug: Optional drug filter
        
        Returns:
            List of similar reactions
        """
        embedding = self.embedding_engine.embed(reaction)
        if embedding is None:
            return []
        
        return self.similarity_engine.find_similar_reactions(embedding, k, drug)

