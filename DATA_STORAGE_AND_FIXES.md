# Data Storage & Recent Fixes

## 📊 **Where Your Data is Stored**

### **Database Table: `pv_cases`**

All uploaded pharmacovigilance data is stored in the **`pv_cases`** table in your Supabase database.

**Table Details:**
- **Location:** Supabase PostgreSQL database
- **Schema:** `public.pv_cases`
- **Multi-tenant:** Yes - data is isolated by `organization` and `user_id`
- **Row-Level Security (RLS):** Enabled - users can only see their own company's data

**What Gets Stored:**
- All case data (drug_name, reaction, dates, demographics, etc.)
- Original raw data in JSONB field (`raw_data`)
- User ID (`user_id`) - who uploaded it
- Organization (`organization`) - company it belongs to
- Source identifier (`source`) - e.g., "FAERS", "E2B", etc.
- Timestamps (`created_at`, `updated_at`)

**Storage Function:**
- **File:** `src/pv_storage.py`
- **Function:** `store_pv_data()`
- **Batch Size:** 1,000 records per batch (for large uploads)

**Example:**
```python
# Data is automatically stored when you upload files (if authenticated)
store_pv_data(normalized_df, user_id, organization, source="FAERS")
```

---

## ✅ **Fixes Applied**

### **1. Fixed Syntax Error (Line 955)**
**Problem:** Duplicate schema mapper section causing syntax error
**Solution:** Removed redundant schema mapper code that was executing after data was already processed
**File:** `src/ui/upload_section.py`
**Status:** ✅ Fixed

### **2. Fixed `validate_filters()` TypeError**
**Problem:** Function was being called with 2 arguments but only accepts 1
```
TypeError: validate_filters() takes 1 positional argument but 2 were given
```
**Solution:** Removed the second argument (`normalized_df`) from the function call
**File:** `src/ui/query_interface.py` (line 327)
**Changed from:**
```python
is_valid, error_msg = nl_query_parser.validate_filters(filters, normalized_df)
```
**Changed to:**
```python
is_valid, error_msg = nl_query_parser.validate_filters(filters)
```
**Status:** ✅ Fixed

### **3. Fixed Query Suggestion Display**
**Problem:** "Did you mean" suggestion was showing even when the suggested query was identical to the user's input (e.g., "are there any cases for dupixent?" → "are there any cases for dupixent?")
**Solution:** Added check to only show suggestion if the corrected query is different from the original
**File:** `src/ui/query_interface.py` (lines 300-307)
**Changed from:**
```python
if suggestions:
    corrected = get_corrected_query(working_query, suggestions)
    working_query = corrected
    st.info(f"Did you mean: **{corrected}**")
```
**Changed to:**
```python
if suggestions:
    corrected = get_corrected_query(working_query, suggestions)
    # Only show suggestion if it's different from the original
    if corrected.strip().lower() != working_query.strip().lower():
        working_query = corrected
        st.info(f"Did you mean: **{corrected}**")
    else:
        # Correction resulted in same query - don't show or apply
        applied_corrections = None
```
**Status:** ✅ Fixed

---

## 📝 **Summary**

All three issues have been resolved:

1. ✅ Syntax error removed (duplicate code section)
2. ✅ `validate_filters()` TypeError fixed (removed extra argument)
3. ✅ Query suggestion only shows when actually different

Your application should now:
- Load without syntax errors
- Execute queries without TypeError
- Only show "Did you mean" suggestions when they provide value

---

## 🗄️ **Database Structure**

**Table: `pv_cases`**
```sql
CREATE TABLE pv_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    organization TEXT NOT NULL,
    source TEXT DEFAULT 'FAERS',
    case_id TEXT,
    drug_name TEXT,
    reaction TEXT,
    -- ... other fields ...
    raw_data JSONB,  -- Complete original data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Access:** Data is automatically loaded from this table when you log in (if data was previously saved).

