# Fix Email Verification Redirect URL - Step by Step

## Current Issue

Email verification works, but redirects to wrong URL:
- **Current redirect:** `localhost:3000` ❌ (nothing runs there)
- **Should redirect to:** `localhost:8501` ✅ (your Streamlit app)

## Fix Instructions

### Option 1: Update in Supabase Dashboard (Recommended)

1. **Go to URL Configuration:**
   - Direct link: https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/auth/url-configuration
   - Or: Dashboard → Authentication → URL Configuration

2. **Update Site URL:**
   - Find **"Site URL"** field
   - Change from: `http://localhost:3000` (or whatever it is)
   - Change to: `http://localhost:8501`
   - Click **"Save"**

3. **Add Redirect URLs:**
   - In **"Redirect URLs"** section
   - Add these URLs (one per line):
     ```
     http://localhost:8501
     http://localhost:8501/
     http://localhost:8501/pages/Login.py
     ```
   - Click **"Save"**

4. **Test:**
   - Register a new test account
   - Check email verification link
   - Should redirect to Streamlit app instead of error

### Option 2: Use Wildcard (Easier for Development)

Instead of specific URLs, you can use wildcards:

**Redirect URLs:**
```
http://localhost:*
```

This allows redirects to any localhost port (8501, 8502, etc.)

⚠️ **Note:** Wildcards are fine for development, but use specific URLs in production.

---

## Current Status

- ✅ **Your account is verified** - the token in the URL proves it
- ✅ **You can login now** - go to http://localhost:8501 and login
- ⚠️ **Redirect needs fixing** - for better UX on future registrations

## After Fixing

Once you update the redirect URL:
- New verification emails will redirect to your Streamlit app
- Users will see a success message instead of connection error
- Better user experience overall

---

## Why This Happened

Supabase has a default redirect URL (`localhost:3000`) which is common for React/Next.js apps. Since you're using Streamlit (port 8501), the redirect URL needs to be updated to match your app.

This is a one-time configuration that will fix it for all future registrations! 🎯

