# Drug Watchlist - Performance Issue & Feature Assessment

## 🚨 **CRITICAL: Performance Issue Identified**

### **Problem:**
The Daily Signal Watch is taking too long because it's calculating PRR/ROR for **EACH candidate individually** in a loop, scanning the entire dataframe multiple times.

**Current Code (SLOW):**
```python
# Line 212-227 in src/watchlist_tab.py
for candidate in candidates:  # If 100 candidates = 100 full scans!
    prr_ror = signal_stats.calculate_prr_ror(
        drug_name,
        reaction_name,
        normalized_df  # ← Scans ALL 438K cases for EACH candidate!
    )
```

**Performance Impact:**
- 6 drugs × 438K cases = potentially **hundreds of candidates**
- Each candidate = **1 full scan of 438K rows**
- **100 candidates = 100 × 438K scans = 43.8 million row scans!**

This is **NOT quantum-optimized** - it's the opposite!

---

## 📍 **Clarification: Drug Watchlist vs Advanced Search Tab**

### **They Are SEPARATE Tabs:**

**Location:** `src/ui/query_interface.py` (line 2011-2022)

```python
query_tab, watchlist_tab_ui, advanced_tab = st.tabs([
    "💬 Natural language query", 
    "🔬 Drug watchlist",  # ← THIS is Drug Watchlist
    "⚙️ Advanced search"  # ← THIS is Advanced Search (currently just a placeholder)
])
```

**Current State:**
- **Drug Watchlist Tab** (`watchlist_tab_ui`): ✅ Full implementation - does signal detection
- **Advanced Search Tab** (`advanced_tab`): ❌ Currently just shows info message (no functionality)

**Answer:** Drug Watchlist is **NOT part of Advanced Search** - they are separate tabs. Drug Watchlist is the one that needs optimization.

---

## ⚡ **Performance Optimization Needed**

### **Problem:** Sequential PRR/ROR Calculation

**Current Flow:**
1. Scan all drugs → Find candidates (fast)
2. **For each candidate, calculate PRR/ROR individually** ← **BOTTLENECK**
3. Apply quantum ranking
4. Display results

**Why It's Slow:**
- `calculate_prr_ror()` scans the entire dataframe for each drug-reaction pair
- If you have 100+ candidates, that's 100+ full dataframe scans
- Each scan processes 438K rows

### **Solution: Batch/Vectorized Calculation**

**Option 1: Pre-compute All Drug-Reaction Pairs (Fastest)**
```python
# Pre-compute all PRR/ROR for unique drug-reaction combinations
# Single pass through dataframe
prr_ror_cache = {}
for candidate in candidates:
    key = (drug, reaction)
    if key not in prr_ror_cache:
        prr_ror_cache[key] = calculate_prr_ror(...)
```

**Option 2: Vectorized Batch Calculation**
- Calculate all PRR/ROR in one pass using vectorized operations
- Use pandas groupby/crosstab for efficiency

**Option 3: Lazy/Deferred Calculation**
- Don't calculate PRR/ROR during initial scan
- Calculate only for top 50 after quantum ranking
- Show PRR/ROR on-demand in drill-down panel

---

## ✅ **User's Requirements**

### **1. Keep PRR/ROR in Main Table ✅**
- **User Decision:** Keep PRR/ROR columns in main table (contrary to expert recommendation)
- **Status:** Already implemented ✅
- **Action:** No changes needed

### **2. Add Severity Badge ✅**
- **Request:** Add severity badge column (High/Medium/Low based on quantum_score)
- **Status:** ❌ Not implemented
- **Action:** Implement now

### **3. Implement All Missing Features**
From the assessment, missing features include:
- Severity badge
- Row click drill-down
- Signal details panel
- All classical metrics (EBGM, IC, BCPNN, Chi-squared, Fisher's)
- Quantum score breakdown
- Trend charts
- Data breakdown
- Case-level view

---

## 🎯 **Implementation Priority**

### **Phase 1: Immediate (Performance Fix)**
1. ⚡ **Optimize PRR/ROR calculation** - Batch/lazy calculation
2. ✅ **Add severity badge** to main table

### **Phase 2: Essential Features**
3. 🔍 **Row selection drill-down** mechanism
4. 📊 **Signal details panel** showing all metrics
5. 📈 **Calculate all classical metrics** (EBGM, IC, BCPNN, etc.)

### **Phase 3: Enhanced Analysis**
6. ⚛️ **Quantum score breakdown** in drill-down
7. 📉 **Trend charts** (cases over time)
8. 📋 **Data breakdown** (age, sex, region)
9. 📝 **Case-level view**

---

## 💡 **Recommended Approach**

### **Performance Fix Strategy:**

**Option A: Lazy Calculation (Recommended)**
- Don't calculate PRR/ROR during initial scan
- Calculate only for top 50 signals after quantum ranking
- Display in main table (as user wants)
- **Result:** 10-100x faster initial scan

**Option B: Batch Calculation**
- Pre-compute PRR/ROR for all unique drug-reaction pairs
- Cache results
- **Result:** 5-10x faster

**Option C: Defer to Drill-Down**
- Don't show PRR/ROR in main table initially
- Calculate on-demand when user drills into signal
- **Result:** Instant main table display

**Recommendation:** Use **Option A** - Calculate PRR/ROR only for top 50 after quantum ranking. This makes the initial scan **10-100x faster** while still showing PRR/ROR in the main table.

---

## 📋 **Implementation Checklist**

### **Immediate (Performance + Severity Badge)**
- [ ] Optimize PRR/ROR calculation (lazy/batch)
- [ ] Add severity badge column to main table
- [ ] Test performance improvement

### **Next (Drill-Down Features)**
- [ ] Implement row selection mechanism
- [ ] Create signal details panel
- [ ] Calculate all classical metrics (EBGM, IC, BCPNN, Chi-squared, Fisher's)
- [ ] Show metrics in drill-down panel

### **Later (Enhanced Analysis)**
- [ ] Quantum score breakdown
- [ ] Trend charts
- [ ] Data breakdown
- [ ] Case-level view

---

## 🎯 **Summary**

### **Performance Issue:**
- ❌ Calculating PRR/ROR for ALL candidates (hundreds) individually
- ✅ **Fix:** Calculate only for top 50 after quantum ranking (lazy calculation)

### **Feature Status:**
- ✅ PRR/ROR in main table (user wants to keep)
- ❌ Severity badge (needs implementation)
- ❌ Drill-down features (need implementation)

### **Tab Structure:**
- Drug Watchlist = Separate tab (NOT part of Advanced Search)
- Advanced Search = Separate empty tab

### **Next Steps:**
1. Optimize performance (lazy PRR/ROR calculation)
2. Add severity badge
3. Implement drill-down features

