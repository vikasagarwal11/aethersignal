# Duplicate Detection Workflow - Complete Analysis

## 🎯 Your Excellent Points

You're absolutely right! The workflow should be:

1. **FILE-LEVEL CHECK FIRST** (Fast, before processing)
   - Check filename + file size
   - Quick rejection if exact same file
   - Ask user: "Skip or re-upload?"

2. **DATA-LEVEL CHECK AFTER** (Sophisticated, after processing)
   - Use quantum/composite signatures
   - Catch duplicates from different files/sources
   - This is what we discussed

3. **DUPLICATE REPORTS** (Question: Save to DB?)
   - Generate report of duplicates found
   - Should we save this to database?
   - Or just show temporarily?

---

## 📋 Proposed Workflow

### **Phase 1: File-Level Duplicate Detection (BEFORE Processing)**

**Purpose:** Fast rejection of exact duplicate files

**Check:**
- Filename (exact match)
- File size (exact match in bytes)
- Optional: File hash (MD5/SHA256 for stronger detection)

**When:** Immediately after file upload, BEFORE processing starts

**User Experience:**
```
User uploads: "FAERS_Q1_2024.zip" (50.2 MB)

System checks:
✅ File "FAERS_Q1_2024.zip" (50.2 MB) was already uploaded on 2024-01-15

Options:
[Skip - Use existing data] [Re-upload anyway] [Cancel]
```

**Benefits:**
- ⚡ FAST (milliseconds)
- 💾 Saves processing time
- 🔒 Prevents accidental duplicate processing
- ✅ User has control

**Implementation:**
- Need to track file metadata in database:
  - `filename`
  - `file_size_bytes`
  - `file_hash` (optional, but more reliable)
  - `uploaded_at`
  - `user_id` + `organization`
  - `cases_count` (how many cases from this file)

---

### **Phase 2: Data-Level Duplicate Detection (AFTER Processing)**

**Purpose:** Catch duplicates even from different files/sources

**Check:**
- Composite signatures (case_id + age + sex + drug + reaction)
- Quantum hash matching
- Fuzzy matching (similar but not identical)
- Cross-source detection (FAERS vs E2B)

**When:** After data is processed and normalized

**User Experience:**
```
Processing complete: 1000 cases loaded

Data-level duplicate check:
✅ 950 new cases inserted
⚠️ 50 duplicates skipped (already in database)

Breakdown:
- 30 exact duplicates (same case_id)
- 20 near-duplicates (same patient/event, different case_id)
```

**Benefits:**
- 🎯 Catches duplicates across different files
- 🔍 Detects near-duplicates (same patient, different IDs)
- 📊 Cross-source duplicate detection
- ⚛️ Uses sophisticated quantum algorithms

**Implementation:**
- Use existing quantum duplicate detection logic
- Check composite signatures against database
- Skip inserting duplicates

---

### **Phase 3: Duplicate Report Generation (Question: Save to DB?)**

**Purpose:** Track and audit duplicate detection results

**Current State:**
- Duplicate detection results are shown in UI
- User can download CSV report
- **NOT saved to database**

**Your Question:**
> "If we need to generate a report for duplicate also or not. If yes, then we will end up saving that data back in database. Is this correct?"

---

## 💭 Analysis: Should Duplicate Reports Be Saved to Database?

### **Option A: Save Report Metadata Only (Recommended)**

**What to Save:**
- ✅ **Report metadata** (when detected, how many duplicates, method used)
- ✅ **Summary statistics** (total cases, duplicates, unique cases)
- ✅ **Action taken** (skipped, merged, user decision)
- ❌ **NOT the duplicate data itself** (that's already in `pv_cases` table)

**Database Table: `duplicate_detection_reports`**
```sql
CREATE TABLE duplicate_detection_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    organization TEXT NOT NULL,
    upload_session_id TEXT, -- Link to file upload session
    detection_date TIMESTAMP DEFAULT NOW(),
    total_cases INTEGER,
    new_cases INTEGER,
    duplicate_cases INTEGER,
    detection_method TEXT, -- 'file_level', 'composite_signature', 'quantum', 'hybrid'
    report_summary JSONB, -- Summary stats, duplicate groups, etc.
    action_taken TEXT, -- 'skipped', 'merged', 'user_review'
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Why This Makes Sense:**
- ✅ Audit trail for regulatory compliance
- ✅ Track duplicate patterns over time
- ✅ Performance monitoring (how often duplicates occur)
- ✅ Doesn't duplicate the actual case data
- ✅ Can regenerate detailed report from metadata + `pv_cases` table

**What NOT to Save:**
- ❌ Full duplicate records (already in `pv_cases`)
- ❌ Large CSV/Excel files (just metadata)
- ❌ Raw detection logs (too verbose)

---

### **Option B: Save Full Report (Not Recommended)**

**What to Save:**
- Full duplicate report as JSON/CSV
- All duplicate case details
- This would **duplicate data** already in `pv_cases`

**Why NOT Recommended:**
- ❌ Data duplication (same cases stored twice)
- ❌ Storage bloat (large files)
- ❌ Hard to keep in sync with `pv_cases` table
- ❌ Reports can be regenerated from `pv_cases` table

---

### **Option C: No Database Storage (Current Approach)**

**What Happens:**
- Report shown in UI only
- User can download CSV
- Nothing saved to database

**Pros:**
- ✅ Simple
- ✅ No storage overhead
- ✅ Privacy (no persistent tracking)

**Cons:**
- ❌ No audit trail
- ❌ Can't track duplicate patterns over time
- ❌ Regulatory compliance issues (pharma needs audit trails)
- ❌ Can't analyze: "How often do we see duplicates?"

---

## 🎯 Recommendation

### **Hybrid Approach (Best of All Worlds):**

1. **File-Level Check:**
   - Create `file_upload_history` table to track:
     - filename
     - file_size_bytes
     - file_hash (MD5)
     - upload_date
     - cases_count
     - user_id + organization

2. **Data-Level Check:**
   - Use composite signatures (quantum algorithms)
   - Skip duplicates during insert
   - Show summary to user

3. **Report Storage:**
   - Save **metadata only** to `duplicate_detection_reports` table
   - Summary statistics (not full data)
   - Link to upload session
   - Action taken
   - **Can regenerate full report from metadata + pv_cases table**

---

## 📊 Complete Workflow

```
┌─────────────────────────────────────────────────────────┐
│ STEP 1: File Upload                                     │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 2: File-Level Duplicate Check (FAST)              │
│ • Check filename + size in file_upload_history          │
│ • If match → Ask user: Skip or Re-upload?              │
│ • If no match → Continue to processing                 │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 3: Process File                                    │
│ • Parse, normalize, schema mapping                      │
│ • Creates normalized DataFrame                          │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 4: Data-Level Duplicate Check (SOPHISTICATED)     │
│ • Generate composite signatures (case_id + age + sex +  │
│   drug + reaction)                                      │
│ • Check against existing records in pv_cases            │
│ • Use quantum hash matching                             │
│ • Skip duplicates, insert only new cases                │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 5: Generate Report & Store Metadata                │
│ • Show summary: "X new, Y duplicates skipped"          │
│ • Save metadata to duplicate_detection_reports table    │
│ • Link to file_upload_history                           │
│ • User can view/download full report                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema Changes Needed

### **1. File Upload History Table**
```sql
CREATE TABLE file_upload_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    organization TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_hash TEXT, -- MD5 hash for stronger duplicate detection
    cases_count INTEGER,
    source TEXT DEFAULT 'FAERS',
    uploaded_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, organization, filename, file_size_bytes)
);
```

### **2. Duplicate Detection Reports Table**
```sql
CREATE TABLE duplicate_detection_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    organization TEXT NOT NULL,
    upload_session_id TEXT, -- Link to file_upload_history.id
    detection_date TIMESTAMP DEFAULT NOW(),
    
    -- Statistics
    total_cases INTEGER,
    new_cases INTEGER,
    duplicate_cases INTEGER,
    exact_duplicates INTEGER,
    near_duplicates INTEGER,
    
    -- Method used
    detection_method TEXT, -- 'file_level', 'composite', 'quantum', 'hybrid'
    
    -- Summary (JSONB for flexibility)
    report_summary JSONB, -- { duplicate_groups: [...], sources: [...] }
    
    -- Action taken
    action_taken TEXT, -- 'skipped', 'merged', 'user_review'
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## ✅ Answer to Your Question

> "If we need to generate a report for duplicate also or not. If yes, then we will end up saving that data back in database. Is this correct?"

**Answer:**

✅ **YES - Generate report, but NO - Don't save duplicate data itself**

**What to Save:**
- ✅ Report metadata (when, how many, method)
- ✅ Summary statistics (counts, breakdowns)
- ✅ Action taken (skipped/merged)

**What NOT to Save:**
- ❌ Duplicate case records (already in `pv_cases`)
- ❌ Full CSV/Excel files (can regenerate)

**Why This Is Correct:**
- Audit trail for compliance ✅
- Track patterns over time ✅
- No data duplication ✅
- Can regenerate full report from metadata + `pv_cases` ✅

---

## 🎯 Summary

1. **File-level check first** → Fast, user-friendly ✅
2. **Data-level check after** → Sophisticated, comprehensive ✅
3. **Save report metadata** → Audit trail, but no data duplication ✅

This gives you the best of all worlds: speed, accuracy, and compliance without bloat.

