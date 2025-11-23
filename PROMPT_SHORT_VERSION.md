# Short Prompt for ChatGPT/Grok

## Quick Version:

**Extend this MedDRA mapping dictionary for pharmacovigilance data. Map common adverse event terms (synonyms, slang, patient language) to MedDRA Preferred Terms.**

**Current format:**
```python
FREE_MEDDRA_LIKE = {
    "fever": "Pyrexia",
    "nausea": "Nausea",
    "rash": "Rash",
    "headache": "Headache",
    # ... 200+ existing mappings
}
```

**Requirements:**
- Keys: lowercase (e.g., "fever")
- Values: MedDRA Preferred Terms, title case (e.g., "Pyrexia")
- Include: synonyms, lay terms, abbreviations, misspellings, patient language
- Organize by category with comments
- Focus on common FAERS terms not already covered

**Provide 50-100 new mappings in Python dictionary format, grouped by medical category.**

---

## Even Shorter (for tight character limits):

**Extend MedDRA dictionary: map adverse event synonyms/slang to MedDRA Preferred Terms. Format: `"lowercase_term": "MedDRA PT"`. Add 50-100 common FAERS terms missing from current 200+ mappings. Include patient language, abbreviations, misspellings. Group by category.**

