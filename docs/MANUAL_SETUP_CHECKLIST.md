# Manual Setup Checklist for Multi-Tenant System

## ✅ What I Cannot Do Automatically

The following steps require manual action because they involve:
- External services (Supabase)
- Security credentials (API keys)
- Service configuration (email settings)

---

## 📋 Step-by-Step Manual Setup

### Step 1: Create Supabase Project

**Action Required:** Manual (I cannot create Supabase projects)

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Fill in:
   - **Project Name:** `aethersignal` (or your preferred name)
   - **Database Password:** Choose a strong password (save it!)
   - **Region:** Choose closest to your users
   - **Pricing Plan:** Free tier is fine for testing
5. Click "Create new project"
6. Wait 2-3 minutes for project to be created

**✅ Checkpoint:** Project created, you should see the dashboard

---

### Step 2: Run Database Schema

**Action Required:** Manual (I cannot execute SQL in your Supabase project)

1. In Supabase dashboard, click **"SQL Editor"** in the left sidebar
2. Click **"New query"**
3. Open `database/schema.sql` from this project
4. Copy **ALL** contents of `database/schema.sql`
5. Paste into the SQL Editor
6. Click **"Run"** (or press Ctrl+Enter)
7. You should see: "Success. No rows returned"
8. Verify tables were created:
   - Go to **"Table Editor"** in left sidebar
   - You should see:
     - ✅ `user_profiles`
     - ✅ `pv_cases`

**✅ Checkpoint:** Both tables visible in Table Editor

**Troubleshooting:**
- If you see errors, check:
  - Are you in the correct project?
  - Did you copy the entire SQL file?
  - Are there any syntax errors? (The SQL should be valid)

---

### Step 3: Get Supabase Credentials

**Action Required:** Manual (I cannot access your Supabase credentials)

1. In Supabase dashboard, click **"Project Settings"** (gear icon in left sidebar)
2. Click **"API"** in the settings menu
3. You'll see:
   - **Project URL:** `https://xxxxx.supabase.co`
   - **anon/public key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - **service_role key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (keep this secret!)

4. Copy these values (you'll need them for `.env` file)

**✅ Checkpoint:** You have:
- Project URL
- anon/public key
- service_role key (optional, for admin operations)

---

### Step 4: Configure Environment Variables

**Action Required:** Manual (I cannot modify your `.env` file with real credentials)

1. Open `.env` file in the project root
2. Add/update these lines:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here  # Optional, for admin operations
```

3. Replace:
   - `your-project-id.supabase.co` with your actual Project URL
   - `your-anon-key-here` with your actual anon/public key
   - `your-service-role-key-here` with your service_role key (optional)

**✅ Checkpoint:** `.env` file has correct Supabase credentials

**Security Note:**
- `.env` file is in `.gitignore` (your keys are safe)
- Never commit `.env` to git
- Never share your service_role key publicly

---

### Step 5: Enable Email Authentication

**Action Required:** Manual (I cannot configure Supabase email settings)

1. In Supabase dashboard, click **"Authentication"** in left sidebar
2. Click **"Providers"** tab
3. Find **"Email"** provider
4. Toggle it **ON** (should be enabled by default)
5. Configure email settings (optional):
   - **Enable email confirmations:** Toggle ON (recommended)
   - **Secure email change:** Toggle ON (recommended)
   - **Double confirm email changes:** Toggle ON (recommended)

**Email Templates (Optional):**
1. Click **"Email Templates"** tab
2. Customize templates if desired:
   - Confirm signup
   - Magic Link
   - Change Email Address
   - Reset Password

**SMTP Configuration (Optional - for custom email):**
- If you want to use your own email service:
  1. Click **"Settings"** in Authentication
  2. Scroll to **"SMTP Settings"**
  3. Configure your SMTP server
  4. Test email sending

**✅ Checkpoint:** Email authentication is enabled

**Note:** Supabase provides free email sending (limited), but you can configure custom SMTP for production.

---

### Step 6: Verify Setup

**Action Required:** Manual (I cannot test your Supabase connection)

1. Start Streamlit:
   ```bash
   streamlit run app.py
   ```

2. Test Registration:
   - Click "Register" in top navigation
   - Create a test account:
     - Email: `test@example.com`
     - Password: `testpassword123`
     - Organization: `Test Company`
   - Click "Create Account"
   - Check Supabase dashboard → Authentication → Users
   - You should see your test user

3. Test Login:
   - Logout (if logged in)
   - Click "Login"
   - Enter test credentials
   - Should successfully login

4. Test Data Storage:
   - Login with test account
   - Upload a small FAERS file
   - Check Supabase dashboard → Table Editor → `pv_cases`
   - You should see data stored with your `user_id` and `organization`

5. Test Data Isolation:
   - Create second test account with different organization
   - Upload different data
   - Verify each account only sees their own data

**✅ Checkpoint:** All tests pass

---

## 🔍 Verification Checklist

After completing all steps, verify:

- [ ] Supabase project created
- [ ] Database schema executed successfully
- [ ] `user_profiles` table exists
- [ ] `pv_cases` table exists
- [ ] `.env` file has correct SUPABASE_URL
- [ ] `.env` file has correct SUPABASE_ANON_KEY
- [ ] Email authentication enabled in Supabase
- [ ] Can register new user
- [ ] Can login with registered user
- [ ] Data upload stores in database
- [ ] Data loads from database on query
- [ ] Multi-tenant isolation works (2 companies can't see each other's data)

---

## 🐛 Troubleshooting

### Issue: "Supabase not available" error

**Solution:**
1. Check `.env` file has correct credentials
2. Verify SUPABASE_URL format: `https://xxxxx.supabase.co` (no trailing slash)
3. Restart Streamlit after changing `.env`

### Issue: "Failed to connect to Supabase" error

**Solution:**
1. Check internet connection
2. Verify Supabase project is active (not paused)
3. Check if you're using correct anon key (not service_role key for client operations)

### Issue: "Registration failed" error

**Solution:**
1. Check email authentication is enabled in Supabase
2. Verify email format is valid
3. Check Supabase dashboard → Authentication → Users for error details

### Issue: "Data not storing in database"

**Solution:**
1. Verify user is authenticated (check session state)
2. Check `pv_cases` table exists
3. Verify RLS policies are enabled
4. Check Supabase logs for errors

### Issue: "Can see other company's data"

**Solution:**
1. Verify RLS policies are enabled:
   ```sql
   SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'pv_cases';
   ```
2. Check policies exist:
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'pv_cases';
   ```
3. Re-run `database/schema.sql` if policies are missing

---

## 📞 Need Help?

If you encounter issues:

1. **Check Supabase Logs:**
   - Dashboard → Logs → API Logs
   - Look for error messages

2. **Check Streamlit Console:**
   - Look for Python errors
   - Check if imports are working

3. **Verify Database:**
   - Run SQL queries in Supabase SQL Editor
   - Check if tables and policies exist

4. **Test Connection:**
   ```python
   from supabase import create_client
   sb = create_client("YOUR_URL", "YOUR_KEY")
   print(sb.table("user_profiles").select("*").limit(1).execute())
   ```

---

## ✅ Summary

**What I Can Do:**
- ✅ Create SQL schema file
- ✅ Create authentication code
- ✅ Create UI components
- ✅ Integrate everything

**What You Must Do:**
- ❌ Create Supabase project (manual)
- ❌ Run SQL schema (manual)
- ❌ Get API credentials (manual)
- ❌ Configure `.env` file (manual)
- ❌ Enable email authentication (manual)
- ❌ Test the system (manual)

**Estimated Time:** 15-30 minutes

**Difficulty:** Easy (just following steps)

---

## 🎉 Once Complete

After completing all steps, your multi-tenant system will be fully operational:
- ✅ Users can register and login
- ✅ Data is stored in database
- ✅ Data persists across sessions
- ✅ Multi-tenant isolation works
- ✅ Ready for production use

Good luck! 🚀

