# 🧠 AetherSignal – Complete Engineering Blueprint

**Version:** 1.0  
**Date:** January 2025  
**Purpose:** Comprehensive system documentation for migration, redesign, or new team onboarding

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Core Modules & Features](#3-core-modules--features)
4. [Data Processing Pipeline](#4-data-processing-pipeline)
5. [AI & Intelligence Layer](#5-ai--intelligence-layer)
6. [Data Sources & Integration](#6-data-sources--integration)
7. [Storage & Persistence](#7-storage--persistence)
8. [User Interface & Navigation](#8-user-interface--navigation)
9. [Business Logic & Algorithms](#9-business-logic--algorithms)
10. [Migration Guide](#10-migration-guide)

---

## 1. Executive Summary

### 1.1 What is AetherSignal?

**AetherSignal** is a comprehensive, cloud-native pharmacovigilance (PV) analytics platform that enables safety scientists to:

- **Upload and analyze safety datasets** (FAERS, Argus, Veeva, CSV, Excel, PDF, ZIP)
- **Query data using natural language** ("Show serious cases with drug aspirin and reaction headache")
- **Detect and rank drug-event signals** using traditional statistics (PRR, ROR, IC, BCPNN) and quantum-inspired algorithms
- **Monitor social media** for patient-reported adverse events (Reddit, Twitter/X)
- **Generate regulatory-ready reports** (PDF summaries, PSUR/DSUR, E2B export)
- **AI-powered safety copilot** for intelligent query assistance
- **Mechanism-of-action predictions** for biological plausibility
- **Evidence governance** with full audit trails and lineage tracking

### 1.2 Current Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Streamlit | 1.38.0 |
| **Backend** | Python | 3.12 |
| **Data Processing** | Pandas, NumPy, SciPy | 2.2.2, 1.26.4 |
| **Visualization** | Plotly | 5.22.0 |
| **Database** | Supabase (PostgreSQL) | - |
| **Authentication** | Supabase Auth | - |
| **AI/LLM** | OpenAI, Anthropic, Groq | - |
| **Quantum** | PennyLane (optional) | 0.38.0 |
| **Deployment** | Streamlit Cloud, Railway, Render | - |

### 1.3 Codebase Statistics

- **Total Lines of Code:** ~15,000+ lines
- **Python Files:** 200+ modules
- **Main Modules:** 10+ major feature areas
- **Data Sources:** 20+ integrated sources
- **UI Components:** 120+ Streamlit components

---

## 2. System Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  (app.py, pages/*.py, src/ui/*.py)                          │
│  - Landing page                                             │
│  - Quantum PV Explorer                                      │
│  - Social AE Explorer                                       │
│  - Executive Dashboard                                      │
│  - Mechanism Explorer                                       │
│  - Governance Workspace                                    │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│              Business Logic Layer                            │
│  (src/*.py - Pure Python, no framework deps)               │
│  - Query processing (nl_query_parser.py)                    │
│  - Signal detection (signal_stats.py)                       │
│  - Quantum ranking (quantum_ranking.py)                     │
│  - Schema detection (pv_schema.py)                          │
│  - Data normalization (normalization/*)                      │
│  - AI copilot (copilot/safety_copilot.py)                   │
│  - Mechanism AI (mechanism/*)                                │
│  - Report generation (reports/*)                            │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│              Data Access Layer                               │
│  - Supabase (pv_storage.py)                                 │
│  - File storage (storage/*)                                  │
│  - Cache layer (hybrid/cache.py)                            │
│  - Data sources (data_sources/*)                            │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│              Infrastructure Layer                            │
│  - Supabase PostgreSQL                                      │
│  - Supabase Auth                                            │
│  - Redis (optional, for caching)                            │
│  - External APIs (OpenFDA, PubMed, etc.)                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Key Architectural Patterns

1. **Modular Monolith**: All business logic in pure Python modules
2. **Session-Based State**: Streamlit `session_state` for temporary data
3. **Database Persistence**: Supabase for multi-tenant data storage
4. **Hybrid Processing**: Auto-selects local/server/hybrid based on dataset size
5. **Plugin Architecture**: Data sources registered via registry pattern
6. **Service Layer**: Business logic separated from UI (testable)

---

## 3. Core Modules & Features

### 3.1 Quantum PV Explorer (Primary Signal Module)

**Location:** `pages/1_Quantum_PV_Explorer.py`

**Purpose:** Main pharmacovigilance signal detection and analysis module.

#### Features Implemented:

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **File Upload** | Multi-format support (CSV, Excel, PDF, ZIP, FAERS ASCII) | `src/ui/upload_section.py` |
| **Schema Detection** | Auto-detects and maps columns to standard PV fields | `src/pv_schema.py` |
| **Data Normalization** | Converts any format to unified schema | `src/normalization/*` |
| **Natural Language Queries** | "Find signals for dupilumab 2021-2023" | `src/nl_query_parser.py` |
| **Query Interface** | ChatGPT-like conversational interface | `src/ui/query_interface.py` |
| **Signal Detection** | PRR, ROR, IC, BCPNN calculations | `src/signal_stats.py` |
| **Advanced Statistics** | Chi-square, Fisher's exact, multi-CI | `src/advanced_stats.py` |
| **Quantum Ranking** | Quantum-inspired signal re-ranking | `src/quantum_ranking.py` |
| **Subgroup Discovery** | Age, sex, country subgroup analysis | `src/subgroup_discovery.py` |
| **Time Trends** | Temporal analysis and visualization | `src/ui/results_display.py` |
| **PDF Reports** | One-click comprehensive reports | `src/pdf_report.py` |
| **Workspace Routing** | Explorer/Governance/Executive/Inspector views | `pages/1_Quantum_PV_Explorer.py` |

#### Business Logic Flow:

```
1. User uploads file → upload_section.py
2. Schema detection → pv_schema.py (fuzzy matching)
3. Data normalization → normalization/* (unified schema)
4. User queries → nl_query_parser.py (extract filters)
5. Apply filters → signal_stats.py (apply_filters)
6. Calculate signals → signal_stats.py (calculate_prr_ror)
7. Quantum ranking → quantum_ranking.py (rerank)
8. Display results → results_display.py (tabs: Overview, Signals, Trends, Cases, Report)
```

#### Key Files:

- `src/faers_loader.py` - FAERS ASCII/ZIP loader
- `src/e2b_import.py` - E2B XML import
- `src/nl_query_parser.py` - Natural language → filter dictionary
- `src/signal_stats.py` - PRR/ROR/IC/BCPNN calculations
- `src/quantum_ranking.py` - Quantum-inspired ranking
- `src/ui/query_interface.py` - Query workbench UI (2000+ lines)
- `src/ui/results_display.py` - Results visualization

---

### 3.2 Social AE Explorer

**Location:** `pages/2_Social_AE_Explorer.py`

**Purpose:** Real-time patient sentiment and AE detection from social media.

#### Features Implemented:

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Social Fetching** | Reddit, Twitter/X scraping | `src/social_ae/social_fetcher.py` |
| **Text Cleaning** | NLP preprocessing | `src/social_ae/social_cleaner.py` |
| **AE Extraction** | Named entity recognition | `src/social_ae/extraction_engine.py` |
| **ML Classification** | ML-based AE detection | `src/social_ae/ml_classifier.py` |
| **Severity Scoring** | Severity keyword detection | `src/social_ae/social_severity.py` |
| **Reaction Clustering** | Group similar reactions | `src/social_ae/reaction_clusters.py` |
| **Co-occurrence Analysis** | Reaction co-occurrence maps | `src/social_ae/reaction_cooccurrence.py` |
| **Social Intelligence** | Advanced analytics | `src/social_ae/intelligence/social_intelligence_engine.py` |
| **Storage** | Supabase persistence | `src/social_ae/social_ae_supabase.py` |
| **Scheduler** | Daily automated pulls | `src/social_ae/social_ae_scheduler.py` |

#### Business Logic Flow:

```
1. Scheduled/Manual pull → social_fetcher.py
2. Text cleaning → social_cleaner.py
3. AE extraction → extraction_engine.py (drug, reaction, symptoms)
4. ML classification → ml_classifier.py (AE vs non-AE)
5. Severity scoring → social_severity.py
6. Storage → social_ae_supabase.py (Supabase)
7. Dashboard display → social_dashboard.py
```

#### Key Files:

- `src/social_ae/social_fetcher.py` - Reddit/Twitter API clients
- `src/social_ae/extraction_engine.py` - NLP extraction
- `src/social_ae/social_dashboard.py` - Dashboard UI (1000+ lines)
- `src/social_ae/social_ae_integration.py` - FAERS + Social merging

---

### 3.3 Safety Copilot (AI Assistant)

**Location:** `src/copilot/safety_copilot.py`

**Purpose:** LLM-powered agent for answering safety questions using PV + Social + Literature data.

#### Features Implemented:

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Query Routing** | Routes queries to appropriate agents | `src/ai_intelligence/copilot/*` |
| **Signal Agent** | Signal investigation | `src/ai_intelligence/copilot/signal_agent.py` |
| **Mechanism Agent** | Mechanistic reasoning | `src/ai_intelligence/copilot/mechanism_agent.py` |
| **Label Agent** | Label intelligence | `src/ai_intelligence/copilot/label_agent.py` |
| **Risk Agent** | Risk prioritization | `src/ai_intelligence/copilot/risk_agent.py` |
| **Literature Agent** | Literature synthesis | `src/ai_intelligence/copilot/literature_agent.py` |
| **Clinical Agent** | Clinical consistency | `src/ai_intelligence/copilot/clinical_agent.py` |
| **Regulatory Agent** | Regulatory writing | `src/ai_intelligence/copilot/regulatory_agent.py` |
| **Analytics Agent** | Data analytics | `src/ai_intelligence/copilot/analytics_agent.py` |
| **Tool Integration** | Calls backend services | `src/ai_intelligence/copilot/tool_router.py` |
| **Memory** | Conversational memory | `src/ai_intelligence/copilot/memory.py` |

#### Business Logic Flow:

```
1. User query → safety_copilot.py
2. Intent detection → QueryRouter
3. Route to agent(s) → signal/mechanism/label/etc.
4. Agent calls tools → query_service, signal_service, etc.
5. Evidence synthesis → LLM combines results
6. Response generation → Structured answer
```

#### Key Files:

- `src/copilot/safety_copilot.py` - Main copilot orchestrator
- `src/ai_intelligence/copilot/*` - Individual agents
- `src/ai_intelligence/model_runtime/*` - LLM client management
- `src/ai_intelligence/cache/*` - Semantic caching

---

### 3.4 Mechanism Explorer

**Location:** `pages/mechanism_explorer.py`

**Purpose:** Biological mechanism-of-action predictions for drug-reaction pairs.

#### Features Implemented:

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Pathway Mapping** | Drug → pathways → reactions | `src/mechanism/biological_pathway_graph.py` |
| **Plausibility Scoring** | Mechanism plausibility score | `src/mechanism/mechanistic_plausibility_scorer.py` |
| **Chain Generation** | Biological chain reasoning | `src/mechanism/mechanistic_chain_generator.py` |
| **LLM Reasoning** | Narrative mechanistic explanation | `src/mechanism/llm_mechanistic_reasoner.py` |
| **GPU Batch Processing** | Fast batch computation | `src/mechanism/gpu_batch_engine.py` |
| **Caching** | Result caching | `src/mechanism/cache.py` |
| **Export** | JSON/CSV/Parquet export | `src/mechanism/mech_exporter.py` |

#### Business Logic Flow:

```
1. Drug + Reaction input → mechanism explorer
2. Embedding lookup → pathway graph
3. Pathway traversal → biological chain
4. Plausibility scoring → mechanistic_plausibility_scorer
5. LLM narrative → llm_mechanistic_reasoner
6. Display results → mechanism_explorer.py UI
```

#### Key Files:

- `src/mechanism/biological_pathway_graph.py` - Pathway knowledge graph
- `src/mechanism/mechanistic_plausibility_scorer.py` - Scoring algorithm
- `src/mechanism/llm_mechanistic_reasoner.py` - LLM narrative generation

---

### 3.5 Executive Dashboard

**Location:** `pages/99_Executive_Dashboard.py`

**Purpose:** High-level portfolio view for leadership.

#### Features Implemented:

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **KPI Tiles** | Key performance indicators | `src/executive_dashboard/visual/tiles.py` |
| **Multi-Source Trends** | FAERS + Social + Literature trends | `src/executive_dashboard/visual/trends.py` |
| **Signal Ranking** | Top signals across portfolio | `src/executive_dashboard/visual/tables.py` |
| **Risk Matrix** | Severity vs frequency matrix | `src/executive_dashboard/visual/risk_matrix.py` |
| **Novelty Panel** | Emerging signals | `src/executive_dashboard/visual/novelty.py` |
| **Geographic Heatmap** | Country-level analysis | `src/executive_dashboard/visual/geo.py` |
| **AI Narrative** | Executive summary generation | `src/executive_dashboard/narrative_ai.py` |
| **Data Aggregation** | Multi-source data fusion | `src/executive_dashboard/aggregator.py` |

#### Business Logic Flow:

```
1. Load unified data → load_unified_ae_data()
2. Aggregate across sources → ExecutiveAggregator
3. Compute KPIs → calculate_kpis()
4. Generate visualizations → visual/* components
5. AI narrative → narrative_ai.py
6. Display dashboard → dashboard.py
```

#### Key Files:

- `src/executive_dashboard/dashboard.py` - Main dashboard orchestrator
- `src/executive_dashboard/aggregator.py` - Data aggregation logic
- `src/executive_dashboard/visual/*` - Visualization components

---

### 3.6 Evidence Governance & Audit

**Location:** `src/evidence_governance/*`

**Purpose:** Full audit trail, lineage tracking, and regulatory compliance.

#### Features Implemented:

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Lineage Tracking** | Data transformation history | `src/evidence_governance/lineage_tracker.py` |
| **Provenance** | Source attribution | `src/evidence_governance/provenance_tracker.py` |
| **Quality Scoring** | Data quality metrics | `src/evidence_governance/quality_scorer.py` |
| **Fingerprinting** | Data fingerprinting | `src/evidence_governance/fingerprints.py` |
| **Fusion Engine** | Multi-source evidence fusion | `src/evidence_governance/fusion_engine.py` |
| **Governance Engine** | Master orchestrator | `src/evidence_governance/governance_engine.py` |

#### Business Logic Flow:

```
1. Record ingestion → governance_engine.process_record()
2. Generate fingerprint → fingerprints.generate_fingerprint()
3. Record lineage → lineage_tracker.record()
4. Record provenance → provenance_tracker.record_provenance()
5. Quality scoring → quality_scorer.score()
6. Store metadata → database
```

#### Key Files:

- `src/evidence_governance/governance_engine.py` - Master orchestrator
- `src/evidence_governance/lineage_tracker.py` - Lineage tracking
- `src/evidence_governance/provenance_tracker.py` - Provenance tracking

---

### 3.7 PSUR/DSUR Auto-Writer

**Location:** `src/reports/*`

**Purpose:** Automated regulatory report generation.

#### Features Implemented:

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **PSUR Generator** | Periodic Safety Update Report | `src/reports/psur_generator.py` |
| **DSUR Generator** | Development Safety Update Report | `src/reports/psur_generator.py` |
| **Signal Report** | Signal detection reports | `src/reports/psur_generator.py` |
| **AI Narrative Writer** | LLM-powered narrative generation | `src/reports/ai_narrative_writer.py` |
| **Context Builder** | PSUR context assembly | `src/reports/psur_context.py` |

#### Business Logic Flow:

```
1. User triggers report → psur_generator.generate()
2. Pull data → FAERS + Social + Literature
3. Compute statistics → signal_stats, trends
4. Build context → psur_context.py
5. Generate sections → template + LLM
6. Export DOCX/PDF → reportlab/python-docx
```

#### Key Files:

- `src/reports/psur_generator.py` - Main generator
- `src/reports/ai_narrative_writer.py` - LLM narrative
- `src/reports/psur_context.py` - Context assembly

---

### 3.8 Hybrid Processing Engine

**Location:** `src/hybrid/*`, `src/engine/*`

**Purpose:** Intelligently routes processing between browser (local) and server.

#### Features Implemented:

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Browser Detection** | Detects WASM/Pyodide support | `src/engine/browser_capability_detector.py` |
| **Dataset Profiling** | Analyzes dataset size/complexity | `src/engine/dataset_profiler.py` |
| **Mode Selection** | Auto-selects local/server/hybrid | `src/engine/hybrid_mode_manager.py` |
| **Local Engine** | Browser-based processing | `src/local_engine/*` |
| **Server Engine** | Server-side processing | `src/signal_stats.py` (existing) |
| **Hybrid Router** | Splits work between local/server | `src/hybrid/router.py` |
| **Cache Layer** | Result caching | `src/hybrid/cache.py` |

#### Business Logic Flow:

```
1. Dataset uploaded → dataset_profiler.profile()
2. Browser detection → browser_capability_detector.detect()
3. Mode decision → hybrid_mode_manager.get_mode()
   - Small dataset + WASM → local
   - Large dataset → server
   - Medium dataset → hybrid
4. Route query → hybrid/router.py
5. Process → local_engine or server
6. Cache results → hybrid/cache.py
```

#### Key Files:

- `src/hybrid/hybrid_master_engine.py` - Master coordinator
- `src/engine/hybrid_mode_manager.py` - Mode selection logic
- `src/local_engine/*` - Browser-based processing
- `src/pyodide/*` - Pyodide/WASM integration

---

## 4. Data Processing Pipeline

### 4.1 Upload & Ingestion

**Entry Point:** `src/ui/upload_section.py`

**Supported Formats:**
- CSV files
- Excel (.xlsx, .xls)
- FAERS ASCII (ZIP archives)
- E2B XML (Argus/EudraVigilance)
- PDF files (table extraction)
- Text files

**Process:**
1. File upload → Streamlit file uploader
2. Format detection → `src/faers_loader.py` or `src/e2b_import.py`
3. Schema detection → `src/pv_schema.py` (fuzzy matching)
4. Data normalization → `src/normalization/*`
5. Store in session → `st.session_state["normalized_data"]`

### 4.2 Schema Detection

**Location:** `src/pv_schema.py`

**Algorithm:**
1. Exact match → Check if column name matches standard field
2. Fuzzy match → Use `rapidfuzz` for similarity scoring
3. Manual mapping → User can override in UI
4. Validation → Ensure required fields present

**Standard Fields:**
- `case_id`, `drug_name`, `reaction`, `age`, `sex`, `country`
- `seriousness`, `onset_date`, `report_date`, `outcome`
- `dose_amount`, `dose_unit`, `route`, `indication`

### 4.3 Data Normalization

**Location:** `src/normalization/*`

**Process:**
1. Column mapping → Apply schema mapping
2. Data type conversion → Dates, numbers, strings
3. Text normalization → `normalize_text()` (lowercase, strip)
4. Drug normalization → `drug_name_normalization.py`
5. Reaction mapping → MedDRA PT mapping (if available)
6. Age extraction → `extract_age()` from various formats

### 4.4 Query Processing

**Location:** `src/nl_query_parser.py`

**Algorithm:**
1. Negation detection → "no X", "without X", "excluding X"
2. Concept detection → "seniors", "pediatrics", "recently"
3. Entity extraction → Drug names, reactions, dates, ages
4. Filter construction → Build filter dictionary
5. LLM fallback → If regex fails, use LLM interpreter

**Filter Dictionary Structure:**
```python
{
    "drug": ["aspirin", "ibuprofen"],
    "reaction": ["headache", "nausea"],
    "reaction_logic": "OR",  # or "AND"
    "exclude_reaction": ["fever"],
    "age_min": 18,
    "age_max": 65,
    "sex": "F",
    "country": "United States",
    "serious": True,
    "date_from": "2021-01-01",
    "date_to": "2023-12-31"
}
```

### 4.5 Signal Detection

**Location:** `src/signal_stats.py`

**Statistics Calculated:**
- **PRR** (Proportional Reporting Ratio) with 95% CI
- **ROR** (Reporting Odds Ratio) with 95% CI
- **IC** (Information Component) with 95% CI
- **BCPNN** (Bayesian Confidence Propagation Neural Network)
- **Chi-square test** (p-value)
- **Fisher's exact test** (p-value)

**Algorithm:**
1. Apply filters → `apply_filters()`
2. Build 2x2 contingency table:
   ```
   | Drug + Reaction | Drug, No Reaction |
   | No Drug, Reaction | No Drug, No Reaction |
   ```
3. Calculate statistics → PRR, ROR, IC, BCPNN
4. Compute confidence intervals → Log-normal approximation
5. Return results → Dictionary with all metrics

### 4.6 Quantum Ranking

**Location:** `src/quantum_ranking.py`

**Algorithm:**
1. Extract features → Rarity, seriousness, recency
2. Calculate quantum score → Weighted combination
3. Quantum-inspired effects → Tunneling, superposition
4. Re-rank signals → Sort by quantum_score
5. Explainability → Feature decomposition

**Features:**
- **Rarity**: 1 - (count / total_cases)
- **Seriousness**: Based on seriousness flags
- **Recency**: More recent cases weighted higher
- **Novelty**: New drug-reaction combinations

---

### 4.7 Drug Watchlist - Daily Signal Monitor

**Location:** `src/watchlist_tab.py`

**Purpose:** Automated Daily Surveillance System - Monitor multiple drugs simultaneously and identify emerging safety signals ranked by quantum-inspired algorithms.

**Core Function:** Drug Watchlist serves as the "Daily Safety Radar" for safety teams, automatically scanning portfolio drugs across all case data to detect newly emerging safety signals and rank them by urgency.

**Features:**
- **Multi-Drug Monitoring**: Paste list of portfolio drugs (one per line)
- **Signal Detection**: Identifies drug-event combinations with minimum 5 cases
- **Quantum Ranking**: Ranks signals by composite score favoring rare, serious, and recent signals
- **Classical Comparison**: Shows both quantum rank and classical rank (by case count)
- **PRR/ROR Statistics**: Calculates disproportionality measures (Proportional Reporting Ratio, Reporting Odds Ratio)
- **Top 50 Signals**: Displays top-ranked signals for focused investigation
- **Export**: Download full report as CSV with all statistics

**Algorithm:**
1. User inputs drug list (one per line)
2. For each drug, scan all cases and find drug-event combinations
3. Filter combinations with minimum case count (default: 5)
4. Calculate PRR/ROR for each combination
5. Apply quantum ranking algorithm
6. Display top 50 signals ranked by quantum score

**Quantum Score (0.0-1.0) - Core Innovation:**

Composite anomaly score informed by:

**Base Components (Weighted):**
- **Rarity (40%)**: Rare events are more interesting than common ones
  - Formula: 1 - (count / total_cases)
  - Higher rarity = higher score
- **Seriousness (35%)**: Serious adverse events get higher priority
  - Based on seriousness flags, outcomes (death, hospitalization, disability)
- **Recency (20%)**: Recent cases are more relevant
  - Cases from last year get full weight (1.0 - 0.5)
  - Older cases get diminishing weight
- **Count (5%)**: Minimum threshold for statistical relevance
  - Normalized: min(1.0, count / 10.0)

**Quantum-Inspired Enhancements:**
- **Bayesian priors**: Incorporates prior knowledge about signal patterns
- **Disproportionality shifts**: Detects unusual reporting patterns
- **Novelty detection**: Identifies new, unexpected signals
- **Temporal spikes**: Catches sudden increases in reporting
- **Cross-feature correlations**: Considers interactions between multiple factors
- **Local Outlier Factor**: Identifies signals that deviate from local patterns
- **Isolation models**: Detects anomalous signals through isolation
- **Quantum-inspired ranking**: Based on eigenvector influence and superposition principles

**Non-linear Interaction Boosts:**
- Rare + Serious = Critical signals (+0.15 boost)
- Rare + Recent = Emerging signals (+0.10 boost)
- Serious + Recent = Urgent signals (+0.10 boost)
- All three = Highest priority signals (+0.20 boost)
- Quantum tunneling: Small boost (+0.05 each) for signals "close" to thresholds

**Quantum Score Interpretation:**
- **0.70 - 1.0**: Very high priority (investigate immediately)
- **0.55 - 0.70**: Elevated priority (investigate soon) - Score near 0.55 is already elevated
- **0.40 - 0.55**: Moderate priority (monitor trends)
- **0.30 - 0.40**: Lower priority (may be expected)
- **0.0 - 0.30**: Low priority (likely expected)

**Classical Statistical Measures:**

**PRR (Proportional Reporting Ratio):**
- Formula: PRR = (a / (a+b)) / (c / (c+d))
- Interpretation: PRR > 2 suggests potential signal
- Standard disproportionality measure used in pharmacovigilance

**ROR (Reporting Odds Ratio):**
- Formula: ROR = (a × d) / (b × c)
- Interpretation: ROR > 2 suggests potential signal
- Alternative disproportionality measure

**EBGM (Empirical Bayes Geometric Mean):** (Available in full report)
- Bayesian shrinkage estimator for sparse data
- EBGM > 2 suggests signal, EB05 > 2 is stronger
- Used by FDA in FAERS analysis

**IC (Information Component):** (Available in full report)
- Formula: IC = log2((a + λ) / expected)
- Interpretation: IC > 0 = more reports than expected, IC > 2 = strong signal
- Used in WHO Vigibase with credibility intervals (IC025, IC975)

**BCPNN (Bayesian Confidence Propagation Neural Network):** (Available in full report)
- Similar to IC with Bayesian priors
- Robust for rare events

**Chi-squared Test:** (Available in full report)
- Tests independence between drug and reaction
- p-value < 0.05 = significant association

**Fisher's Exact Test:** (Available in full report)
- Exact probability test for 2x2 tables
- Better for small datasets than chi-squared

**Output Columns:**
- `source_drug`: Drug name from watchlist
- `reaction`: Adverse event/reaction reported (MedDRA PT or combinations)
- `count`: Number of cases with this drug-reaction combination
- `quantum_score`: Composite priority score (0.0-1.0) - higher = more urgent
- `quantum_rank`: Ranking by quantum score (1 = highest priority, most concerning emerging signal)
- `classical_rank`: Ranking by case count (1 = most cases, traditional frequency-based ranking)
- `prr`: Proportional Reporting Ratio (if calculated)
- `ror`: Reporting Odds Ratio (if calculated)

**Ranking Comparison Logic:**

Differences between Quantum Rank and Classical Rank are telling:

| If quantum rank is high but classical rank is low… | Meaning                                            |
| -------------------------------------------------- | -------------------------------------------------- |
| Risk is newly emerging                             | Classical methods are slow to detect early signals |
| Rare-event signal                                  | Classical methods underperform on sparse datasets  |
| Complex correlation pattern                        | Quantum model captures nonlinear relationships     |

**Use Cases:**
- **Daily signal monitoring** for drug portfolio
- **Prioritize safety review meetings** - safety leads review top-ranked signals
- **Identify emerging safety trends early** - catch rare but serious AEs before classical methods
- **Triage risks before formal signal detection** - catch issues before regulators ask
- **Generate evidence for PSUR/PBRER reports** - Section 15 (Significant safety findings)
- **Replace manual Excel filtering** and slow FAERS searches

**Real-World Safety Team Workflow:**
1. Safety leads review top-ranked quantum signals daily
2. Identify newly emerging reactions and mismatches between quantum/classical
3. Decide which signals analysts should review today
4. Determine if follow-up case evaluation or SME review needed
5. Escalate signals with quantum_score > 0.70 immediately

**Integration:**
- Tab in Query Interface (`src/ui/query_interface.py`)
- Uses `signal_stats.py` for drug-event combinations and PRR/ROR calculation
- Uses `quantum_ranking.py` for signal ranking
- Uses `advanced_stats.py` for EBGM, IC, BCPNN, Chi-squared, Fisher's exact test
- Default drugs populated from uploaded dataset
- Download button provides full CSV report with all statistics

**Regulatory Considerations:**
- Quantum ranking helps prioritize, but classical metrics provide validation
- Use both quantum and classical for comprehensive analysis
- Document methodology in regulatory submissions
- Signals with quantum_score > 0.55 should be included in PSUR/PBRER

---

## 5. AI & Intelligence Layer

### 5.1 LLM Integration

**Location:** `src/local_llm/*`, `src/ai/*`

**Providers Supported:**
- OpenAI (GPT-4, GPT-4o-mini)
- Anthropic (Claude)
- Groq (LLaMA-3 70B)
- HuggingFace (BioGPT)

**Architecture:**
- **Model Router** → `src/local_llm/model_router.py` (selects best model)
- **Fallback Manager** → `src/local_llm/fallback_manager.py` (handles failures)
- **Caching Layer** → `src/local_llm/caching_layer.py` (semantic caching)
- **Vector Store** → `src/local_llm/vector_store.py` (embedding cache)

### 5.2 AI Agents

**Location:** `src/ai_intelligence/copilot/*`

**Agents:**
1. **Signal Agent** → Signal investigation
2. **Mechanism Agent** → Mechanistic reasoning
3. **Label Agent** → Label intelligence
4. **Risk Agent** → Risk prioritization
5. **Literature Agent** → Literature synthesis
6. **Clinical Agent** → Clinical consistency
7. **Regulatory Agent** → Regulatory writing
8. **Analytics Agent** → Data analytics

### 5.3 Prompt Optimization

**Location:** `src/ai_intelligence/prompt_optimizer/*`

**Features:**
- Prompt templates
- Context injection
- Few-shot examples
- Chain-of-thought reasoning

---

## 6. Data Sources & Integration

### 6.1 Data Source Registry

**Location:** `src/data_sources/registry.py`

**Architecture:**
- **Base Class** → `src/data_sources/base.py` (SourceClientBase)
- **Registry** → Auto-discovers and instantiates sources
- **Config** → `data_source_config.yaml` (YAML configuration)
- **Safe Executor** → `src/data_sources/safe_executor.py` (retry logic)

### 6.2 Free Sources

| Source | Description | Implementation |
|--------|-------------|----------------|
| **OpenFDA** | FAERS data via API | `src/data_sources/sources/openfda.py` |
| **PubMed** | Medical literature | `src/data_sources/sources/pubmed.py` |
| **ClinicalTrials.gov** | Clinical trial data | `src/data_sources/sources/clinicaltrials.py` |
| **DailyMed** | Drug labels | `src/data_sources/sources/dailymed.py` |
| **MedSafetyAlerts** | RSS feed alerts | `src/data_sources/sources/medsafety_alerts.py` |
| **Reddit** | Social media (via social_ae) | `src/social_ae/social_fetcher.py` |
| **Twitter/X** | Social media (via social_ae) | `src/social_ae/social_fetcher.py` |

### 6.3 Paid Sources (Placeholder)

| Source | Description | Status |
|--------|-------------|--------|
| **HumanAPI** | Patient data | Placeholder |
| **Metriport** | Health data | Placeholder |
| **DrugBank** | Drug database | Placeholder |
| **VigiBase** | WHO database | Placeholder |
| **Epic FHIR** | EHR integration | Placeholder |
| **Cerner FHIR** | EHR integration | Placeholder |
| **OHDSI** | Observational data | Placeholder |

### 6.4 Unified Integration

**Location:** `src/data_sources/unified_integration.py`

**Purpose:** Combines all sources into unified schema.

**Process:**
1. Fetch from all enabled sources
2. Normalize to unified schema
3. Deduplicate (cross-source)
4. Store in `public_ae_data` table

---

## 7. Storage & Persistence

### 7.1 Session State (Temporary)

**Location:** Streamlit `st.session_state`

**Stored:**
- Uploaded data (`data`, `normalized_data`)
- Query results (`last_filters`, `last_query_text`)
- UI state (`active_workspace`, `processing_mode`)
- Chat history (`chat_history`)
- Memory state (`memory_state`)

### 7.2 Database Architecture & Recommendations

#### 7.2.1 Current Setup

**Location:** Supabase PostgreSQL

**Complete Database Inventory:** See `DATABASE_INVENTORY_AND_CURRENT_STATE.md` for full details.

**Active Tables (Currently Used):**
- ✅ `user_profiles` - User information (used)
- ✅ `pv_cases` - PV case data (multi-tenant, used)
- ✅ `tenants` - Tenant registry (used)
- ✅ `user_tenants` - User-tenant mapping (used)
- ✅ `user_data_summary` - VIEW (aggregated stats per user/org)

**Tables That Exist But Are NOT Used:**
- ❌ `activity_logs` - Table exists but NOT WRITTEN TO (logging writes to file only)
- ⚠️ `saved_queries` - Table exists but NOT WRITTEN TO (stored in session only)
- ⚠️ `query_history` - Table exists but NOT WRITTEN TO (stored in session only)

**Other Tables (Usage Unknown):**
- ❓ `org_profile_config` - Organization configuration
- ❓ `ae_events`, `drugs`, `reactions` - Unified AE schema tables
- ❓ `public_ae_data` - Public data sources

**Missing Critical Tables:**
- ❌ `file_upload_history` - Track individual file uploads (needed for duplicate detection)
- ❌ `pre_calculated_stats` - Cache common query results (needed for performance)
- ❌ `background_jobs` - Job queue for background processing
- ❌ `query_learning` - Learn from user queries for auto-precomputation

**Critical Issues:**
1. **Activity Logs Not Persisted:** `activity_logs` table exists but audit logging writes to file only (`analytics/audit_log.jsonl`) - compliance concern
2. **Query History Lost:** Query history stored in session state only, lost on logout
3. **No File Tracking:** Cannot distinguish individual file uploads (only aggregates by date/source)
4. **Missing Indexes:** Dataset listing takes 5-10 seconds (needs composite indexes)

**Current Schema:**
```sql
pv_cases (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    organization TEXT NOT NULL,
    case_id TEXT,
    drug_name TEXT,
    reaction TEXT,
    age NUMERIC,
    sex TEXT,
    country TEXT,
    serious BOOLEAN,
    onset_date DATE,
    report_date DATE,
    source TEXT,
    raw_data JSONB,
    created_at TIMESTAMP
)
```

**Storage Module:** `src/pv_storage.py`

**Functions:**
- `store_pv_data()` - Store uploaded data
- `load_pv_data()` - Load user data
- `get_user_data_stats()` - Statistics
- `list_available_datasets()` - Dataset listing
- `delete_user_data()` - Data deletion

#### 7.2.2 Data Growth Projections

**Expected Growth:**
- **PV Cases**: 1M+ cases per organization (FAERS alone has 20M+ cases)
- **Social AE Posts**: 100K+ posts per month (Reddit, Twitter)
- **Public Data**: 10M+ records from OpenFDA, PubMed, etc.
- **Total**: 50M+ records within 1-2 years

**Query Patterns:**
- **Transactional**: User uploads, real-time queries (low latency)
- **Analytical**: Signal detection, PRR/ROR calculations (complex aggregations)
- **Time-Series**: Trend analysis, temporal queries
- **Multi-Tenant**: RLS policies, organization isolation

#### 7.2.3 Database Options Analysis

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **PostgreSQL (Current)** | ✅ ACID transactions<br>✅ Complex queries<br>✅ RLS support<br>✅ JSONB support | ❌ Slower for analytics<br>❌ Limited time-series<br>❌ Scaling challenges | Transactional data, user data, real-time queries |
| **TimescaleDB** | ✅ PostgreSQL extension<br>✅ Time-series optimized<br>✅ Automatic partitioning<br>✅ Same SQL interface | ⚠️ Requires migration<br>⚠️ Still PostgreSQL limits | Time-series data, trends, temporal analytics |
| **ClickHouse** | ✅ Columnar storage<br>✅ 10-100x faster analytics<br>✅ Excellent compression<br>✅ Handles billions of rows | ❌ No ACID transactions<br>❌ Separate system<br>❌ Learning curve | Analytics, signal detection, aggregations |
| **BigQuery** | ✅ Serverless<br>✅ Auto-scaling<br>✅ Excellent for analytics<br>✅ Pay-per-query | ❌ Vendor lock-in<br>❌ Cost at scale<br>❌ Latency for real-time | Cloud-native, analytics workloads |
| **Snowflake** | ✅ Excellent scaling<br>✅ Good analytics<br>✅ Multi-cloud | ❌ Expensive<br>❌ Overkill for start | Enterprise, large-scale analytics |
| **Hybrid: PostgreSQL + ClickHouse** | ✅ Best of both worlds<br>✅ PostgreSQL for transactions<br>✅ ClickHouse for analytics<br>✅ Optimal performance | ⚠️ More complex<br>⚠️ Data sync needed | **RECOMMENDED** |

#### 7.2.4 **RECOMMENDED: Three-Layer Architecture**

**Understanding the Three Backend Decisions:**

1. **Backend Framework/API Layer** → How clients talk to your system
2. **Primary Database(s)** → Where you store transactional vs analytical data
3. **Processing + Storage Architecture** → How you ingest and analyze large datasets

---

**Phase 1: MVP+ Architecture (Now - 6 months)**

**Framework:** FastAPI (Python)
- Keep all existing Python logic (no rewrite)
- Async I/O for file uploads, DB queries, LLM calls
- Auto-generated OpenAPI/Swagger docs
- Works with Postgres, Redis, Celery/RQ

**Transactional DB:** Supabase PostgreSQL
- User authentication & profiles
- Organization data & roles
- Dataset metadata (name, owner, size, schema, status)
- Saved queries, dashboards, workflows
- Audit logs, billing metadata, feature flags
- Multi-tenant RLS (security)

**Case-Level Storage:** Parquet + DuckDB/Polars
- Raw uploads → Object storage (S3, Supabase Storage, GCS)
- Normalized data → Parquet files partitioned by:
  - Product/organization
  - Year/month
  - Source (FAERS, E2B, Social AE)
- Analytics queries → DuckDB (server-side) or Polars
- Results exposed via FastAPI endpoints

**Architecture:**
```
┌─────────────────────────────────────────┐
│     FastAPI Backend                     │
│  - REST API endpoints                   │
│  - Authentication (Supabase Auth)      │
│  - Request validation (Pydantic)       │
└─────────────────────────────────────────┘
              ↕
┌─────────────────────────────────────────┐
│     PostgreSQL (Supabase)               │
│  - Users, orgs, configs                 │
│  - Dataset metadata                     │
│  - Saved queries, dashboards            │
│  - Audit logs                           │
└─────────────────────────────────────────┘
              ↕
┌─────────────────────────────────────────┐
│     Object Storage (S3/Supabase)       │
│  - Raw uploaded files                   │
│  - Parquet files (partitioned)          │
│  - Organized by: org/product/date       │
└─────────────────────────────────────────┘
              ↕
┌─────────────────────────────────────────┐
│     DuckDB/Polars (Analytics)           │
│  - Scan Parquet files                   │
│  - Signal detection queries             │
│  - PRR/ROR calculations                 │
│  - Fast aggregations                    │
└─────────────────────────────────────────┘
```

**Data Flow:**
1. User uploads file → FastAPI endpoint
2. Normalize data → Write Parquet files to object storage
3. Store metadata → PostgreSQL (dataset info, schema)
4. Analytics queries → DuckDB scans Parquet → FastAPI returns results
5. Real-time queries → PostgreSQL (metadata, small datasets)

**Pros:**
- ✅ Very cheap storage (object storage + Parquet compression)
- ✅ Great performance for analytical queries on large files
- ✅ Minimal infrastructure
- ✅ Reuses existing Python code
- ✅ No database scaling headaches initially

**Cons:**
- ⚠️ Harder for cross-dataset, multi-tenant concurrent queries at scale
- ⚠️ Not ideal for real-time dashboards with many concurrent users
- ⚠️ Requires ETL pipeline to write Parquet files

**Implementation:**
```python
# src/storage/parquet_storage.py
import duckdb
import pyarrow.parquet as pq
from pathlib import Path

class ParquetAnalytics:
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.conn = duckdb.connect()
    
    def store_dataset(self, df: pd.DataFrame, org_id: str, dataset_id: str):
        """Store normalized data as Parquet"""
        partition_path = self.storage_path / org_id / dataset_id
        partition_path.mkdir(parents=True, exist_ok=True)
        
        # Write Parquet file
        parquet_file = partition_path / f"{dataset_id}.parquet"
        df.to_parquet(parquet_file, compression='snappy', index=False)
        
        return str(parquet_file)
    
    def query_signals(self, org_id: str, filters: dict):
        """Query Parquet files using DuckDB"""
        # Find relevant Parquet files
        parquet_files = list((self.storage_path / org_id).glob("**/*.parquet"))
        
        # DuckDB query
        query = f"""
        SELECT 
            drug_name,
            reaction,
            COUNT(*) as case_count,
            COUNT(*) FILTER (WHERE serious = true) as serious_count
        FROM read_parquet({parquet_files})
        WHERE drug_name = '{filters.get("drug")}'
        GROUP BY drug_name, reaction
        """
        
        result = self.conn.execute(query).df()
        return result
```

---

**Phase 2: Scale-Up Architecture (6-12 months)**

**When to Migrate:**
- Parquet queries become slow (> 5 seconds)
- Need cross-dataset queries
- Many concurrent analytical queries
- Data volume > 100M rows

**Add ClickHouse:**
- Keep PostgreSQL for transactional data
- Move heavy case tables → ClickHouse
- Parquet still as raw layer (can ingest into ClickHouse)
- Same FastAPI API, different storage backend

**Architecture:**
```
┌─────────────────────────────────────────┐
│     FastAPI Backend                     │
│  - REST API endpoints                   │
│  - Routes to Postgres OR ClickHouse     │
└─────────────────────────────────────────┘
              ↕                    ↕
┌─────────────────────────┐  ┌─────────────────────────┐
│  PostgreSQL (Supabase) │  │  ClickHouse (Analytics) │
│  - Users, metadata      │  │  - Case-level data      │
│  - Configs             │  │  - Signal detection     │
│  - Saved queries       │  │  - PRR/ROR calculations  │
└─────────────────────────┘  │  - Trend analysis       │
              ↕              └─────────────────────────┘
┌─────────────────────────────────────────┐
│     Object Storage (S3/Supabase)       │
│  - Raw files                            │
│  - Parquet (backup/archive)            │
└─────────────────────────────────────────┘
```

**Data Flow:**
1. User uploads → FastAPI → Normalize → Write Parquet
2. Background ETL → Ingest Parquet into ClickHouse (async)
3. Analytics queries → ClickHouse (fast, 10-100x faster)
4. Metadata queries → PostgreSQL (real-time)
5. Parquet remains as backup/archive layer

**Migration Strategy:**
- Keep Parquet + DuckDB for new/small datasets
- Migrate large datasets to ClickHouse gradually
- Dual-write during migration period
- Switch query routing based on dataset size

**Implementation:**
```python
# src/storage/clickhouse_client.py
class ClickHouseAnalytics:
    def sync_from_postgres(self):
        """Sync data from PostgreSQL to ClickHouse"""
        # Use Debezium, Kafka, or direct ETL
        pass
    
    def query_signals(self, filters):
        """Fast signal detection queries"""
        # 10-100x faster than PostgreSQL
        pass
```

#### 7.2.5 Implementation Details

**Parquet Storage Structure:**
```
storage/
├── {organization_id}/
│   ├── {dataset_id}/
│   │   ├── 2025/
│   │   │   ├── 01/  # January
│   │   │   │   ├── faers.parquet
│   │   │   │   └── social_ae.parquet
│   │   │   └── 02/  # February
│   │   └── metadata.json  # Schema, upload date, etc.
```

**DuckDB Query Example:**
```python
# Fast signal detection on Parquet files
conn = duckdb.connect()
result = conn.execute("""
    SELECT 
        drug_name,
        reaction,
        COUNT(*) as cases,
        COUNT(*) FILTER (WHERE serious = true) as serious_cases
    FROM read_parquet('storage/org_123/dataset_456/2025/01/*.parquet')
    WHERE drug_name = 'aspirin'
    GROUP BY drug_name, reaction
    ORDER BY cases DESC
    LIMIT 100
""").df()
```

**ClickHouse Schema (Phase 2):**
```sql
CREATE TABLE pv_cases_analytics (
    id UUID,
    user_id UUID,
    organization String,
    case_id String,
    drug_name String,
    reaction String,
    age Float32,
    sex String,
    country String,
    serious UInt8,
    onset_date Date,
    report_date Date,
    source String,
    created_at DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (organization, drug_name, reaction, created_at);
```

#### 7.2.6 Immediate Optimizations (Do Now)

**1. Add Proper Indexes:**

**Current Indexes (Good):**
- Basic indexes: user_id, organization, drug_name, reaction, case_id, source, created_at
- Composite: user+drug, user+reaction

**Missing Critical Indexes (Add Immediately):**
```sql
-- 1. Composite index for common drug-event queries (MOST IMPORTANT)
CREATE INDEX IF NOT EXISTS idx_pv_cases_user_drug_reaction 
    ON pv_cases(user_id, drug_name, reaction) 
    WHERE drug_name IS NOT NULL AND reaction IS NOT NULL;

-- 2. Date range index for dataset listing (10-20x faster)
CREATE INDEX IF NOT EXISTS idx_pv_cases_created_at_org 
    ON pv_cases(organization, created_at DESC);

-- 3. Event date index for trend analysis
CREATE INDEX IF NOT EXISTS idx_pv_cases_event_date 
    ON pv_cases(event_date) 
    WHERE event_date IS NOT NULL;

-- 4. Seriousness/outcome index for filtering
CREATE INDEX IF NOT EXISTS idx_pv_cases_serious_outcome 
    ON pv_cases(serious, outcome) 
    WHERE serious = TRUE OR outcome LIKE '%Death%';

-- 5. Partial index for serious cases
CREATE INDEX IF NOT EXISTS idx_pv_cases_serious 
    ON pv_cases(user_id, drug_name, reaction) 
    WHERE serious = true;

-- 6. GIN index for JSONB queries (if raw_data is queried)
CREATE INDEX IF NOT EXISTS idx_pv_cases_raw_data_gin 
    ON pv_cases USING GIN (raw_data);
```

**Performance Impact:**
- Dataset listing: Currently 5-10 seconds → <500ms with proper indexes (10-20x faster)
- Common queries: Currently 500ms-2s → 100-500ms with composite index (2-4x faster)

**2. Implement Table Partitioning:**
```sql
-- Partition by month (for large tables)
CREATE TABLE pv_cases (
    ...
) PARTITION BY RANGE (created_at);

-- Auto-create partitions
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
BEGIN
    -- Create next month's partition
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS pv_cases_%s 
        PARTITION OF pv_cases
        FOR VALUES FROM (%L) TO (%L)',
        to_char(CURRENT_DATE + interval '1 month', 'YYYY_MM'),
        date_trunc('month', CURRENT_DATE + interval '1 month'),
        date_trunc('month', CURRENT_DATE + interval '2 months')
    );
END;
$$ LANGUAGE plpgsql;
```

**3. Add Materialized Views:**
```sql
-- Pre-compute signal statistics
CREATE MATERIALIZED VIEW mv_signal_stats AS
SELECT 
    user_id,
    organization,
    drug_name,
    reaction,
    COUNT(*) as total_cases,
    COUNT(*) FILTER (WHERE serious = true) as serious_cases,
    AVG(age) as avg_age,
    COUNT(DISTINCT country) as countries
FROM pv_cases
WHERE drug_name IS NOT NULL AND reaction IS NOT NULL
GROUP BY user_id, organization, drug_name, reaction;

-- Refresh every hour
CREATE INDEX ON mv_signal_stats(user_id, drug_name, reaction);
```

**4. Connection Pooling:**
```python
# Use PgBouncer or Supabase connection pooling
# Supabase already provides this, but ensure proper pool size
```

**5. Query Optimization:**
```python
# Use EXPLAIN ANALYZE to identify slow queries
# Add LIMIT clauses where appropriate
# Use pagination for large result sets
# Cache frequently accessed data
```

#### 7.2.7 Migration Path

**Month 1-3: Implement Parquet + DuckDB**
- Set up object storage (S3 or Supabase Storage)
- Implement Parquet writer (normalize → Parquet)
- Add DuckDB query layer
- Migrate existing data to Parquet
- Update FastAPI endpoints to use DuckDB

**Month 4-6: Optimize & Monitor**
- Optimize Parquet partitioning strategy
- Add caching layer (Redis)
- Monitor query performance
- Benchmark against PostgreSQL

**Month 7-12: Evaluate ClickHouse (if needed)**
- Set up ClickHouse instance (managed or self-hosted)
- Implement ETL pipeline (Parquet → ClickHouse)
- Migrate analytical queries gradually
- Keep Parquet as backup/archive
- Keep PostgreSQL for transactional

#### 7.2.8 Cost Considerations

| Solution | Monthly Cost (Estimate) | Notes |
|---------|------------------------|-------|
| **Phase 1: Parquet + DuckDB** | | |
| Supabase Pro | $25/month | Up to 8GB database |
| S3/Supabase Storage | $0.023/GB | Very cheap for Parquet |
| DuckDB | $0 | Open source, runs in-process |
| **Total Phase 1** | **~$25-50/month** | Very cost-effective |
| **Phase 2: ClickHouse** | | |
| Supabase Team | $599/month | Better PostgreSQL performance |
| ClickHouse Cloud | $200-500/month | Depends on data volume |
| S3 Storage | $0.023/GB | Parquet backup/archive |
| **Total Phase 2** | **~$800-1100/month** | When you need scale |
| **Self-Hosted Option** | | |
| VPS (ClickHouse) | $50-200/month | More management overhead |

**Recommendation:**
- Start with Supabase Pro ($25/month)
- Upgrade to Team when needed ($599/month)
- Add ClickHouse when analytics queries slow down ($200-500/month)
- Total: ~$800-1100/month at scale

#### 7.2.9 Final Recommendation

**✅ RECOMMENDED: Three-Layer Architecture**

**Phase 1 (Now - 6 months): Parquet + DuckDB**
- **Backend Framework**: FastAPI (Python)
- **Transactional DB**: Supabase PostgreSQL (users, metadata, configs)
- **Case Storage**: Parquet files in object storage (S3/Supabase Storage)
- **Analytics Engine**: DuckDB/Polars (scans Parquet files)
- **Workers**: RQ/Celery for heavy jobs (file ingest, PSUR generation)
- **Cache**: Redis (optional but helpful)

**Why This Works:**
- ✅ Very cheap storage (object storage + Parquet compression)
- ✅ Excellent performance for analytical queries
- ✅ Minimal infrastructure (no separate database to manage)
- ✅ Reuses all existing Python code
- ✅ Easy to scale storage (just add more Parquet files)

**Phase 2 (6-12 months): Add ClickHouse**
- Keep PostgreSQL for transactional data
- Move heavy case tables → ClickHouse
- Parquet remains as raw layer (backup/archive)
- Same FastAPI API, different storage backend

**Why ClickHouse Later:**
- 10-100x faster than DuckDB for very large datasets
- Better for cross-dataset queries
- Handles concurrent analytical queries better
- Needed when data > 100M rows or many concurrent users

**Migration Strategy:**
1. **Now**: Implement Parquet + DuckDB (Phase 1)
2. **6 months**: Monitor performance, optimize Parquet partitioning
3. **12 months**: Add ClickHouse if needed (Phase 2)

**Alternative (Simpler):**
- **PostgreSQL only** (with optimizations)
- Good for < 10M rows
- Will struggle at FAERS scale (20M+ cases)
- Not recommended for fast-growing data

### 7.3 File Storage

**Location:** `src/storage/*`

**Features:**
- File upload handling
- Temporary file management
- File validation

**Recommendation for Scale:**
- **Small files (< 100MB)**: Supabase Storage
- **Large files (> 100MB)**: AWS S3 or Cloudflare R2
- **Archive**: Glacier or similar for old data

---

## 8. User Interface & Navigation

### 8.1 Page Structure

**Main Pages:**
- `app.py` - Landing page
- `pages/1_Quantum_PV_Explorer.py` - Signal module
- `pages/2_Social_AE_Explorer.py` - Social AE module
- `pages/99_Executive_Dashboard.py` - Executive dashboard
- `pages/mechanism_explorer.py` - Mechanism AI
- `pages/Login.py` - Authentication
- `pages/Register.py` - Registration
- `pages/Profile.py` - User profile
- `pages/Settings.py` - Settings
- `pages/Admin_Data_Sources.py` - Admin

### 8.2 Navigation System

**Location:** `src/ui/top_nav.py`

**Components:**
- Top navigation bar (custom HTML/JS)
- User menu (Profile, Logout)
- Module switcher
- Workspace selector

**Issues:**
- Multiple sidebars (5 unused)
- Navigation complexity
- **Will be replaced in v2**

### 8.3 UI Components

**Location:** `src/ui/*`

**Key Components:**
- `upload_section.py` - File upload (1800+ lines)
- `query_interface.py` - Query workbench (2000+ lines)
- `results_display.py` - Results visualization
- `chat_interface.py` - ChatGPT-like interface
- `sidebar.py` - Sidebar filters
- `top_nav.py` - Top navigation

---

## 9. Business Logic & Algorithms

### 9.1 Signal Detection Algorithms

**PRR (Proportional Reporting Ratio):**
```
PRR = (a/(a+b)) / (c/(c+d))
95% CI: exp(ln(PRR) ± 1.96 * SE)
```

**ROR (Reporting Odds Ratio):**
```
ROR = (a×d) / (b×c)
95% CI: exp(ln(ROR) ± 1.96 * SE)
```

**IC (Information Component):**
```
IC = log2((a/(a+b)) / (c/(c+d)))
```

**BCPNN:**
- Bayesian network approach
- Handles missing data
- Provides credibility intervals

### 9.2 Quantum Ranking Algorithm

**Quantum Score:**
```
quantum_score = w1 * rarity + w2 * seriousness + w3 * recency + w4 * novelty
```

**Quantum Effects:**
- **Tunneling**: Near-threshold signals get boost
- **Superposition**: Multiple signal states
- **Entanglement**: Drug-reaction correlations

### 9.3 Subgroup Discovery

**Location:** `src/subgroup_discovery.py`

**Algorithm:**
1. Stratify by age/sex/country
2. Calculate signals per subgroup
3. Compare to overall population
4. Identify significant differences

---

## 10. Migration Guide

### 10.1 What to Migrate (Backend Services)

**✅ Keep as-is (Pure Python):**

| Module | Location | Why |
|--------|----------|-----|
| Query Parser | `src/nl_query_parser.py` | Core IP, no Streamlit deps |
| Signal Detection | `src/signal_stats.py` | Heavy lifting, testable |
| Quantum Ranking | `src/quantum_ranking.py` | Proprietary algorithm |
| Schema Detection | `src/pv_schema.py` | Reusable logic |
| Normalization | `src/normalization/*` | Pure Python |
| FAERS Loader | `src/faers_loader.py` | Complex parsing |
| E2B Import | `src/e2b_import.py` | XML parsing |
| Mechanism AI | `src/mechanism/*` | Python embeddings |
| Copilot Engine | `src/copilot/*` | Multi-agent design |
| Report Generator | `src/reports/*` | Structured output |
| Evidence Governance | `src/evidence_governance/*` | Audit logic |
| Data Sources | `src/data_sources/*` | Plugin architecture |

**Migration Strategy:**
1. Wrap in FastAPI endpoints
2. Keep business logic unchanged
3. Add API layer on top
4. Test thoroughly

### 10.2 What to Rebuild (Frontend)

**❌ Rebuild in React/Next.js:**

| Component | Current | New |
|-----------|---------|-----|
| Top Navigation | `src/ui/top_nav.py` | `components/TopNav.tsx` |
| Sidebar | `src/ui/sidebar.py` | `components/Sidebar.tsx` |
| Upload UI | `src/ui/upload_section.py` | `components/Upload.tsx` |
| Query Interface | `src/ui/query_interface.py` | `components/QueryInterface.tsx` |
| Results Display | `src/ui/results_display.py` | `components/ResultsDisplay.tsx` |
| Chat Interface | `src/ui/chat_interface.py` | `components/ChatInterface.tsx` |
| All Pages | `pages/*.py` | `app/**/page.tsx` |

**Why Rebuild:**
- Streamlit limitations
- Better UX/UI control
- Modern React patterns
- Mobile responsive
- Better performance

### 10.3 API Endpoints to Create

**Signal Module:**
- `POST /api/v1/signals/query` - Execute query
- `POST /api/v1/signals/upload` - Upload file
- `GET /api/v1/signals/results` - Get results
- `POST /api/v1/signals/rank` - Quantum ranking

**Social AE:**
- `GET /api/v1/social/posts` - Get social posts
- `POST /api/v1/social/pull` - Trigger pull
- `GET /api/v1/social/trends` - Get trends

**Copilot:**
- `POST /api/v1/copilot/chat` - Chat endpoint
- `GET /api/v1/copilot/history` - Chat history

**Mechanism:**
- `POST /api/v1/mechanism/predict` - Mechanism prediction
- `GET /api/v1/mechanism/pathways` - Get pathways

**Reports:**
- `POST /api/v1/reports/psur` - Generate PSUR
- `POST /api/v1/reports/dsur` - Generate DSUR

### 10.4 Database Schema

**Keep Supabase:**
- Same database structure
- Same RLS policies
- Same authentication

**No Changes Needed:**
- `pv_cases` table
- `public_ae_data` table
- `social_ae_posts` table
- User tables (Supabase Auth)

---

## 11. Key Files Reference

### 11.1 Core Business Logic

| File | Lines | Purpose |
|------|-------|---------|
| `src/nl_query_parser.py` | 659 | Natural language → filters |
| `src/signal_stats.py` | 480 | PRR/ROR/IC/BCPNN calculations |
| `src/quantum_ranking.py` | 281 | Quantum-inspired ranking |
| `src/pv_schema.py` | 195 | Schema detection |
| `src/faers_loader.py` | ~500 | FAERS file loading |
| `src/e2b_import.py` | ~300 | E2B XML import |

### 11.2 UI Components

| File | Lines | Purpose |
|------|-------|---------|
| `src/ui/query_interface.py` | 2023 | Query workbench |
| `src/ui/upload_section.py` | 1846 | File upload |
| `src/ui/results_display.py` | ~800 | Results visualization |
| `src/ui/chat_interface.py` | 930 | ChatGPT interface |
| `src/ui/top_nav.py` | 485 | Top navigation |

### 11.3 Major Modules

| Module | Files | Purpose |
|--------|-------|---------|
| `src/social_ae/` | 24 files | Social AE module |
| `src/ai/` | 84 files | AI/LLM integration |
| `src/mechanism/` | 8 files | Mechanism AI |
| `src/reports/` | 7 files | Report generation |
| `src/evidence_governance/` | 12 files | Governance |
| `src/data_sources/` | 20+ files | Data source integration |

---

## 12. Environment Variables

**Required:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_KEY` - Supabase service key (backend only)

**Optional (AI):**
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GROQ_API_KEY` - Groq API key

**Optional (Data Sources):**
- `REDDIT_CLIENT_ID` - Reddit API
- `REDDIT_CLIENT_SECRET` - Reddit API
- `TWITTER_BEARER_TOKEN` - Twitter API
- `PUBMED_API_KEY` - PubMed API (optional)

---

## 13. Deployment

**Current:**
- Streamlit Cloud
- Railway
- Render

**Future (v2):**
- Frontend: Vercel (Next.js)
- Backend: Fly.io, Railway, or Render (FastAPI)
- Database: Supabase (keep existing)
- Redis: Upstash (caching)

---

## 14. Testing

**Current State:**
- Limited unit tests
- Manual testing
- No E2E tests

**Recommended (v2):**
- Unit tests for all business logic
- Integration tests for API endpoints
- E2E tests with Playwright
- Test coverage > 80%

---

## 15. Known Issues & Technical Debt

1. **Navigation Complexity** - Multiple sidebars, needs simplification
2. **Large Files** - `query_interface.py` (2000+ lines) needs refactoring
3. **Streamlit Limitations** - UI constraints, needs React rebuild
4. **Limited Testing** - Needs comprehensive test suite
5. **Session State** - Fragile, needs proper state management
6. **Error Handling** - Inconsistent, needs centralization

---

## 16. Future Enhancements

1. **Client-Side Processing** - DuckDB WASM for small datasets
2. **Real-Time Updates** - WebSocket for live data
3. **Advanced Visualizations** - D3.js custom charts
4. **Mobile App** - React Native
5. **API Documentation** - OpenAPI/Swagger
6. **GraphQL API** - Alternative to REST
7. **Microservices** - Split into services when needed

---

## 17. Database Strategy Summary

### 17.1 Current State
- **Database**: Supabase PostgreSQL
- **Data Volume**: Growing rapidly (expected 50M+ records in 1-2 years)
- **Query Patterns**: Mix of transactional (real-time) and analytical (signal detection)

### 17.2 Recommended Strategy: Three-Layer Architecture

**Phase 1 (Now - 6 months): Parquet + DuckDB**
- ✅ **Backend Framework**: FastAPI (Python)
- ✅ **Transactional DB**: Supabase PostgreSQL (users, metadata, configs)
- ✅ **Case Storage**: Parquet files in object storage
- ✅ **Analytics Engine**: DuckDB/Polars (scans Parquet)
- ✅ **Workers**: RQ/Celery for heavy jobs
- ✅ **Cache**: Redis (optional)

**Why This Works:**
- Very cheap storage (object storage + Parquet compression)
- Excellent performance for analytical queries
- Minimal infrastructure
- Reuses all existing Python code

**Phase 2 (6-12 months): Add ClickHouse**
- Keep PostgreSQL for transactional data
- Move heavy case tables → ClickHouse
- Parquet remains as backup/archive layer
- Same FastAPI API, different storage backend

**Why ClickHouse Later:**
- 10-100x faster for very large datasets (> 100M rows)
- Better for cross-dataset queries
- Handles concurrent analytical queries better

### 17.3 Architecture Breakdown

**Backend Framework:**
- **FastAPI** (Python) - Keep all existing logic, async I/O, auto API docs

**Transactional Layer:**
- **PostgreSQL (Supabase)** - Users, orgs, metadata, saved queries, audit logs

**Analytical Layer (Phase 1):**
- **Parquet + DuckDB** - Case-level data, signal detection, PRR/ROR calculations

**Analytical Layer (Phase 2):**
- **ClickHouse** - When Parquet queries become slow or need cross-dataset queries

### 17.4 Cost Estimate

| Phase | Solution | Monthly Cost |
|-------|----------|--------------|
| **Phase 1** | Supabase Pro + S3 Storage + DuckDB | $25-50/month |
| **Phase 2** | Supabase Team + ClickHouse Cloud | $800-1100/month |

### 17.5 Immediate Actions

**Do Now:**
1. Add composite indexes (see Section 7.2.5)
2. Implement table partitioning
3. Create materialized views for common queries
4. Monitor query performance

**Plan For:**
1. TimescaleDB evaluation (6 months)
2. ClickHouse setup (12 months)
3. Data sync architecture (Kafka/Debezium)

---

## 18. Conclusion

AetherSignal is a **comprehensive, production-ready PV platform** with:

- ✅ **15,000+ lines of code**
- ✅ **200+ Python modules**
- ✅ **20+ data sources**
- ✅ **10+ major features**
- ✅ **Advanced AI integration**
- ✅ **Regulatory compliance features**

**For Migration:**
- Keep all backend Python services
- Rebuild frontend in React/Next.js
- Wrap services in FastAPI
- **Optimize database (see Section 7.2)**
- Preserve business logic

**Database Strategy:**
- **Short-term**: Optimize PostgreSQL (indexes, partitioning, materialized views)
- **Medium-term**: Consider TimescaleDB for time-series
- **Long-term**: Add ClickHouse for analytics at scale

**This blueprint serves as:**
- Migration reference
- Onboarding documentation
- Architecture guide
- Feature inventory
- **Database scaling roadmap**

---

**End of Blueprint**

