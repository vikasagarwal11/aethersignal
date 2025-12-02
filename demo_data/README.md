# Demo Data

This directory contains sample datasets for testing and demonstration purposes.

## Files

- `faers_sample.csv` - Sample FAERS reports (de-identified)
- `social_sample.csv` - Sample social media posts (anonymized)
- `lit_sample.csv` - Sample literature references

## Usage

These datasets can be loaded in the UI using the "Load Demo Data" button, or programmatically:

```python
import pandas as pd

# Load demo data
faers_demo = pd.read_csv("demo_data/faers_sample.csv")
social_demo = pd.read_csv("demo_data/social_sample.csv")
lit_demo = pd.read_csv("demo_data/lit_sample.csv")
```

## Privacy

All data has been:
- De-identified
- Anonymized
- Sanitized
- Safe for public use

## Generating Demo Data

To generate new demo data, use the demo data generator:

```bash
python tools/generate_demo_data.py
```

