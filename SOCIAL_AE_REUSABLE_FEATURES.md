# Social AE Module - Reusable Features from Signal/FAERS Module

## 📋 **Executive Summary**

**Great news!** You already have **60-70% of the code** needed for Social AE Phase 1-2 features. Here's what you can reuse:

---

## ✅ **FULLY REUSABLE (Copy & Adapt)**

### **1. Drug Name Normalization** ✅ **100% Reusable**

**Location:** `src/drug_name_normalization.py`

**What it does:**
- Brand-to-generic conversion (200+ drugs)
- Abbreviation expansion
- Misspelling correction
- Fuzzy matching with rapidfuzz
- Multi-drug splitting

**For Social AE:**
- ✅ Normalize drug names from social posts (ozempic → semaglutide)
- ✅ Handle misspellings ("ozempik", "ozempic")
- ✅ Group similar drugs together

**How to use:**
```python
from src.drug_name_normalization import normalize_drug_name, normalize_drug_column

# Normalize single drug
normalized = normalize_drug_name("ozempic")  # Returns "Semaglutide"

# Normalize entire DataFrame
df_normalized = normalize_drug_column(df, drug_column="drug_match")
```

**Effort:** **0 hours** - Already works!

---

### **2. Trendline/Time-Series Charts** ✅ **90% Reusable**

**Location:** `src/ui/results_display.py` (lines 1843-1889)

**What it does:**
- Plotly line charts
- Time-series visualization
- Moving averages
- Delta calculations
- Period comparisons

**For Social AE:**
- ✅ Show reaction trends over time
- ✅ Compare periods (last 30 days vs previous)
- ✅ Visualize spikes

**How to use:**
```python
from src.ui.results_display import _render_trends_tab
import plotly.express as px

# Create trend data (same format as FAERS)
trend_data = {
    "2025-01-01": 10,
    "2025-01-02": 15,
    "2025-01-03": 12,
    # ...
}

# Use existing Plotly code
trend_df = pd.DataFrame(list(trend_data.items()), columns=["Period", "Count"])
trend_df["Period"] = pd.to_datetime(trend_df["Period"])

fig = px.line(
    trend_df,
    x="Period",
    y="Count",
    markers=True,
    color_discrete_sequence=["#2563eb"],
)
st.plotly_chart(fig, use_container_width=True)
```

**Effort:** **2-3 hours** - Adapt existing code

---

### **3. Time-Series Analysis Engine** ✅ **100% Reusable**

**Location:** `src/ai/timeseries_engine.py`

**What it does:**
- Moving averages (MA)
- Exponentially weighted moving average (EWMA)
- Change-point detection
- Control limits
- Anomaly detection

**For Social AE:**
- ✅ Detect spikes in reaction mentions
- ✅ Identify trend changes
- ✅ Calculate expected vs observed

**How to use:**
```python
from src.ai.timeseries_engine import TimeSeriesEngine

ts_engine = TimeSeriesEngine()

# Summarize time-series for Social AE
summary = ts_engine.summarize_timeseries(
    df=social_ae_df,
    drug="ozempic",
    reaction="nausea",
    date_col="created_date",
    drug_col="drug_match",
    reaction_col="reaction"
)

# Returns: moving averages, anomalies, change points, etc.
```

**Effort:** **0 hours** - Already works!

---

### **4. Export Functionality** ✅ **100% Reusable**

**Location:** Multiple files (see below)

**What it does:**
- CSV export with `st.download_button`
- JSON export
- Excel export (with openpyxl)
- Proper encoding and formatting

**For Social AE:**
- ✅ Export labeled dataset (CSV)
- ✅ Export for annotation tools
- ✅ Export with specific columns

**How to use:**
```python
# Pattern from src/ui/results_display.py (line 2220)
csv_data = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download as CSV",
    data=csv_data,
    file_name=f"social_ae_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
    use_container_width=True,
)
```

**Effort:** **1 hour** - Copy pattern, adjust columns

---

### **5. Severity/Seriousness Scoring** ✅ **80% Reusable**

**Location:** 
- `src/quantum_ranking.py` (lines 89-128)
- `src/ai/qsp_engine.py` (lines 113-139)
- `src/ai/risk_prioritization.py` (lines 59-85)

**What it does:**
- Calculates seriousness scores (0-1.0)
- Detects fatal cases
- Hospitalization detection
- Disability detection
- Serious case rate calculation

**For Social AE:**
- ✅ Adapt for social post severity ("mild", "severe", "hospitalized")
- ✅ Detect severity keywords ("ER", "hospital", "fatal")
- ✅ Score severity based on language

**How to adapt:**
```python
# From src/quantum_ranking.py
def calculate_seriousness_score(signal: Dict[str, Any]) -> float:
    score = 0.0
    
    # Check for explicit seriousness flag
    seriousness = signal.get('seriousness')
    if seriousness is not None:
        seriousness_str = normalize_text(str(seriousness))
        if seriousness_str in ['1', 'yes', 'y', 'true', 'serious']:
            score += 0.5
    
    # Check for outcome information
    outcome = signal.get('outcome')
    if outcome is not None:
        outcome_str = normalize_text(str(outcome))
        if any(term in outcome_str for term in ['death', 'fatal', 'died']):
            score += 0.5
        elif any(term in outcome_str for term in ['hospital', 'hospitalized']):
            score += 0.3
    
    return min(1.0, score)

# Adapt for Social AE:
def calculate_social_ae_severity(post_text: str) -> float:
    text_lower = post_text.lower()
    score = 0.0
    
    # Severe keywords
    if any(term in text_lower for term in ['hospital', 'er', 'emergency', 'icu']):
        score += 0.5
    if any(term in text_lower for term in ['severe', 'terrible', 'awful', 'worst']):
        score += 0.3
    if any(term in text_lower for term in ['mild', 'slight', 'minor']):
        score -= 0.2
    
    return max(0.0, min(1.0, score))
```

**Effort:** **4-6 hours** - Adapt existing logic

---

### **6. MedDRA Mapping (Basic)** ✅ **70% Reusable**

**Location:** `src/utils.py` (lines 1064-1115)

**What it does:**
- Maps reaction terms to MedDRA PT
- Uses free synonym dictionary
- Handles partial matches
- Covers ~95% of common AEs

**For Social AE:**
- ✅ Already used in `social_mapper.py` (line 224)
- ✅ Can expand with more terms
- ✅ Works with slang mappings

**How to use:**
```python
from src.utils import map_to_meddra_pt

# Already in your code!
reaction_df["MedDRA PT"] = reaction_df["Reaction"].apply(map_to_meddra_pt)
```

**Effort:** **0 hours** - Already integrated!

---

### **7. Plotly Dependencies** ✅ **100% Reusable**

**Location:** `requirements.txt` (line 8)

**What it does:**
- Plotly 5.22.0 already installed
- Used extensively in FAERS module

**For Social AE:**
- ✅ Heatmaps (drug × reaction)
- ✅ Trendlines
- ✅ Co-occurrence graphs
- ✅ Network graphs

**How to use:**
```python
import plotly.express as px
import plotly.graph_objects as go

# Heatmap example (from src/ui/governance_heatmap.py pattern)
fig = px.imshow(
    heatmap_data,
    labels=dict(x="Drug", y="Reaction", color="Count"),
    x=heatmap_data.columns,
    y=heatmap_data.index,
    color_continuous_scale="Viridis"
)
st.plotly_chart(fig, use_container_width=True)
```

**Effort:** **0 hours** - Already installed!

---

## ⚠️ **PARTIALLY REUSABLE (Needs Adaptation)**

### **8. Retry Logic** ⚠️ **30% Reusable**

**Location:** 
- Documentation mentions it (`COVERAGE_VERIFICATION.md`)
- `src/ai/safe_executor.py` has timeout handling
- No complete retry implementation found

**What exists:**
- Timeout handling (`run_with_timeout`)
- Error handling patterns

**What's missing:**
- Exponential backoff
- Circuit breaker
- Automatic retry decorators

**For Social AE:**
- ⚠️ Need to implement retry logic (but patterns exist)
- Can use `tenacity` library (not in requirements yet)

**How to implement:**
```python
# Add to requirements.txt: tenacity>=8.2.0

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_reddit_posts(...):
    # existing code
```

**Effort:** **2-3 hours** - Add tenacity, implement retry decorators

---

### **9. Co-occurrence Analysis** ⚠️ **50% Reusable**

**Location:** `src/ui/results_display.py` (co-reactions section)

**What exists:**
- Co-reaction detection patterns
- Grouping logic

**For Social AE:**
- ⚠️ Need to adapt for drug-reaction co-occurrence
- Can use similar grouping patterns

**Effort:** **4-6 hours** - Adapt existing patterns

---

## ❌ **NOT REUSABLE (Social AE Specific)**

### **10. Emoji Detection** ❌ **Not Found**

**Status:** Not implemented in signal module

**For Social AE:**
- Need to implement from scratch
- But it's easy (40-line dictionary)

**Effort:** **2-3 hours** - New implementation

---

### **11. Multiple AE Extraction** ❌ **Not Found**

**Status:** Signal module assumes one reaction per case

**For Social AE:**
- Need to implement from scratch
- Extract multiple reactions from single post

**Effort:** **1 week** - New implementation

---

## 📊 **Reusability Summary**

| Feature | Reusability | Effort Saved | Location |
|---------|-------------|--------------|----------|
| **Drug Normalization** | ✅ 100% | 1-2 weeks | `src/drug_name_normalization.py` |
| **Trendline Charts** | ✅ 90% | 2-3 days | `src/ui/results_display.py` |
| **Time-Series Engine** | ✅ 100% | 1 week | `src/ai/timeseries_engine.py` |
| **Export Functionality** | ✅ 100% | 1 day | Multiple files |
| **Severity Scoring** | ✅ 80% | 3-4 days | `src/quantum_ranking.py` |
| **MedDRA Mapping** | ✅ 70% | 1 day | `src/utils.py` |
| **Plotly/Charts** | ✅ 100% | 0 hours | `requirements.txt` |
| **Retry Logic** | ⚠️ 30% | 1 day | Patterns exist |
| **Co-occurrence** | ⚠️ 50% | 2-3 days | Patterns exist |
| **Emoji Detection** | ❌ 0% | 0 hours | New |
| **Multiple AEs** | ❌ 0% | 0 hours | New |

**Total Effort Saved: ~3-4 weeks!**

---

## 🎯 **Recommended Implementation Order**

### **Phase 1 (Week 1) - Reuse Existing**

1. ✅ **Drug Normalization** (0 hours)
   - Import `normalize_drug_name` from `src/drug_name_normalization.py`
   - Apply to `drug_match` column in Social AE

2. ✅ **Export Labeled Dataset** (1 hour)
   - Copy CSV export pattern from `src/ui/results_display.py`
   - Adjust columns for annotation format

3. ✅ **Trendlines** (2-3 hours)
   - Copy Plotly code from `src/ui/results_display.py`
   - Adapt for Social AE date column

4. ⚠️ **Retry Logic** (2-3 hours)
   - Add `tenacity` to requirements.txt
   - Add retry decorators to `social_fetcher.py`

5. ❌ **Emoji Detection** (2-3 hours)
   - New implementation (easy)

**Total: 7-10 hours** (vs 2-3 days if building from scratch)

---

### **Phase 2 (Q1 2026) - Reuse + Adapt**

1. ✅ **Time-Series Analysis** (0 hours)
   - Use `TimeSeriesEngine` directly
   - Already works!

2. ✅ **Severity Scoring** (4-6 hours)
   - Adapt `calculate_seriousness_score` from `src/quantum_ranking.py`
   - Modify for social post language

3. ✅ **Co-occurrence Heatmap** (4-6 hours)
   - Adapt patterns from `src/ui/governance_heatmap.py`
   - Use Plotly (already installed)

4. ❌ **Multiple AE Extraction** (1 week)
   - New implementation

**Total: 1.5-2 weeks** (vs 3-4 weeks if building from scratch)

---

## 💡 **Quick Wins (Copy-Paste Ready)**

### **1. Drug Normalization in Social AE**

```python
# In src/social_ae/social_mapper.py or social_dashboard.py
from src.drug_name_normalization import normalize_drug_name

# Normalize drug_match column
if "drug_match" in df.columns:
    df["drug_match_normalized"] = df["drug_match"].apply(
        lambda x: normalize_drug_name(str(x)) if pd.notna(x) else ""
    )
```

### **2. Trendline Chart in Social Dashboard**

```python
# In src/social_ae/social_dashboard.py
import plotly.express as px
from datetime import datetime

# Group by date
df["date"] = pd.to_datetime(df["created_date"])
df["year_month"] = df["date"].dt.to_period("M").astype(str)
trend_data = df.groupby("year_month").size().reset_index(name="count")

# Create chart (copy from src/ui/results_display.py:1854)
fig = px.line(
    trend_data,
    x="year_month",
    y="count",
    markers=True,
    color_discrete_sequence=["#2563eb"],
)
fig.update_layout(
    xaxis_title="Period",
    yaxis_title="Posts",
    height=320,
)
st.plotly_chart(fig, use_container_width=True)
```

### **3. Export with Specific Columns**

```python
# In src/social_ae/social_dashboard.py
# Copy from src/ui/results_display.py:2220

# Define columns for annotation
export_columns = [
    "post_id", "text", "reaction", "confidence_score", 
    "drug_match", "platform", "created_date", "needs_review"
]

# Filter to available columns
available_cols = [col for col in export_columns if col in df.columns]
export_df = df[available_cols].copy()

# Add empty needs_review column if missing
if "needs_review" not in export_df.columns:
    export_df["needs_review"] = ""

# Export
csv_data = export_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Export for Annotation (CSV)",
    data=csv_data,
    file_name=f"social_ae_annotation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
)
```

---

## ✅ **Final Recommendation**

**You can save 3-4 weeks of development** by reusing existing code!

**Priority order:**
1. ✅ **Drug normalization** - 0 hours (already works)
2. ✅ **Trendlines** - 2-3 hours (copy-paste)
3. ✅ **Export** - 1 hour (copy-paste)
4. ✅ **Time-series engine** - 0 hours (already works)
5. ⚠️ **Retry logic** - 2-3 hours (add tenacity)
6. ✅ **Severity scoring** - 4-6 hours (adapt existing)
7. ✅ **Co-occurrence** - 4-6 hours (adapt existing)

**Total saved: ~3-4 weeks of development time!**

---

## 📝 **Action Items**

1. ✅ **Add drug normalization** to Social AE (0 hours)
2. ✅ **Copy trendline code** to Social dashboard (2-3 hours)
3. ✅ **Copy export pattern** for labeled dataset (1 hour)
4. ✅ **Use TimeSeriesEngine** for trend analysis (0 hours)
5. ⚠️ **Add tenacity** to requirements.txt (5 minutes)
6. ⚠️ **Add retry decorators** to social_fetcher.py (2-3 hours)
7. ✅ **Adapt severity scoring** from quantum_ranking.py (4-6 hours)

**You're in great shape - most of the hard work is already done!** 🚀

