"""
ML-based AE detection using DistilBERT/ClinicalBERT.
Provides model-based adverse event classification.
"""

import os
from typing import Optional, Tuple
import pandas as pd

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    import torch
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    torch = None

# Model configuration
# Using a lightweight model for faster inference
MODEL_NAME = "distilbert-base-uncased"  # Can be swapped for clinical models
USE_CLINICAL_MODEL = os.getenv("USE_CLINICAL_BERT", "false").lower() == "true"

if USE_CLINICAL_MODEL:
    # Clinical model (larger, more accurate, slower)
    MODEL_NAME = "emilyalsentzer/Bio_ClinicalBERT"  # Or "bvanaken/clinical-bert-base-768-clinical-ner"

# Cache for model loading
_model = None
_tokenizer = None
_classifier = None


def load_model():
    """Load the ML model (lazy loading)."""
    global _model, _tokenizer, _classifier
    
    if not ML_AVAILABLE:
        return None, None, None
    
    if _model is not None:
        return _model, _tokenizer, _classifier
    
    try:
        # Use pipeline for easier classification
        _classifier = pipeline(
            "text-classification",
            model=MODEL_NAME,
            device=0 if torch and torch.cuda.is_available() else -1
        )
        return _model, _tokenizer, _classifier
    except Exception:
        # Fallback: return None if model loading fails
        return None, None, None


def predict_ae_probability(text: str) -> float:
    """
    Predict probability that text contains an adverse event.
    
    Args:
        text: Post text to analyze
    
    Returns:
        Probability (0.0-1.0) that text contains an AE
    """
    if not ML_AVAILABLE or not text or len(text.strip()) < 10:
        return 0.0
    
    _, _, classifier = load_model()
    if classifier is None:
        return 0.0
    
    try:
        # Truncate to model's max length (typically 512 tokens)
        text_truncated = text[:500]  # Safe truncation
        
        result = classifier(text_truncated)
        
        # Handle different output formats
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict):
                # Get positive class probability
                label = result[0].get("label", "")
                score = result[0].get("score", 0.0)
                
                # If label indicates positive, return score; otherwise return 1-score
                if "positive" in label.lower() or "adverse" in label.lower():
                    return float(score)
                else:
                    return 1.0 - float(score)
            else:
                return float(result[0]) if isinstance(result[0], (int, float)) else 0.0
        
        return 0.0
    except Exception:
        return 0.0


def predict_ae_batch(texts: list) -> list:
    """
    Predict AE probabilities for a batch of texts.
    
    Args:
        texts: List of text strings
    
    Returns:
        List of probabilities
    """
    if not ML_AVAILABLE:
        return [0.0] * len(texts)
    
    _, _, classifier = load_model()
    if classifier is None:
        return [0.0] * len(texts)
    
    try:
        # Process in batches for efficiency
        batch_size = 32
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = classifier(batch)
            
            for result in batch_results:
                if isinstance(result, dict):
                    label = result.get("label", "")
                    score = result.get("score", 0.0)
                    if "positive" in label.lower() or "adverse" in label.lower():
                        results.append(float(score))
                    else:
                        results.append(1.0 - float(score))
                else:
                    results.append(float(result) if isinstance(result, (int, float)) else 0.0)
        
        return results
    except Exception:
        return [0.0] * len(texts)


def enhance_with_ml(df: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    """
    Enhance DataFrame with ML-based AE probabilities.
    
    Args:
        df: DataFrame with posts
        text_column: Column name containing text
    
    Returns:
        DataFrame with added 'ae_prob' column
    """
    if df.empty or text_column not in df.columns:
        return df
    
    df = df.copy()
    
    # Check if ML is available
    if not ML_AVAILABLE:
        df["ae_prob"] = 0.0
        df["ml_available"] = False
        return df
    
    # Load model
    _, _, classifier = load_model()
    if classifier is None:
        df["ae_prob"] = 0.0
        df["ml_available"] = False
        return df
    
    # Predict probabilities
    texts = df[text_column].fillna("").astype(str).tolist()
    probabilities = predict_ae_batch(texts)
    
    df["ae_prob"] = probabilities
    df["ml_available"] = True
    
    # Update possible_ae based on ML probability (threshold: 0.55)
    if "possible_ae" in df.columns:
        # Combine rule-based and ML-based
        df["possible_ae"] = df["possible_ae"] | (df["ae_prob"] > 0.55)
    else:
        df["possible_ae"] = df["ae_prob"] > 0.55
    
    return df


def is_ml_available() -> bool:
    """Check if ML models are available."""
    if not ML_AVAILABLE:
        return False
    
    _, _, classifier = load_model()
    return classifier is not None

