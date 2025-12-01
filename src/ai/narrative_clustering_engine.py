"""
Narrative Semantic Clustering Engine for Pharmacovigilance (CHUNK 6.11.12)
Uses LLM embeddings, UMAP dimensionality reduction, and HDBSCAN clustering
to detect hidden patterns in case narratives.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import json

# Optional dependencies for clustering
try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False


class NarrativeClusteringEngine:
    """
    Narrative clustering engine using embeddings and clustering algorithms.
    Detects hidden patterns in case narratives that simple filters cannot catch.
    """
    
    def __init__(self, use_openai_embeddings: bool = True):
        """
        Initialize the narrative clustering engine.
        
        Args:
            use_openai_embeddings: If True, use OpenAI embeddings (requires API key).
                                  If False, use TF-IDF or other local methods.
        """
        self.use_openai_embeddings = use_openai_embeddings
    
    def _find_narrative_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find narrative column by checking common names."""
        narrative_cols = ["narrative", "case_narrative", "description", "case_description", "text"]
        for col in narrative_cols:
            if col in df.columns:
                return col
        return None
    
    async def generate_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        Generate embeddings for narratives using OpenAI or local methods.
        
        Args:
            texts: List of narrative texts
            
        Returns:
            Numpy array of embeddings or None if generation fails
        """
        if not texts or len(texts) == 0:
            return None
        
        # Try OpenAI embeddings if available and enabled
        if self.use_openai_embeddings:
            try:
                import os
                from openai import OpenAI
                
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    # Fallback to local method
                    return self._generate_local_embeddings(texts)
                
                client = OpenAI(api_key=api_key, timeout=30.0)
                
                # Batch embeddings (OpenAI supports up to 2048 inputs per request)
                batch_size = 100
                all_embeddings = []
                
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i+batch_size]
                    try:
                        # Use synchronous API call (not async) for Streamlit compatibility
                        response = client.embeddings.create(
                            model="text-embedding-3-small",
                            input=[str(t) for t in batch]
                        )
                        batch_embeddings = [e.embedding for e in response.data]
                        all_embeddings.extend(batch_embeddings)
                    except Exception:
                        # If batch fails, try individual texts
                        for text in batch:
                            try:
                                response = client.embeddings.create(
                                    model="text-embedding-3-small",
                                    input=[str(text)]
                                )
                                all_embeddings.append(response.data[0].embedding)
                            except Exception:
                                # Use zeros as fallback for failed embeddings
                                all_embeddings.append([0.0] * 1536)
                
                return np.array(all_embeddings)
                
            except Exception:
                # Fallback to local method
                return self._generate_local_embeddings(texts)
        
        # Use local embeddings
        return self._generate_local_embeddings(texts)
    
    def _generate_local_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings using TF-IDF (local method, no API required).
        
        Args:
            texts: List of narrative texts
            
        Returns:
            Numpy array of TF-IDF embeddings
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            vectorizer = TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                stop_words='english'
            )
            
            embeddings = vectorizer.fit_transform(texts)
            # Convert sparse matrix to dense numpy array
            return embeddings.toarray()
            
        except Exception:
            # Ultimate fallback: return random embeddings (not useful but prevents crash)
            return np.random.rand(len(texts), 100)
    
    def cluster_narratives(
        self,
        df: pd.DataFrame,
        drug: Optional[str] = None,
        reaction: Optional[str] = None,
        min_cluster_size: int = 5,
        max_clusters: int = 20
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Cluster narratives to detect hidden patterns (CHUNK 6.11.12).
        
        Args:
            df: DataFrame with case data
            drug: Optional drug name to filter
            reaction: Optional reaction name to filter
            min_cluster_size: Minimum number of narratives in a cluster
            max_clusters: Maximum number of clusters to return
            
        Returns:
            List of cluster dictionaries or None if clustering fails
        """
        if df is None or len(df) == 0:
            return None
        
        # Find narrative column
        narrative_col = self._find_narrative_column(df)
        if not narrative_col:
            return None
        
        # Filter by drug/reaction if provided
        filtered = df.copy()
        
        if drug:
            drug_col = None
            for col in ["drug_name", "drug", "drug_concept_name"]:
                if col in filtered.columns:
                    drug_col = col
                    break
            
            if drug_col:
                filtered = filtered[
                    filtered[drug_col].astype(str).str.contains(str(drug), na=False, case=False)
                ]
        
        if reaction:
            reaction_col = None
            for col in ["reaction", "reaction_pt", "reaction_name"]:
                if col in filtered.columns:
                    reaction_col = col
                    break
            
            if reaction_col:
                filtered = filtered[
                    filtered[reaction_col].astype(str).str.contains(str(reaction), na=False, case=False)
                ]
        
        # Extract narratives
        narratives = filtered[narrative_col].dropna().astype(str)
        # Filter out very short narratives
        narratives = narratives[narratives.str.len() > 20]
        
        if len(narratives) < 8:
            return None
        
        narratives_list = narratives.tolist()
        narrative_indices = narratives.index.tolist()
        
        try:
            # Step 1: Generate embeddings
            embeddings = self.generate_embeddings(narratives_list)
            if embeddings is None or len(embeddings) == 0:
                return None
            
            # Step 2: Dimensionality reduction (if UMAP available)
            if UMAP_AVAILABLE and embeddings.shape[1] > 50:
                try:
                    reducer = umap.UMAP(
                        n_neighbors=min(15, len(narratives_list) - 1),
                        min_dist=0.1,
                        metric='cosine',
                        n_components=min(50, embeddings.shape[1] - 1),
                        random_state=42
                    )
                    reduced_embeddings = reducer.fit_transform(embeddings)
                except Exception:
                    # If UMAP fails, use original embeddings
                    reduced_embeddings = embeddings
            else:
                reduced_embeddings = embeddings
            
            # Step 3: Clustering via HDBSCAN (if available)
            if HDBSCAN_AVAILABLE and len(narratives_list) >= min_cluster_size * 2:
                try:
                    clusterer = hdbscan.HDBSCAN(
                        min_cluster_size=max(min_cluster_size, 3),
                        min_samples=max(2, min_cluster_size // 2),
                        metric='euclidean'
                    )
                    cluster_labels = clusterer.fit_predict(reduced_embeddings)
                except Exception:
                    # Fallback: use simple K-means-like approach
                    cluster_labels = self._simple_clustering(reduced_embeddings, min_cluster_size)
            else:
                # Fallback: use simple clustering
                cluster_labels = self._simple_clustering(reduced_embeddings, min_cluster_size)
            
            # Step 4: Group narratives by cluster
            clusters = {}
            for idx, label in enumerate(cluster_labels):
                if label == -1:  # HDBSCAN noise/outliers
                    continue
                
                cluster_id = int(label)
                if cluster_id not in clusters:
                    clusters[cluster_id] = {
                        "narratives": [],
                        "indices": []
                    }
                clusters[cluster_id]["narratives"].append(narratives_list[idx])
                clusters[cluster_id]["indices"].append(narrative_indices[idx])
            
            if not clusters:
                return None
            
            # Step 5: Prepare cluster results (will be enriched with LLM in trend_alerts)
            results = []
            for cluster_id, cluster_data in list(clusters.items())[:max_clusters]:
                narratives_in_cluster = cluster_data["narratives"]
                
                results.append({
                    "cluster_id": cluster_id,
                    "size": len(narratives_in_cluster),
                    "examples": narratives_in_cluster[:5],  # Top 5 examples
                    "all_narratives": narratives_in_cluster,  # For LLM labeling
                    "indices": cluster_data["indices"][:10]  # First 10 case indices
                })
            
            return results if results else None
            
        except Exception as e:
            # Fail gracefully
            print(f"Narrative clustering error: {e}")
            return None
    
    def _simple_clustering(self, embeddings: np.ndarray, min_cluster_size: int) -> np.ndarray:
        """
        Simple clustering fallback using cosine similarity thresholding.
        
        Args:
            embeddings: Embedding matrix
            min_cluster_size: Minimum cluster size
            
        Returns:
            Cluster labels array
        """
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            from sklearn.cluster import AgglomerativeClustering
            
            # Use hierarchical clustering as fallback
            if len(embeddings) < min_cluster_size * 2:
                # Too few points, return all as noise
                return np.array([-1] * len(embeddings))
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(embeddings)
            
            # Use agglomerative clustering
            n_clusters = max(2, len(embeddings) // min_cluster_size)
            n_clusters = min(n_clusters, len(embeddings) // 2)  # Don't create too many clusters
            
            clusterer = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='average',
                metric='cosine'
            )
            
            labels = clusterer.fit_predict(embeddings)
            return labels
            
        except Exception:
            # Ultimate fallback: no clustering
            return np.array([-1] * len(embeddings))

