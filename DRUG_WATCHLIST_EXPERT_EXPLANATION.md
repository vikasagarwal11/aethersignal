# Drug Watchlist – Expert-Level Explanation (Regulatory-Facing)

## ✅ **1. What Drug Watchlist Actually Does**

**Drug Watchlist = Automated Daily Surveillance System**

Its purpose is to:

* Take a list of your **portfolio drugs**
* Search across **all uploaded case data (FAERS/Argus/Veeva/E2B/etc.)**
* Detect **newly emerging safety signals**
* Rank them using **quantum score** + classical disproportionality metrics
* Return **top priority risks** that you should review today

This is essentially your **"Daily Safety Radar"**.

---

## ✅ **2. What Information Is Shown Here?**

### **📌 Column: source_drug**

The drug from your input list that was identified in case data.

**Why useful:**

You see exactly which drug in your portfolio generated a signal.

---

### **📌 Column: reaction**

The MedDRA term(s) associated with that signal.

May include:

* PT (Preferred Term)
* Combinations of PTs depending on data structure
* Concomitant reactions if they co-occur frequently

**Why useful:**

Identifies the **adverse event** that is showing unusual frequency or severity.

---

### **📌 Column: count**

How many reports were found for that (drug, reaction) combination.

**Why useful:**

Volume indicator: a cluster of many cases is more concerning.

---

### **📌 Column: quantum_score (0–1 range)**

This is the **core innovation** of your system.

Quantum score = a composite anomaly score informed by:

* **Rarity (40%)**: Rare events are more interesting than common ones
  - Formula: 1 - (count / total_cases)
  - Higher rarity = higher score
* **Seriousness (35%)**: Serious adverse events get higher priority
  - Based on seriousness flags, outcomes (death, hospitalization, etc.)
* **Recency (20%)**: Recent cases are more relevant
  - Cases from last year get full weight
  - Older cases get diminishing weight
* **Count (5%)**: Minimum threshold for statistical relevance
  - Normalized: min(1.0, count / 10.0)

**Quantum-Inspired Enhancements:**
* **Bayesian priors**: Incorporates prior knowledge about signal patterns
* **Disproportionality shifts**: Detects unusual reporting patterns
* **Novelty detection**: Identifies new, unexpected signals
* **Temporal spikes**: Catches sudden increases in reporting
* **Cross-feature correlations**: Considers interactions between multiple factors
* **Local Outlier Factor**: Identifies signals that deviate from local patterns
* **Isolation models**: Detects anomalous signals through isolation
* **Quantum-inspired ranking**: Based on eigenvector influence and superposition principles

**Non-linear Interaction Boosts:**
* Rare + Serious = Critical signals (+0.15 boost)
* Rare + Recent = Emerging signals (+0.10 boost)
* Serious + Recent = Urgent signals (+0.10 boost)
* All three = Highest priority signals (+0.20 boost)
* Quantum tunneling: Small boost for signals "close" to thresholds (+0.05 each)

**Higher = more urgent signal**

**Interpretation:**
* **0.70 - 1.0**: Very high priority (investigate immediately)
* **0.55 - 0.70**: Elevated priority (investigate soon)
* **0.40 - 0.55**: Moderate priority (monitor trends)
* **0.30 - 0.40**: Lower priority (may be expected)
* **0.0 - 0.30**: Low priority (likely expected)

A score near **0.55** is already elevated.

A score near **0.70** would be very high.

---

### **📌 Column: quantum_rank**

Rank position among all detected signals **based on quantum score**.

**1 = most concerning emerging signal**

This is your **machine-prioritized short list** of where to look.

---

### **📌 Column: classical_rank**

Rank based on **traditional PV metrics**:

* **PRR** (Proportional Reporting Ratio)
* **ROR** (Reporting Odds Ratio)
* **EBGM** (Empirical Bayes Geometric Mean)
* **IC** (Information Component)
* **Chi-squared** test
* **Reporting Odds Ratio**

**Why useful:**

Shows whether classical disproportionality analysis agrees (or disagrees) with the quantum signal.

**Differences can be telling:**

| If quantum rank is high but classical rank is low… | Meaning                                            |
| -------------------------------------------------- | -------------------------------------------------- |
| Risk is newly emerging                             | Classical methods are slow to detect early signals |
| Rare-event signal                                  | Classical methods underperform on sparse datasets  |
| Complex correlation pattern                        | Quantum model captures nonlinear relationships     |

---

### **📌 Column: PRR (Proportional Reporting Ratio)**

**Formula:** PRR = (a / (a+b)) / (c / (c+d))

Where:
* a = Drug + Reaction cases
* b = Drug, no Reaction cases
* c = No Drug, Reaction cases
* d = No Drug, no Reaction cases

**Interpretation:**
* **PRR > 2**: Suggests potential signal (reaction reported more often with drug than without)
* **PRR > 3**: Stronger signal
* **PRR < 1**: Reaction reported less often with drug (potential protective effect)

**Why useful:**

Standard disproportionality measure used in pharmacovigilance. Measures how often a reaction is reported with a drug relative to all other drugs.

---

### **📌 Column: ROR (Reporting Odds Ratio)**

**Formula:** ROR = (a × d) / (b × c)

**Interpretation:**
* **ROR > 2**: Suggests potential signal
* **ROR > 3**: Stronger signal
* **ROR < 1**: Protective effect possible

**Why useful:**

Alternative disproportionality measure. Similar to PRR but uses odds ratio instead of proportions.

---

## ✅ **3. The Green Banner: Signal Summary**

You saw:

> **Found 841 potential signals → showing top 50 ranked by quantum score**

Meaning:

* The system scanned your portfolio across the entire dataset.
* It found **841 unique drug–reaction pairs** that might be important.
* It returns **only the top 50**, ranked by urgency.

---

## ✅ **4. Additional Statistical Measures (Available in Full Report)**

### **EBGM (Empirical Bayes Geometric Mean)**

**What it is:**

Bayesian shrinkage estimator that stabilizes estimates for rare events.

**Formula:**

EBGM = exp(log(observed / expected))

With confidence intervals: EB05, EB95

**Interpretation:**
* **EBGM > 2**: Suggests potential signal
* **EB05 > 2**: Lower bound of 90% CI exceeds 2 (stronger signal)
* **EB95**: Upper bound of 90% CI

**Why useful:**

Handles sparse data better than PRR/ROR. Used by FDA in FAERS analysis.

---

### **IC (Information Component)**

**What it is:**

Log2 of the ratio of observed to expected cases.

**Formula:**

IC = log2((a + λ) / expected)

Where λ = shrinkage parameter (typically 0.5)

**Interpretation:**
* **IC > 0**: More reports than expected
* **IC > 2**: Strong signal
* **IC with IC025 > 0**: Credibility interval suggests signal

**Why useful:**

Used in WHO Vigibase. Provides credibility intervals (IC025, IC975).

---

### **BCPNN (Bayesian Confidence Propagation Neural Network)**

**What it is:**

Bayesian method for signal detection using neural network principles.

**Formula:**

Similar to IC calculation with Bayesian priors.

**Interpretation:**
* Similar to IC
* Provides credibility intervals
* Handles uncertainty in sparse data

**Why useful:**

Robust for rare events. Used in pharmacovigilance databases.

---

### **Chi-squared Test**

**What it is:**

Statistical test for independence between drug and reaction.

**Formula:**

χ² = Σ((observed - expected)² / expected)

**Interpretation:**
* **p-value < 0.05**: Significant association
* **p-value < 0.01**: Highly significant
* Higher χ² = stronger association

**Why useful:**

Tests whether drug-reaction association is statistically significant.

---

### **Fisher's Exact Test**

**What it is:**

Exact probability test for 2x2 contingency tables.

**Interpretation:**
* **p-value < 0.05**: Significant association
* More accurate for small sample sizes than chi-squared

**Why useful:**

Better than chi-squared for small datasets or sparse tables.

---

## ✅ **5. How This View Is Used in Real Safety Teams**

This is the **daily dashboard for safety surveillance**.

Pharma companies use this exact workflow to:

---

### 🧭 **1. Prioritize Safety Review Meetings**

Safety leads look at:

* top-ranked quantum signals
* newly emerging reactions
* mismatches between quantum and classical

They decide:

* which signals analysts should review today
* whether follow-up case evaluation is needed
* whether a safety narrative or SME review is required

---

### 🧪 **2. Identify emerging safety trends early**

The system can catch:

* rare but serious AEs earlier than classical metrics
* unexpected clusters
* device-related events
* medication errors
* injection-site issues
* immune-related complications

Because the model looks at **patterns**, not just counts.

---

### ⚠️ **3. Triage risks before formal signal detection**

This lets safety teams:

* Catch potential issues **before regulators ask**
* Reduce risk of:
  * missing early signals
  * late detection
  * safety escalations
  * label-update delays

---

### 🧾 **4. Generate evidence for PSUR / PBRER reports**

Signals detected here feed into:

* Section 15 (Significant safety findings)
* New risk signals requiring evaluation
* Line listings and aggregate trend analyses

The "Download Full Report" button provides:

* ranked signals
* supporting case counts
* disproportionality
* quantum anomaly metrics
* trend timelines

All needed for regulatory documents.

---

## ✅ **6. TL;DR: Why Drug Watchlist Is So Valuable**

### It automatically:

* Monitors **your whole drug portfolio**
* Scans **hundreds of thousands of cases**
* Identifies **unusual patterns**
* Ranks signals by urgency
* Highlights **what changed today**

### It replaces:

* Manual Excel filtering
* Slow FAERS searches
* Outdated disproportionality-only methods
* Human triage bottlenecks

### It gives you:

* A daily "Safety Weather Radar"
* Early threat detection
* More confidence in surveillance
* Reduced analyst workload
* Faster safety decision-making

---

## 📊 **7. Scoring Metrics Comparison Table**

| Metric | Range | Interpretation | Best For |
|--------|-------|----------------|----------|
| **Quantum Score** | 0.0 - 1.0 | Higher = more urgent | Prioritizing signals, rare events, emerging trends |
| **PRR** | 0 - ∞ | >2 = signal | Standard disproportionality, common signals |
| **ROR** | 0 - ∞ | >2 = signal | Alternative disproportionality measure |
| **EBGM** | 0 - ∞ | >2 = signal, EB05>2 = stronger | Sparse data, FDA standard |
| **IC** | -∞ - +∞ | >0 = signal, >2 = strong | WHO Vigibase, rare events |
| **BCPNN** | -∞ - +∞ | Similar to IC | Bayesian approach, sparse data |
| **Chi-squared p-value** | 0 - 1 | <0.05 = significant | Statistical significance |
| **Fisher's p-value** | 0 - 1 | <0.05 = significant | Small datasets, exact test |

---

## 🎯 **8. Decision Matrix: When to Investigate**

| Quantum Score | PRR/ROR | Classical Rank | Action |
|--------------|---------|----------------|--------|
| >0.70 | >2 | Any | **Investigate immediately** |
| >0.55 | >2 | High | **Investigate soon** |
| >0.55 | <2 | High | **Monitor closely** (quantum detected, classical didn't) |
| 0.40-0.55 | >2 | Moderate | **Review case series** |
| <0.40 | >3 | Low | **May investigate** (strong classical signal) |
| <0.40 | <2 | Any | **Monitor** (low priority) |

---

## 📋 **9. Regulatory Considerations**

**For PSUR/PBRER:**
* Include signals with quantum_score > 0.55
* Document PRR/ROR for regulatory validation
* Provide case counts and timelines
* Include classical rankings for comparison

**For Signal Detection:**
* Quantum ranking helps prioritize, but classical metrics provide validation
* Use both quantum and classical for comprehensive analysis
* Document methodology in regulatory submissions

**For Safety Reviews:**
* Review top 20 quantum-ranked signals daily
* Escalate signals with quantum_score > 0.70
* Compare with previous periods to identify trends

---

This expert explanation provides the regulatory-facing and product design documentation needed for Drug Watchlist feature.

