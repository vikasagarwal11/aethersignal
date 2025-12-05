# Drug Watchlist - Missing Features Assessment

## 📋 Expert Recommendation Summary

The expert recommends:

1. **Simplify Main Table** - Keep it simple for triage (remove PRR/ROR from main view)
2. **Row Click Drill-Down** - Click row → see detailed signal panel
3. **Signal Details Panel** - Show all metrics, breakdowns, trends, cases
4. **All Metrics Explained** - Elaborate PRR, ROR, EBGM, IC, Chi-squared, quantum_score in docs

---

## ✅ WHAT IS CURRENTLY IMPLEMENTED

### **1. Main Table ✅**
- Shows: Drug, Reaction, Count, Quantum Score, Quantum Rank, Classical Rank
- **ALSO shows:** PRR and ROR (these should be moved to drill-down per expert)

### **2. Help Section ✅**
- Comprehensive expandable help section
- Explains all scores and metrics
- Decision matrix and usage guide

### **3. Documentation ✅**
- Expert explanation document created
- Comprehensive scoring metrics guide
- Engineering Blueprint updated

### **4. Statistical Functions ✅**
- PRR/ROR calculation implemented in Drug Watchlist
- All other functions exist elsewhere but **NOT used in Drug Watchlist**

---

## ❌ WHAT IS NOT IMPLEMENTED (From Expert Recommendation)

### **1. Simplified Main Table ❌**

**Expert Says:**
> "Keep main table simple for triage. Remove PRR/ROR from main view."

**Current State:**
- ❌ PRR/ROR columns are shown in main table
- ❌ Table is not simplified for quick triage
- ❌ No severity badge column

**What's Missing:**
- Remove PRR/ROR from main table columns
- Add severity badge (High/Medium/Low based on quantum_score)
- Keep only: drug, reaction, count, quantum_score, quantum_rank, classical_rank

---

### **2. Row Click Drill-Down Feature ❌ (MAJOR GAP)**

**Expert Says:**
> "Yes – I would absolutely add a feature where **clicking a row** opens a detailed view"

**Current State:**
- ❌ **NO row click feature exists**
- ❌ No signal details panel
- ❌ No drill-down capability

**What's Missing:**
- Row selection mechanism (Streamlit limitation - use selectbox or expander per row)
- Signal details panel (right-hand side or modal)
- All detailed information shown in drill-down, not main table

**Similar Feature Exists:** `src/ui/signal_governance_panel.py` has signal details, but not integrated into Drug Watchlist

---

### **3. Classical Metrics in Drill-Down ❌**

**Expert Says:**
> "Show PRR, ROR, EBGM, IC, χ², ROR CI, etc. in drill-down panel with thresholds and interpretation"

**Current State:**
- ✅ PRR calculated and shown in main table
- ✅ ROR calculated and shown in main table
- ❌ **EBGM NOT calculated** in Drug Watchlist (function exists in `src/advanced_stats.py`)
- ❌ **IC NOT calculated** in Drug Watchlist (function exists in `src/advanced_stats.py`)
- ❌ **BCPNN NOT calculated** in Drug Watchlist (function exists in `src/advanced_stats.py`)
- ❌ **Chi-squared NOT calculated** in Drug Watchlist (function exists in `src/advanced_stats.py`)
- ❌ **Fisher's Exact NOT calculated** in Drug Watchlist (function exists in `src/advanced_stats.py`)
- ❌ No threshold flags shown
- ❌ No interpretation text shown

**What's Missing:**
- Calculate ALL metrics (EBGM, IC, BCPNN, Chi-squared, Fisher's)
- Move PRR/ROR to drill-down panel
- Show threshold flags (e.g., "PRR ≥ 2 & χ² ≥ 4")
- Show interpretation text

---

### **4. Quantum Score Breakdown in Drill-Down ❌**

**Expert Says:**
> "Show quantum score breakdown with drivers (temporal spike, novelty, network centrality, etc.) and natural language explanation"

**Current State:**
- ❌ **No quantum breakdown shown in Drug Watchlist**
- ✅ Explanation function exists in `src/quantum_explainability.py` but not integrated

**What's Missing:**
- Component-by-component breakdown (rarity, seriousness, recency, count)
- Interaction terms breakdown
- Natural language explanation
- Driver identification (temporal spike, novelty, etc.)

---

### **5. Trend Charts ❌**

**Expert Says:**
> "Trend chart: cases over time (last 12–24 months)"

**Current State:**
- ❌ **No trend chart in Drug Watchlist**
- ✅ Trend chart functions exist in other modules (`src/ui/signal_governance_panel.py`)

**What's Missing:**
- Cases over time chart (monthly/quarterly)
- Last 12-24 months visualization
- Show in drill-down panel

---

### **6. Data Breakdown ❌**

**Expert Says:**
> "Breakdown: by age, sex, region, reporter type, seriousness"

**Current State:**
- ❌ **No breakdown in Drug Watchlist**
- ✅ Breakdown functions exist in `src/signal_stats.py` (`get_summary_stats()`)

**What's Missing:**
- Age distribution
- Sex distribution
- Country/region distribution
- Seriousness breakdown
- Reporter type breakdown
- Show in drill-down panel

---

### **7. Case-Level Drill-Down ❌**

**Expert Says:**
> "Link/Button: 'View underlying cases' → opens a case table with Case ID, age, sex, country, seriousness, outcome, narrative link"

**Current State:**
- ❌ **No case table in Drug Watchlist**
- ✅ Case drill-down exists in `src/ui/results_display.py` but not in Drug Watchlist

**What's Missing:**
- Link/button to view underlying cases
- Case table showing individual cases
- Case details: ID, age, sex, country, seriousness, outcome, narrative

---

### **8. Severity Badge ❌**

**Expert Says:**
> "Maybe one extra column like a severity badge (e.g. 'High / Medium / Low')"

**Current State:**
- ❌ **No severity badge column**

**What's Missing:**
- Severity badge based on quantum_score
- High (≥0.70), Medium (0.40-0.70), Low (<0.40)
- Show in main table for quick triage

---

## 📊 Implementation Status Matrix

| Feature | Expert Request | Current Status | Gap |
|---------|---------------|----------------|-----|
| **Simplified Main Table** | ✅ Yes - Remove PRR/ROR | ❌ Shows PRR/ROR | **NEEDS SIMPLIFICATION** |
| **Severity Badge** | ✅ Yes - Add to main table | ❌ Not implemented | **MISSING** |
| **Row Click Drill-Down** | ✅ Yes - Essential | ❌ Not implemented | **MAJOR GAP** |
| **Signal Details Panel** | ✅ Yes - Right-hand/modal | ❌ Not implemented | **MAJOR GAP** |
| **All Classical Metrics** | ✅ Yes - In drill-down | ⚠️ Only PRR/ROR | **MISSING EBGM, IC, etc.** |
| **Quantum Breakdown** | ✅ Yes - Component breakdown | ❌ Not shown | **MISSING** |
| **Trend Charts** | ✅ Yes - Cases over time | ❌ Not implemented | **MISSING** |
| **Data Breakdown** | ✅ Yes - Age/sex/region | ❌ Not implemented | **MISSING** |
| **Case-Level View** | ✅ Yes - Case table | ❌ Not implemented | **MISSING** |
| **Documentation** | ✅ Yes - Elaborate metrics | ✅ Complete | **DONE** |

---

## 🎯 Key Gaps Identified

### **Gap 1: No Drill-Down Feature (CRITICAL)**

**Status:** ❌ **NOT IMPLEMENTED**

**What's Missing:**
- Row selection mechanism
- Signal details panel
- All metrics shown together

**Impact:** Users can't drill into signals for detailed analysis

---

### **Gap 2: Main Table Not Simplified**

**Status:** ❌ **NOT SIMPLIFIED**

**What's Missing:**
- PRR/ROR should be in drill-down, not main table
- Severity badge column needed

**Impact:** Main table is cluttered, not optimized for quick triage

---

### **Gap 3: Not All Metrics Calculated**

**Status:** ⚠️ **PARTIAL**

**What's Missing:**
- EBGM, IC, BCPNN, Chi-squared, Fisher's NOT calculated
- Functions exist but not called

**Impact:** Missing important statistical validation

---

### **Gap 4: No Quantum Breakdown**

**Status:** ❌ **NOT SHOWN**

**What's Missing:**
- Component breakdown display
- Natural language explanation
- Driver identification

**Impact:** Users can't understand why quantum_score is high

---

### **Gap 5: No Trend Charts**

**Status:** ❌ **NOT IMPLEMENTED**

**What's Missing:**
- Cases over time visualization
- Temporal pattern analysis

**Impact:** Can't see if signal is emerging or stable

---

### **Gap 6: No Data Breakdown**

**Status:** ❌ **NOT IMPLEMENTED**

**What's Missing:**
- Demographics breakdown
- Seriousness breakdown
- Geographic distribution

**Impact:** Can't identify at-risk populations

---

### **Gap 7: No Case-Level View**

**Status:** ❌ **NOT IMPLEMENTED**

**What's Missing:**
- Individual case table
- Case details view
- Narrative links

**Impact:** Can't review individual cases for validation

---

## ✅ What Exists Elsewhere (Can Be Reused)

### **1. Statistical Functions ✅**
- `src/advanced_stats.py`:
  - `calculate_ebgm()` - EBGM with EB05/EB95
  - `calculate_ic()` - IC with IC025/IC975
  - `calculate_bcpnn()` - BCPNN
  - `chi_square_test()` - Chi-squared test
  - `fisher_exact_test()` - Fisher's exact test

### **2. Quantum Explainability ✅**
- `src/quantum_explainability.py`:
  - `explain_quantum_ranking()` - Component breakdown
  - Natural language explanations

### **3. Trend Charts ✅**
- `src/ui/signal_governance_panel.py` - Trend chart rendering
- `src/ui/results_display.py` - Time series charts

### **4. Signal Details Panel ✅**
- `src/ui/signal_governance_panel.py` - Full signal details panel with tabs

### **5. Case Drill-Down ✅**
- `src/ui/results_display.py` - Case-level drill-down
- `src/ui/drill_down.py` - Drill-down utilities

### **6. Data Breakdown ✅**
- `src/signal_stats.py` - `get_summary_stats()` - Age, sex, country breakdowns

---

## 🎯 Recommendation Priority

### **Priority 1: Critical Missing Features**

1. **Row Click Drill-Down** ⚠️ **CRITICAL**
   - No way to see signal details currently
   - This is the core of the expert's recommendation
   - Status: ❌ **NOT IMPLEMENTED**

2. **Simplify Main Table**
   - Remove PRR/ROR from main view
   - Add severity badge
   - Status: ❌ **NOT SIMPLIFIED**

3. **Signal Details Panel**
   - Show all metrics together
   - Component breakdowns
   - Status: ❌ **NOT IMPLEMENTED**

### **Priority 2: Essential Metrics**

4. **Calculate All Classical Metrics**
   - EBGM, IC, BCPNN, Chi-squared, Fisher's
   - Status: ❌ **Functions exist but not called**

5. **Quantum Score Breakdown**
   - Component-by-component view
   - Natural language explanation
   - Status: ❌ **Explanation function exists but not integrated**

### **Priority 3: Enhanced Analysis**

6. **Trend Charts**
   - Cases over time visualization
   - Status: ❌ **Chart functions exist but not integrated**

7. **Data Breakdown**
   - Age, sex, region, seriousness
   - Status: ❌ **Breakdown functions exist but not used**

8. **Case-Level View**
   - Individual case table
   - Status: ❌ **Case viewer exists but not integrated**

---

## 💡 Assessment Summary

### **✅ What We Have:**
1. ✅ Main table showing signals
2. ✅ PRR/ROR calculation and display
3. ✅ Comprehensive help section
4. ✅ Complete documentation
5. ✅ All statistical functions exist elsewhere

### **❌ What We're Missing (From Expert Recommendation):**

1. **Simplified main table** - Remove PRR/ROR, add severity badge
2. **Row click drill-down** - **MAJOR GAP - completely missing**
3. **Signal details panel** - **MAJOR GAP - completely missing**
4. **All classical metrics** - Only PRR/ROR shown, need EBGM, IC, BCPNN, Chi-squared, Fisher's
5. **Quantum score breakdown** - Component breakdown not shown
6. **Trend charts** - Cases over time not visualized
7. **Data breakdown** - Demographics not shown
8. **Case-level view** - Individual cases not accessible

### **🎯 Bottom Line:**

**The main gap is: NO DRILL-DOWN FEATURE**

The expert's recommendation centers around:
- **Simple main table** (for triage) ✅ We have this mostly, but need to simplify
- **Drill-down panel** (for details) ❌ **COMPLETELY MISSING**

All the underlying functions exist - they just need to be integrated into Drug Watchlist with a drill-down UI!

