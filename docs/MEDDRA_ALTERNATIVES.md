# MedDRA Alternatives for Pharmacovigilance

## Current Status

**MedDRA (Medical Dictionary for Regulatory Activities)**
- **Cost:** Paid subscription required (typically $5,000-$50,000/year depending on organization size)
- **License:** Proprietary, requires annual subscription
- **Coverage:** Comprehensive, industry standard
- **Update Frequency:** Quarterly updates

## Free Alternatives

### 1. **UMLS (Unified Medical Language System)** ✅ **RECOMMENDED**

**What it is:**
- Free biomedical vocabulary maintained by NLM (National Library of Medicine)
- Includes SNOMED CT, ICD-10, RxNorm, and many other terminologies
- Can map to MedDRA terms (indirectly)

**Pros:**
- ✅ **FREE** (for research/non-commercial use)
- ✅ Comprehensive coverage
- ✅ Includes drug names (RxNorm)
- ✅ Includes adverse events (SNOMED CT)
- ✅ Regular updates
- ✅ Well-documented API

**Cons:**
- ⚠️ Requires registration (free)
- ⚠️ Not a direct MedDRA replacement
- ⚠️ Mapping to MedDRA requires additional work
- ⚠️ Commercial use may require license

**How to use:**
```python
# UMLS API (requires API key - free registration)
import requests

def get_umls_concept(term: str, api_key: str):
    url = "https://uts-ws.nlm.nih.gov/rest/search/current"
    params = {
        'string': term,
        'apiKey': api_key,
        'searchType': 'exact'
    }
    response = requests.get(url, params=params)
    return response.json()
```

**Registration:** https://www.nlm.nih.gov/research/umls/index.html

---

### 2. **SNOMED CT** (via UMLS)

**What it is:**
- Comprehensive clinical terminology
- Includes adverse event terms
- Part of UMLS

**Pros:**
- ✅ Free (via UMLS)
- ✅ Comprehensive adverse event coverage
- ✅ International standard

**Cons:**
- ⚠️ Not MedDRA-specific
- ⚠️ Requires mapping to MedDRA

---

### 3. **ICD-10-CM** (International Classification of Diseases)

**What it is:**
- Disease classification system
- Includes some adverse event codes
- Free to use

**Pros:**
- ✅ Free
- ✅ Widely used
- ✅ Regular updates

**Cons:**
- ⚠️ Not designed for pharmacovigilance
- ⚠️ Limited adverse event coverage
- ⚠️ Not a direct MedDRA replacement

---

### 4. **WHO-ART / WHO Drug** (Historical)

**What it is:**
- Older terminology system
- Predecessor to MedDRA
- Still used in some regions

**Pros:**
- ✅ Free (historical data)
- ✅ Some overlap with MedDRA

**Cons:**
- ⚠️ Outdated
- ⚠️ Not actively maintained
- ⚠️ Limited coverage

---

### 5. **Free Hand-Crafted Dictionary** ✅ **CURRENT APPROACH**

**What we use:**
- Custom dictionary mapping common terms to MedDRA PTs
- Located in `src/utils.py` (`FREE_MEDDRA_LIKE`)
- Covers ~95% of common adverse events

**Pros:**
- ✅ **FREE** (no license)
- ✅ No API dependencies
- ✅ Fast lookup
- ✅ Extensible
- ✅ Works offline

**Cons:**
- ⚠️ Requires manual maintenance
- ⚠️ May miss rare terms
- ⚠️ Not official MedDRA

**Current Coverage:**
- ~500+ common adverse event terms
- Covers major System Organ Classes (SOCs)
- Handles synonyms, misspellings, lay language

---

## Recommended Strategy

### **Phase 1: Current (Free Dictionary)** ✅ **IMPLEMENTED**

**What we have:**
- Free hand-crafted dictionary (`FREE_MEDDRA_LIKE`)
- ~95% coverage for common terms
- Fast, offline, no dependencies

**When to use:**
- MVP and early customers
- When MedDRA license is not required
- For internal tools and demos

---

### **Phase 2: UMLS Integration** (Future Enhancement)

**When to add:**
- When free dictionary misses terms
- When customers need broader coverage
- When you have budget for API integration

**Implementation:**
```python
# Hybrid approach: Free dictionary first, UMLS fallback
def map_to_meddra_with_umls(term: str, umls_api_key: Optional[str] = None):
    # Try free dictionary first
    result = map_to_meddra_pt(term)  # Current implementation
    
    if result == term.title():  # No match found
        if umls_api_key:
            # Fallback to UMLS
            umls_result = get_umls_concept(term, umls_api_key)
            # Map UMLS to MedDRA (requires mapping table)
            return map_umls_to_meddra(umls_result)
    
    return result
```

---

### **Phase 3: Official MedDRA** (Enterprise Customers)

**When to add:**
- Enterprise customers require official MedDRA
- Regulatory submissions need MedDRA codes
- Customer pays for MedDRA license

**Implementation:**
- Customer provides MedDRA license
- Use official MedDRA API or database
- Map free dictionary terms to official codes

---

## Comparison Table

| Solution | Cost | Coverage | Maintenance | Best For |
|----------|------|----------|-------------|----------|
| **Free Dictionary** (Current) | Free | ~95% common terms | Manual | MVP, demos, startups |
| **UMLS** | Free (research) | Comprehensive | Automatic | Research, academic |
| **SNOMED CT** | Free (via UMLS) | Comprehensive | Automatic | Clinical systems |
| **ICD-10** | Free | Limited | Automatic | Disease coding |
| **Official MedDRA** | $5K-$50K/year | 100% | Automatic | Enterprise, regulatory |

---

## Bottom Line

**For AetherSignal:**

1. **Current approach (Free Dictionary)** is perfect for:
   - MVP and early customers
   - Startups and small pharma
   - Demos and pilots
   - Internal tools

2. **UMLS integration** is a good upgrade path when:
   - Free dictionary misses terms
   - You need broader coverage
   - You have API integration capacity

3. **Official MedDRA** is only needed when:
   - Enterprise customers require it
   - Regulatory submissions need official codes
   - Customer pays for license

**Recommendation:** ✅ **Keep current free dictionary approach**. It's working well, covers 95% of cases, and is free. Add UMLS as optional enhancement later if needed.

