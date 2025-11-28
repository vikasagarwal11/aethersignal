# What Data Is Saved - Current vs. Extended Schema

## Current State (What's Already Saved)

### ✅ **Currently Saved in Database:**

1. **User Profiles** (`user_profiles` table)
   - User information (email, name, organization, role)
   - ✅ Persisted across sessions
   - ✅ Company-isolated

2. **PV Case Data** (`pv_cases` table)
   - All uploaded pharmacovigilance case data
   - ✅ Persisted across sessions
   - ✅ Company-isolated

### ❌ **Currently NOT Saved in Database:**

1. **Saved Queries**
   - Stored in: `st.session_state.saved_queries`
   - ❌ Lost when session ends
   - ❌ Not shared across devices
   - ❌ Not company-isolated in database

2. **Query History**
   - Stored in: `st.session_state.query_history`
   - ❌ Lost when session ends
   - ❌ Only last 20 queries kept (in session)
   - ❌ Not persisted

3. **Activity Logs**
   - Stored in: `analytics/audit_log.jsonl` (local file)
   - ❌ File-based (not in database)
   - ❌ Not accessible via Supabase
   - ❌ Not multi-tenant

---

## Extended Schema (What You Can Add)

I've created `database/schema_extensions.sql` that adds:

### ✅ **New Tables to Add:**

1. **`saved_queries` Table**
   - Stores all saved queries permanently
   - ✅ Persisted across sessions
   - ✅ Company-isolated
   - ✅ Shared within company
   - Fields: name, query_text, filters, usage_count, last_used_at

2. **`query_history` Table**
   - Stores all executed queries
   - ✅ Complete history (not just last 20)
   - ✅ Company-isolated
   - ✅ Shared within company
   - Fields: query_text, filters, results_count, execution_time

3. **`activity_logs` Table**
   - Comprehensive activity tracking
   - ✅ All user actions logged
   - ✅ Company-isolated
   - ✅ Replaces file-based audit logs
   - Fields: event_type, event_details, ip_address, user_agent

---

## How Multi-Tenant Isolation Works

**Same pattern as PV cases:**

```
Company ABC:
  ├── User 1's saved queries → Visible to User 1 and User 2
  ├── User 2's saved queries → Visible to User 1 and User 2
  ├── User 1's query history → Visible to User 1 and User 2
  └── User 2's query history → Visible to User 1 and User 2

Company XYZ:
  ├── User 3's saved queries → Visible to User 3 and User 4
  ├── User 4's saved queries → Visible to User 3 and User 4
  ├── User 3's query history → Visible to User 3 and User 4
  └── User 4's query history → Visible to User 3 and User 4

Isolation:
  ❌ ABC users CANNOT see XYZ queries/history
  ❌ XYZ users CANNOT see ABC queries/history
```

---

## To Enable Full Data Persistence

**Option 1: Run Schema Extensions (Recommended)**

1. Open Supabase SQL Editor:
   ```
   https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql
   ```

2. Open `database/schema_extensions.sql`

3. Copy all contents and paste into SQL Editor

4. Click "Run"

5. This will add 3 new tables with full RLS policies

**Option 2: I Can Run It For You**

Just say "run the schema extensions" and I'll execute it!

---

## After Running Extensions

Once the extended schema is in place:

✅ **Saved queries** → Stored in database, persistent
✅ **Query history** → Complete history, persistent
✅ **Activity logs** → All actions logged, persistent
✅ **All data** → Company-isolated with RLS

Everything will be saved and accessible across:
- Different browsers
- Different devices
- After logout/login
- Across sessions

**Would you like me to run the schema extensions now?**

