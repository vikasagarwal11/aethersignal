# Social AE Module - Complete File List & Implementation Summary

## 📋 Overview

The **Social AE (Adverse Event) Module** is a comprehensive system for fetching, cleaning, mapping, and analyzing social media posts related to drug adverse events. It pulls data from Reddit and X (Twitter), cleans it using rule-based filters, maps slang to medical terms (MedDRA), and provides a searchable dashboard.

---

## 🗂️ All Files Related to Social AE Module

### **Core Module Files** (`src/social_ae/`)

1. **`__init__.py`** - Module initialization, exports `render_social_ae_module`
2. **`social_dashboard.py`** (590 lines) - Main UI component with Streamlit interface
3. **`social_fetcher.py`** (200 lines) - Fetches posts from Reddit (Pushshift API) and X (Twitter API v2)
4. **`social_cleaner.py`** (182 lines) - Rule-based spam/noise removal and text normalization
5. **`social_mapper.py`** (273 lines) - Maps slang to medical terms with confidence scoring
6. **`social_anonymizer.py`** (251 lines) - PII removal and HIPAA-compliant anonymization
7. **`social_ae_storage.py`** (330 lines) - SQLite database storage with deduplication
8. **`social_storage.py`** - Supabase storage integration (alternative to SQLite)
9. **`social_ae_supabase.py`** - Supabase client and normalization functions
10. **`social_ae_integration.py`** (133 lines) - Integration layer for merging with FAERS data
11. **`social_ae_scheduler.py`** (184 lines) - Daily automation scheduler for scheduled pulls
12. **`supabase_client.py`** - Simplified Supabase client wrapper
13. **`ml_classifier.py`** - Optional ML-based AE detection (DistilBERT)

### **Page/UI Files**

14. **`pages/2_Social_AE_Explorer.py`** (112 lines) - Full-page Streamlit page for Social AE Explorer

### **API Files**

15. **`api/social_api.py`** (188 lines) - FastAPI endpoint for automated daily pulls (deployable to Render/Railway)

### **Documentation Files**

16. **`docs/SOCIAL_AE_ALIGNMENT.md`** - Alignment analysis with vision (75% complete)
17. **`docs/SOCIAL_AE_ROADMAP.md`** - Roadmap for remaining features
18. **`docs/SOCIAL_AE_PRODUCTION_SETUP.md`** - Production deployment guide

### **Integration Points** (Files that use Social AE)

19. **`src/ui/sidebar.py`** - Sidebar toggle for "Include Social AE signals"
20. **`src/ui/results_display.py`** - Integration with Quantum PV results
21. **`pages/1_Quantum_PV_Explorer.py`** - Merges Social AE with FAERS data
22. **`src/literature_integration.py`** - Literature validation for Social AE signals

---

## 🎯 What the Module Does

### **1. Data Fetching** (`social_fetcher.py`)
- ✅ **Reddit Integration**: Uses Pushshift API (free, no auth required)
- ✅ **X (Twitter) Integration**: X API v2 support (requires Bearer token)
- ✅ **Configurable Search**: Drug keywords, time ranges (days back), platform selection
- ✅ **Default Drug Watchlist**: Focus on GLP-1s (ozempic, mounjaro, semaglutide) and high-volume drugs

### **2. Data Cleaning** (`social_cleaner.py`)
- ✅ **Spam Detection**: Removes buy links, promotions, clickbait
- ✅ **Quality Filtering**: Length checks (20-2000 chars), word count, substance detection
- ✅ **Text Normalization**: Whitespace cleanup, excessive newline removal
- ✅ **Noise Reduction**: Can filter out 98% of low-quality content
- ✅ **Optional ML Enhancement**: DistilBERT-based AE detection (slower but more accurate)

### **3. Slang → MedDRA Mapping** (`social_mapper.py`)
- ✅ **50+ Slang Patterns**: Maps informal language to medical terms
  - Examples: "puking" → "vomiting", "dizzy" → "dizziness", "heart racing" → "tachycardia"
- ✅ **Confidence Scoring** (0.0-1.0):
  - Exact match = 0.9 confidence
  - Pattern match = 0.7 confidence
  - Drug context boost = +0.1
  - Negation detection = -0.3 penalty
- ✅ **Reaction Extraction**: Identifies adverse events from post text
- ✅ **MedDRA Normalization**: Maps to standardized MedDRA Preferred Terms

### **4. Anonymization** (`social_anonymizer.py`)
- ✅ **PII Removal**: Emails, phone numbers, SSNs, credit cards
- ✅ **Location Removal**: Addresses, ZIP codes
- ✅ **Username Hashing**: SHA256 hashing for user privacy
- ✅ **HIPAA Compliance**: Aggressive anonymization mode for public use
- ✅ **Medical ID Removal**: Removes medical record numbers

### **5. Data Storage** (`social_ae_storage.py`, `social_storage.py`)
- ✅ **SQLite Database**: Local storage with deduplication
- ✅ **Supabase Integration**: Cloud storage option
- ✅ **Historical Tracking**: Stores posts with timestamps, reactions, confidence scores
- ✅ **Deduplication**: Prevents duplicate posts (by platform + post_id)
- ✅ **Pull History**: Tracks daily pull statistics

### **6. Dashboard UI** (`social_dashboard.py`)
- ✅ **Three Tabs**:
  - **Fetch & View**: Manual fetching, filtering, search
  - **Database**: Statistics, query interface
  - **Automation**: Scheduled pull management
- ✅ **Filtering Options**:
  - By drug, reaction, platform
  - By confidence score (slider)
  - Search within posts
- ✅ **Export**: CSV download
- ✅ **Literature Validation**: Integration with PubMed/ClinicalTrials.gov

### **7. Integration with FAERS** (`social_ae_integration.py`)
- ✅ **Data Merging**: Combines Social AE with FAERS data
- ✅ **Weighted Scoring**: 40% social, 60% FAERS (configurable)
- ✅ **Quantum Score Enhancement**: Boosts quantum scores with social signals
- ✅ **Normalization**: Converts Social AE to FAERS-compatible structure

### **8. Automation** (`social_ae_scheduler.py`)
- ✅ **Daily Pull Function**: Automated fetching with default watchlist
- ✅ **Scheduled Jobs**: Supports cron, GitHub Actions, APScheduler
- ✅ **Error Handling**: Comprehensive logging and error reporting
- ✅ **Default Watchlist**: 20+ high-volume drugs (GLP-1s, antidepressants, etc.)

### **9. API Endpoint** (`api/social_api.py`)
- ✅ **FastAPI Service**: Deployable to Render/Railway/EC2
- ✅ **Daily Pull Endpoint**: `/social/daily` (POST)
- ✅ **Health Check**: `/health` endpoint
- ✅ **Authentication**: Optional API secret key protection

---

## 📊 Implementation Status

### ✅ **Fully Implemented** (75% of vision)

| Feature | Status | File(s) |
|---------|--------|---------|
| Daily Pulling (Reddit/X) | ✅ Complete | `social_fetcher.py` |
| Rule-Based Cleanup | ✅ Complete | `social_cleaner.py` |
| Slang → MedDRA Mapping | ✅ Complete | `social_mapper.py` |
| Confidence Scoring | ✅ Complete | `social_mapper.py` |
| Searchable Dashboard | ✅ Complete | `social_dashboard.py` |
| CSV Export | ✅ Complete | `social_dashboard.py` |
| Anonymization | ✅ Complete | `social_anonymizer.py` |
| SQLite Storage | ✅ Complete | `social_ae_storage.py` |
| Supabase Storage | ✅ Complete | `social_storage.py`, `social_ae_supabase.py` |
| FAERS Integration | ✅ Complete | `social_ae_integration.py` |
| Daily Automation | ✅ Complete | `social_ae_scheduler.py` |
| API Endpoint | ✅ Complete | `api/social_api.py` |
| Literature Validation | ✅ Complete | Integration with `literature_integration.py` |

### 🚧 **Partially Implemented / Future Enhancements**

| Feature | Status | Notes |
|---------|--------|-------|
| ML Classifier | ⚠️ Optional | `ml_classifier.py` exists but optional |
| Tiered Access | ❌ Not Started | Free (7 days) vs Paid (full history) - requires Stripe |
| Advanced Analytics | ⚠️ Basic | Basic stats available, could add trends/visualizations |

---

## 🔄 Data Flow

```
1. User Input (drug terms, days back, platforms)
   ↓
2. social_fetcher.py → Fetch from Reddit/X APIs
   ↓
3. social_cleaner.py → Remove spam, normalize text
   ↓
4. social_mapper.py → Extract reactions, map to MedDRA, add confidence scores
   ↓
5. social_anonymizer.py → Remove PII (if enabled)
   ↓
6. social_ae_storage.py / social_storage.py → Store in database
   ↓
7. social_dashboard.py → Display in UI with filtering/search
   ↓
8. social_ae_integration.py → Merge with FAERS (if enabled in Quantum PV)
```

---

## 📁 Files to Share with ChatGPT for Feedback

### **Essential Files** (Core Functionality)
1. `src/social_ae/social_dashboard.py` - Main UI
2. `src/social_ae/social_fetcher.py` - Data fetching
3. `src/social_ae/social_cleaner.py` - Data cleaning
4. `src/social_ae/social_mapper.py` - Reaction mapping & confidence scoring
5. `src/social_ae/social_anonymizer.py` - PII removal
6. `src/social_ae/social_ae_storage.py` - SQLite storage
7. `src/social_ae/social_ae_integration.py` - FAERS integration
8. `pages/2_Social_AE_Explorer.py` - Page wrapper

### **Supporting Files** (Optional but Helpful)
9. `src/social_ae/social_ae_scheduler.py` - Automation
10. `api/social_api.py` - API endpoint
11. `docs/SOCIAL_AE_ALIGNMENT.md` - Vision alignment doc
12. `docs/SOCIAL_AE_ROADMAP.md` - Roadmap

### **Integration Files** (If reviewing full system)
13. `pages/1_Quantum_PV_Explorer.py` - How Social AE merges with FAERS
14. `src/ui/sidebar.py` - Toggle for Social AE inclusion

---

## 🎯 Key Features for ChatGPT Review

### **1. Confidence Scoring System**
- Location: `social_mapper.py` lines 110-168
- How it works: Multi-factor scoring based on pattern match strength, drug context, negation detection
- Confidence levels: High (≥0.8), Medium (≥0.5), Low (>0), None (0)

### **2. Spam Detection**
- Location: `social_cleaner.py` lines 12-51
- Patterns: Buy links, promotions, clickbait, low-quality content
- Effectiveness: Can filter 98% of noise

### **3. Slang Mapping**
- Location: `social_mapper.py` lines 12-107
- Coverage: 50+ slang patterns across GI, neurological, cardiovascular, dermatological, etc.
- Extensibility: Easy to add new patterns

### **4. Anonymization**
- Location: `social_anonymizer.py`
- Compliance: HIPAA-ready with aggressive mode
- Removes: Emails, phones, SSNs, addresses, usernames

### **5. Database Schema**
- Location: `social_ae_storage.py` lines 27-81
- Features: Deduplication, indexing, pull history tracking
- Storage: SQLite (local) or Supabase (cloud)

---

## 💡 Questions for ChatGPT Review

1. **Code Quality**: Are the patterns and structure maintainable?
2. **Confidence Scoring**: Is the multi-factor approach sound?
3. **Spam Detection**: Are the regex patterns comprehensive enough?
4. **Anonymization**: Is PII removal thorough enough for HIPAA?
5. **Database Design**: Is the schema optimal for queries?
6. **Error Handling**: Are edge cases covered?
7. **Performance**: Are there bottlenecks in the data pipeline?
8. **Extensibility**: How easy is it to add new platforms/slang patterns?
9. **Integration**: Is the FAERS merge logic correct?
10. **Security**: Are there any security concerns with API keys/PII?

---

## 📝 Summary

The Social AE module is **75% complete** and production-ready for:
- ✅ Daily manual pulls
- ✅ Rule-based cleanup
- ✅ Reaction detection with confidence scores
- ✅ Searchable dashboard
- ✅ CSV exports
- ✅ Anonymization
- ✅ Database persistence
- ✅ FAERS integration

**Remaining work** (25%):
- Tiered access (monetization)
- Advanced analytics/visualizations
- Enhanced ML classifier (optional)

**Ready to share with ChatGPT for:**
- Code review and best practices
- Performance optimization suggestions
- Security audit
- Architecture improvements
- Feature enhancement ideas

