# Quick Setup - Execute Schema in SQL Editor

## Why This Approach?

**The automated connections are failing due to:**
- Network/DNS configuration on your machine
- CLI requires interactive linking (password prompt)

**The SQL Editor approach:**
- ✅ Works 100% reliably
- ✅ Takes only 2 minutes
- ✅ No password or connection issues
- ✅ Standard way to set up schemas

## Step-by-Step Instructions

### 1. Open SQL Editor

The browser should have opened. If not, go to:
```
https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql
```

### 2. Create New Query

- Click the **"New query"** button (top right of the SQL Editor)

### 3. Copy Schema SQL

- Open `database/schema.sql` in VS Code (in your project)
- **Select ALL** text (Ctrl+A)
- **Copy** (Ctrl+C)

### 4. Paste and Run

- Paste into the SQL Editor (Ctrl+V)
- Click the **"Run"** button (or press Ctrl+Enter)

### 5. Wait for Success

- Should complete in 5-10 seconds
- You'll see: "Success. No rows returned"

### 6. Verify

- Go to "Table Editor" in the left sidebar
- You should see:
  - ✅ `user_profiles`
  - ✅ `pv_cases`

Or run:
```powershell
python final_setup_check.py
```

## That's It!

The schema is now set up. This is actually the **recommended approach** for one-time schema setup in Supabase.

**Total time**: ~2 minutes

---

**Note**: The automated scripts we created will work in the future once network/DNS issues are resolved, but for initial setup, SQL Editor is fastest!

