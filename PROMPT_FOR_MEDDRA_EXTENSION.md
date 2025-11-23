# Prompt for Extending MedDRA Dictionary

## Copy this prompt to ChatGPT/Grok:

---

**I need help extending a medical dictionary mapping for pharmacovigilance data analysis. I'm working with FAERS (FDA Adverse Event Reporting System) data and need to map common reaction terms to MedDRA Preferred Terms (PTs).**

### Context:
- This dictionary maps patient-reported adverse event terms (synonyms, slang, lay terms) to standardized MedDRA Preferred Terms
- It's used in a Python application that processes pharmacovigilance data
- Format: lowercase key → MedDRA Preferred Term (title case)

### Current Dictionary Structure:
```python
FREE_MEDDRA_LIKE = {
    # Fever / Temperature
    "fever": "Pyrexia",
    "pyrexia": "Pyrexia",
    "high temperature": "Pyrexia",
    
    # Mental health
    "depression": "Depression",
    "anxiety": "Anxiety",
    "suicidal thoughts": "Suicidal ideation",
    
    # Gastrointestinal
    "nausea": "Nausea",
    "vomiting": "Vomiting",
    "diarrhea": "Diarrhoea",
    "constipation": "Constipation",
    
    # Skin
    "rash": "Rash",
    "itching": "Pruritus",
    "hives": "Urticaria",
    
    # Pain
    "headache": "Headache",
    "abdominal pain": "Abdominal pain",
    "joint pain": "Arthralgia",
    "muscle pain": "Myalgia",
    
    # Cardiovascular
    "heart attack": "Myocardial infarction",
    "palpitations": "Palpitations",
    "tachycardia": "Tachycardia",
    
    # Respiratory
    "shortness of breath": "Dyspnoea",
    "cough": "Cough",
    "wheezing": "Wheezing",
    
    # And many more categories...
}
```

### Already Covered Categories:
- Fever/Temperature
- Mental health (depression, anxiety, suicidal ideation)
- Hair loss (alopecia)
- Pancreatitis
- Gallstones
- Nausea/Vomiting
- Diarrhea/Constipation
- Headache/Migraine
- Fatigue
- Dizziness/Vertigo
- Rash/Urticaria/Pruritus
- Injection site reactions
- Pain (abdominal, chest, back, joint, muscle)
- Cardiovascular (MI, heart failure, arrhythmias)
- Respiratory (dyspnea, cough, wheezing)
- Kidney (renal failure, AKI)
- Liver (hepatic failure, hepatitis)
- Blood/Hematologic (anemia, bleeding, bruising)
- Neurological (seizures, stroke, confusion)
- Vision problems
- Weight/Appetite changes
- Sleep disorders
- Skin conditions
- GI disorders
- Endocrine/Metabolic
- Musculoskeletal
- Infections
- Allergic reactions
- Swelling/Oedema
- Death/Serious outcomes
- Off-label use/Product issues

### What I Need:

**Please provide additional mappings for:**

1. **Missing common adverse events** that appear frequently in FAERS data but aren't in the list above
2. **Additional synonyms/variations** for existing terms (e.g., "threw up" → "Vomiting", "puking" → "Vomiting")
3. **Lay terms and patient language** (e.g., "can't sleep" → "Insomnia", "feeling blue" → "Depression")
4. **Medical abbreviations** (e.g., "SOB" → "Dyspnoea", "CP" → "Chest pain")
5. **Common misspellings** (e.g., "diarrhea" vs "diarrhoea" - both should map correctly)
6. **Drug-specific reactions** (e.g., "ozempic face" → "Face oedema" - already have this)
7. **Device-related reactions** (e.g., "injection site bruising" - already have some)
8. **Pregnancy-related terms** (if applicable)
9. **Pediatric-specific terms**
10. **Elderly-specific terms**

### Format Requirements:
- Keys must be **lowercase** (e.g., "fever", not "Fever")
- Values must be **MedDRA Preferred Terms** in proper title case (e.g., "Pyrexia", not "pyrexia")
- Include multiple synonyms for the same MedDRA term
- Group by category with comments (e.g., `# Category name`)
- Use Python dictionary format: `"key": "MedDRA PT",`

### Example Output Format:
```python
# New Category Name
"term1": "MedDRA Preferred Term",
"term2": "MedDRA Preferred Term",
"synonym for term1": "MedDRA Preferred Term",  # Maps to same PT as term1

# Another Category
"another term": "Another MedDRA PT",
```

### Important Notes:
- Use **official MedDRA Preferred Terms** when possible
- If unsure of exact MedDRA PT, use the most appropriate standardized medical term
- Include common patient language and slang terms
- Prioritize terms that appear frequently in spontaneous reporting systems
- Include both American and British English spellings (e.g., "anemia" and "anaemia")

**Please provide at least 50-100 new mappings, organized by category, focusing on the most common adverse events that might be missing from the current dictionary.**

---

## Alternative Shorter Prompt (if character limit is an issue):

**Extend this MedDRA mapping dictionary for pharmacovigilance. Map common adverse event terms (synonyms, slang, lay terms) to MedDRA Preferred Terms. Format: lowercase key → MedDRA PT (title case). Include: missing common AEs, additional synonyms, patient language, abbreviations, misspellings. Provide 50-100 new mappings organized by category. Focus on terms frequently seen in FAERS/spontaneous reports.**

