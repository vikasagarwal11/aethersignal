"""
Local Case Clustering Engine (CHUNK 6.24)
Performs unsupervised clustering of cases to identify unusual patterns.

Runs entirely in browser using scikit-learn-in-pyodide or lightweight alternatives.
"""
from typing import Dict, List, Any, Optional, Tuple
import json


# Check for pandas availability
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Check for scikit-learn availability (Pyodide)
try:
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class LocalCaseClustering:
    """
    Local case clustering engine for browser-based processing.
    
    Clusters cases by:
    - Age, sex, drug name, reaction (PT)
    - Identifies unusual case groupings
    - Detects rare drug-reaction clusters
    - Finds distinct patient profile groups
    - Discovers emerging safety sub-signals
    
    Works with both pandas DataFrames and lightweight list-of-dicts.
    """
    
    def __init__(self, n_clusters: int = 6, random_state: int = 42):
        """
        Initialize clustering engine.
        
        Args:
            n_clusters: Number of clusters to create
            random_state: Random seed for reproducibility
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model = None
        self.encoder = None
    
    def fit(self, data: Any) -> Tuple[Any, Any, Any]:
        """
        Fit clustering model on case data.
        
        Args:
            data: DataFrame or list of dicts with case records
            
        Returns:
            Tuple of (data_with_clusters, model, encoder)
        """
        # Convert to DataFrame if needed
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            df = data.copy()
        elif isinstance(data, list):
            # Convert list of dicts to DataFrame if pandas available
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(data)
            else:
                # Fallback: lightweight clustering without pandas
                return self._fit_lightweight(data)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
        
        # Select clustering features
        feature_cols = []
        
        # Find available columns (handle case variations)
        age_cols = ["AGE", "age", "Age"]
        sex_cols = ["SEX", "sex", "Sex"]
        drug_cols = ["drug_name", "DRUGNAME", "drugname", "DRUG"]
        reaction_cols = ["reaction", "PT", "pt", "REACTION"]
        
        age_col = next((c for c in age_cols if c in df.columns), None)
        sex_col = next((c for c in sex_cols if c in df.columns), None)
        drug_col = next((c for c in drug_cols if c in df.columns), None)
        reaction_col = next((c for c in reaction_cols if c in df.columns), None)
        
        if age_col:
            feature_cols.append(age_col)
        if sex_col:
            feature_cols.append(sex_col)
        if drug_col:
            feature_cols.append(drug_col)
        if reaction_col:
            feature_cols.append(reaction_col)
        
        if not feature_cols:
            raise ValueError("No suitable clustering features found in data")
        
        # Prepare feature data
        feature_data = df[feature_cols].astype(str).fillna("UNKNOWN")
        
        # Use sklearn if available
        if SKLEARN_AVAILABLE:
            # One-hot encode categorical features
            encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            X = encoder.fit_transform(feature_data)
            
            # Cluster using KMeans
            model = KMeans(
                n_clusters=self.n_clusters,
                random_state=self.random_state,
                n_init=10
            )
            labels = model.fit_predict(X)
            
            # Add cluster labels to DataFrame
            df["CLUSTER"] = labels
            
            self.model = model
            self.encoder = encoder
            
            return df, model, encoder
        
        else:
            # Fallback: simple clustering without sklearn
            return self._fit_simple_clustering(df, feature_cols)
    
    def _fit_simple_clustering(self, df: Any, feature_cols: List[str]) -> Tuple[Any, None, None]:
        """
        Simple clustering fallback without sklearn.
        
        Groups cases by feature combinations.
        """
        if not PANDAS_AVAILABLE:
            # Without pandas, use lightweight approach
            return self._fit_lightweight(df if isinstance(df, list) else df.to_dict('records'))
        
        # Group by feature combinations and assign cluster IDs
        feature_data = df[feature_cols].astype(str).fillna("UNKNOWN")
        
        # Create feature hash for grouping
        feature_data["_feature_hash"] = feature_data.apply(
            lambda x: hash(tuple(x.values)), axis=1
        )
        
        # Assign clusters based on feature hash
        unique_hashes = feature_data["_feature_hash"].unique()
        hash_to_cluster = {
            h: i % self.n_clusters 
            for i, h in enumerate(unique_hashes)
        }
        
        df["CLUSTER"] = feature_data["_feature_hash"].map(hash_to_cluster)
        feature_data.drop("_feature_hash", axis=1, inplace=True)
        
        return df, None, None
    
    def _fit_lightweight(self, data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], None, None]:
        """
        Lightweight clustering for list-of-dicts without pandas/sklearn.
        
        Groups cases by feature combinations.
        """
        # Extract features
        for case in data:
            # Build feature hash
            age = str(case.get("AGE") or case.get("age") or "UNKNOWN")
            sex = str(case.get("SEX") or case.get("sex") or "UNKNOWN")
            drug = str(case.get("drug_name") or case.get("DRUGNAME") or "UNKNOWN")
            reaction = str(case.get("reaction") or case.get("PT") or "UNKNOWN")
            
            feature_hash = hash((age, sex, drug, reaction))
            cluster_id = feature_hash % self.n_clusters
            
            case["CLUSTER"] = cluster_id
        
        return data, None, None
    
    def predict(self, data: Any) -> List[int]:
        """
        Predict cluster labels for new cases.
        
        Args:
            data: DataFrame or list of dicts
            
        Returns:
            List of cluster labels
        """
        if self.model is None or self.encoder is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if not SKLEARN_AVAILABLE:
            raise ValueError("sklearn required for prediction")
        
        # Convert to DataFrame if needed
        if isinstance(data, list) and PANDAS_AVAILABLE:
            df = pd.DataFrame(data)
        elif PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError("pandas required for prediction")
        
        # Use same feature columns as training
        # (In real implementation, store feature columns from fit)
        feature_cols = ["AGE", "SEX", "drug_name", "reaction"]
        feature_cols = [c for c in feature_cols if c in df.columns]
        
        feature_data = df[feature_cols].astype(str).fillna("UNKNOWN")
        X = self.encoder.transform(feature_data)
        
        labels = self.model.predict(X)
        return labels.tolist()
    
    def get_cluster_summary(self, data_with_clusters: Any) -> List[Dict[str, Any]]:
        """
        Generate summary statistics for each cluster.
        
        Args:
            data_with_clusters: Data with CLUSTER column added
            
        Returns:
            List of cluster summaries
        """
        if PANDAS_AVAILABLE and isinstance(data_with_clusters, pd.DataFrame):
            df = data_with_clusters
            
            summaries = []
            for cluster_id in range(self.n_clusters):
                cluster_data = df[df["CLUSTER"] == cluster_id]
                
                if len(cluster_data) == 0:
                    continue
                
                summary = {
                    "cluster_id": cluster_id,
                    "size": len(cluster_data),
                    "mean_age": cluster_data["AGE"].mean() if "AGE" in cluster_data.columns else None,
                    "serious_pct": (
                        (cluster_data["serious"] == True).sum() / len(cluster_data) * 100
                        if "serious" in cluster_data.columns else None
                    ),
                    "male_pct": (
                        (cluster_data["SEX"] == "M").sum() / len(cluster_data) * 100
                        if "SEX" in cluster_data.columns else None
                    ),
                }
                
                summaries.append(summary)
            
            return summaries
        
        elif isinstance(data_with_clusters, list):
            # Lightweight summary for list-of-dicts
            summaries = []
            clusters = {}
            
            for case in data_with_clusters:
                cluster_id = case.get("CLUSTER", -1)
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(case)
            
            for cluster_id, cases in clusters.items():
                if cluster_id == -1:
                    continue
                
                ages = [c.get("AGE") or c.get("age") for c in cases if c.get("AGE") or c.get("age")]
                serious_count = sum(1 for c in cases if c.get("serious") or c.get("SERIOUS"))
                
                summary = {
                    "cluster_id": cluster_id,
                    "size": len(cases),
                    "mean_age": sum(ages) / len(ages) if ages else None,
                    "serious_pct": (serious_count / len(cases) * 100) if cases else 0,
                }
                
                summaries.append(summary)
            
            return summaries
        
        else:
            return []

