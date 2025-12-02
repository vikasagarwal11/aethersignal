# 🚀 **IMPLEMENTATION PLAN: PUBLIC DATA PLATFORM**

**Date:** Current  
**Purpose:** Complete plan for daily automated pulls and public data publishing

---

## ✅ **WHAT WE JUST IMPLEMENTED**

### **1. MedSafetyAlerts** ✅ **DONE**
- ✅ Created `src/data_sources/sources/medsafety_alerts.py`
- ✅ Integrated into registry
- ✅ Added to `data_source_config.yaml`
- ✅ Added `feedparser` to requirements.txt
- ✅ Fetches FDA MedWatch + EMA RSS feeds
- ✅ Normalizes to unified schema

**Status:** Ready to use! ✅

---

## 🎯 **YOUR STRATEGY: PUBLIC DATA PLATFORM**

### **Concept:**
- **Daily automated pulls** for all major drugs
- **Generic AE data** (no company-specific analysis)
- **Publicly accessible** (no login required)
- **Searchable, filterable, exportable**

### **Benefits:**
1. ✅ **Public good** - Free AE data for everyone
2. ✅ **SEO & Traffic** - Public pages rank well
3. ✅ **Differentiation** - Most PV tools are behind paywalls
4. ✅ **Lead generation** - Free users → paid customers
5. ✅ **Data moat** - Historical data becomes valuable

---

## 📋 **IMPLEMENTATION STEPS**

### **Phase 1: Daily Automated Pulls** ✅ **INFRASTRUCTURE EXISTS**

**What exists:**
- ✅ `src/social_ae/social_ae_scheduler.py` - Daily pull function
- ✅ `api/social_api.py` - API endpoint `/social/daily`
- ✅ Default drug watchlist (40+ drugs)
- ✅ MedSafetyAlerts client (just added)

**What needs setup:**
- ⚠️ **Scheduler configuration** (GitHub Actions / Cron / Supabase)

**Next:** Set up actual scheduler (see below)

---

### **Phase 2: Public Data Storage**

**New table needed:**
```sql
CREATE TABLE public_ae_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drug_name TEXT NOT NULL,
    reaction TEXT,
    source TEXT NOT NULL,  -- 'reddit', 'openfda', 'pubmed', 'medsafety_alerts'
    text TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    confidence FLOAT,
    severity FLOAT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_drug (drug_name),
    INDEX idx_reaction (reaction),
    INDEX idx_source (source),
    INDEX idx_timestamp (timestamp)
);
```

**Key difference:** No `user_id` or `organization` - this is **public data**.

---

### **Phase 3: Public Data Pages**

**URL Structure:**
```
/drug/{drug_name}          - All AEs for a drug
/ae/{reaction_name}        - All drugs causing a reaction
/alerts                     - Latest safety alerts
/dashboard                  - Public dashboard
```

**Features:**
- No authentication required
- Searchable
- Filterable by source, date, severity
- Exportable (CSV download)
- Real-time updates (from daily pulls)

---

## 🚀 **RECOMMENDATIONS FOR ADDITIONAL SOURCES**

### **✅ Implement: MedSafetyAlerts** ✅ **DONE**
- **Status:** ✅ Just implemented
- **Value:** High (regulatory alerts)
- **Effort:** Low (RSS feeds)

---

### **❌ Skip: VAERS**
- **Why:** Vaccine-specific (different use case)
- **Priority:** Low (unless you want vaccine monitoring)
- **Recommendation:** Skip for now

---

### **❌ Skip: RxNorm**
- **Why:** Enhancement only (you have your own normalization)
- **Priority:** Low
- **Recommendation:** Skip for now

---

### **❌ Skip: OpenTrials/EUCTR**
- **Why:** Redundant with ClinicalTrials.gov
- **Priority:** Low
- **Recommendation:** Skip for now

---

## 📅 **DAILY SCHEDULING SETUP**

### **Option 1: GitHub Actions (Recommended for MVP)**

**File:** `.github/workflows/daily_pull.yml`
```yaml
name: Daily AE Data Pull

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
  workflow_dispatch:  # Manual trigger

jobs:
  pull:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python -m src.social_ae.social_ae_scheduler
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
```

---

### **Option 2: Supabase Edge Function**

**File:** `supabase/functions/daily-pull/index.ts`
```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  // Call your Python scheduler via HTTP
  const response = await fetch('https://your-api.com/social/daily', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('API_SECRET_KEY')}`
    }
  })
  
  return new Response(JSON.stringify(await response.json()), {
    headers: { 'Content-Type': 'application/json' }
  })
})
```

**Schedule:** Set up in Supabase Dashboard → Edge Functions → Cron

---

### **Option 3: Streamlit Cloud Cron (If Available)**

**File:** `scripts/daily_pull.py`
```python
#!/usr/bin/env python3
"""Daily pull script for Streamlit Cloud cron."""

from src.social_ae.social_ae_scheduler import run_scheduled_pull

if __name__ == "__main__":
    result = run_scheduled_pull()
    print(f"Daily pull completed: {result}")
```

**Note:** Streamlit Cloud doesn't have built-in cron, but you can use external cron services.

---

## 🎯 **RECOMMENDED NEXT STEPS**

### **Priority 1: Set Up Daily Scheduling** ⚡
1. ✅ Choose scheduler (GitHub Actions recommended)
2. ✅ Create workflow file
3. ✅ Test manual run
4. ✅ Enable scheduled runs

### **Priority 2: Create Public Data Table** 📊
1. ✅ Create `public_ae_data` table in Supabase
2. ✅ Modify scheduler to store in public table
3. ✅ Add indexes for performance

### **Priority 3: Create Public Pages** 🌐
1. ✅ Create `/drug/{drug_name}` page
2. ✅ Create `/alerts` page
3. ✅ Create public dashboard
4. ✅ Add search/filter functionality

### **Priority 4: Skip Other Sources** ⏭️
- ❌ VAERS (skip - different use case)
- ❌ RxNorm (skip - enhancement only)
- ❌ OpenTrials (skip - redundant)

---

## ✅ **WHAT'S READY NOW**

1. ✅ **MedSafetyAlerts** - Fully implemented
2. ✅ **Scheduler infrastructure** - Ready to configure
3. ✅ **Default drug watchlist** - 40+ drugs ready
4. ✅ **All free sources** - Reddit, OpenFDA, PubMed, ClinicalTrials, DailyMed

---

## 🚀 **SHOULD I PROCEED WITH?**

**A) Set up GitHub Actions scheduler** (30 min)
**B) Create public data table schema** (15 min)
**C) Create public data pages** (2-3 hours)
**D) All of the above** (recommended)

**Which one should I implement next?**

