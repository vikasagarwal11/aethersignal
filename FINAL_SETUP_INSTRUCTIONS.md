# Final Setup Instructions - Schema Execution

## Current Status

✅ **Environment configured**:
- `.env` file has: `SUPABASE_DB_PASSWORD=Hsgbu@118811`
- Schema file ready: `database/schema.sql`
- Migration file ready: `supabase/migrations/20251127230449_initial_schema.sql`

❌ **Automated connection failing**:
- DNS/network configuration issues preventing direct PostgreSQL connection
- Multiple connection methods tested but blocked by network

## ✅ **RECOMMENDED: SQL Editor Approach (2 Minutes)**

This is the **fastest and most reliable** method - no password needed!

### Steps:

1. **Open SQL Editor** (browser should open automatically):
   ```
   https://supabase.com/dashboard/project/scrksfxnkxmvvdzwmqnc/sql
   ```

2. **Click "New query"** button (top right)

3. **Open schema file**:
   - In VS Code: Open `database/schema.sql`
   - Select ALL (Ctrl+A)
   - Copy (Ctrl+C)

4. **Paste into SQL Editor**:
   - Paste (Ctrl+V) into the SQL Editor

5. **Run the query**:
   - Click "Run" button OR
   - Press Ctrl+Enter

6. **Wait for success**:
   - Should complete in 5-10 seconds
   - You'll see "Success. No rows returned" message

7. **Verify tables were created**:
   - Go to "Table Editor" in left sidebar
   - You should see:
     - ✅ `user_profiles`
     - ✅ `pv_cases`

8. **Run verification**:
   ```powershell
   python final_setup_check.py
   ```

## After Schema Execution

Once tables are created, your database is ready! Next steps:

1. **Test the application**:
   ```powershell
   streamlit run app.py
   ```

2. **Test registration**:
   - Create a new account
   - Verify profile creation works

3. **Test data upload**:
   - Upload FAERS data
   - Verify it's stored in database

## Notes

- The `.env` file has the password saved (`SUPABASE_DB_PASSWORD=Hsgbu@118811`)
- If the network/DNS issues are resolved later, automated scripts will work
- The SQL Editor approach is actually faster than troubleshooting connection issues!

**Total time**: ~2 minutes with SQL Editor approach.

