# 🌐 **SOCIAL SOURCES - COMPLETE OPERATIONAL GUIDE**

**Date:** Current  
**Purpose:** Answer all questions about how social media sources work, scheduling, API keys, and where to see results

---

## ✅ **QUICK ANSWERS**

### **1. Do we need to map which tabs/screens use which sources?**

**No, not critical right now.** The mapping is already clear:
- **Social AE Explorer** (`pages/2_Social_AE_Explorer.py`) → Uses Reddit + X
- **Signal Module** (`pages/1_Quantum_PV_Explorer.py`) → Uses FAERS + Literature + Social (for correlation)
- **Executive Dashboard** → Uses ALL sources (unified view)

**But if you want it for documentation/pitch deck, I can create it.**

---

### **2. Is Reddit complete? No more action needed?**

**✅ YES - Reddit is COMPLETE and production-ready.**

**What's working:**
- ✅ Fetches posts/comments via Pushshift API (free, no auth)
- ✅ Searches by drug keywords
- ✅ Cleans and normalizes text
- ✅ Maps slang → MedDRA AE terms
- ✅ Stores in unified database
- ✅ Shows in Social AE Explorer tabs
- ✅ Integrated with signal detection

**No action needed** - it's fully functional and running.

---

## 🔄 **HOW PLATFORMS WORK: ON-DEMAND vs SCHEDULED**

### **Current Status: ON-DEMAND ONLY**

**How it works TODAY:**

1. **User clicks "Fetch latest posts"** in Social AE Explorer
2. **System fetches** Reddit/X posts for specified drug terms
3. **Results display** immediately in the UI
4. **Optional:** User can choose to store in database

**No automatic daily fetching** is running yet (but infrastructure exists).

---

### **Scheduled/Daily Fetching: AVAILABLE BUT NOT ACTIVE**

**Infrastructure exists:**
- ✅ `src/social_ae/social_ae_scheduler.py` - Daily pull function
- ✅ `api/social_api.py` - API endpoint for scheduled calls
- ✅ Automation tab in Social AE Explorer with "Run Daily Pull Now" button

**How to enable scheduled fetching:**

**Option 1: GitHub Actions (Recommended)**
```yaml
# .github/workflows/daily_social_pull.yml
name: Daily Social AE Pull
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
jobs:
  pull:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run daily pull
        run: python -m src.social_ae.social_ae_scheduler
```

**Option 2: Cron Job (Linux/Mac)**
```bash
# Add to crontab: crontab -e
0 2 * * * cd /path/to/aethersignal && python -m src.social_ae.social_ae_scheduler
```

**Option 3: Supabase Edge Function**
- Create edge function that calls `/social/daily` endpoint
- Schedule via Supabase cron

**Option 4: Manual trigger**
- Use "Run Daily Pull Now" button in Automation tab

---

## 📊 **WHERE TO SEE RESULTS**

### **Social AE Explorer (`pages/2_Social_AE_Explorer.py`)**

**5 Tabs:**

1. **🔍 Fetch & View Tab**
   - Click "Fetch latest posts"
   - See raw posts/comments
   - See extracted reactions
   - See severity scores
   - Option to store in database

2. **📈 Trends Tab**
   - Time-series charts
   - Reaction frequency over time
   - Platform comparison (Reddit vs X)

3. **🧠 Intelligence Tab**
   - Spike detection
   - Novelty detection (social-only reactions)
   - Post clustering
   - FAERS cross-linking

4. **📊 Database Tab**
   - View stored posts
   - Statistics (total posts, reactions, etc.)
   - Filter by drug, date, platform

5. **⚙️ Automation Tab**
   - Run daily pull manually
   - View scheduled job status
   - Configure watchlist

---

### **Signal Module (`pages/1_Quantum_PV_Explorer.py`)**

**Social data appears in:**
- **Overview Tab** - Shows source breakdown (FAERS vs Social vs Literature)
- **Signals Tab** - Social signals included in signal ranking
- **Trends Tab** - Social trends shown alongside FAERS trends
- **Executive Dashboard** - Unified view of all sources

---

## 🔬 **THE ACTUAL SCIENCE: HOW REDDIT WORKS**

### **How Reddit Fetching Works:**

**1. API Used:**
- **Pushshift API** (`https://api.pushshift.io/reddit/search/comment/`)
- **FREE** - No authentication required
- **Rate limits:** ~1 request per second (we use 0.5s delay)

**2. Search Method:**
- **Does NOT search every message** - Uses Reddit's indexed search
- **Keyword-based search:** Searches for drug terms in comment bodies
- **Time-windowed:** Only searches comments from last N days (default: 7 days)
- **Sorted by:** Most recent first (`sort_type: desc`)

**3. What Gets Searched:**
```python
# Example: Searching for "ozempic"
API Call:
  URL: https://api.pushshift.io/reddit/search/comment/
  Params:
    q: "ozempic"           # Search term
    size: 50               # Max results per term
    after: <timestamp>     # Only comments after this date
    sort: "created_utc"    # Sort by creation time
```

**4. Coverage:**
- ✅ **All public Reddit comments** (not just specific subreddits)
- ✅ **All subreddits** (r/ADHD, r/PCOS, r/LoseIt, etc.)
- ✅ **Comments AND posts** (Pushshift indexes both)
- ⚠️ **Limitation:** Only searches last ~7 days by default (can increase)

**5. Filtering:**
- Filters out very short comments (< 20 characters)
- Filters by date range
- Can filter by subreddit (if needed)

**6. Processing Pipeline:**
```
Reddit Comment
    ↓
Fetch via Pushshift API
    ↓
Clean text (remove URLs, normalize)
    ↓
Extract reactions (slang → MedDRA mapping)
    ↓
Calculate severity score
    ↓
Store in unified database
    ↓
Show in UI / Use in signal detection
```

---

## 🐦 **HOW X/TWITTER WORKS**

### **How Twitter/X Fetching Works:**

**1. API Used:**
- **Twitter API v2** (`https://api.twitter.com/2/tweets/search/recent`)
- **PAID** - Requires Bearer Token (API key)
- **Rate limits:** Varies by tier (Free tier: 500 tweets/month)

**2. Search Method:**
- **Keyword-based search:** Searches tweets containing drug terms
- **Query format:** `"{drug_term} -is:retweet lang:en"`
  - Excludes retweets
  - English language only
- **Time-windowed:** Recent tweets only (API limitation)

**3. What Gets Searched:**
```python
# Example: Searching for "ozempic"
API Call:
  URL: https://api.twitter.com/2/tweets/search/recent
  Headers:
    Authorization: Bearer <YOUR_TOKEN>
  Params:
    query: "ozempic -is:retweet lang:en"
    max_results: 50
```

**4. Coverage:**
- ✅ **All public tweets** (not just specific accounts)
- ✅ **Real-time** (searches recent tweets)
- ⚠️ **Limitation:** Free tier only searches last 7 days
- ⚠️ **Limitation:** Requires API key (paid)

**5. Current Status:**
- ✅ **Code is ready** - Fully implemented
- ⚠️ **Needs API key** - Won't fetch without `X_API_BEARER_TOKEN`
- ✅ **Graceful fallback** - Shows friendly message if no key

---

## 🔑 **HOW TO GET X/TWITTER API KEY**

### **Step-by-Step Guide:**

**1. Go to Twitter Developer Portal:**
   - **URL:** https://developer.twitter.com/en/portal/dashboard
   - **Sign in** with your Twitter/X account

**2. Create a Project:**
   - Click "Create Project"
   - Fill in project details:
     - Project name: "AetherSignal"
     - Use case: "Making a bot" or "Exploring API"
     - Description: "Pharmacovigilance adverse event monitoring"

**3. Create an App:**
   - Within your project, create an app
   - App name: "AetherSignal Social AE"

**4. Get API Keys:**
   - Go to "Keys and Tokens" tab
   - **Generate Bearer Token** (this is what you need)
   - Copy the token (starts with `AAAAAAAAAAAAAAAAAAAAA...`)

**5. Add to AetherSignal:**
   - **Option A:** Add to `.env` file:
     ```
     X_API_BEARER_TOKEN=your_token_here
     ```
   - **Option B:** Add to Streamlit secrets (if using Streamlit Cloud):
     ```toml
     # .streamlit/secrets.toml
     X_API_BEARER_TOKEN = "your_token_here"
     ```
   - **Option C:** Use API Key Manager UI:
     - Go to Settings → API Key Manager
     - Enter token in "Twitter/X API Key" field

**6. Pricing (Updated 2024):**
   - **Free Tier:** $0/month
     - Very limited access (mostly read-only)
     - Good for testing only
     - **Note:** Free tier may have restrictions
   - **Basic Tier:** $200/month (or $175/month if billed annually = $2,100/year)
     - Write: 3,000 posts per month
     - Read: 10,000 posts per month
     - Access to X's v2 API endpoints
     - **Best for:** Small to medium scale production use
   - **Pro Tier:** Custom pricing (contact X)
     - Higher limits
     - Full archive access
     - Enterprise features

**Links:**
- **Developer Portal:** https://developer.x.com/en/portal/dashboard
- **API Documentation:** https://developer.x.com/en/docs/twitter-api
- **Pricing:** https://developer.x.com/en/portal/petition/essential/basic-info
- **Sign Up:** https://developer.x.com/en/portal/petition/essential/basic-info

---

## 📋 **ALL AVAILABLE APIs & LINKS**

### **Social Media APIs:**

| Platform | API | Status | Free/Paid | Link | Key Required |
|----------|-----|--------|----------|------|--------------|
| **Reddit** | Pushshift API | ✅ Active | ✅ **FREE** | https://api.pushshift.io | ❌ No |
| **X/Twitter** | Twitter API v2 | ✅ Ready | 💰 **PAID** ($200/mo Basic) | https://developer.x.com | ✅ Yes (Bearer Token) |
| **YouTube** | YouTube Data API | ⚠️ Scaffolded | ✅ **FREE** (quota) | https://developers.google.com/youtube/v3 | ✅ Yes (API Key) |
| **TikTok** | Unofficial API | ⚠️ Scaffolded | ⚠️ **Unofficial** | N/A | ❌ No |

---

### **Regulatory & Literature APIs:**

| Source | API | Status | Free/Paid | Link | Key Required |
|--------|-----|--------|-----------|------|--------------|
| **FAERS** | FDA Download | ✅ Active | ✅ **FREE** | https://fis.fda.gov/content/Exports/faers_extract.zip | ❌ No |
| **OpenFDA** | OpenFDA API | ✅ Active | ✅ **FREE** | https://open.fda.gov | ❌ No (optional key for higher limits) |
| **PubMed** | E-utilities API | ✅ Active | ✅ **FREE** | https://eutils.ncbi.nlm.nih.gov | ❌ No (optional key for higher limits) |
| **ClinicalTrials.gov** | ClinicalTrials.gov API | ✅ Active | ✅ **FREE** | https://clinicaltrials.gov/api | ❌ No |
| **DailyMed** | DailyMed API | ✅ Active | ✅ **FREE** | https://dailymed.nlm.nih.gov | ❌ No |
| **EMA** | EudraVigilance | ⚠️ CSV Only | ✅ **FREE** | https://www.ema.europa.eu | ❌ No |
| **VigiBase** | WHO API | ⚠️ Scaffolded | 💰 **PAID** | Requires subscription | ✅ Yes |

---

### **Health Data APIs:**

| Source | API | Status | Free/Paid | Link | Key Required |
|--------|-----|--------|-----------|------|--------------|
| **CMS Blue Button** | CMS API | ⚠️ Scaffolded | ✅ **FREE** | https://bluebutton.cms.gov | ✅ Yes (OAuth) |
| **Human API** | Human API | ⚠️ Scaffolded | 💰 **PAID** | https://www.humanapi.co | ✅ Yes |
| **Metriport** | Metriport API | ⚠️ Scaffolded | 💰 **PAID** | https://www.metriport.com | ✅ Yes |
| **OHDSI** | OHDSI API | ⚠️ Scaffolded | ✅ **FREE** | https://www.ohdsi.org | ❌ No |

---

## 🔬 **DETAILED SCIENCE: HOW EACH PLATFORM WORKS**

### **1. Reddit (Pushshift API)**

**How it works:**
```
1. You provide: Drug name (e.g., "ozempic")
2. Pushshift searches: ALL Reddit comments containing "ozempic"
3. Returns: Up to 50 most recent comments (within date range)
4. We process: Extract reactions, calculate severity, store
```

**What it searches:**
- ✅ **All public subreddits** (r/ADHD, r/PCOS, r/LoseIt, r/AskDocs, etc.)
- ✅ **All comments** (not just top-level posts)
- ✅ **Keyword matching** (exact match + case-insensitive)
- ⚠️ **Time-limited** (default: last 7 days, can increase)

**Example query:**
```python
# Searching for "ozempic" in last 7 days
GET https://api.pushshift.io/reddit/search/comment/
  ?q=ozempic
  &size=50
  &after=1704067200  # Unix timestamp (7 days ago)
  &sort=created_utc
  &sort_type=desc
```

**Result:**
- Returns JSON with comment data:
  - `body`: Comment text
  - `created_utc`: Timestamp
  - `subreddit`: Which subreddit
  - `author`: Username
  - `score`: Upvotes

**Limitations:**
- ⚠️ Pushshift may have delays (not real-time)
- ⚠️ Rate limits (we use 0.5s delay between requests)
- ⚠️ Only searches indexed comments (not ALL Reddit)

---

### **2. X/Twitter (Twitter API v2)**

**How it works:**
```
1. You provide: Drug name (e.g., "ozempic")
2. Twitter searches: Recent tweets containing "ozempic"
3. Returns: Up to 100 tweets (API limit)
4. We process: Extract reactions, calculate severity, store
```

**What it searches:**
- ✅ **All public tweets** (not just specific accounts)
- ✅ **Real-time** (searches most recent tweets)
- ✅ **Excludes retweets** (original content only)
- ✅ **English only** (lang:en filter)
- ⚠️ **Time-limited** (Free tier: last 7 days only)

**Example query:**
```python
# Searching for "ozempic" tweets
GET https://api.twitter.com/2/tweets/search/recent
  Headers:
    Authorization: Bearer <YOUR_TOKEN>
  Params:
    query: "ozempic -is:retweet lang:en"
    max_results: 50
    tweet.fields: created_at,author_id,public_metrics
```

**Result:**
- Returns JSON with tweet data:
  - `text`: Tweet content
  - `created_at`: Timestamp
  - `author_id`: User ID
  - `public_metrics`: Likes, retweets, replies

**Limitations:**
- ⚠️ Requires paid API key (Free tier: $0 but limited)
- ⚠️ Rate limits (Free: 500 tweets/month)
- ⚠️ Only recent tweets (Free: 7 days, Paid: 30 days)

---

### **3. YouTube (YouTube Data API)**

**How it works (when enabled):**
```
1. You provide: Drug name
2. YouTube searches: Videos about the drug
3. Returns: Video metadata + comments
4. We process: Extract reactions from comments
```

**API:** https://developers.google.com/youtube/v3
- ✅ **FREE** (with quota limits)
- ✅ **API Key required** (free from Google Cloud)
- ⚠️ **Quota:** 10,000 units/day (1 search = 100 units)

**How to get API key:**
1. Go to https://console.cloud.google.com
2. Create project
3. Enable "YouTube Data API v3"
4. Create credentials → API Key
5. Add to `.env`: `YOUTUBE_API_KEY=your_key`

---

### **4. TikTok (Unofficial)**

**Status:** Scaffolded, disabled by default
**Why:** High noise, low signal quality
**How:** Would use unofficial scraping libraries (not recommended for production)

---

## 📊 **WHERE RESULTS APPEAR**

### **Social AE Explorer Page:**

**Tab 1: Fetch & View**
- Raw posts/comments
- Extracted reactions
- Severity scores
- Source breakdown

**Tab 2: Trends**
- Time-series charts
- Reaction frequency
- Platform comparison

**Tab 3: Intelligence**
- Spike detection
- Novelty signals
- Post clustering
- FAERS correlation

**Tab 4: Database**
- Stored posts
- Statistics
- Filter/search

**Tab 5: Automation**
- Manual daily pull
- Scheduled job status

---

### **Signal Module:**

**Overview Tab:**
- Source breakdown pie chart
- "X posts from Reddit, Y from Twitter"

**Signals Tab:**
- Social signals included in ranking
- Shows source: "FAERS + Social"

**Trends Tab:**
- Social trends alongside FAERS trends
- Multi-source time series

**Executive Dashboard:**
- Unified view of ALL sources
- Social data integrated

---

## 🎯 **SUMMARY**

### **Reddit:**
- ✅ **COMPLETE** - No action needed
- ✅ **FREE** - No API key required
- ✅ **ON-DEMAND** - Fetches when you click "Fetch"
- ✅ **Searches:** All Reddit comments (keyword-based, not every message)
- ✅ **Results:** Appear in Social AE Explorer tabs

### **X/Twitter:**
- ✅ **READY** - Needs API key to activate
- 💰 **PAID** - Free tier available ($0/month, 500 tweets/month)
- ✅ **ON-DEMAND** - Fetches when you click "Fetch"
- ✅ **Searches:** Recent tweets (keyword-based)
- ✅ **Results:** Appear in Social AE Explorer tabs

### **Other Platforms:**
- ⚠️ **Scaffolded** - Ready to enable with API keys
- ⚠️ **ON-DEMAND** - No automatic scheduling yet
- ✅ **Infrastructure exists** - Can enable scheduled pulls

---

## 🚀 **NEXT STEPS (If You Want)**

1. **Enable X/Twitter:**
   - Get API key from https://developer.twitter.com
   - Add to `.env` or Streamlit secrets
   - X will start fetching automatically

2. **Enable Scheduled Pulls:**
   - Set up GitHub Actions or cron job
   - Daily pulls will run automatically
   - Results stored in database

3. **Enable Other Platforms:**
   - Get API keys (YouTube, etc.)
   - Add to `.env`
   - Enable in Data Source Manager

---

**Last Updated:** Current  
**Status:** Complete Guide

