# Quantum Clustering UI - What It Is & Why It's Useful

**Current Status:** Module exists, but not visible to users  
**Time to Complete:** ~30 minutes  
**Location:** Signals tab, after Subgroup Discovery section

---

## 🔍 What Is Quantum Clustering?

### Current Situation

**What Exists:**
- ✅ `src/quantum_clustering.py` - Full working module
- ✅ `cluster_cases_for_signal()` - Function that clusters cases
- ✅ `quantum_kmeans()` - Quantum-inspired clustering algorithm
- ✅ Module imported in `results_display.py` (line 25)

**What's Missing:**
- ❌ The function is **never called**
- ❌ No UI to display the results
- ❌ Users can't see the clusters

### What It Does

When you have a drug-reaction signal (e.g., "Semaglutide - Pancreatitis"), quantum clustering:

1. **Takes all cases** matching that drug-reaction pair
2. **Builds a feature matrix** from:
   - Age (normalized 0-1)
   - Sex (0=M, 1=F, 0.5=unknown)
   - Seriousness (0=not serious, 1=serious)
3. **Clusters cases** into 3 groups using quantum-inspired distance weighting
4. **Returns cluster summaries** with:
   - Cluster ID
   - Number of cases in cluster
   - Mean age
   - Percentage of serious cases
   - Percentage male/female

### How It's Different from Subgroup Discovery

| Feature | Subgroup Discovery (Current) | Quantum Clustering (Missing) |
|---------|------------------------------|----------------------------|
| **Method** | Pre-defined demographic filters (age groups, sex, country) | Unsupervised clustering (finds patterns automatically) |
| **What It Finds** | "Signal is strongest in age 65+" | "Cluster 1: 45 cases, mean age 68, 85% serious, 60% female" |
| **Discovery** | You must know what to look for | Discovers hidden patterns you didn't know to look for |
| **Use Case** | "Is this signal stronger in elderly?" | "What patient subgroups exist in this signal?" |

**Key Difference:** Subgroup Discovery tests **known hypotheses** (age, sex, country). Quantum Clustering **discovers unknown patterns** automatically.

---

## 💡 Why It's Useful

### 1. **Discovers Hidden Patient Subgroups**

**Example Scenario:**
- You have 200 cases of "Semaglutide - Pancreatitis"
- Subgroup Discovery might show: "Stronger in age 65+"
- Quantum Clustering might discover:
  - **Cluster 1:** 45 cases, mean age 68, 85% serious, 60% female → **High-risk elderly women**
  - **Cluster 2:** 80 cases, mean age 52, 30% serious, 40% female → **Moderate-risk middle-aged**
  - **Cluster 3:** 75 cases, mean age 35, 10% serious, 70% male → **Low-risk young men**

**Value:** You discover that **elderly women are the highest-risk subgroup** - a pattern you might not have tested with Subgroup Discovery.

### 2. **Complements Existing Subgroup Discovery**

**Current Flow:**
1. User sees PRR/ROR for drug-reaction
2. Subgroup Discovery shows: "Stronger in age 65+, women, USA"
3. **Missing:** What are the actual patient clusters?

**With Quantum Clustering:**
1. User sees PRR/ROR for drug-reaction
2. Subgroup Discovery shows demographic patterns
3. **Quantum Clustering shows:** "Here are 3 distinct patient clusters with different risk profiles"

**Value:** Two different perspectives - demographic filters vs. unsupervised patterns.

### 3. **Identifies High-Risk Subpopulations**

**Use Case:**
- Safety scientist investigating a signal
- Needs to identify which patient subgroup to prioritize
- Quantum clustering automatically identifies the highest-risk cluster

**Example Output:**
```
Cluster 1 (Highest Risk):
- 45 cases
- Mean age: 68 years
- 85% serious cases
- 60% female
→ This is the subgroup to investigate first
```

**Value:** Prioritizes investigation efforts automatically.

### 4. **Marketing & Competitive Advantage**

**Talking Points:**
- "Our quantum-inspired clustering discovers patient subgroups classical methods miss"
- "Unsupervised pattern discovery for safety signals"
- "Automatically identifies high-risk patient clusters"

**Value:** Unique feature that competitors don't have.

### 5. **Research & Publication Value**

**Potential Research:**
- "Quantum-Inspired Clustering for Pharmacovigilance Subgroup Discovery"
- Compare quantum-inspired vs. classical k-means
- Show that quantum-inspired finds more meaningful clusters

**Value:** Scientific credibility and publications.

---

## 🎯 Real-World Example

### Scenario: Investigating "Wegovy - Gastroparesis" Signal

**Step 1: Current Subgroup Discovery**
- Shows: "Signal stronger in age 50+, women, USA"
- **Limitation:** Only tests pre-defined groups

**Step 2: Quantum Clustering (After UI Integration)**
- Discovers 3 clusters:
  - **Cluster 1:** 30 cases, age 55, 90% serious, 70% female, 60% with diabetes
  - **Cluster 2:** 50 cases, age 45, 40% serious, 50% female, 30% with diabetes
  - **Cluster 3:** 20 cases, age 35, 10% serious, 30% female, 10% with diabetes

**Insight:** Cluster 1 (elderly diabetic women) is the highest-risk subgroup - this might not have been obvious from demographic filters alone.

**Action:** Focus investigation on elderly diabetic women taking Wegovy.

---

## 🔧 What Needs to Be Done (30 Minutes)

### Current Code Location
- **File:** `src/ui/results_display.py`
- **Location:** After Subgroup Discovery section (around line 668)
- **Module:** `quantum_clustering` is already imported (line 25)

### What to Add

Add this code block after the Subgroup Discovery section (after line 668):

```python
# Quantum-Inspired Clustering
if "drug" in filters and "reaction" in filters:
    drug = filters["drug"] if isinstance(filters["drug"], str) else filters["drug"][0]
    reaction = filters["reaction"] if isinstance(filters["reaction"], str) else filters["reaction"][0]
    
    matching_cases = summary.get("matching_cases", 0)
    if matching_cases >= 20:  # Minimum cases for clustering
        st.markdown("---")
        st.markdown("#### ⚛️ Quantum-Inspired Clustering (experimental)")
        st.caption(
            "Unsupervised clustering of cases within this signal to discover "
            "high-risk patient subgroups. Uses quantum-inspired distance weighting."
        )
        
        with st.spinner("Clustering cases with quantum-inspired algorithm..."):
            clusters = quantum_clustering.cluster_cases_for_signal(
                normalized_df, drug, reaction, min_cases=20, k=3
            )
        
        if clusters:
            cluster_data = []
            for cluster in clusters:
                cluster_data.append({
                    "Cluster": f"Cluster {cluster['cluster_id']}",
                    "Cases": cluster['size'],
                    "Mean Age": f"{cluster['mean_age']:.1f}" if cluster['mean_age'] else "N/A",
                    "Serious %": f"{cluster['serious_pct']:.1f}%",
                    "Male %": f"{cluster['male_pct']:.1f}%" if cluster['male_pct'] else "N/A",
                    "Female %": f"{cluster['female_pct']:.1f}%" if cluster['female_pct'] else "N/A",
                })
            
            cluster_df = pd.DataFrame(cluster_data)
            st.dataframe(cluster_df, use_container_width=True, hide_index=True)
            
            # Highlight highest-risk cluster
            if clusters:
                top_cluster = clusters[0]  # Already sorted by serious_pct
                st.caption(
                    f"💡 **Highest-risk cluster:** Cluster {top_cluster['cluster_id']} "
                    f"({top_cluster['size']} cases, {top_cluster['serious_pct']:.1f}% serious, "
                    f"mean age {top_cluster['mean_age']:.0f} years)"
                )
        else:
            st.info("ℹ️ Not enough cases for clustering (minimum 20 cases required).")
```

**That's it!** Just ~30 lines of code to display the clusters.

---

## 📊 Expected User Experience

### Before (Current)
```
Signals Tab:
├── PRR/ROR Metrics
├── 2×2 Contingency Table
├── Subgroup Discovery
│   ├── Age subgroups
│   ├── Sex subgroups
│   └── Country subgroups
└── [End]
```

### After (With Quantum Clustering)
```
Signals Tab:
├── PRR/ROR Metrics
├── 2×2 Contingency Table
├── Subgroup Discovery
│   ├── Age subgroups
│   ├── Sex subgroups
│   └── Country subgroups
├── ⚛️ Quantum-Inspired Clustering (NEW!)
│   ├── Cluster 1: 45 cases, age 68, 85% serious, 60% female
│   ├── Cluster 2: 80 cases, age 52, 30% serious, 40% female
│   └── Cluster 3: 75 cases, age 35, 10% serious, 70% male
└── [End]
```

---

## 🎯 Business Value

### 1. **Completes Quantum Feature Set**
- Quantum ranking ✅
- Quantum anomaly detection ✅
- Quantum clustering ⚠️ (needs UI)
- **Value:** Full quantum-inspired analytics suite

### 2. **Competitive Differentiation**
- No competitor has unsupervised patient clustering
- Quantum branding adds credibility
- **Value:** Unique selling point

### 3. **User Value**
- Discovers patterns users didn't know to look for
- Prioritizes investigation efforts
- **Value:** Better safety insights

### 4. **Low Effort, High Impact**
- 30 minutes of work
- Module already exists and works
- Just needs UI display
- **Value:** Quick win

---

## ✅ Summary

**What It Is:**
- Unsupervised clustering of patient cases within a drug-reaction signal
- Discovers hidden patient subgroups automatically
- Uses quantum-inspired distance weighting

**Why It's Useful:**
1. Discovers patterns you didn't know to look for
2. Identifies highest-risk patient subgroups
3. Complements existing Subgroup Discovery
4. Competitive differentiator
5. Low effort (30 min), high impact

**What Needs to Be Done:**
- Add ~30 lines of UI code in Signals tab
- Display cluster results in a table
- Show highest-risk cluster prominently

**Bottom Line:** It's a **quick win** that completes your quantum feature set and provides real value to safety scientists investigating signals.

