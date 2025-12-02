"""
Demo Data Loader - Loads pre-curated demo datasets
Wave 4: Public Demo Portal
"""

import pandas as pd
import os
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def load_demo_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load pre-curated demo datasets for public demo.
    
    Returns:
        Tuple of (social_df, faers_df)
    """
    demo_dir = "demo_data"
    
    # Try to load demo data files
    social_df = pd.DataFrame()
    faers_df = pd.DataFrame()
    
    # Load social demo data
    social_path = os.path.join(demo_dir, "social_sample.csv")
    if os.path.exists(social_path):
        try:
            social_df = pd.read_csv(social_path)
            logger.info(f"Loaded {len(social_df)} social demo records")
        except Exception as e:
            logger.warning(f"Could not load social demo data: {e}")
    else:
        # Generate minimal demo data if file doesn't exist
        social_df = _generate_minimal_social_demo()
    
    # Load FAERS demo data
    faers_path = os.path.join(demo_dir, "faers_sample.csv")
    if os.path.exists(faers_path):
        try:
            faers_df = pd.read_csv(faers_path)
            logger.info(f"Loaded {len(faers_df)} FAERS demo records")
        except Exception as e:
            logger.warning(f"Could not load FAERS demo data: {e}")
    else:
        # Generate minimal demo data if file doesn't exist
        faers_df = _generate_minimal_faers_demo()
    
    return social_df, faers_df


def _generate_minimal_social_demo() -> pd.DataFrame:
    """Generate minimal social demo data if file doesn't exist."""
    import pandas as pd
    from datetime import datetime, timedelta
    
    data = []
    drugs = ["semaglutide", "tirzepatide", "liraglutide"]
    reactions = ["nausea", "vomiting", "diarrhea", "pancreatitis"]
    
    for i in range(50):
        data.append({
            "post_id": f"POST_{i+1:05d}",
            "drug_match": drugs[i % len(drugs)],
            "reaction": reactions[i % len(reactions)],
            "text": f"Sample post about {drugs[i % len(drugs)]} and {reactions[i % len(reactions)]}",
            "confidence": 0.7 + (i % 3) * 0.1,
            "severity": ["mild", "moderate", "severe"][i % 3],
            "source": "reddit",
            "created_date": (datetime.now() - timedelta(days=i % 30)).isoformat()
        })
    
    return pd.DataFrame(data)


def _generate_minimal_faers_demo() -> pd.DataFrame:
    """Generate minimal FAERS demo data if file doesn't exist."""
    import pandas as pd
    from datetime import datetime, timedelta
    
    data = []
    drugs = ["semaglutide", "tirzepatide", "liraglutide"]
    reactions = ["nausea", "vomiting", "diarrhea", "pancreatitis"]
    
    for i in range(100):
        data.append({
            "case_id": f"FAERS_{i+1:05d}",
            "drug": drugs[i % len(drugs)],
            "reaction": reactions[i % len(reactions)],
            "seriousness": i % 2,
            "age": 30 + (i % 50),
            "sex": ["M", "F"][i % 2],
            "country": ["US", "CA", "UK"][i % 3],
            "event_date": (datetime.now() - timedelta(days=i % 365)).strftime("%Y-%m-%d"),
            "source": "faers"
        })
    
    return pd.DataFrame(data)

