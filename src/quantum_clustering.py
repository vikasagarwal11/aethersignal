"""
Quantum-inspired clustering for AetherSignal.

This module provides an unsupervised clustering routine for cases within
an active drug–reaction signal. It uses classical k-means on a small
feature set (age, sex, seriousness) but adds a non-linear weighting
scheme inspired by quantum potentials to emphasize dense, high-risk
regions in feature space.
"""

from __future__ import annotations

from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd

from src.utils import extract_age, normalize_text, safe_divide


def _build_feature_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, List[int]]:
    """
    Build feature matrix for clustering:
        - Age (normalized 0–1)
        - Sex (0=M, 1=F, 0.5 other/unknown)
        - Seriousness (0 or 1 based on seriousness/outcome)

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
            continue  # skip rows without age for now

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

    ages_arr = np.array(ages, dtype=float)
    min_age = float(np.min(ages_arr))
    max_age = float(np.max(ages_arr))
    if max_age > min_age:
        ages_norm = (ages_arr - min_age) / (max_age - min_age)
    else:
        ages_norm = np.zeros_like(ages_arr)

    features = np.stack([ages_norm, np.array(sexes), np.array(serious)], axis=1)
    return features, indices


def _initialize_centroids(features: np.ndarray, k: int) -> np.ndarray:
    """
    Initialize centroids using a simple k-means++ like heuristic.
    """
    n = features.shape[0]
    if n == 0 or k <= 0:
        return np.empty((0, features.shape[1]))
    k = min(k, n)

    centroids = []
    # Pick first centroid at random
    idx = np.random.randint(0, n)
    centroids.append(features[idx])

    # Pick remaining centroids probabilistically by distance
    for _ in range(1, k):
        dists = np.min(
            [np.linalg.norm(features - c, axis=1) ** 2 for c in centroids],
            axis=0,
        )
        probs = dists / np.sum(dists) if np.sum(dists) > 0 else np.ones_like(dists) / len(dists)
        idx = np.random.choice(n, p=probs)
        centroids.append(features[idx])

    return np.vstack(centroids)


def _quantum_weighted_distance(x: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    """
    Quantum-inspired distance: classical Euclidean distance with a
    non-linear weighting that emphasizes dense, high-seriousness regions.

    Here we treat each centroid as a potential well and penalize points
    that lie in low-density gaps between wells.
    """
    # Classical distances
    dists = np.linalg.norm(x[:, None, :] - centroids[None, :, :], axis=2)  # (n,k)

    # Simple potential: closer points get slightly reduced distance
    # to reflect "tunneling" into nearby wells; far points are amplified.
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = np.where(dists > 0, 1.0 / dists, 0.0)
    potential = np.exp(-dists) + 0.5 * inv  # higher where distances small

    # Effective distance = dists / (1 + potential)
    eff = dists / (1.0 + potential)
    return eff


def quantum_kmeans(
    features: np.ndarray,
    k: int = 3,
    max_iter: int = 30,
) -> np.ndarray:
    """
    Quantum-inspired k-means clustering.

    Args:
        features: (n, d) feature matrix
        k: number of clusters
        max_iter: maximum iterations

    Returns:
        Cluster labels (n,)
    """
    n = features.shape[0]
    if n == 0 or k <= 0:
        return np.array([], dtype=int)

    centroids = _initialize_centroids(features, k)

    labels = np.zeros(n, dtype=int)
    for _ in range(max_iter):
        # Assign step with quantum-weighted distance
        eff_dists = _quantum_weighted_distance(features, centroids)  # (n,k)
        new_labels = np.argmin(eff_dists, axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels

        # Update centroids
        for j in range(k):
            mask = labels == j
            if np.any(mask):
                centroids[j] = features[mask].mean(axis=0)

    return labels


def cluster_cases_for_signal(
    df: pd.DataFrame,
    drug: str,
    reaction: str,
    min_cases: int = 20,
    k: int = 3,
    use_quantum: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """
    Cluster cases for a specific drug–reaction pair into k clusters.
    
    Automatically uses Qiskit quantum clustering if available, otherwise
    falls back to quantum-inspired classical clustering.

    Args:
        df: normalized dataframe
        drug: drug name
        reaction: reaction term
        min_cases: minimum cases required for clustering
        k: number of clusters
        use_quantum: Whether to attempt quantum (None = auto-detect)

    Returns:
        List of cluster dicts with:
            - cluster_id
            - size
            - mean_age
            - serious_pct
            - male_pct / female_pct
            - method: "quantum" or "classical"
    """
    # Try to use Qiskit quantum clustering if available
    try:
        from src.quantum.qiskit_clustering import qiskit_cluster_cases_for_signal
        from src.quantum.config import get_config
        
        # Auto-detect quantum usage if not specified
        if use_quantum is None:
            config = get_config()
            subset_size = len(df[
                df["drug_name"].astype(str).str.contains(str(drug), case=False, na=False)
                & df["reaction"].astype(str).str.contains(str(reaction), case=False, na=False)
            ]) if "drug_name" in df.columns and "reaction" in df.columns else 0
            use_quantum = config.is_framework_enabled("qiskit") and config.should_use_quantum(subset_size, "clustering")
        
        # Try Qiskit version
        if use_quantum:
            return qiskit_cluster_cases_for_signal(df, drug, reaction, min_cases, k, use_quantum=True)
    except (ImportError, Exception) as e:
        # Fall back to classical if Qiskit not available or fails
        import logging
        logger = logging.getLogger(__name__)
        if use_quantum:  # Only log if quantum was requested
            logger.debug(f"Qiskit clustering not available, using classical: {e}")
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

    labels = quantum_kmeans(features, k=k)
    if labels.size == 0:
        return []

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
            }
        )

    # Sort clusters by serious_pct descending, then size
    clusters.sort(key=lambda c: (c.get("serious_pct", 0.0), c.get("size", 0)), reverse=True)
    return clusters

