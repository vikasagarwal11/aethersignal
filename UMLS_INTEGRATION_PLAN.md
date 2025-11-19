# UMLS Metathesaurus Integration Plan

## Overview
This document outlines a lightweight approach to integrating UMLS Metathesaurus for MedDRA mapping, designed to be optional and non-breaking.

## Strategy: Hybrid Approach

### Phase 1: Lightweight UMLS Integration (Recommended)
- **Use UMLS REST API** (no downloads needed)
- **Fallback to current dictionary** if API unavailable
- **Cache results** to minimize API calls
- **Zero breaking changes** to existing code

### Phase 2: Full UMLS Integration (If Needed)
- Download and parse UMLS RRF files
- Build local lookup database
- Requires ~5GB storage and parsing infrastructure

---

## Implementation Options

### Option A: UMLS REST API (Recommended - Lightweight)

**Pros:**
- ✅ No downloads required
- ✅ Always up-to-date
- ✅ Minimal code changes
- ✅ Works immediately

**Cons:**
- ⚠️ Requires internet connection
- ⚠️ API rate limits (but we can cache)
- ⚠️ Requires UMLS account (free)

**Implementation:**
```python
# src/umls_mapper.py
import requests
from typing import Optional
import json
from functools import lru_cache

UMLS_API_KEY = None  # Set via environment variable
UMLS_BASE_URL = "https://uts-ws.nlm.nih.gov/rest"

@lru_cache(maxsize=10000)
def map_to_meddra_via_umls(term: str) -> Optional[str]:
    """
    Map term to MedDRA PT via UMLS REST API.
    Cached to minimize API calls.
    """
    if not UMLS_API_KEY:
        return None
    
    try:
        # Search UMLS for term
        search_url = f"{UMLS_BASE_URL}/search/current"
        params = {
            "string": term,
            "apiKey": UMLS_API_KEY,
            "sabs": "MDR",  # MedDRA source
            "returnIdType": "code"
        }
        response = requests.get(search_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Extract MedDRA PT from results
            # ... parsing logic ...
            return meddra_pt
    except:
        pass
    
    return None
```

**Integration:**
```python
# In utils.py - modify map_to_meddra_pt()
def map_to_meddra_pt(term: str, use_umls: bool = False) -> str:
    # Try current dictionary first (fast)
    result = _map_via_dictionary(term)
    if result != term.title():  # If we found a match
        return result
    
    # Fallback to UMLS if enabled
    if use_umls:
        umls_result = map_to_meddra_via_umls(term)
        if umls_result:
            return umls_result
    
    return term.title()
```

---

### Option B: Pre-processed UMLS Subset (Medium Complexity)

**Pros:**
- ✅ No API calls needed
- ✅ Works offline
- ✅ Fast lookups

**Cons:**
- ⚠️ Requires initial download/processing
- ⚠️ Needs periodic updates
- ⚠️ ~100-500MB file size

**Implementation:**
1. Download UMLS subset (MedDRA terms only)
2. Process into SQLite database or JSON file
3. Load on startup
4. Fast lookup via database

---

### Option C: Full UMLS Integration (High Complexity)

**Pros:**
- ✅ Most comprehensive
- ✅ Includes semantic relationships
- ✅ Full MedDRA hierarchy

**Cons:**
- ❌ Requires ~5GB storage
- ❌ Complex parsing (RRF format)
- ❌ Significant development time
- ❌ Maintenance overhead

**Not recommended for MVP.**

---

## Recommended Approach: Option A (UMLS API)

### Implementation Steps:

1. **Create `src/umls_mapper.py`** (lightweight API wrapper)
2. **Add environment variable** for UMLS API key
3. **Modify `map_to_meddra_pt()`** to try UMLS as fallback
4. **Add caching** to minimize API calls
5. **Make it optional** (feature flag)

### Code Structure:

```
src/
  umls_mapper.py          # New: UMLS API integration
  utils.py                 # Modified: Add UMLS fallback
  .env.example            # New: UMLS_API_KEY template
```

### User Experience:

- **Default**: Uses current dictionary (fast, no setup)
- **With UMLS key**: Automatically uses UMLS for unmapped terms
- **Transparent**: Users don't need to know which source was used

---

## Getting UMLS API Key (Free)

1. Go to: https://uts.nlm.nih.gov/uts/
2. Create account (free)
3. Accept UMLS license
4. Generate API key
5. Set environment variable: `UMLS_API_KEY=your_key_here`

---

## Testing Strategy

1. Test with current dictionary (baseline)
2. Test with UMLS API enabled
3. Compare coverage on real FAERS data
4. Measure performance impact
5. Document unmapped terms for dictionary expansion

---

## Decision Matrix

| Scenario | Recommendation |
|----------|---------------|
| **MVP / Pilots** | ✅ Current dictionary (95% coverage) |
| **Production with gaps** | ✅ Add UMLS API (Option A) |
| **Offline requirement** | ✅ Pre-processed subset (Option B) |
| **Enterprise customer** | ✅ Full UMLS (Option C) or Official MedDRA |

---

## Next Steps (If Proceeding)

1. ✅ Create UMLS account and get API key
2. ✅ Implement Option A (UMLS API wrapper)
3. ✅ Add feature flag in app.py
4. ✅ Test on real data
5. ✅ Document setup process

---

## Estimated Effort

- **Option A (UMLS API)**: 2-3 hours
- **Option B (Pre-processed)**: 4-6 hours
- **Option C (Full UMLS)**: 2-3 days

---

## Conclusion

**For now**: Current dictionary is sufficient (95% coverage, zero complexity)

**When needed**: Implement Option A (UMLS API) as optional enhancement

**Future**: Consider official MedDRA when enterprise customer requires GxP validation

