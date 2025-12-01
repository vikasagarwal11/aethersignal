# Component Reuse Analysis - Phase 2.0 & 2.1

**Date:** December 2025  
**Status:** ✅ **Refactored to Reuse Existing Components**

---

## ✅ **What We're REUSING (Existing Components)**

### **1. From `social_mapper.py`:**

#### ✅ `extract_emoji_reactions(text)` 
- **Location:** Line 334
- **What it does:** Extracts reactions from emojis using EMOJI_AE_MAP
- **Reused in:** `extraction_engine.py` - directly imported and used

#### ✅ `extract_multiple_reactions(text, return_confidence=False)`
- **Location:** Line 363
- **What it does:** 
  - Extracts multiple reactions from a single post
  - Handles emoji-based reactions
  - Handles slang-based reactions (SLANG_MAP)
  - Handles pattern-based reactions (PATTERN_MAP)
  - Negation detection
  - Confidence scoring
- **Reused in:** `extraction_engine.py` - directly imported and used as the base extraction method

#### ✅ `_is_negated(text, term)`
- **Location:** Line 438
- **What it does:** Checks if a term is negated in text
- **Reused in:** `extraction_engine.py` - directly imported (though we also use it indirectly through extract_multiple_reactions)

#### ✅ `EMOJI_AE_MAP`, `SLANG_AE_MAP`, `SLANG_KEYS`
- **Location:** Lines 14-303
- **What they do:** Comprehensive mappings for emoji and slang to medical terms
- **Reused in:** `extraction_engine.py` - indirectly through extract_multiple_reactions

### **2. From `social_severity.py`:**

#### ✅ `calculate_severity_score(text, reactions)`
- **Location:** Line 100
- **What it does:** Calculates numeric severity score (0.0-1.0) from text
- **Status:** Still available, but we added new functions for direct text classification

#### ✅ `classify_severity(score)` 
- **Location:** Line 215
- **What it does:** Converts numeric score to category ("Low", "Medium", "High", "Critical")
- **Status:** Still available for backward compatibility

#### ✅ `SEVERITY_KEYWORDS`, `OUTCOME_KEYWORDS`, `DURATION_KEYWORDS`
- **Location:** Lines 12-97
- **What they do:** Comprehensive keyword mappings for severity detection
- **Reused in:** New `classify_severity_from_text()` function

---

## 🆕 **What's NEW (Phase 2.0 & 2.1)**

### **1. New File: `extraction_engine.py`**

#### 🆕 `extract_all_reactions(text, drug, use_llm)`
- **What it does:** 
  - **REUSES** `extract_multiple_reactions()` for base extraction
  - **ADDS** LLM fallback when no reactions found
  - **ADDS** Unified severity classification
  - **ADDS** Unified confidence scoring v2.0
- **Why it's needed:** Wraps existing extraction with LLM fallback and unified scoring

#### 🆕 `extract_reactions_llm(text, drug)`
- **What it does:** Uses OpenAI API to extract reactions when regex+emoji fails
- **Why it's needed:** Handles ambiguous posts that pattern matching can't handle

### **2. New File: `confidence_engine.py`**

#### 🆕 `final_confidence(text, reactions, regex_rx, emoji_rx, severity, drug, llm_used)`
- **What it does:** Calculates unified confidence score (0.0-1.0) using hybrid system
- **Why it's needed:** Provides consistent confidence scoring across all extraction methods

#### 🆕 `base_confidence(regex_reactions, emoji_reactions, llm_used)`
- **What it does:** Base confidence from extraction method
- **Why it's needed:** Part of confidence scoring v2.0 system

#### 🆕 `drug_context_boost(text, drug)`
- **What it does:** Boosts confidence if drug is explicitly mentioned
- **Why it's needed:** Context-aware confidence scoring

#### 🆕 `multi_reaction_boost(reactions)`
- **What it does:** Boosts confidence if multiple reactions detected
- **Why it's needed:** Multiple reactions = higher confidence

#### 🆕 `severity_boost(severity)`
- **What it does:** Boosts confidence based on severity indicators
- **Why it's needed:** Severe reactions = higher confidence

#### 🆕 `pattern_strength_boost(text, reactions)`
- **What it does:** Boosts confidence based on pattern match strength
- **Why it's needed:** Exact matches = higher confidence

### **3. Enhanced: `social_severity.py`**

#### 🆕 `classify_severity_from_text(text)`
- **What it does:** Classifies severity directly from text (returns "severe", "moderate", "mild", "unknown")
- **Why it's needed:** Simpler interface for extraction engine (vs calculating score first)

#### 🆕 `severity_score_from_label(severity_label)`
- **What it does:** Converts severity label to numeric score (0.0-1.0)
- **Why it's needed:** Unified severity scoring for extraction engine

---

## 📊 **Architecture: Reuse vs New**

```
extraction_engine.py (NEW)
├── REUSES: extract_multiple_reactions() from social_mapper.py
├── REUSES: extract_emoji_reactions() from social_mapper.py  
├── ADDS: extract_reactions_llm() (LLM fallback)
├── REUSES: classify_severity_from_text() from social_severity.py
├── REUSES: severity_score_from_label() from social_severity.py
└── ADDS: final_confidence() from confidence_engine.py (NEW)

confidence_engine.py (NEW)
└── All functions are NEW (confidence scoring v2.0)

social_severity.py (ENHANCED)
├── KEEPS: calculate_severity_score() (existing)
├── KEEPS: classify_severity() (existing)
└── ADDS: classify_severity_from_text() (new)
└── ADDS: severity_score_from_label() (new)
```

---

## ✅ **Benefits of Reusing**

1. **No Code Duplication:** We don't reimplement emoji extraction, slang mapping, or negation detection
2. **Consistency:** Uses the same logic that's already tested and working
3. **Maintainability:** Changes to base extraction logic automatically benefit the new engine
4. **Backward Compatibility:** Existing code using `extract_multiple_reactions()` continues to work

---

## 🎯 **What We Added (Value)**

1. **LLM Fallback:** Handles ambiguous posts that pattern matching can't handle
2. **Unified Scoring:** Consistent severity and confidence scoring across all methods
3. **Better Integration:** Wraps existing extraction with enhanced scoring and LLM support
4. **Production Ready:** Enterprise-grade extraction with multiple fallback layers

---

## 📝 **Summary**

**Reused Components:**
- ✅ `extract_emoji_reactions()` - Emoji extraction
- ✅ `extract_multiple_reactions()` - Multi-reaction extraction with negation
- ✅ `_is_negated()` - Negation detection
- ✅ `EMOJI_AE_MAP`, `SLANG_AE_MAP` - Mappings
- ✅ `SEVERITY_KEYWORDS` - Severity detection keywords

**New Components:**
- 🆕 `extract_reactions_llm()` - LLM fallback
- 🆕 `confidence_engine.py` - Confidence scoring v2.0
- 🆕 `classify_severity_from_text()` - Direct text classification
- 🆕 `severity_score_from_label()` - Label to score mapping
- 🆕 `extract_all_reactions()` - Unified wrapper

**Result:** Maximum reuse of existing, tested components + strategic additions for LLM and unified scoring.

