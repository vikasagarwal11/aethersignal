# 🧪 Complete Features Testing Guide - AetherSignal

## 📋 Table of Contents
1. [Core Modules](#core-modules)
2. [Data Upload & Schema Detection](#data-upload--schema-detection)
3. [Query & Analysis Features](#query--analysis-features)
4. [Signal Detection & Statistics](#signal-detection--statistics)
5. [AI-Enhanced Features](#ai-enhanced-features)
6. [Quantum-Inspired Features](#quantum-inspired-features)
7. [Social AE Explorer](#social-ae-explorer)
8. [Reporting & Export](#reporting--export)
9. [Advanced Features](#advanced-features)

---

## 🏗️ Core Modules

### 1. Landing Page (`app.py`)
**Location:** `http://localhost:8501/`

**Features:**
- Navigation to Quantum PV Explorer
- Navigation to Social AE Explorer
- Feature overview

**How to Test:**
1. Open `http://localhost:8501/`
2. Click "⚛️ Launch Quantum PV Explorer"
3. Click "🌐 Open Social AE Explorer"
4. Verify navigation works correctly

---

## 📤 Data Upload & Schema Detection

### 2. Multi-Format Data Upload
**Location:** Quantum PV Explorer → Step 1

**Features:**
- CSV, Excel (.xlsx, .xls)
- Text files
- ZIP archives (FAERS ASCII format)
- PDF files (basic extraction)
- Multiple file upload

**How to Test:**
1. Go to Quantum PV Explorer
2. Upload a CSV file with safety data
3. Upload an Excel file
4. Try uploading a ZIP archive (FAERS format)
5. Verify files are accepted

### 3. Automatic Schema Detection
**Location:** Quantum PV Explorer → Step 1 → After upload

**Features:**
- Fuzzy column matching
- Auto-detection of: case_id, drug_name, reaction, age, sex, country, seriousness, dates, outcome
- Manual schema mapping UI
- Vendor-agnostic (works with any format)

**How to Test:**
1. Upload a file with non-standard column names (e.g., "Medication" instead of "drug_name")
2. Click "Load & map data"
3. Verify system detects columns automatically
4. Use manual mapping if needed
5. Check that data loads correctly

**Test Data Formats:**
- FAERS ASCII format
- Custom CSV with different column names
- Excel with mixed formats

---

## 💬 Query & Analysis Features

### 4. Natural Language Queries
**Location:** Quantum PV Explorer → Step 2 → "Natural Language Query" tab

**Features:**
- Plain English queries
- Context-aware drug/reaction detection
- Concept detection (seniors, pediatrics, recently, etc.)
- Multiple drugs/reactions support
- Starter questions

**How to Test:**
1. Enable "🤖 Enable AI-enhanced features" (optional)
2. Try these queries:
   - "find all cases related to Dupixent"
   - "show me serious cases for drug aspirin and reaction headache"
   - "find cases for seniors with drug metformin"
   - "show reactions for drug Dupixent drug Semaglutide"
   - "find cases recently reported for drug Ozempic"
3. Click starter questions to auto-fill queries
4. Verify results appear correctly

**Advanced Queries:**
- "find all high-risk events for drug Dupixent"
- "show me cases with drug ibuprofen and reaction nausea in United States"
- "cases with drug paracetamol since 2020"
- "find pregnant women with drug X"

### 5. Advanced Structured Filters
**Location:** Sidebar (left panel)

**Features:**
- Drug name filter
- Reaction/event filter
- Age range (min/max)
- Sex filter (M/F)
- Country filter
- Seriousness flag
- Date range (from/to)
- Clear filters button

**How to Test:**
1. Open sidebar
2. Set drug name: "aspirin"
3. Set reaction: "headache"
4. Set age range: 18-65
5. Set country: "United States"
6. Enable seriousness filter
7. Set date range
8. Click "Apply Filters"
9. Verify filtered results

### 6. Drug Watchlist
**Location:** Quantum PV Explorer → Step 2 → "Drug Watchlist" tab

**Features:**
- Add drugs to watchlist
- View top reactions for watched drugs
- Quick filter by watchlist drug
- Remove drugs from watchlist

**How to Test:**
1. Go to "Drug Watchlist" tab
2. Add a drug: "Dupixent"
3. Add another: "Ozempic"
4. View top reactions for each
5. Click on a reaction to filter
6. Remove a drug from watchlist

### 7. Browse All Drugs/Reactions
**Location:** Quantum PV Explorer → Step 2 → Natural Language Query tab

**Features:**
- Top drugs/reactions as clickable chips
- Collapsible "Browse all drugs" section
- Searchable multiselect for all drugs
- Collapsible "Browse all reactions" section
- Searchable multiselect for all reactions

**How to Test:**
1. After loading data, see top drugs/reactions as chips
2. Click a chip to add to query
3. Expand "Browse all drugs"
4. Search for a specific drug
5. Select multiple drugs
6. Do the same for reactions
7. Verify selections appear in query

---

## 📊 Signal Detection & Statistics

### 8. PRR/ROR Calculation
**Location:** Results → Signals tab

**Features:**
- Proportional Reporting Ratio (PRR) with 95% CI
- Reporting Odds Ratio (ROR) with 95% CI
- Information Component (IC) with 95% CI
- BCPNN (Bayesian Confidence Propagation Neural Network)
- Chi-square test
- Fisher's exact test
- 2×2 contingency tables

**How to Test:**
1. Query with both drug and reaction (e.g., "drug aspirin reaction headache")
2. Go to "Signals" tab
3. Verify PRR, ROR, IC values
4. Check confidence intervals
5. View 2×2 contingency table
6. Verify statistical tests

### 9. Subgroup Discovery
**Location:** Results → Signals tab → Subgroup Discovery

**Features:**
- Age subgroup analysis
- Sex subgroup analysis
- Country subgroup analysis
- Statistical comparisons

**How to Test:**
1. Run a query with drug and reaction
2. Go to Signals tab
3. Scroll to "Subgroup Discovery"
4. View age distribution
5. View sex distribution
6. View country distribution
7. Verify statistics for each subgroup

### 10. Time Trend Analysis
**Location:** Results → Trends tab

**Features:**
- Case count over time
- Monthly/quarterly aggregation
- Trend direction (increasing/decreasing/stable)
- Spike detection
- Interactive Plotly charts

**How to Test:**
1. Run a query
2. Go to "Trends" tab
3. View time series chart
4. Check trend direction indicator
5. View detected spikes
6. Hover over chart for details
7. Try different time aggregations

### 11. Co-Reaction Analysis
**Location:** Results → Overview tab

**Features:**
- Top co-occurring reactions
- Reaction co-occurrence matrix
- Network visualization (if available)

**How to Test:**
1. Query for a specific drug
2. View "Top Co-occurring Reactions"
3. Click on a co-reaction to filter
4. Verify co-occurrence statistics

### 12. New Signal Detection
**Location:** Results → Signals tab → New Signal Detection

**Features:**
- Unexpectedness scoring
- Novel signal identification
- Threshold-based filtering

**How to Test:**
1. Run a query
2. Go to Signals tab
3. Scroll to "New Signal Detection"
4. View unexpectedness scores
5. Check for novel signals
6. Adjust threshold if available

---

## 🤖 AI-Enhanced Features

### 13. Enhanced Query Interpretation
**Location:** Quantum PV Explorer → Step 2 → Enable AI checkbox

**Features:**
- Hybrid router (rule-based + LLM)
- Context-aware detection
- Concept detection
- Confidence scoring

**How to Test:**
1. Check "🤖 Enable AI-enhanced features"
2. Try complex queries:
   - "Are there any eye-related safety concerns with Dupixent after 2022?"
   - "Find all cases related to dupixent" (no explicit keywords)
   - "Show me serious cases for seniors"
3. Verify query is interpreted correctly
4. Check confidence score (if displayed)

### 14. Enhanced Literature Integration
**Location:** Results → Signals tab → Literature Evidence

**Features:**
- PubMed search
- ClinicalTrials.gov search
- LLM-powered abstract summarization
- Key findings extraction
- Mechanism identification
- Consensus view

**How to Test:**
1. Query for a drug-reaction pair (e.g., "drug Dupixent reaction conjunctivitis")
2. Go to Signals tab
3. Expand "Literature Evidence"
4. Click "🔍 Search Literature"
5. If AI enabled, view:
   - AI-generated summaries for each abstract
   - Key findings across papers
   - Proposed mechanisms
   - Consensus view
6. Click on PubMed/ClinicalTrials links

### 15. Case Narrative Analysis
**Location:** Results → Cases tab → Case Details → "🤖 Analyze Narrative"

**Features:**
- Extract structured data from narratives
- Summarize case narratives
- Identify missing information
- Flag inconsistencies

**How to Test:**
1. Query for cases
2. Go to "Cases" tab
3. Select a case with a narrative
4. Click "🤖 Analyze Narrative" (if AI enabled)
5. View:
   - Extracted drugs, reactions, dates
   - Narrative summary
   - Missing information list
   - Inconsistencies (if any)

### 16. Causal Explanation
**Location:** Results → Conversational tab → "🧠 Generate Causal Explanation"

**Features:**
- Mechanism explanation
- Clinical context
- Risk assessment
- Uses Claude Opus (if available) for best reasoning

**How to Test:**
1. Enable AI features
2. Query for a drug-reaction pair
3. Go to "💬 Conversational" tab
4. Generate comprehensive summary
5. Click "🧠 Generate Causal Explanation"
6. View mechanism analysis

### 17. Conversational Safety Engine
**Location:** Results → Conversational tab

**Features:**
- Natural language responses
- Red flag detection
- Trend interpretation
- Demographics summary

**How to Test:**
1. Enable AI features
2. Query: "Is Dupixent showing any new red flags recently?"
3. Go to "💬 Conversational" tab
4. View natural language response
5. Check red flags section
6. View trends interpretation

### 18. Enhanced MedDRA Mapping
**Location:** Automatic (when AI enabled)

**Features:**
- Context-aware mapping
- Synonym expansion
- Colloquial term mapping

**How to Test:**
1. Enable AI features
2. Use colloquial terms in queries (e.g., "fever" instead of "pyrexia")
3. Verify system maps to correct MedDRA terms
4. Check synonym expansion

---

## ⚛️ Quantum-Inspired Features

### 19. Quantum-Inspired Ranking
**Location:** Sidebar → "Enable quantum-inspired ranking"

**Features:**
- Multi-factor signal scoring
- Quantum-inspired interaction terms
- Tunneling effects
- Re-ranking of drug-event pairs

**How to Test:**
1. Enable "⚛️ Enable quantum-inspired ranking" in sidebar
2. Run a query
3. Go to Signals tab
4. View quantum-enhanced rankings
5. Compare with classical rankings
6. Check quantum scores

### 20. Quantum-Inspired Anomaly Detection
**Location:** Results → Trends tab → Quantum-inspired anomaly detection

**Features:**
- Time series anomaly scoring
- Z-score calculation
- Curvature-based detection
- Top anomalous periods

**How to Test:**
1. Run a query with time data
2. Go to Trends tab
3. Expand "Quantum-inspired anomaly detection (experimental)"
4. View top 10 anomalous periods
5. Check z-scores and anomaly scores
6. Verify periods make sense

### 21. Quantum-Inspired Clustering
**Location:** Results → Signals tab (if integrated)

**Features:**
- Case clustering by demographics
- Quantum-weighted distance
- Cluster summaries

**How to Test:**
1. Run a query
2. Go to Signals tab
3. Look for clustering section (if integrated)
4. View cluster summaries
5. Check cluster characteristics

---

## 🌐 Social AE Explorer

### 22. Social Media Data Fetching
**Location:** Social AE Explorer → Fetch & View tab

**Features:**
- Reddit scraping
- X (Twitter) scraping
- Patient forum integration
- Date range filtering
- Drug term filtering
- Platform selection

**How to Test:**
1. Go to Social AE Explorer
2. Enter drug terms: "Dupixent, Ozempic"
3. Set days back: 30
4. Select platforms: Reddit, X
5. Enable options:
   - Anonymize posts
   - Store in database
   - Use ML detection
6. Click "🔍 Fetch latest posts"
7. View fetched posts

### 23. Social AE Cleaning & Filtering
**Location:** Automatic (after fetching)

**Features:**
- Text cleaning
- PII removal
- Duplicate detection
- Relevance filtering

**How to Test:**
1. Fetch social posts
2. View cleaned posts
3. Verify PII is removed
4. Check for duplicates
5. Verify relevance

### 24. ML-Based AE Detection
**Location:** Social AE Explorer → "🤖 Use ML detection" checkbox

**Features:**
- DistilBERT-based classification
- AE probability scoring
- Automatic filtering

**How to Test:**
1. Enable "🤖 Use ML detection"
2. Fetch posts
3. View AE probability scores
4. Verify high-probability posts are flagged
5. Check classification accuracy

### 25. Social AE Integration with FAERS
**Location:** Quantum PV Explorer → Sidebar → "Include Social AE signals"

**Features:**
- Merge Social AE with FAERS data
- Weighted scoring (40% social, 60% FAERS)
- Unified query interface

**How to Test:**
1. Enable "Include Social AE signals" in sidebar
2. Load FAERS data
3. Run a query
4. Verify social AE data is included
5. Check merged results
6. View social AE counts in results

### 26. Social AE Dashboard
**Location:** Social AE Explorer → Dashboard tab

**Features:**
- Post statistics
- Drug mentions
- Reaction mentions
- Platform distribution
- Time trends

**How to Test:**
1. Go to Social AE Explorer
2. Click "Dashboard" tab
3. View statistics
4. Check charts
5. Filter by drug/reaction
6. View time trends

### 27. Social AE Automation
**Location:** Social AE Explorer → Automation tab

**Features:**
- Scheduled fetching
- Supabase Edge Function integration
- API endpoint for automation

**How to Test:**
1. Go to Automation tab
2. Set up scheduled fetching
3. Configure Supabase (if available)
4. Test API endpoint
5. Verify automation works

---

## 📄 Reporting & Export

### 28. PDF Report Generation
**Location:** Results → Report tab

**Features:**
- One-page comprehensive summary
- Query summary
- Statistics
- Signal detection metrics
- Top drugs and reactions
- Age statistics
- Downloadable PDF

**How to Test:**
1. Run a query
2. Go to "Report" tab
3. Review report preview
4. Click "Download PDF Report"
5. Open downloaded PDF
6. Verify all sections are included

### 29. E2B(R3) XML Export
**Location:** Results → Cases tab → Export options

**Features:**
- E2B(R3) compliant XML
- Case export
- ICH-compliant format

**How to Test:**
1. Query for cases
2. Go to Cases tab
3. Select cases
4. Click export/E2B button
5. Download XML file
6. Verify E2B format

### 30. Query Export/Import
**Location:** Query interface

**Features:**
- Export queries as JSON
- Import saved queries
- Query history

**How to Test:**
1. Create a query
2. Export query (if available)
3. Save as JSON
4. Import saved query
5. Verify query is restored

---

## 🔍 Advanced Features

### 31. Time-to-Onset Analysis
**Location:** Results → Cases tab

**Features:**
- Calculate time-to-onset
- Distribution analysis
- Median/mean calculations

**How to Test:**
1. Query cases with date data
2. Go to Cases tab
3. View time-to-onset for cases
4. Check distribution
5. Verify calculations

### 32. Longitudinal Spike Detection
**Location:** Results → Trends tab

**Features:**
- Detect significant spikes
- Statistical significance testing
- Spike visualization

**How to Test:**
1. Query with time data
2. Go to Trends tab
3. View detected spikes
4. Check significance
5. Verify spike periods

### 33. Class Effect Detection
**Location:** Results → Signals tab

**Features:**
- Drug class identification
- Class-level signal detection
- Cross-drug analysis

**How to Test:**
1. Query for multiple drugs in a class
2. Go to Signals tab
3. View class effects
4. Check class-level signals
5. Verify cross-drug patterns

### 34. Duplicate Detection
**Location:** Automatic (during data loading)

**Features:**
- Quantum-inspired duplicate detection
- Similarity scoring
- Duplicate flagging

**How to Test:**
1. Upload data with potential duplicates
2. Check for duplicate flags
3. View similarity scores
4. Verify detection accuracy

### 35. Case Series Viewer
**Location:** Results → Cases tab

**Features:**
- Detailed case view
- Patient demographics
- Drug/reaction details
- Narrative display
- Time-to-onset

**How to Test:**
1. Query for cases
2. Go to Cases tab
3. Click on a case
4. View detailed information
5. Check all fields
6. Test narrative analysis (if AI enabled)

### 36. Drill-Down Analysis
**Location:** Results → Various tabs

**Features:**
- Click-through analysis
- Filter refinement
- Subset exploration

**How to Test:**
1. View results
2. Click on drugs/reactions to filter
3. Drill down into subgroups
4. Refine filters
5. Explore subsets

---

## 🧪 Complete Testing Workflow

### End-to-End Test Scenario

1. **Data Upload:**
   - Upload FAERS CSV file
   - Verify schema detection
   - Load data

2. **Natural Language Query:**
   - Enable AI features
   - Query: "find all cases related to Dupixent with eye problems"
   - Verify results

3. **Signal Analysis:**
   - Go to Signals tab
   - Check PRR/ROR values
   - View subgroup discovery
   - Generate causal explanation

4. **Literature Integration:**
   - Search literature
   - View AI summaries
   - Check mechanisms

5. **Social AE Integration:**
   - Enable Social AE in sidebar
   - Verify merged data
   - Check social counts

6. **Quantum Features:**
   - Enable quantum ranking
   - View quantum scores
   - Check anomaly detection

7. **Export:**
   - Generate PDF report
   - Export E2B XML (if available)
   - Verify exports

---

## ✅ Testing Checklist

- [ ] Landing page navigation
- [ ] Data upload (CSV, Excel, ZIP)
- [ ] Schema detection and mapping
- [ ] Natural language queries
- [ ] Advanced filters
- [ ] Drug watchlist
- [ ] Browse all drugs/reactions
- [ ] PRR/ROR calculation
- [ ] Subgroup discovery
- [ ] Time trend analysis
- [ ] Co-reaction analysis
- [ ] New signal detection
- [ ] AI-enhanced query interpretation
- [ ] Enhanced literature integration
- [ ] Case narrative analysis
- [ ] Causal explanation
- [ ] Conversational engine
- [ ] Enhanced MedDRA mapping
- [ ] Quantum-inspired ranking
- [ ] Quantum anomaly detection
- [ ] Social AE fetching
- [ ] Social AE cleaning
- [ ] ML-based AE detection
- [ ] Social AE integration
- [ ] PDF report generation
- [ ] E2B export
- [ ] Time-to-onset analysis
- [ ] Longitudinal spike detection
- [ ] Class effect detection
- [ ] Duplicate detection
- [ ] Case series viewer

---

## 🐛 Common Issues & Solutions

### Issue: No results from query
**Solution:** Check filters, verify data is loaded, check drug/reaction names match dataset

### Issue: AI features not working
**Solution:** Verify API keys in `.env` file, check "Enable AI-enhanced features" is checked

### Issue: Social AE not fetching
**Solution:** Check Supabase configuration, verify API keys, check network connectivity

### Issue: PDF not generating
**Solution:** Check fpdf2 is installed, verify data is available, check file permissions

---

## 📝 Notes

- All features are session-based (data cleared on refresh)
- AI features require API keys (OpenAI minimum, Claude/Grok optional)
- Social AE requires Supabase setup (optional)
- Quantum features work with or without PennyLane
- Some features are experimental (marked in UI)

---

**Last Updated:** January 2025  
**Version:** 1.0

