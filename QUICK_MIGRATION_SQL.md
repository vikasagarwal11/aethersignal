# ⚡ Quick Migration SQL - Copy & Paste Ready

## 🚀 **Step 1: Run Migration Script**

Copy and paste this into Supabase SQL Editor:

```sql
-- ============================================================================
-- Migration: Add super_admin role to existing database
-- ============================================================================

-- Drop existing constraint
ALTER TABLE user_profiles 
DROP CONSTRAINT IF EXISTS user_profiles_role_check;

-- Add new constraint with super_admin
ALTER TABLE user_profiles 
ADD CONSTRAINT user_profiles_role_check 
CHECK (role IN ('super_admin', 'admin', 'scientist', 'viewer'));
```

**Click "Run"** ✅

---

## 👤 **Step 2: Promote Your Account**

**⚠️ Replace `YOUR_EMAIL_HERE` with your actual email!**

```sql
UPDATE user_profiles
SET role = 'super_admin'
WHERE email = 'YOUR_EMAIL_HERE';
```

**Click "Run"** ✅

---

## ✅ **Step 3: Verify**

```sql
SELECT email, role, full_name
FROM user_profiles
WHERE role = 'super_admin';
```

**Expected:** Should show your account ✅

---

## 🧪 **Step 4: Test in App**

1. Log out (if logged in)
2. Log back in
3. Try `/Settings` → Should work ✅
4. Try `/API_Keys` → Should work ✅

---

**That's it!** 🎉

