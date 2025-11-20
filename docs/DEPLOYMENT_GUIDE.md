# Complete Deployment Guide - Social AE Module

## 🚀 **Full Production Deployment**

This guide covers deploying all components:
1. Supabase Edge Function (scheduled daily pulls)
2. FastAPI endpoint (social AE ingestion)
3. Database setup
4. Environment configuration

---

## 📋 **Step 1: Create Supabase Tables**

Go to Supabase Dashboard → SQL Editor and run:

```sql
-- Main Social AE table (simplified schema)
CREATE TABLE IF NOT EXISTS social_ae (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  drug_name TEXT,
  reaction TEXT,
  meddra_pt TEXT,
  ae_prob NUMERIC,
  created TIMESTAMP NOT NULL,
  text TEXT NOT NULL,
  subreddit TEXT,
  score INTEGER DEFAULT 0,
  inserted_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_social_created ON social_ae (created);
CREATE INDEX idx_social_drug ON social_ae (drug_name);
CREATE INDEX idx_social_reaction ON social_ae (reaction);

-- Pull history table
CREATE TABLE IF NOT EXISTS pull_history (
  id BIGSERIAL PRIMARY KEY,
  pull_date TIMESTAMP DEFAULT NOW(),
  drug_terms TEXT,
  platforms TEXT,
  posts_fetched INTEGER,
  posts_new INTEGER,
  posts_duplicate INTEGER,
  status TEXT,
  error_message TEXT
);
```

---

## 📋 **Step 2: Deploy FastAPI Endpoint**

### Option A: Render (Recommended - Free tier available)

1. **Create Render account**: https://render.com

2. **Create new Web Service**:
   - Connect your GitHub repository
   - **Build Command**: `pip install -r api/requirements.txt && pip install -r requirements.txt`
   - **Start Command**: `cd api && uvicorn social_api:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3

3. **Set Environment Variables**:
   ```
   SUPABASE_URL=https://scrksfxnkxmvvdzwmqnc.supabase.co
   SUPABASE_SERVICE_KEY=your_service_key_here
   API_SECRET_KEY=generate_random_string
   PORT=8000
   ```

4. **Deploy**: Click "Create Web Service"

5. **Get your endpoint URL**: `https://your-app.onrender.com`

### Option B: Railway

1. **Create Railway account**: https://railway.app

2. **New Project** → **Deploy from GitHub**

3. **Configure**:
   - Root Directory: `/`
   - Build Command: `pip install -r api/requirements.txt`
   - Start Command: `cd api && uvicorn social_api:app --host 0.0.0.0 --port $PORT`

4. **Set Environment Variables** (same as Render)

5. **Deploy**: Railway auto-deploys on push

### Option C: Docker (Any platform)

```bash
# Build image
docker build -t social-ae-api .

# Run container
docker run -d \
  -p 8000:8000 \
  -e SUPABASE_URL=https://scrksfxnkxmvvdzwmqnc.supabase.co \
  -e SUPABASE_SERVICE_KEY=your_key \
  -e API_SECRET_KEY=your_secret \
  social-ae-api
```

---

## 📋 **Step 3: Deploy Supabase Edge Function**

### Install Supabase CLI

```bash
# macOS
brew install supabase/tap/supabase

# Windows (via Scoop)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# Linux
npm install -g supabase
```

### Login and Link Project

```bash
# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref scrksfxnkxmvvdzwmqnc
```

### Deploy Edge Function

```bash
# Navigate to project root
cd /path/to/aethersignal

# Deploy the function
supabase functions deploy social_ae_pull
```

### Set Environment Variables

```bash
# Set your API endpoint (from Step 2)
supabase secrets set SOCIAL_AE_API_ENDPOINT=https://your-api.onrender.com/social/daily

# Set API secret key (same as in FastAPI)
supabase secrets set API_SECRET_KEY=your_secret_key_here
```

### Setup Cron Job

1. Go to Supabase Dashboard → Database → Cron Jobs
2. Click "New Cron Job"
3. Configure:
   - **Name**: `daily_social_ae_pull`
   - **Schedule**: `0 1 * * *` (1 AM UTC daily)
   - **Function**: `social_ae_pull`
   - **Enabled**: Yes
4. Save

---

## 📋 **Step 4: Get Supabase Service Key**

1. Go to Supabase Dashboard → Project Settings → API
2. Copy **Service Role Key** (not anon key!)
3. Use this in:
   - FastAPI environment variables
   - Edge Function secrets (already set via CLI)

⚠️ **Important**: Service key bypasses RLS. Never expose in frontend!

---

## 📋 **Step 5: Test the System**

### Test FastAPI Endpoint

```bash
# Test health check
curl https://your-api.onrender.com/health

# Test daily pull (manual trigger)
curl -X POST https://your-api.onrender.com/social/daily \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_secret_key" \
  -d '{"source": "manual_test"}'
```

### Test Edge Function

```bash
# Invoke function manually
supabase functions invoke social_ae_pull
```

### Verify Data in Supabase

1. Go to Supabase Dashboard → Table Editor
2. Check `social_ae` table for new posts
3. Check `pull_history` for pull logs

---

## 📋 **Step 6: Update Streamlit App**

The Streamlit app will automatically:
- Use Supabase when available
- Fallback to SQLite if Supabase unavailable
- Load Social AE data when "Include Social AE signals" is enabled

No changes needed - it's already integrated!

---

## 🔧 **Troubleshooting**

### Edge Function Not Running

1. Check cron job is enabled in Supabase Dashboard
2. Verify function deployed: `supabase functions list`
3. Check logs: Supabase Dashboard → Edge Functions → Logs

### API Endpoint Errors

1. Check environment variables are set
2. Verify Supabase service key is correct
3. Check API logs in Render/Railway dashboard
4. Test endpoint manually with curl

### No Data in Supabase

1. Verify tables exist: Run SQL from Step 1
2. Check API is storing: Look at API response
3. Verify service key has write permissions
4. Check Supabase logs for errors

---

## 📊 **Monitoring**

### Supabase Dashboard
- View stored posts: Table Editor → `social_ae`
- Check pull history: Table Editor → `pull_history`
- Monitor function runs: Edge Functions → Logs

### API Monitoring
- Render: Dashboard → Logs
- Railway: Dashboard → Deployments → Logs

### Expected Daily Volume
- **Posts fetched**: 500-2,000 per day
- **After cleaning**: 200-800 posts
- **Stored**: 100-500 new posts (after deduplication)

---

## 🎉 **You're Deployed!**

Your system is now:
- ✅ Pulling social posts daily (via Edge Function)
- ✅ Storing in Supabase (via FastAPI)
- ✅ Available in Streamlit app (automatic integration)
- ✅ Merging with FAERS data (when enabled)

**Next**: Monitor the first few daily pulls to ensure everything works!

