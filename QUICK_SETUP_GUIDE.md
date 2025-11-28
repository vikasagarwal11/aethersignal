# Quick Setup Guide - Multi-Tenant System

## 🚀 What You Need to Do Manually (5 Steps)

I've created all the code, but you need to complete these 5 manual steps to connect to Supabase:

---

### Step 1: Create Supabase Project ⏱️ 5 minutes

1. Go to https://supabase.com
2. Sign up/login
3. Click "New Project"
4. Fill in:
   - Project Name: `aethersignal`
   - Database Password: (save this!)
   - Region: (choose closest)
5. Wait 2-3 minutes for project creation

**✅ Done when:** You see the Supabase dashboard

---

### Step 2: Run Database Schema ⏱️ 2 minutes

1. In Supabase dashboard → Click **"SQL Editor"** (left sidebar)
2. Click **"New query"**
3. Open `database/schema.sql` from this project
4. Copy **ALL** contents
5. Paste into SQL Editor
6. Click **"Run"** (or Ctrl+Enter)
7. Should see: "Success. No rows returned"

**✅ Done when:** You see `user_profiles` and `pv_cases` tables in "Table Editor"

---

### Step 3: Get API Credentials ⏱️ 1 minute

1. In Supabase dashboard → Click **"Project Settings"** (gear icon)
2. Click **"API"** tab
3. Copy these values:
   - **Project URL:** `https://xxxxx.supabase.co`
   - **anon/public key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**✅ Done when:** You have both values copied

---

### Step 4: Configure .env File ⏱️ 2 minutes

1. Open `.env` file in project root
2. Add/update these lines:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

3. Replace with your actual values from Step 3

**✅ Done when:** `.env` file has real Supabase credentials (not placeholders)

---

### Step 5: Enable Email Authentication ⏱️ 1 minute

1. In Supabase dashboard → Click **"Authentication"** (left sidebar)
2. Click **"Providers"** tab
3. Find **"Email"** provider
4. Toggle it **ON** (should be enabled by default)

**✅ Done when:** Email provider is enabled

---

## ✅ Verify Setup

Run this command to check if everything is configured:

```bash
python setup_supabase.py
```

You should see:
- [OK] Schema file exists
- [OK] supabase package is installed
- [OK] All required environment variables are set
- [OK] Successfully connected to Supabase
- [OK] user_profiles table exists

---

## 🎉 You're Done!

After completing these 5 steps:

1. Start Streamlit: `streamlit run app.py`
2. Click "Register" in top navigation
3. Create a test account
4. Upload data
5. Verify data is stored in Supabase

---

## 📋 Detailed Instructions

For more detailed instructions, see:
- `docs/MANUAL_SETUP_CHECKLIST.md` - Complete step-by-step guide
- `docs/MULTI_TENANT_SETUP_GUIDE.md` - Architecture and setup details

---

## ⚠️ Troubleshooting

**"Supabase not available" error:**
- Check `.env` file has correct credentials
- Restart Streamlit after changing `.env`

**"Failed to connect" error:**
- Verify SUPABASE_URL format: `https://xxxxx.supabase.co` (no trailing slash)
- Check internet connection

**"Table not found" error:**
- Run `database/schema.sql` in Supabase SQL Editor
- Verify tables exist in "Table Editor"

---

**Total Time:** ~10-15 minutes

**Difficulty:** Easy (just copy/paste and toggle switches)

Good luck! 🚀

