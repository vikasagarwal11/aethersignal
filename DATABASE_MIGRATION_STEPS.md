# 🗄️ Database Migration Steps - Add super_admin Role

## 📋 **Step-by-Step Instructions**

### **Step 1: Open Supabase SQL Editor**

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor** (left sidebar)
3. Click **"New query"**

---

### **Step 2: Run the Migration Script**

Copy and paste the **entire contents** of `database/01_migration_add_super_admin_role.sql`:

```sql
-- ============================================================================
-- Migration: Add super_admin role to existing database
-- EXECUTION ORDER: 02 (Run this AFTER 00_schema.sql if database already exists)
-- ============================================================================
-- This script updates the role constraint to include 'super_admin'
-- Run this ONCE in Supabase SQL Editor for existing databases

-- Drop existing constraint
ALTER TABLE user_profiles 
DROP CONSTRAINT IF EXISTS user_profiles_role_check;

-- Add new constraint with super_admin
ALTER TABLE user_profiles 
ADD CONSTRAINT user_profiles_role_check 
CHECK (role IN ('super_admin', 'admin', 'scientist', 'viewer'));
```

**Click "Run"** (or press Ctrl+Enter)

**Expected Result:** ✅ Success message - "Success. No rows returned"

---

### **Step 3: Verify the Constraint Was Updated**

Run this query to verify:

```sql
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'user_profiles'::regclass
AND conname = 'user_profiles_role_check';
```

**Expected Result:** Should show the constraint includes `'super_admin'`

---

### **Step 4: Promote Your Account to super_admin**

**⚠️ IMPORTANT:** Replace `YOUR_EMAIL_HERE` with your actual email address!

```sql
UPDATE user_profiles
SET role = 'super_admin'
WHERE email = 'YOUR_EMAIL_HERE';
```

**Example:**
```sql
UPDATE user_profiles
SET role = 'super_admin'
WHERE email = 'vikas@example.com';
```

**Click "Run"**

**Expected Result:** ✅ Success message - "UPDATE 1" (if your email exists)

---

### **Step 5: Verify Your Account Was Updated**

Run this query to verify:

```sql
SELECT email, role, full_name, organization
FROM user_profiles
WHERE role = 'super_admin';
```

**Expected Result:** Should show your account with `role = 'super_admin'`

---

### **Step 6: Test in Application**

1. **Log out** of AetherSignal (if currently logged in)
2. **Log back in** with your account
3. **Try accessing:**
   - `/Settings` → Should work (no access denied)
   - `/API_Keys` → Should work (no access denied)

---

## ✅ **Success Checklist**

- [ ] Migration script ran successfully
- [ ] Constraint verification shows `super_admin` in allowed roles
- [ ] Your account updated to `super_admin`
- [ ] Verification query shows your account with `super_admin` role
- [ ] Can access Settings page without errors
- [ ] Can access API Keys page without errors

---

## ⚠️ **Troubleshooting**

### **Issue: "relation user_profiles does not exist"**
- **Solution:** You need to run `database/00_schema.sql` first to create the table

### **Issue: "UPDATE 0" (no rows updated)**
- **Solution:** Check your email address - it must match exactly (case-sensitive)
- Try: `SELECT email FROM user_profiles;` to see all emails

### **Issue: "constraint does not exist"**
- **Solution:** This is OK - the script uses `IF EXISTS`, so it's safe if constraint doesn't exist yet

### **Issue: Still getting "Access Denied" after update**
- **Solution:** 
  1. Make sure you logged out and logged back in
  2. Check session state: The app caches user profile in session
  3. Clear browser cache or use incognito mode
  4. Verify in database: `SELECT email, role FROM user_profiles WHERE email = 'your@email.com';`

---

## 📝 **Quick Reference**

### **Check Current Role:**
```sql
SELECT email, role FROM user_profiles WHERE email = 'your@email.com';
```

### **List All super_admin Users:**
```sql
SELECT email, role, full_name FROM user_profiles WHERE role = 'super_admin';
```

### **Promote Another User:**
```sql
UPDATE user_profiles
SET role = 'super_admin'
WHERE email = 'another@email.com';
```

### **Demote User (if needed):**
```sql
UPDATE user_profiles
SET role = 'scientist'
WHERE email = 'user@email.com';
```

---

**Created:** 2025-12-02  
**Status:** Ready to Execute

