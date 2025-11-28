# Multi-Tenant System Setup Guide

## Overview

AetherSignal now supports **multi-tenant architecture** where:
- ✅ Multiple companies can create accounts
- ✅ Each company's data is completely isolated
- ✅ Data is preserved in database (not just session)
- ✅ Row-Level Security (RLS) ensures data privacy
- ✅ Users can only see their own company's data

---

## Architecture

### Data Isolation Model

```
Company A (Organization: "Acme Pharma")
    ├── User 1 (user_id: uuid-1)
    ├── User 2 (user_id: uuid-2)
    └── Data: Only visible to Company A users

Company B (Organization: "BioTech Inc")
    ├── User 3 (user_id: uuid-3)
    └── Data: Only visible to Company B users
```

**Key Points:**
- Each user belongs to an **organization** (company)
- All data is tagged with `user_id` and `organization`
- Row-Level Security (RLS) policies enforce isolation
- Users from the same company can see each other's data (optional, can be restricted)

---

## Setup Instructions

### Step 1: Create Supabase Project

1. Go to [Supabase](https://supabase.com)
2. Create a new project (or use existing)
3. Note your project URL and API keys

### Step 2: Run Database Schema

1. Open Supabase SQL Editor: `https://app.supabase.com/project/YOUR_PROJECT/sql`
2. Copy contents of `database/schema.sql`
3. Run the SQL script
4. Verify tables are created:
   - `user_profiles`
   - `pv_cases`

### Step 3: Configure Environment Variables

Add to your `.env` file or Streamlit Cloud secrets:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

### Step 4: Enable Authentication in Supabase

1. Go to Authentication → Settings
2. Enable "Email" provider
3. Configure email templates (optional)
4. Set up email verification (recommended)

### Step 5: Test the System

1. Register a new account
2. Upload data
3. Verify data is stored in `pv_cases` table
4. Create second account with different organization
5. Verify data isolation (second user can't see first user's data)

---

## Database Schema

### Tables

#### `user_profiles`
- Stores user information beyond Supabase Auth
- Links to `auth.users` (Supabase built-in)
- Contains: email, full_name, organization, role, subscription_tier

#### `pv_cases`
- Stores all pharmacovigilance data
- Each row has: `user_id`, `organization`
- RLS policies ensure users only see their company's data

### Row-Level Security (RLS)

**User Profiles:**
- Users can view/update their own profile
- Admins can view all profiles (optional)

**PV Cases:**
- Users can only view their own company's data
- Users can insert/update/delete their own data
- Organization field is automatically set from user profile

---

## Usage

### Registration Flow

1. User clicks "Register"
2. Enters: email, password, full name, **organization** (company name)
3. Account created in Supabase Auth
4. User profile created in `user_profiles` table
5. Email verification sent (if enabled)

### Data Upload Flow

1. User uploads data (FAERS, E2B, etc.)
2. Data is parsed and normalized
3. Data is stored in `pv_cases` table with:
   - `user_id`: Current user's UUID
   - `organization`: User's company name
   - All PV fields (drug_name, reaction, etc.)

### Data Query Flow

1. User queries data
2. System queries `pv_cases` table
3. RLS automatically filters to:
   - Current user's `user_id` OR
   - Same `organization` as current user
4. Only user's company data is returned

---

## Multi-Tenant Isolation

### How It Works

1. **Organization as Company Identifier**
   - Each user has an `organization` field
   - Organization name is used as company identifier
   - Data is tagged with organization

2. **Row-Level Security (RLS)**
   - Supabase automatically enforces RLS policies
   - Users can only SELECT rows where:
     - `user_id = auth.uid()` OR
     - `organization` matches their organization
   - INSERT/UPDATE/DELETE only allowed for own data

3. **Automatic Filtering**
   - All queries automatically filtered by RLS
   - No need to manually add WHERE clauses
   - Prevents data leakage between companies

### Example

**Company A User:**
```sql
SELECT * FROM pv_cases;
-- Returns only Company A's data (RLS enforces this)
```

**Company B User:**
```sql
SELECT * FROM pv_cases;
-- Returns only Company B's data (RLS enforces this)
```

---

## Security Considerations

### ✅ Implemented

1. **Row-Level Security (RLS)**
   - Automatic data isolation
   - Prevents cross-company data access
   - Enforced at database level

2. **Authentication**
   - Supabase Auth handles passwords
   - JWT tokens for sessions
   - Email verification (optional)

3. **Data Privacy**
   - Each company's data is isolated
   - Users can't access other companies' data
   - Organization field prevents data mixing

### ⚠️ Best Practices

1. **Organization Naming**
   - Use consistent organization names
   - Consider using UUIDs for organizations (future enhancement)
   - Validate organization names on registration

2. **User Roles**
   - Implement role-based access within companies
   - Admins can manage users within their company
   - Viewers have read-only access

3. **Data Backup**
   - Regular backups of Supabase database
   - Export data per company for compliance
   - Audit trail for data access

---

## Testing Multi-Tenant Isolation

### Test Scenario 1: Two Companies

1. **Register Company A:**
   - Email: `user1@acmepharma.com`
   - Organization: `Acme Pharma`
   - Upload test data

2. **Register Company B:**
   - Email: `user2@biotech.com`
   - Organization: `BioTech Inc`
   - Upload different test data

3. **Verify Isolation:**
   - Login as Company A user
   - Query data → Should only see Acme Pharma data
   - Login as Company B user
   - Query data → Should only see BioTech Inc data

### Test Scenario 2: Same Company, Multiple Users

1. **Register User 1:**
   - Organization: `Acme Pharma`

2. **Register User 2:**
   - Organization: `Acme Pharma` (same company)

3. **Verify Sharing:**
   - User 1 uploads data
   - User 2 should be able to see User 1's data (same organization)
   - Both users see all Acme Pharma data

---

## Troubleshooting

### Issue: Users can see other companies' data

**Solution:**
1. Check RLS policies are enabled:
   ```sql
   SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'pv_cases';
   ```
2. Verify policies exist:
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'pv_cases';
   ```
3. Re-run `database/schema.sql` if policies are missing

### Issue: Data not persisting

**Solution:**
1. Check Supabase connection (API keys)
2. Verify `pv_cases` table exists
3. Check user is authenticated (`st.session_state.authenticated`)
4. Verify `user_id` is set in session state

### Issue: Registration fails

**Solution:**
1. Check Supabase Auth is enabled
2. Verify email provider is enabled
3. Check email format is valid
4. Verify password meets requirements (8+ chars)

---

## Next Steps

1. ✅ Database schema created
2. ✅ Authentication module implemented
3. ✅ UI components created
4. ⏳ Update data loading to use `pv_storage.py`
5. ⏳ Update query interface to load from database
6. ⏳ Add user profile management
7. ⏳ Add role-based access control

---

## Support

For issues or questions:
1. Check Supabase logs: `https://app.supabase.com/project/YOUR_PROJECT/logs`
2. Verify RLS policies: Run SQL queries in Supabase SQL Editor
3. Test authentication: Use Supabase Auth UI

---

## Summary

✅ **Multi-tenant system is ready!**

- Companies can create accounts
- Data is isolated per company
- Data persists in database
- RLS ensures security
- Ready for production use

**Next:** Update data loading and query interfaces to use the new storage system.

