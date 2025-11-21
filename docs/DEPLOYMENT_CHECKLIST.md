# 🚀 Complete Deployment Checklist

## ✅ **All Code Created - Ready to Deploy!**

All files have been created. Follow this checklist to deploy:

---

## 📋 **Phase 1: Supabase Setup (5 minutes)**

### Step 1.1: Create Tables
- [ ] Go to Supabase Dashboard → SQL Editor
- [ ] Run SQL from `scripts/setup_supabase_tables.sql`
- [ ] Verify tables created: `social_ae` and `pull_history`

### Step 1.2: Get Service Key
- [ ] Go to Supabase Dashboard → Project Settings → API
- [ ] Copy **Service Role Key** (not anon key!)
- [ ] Save for Step 2

---

## 📋 **Phase 2: Deploy FastAPI Endpoint (15 minutes)**

### Option A: Render (Recommended)

- [ ] Create account at https://render.com
- [ ] New → Web Service
- [ ] Connect GitHub repository
- [ ] Configure:
  - **Name**: `social-ae-api`
  - **Environment**: Python 3
  - **Build Command**: `pip install -r api/requirements.txt && pip install -r requirements.txt`
  - **Start Command**: `cd api && uvicorn social_api:app --host 0.0.0.0 --port $PORT`
- [ ] Set Environment Variables:
  - `SUPABASE_URL` = `https://scrksfxnkxmvvdzwmqnc.supabase.co`
  - `SUPABASE_SERVICE_KEY` = (from Step 1.2)
  - `API_SECRET_KEY` = (generate random string)
- [ ] Deploy
- [ ] Copy your endpoint URL: `https://your-app.onrender.com`

### Option B: Railway

- [ ] Create account at https://railway.app
- [ ] New Project → Deploy from GitHub
- [ ] Configure environment variables (same as Render)
- [ ] Deploy
- [ ] Copy endpoint URL

### Option C: Docker

- [ ] Build: `docker build -t social-ae-api .`
- [ ] Run: `docker run -d -p 8000:8000 -e SUPABASE_URL=... -e SUPABASE_SERVICE_KEY=... social-ae-api`
- [ ] Your endpoint: `http://localhost:8000` (or your server IP)

---

## 📋 **Phase 3: Deploy Edge Function (10 minutes)**

### Step 3.1: Install Supabase CLI

```bash
# macOS
brew install supabase/tap/supabase

# Windows
npm install -g supabase

# Linux
npm install -g supabase
```

### Step 3.2: Deploy Function

```bash
# Login
supabase login

# Link project
supabase link --project-ref scrksfxnkxmvvdzwmqnc

# Deploy
supabase functions deploy social_ae_pull

# Set secrets (use your API endpoint from Phase 2)
supabase secrets set SOCIAL_AE_API_ENDPOINT=https://your-app.onrender.com/social/daily
supabase secrets set API_SECRET_KEY=your_secret_key_from_phase_2
```

**OR use the script:**
```bash
# Windows
scripts\deploy_supabase_function.bat

# Mac/Linux
chmod +x scripts/deploy_supabase_function.sh
./scripts/deploy_supabase_function.sh
```

### Step 3.3: Setup Cron Job

- [ ] Go to Supabase Dashboard → Database → Cron Jobs
- [ ] New Cron Job:
  - **Name**: `daily_social_ae_pull`
  - **Schedule**: `0 1 * * *` (1 AM UTC daily)
  - **Function**: `social_ae_pull`
  - **Enabled**: Yes
- [ ] Save

---

## 📋 **Phase 4: Test Everything (5 minutes)**

### Test 1: API Health Check
```bash
curl https://your-app.onrender.com/health
```
Expected: `{"status": "healthy", ...}`

### Test 2: Manual Pull
```bash
curl -X POST https://your-app.onrender.com/social/daily \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_secret_key" \
  -d '{"source": "manual_test"}'
```
Expected: `{"success": true, "inserted": X, ...}`

### Test 3: Check Supabase
- [ ] Go to Supabase Dashboard → Table Editor
- [ ] Check `social_ae` table has new rows
- [ ] Check `pull_history` has log entry

### Test 4: Test Edge Function
```bash
supabase functions invoke social_ae_pull
```
Expected: Success response

---

## 📋 **Phase 5: Verify Integration (2 minutes)**

### In Streamlit App:
- [ ] Enable "Include Social AE signals" in sidebar
- [ ] Run a query
- [ ] Check if Social AE data appears in results
- [ ] Verify quantum ranking shows social signal counts

---

## 🎉 **You're Live!**

Your system is now:
- ✅ Pulling social posts daily (1 AM UTC)
- ✅ Storing in Supabase
- ✅ Available in Streamlit app
- ✅ Merging with FAERS data

---

## 📊 **Monitor Daily**

Check these daily:
1. Supabase Dashboard → `pull_history` table
2. API logs (Render/Railway dashboard)
3. Edge Function logs (Supabase Dashboard)

---

## 🆘 **Troubleshooting**

### No posts in Supabase
- Check API endpoint is accessible
- Verify service key is correct
- Check API logs for errors

### Edge Function not running
- Verify cron job is enabled
- Check function deployed: `supabase functions list`
- Check Edge Function logs

### Streamlit not showing Social AE
- Verify "Include Social AE signals" is enabled
- Check Supabase has data
- Check browser console for errors

---

## 📝 **Files Created**

All deployment files are ready:
- ✅ `supabase/functions/social_ae_pull/index.ts` - Edge Function
- ✅ `api/social_api.py` - FastAPI endpoint
- ✅ `scripts/setup_supabase_tables.sql` - Database schema
- ✅ `scripts/deploy_supabase_function.sh/bat` - Deployment scripts
- ✅ `render.yaml` - Render config
- ✅ `railway.json` - Railway config
- ✅ `Dockerfile` - Docker config
- ✅ `docs/DEPLOYMENT_GUIDE.md` - Full guide

**Everything is ready - just follow the checklist above!** 🚀

