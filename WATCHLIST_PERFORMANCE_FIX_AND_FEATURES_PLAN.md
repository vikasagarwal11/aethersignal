# Drug Watchlist - Performance Fix & Features Implementation Plan

## 🚨 **CRITICAL PERFORMANCE ISSUE**

### **The Problem:**

Your Daily Signal Watch is **taking too long** because it's calculating PRR/ROR for **EACH candidate individually** in a loop.

**Current Code (VERY SLOW):**
```python
# src/watchlist_tab.py lines 212-227
for candidate in candidates:  # If you have 100+ candidates...
    prr_ror = signal_stats.calculate_prr_ror(
        drug_name,
        reaction_name,
        normalized_df  # ← Scans ALL 438K cases for EACH candidate!
    )
```

**Why It's Slow:**
- 6 drugs scanning 438K cases = potentially **hundreds of candidates**
- Each `calculate_prr_ror()` call scans the **entire 438K row dataframe**
- **100 candidates = 100 full scans = 43.8 million row operations!**

This defeats the purpose of quantum-optimized fast processing!

---

## ⚡ **Performance Fix Strategy**

### **Solution: Lazy Calculation (Calculate Only for Top 50)**

**Instead of:** Calculate PRR/ROR for ALL candidates (hundreds)

**Do This:** 
1. Find all candidates (fast)
2. Apply quantum ranking (fast)
3. **Then** calculate PRR/ROR only for **top 50** after ranking

**Performance Gain:** 
- **Before:** 100+ candidates × 438K scans = slow
- **After:** 50 candidates × 438K scans = **2x faster**
- **Better:** Calculate only when needed (lazy) = **10-100x faster**

---

## 📍 **Clarification: Drug Watchlist vs Advanced Search**

### **They Are SEPARATE Tabs:**

Looking at `src/ui/query_interface.py`:

```python
query_tab, watchlist_tab_ui, advanced_tab = st.tabs([
    "💬 Natural language query", 
    "🔬 Drug watchlist",  # ← THIS is your Drug Watchlist (full implementation)
    "⚙️ Advanced search"  # ← THIS is Advanced Search (currently just placeholder)
])
```

**Current Status:**
- ✅ **Drug Watchlist Tab:** Full implementation - does signal detection (needs optimization)
- ❌ **Advanced Search Tab:** Just shows info message (no functionality yet)

**Answer:** Drug Watchlist is **NOT part of Advanced Search** - they're completely separate tabs. The performance issue is in the Drug Watchlist tab.

---

## ✅ **User Requirements Summary**

### **1. Keep PRR/ROR in Main Table ✅**
- **User Decision:** Keep PRR/ROR columns visible in main table
- **Status:** ✅ Already implemented
- **Action:** No changes needed

### **2. Add Severity Badge ✅**
- **Request:** Add severity badge column (High/Medium/Low based on quantum_score)
- **Status:** ❌ Not implemented
- **Action:** Implement now

**Severity Badge Logic:**
- **High:** quantum_score ≥ 0.70
- **Medium:** 0.40 ≤ quantum_score < 0.70
- **Low:** quantum_score < 0.40

### **3. Fix Performance ⚡**
- **Request:** Make it faster (quantum concept should be fast)
- **Status:** ❌ Current implementation is slow
- **Action:** Optimize PRR/ROR calculation (lazy/batch)

### **4. Implement All Missing Features**
From expert recommendation, missing:
- Row click drill-down
- Signal details panel
- All classical metrics (EBGM, IC, BCPNN, Chi-squared, Fisher's)
- Quantum score breakdown
- Trend charts
- Data breakdown
- Case-level view

---

## 🎯 **Implementation Plan**

### **Phase 1: Immediate (Performance + Severity Badge)**

#### **Task 1.1: Optimize PRR/ROR Calculation ⚡**

**Current (SLOW):**
```python
# Calculate PRR/ROR for ALL candidates
for candidate in candidates:
    prr_ror = calculate_prr_ror(...)
```

**New (FAST - Lazy Calculation):**
```python
# Step 1: Find candidates (fast)
candidates = [...]  # No PRR/ROR yet

# Step 2: Apply quantum ranking (fast)
ranked = quantum_ranking.quantum_rerank_signals(candidates)

# Step 3: Calculate PRR/ROR ONLY for top 50 (lazy)
df = pd.DataFrame(ranked).head(50)

for idx, row in df.iterrows():
    prr_ror = calculate_prr_ror(row['drug'], row['reaction'], normalized_df)
    # Update row with PRR/ROR
```

**Performance Improvement:**
- **Before:** Calculate for 100+ candidates = slow
- **After:** Calculate for top 50 only = **2x+ faster**
- **Even Better:** Could cache/vectorize = **10-100x faster**

#### **Task 1.2: Add Severity Badge Column**

**Implementation:**
```python
def get_severity_badge(quantum_score: float) -> str:
    """Return severity badge based on quantum score."""
    if quantum_score >= 0.70:
        return "🔴 High"
    elif quantum_score >= 0.40:
        return "🟡 Medium"
    else:
        return "🟢 Low"

# Add to dataframe
df['severity'] = df['quantum_score'].apply(get_severity_badge)
```

**Display in Table:**
- Add "Severity" column after "Quantum Score"
- Show badge with color coding

---

### **Phase 2: Essential Features (Drill-Down)**

#### **Task 2.1: Row Selection Mechanism**

**Streamlit Limitation:** No native row click support

**Solution Options:**
1. **Selectbox approach:** Dropdown to select signal for details
2. **Expander per row:** Each row expands to show details
3. **Checkbox selection:** Select signal(s) to view details

**Recommended:** Selectbox for single signal selection

#### **Task 2.2: Signal Details Panel**

Create a panel showing:
- All classical metrics (PRR, ROR, EBGM, IC, BCPNN, Chi-squared, Fisher's)
- Quantum score breakdown
- Trend charts
- Data breakdown (age, sex, region, seriousness)
- Case-level table

**Reuse Existing Code:**
- `src/ui/signal_governance_panel.py` has similar panel
- `src/quantum_explainability.py` has quantum breakdown
- `src/advanced_stats.py` has all metric functions

#### **Task 2.3: Calculate All Classical Metrics**

**Current:** Only PRR/ROR calculated

**Add:**
- EBGM (from `src/advanced_stats.py`)
- IC (from `src/advanced_stats.py`)
- BCPNN (from `src/advanced_stats.py`)
- Chi-squared (from `src/advanced_stats.py`)
- Fisher's Exact (from `src/advanced_stats.py`)

**Display:** In drill-down panel (not main table to keep it simple)

---

### **Phase 3: Enhanced Analysis**

- Quantum score breakdown
- Trend charts
- Data breakdown
- Case-level view

---

## 📊 **Implementation Status**

| Feature | Status | Priority | Effort |
|---------|--------|----------|--------|
| **Performance Optimization** | ❌ Not done | 🔴 Critical | Medium |
| **Severity Badge** | ❌ Not done | 🔴 High | Low |
| **Row Selection** | ❌ Not done | 🟡 Medium | Medium |
| **Signal Details Panel** | ❌ Not done | 🟡 Medium | High |
| **All Classical Metrics** | ❌ Not done | 🟡 Medium | Medium |
| **Quantum Breakdown** | ❌ Not done | 🟢 Low | Medium |
| **Trend Charts** | ❌ Not done | 🟢 Low | Medium |
| **Data Breakdown** | ❌ Not done | 🟢 Low | Medium |
| **Case-Level View** | ❌ Not done | 🟢 Low | Medium |

---

## 🎯 **Recommended Implementation Order**

### **Step 1: Fix Performance (NOW)**
1. Optimize PRR/ROR calculation (lazy for top 50 only)
2. Test performance improvement
3. Should see **2-10x faster** results

### **Step 2: Add Severity Badge (NOW)**
1. Add severity badge function
2. Add column to main table
3. Test display

### **Step 3: Drill-Down Features (NEXT)**
1. Add row selection mechanism
2. Create signal details panel
3. Calculate all metrics on-demand

---

## 💡 **Key Takeaways**

1. **Performance Issue:** PRR/ROR calculation is the bottleneck - fix with lazy calculation
2. **Drug Watchlist ≠ Advanced Search:** They're separate tabs
3. **Keep PRR/ROR in main table:** User wants this (contrary to expert recommendation)
4. **Add severity badge:** Simple addition, high value
5. **All features exist elsewhere:** Just need to integrate into Drug Watchlist

---

## 🚀 **Ready to Implement?**

Should I proceed with:
1. ⚡ Performance optimization (lazy PRR/ROR calculation)
2. ✅ Severity badge addition
3. 🔍 Basic drill-down (row selection + details panel)

This will make Drug Watchlist **fast** and **feature-complete**!

