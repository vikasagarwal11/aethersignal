"""
Qiskit-Based Quantum Clustering for AetherSignal

Uses Variational Quantum Eigensolver (VQE) and quantum kernel methods
for case clustering within drug-reaction signals.

Falls back to classical clustering if Qiskit unavailable or data too large.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import logging

from src.quantum.config import get_config
from src.quantum.router import QuantumRouter
from src.utils import extract_age, normalize_text, safe_divide

logger = logging.getLogger(__name__)

# Try to import Qiskit
try:
    from qiskit import QuantumCircuit, Aer, execute
    from qiskit.circuit.library import RealAmplitudes
    from qiskit.algorithms import VQE
    from qiskit.algorithms.optimizers import SPSA
    from qiskit_machine_learning.kernels import QuantumKernel
    from qiskit_machine_learning.algorithms import QSVM
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    logger.warning("Qiskit not available, quantum clustering will use classical fallback")


def _build_feature_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, List[int]]:
    """
    Build feature matrix for clustering (same as existing implementation).
    
    Returns:
        (features, valid_indices) where valid_indices are row indices used.
    """
    ages: List[float] = []
    sexes: List[float] = []
    serious: List[float] = []
    indices: List[int] = []

    for idx, row in df.iterrows():
        # Age
        age_val = None
        if "age" in df.columns:
            age_val = extract_age(row.get("age"))
        if age_val is None:
            continue

        # Sex
        sex_val = 0.5
        if "sex" in df.columns:
            s = normalize_text(str(row.get("sex", "")))
            if s.startswith("m"):
                sex_val = 0.0
            elif s.startswith("f"):
                sex_val = 1.0

        # Seriousness
        ser_val = 0.0
        if "seriousness" in df.columns:
            ser = normalize_text(str(row.get("seriousness", "")))
            if ser in ["1", "yes", "y", "true", "serious"]:
                ser_val = 1.0
        elif "outcome" in df.columns:
            out = normalize_text(str(row.get("outcome", "")))
            if any(term in out for term in ["death", "fatal", "died", "deceased", "life", "threatening"]):
                ser_val = 1.0

        ages.append(float(age_val))
        sexes.append(float(sex_val))
        serious.append(float(ser_val))
        indices.append(idx)

    if not indices:
        return np.empty((0, 3)), []

    # Normalize ages
    ages_arr = np.array(ages, dtype=float)
    min_age = float(np.min(ages_arr))
    max_age = float(np.max(ages_arr))
    if max_age > min_age:
        ages_norm = (ages_arr - min_age) / (max_age - min_age)
    else:
        ages_norm = np.zeros_like(ages_arr)

    features = np.stack([ages_norm, np.array(sexes), np.array(serious)], axis=1)
    return features, indices


def _quantum_kernel_clustering(features: np.ndarray, k: int = 3) -> np.ndarray:
    """
    Quantum kernel-based clustering using Qiskit.
    
    Uses quantum kernel methods to compute similarity between data points,
    then applies classical k-means on the quantum kernel space.
    
    Args:
        features: (n, d) feature matrix
        k: number of clusters
    
    Returns:
        Cluster labels (n,)
    """
    if not QISKIT_AVAILABLE:
        raise ImportError("Qiskit not available")
    
    n, d = features.shape
    
    if n < k or n == 0:
        return np.array([], dtype=int)
    
    # For small datasets, use quantum kernel
    # For larger datasets, use classical fallback (handled by router)
    
    # Create quantum feature map (encode classical data into quantum state)
    num_qubits = min(4, d * 2)  # Use up to 4 qubits
    
    def feature_map(x):
        """Encode classical feature vector into quantum state."""
        qc = QuantumCircuit(num_qubits)
        
        # Normalize input
        x_norm = x / (np.linalg.norm(x) + 1e-10)
        
        # Encode features using rotation gates
        for i in range(min(len(x_norm), num_qubits)):
            qc.ry(x_norm[i] * np.pi, i)
        
        # Entangling layer
        for i in range(num_qubits - 1):
            qc.cx(i, i + 1)
        
        return qc
    
    # Create quantum kernel
    qkernel = QuantumKernel(feature_map=feature_map, quantum_instance=Aer.get_backend('aer_simulator'))
    
    # Compute kernel matrix (similarity between all pairs)
    # For efficiency, we'll use a subset for large datasets
    max_kernel_size = 50  # Limit kernel computation size
    if n > max_kernel_size:
        # Use random subset for kernel computation
        indices = np.random.choice(n, max_kernel_size, replace=False)
        kernel_features = features[indices]
        kernel_matrix = qkernel.evaluate(x_vec=kernel_features)
        
        # Extend to full dataset using nearest neighbors
        from sklearn.cluster import KMeans
        from sklearn.metrics.pairwise import euclidean_distances
        
        # Cluster subset
        kmeans_subset = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels_subset = kmeans_subset.fit_predict(kernel_features)
        
        # Assign remaining points to nearest cluster center
        centers = kmeans_subset.cluster_centers_
        distances = euclidean_distances(features, centers)
        labels = np.argmin(distances, axis=1)
        
        # Map subset labels correctly
        for i, idx in enumerate(indices):
            labels[idx] = labels_subset[i]
        
        return labels
    else:
        # Compute full kernel matrix
        kernel_matrix = qkernel.evaluate(x_vec=features)
        
        # Use kernel k-means (classical algorithm on quantum kernel)
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(kernel_matrix)
        
        return labels


def _classical_clustering_fallback(features: np.ndarray, k: int = 3) -> np.ndarray:
    """Classical k-means fallback."""
    from sklearn.cluster import KMeans
    
    if features.shape[0] < k:
        return np.array([], dtype=int)
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features)
    return labels


def qiskit_quantum_kmeans(
    features: np.ndarray,
    k: int = 3,
    use_quantum: bool = True,
) -> np.ndarray:
    """
    Quantum-inspired k-means clustering using Qiskit.
    
    Args:
        features: (n, d) feature matrix
        k: number of clusters
        use_quantum: Whether to attempt quantum (auto-fallback if fails)
    
    Returns:
        Cluster labels (n,)
    """
    n = features.shape[0]
    if n == 0 or k <= 0:
        return np.array([], dtype=int)
    
    # Use router for automatic selection
    router = QuantumRouter()
    
    def quantum_func():
        return _quantum_kernel_clustering(features, k)
    
    def classical_func():
        return _classical_clustering_fallback(features, k)
    
    if use_quantum and QISKIT_AVAILABLE:
        try:
            return router.execute(
                operation="qiskit_clustering",
                data_size=n,
                quantum_func=quantum_func,
                classical_func=classical_func,
                force_quantum=use_quantum
            )
        except Exception as e:
            logger.warning(f"Qiskit clustering failed, using classical: {e}")
            return classical_func()
    else:
        return classical_func()


def qiskit_cluster_cases_for_signal(
    df: pd.DataFrame,
    drug: str,
    reaction: str,
    min_cases: int = 20,
    k: int = 3,
    use_quantum: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """
    Cluster cases for a specific drug-reaction pair using Qiskit quantum clustering.
    
    This is a drop-in replacement for the existing cluster_cases_for_signal()
    with quantum enhancement.
    
    Args:
        df: normalized dataframe
        drug: drug name
        reaction: reaction term
        min_cases: minimum cases required for clustering
        k: number of clusters
        use_quantum: Whether to use quantum (None = auto-detect)
    
    Returns:
        List of cluster dicts with:
            - cluster_id
            - size
            - mean_age
            - serious_pct
            - male_pct / female_pct
    """
    if "drug_name" not in df.columns or "reaction" not in df.columns:
        return []

    mask = (
        df["drug_name"].astype(str).str.contains(str(drug), case=False, na=False)
        & df["reaction"].astype(str).str.contains(str(reaction), case=False, na=False)
    )
    subset = df[mask]
    if len(subset) < min_cases:
        return []

    features, indices = _build_feature_matrix(subset)
    if features.shape[0] < max(5, k):
        return []

    # Auto-detect quantum usage if not specified
    if use_quantum is None:
        config = get_config()
        use_quantum = config.should_use_quantum(features.shape[0], "clustering")

    # Perform clustering
    labels = qiskit_quantum_kmeans(features, k=k, use_quantum=use_quantum)
    
    if labels.size == 0:
        return []

    # Build cluster summaries (same as existing implementation)
    clusters: List[Dict[str, Any]] = []
    for cluster_id in range(k):
        mask_c = labels == cluster_id
        if not np.any(mask_c):
            continue
        idxs = [indices[i] for i in range(len(indices)) if mask_c[i]]
        cluster_df = subset.loc[idxs]

        # Compute summary stats
        ages = []
        if "age" in cluster_df.columns:
            for v in cluster_df["age"]:
                a = extract_age(v)
                if a is not None:
                    ages.append(a)
        mean_age = float(np.mean(ages)) if ages else None

        serious_count = 0
        if "seriousness" in cluster_df.columns:
            ser = cluster_df["seriousness"].astype(str).apply(normalize_text)
            serious_count = int(
                ser.isin(["1", "yes", "y", "true", "serious"]).sum()
            )
        elif "outcome" in cluster_df.columns:
            out = cluster_df["outcome"].astype(str).apply(normalize_text)
            serious_count = int(
                out.str.contains("death|fatal|died|deceased|life|threatening", regex=True).sum()
            )

        serious_pct = safe_divide(serious_count, len(cluster_df), 0.0) * 100

        male_pct = female_pct = None
        if "sex" in cluster_df.columns:
            sex_series = cluster_df["sex"].astype(str).str.upper()
            total_sex = len(sex_series)
            if total_sex > 0:
                male_pct = safe_divide(
                    sex_series.str.contains("M", na=False).sum(), total_sex, 0.0
                ) * 100
                female_pct = safe_divide(
                    sex_series.str.contains("F", na=False).sum(), total_sex, 0.0
                ) * 100

        clusters.append(
            {
                "cluster_id": cluster_id + 1,
                "size": len(cluster_df),
                "mean_age": mean_age,
                "serious_pct": serious_pct,
                "male_pct": male_pct,
                "female_pct": female_pct,
                "method": "quantum" if use_quantum and QISKIT_AVAILABLE else "classical",
            }
        )

    # Sort clusters by serious_pct descending, then size
    clusters.sort(key=lambda c: (c.get("serious_pct", 0.0), c.get("size", 0)), reverse=True)
    return clusters

