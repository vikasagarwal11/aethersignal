"""
Cross-Signal Correlation Engine (CHUNK 6.28)
Identifies relationships across multiple signals, drugs, and reactions.

This engine detects:
- Class effects
- Cross-drug correlations
- Cross-reaction patterns
- Shared biological pathways
- Hidden correlations
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

try:
    from sklearn.cluster import DBSCAN
    from sklearn.metrics import pairwise_distances
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class SignalCluster:
    """Represents a cluster of correlated signals."""
    cluster_id: int
    signals: List[str]  # List of drug-reaction pairs
    correlation_strength: float
    cluster_type: str  # "class_effect", "reaction_cluster", "drug_cluster"
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "signals": self.signals,
            "correlation_strength": self.correlation_strength,
            "cluster_type": self.cluster_type,
            "description": self.description
        }


class CrossSignalCorrelationEngine:
    """
    Detects cross-signal correlations and class effects.
    
    Identifies:
    - Signals that co-occur across drugs (reaction clusters)
    - Signals that cluster by drug (class effects)
    - Cross-drug correlations
    - Hidden patterns across multiple signals
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with DataFrame.
        
        Args:
            df: Safety data DataFrame
        """
        self.df = df.copy()
    
    def build_matrix(self) -> pd.DataFrame:
        """
        Build drug × reaction matrix.
        
        Returns:
            DataFrame with drugs as rows, reactions as columns
        """
        # Find column names
        drug_col = self._find_column(self.df, ["drug", "drug_name", "drug_normalized"])
        reaction_col = self._find_column(self.df, ["reaction", "reaction_pt", "reaction_normalized"])
        
        if not drug_col or not reaction_col:
            return pd.DataFrame()
        
        # Build matrix
        mat = (
            self.df.groupby([drug_col, reaction_col])
            .size()
            .unstack(fill_value=0)
        )
        
        return mat
    
    def compute_signal_corr(self, mat: pd.DataFrame) -> pd.DataFrame:
        """
        Compute correlation matrix between drugs (signals).
        
        Args:
            mat: Drug × Reaction matrix
            
        Returns:
            Correlation matrix (drug × drug)
        """
        if mat.empty:
            return pd.DataFrame()
        
        # Transpose to get reactions as rows, drugs as columns
        # Then correlate drugs (columns)
        corr = mat.T.corr(method="pearson")
        corr = corr.fillna(0)
        
        return corr
    
    def detect_clusters(self, corr: pd.DataFrame, min_correlation: float = 0.5) -> List[SignalCluster]:
        """
        Detect clusters of correlated signals using DBSCAN.
        
        Args:
            corr: Correlation matrix
            min_correlation: Minimum correlation to consider as cluster
            
        Returns:
            List of SignalCluster objects
        """
        if not SKLEARN_AVAILABLE or corr.empty:
            return []
        
        # Convert correlation to distance (1 - correlation)
        dist = 1 - corr.abs()
        
        # Use DBSCAN to find clusters
        eps = 1.0 - min_correlation  # Distance threshold
        db = DBSCAN(eps=eps, min_samples=2, metric="precomputed")
        labels = db.fit_predict(dist.values)
        
        clusters = []
        unique_labels = set(labels) - {-1}  # Exclude noise
        
        for label in unique_labels:
            mask = labels == label
            cluster_drugs = corr.columns[mask].tolist()
            
            if len(cluster_drugs) < 2:
                continue
            
            # Compute average correlation within cluster
            cluster_corr = corr.loc[cluster_drugs, cluster_drugs]
            avg_corr = cluster_corr.values[np.triu_indices(len(cluster_drugs), k=1)].mean()
            
            # Determine cluster type
            cluster_type = self._classify_cluster_type(cluster_drugs)
            
            clusters.append(SignalCluster(
                cluster_id=int(label),
                signals=cluster_drugs,
                correlation_strength=float(avg_corr),
                cluster_type=cluster_type,
                description=self._describe_cluster(cluster_drugs, cluster_type)
            ))
        
        return clusters
    
    def build_graph(self, corr: pd.DataFrame, min_correlation: float = 0.5) -> Dict[str, Any]:
        """
        Build network graph for visualization.
        
        Args:
            corr: Correlation matrix
            min_correlation: Minimum correlation to include as edge
            
        Returns:
            Dictionary with nodes and edges for network visualization
        """
        edges = []
        
        for i, drug_a in enumerate(corr.columns):
            for drug_b in corr.columns[i+1:]:
                strength = corr.loc[drug_a, drug_b]
                
                if abs(strength) >= min_correlation:
                    edges.append({
                        "source": str(drug_a),
                        "target": str(drug_b),
                        "corr": float(strength),
                        "weight": abs(strength)
                    })
        
        return {
            "nodes": [{"id": str(drug), "label": str(drug)} for drug in corr.columns],
            "edges": edges
        }
    
    def detect_class_effects(self, mat: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect class effects by grouping drugs with similar reaction patterns.
        
        Args:
            mat: Drug × Reaction matrix
            
        Returns:
            List of class effect findings
        """
        if mat.empty:
            return []
        
        # Compute drug-drug correlation (based on reaction patterns)
        drug_corr = mat.T.corr()
        
        # Find groups of drugs with high correlation (>0.6)
        class_effects = []
        processed = set()
        
        for drug_a in drug_corr.columns:
            if drug_a in processed:
                continue
            
            similar_drugs = []
            for drug_b in drug_corr.columns:
                if drug_a == drug_b or drug_b in processed:
                    continue
                
                corr_val = drug_corr.loc[drug_a, drug_b]
                if corr_val > 0.6:
                    similar_drugs.append((drug_b, corr_val))
                    processed.add(drug_b)
            
            if similar_drugs:
                all_drugs = [drug_a] + [d for d, _ in similar_drugs]
                processed.add(drug_a)
                
                # Find common reactions
                common_reactions = []
                for reaction in mat.columns:
                    if mat.loc[all_drugs, reaction].sum() > 0:
                        common_reactions.append(reaction)
                
                class_effects.append({
                    "drugs": all_drugs,
                    "correlation_strength": np.mean([c for _, c in similar_drugs]),
                    "common_reactions": common_reactions[:5],  # Top 5
                    "type": "potential_class_effect"
                })
        
        return class_effects
    
    def run(self, min_correlation: float = 0.5) -> Dict[str, Any]:
        """
        Run complete cross-signal correlation analysis.
        
        Args:
            min_correlation: Minimum correlation threshold
            
        Returns:
            Dictionary with all analysis results
        """
        # Step 1: Build matrix
        mat = self.build_matrix()
        
        if mat.empty:
            return {
                "matrix": None,
                "corr_matrix": None,
                "clusters": [],
                "graph": {"nodes": [], "edges": []},
                "class_effects": []
            }
        
        # Step 2: Compute correlation
        corr = self.compute_signal_corr(mat)
        
        # Step 3: Detect clusters
        clusters = self.detect_clusters(corr, min_correlation)
        
        # Step 4: Build graph
        graph = self.build_graph(corr, min_correlation)
        
        # Step 5: Detect class effects
        class_effects = self.detect_class_effects(mat)
        
        return {
            "matrix": mat.to_dict() if not mat.empty else None,
            "corr_matrix": corr.to_dict() if not corr.empty else None,
            "clusters": [c.to_dict() for c in clusters],
            "graph": graph,
            "class_effects": class_effects
        }
    
    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        """Find column in DataFrame."""
        for candidate in candidates:
            if candidate in df.columns:
                return candidate
        return None
    
    def _classify_cluster_type(self, drugs: List[str]) -> str:
        """Classify cluster type based on drug names."""
        # Simple heuristic - in production, use drug class database
        drug_lower = [str(d).lower() for d in drugs]
        
        # Check for common suffixes/prefixes
        if any("inhibitor" in d or "-in" in d for d in drug_lower):
            return "class_effect"
        
        return "correlated_signals"
    
    def _describe_cluster(self, drugs: List[str], cluster_type: str) -> str:
        """Generate description for cluster."""
        if cluster_type == "class_effect":
            return f"Potential class effect involving {len(drugs)} drugs"
        else:
            return f"Cluster of {len(drugs)} correlated signals"


def analyze_cross_signal_correlation(
    df: pd.DataFrame,
    min_correlation: float = 0.5
) -> Dict[str, Any]:
    """
    Convenience function for cross-signal correlation analysis.
    
    Args:
        df: Safety data DataFrame
        min_correlation: Minimum correlation threshold
        
    Returns:
        Dictionary with analysis results
    """
    engine = CrossSignalCorrelationEngine(df)
    return engine.run(min_correlation)

