# 🚀 PHASE 2C — Global Source Expansion (Implementation Plan)

**Status:** ✅ **READY TO IMPLEMENT**

---

## 📋 **What Already Exists**

### ✅ **Tier 1 Sources (Implemented)**
- ✅ OpenFDA (`src/data_sources/sources/openfda.py`)
- ✅ PubMed (`src/data_sources/sources/pubmed.py`)
- ✅ ClinicalTrials (`src/data_sources/sources/clinicaltrials.py`)
- ✅ DailyMed (`src/data_sources/sources/dailymed.py`)

### ⚠️ **Tier 2 Sources (Need Enhancement)**
- ⚠️ EMA PRAC (`src/data_sources/sources/ema_prac.py`) - Basic placeholder
- ❌ YellowCard (MHRA) - Not implemented
- ❌ Health Canada - Not implemented
- ❌ Google Places - Not implemented

---

## 🎯 **Implementation Tasks**

### **Task 1: Enhance Existing Sources with Reaction Intelligence Core**

All existing sources need to:
1. Use `ReactionNormalizer` for reaction normalization
2. Generate embeddings via `ReactionEmbeddingEngine`
3. Add to vector store via `ReactionSimilarityEngine`
4. Get category mapping from dictionary

### **Task 2: Implement Missing International Sources**

1. **EMA EudraVigilance** - Enhanced CSV/XML parser
2. **YellowCard (MHRA)** - UK CSV parser
3. **Health Canada** - CADRMP CSV parser
4. **Google Places** - Reviews API integration

### **Task 3: Create Unified Integration Layer**

A new module that:
- Routes all sources through Reaction Intelligence Core
- Handles normalization, embedding, clustering
- Provides unified output format
- Manages cross-source deduplication

### **Task 4: Update Pipeline Integration**

- Update `AEPipeline` to use unified integration
- Add source statistics tracking
- Add cross-source fusion logic

---

## 📝 **Next Steps**

1. Enhance existing 4 sources with Reaction Intelligence Core
2. Implement 4 missing international sources
3. Create unified integration layer
4. Update pipeline
5. Add SuperAdmin UI enhancements

**Ready to proceed!**

