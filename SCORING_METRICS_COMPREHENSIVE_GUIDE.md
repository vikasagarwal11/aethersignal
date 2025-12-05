# Comprehensive Scoring Metrics Guide - Drug Watchlist

## Overview

This document provides detailed explanations of all scoring and ranking metrics used in Drug Watchlist for signal detection and prioritization in pharmacovigilance.

---

## 📊 Quantum Score (0.0 - 1.0)

### **Core Innovation**

The Quantum Score is AetherSignal's proprietary composite anomaly score that prioritizes signals based on multiple dimensions, not just frequency.

### **Component Breakdown**

#### **1. Rarity Component (40% weight)**

**Formula:** `rarity = 1 - (count / total_cases)`

**Purpose:** Rare events are more interesting than common ones. A reaction that appears in 1% of cases is more noteworthy than one appearing in 50%.

**Calculation:**
- If signal has 100 cases out of 10,000 total: rarity = 1 - (100/10,000) = 0.99
- If signal has 5,000 cases out of 10,000 total: rarity = 1 - (5,000/10,000) = 0.50

**Why 40%?** Rare events often indicate unexpected safety concerns that need investigation.

---

#### **2. Seriousness Component (35% weight)**

**Purpose:** Serious adverse events get higher priority than non-serious ones.

**Factors Considered:**

**a) Explicit Seriousness Flags:**
- `serious = True/1` → +0.5 score
- `serious = False/0` → +0.0 score

**b) Outcome Information:**
- **Death**: +0.5 score
  - Keywords: "death", "fatal", "died", "deceased"
- **Life-Threatening/Hospitalization**: +0.3 score
  - Keywords: "hospital", "hospitalized", "life", "threatening"
- **Disability**: +0.2 score
  - Keywords: "disability", "disabled", "permanent"

**c) Serious Proportion:**
- `serious_proportion = serious_count / total_count`
- Adds: `serious_proportion × 0.3` to score

**Example:**
- Signal with 50 serious cases out of 100 total:
  - Serious proportion = 0.5
  - Seriousness score = 0.5 + (0.5 × 0.3) = 0.65

**Why 35%?** Serious events require immediate attention and regulatory reporting.

---

#### **3. Recency Component (20% weight)**

**Purpose:** Recent cases are more relevant than old cases.

**Time-Based Scoring:**

**Last Year (0-365 days):**
- Recency score = 1.0 - (days_ago / 365.0) × 0.5
- Range: 0.5 to 1.0
- Example: 30 days ago → score = 1.0 - (30/365) × 0.5 = 0.96

**Year 2 (366-730 days):**
- Recency score = 0.5 - ((days_ago - 365) / 365.0) × 0.3
- Range: 0.2 to 0.5

**Older (>730 days):**
- Recency score = max(0.0, 0.2 - (days_ago - 730) / 3650.0)
- Diminishing weight

**Why 20%?** Recent signals may indicate emerging trends or changes in reporting patterns.

---

#### **4. Count Component (5% weight)**

**Formula:** `min(1.0, count / 10.0)`

**Purpose:** Minimum threshold for statistical relevance. Ensures we have enough cases to make meaningful conclusions.

**Example:**
- 5 cases → score = 5/10 = 0.5
- 10 cases → score = 1.0
- 20 cases → score = 1.0 (capped)

**Why 5%?** Small weight to ensure minimum case count without overwhelming other factors.

---

### **Quantum-Inspired Enhancements**

These are the "quantum" aspects that add non-linear interactions:

#### **1. Interaction Terms**

**Rare + Serious (+0.15 boost):**
- If rarity > 0.7 AND seriousness > 0.5
- Critical signals that need immediate attention

**Rare + Recent (+0.10 boost):**
- If rarity > 0.7 AND recency > 0.7
- Emerging signals that just appeared

**Serious + Recent (+0.10 boost):**
- If seriousness > 0.7 AND recency > 0.7
- Urgent signals requiring immediate action

**All Three (+0.20 boost):**
- If rarity > 0.6 AND seriousness > 0.6 AND recency > 0.6
- Highest priority signals

#### **2. Quantum Tunneling Effect (+0.05 each)**

Small boost for signals that are "close" to being rare/serious/recent:
- If 0.5 < rarity ≤ 0.7 → +0.05
- If 0.5 < seriousness ≤ 0.7 → +0.05
- If 0.5 < recency ≤ 0.7 → +0.05

**Purpose:** Captures signals that are "almost" important but might be missed by strict thresholds.

---

### **Final Quantum Score Calculation**

```
base_score = (0.40 × rarity) + (0.35 × seriousness) + (0.20 × recency) + (0.05 × count_normalized)
interaction_term = sum of all applicable interaction boosts
tunneling_boost = sum of all tunneling effects
quantum_score = base_score + interaction_term + tunneling_boost
quantum_score = max(0.0, min(1.0, quantum_score))  # Clamp to [0, 1]
```

---

## 📈 Classical Statistical Measures

### **PRR (Proportional Reporting Ratio)**

**What it is:** Measures how often a reaction is reported with a drug compared to all other drugs.

**Formula:**
```
PRR = (a / (a+b)) / (c / (c+d))
```

Where:
- a = Drug + Reaction cases
- b = Drug, no Reaction cases
- c = No Drug, Reaction cases
- d = No Drug, no Reaction cases

**Example:**
- 100 cases with Drug X + Reaction Y
- 900 cases with Drug X, no Reaction Y
- 500 cases with no Drug X, but Reaction Y
- 10,000 cases with no Drug X, no Reaction Y

PRR = (100/1000) / (500/10,500) = 0.1 / 0.048 = 2.08

**Interpretation:**
- **PRR = 1.0**: No association (reaction reported equally with/without drug)
- **PRR > 2**: Suggests potential signal (reaction reported 2x more often with drug)
- **PRR > 3**: Stronger signal
- **PRR < 1**: Reaction reported less often with drug (possible protective effect)

**95% Confidence Interval:**
- Calculated using log-normal approximation
- If CI lower bound > 1, signal is statistically significant

**Use Cases:**
- Standard disproportionality analysis
- Regulatory submissions (FDA, EMA)
- Routine signal detection

---

### **ROR (Reporting Odds Ratio)**

**What it is:** Alternative disproportionality measure using odds ratio.

**Formula:**
```
ROR = (a × d) / (b × c)
```

Using same example:
ROR = (100 × 10,000) / (900 × 500) = 1,000,000 / 450,000 = 2.22

**Interpretation:**
- **ROR = 1.0**: No association
- **ROR > 2**: Suggests potential signal
- **ROR > 3**: Stronger signal

**95% Confidence Interval:**
- Calculated using log-normal approximation

**Advantages:**
- Simpler calculation than PRR
- Works well for rare events

**Use Cases:**
- Alternative to PRR
- Cross-validation of PRR results

---

### **EBGM (Empirical Bayes Geometric Mean)**

**What it is:** Bayesian shrinkage estimator that stabilizes estimates for rare events.

**Formula:**
```
Expected = (row_total × col_total) / n
obs = a + 0.5  (prior adjustment)
exp_adj = expected + 0.5
rr = obs / exp_adj
EBGM = exp(log(rr))
```

**Confidence Intervals:**
- **EB05**: Lower bound of 90% confidence interval
- **EB95**: Upper bound of 90% confidence interval

**Interpretation:**
- **EBGM > 2**: Suggests potential signal
- **EB05 > 2**: Lower bound exceeds 2 (stronger signal)
- **EB95**: Upper bound

**Advantages:**
- Handles sparse data better than PRR/ROR
- Bayesian approach reduces false positives
- Used by FDA in FAERS analysis

**Use Cases:**
- Large databases (FAERS, EudraVigilance)
- Rare event detection
- Regulatory standard (FDA)

---

### **IC (Information Component)**

**What it is:** Log2 of the ratio of observed to expected cases.

**Formula:**
```
Expected = ((a + b) × (a + c)) / n
IC = log2((a + λ) / expected)
```

Where λ = shrinkage parameter (typically 0.5)

**Credibility Intervals:**
- **IC025**: Lower bound of 95% credibility interval
- **IC975**: Upper bound of 95% credibility interval

**Interpretation:**
- **IC = 0**: No signal (observed = expected)
- **IC > 0**: More reports than expected
- **IC > 2**: Strong signal
- **IC025 > 0**: Credibility interval suggests signal

**Advantages:**
- Handles uncertainty in sparse data
- Used by WHO in Vigibase
- Provides credibility intervals

**Use Cases:**
- WHO Vigibase analysis
- Rare event detection
- International pharmacovigilance

---

### **BCPNN (Bayesian Confidence Propagation Neural Network)**

**What it is:** Bayesian method using neural network principles.

**Formula:** Similar to IC with Bayesian priors

**Interpretation:** Same as IC

**Advantages:**
- Robust for rare events
- Bayesian approach reduces false positives
- Neural network principles for pattern recognition

**Use Cases:**
- Advanced signal detection
- Pattern recognition
- Complex data structures

---

### **Chi-squared Test**

**What it is:** Statistical test for independence between drug and reaction.

**Formula:**
```
χ² = Σ((observed - expected)² / expected)
```

**Contingency Table:**
```
        Reaction  No Reaction
Drug        a          b
No Drug     c          d
```

**p-value Interpretation:**
- **p < 0.05**: Significant association (reject independence)
- **p < 0.01**: Highly significant
- **p > 0.05**: No significant association

**Use Cases:**
- Hypothesis testing
- Statistical validation
- Regulatory documentation

---

### **Fisher's Exact Test**

**What it is:** Exact probability test for 2x2 contingency tables.

**Advantages:**
- More accurate for small sample sizes than chi-squared
- Exact calculation (no approximation)
- Works well for sparse data

**Interpretation:**
- **p < 0.05**: Significant association
- **p < 0.01**: Highly significant

**Use Cases:**
- Small datasets
- Rare events
- When chi-squared assumptions don't hold

---

## 🏆 Ranking Systems

### **Quantum Rank**

**Definition:** Position when signals are sorted by Quantum Score (descending)

**Calculation:**
1. Calculate quantum_score for all signals
2. Sort by quantum_score (highest first)
3. Assign ranks: 1, 2, 3, ...
4. Signals with same score get same rank

**Interpretation:**
- **Rank 1**: Highest priority signal (highest quantum score)
- Lower rank = Higher priority

**Use Cases:**
- Primary prioritization method
- Daily surveillance
- Safety review meetings

---

### **Classical Rank**

**Definition:** Position when signals are sorted by case count (descending)

**Calculation:**
1. Sort all signals by count (highest first)
2. Assign ranks: 1, 2, 3, ...

**Interpretation:**
- **Rank 1**: Most cases reported
- Traditional frequency-based ranking

**Use Cases:**
- Comparison with quantum ranking
- Traditional signal detection
- Volume-based prioritization

---

## 📊 Comparison Table

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

## 🎯 Decision Matrix

| Quantum Score | PRR/ROR | Classical Rank | Action |
|--------------|---------|----------------|--------|
| >0.70 | >2 | Any | **Investigate immediately** |
| >0.55 | >2 | High | **Investigate soon** |
| >0.55 | <2 | High | **Monitor closely** (quantum detected, classical didn't) |
| 0.40-0.55 | >2 | Moderate | **Review case series** |
| <0.40 | >3 | Low | **May investigate** (strong classical signal) |
| <0.40 | <2 | Any | **Monitor** (low priority) |

---

## 📋 Regulatory Considerations

**For PSUR/PBRER:**
- Include signals with quantum_score > 0.55
- Document PRR/ROR for regulatory validation
- Provide case counts and timelines
- Include classical rankings for comparison

**For Signal Detection:**
- Quantum ranking helps prioritize, but classical metrics provide validation
- Use both quantum and classical for comprehensive analysis
- Document methodology in regulatory submissions

**For Safety Reviews:**
- Review top 20 quantum-ranked signals daily
- Escalate signals with quantum_score > 0.70
- Compare with previous periods to identify trends

---

## ✅ Summary

**Quantum Score** provides intelligent prioritization based on rarity, seriousness, and recency.

**Classical Metrics** (PRR, ROR, EBGM, IC) provide statistical validation and regulatory compliance.

**Combined Approach** gives safety teams the best of both worlds:
- Early detection (quantum)
- Statistical rigor (classical)
- Regulatory acceptance (standard metrics)

