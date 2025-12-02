"""
Demo Data Generator - Generate sample datasets for testing
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import random

DEMO_DATA_DIR = "demo_data"


def generate_faers_sample():
    """Generate sample FAERS data."""
    drugs = ["semaglutide", "tirzepatide", "liraglutide"]
    reactions = ["nausea", "vomiting", "diarrhea", "pancreatitis", "gastroparesis"]
    
    data = []
    for i in range(200):
        data.append({
            "case_id": f"FAERS_{i+1:05d}",
            "drug": random.choice(drugs),
            "reaction": random.choice(reactions),
            "seriousness": random.choice([0, 1]),
            "age": random.randint(25, 75),
            "sex": random.choice(["M", "F"]),
            "country": random.choice(["US", "CA", "UK"]),
            "event_date": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
            "source": "faers"
        })
    
    df = pd.DataFrame(data)
    os.makedirs(DEMO_DATA_DIR, exist_ok=True)
    df.to_csv(f"{DEMO_DATA_DIR}/faers_sample.csv", index=False)
    print(f"✅ Generated {len(df)} FAERS sample records")


def generate_social_sample():
    """Generate sample social media data."""
    drugs = ["semaglutide", "ozempic", "wegovy", "mounjaro"]
    reactions = ["nausea", "vomiting", "diarrhea", "fatigue", "headache"]
    severity_keywords = ["mild", "moderate", "severe", "terrible"]
    
    sample_posts = [
        "Started {drug} and got {reaction} 🤮",
        "Anyone else experience {reaction} on {drug}?",
        "{drug} gave me {reaction} but it's worth it",
        "Severe {reaction} after {drug} injection",
        "Mild {reaction} on {drug}, nothing major"
    ]
    
    data = []
    for i in range(100):
        drug = random.choice(drugs)
        reaction = random.choice(reactions)
        post_template = random.choice(sample_posts)
        post_text = post_template.format(drug=drug, reaction=reaction)
        
        data.append({
            "post_id": f"POST_{i+1:05d}",
            "drug_match": drug,
            "reaction": reaction,
            "text": post_text,
            "confidence": round(random.uniform(0.6, 0.95), 2),
            "severity": random.choice(severity_keywords),
            "source": "reddit",
            "timestamp": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
        })
    
    df = pd.DataFrame(data)
    os.makedirs(DEMO_DATA_DIR, exist_ok=True)
    df.to_csv(f"{DEMO_DATA_DIR}/social_sample.csv", index=False)
    print(f"✅ Generated {len(df)} social media sample records")


def generate_lit_sample():
    """Generate sample literature data."""
    drugs = ["semaglutide", "tirzepatide", "liraglutide"]
    reactions = ["nausea", "pancreatitis", "thyroid events", "gastroparesis"]
    
    data = []
    for i in range(40):
        data.append({
            "pmid": f"PMID_{i+1:06d}",
            "drug": random.choice(drugs),
            "reaction": random.choice(reactions),
            "title": f"Case report: {random.choice(reactions)} associated with {random.choice(drugs)}",
            "abstract": f"Background: This case report describes a patient who developed {random.choice(reactions)} while taking {random.choice(drugs)}.",
            "source": "pubmed",
            "year": random.randint(2020, 2025)
        })
    
    df = pd.DataFrame(data)
    os.makedirs(DEMO_DATA_DIR, exist_ok=True)
    df.to_csv(f"{DEMO_DATA_DIR}/lit_sample.csv", index=False)
    print(f"✅ Generated {len(df)} literature sample records")


def generate_all_demo_data():
    """Generate all demo datasets."""
    print("Generating demo datasets...")
    print("")
    
    generate_faers_sample()
    generate_social_sample()
    generate_lit_sample()
    
    print("")
    print("✨ All demo datasets generated in demo_data/")
    print("")
    print("Files created:")
    print("  - demo_data/faers_sample.csv")
    print("  - demo_data/social_sample.csv")
    print("  - demo_data/lit_sample.csv")


if __name__ == "__main__":
    generate_all_demo_data()

