# 🚀 Quick Start - Deploy Everything in 30 Minutes

## ✅ **All Code Created - Ready to Deploy!**

I've created all the files. Here's the fastest path to deployment:

---

## 📋 **Step 1: Create Supabase Tables (2 minutes)**

1. Go to: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql/new
2. Copy and paste the SQL from `scripts/setup_supabase_tables.sql`
3. Click "Run"
4. ✅ Tables created!

---

## 📋 **Step 2: Deploy FastAPI to Render (10 minutes)**

### Quick Deploy:

1. **Go to**: https://render.com → Sign up/Login
2. **New** → **Web Service**
3. **Connect GitHub** → Select your `aethersignal` repo
4. **Configure**:
   - **Name**: `social-ae-api`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r api/requirements.txt && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     cd api && uvicorn social_api:app --host 0.0.0.0 --port $PORT
     ```
5. **Environment Variables** (click "Add Environment Variable"):
   ```
   SUPABASE_URL = https://scrksfxnkxmvvdzwmqnc.supabase.co
   SUPABASE_SERVICE_KEY = [Get from Supabase Dashboard → Settings → API → service_role key]
   API_SECRET_KEY = [Generate random string, e.g., openssl rand -hex 32]
   ```
6. **Create Web Service**
7. **Wait for deployment** (~5 minutes)
8. **Copy your URL**: `https://your-app.onrender.com`

---

## 📋 **Step 3: Deploy Edge Function (5 minutes)**

### Install Supabase CLI:

```bash
# Windows (PowerShell)
npm install -g supabase

# Mac
brew install supabase/tap/supabase

# Linux
npm install -g supabase
```

### Deploy:

```bash
# Login
supabase login

# Link project
supabase link --project-ref scrksfxnkxmvvdzwmqnc

# Deploy function
supabase functions deploy social_ae_pull

# Set secrets (use your Render URL from Step 2)
supabase secrets set SOCIAL_AE_API_ENDPOINT=https://your-app.onrender.com/social/daily
supabase secrets set API_SECRET_KEY=your_secret_key_from_step_2
```

**OR use the script:**
```bash
# Windows
scripts\deploy_supabase_function.bat

# Mac/Linux
chmod +x scripts/deploy_supabase_function.sh
./scripts/deploy_supabase_function.sh
```

---

## 📋 **Step 4: Setup Cron Job (2 minutes)**

1. Go to: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/database/cron
2. **New Cron Job**:
   - **Name**: `daily_social_ae_pull`
   - **Schedule**: `0 1 * * *` (1 AM UTC daily)
   - **Function**: `social_ae_pull`
   - **Enabled**: ✅ Yes
3. **Save**

---

## 📋 **Step 5: Test (5 minutes)**

### Test API:
```bash
curl https://your-app.onrender.com/health
```

### Test Manual Pull:
```bash
curl -X POST https://your-app.onrender.com/social/daily \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_secret_key" \
  -d '{"source": "test"}'
```

### Check Supabase:
- Go to Table Editor → `social_ae`
- Should see new posts!

---

## 🎉 **Done!**

Your system is now:
- ✅ Pulling social posts daily at 1 AM UTC
- ✅ Storing in Supabase
- ✅ Available in Streamlit app
- ✅ Ready for production use

---

## 📁 **Files Created**

All deployment files ready:
- ✅ `supabase/functions/social_ae_pull/index.ts` - Edge Function
- ✅ `api/social_api.py` - FastAPI endpoint  
- ✅ `src/social_ae/supabase_client.py` - Supabase client
- ✅ `src/social_ae/social_storage.py` - Simplified storage
- ✅ `scripts/setup_supabase_tables.sql` - Database schema
- ✅ `scripts/deploy_supabase_function.sh/bat` - Deployment scripts
- ✅ `render.yaml` - Render config
- ✅ `railway.json` - Railway config
- ✅ `Dockerfile` - Docker config

**Everything is ready - just follow the steps above!** 🚀

