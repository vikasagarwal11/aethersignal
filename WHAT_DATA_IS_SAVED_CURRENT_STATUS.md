# What Data Is Currently Saved - Complete Status Report

## ✅ **What IS Currently Saved in Database**

### 1. **Uploaded FAERS Data** ✅ **YES - SAVED**

**Location:** `pv_cases` table in Supabase

**When it happens:**
- User uploads FAERS files
- Data is parsed and normalized
- Automatically stored in `pv_cases` table with:
  - `user_id` - who uploaded it
  - `organization` - company it belongs to
  - All case data (drug_name, reaction, dates, etc.)
  - `raw_data` JSONB field - complete original data

**Code location:** `src/ui/upload_section.py` (lines 928-936)
```python
# Automatically stores data when user is authenticated
if is_authenticated() and normalized is not None:
    store_pv_data(normalized, user_id, organization, source)
```

**Status:** ✅ **Fully working** - Data persists across sessions

---

### 2. **User Profiles** ✅ **YES - SAVED**

**Location:** `user_profiles` table in Supabase

**What's saved:**
- User email, name
- Organization/company
- Role (admin, scientist, viewer)
- Subscription tier

**Status:** ✅ **Fully working** - Persists across sessions

---

## ❌ **What is NOT Currently Saved in Database**

### 3. **Generated PDF Reports** ❌ **NO - NOT SAVED**

**Current behavior:**
- PDF reports are **generated on-demand**
- User clicks "Download PDF Report"
- PDF is generated and **downloaded to user's computer**
- PDF is **NOT stored in database**
- Only an **audit log entry** is created (file-based)

**Where PDFs go:** User's Downloads folder (not in database)

**Code location:** `src/ui/results_display.py` (lines 2205-2210)
```python
pdf_bytes = pdf_report.build_pdf_report(pdf_summary)
st.download_button("Download PDF report", data=pdf_bytes, ...)
# PDF is only downloaded, not stored
```

**Status:** ❌ **Not saved in database** - Generated each time, not persisted

---

### 4. **Excel/CSV Exports** ❌ **NO - NOT SAVED**

**Current behavior:**
- Data can be exported to Excel/CSV
- Files are **downloaded to user's computer**
- **NOT stored in database**

**Status:** ❌ **Not saved in database** - Download only

---

### 5. **E2B XML Exports** ❌ **NO - NOT SAVED**

**Current behavior:**
- E2B(R3) XML files can be generated
- Files are **downloaded to user's computer**
- **NOT stored in database**

**Status:** ❌ **Not saved in database** - Download only

---

### 6. **Saved Queries** ❌ **NO - NOT SAVED**

**Current storage:** `st.session_state.saved_queries` (session memory)

**What happens:**
- Queries saved during session
- **Lost when browser is closed/refreshed**
- **NOT in database**

**Status:** ❌ **Session-only** - Not persisted

---

### 7. **Query History** ❌ **NO - NOT SAVED**

**Current storage:** `st.session_state.query_history` (session memory)

**What happens:**
- Last 20 queries stored in session
- **Lost when browser is closed/refreshed**
- **NOT in database**

**Status:** ❌ **Session-only** - Not persisted

---

### 8. **Activity Logs** ❌ **NO - NOT IN DATABASE**

**Current storage:** `analytics/audit_log.jsonl` (local file)

**What happens:**
- Activities logged to JSONL file
- **File-based, not in Supabase database**
- **Not multi-tenant**
- **Not accessible via Supabase**

**Status:** ❌ **File-based only** - Not in database

---

## 📊 **Summary Table**

| Data Type | Saved in Database? | Where Stored | Persists? |
|-----------|-------------------|--------------|-----------|
| **Uploaded FAERS Data** | ✅ YES | `pv_cases` table | ✅ Yes |
| **User Profiles** | ✅ YES | `user_profiles` table | ✅ Yes |
| **PDF Reports** | ❌ NO | User's Downloads folder | ❌ No |
| **Excel/CSV Exports** | ❌ NO | User's Downloads folder | ❌ No |
| **E2B XML Exports** | ❌ NO | User's Downloads folder | ❌ No |
| **Saved Queries** | ❌ NO | Session memory | ❌ No |
| **Query History** | ❌ NO | Session memory | ❌ No |
| **Activity Logs** | ❌ NO | Local JSONL file | ⚠️ File only |

---

## 🔍 **Details**

### Uploaded Data (FAERS Files)

**✅ Currently Working:**
- When a user uploads FAERS files
- Data is automatically stored in `pv_cases` table
- Includes all case information
- Tagged with `user_id` and `organization`
- **Persists across sessions**
- **Company-isolated** via RLS

**What gets saved:**
- All case data (drug_name, reaction, dates, etc.)
- Original raw data in JSONB field
- Source identifier (FAERS, E2B, etc.)
- User and organization tags

**Example:**
```
User uploads FAERS file → 1000 cases
→ All 1000 cases stored in pv_cases table
→ User logs out and logs back in
→ All 1000 cases are still there (loaded from database)
```

---

### Generated Reports (PDF/Excel)

**❌ Currently NOT Saved:**
- Reports are generated **on-demand**
- User downloads them to their computer
- Reports are **NOT stored in database**
- Each time user wants a report, it's generated fresh

**What this means:**
- If user generates a PDF report today
- That PDF is only on their computer
- Not accessible from another device
- Not accessible after deletion
- Would need to regenerate report to get it again

**Current workflow:**
```
User runs query → Generates PDF → Downloads to computer
→ PDF is NOT saved in database
→ User needs to regenerate if they want it again
```

---

## 🎯 **What You Asked About**

**Question:** "Are all the data been loaded by the user, and the reports etc. saved?"

**Answer:**
- ✅ **Uploaded data (FAERS files):** YES - Saved in database
- ❌ **Generated reports (PDF/Excel):** NO - Not saved in database
- ❌ **Saved queries:** NO - Not saved in database
- ❌ **Query history:** NO - Not saved in database

---

## 📝 **Current Architecture**

```
┌─────────────────────────────────────┐
│         USER ACTIONS                │
└─────────────────────────────────────┘
            │
            ├─── Upload FAERS Files
            │    └─── ✅ SAVED → pv_cases table
            │
            ├─── Generate PDF Report
            │    └─── ❌ NOT SAVED → Downloads folder only
            │
            ├─── Export Excel/CSV
            │    └─── ❌ NOT SAVED → Downloads folder only
            │
            ├─── Save Query
            │    └─── ❌ NOT SAVED → Session memory only
            │
            └─── Query History
                 └─── ❌ NOT SAVED → Session memory only
```

---

## 🔄 **What Happens on Next Login**

**Will be available:**
- ✅ All previously uploaded FAERS data (from `pv_cases` table)
- ✅ User profile information

**Will NOT be available:**
- ❌ Previously generated PDF reports (not saved)
- ❌ Previously saved queries (lost on logout)
- ❌ Query history (lost on logout)
- ❌ Downloaded Excel/CSV files (on user's computer only)

---

## 💡 **To Save Everything**

I've already created `database/schema_extensions.sql` that would add:
1. `saved_queries` table - For persistent saved queries
2. `query_history` table - For complete query history
3. `activity_logs` table - For activity logs (replaces file-based)
4. `reports` table (could add) - For storing generated PDF reports

**But currently, only uploaded FAERS data and user profiles are saved in the database.**

---

This is the current state - no changes made, just showing you what's saved and what's not.

