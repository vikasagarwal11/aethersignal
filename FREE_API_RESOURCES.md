# 🆓 **FREE API RESOURCES FOR AETHER SIGNAL**

**Date:** Current  
**Purpose:** List all free APIs available for social media, literature, and regulatory data  
**Status:** Comprehensive resource list

---

## ✅ **CONFIRMED: REDDIT STATUS**

**Yes, Reddit is COMPLETE for MVP/SaaS launch.**

**What's working:**
- ✅ Fetching via Pushshift API (free)
- ✅ Cleaning, normalization, AE extraction
- ✅ Storage, scoring, de-dup
- ✅ Integrated with signal detection

**Nice-to-haves (not blockers):**
- Better multi-AE extraction from single post
- Richer emoji/slang dictionaries
- Larger historical backfill

**Verdict:** ✅ **No more action needed for Reddit** - it's production-ready.

---

## 💰 **X/TWITTER PRICING (UPDATED)**

Based on X Developer Portal (2024):

| Tier | Price | Write Limit | Read Limit | Best For |
|------|-------|-------------|------------|----------|
| **Free** | $0/month | Very limited | Very limited | Testing only |
| **Basic** | **$200/month**<br>($175/month annual = $2,100/year) | 3,000 posts/month | 10,000 posts/month | Small-medium production |
| **Pro** | Custom (contact X) | Higher limits | Higher limits | Enterprise |

**Links:**
- **Pricing Page:** https://developer.x.com/en/portal/petition/essential/basic-info
- **Developer Portal:** https://developer.x.com/en/portal/dashboard
- **Sign Up:** https://developer.x.com/en/portal/petition/essential/basic-info

**Note:** X/Twitter API is **NOT free** for production use. Basic tier is $200/month.

---

## 🆓 **FREE API RESOURCES**

### **1. SOCIAL MEDIA APIS (FREE)**

#### **Reddit - Pushshift API** ✅ **FREE**
- **URL:** https://api.pushshift.io
- **Documentation:** https://github.com/pushshift/api
- **Status:** ✅ **Currently Active**
- **Rate Limits:** ~1 request/second (we use 0.5s delay)
- **Coverage:** All public Reddit comments
- **No API Key Required**

**Alternative Reddit APIs:**
- **Reddit API (Official):** https://www.reddit.com/dev/api
  - **Status:** FREE (requires OAuth for some endpoints)
  - **Rate Limits:** 60 requests/minute
  - **Better for:** Real-time, authenticated access

---

#### **YouTube Data API** ✅ **FREE (with quota)**
- **URL:** https://developers.google.com/youtube/v3
- **Documentation:** https://developers.google.com/youtube/v3/docs
- **Status:** ✅ **FREE** (10,000 units/day quota)
- **API Key:** Required (free from Google Cloud)
- **How to get:**
  1. Go to https://console.cloud.google.com
  2. Create project
  3. Enable "YouTube Data API v3"
  4. Create credentials → API Key
- **Quota:** 1 search = 100 units, so ~100 searches/day
- **Coverage:** Video metadata, comments, channel info

---

#### **Reddit (Official API)** ✅ **FREE**
- **URL:** https://www.reddit.com/dev/api
- **Documentation:** https://www.reddit.com/dev/api
- **Status:** ✅ **FREE** (OAuth required for some endpoints)
- **Rate Limits:** 60 requests/minute
- **Better for:** Real-time, authenticated access
- **Note:** Pushshift is easier for historical data

---

### **2. REGULATORY & PHARMACOVIGILANCE APIS (FREE)**

#### **FAERS (FDA Adverse Event Reporting System)** ✅ **FREE**
- **URL:** https://fis.fda.gov/content/Exports/faers_extract.zip
- **Documentation:** https://www.fda.gov/drugs/surveillance/questions-and-answers-fdas-adverse-event-reporting-system-faers
- **Status:** ✅ **FREE** (public data download)
- **Format:** Quarterly ZIP files (CSV)
- **Coverage:** All FDA adverse event reports
- **No API Key Required**

---

#### **OpenFDA API** ✅ **FREE**
- **URL:** https://open.fda.gov
- **Documentation:** https://open.fda.gov/apis/
- **Status:** ✅ **FREE** (optional key for higher limits)
- **Endpoints:**
  - `/drug/event` - Adverse events
  - `/drug/label` - Drug labels
  - `/drug/recall` - Recalls
- **Rate Limits:** 240 requests/minute (with key), 1 request/second (without key)
- **API Key:** Optional (get at https://api.data.gov/signup/)
- **Coverage:** FAERS data, drug labels, recalls, enforcement reports

---

#### **PubMed E-utilities API** ✅ **FREE**
- **URL:** https://eutils.ncbi.nlm.nih.gov
- **Documentation:** https://www.ncbi.nlm.nih.gov/books/NBK25497/
- **Status:** ✅ **FREE** (optional key for higher limits)
- **Endpoints:**
  - `esearch.fcgi` - Search PubMed
  - `efetch.fcgi` - Fetch abstracts/full text
- **Rate Limits:** 3 requests/second (without key), 10 requests/second (with key)
- **API Key:** Optional (get at https://account.ncbi.nlm.nih.gov/)
- **Coverage:** All PubMed abstracts, full-text links

---

#### **ClinicalTrials.gov API** ✅ **FREE**
- **URL:** https://clinicaltrials.gov/api
- **Documentation:** https://clinicaltrials.gov/api/v2/docs
- **Status:** ✅ **FREE** (no key required)
- **Rate Limits:** Reasonable (not strictly enforced)
- **Coverage:** All clinical trial data, adverse events, outcomes
- **No API Key Required**

---

#### **DailyMed API** ✅ **FREE**
- **URL:** https://dailymed.nlm.nih.gov/dailymed/
- **Documentation:** https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2
- **Status:** ✅ **FREE** (no key required)
- **Coverage:** FDA drug labels, adverse reactions, warnings
- **No API Key Required**

---

#### **Europe PMC API** ✅ **FREE**
- **URL:** https://europepmc.org/RestfulWebService
- **Documentation:** https://europepmc.org/Help
- **Status:** ✅ **FREE** (no key required)
- **Coverage:** European biomedical literature, preprints
- **No API Key Required**

---

### **3. NEWS & ALERTS APIS (FREE)**

#### **FDA MedWatch RSS** ✅ **FREE**
- **URL:** https://www.fda.gov/safety/medwatch-fda-safety-information-and-adverse-event-reporting-program
- **Format:** RSS Feed
- **Status:** ✅ **FREE** (RSS, no API key)
- **Coverage:** Drug safety alerts, recalls, warnings

---

#### **EMA Safety Updates** ✅ **FREE**
- **URL:** https://www.ema.europa.eu/en/medicines/regulatory-procedures-guidelines
- **Format:** RSS/PDF
- **Status:** ✅ **FREE** (public data)
- **Coverage:** EMA safety communications

---

#### **Health Canada Alerts** ✅ **FREE**
- **URL:** https://www.canada.ca/en/health-canada/services/drugs-health-products/medeffect-canada.html
- **Format:** RSS Feed
- **Status:** ✅ **FREE** (public data)
- **Coverage:** Canadian drug safety alerts

---

### **4. HEALTH DATA APIS (FREE)**

#### **CMS Blue Button 2.0** ✅ **FREE**
- **URL:** https://bluebutton.cms.gov
- **Documentation:** https://bluebutton.cms.gov/developers/
- **Status:** ✅ **FREE** (requires OAuth per patient)
- **Coverage:** Medicare claims data (with patient consent)
- **Note:** Requires OAuth, patient-specific

---

#### **OHDSI (Observational Health Data Sciences and Informatics)** ✅ **FREE**
- **URL:** https://www.ohdsi.org
- **Documentation:** https://www.ohdsi.org/web/wiki/doku.php?id=resources:software
- **Status:** ✅ **FREE** (open-source tools)
- **Coverage:** Observational health data, cohorts, studies
- **Note:** Tools and datasets, not direct API

---

### **5. ALTERNATIVE FREE SOCIAL MEDIA SOURCES**

#### **Reddit (via Pushshift)** ✅ **FREE**
- **URL:** https://api.pushshift.io
- **Status:** ✅ **Currently Active**
- **Best for:** Historical Reddit data

#### **Reddit (Official API)** ✅ **FREE**
- **URL:** https://www.reddit.com/dev/api
- **Status:** ✅ **FREE** (OAuth)
- **Best for:** Real-time Reddit data

#### **Reddit (via PRAW)** ✅ **FREE**
- **Library:** https://praw.readthedocs.io/
- **Status:** ✅ **FREE** (Python wrapper for Reddit API)
- **Best for:** Python-based Reddit access

---

## 📊 **FREE API SUMMARY TABLE**

| API | URL | Status | Key Required | Rate Limits | Best For |
|-----|-----|--------|--------------|-------------|----------|
| **Pushshift (Reddit)** | https://api.pushshift.io | ✅ Active | ❌ No | ~1 req/sec | Historical Reddit data |
| **Reddit Official** | https://www.reddit.com/dev/api | ✅ Active | ⚠️ OAuth | 60 req/min | Real-time Reddit |
| **OpenFDA** | https://open.fda.gov | ✅ Active | ⚠️ Optional | 240 req/min (with key) | FAERS, labels, recalls |
| **PubMed** | https://eutils.ncbi.nlm.nih.gov | ✅ Active | ⚠️ Optional | 10 req/sec (with key) | Biomedical literature |
| **ClinicalTrials.gov** | https://clinicaltrials.gov/api | ✅ Active | ❌ No | Reasonable | Clinical trial AEs |
| **DailyMed** | https://dailymed.nlm.nih.gov | ✅ Active | ❌ No | Reasonable | Drug labels |
| **Europe PMC** | https://europepmc.org | ✅ Active | ❌ No | Reasonable | European literature |
| **YouTube Data** | https://developers.google.com/youtube/v3 | ✅ Active | ✅ Yes (free) | 10K units/day | Video comments |
| **FDA MedWatch** | RSS Feed | ✅ Active | ❌ No | N/A | Safety alerts |
| **EMA Updates** | RSS Feed | ✅ Active | ❌ No | N/A | EU safety alerts |
| **Health Canada** | RSS Feed | ✅ Active | ❌ No | N/A | CA safety alerts |

---

## 🎯 **RECOMMENDATIONS**

### **For MVP/Free Launch:**

**Use these FREE APIs:**
1. ✅ **Reddit (Pushshift)** - Already integrated, FREE
2. ✅ **OpenFDA** - FAERS data, FREE
3. ✅ **PubMed** - Literature, FREE
4. ✅ **ClinicalTrials.gov** - Trial data, FREE
5. ✅ **DailyMed** - Drug labels, FREE

**Skip these (paid):**
- ❌ **X/Twitter** - $200/month (too expensive for free launch)
- ❌ **YouTube** - Free but quota-limited (can add later)
- ❌ **Paid health APIs** - Not needed for MVP

### **For Production (when you have revenue):**

**Add these:**
- 💰 **X/Twitter Basic** - $200/month (if budget allows)
- 💰 **YouTube** - Free tier sufficient initially
- 💰 **VigiBase** - If enterprise customers need it

---

## 🔗 **QUICK LINKS**

### **Social Media:**
- **Pushshift (Reddit):** https://api.pushshift.io
- **Reddit Official API:** https://www.reddit.com/dev/api
- **YouTube Data API:** https://developers.google.com/youtube/v3

### **Regulatory:**
- **OpenFDA:** https://open.fda.gov
- **FAERS Download:** https://fis.fda.gov/content/Exports/faers_extract.zip
- **ClinicalTrials.gov:** https://clinicaltrials.gov/api
- **DailyMed:** https://dailymed.nlm.nih.gov

### **Literature:**
- **PubMed E-utilities:** https://eutils.ncbi.nlm.nih.gov
- **Europe PMC:** https://europepmc.org/RestfulWebService

### **Alerts:**
- **FDA MedWatch:** https://www.fda.gov/safety/medwatch
- **EMA:** https://www.ema.europa.eu
- **Health Canada:** https://www.canada.ca/en/health-canada/services/drugs-health-products/medeffect-canada.html

---

## ✅ **FINAL ANSWER**

### **Reddit:**
- ✅ **COMPLETE** - No more action needed for MVP
- ✅ **FREE** - Pushshift API works perfectly
- ✅ **Production-ready**

### **X/Twitter:**
- 💰 **NOT FREE** - Basic tier is **$200/month** ($175/month if annual)
- ⚠️ **Skip for free launch** - Too expensive
- ✅ **Can add later** when you have revenue

### **Free APIs Available:**
- ✅ **Reddit** (Pushshift) - Already using
- ✅ **OpenFDA** - Already using
- ✅ **PubMed** - Already using
- ✅ **ClinicalTrials.gov** - Can add
- ✅ **DailyMed** - Can add
- ✅ **Europe PMC** - Can add
- ✅ **RSS Feeds** (FDA, EMA, Health Canada) - Can add

**Recommendation:** Stick with free APIs for MVP. Add X/Twitter later when you have paying customers.

---

**Last Updated:** Current  
**Status:** Complete Resource List

