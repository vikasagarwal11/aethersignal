# Comprehensive Performance Optimization Analysis
## File Upload Tracking, Background Processing & Continuous Learning

**Date:** December 2024  
**Purpose:** Analyze and design architecture for:
- File upload history tracking
- Background processing (non-blocking uploads)
- Pre-calculated statistics storage
- Background assessment jobs
- Continuous learning from user queries

---

## 📊 Current State Assessment

### ✅ What Exists Now:

1. **`pv_cases` Table** - Stores individual case records
   - ✅ Has `user_id`, `organization`, `source`, `created_at`
   - ❌ No file-level tracking (groups by date/source only)
   - ❌ No file metadata (filename, size, hash)

2. **`list_available_datasets()` Function** (`src/pv_storage.py:453`)
   - ✅ Groups datasets by upload date + source
   - ❌ Cannot distinguish same file uploaded twice on same day
   - ❌ No filename or file size tracking

3. **Database Storage** (`src/pv_storage.py:88`)
   - ✅ Stores cases in `pv_cases` table
   - ❌ **Blocking** - User waits for entire upload to complete
   - ❌ No file-level metadata stored
   - ❌ Stats calculated on-demand (slow for queries)

4. **Query Processing** (`src/ui/query_interface.py`)
   - ✅ Real-time query processing
   - ❌ Calculates stats every time (no caching)
   - ❌ Slow for repeated queries

5. **No Background Processing**
   - ❌ Everything is synchronous
   - ❌ No job queue
   - ❌ No background workers

---

### 📋 Complete Database Inventory

**See:** `DATABASE_INVENTORY_AND_CURRENT_STATE.md` for full details

#### **Active Tables:**
- ✅ `user_profiles` - User information (used)
- ✅ `pv_cases` - Case data storage (used)
- ✅ `tenants` - Tenant registry (used)
- ✅ `user_tenants` - User-tenant mapping (used)

#### **Views:**
- ✅ `user_data_summary` - Aggregated stats per user/org (VIEW, not table)
  - **Limitation:** Aggregates ALL data, cannot distinguish individual file uploads
  - Shows: total_cases, unique_drugs, unique_reactions, first_upload, last_upload

#### **Tables That Exist But Are NOT Used:**
- ❌ `activity_logs` - Table exists but **NOT WRITTEN TO**
  - Current logging: File-based (`analytics/audit_log.jsonl`)
  - **Fix Needed:** Update `src/audit_trail.py` to write to database
  
- ⚠️ `saved_queries` - Table exists but **NOT WRITTEN TO**
  - Current: Stored in session state only
  - **Fix Needed:** Write saved queries to database
  
- ⚠️ `query_history` - Table exists but **NOT WRITTEN TO**
  - Current: Stored in session state only
  - **Fix Needed:** Write query history to database

#### **Missing Tables (Need to Create):**
- ❌ `file_upload_history` - Track individual file uploads
- ❌ `pre_calculated_stats` - Cache common query results
- ❌ `background_jobs` - Job queue for background processing
- ❌ `query_learning` - Learn from user queries

#### **Index Status:**
**Current Indexes (Good):**
- Basic indexes on `pv_cases`: user_id, organization, drug_name, reaction, case_id, source, created_at
- Composite indexes: user+drug, user+reaction

**Missing Critical Indexes:**
- ❌ `idx_pv_cases_user_drug_reaction` - For common drug-event queries
- ❌ `idx_pv_cases_created_at_org` - For dataset listing performance
- ❌ `idx_pv_cases_event_date` - For trend analysis
- ❌ `idx_pv_cases_serious_outcome` - For serious case filtering

**Performance Impact:**
- Dataset listing: Currently 5-10 seconds → Could be <500ms with proper indexes
- Common queries: Currently 500ms-2s → Could be 100-500ms with composite index

---

### ⚠️ Critical Discovery: Existing Tables Not Being Used

#### **1. `activity_logs` Table - EXISTS BUT NOT USED**
- ✅ **Table exists** in database (`database/schema_extensions.sql`)
- ✅ **RLS policies** configured
- ✅ **Indexes** created
- ❌ **NOT WRITTEN TO** - Current logging writes to FILE only
- **Current Implementation:** `src/audit_trail.py` → writes to `analytics/audit_log.jsonl`
- **Impact:** No database-based audit trail, compliance concerns
- **Fix Needed:** Update audit logging to write to database table

#### **2. `saved_queries` Table - EXISTS BUT NOT USED**
- ✅ Table exists with proper schema
- ❌ NOT written to - queries stored in session state only
- **Impact:** Saved queries lost on logout

#### **3. `query_history` Table - EXISTS BUT NOT USED**
- ✅ Table exists with proper schema  
- ❌ NOT written to - history stored in session state only
- **Impact:** Query history lost on logout

---

## 🎯 Your Requirements (Summarized)

### **1. File Upload History Table**
- Track each file upload separately
- Store: filename, file size, upload timestamp
- High-level stats: total cases, # events, # drugs, etc.
- Enable duplicate file detection (same filename + size)

### **2. Fast Upload (Non-Blocking)**
- Upload data to buffer immediately
- Dump to database in background (parallel thread)
- User can continue using app immediately
- No UI delays

### **3. Background Statistics Calculation**
- Calculate stats in background during upload
- Store pre-calculated stats in database
- Query stats directly from stored values (fast)
- Keep in sync with new data

### **4. Background Assessment Jobs**
- Run automatic assessments during low peak times
- Pre-compute common queries
- Keep statistics fresh

### **5. Continuous Learning**
- Learn from user queries
- Identify query patterns
- Automatically run similar queries in background
- Pre-compute likely needed results

---

## 🏗️ Proposed Architecture

### **Phase 1: File Upload History & Metadata Tracking**

#### **1.1 New Database Tables**

```sql
-- ============================================================================
-- FILE UPLOAD HISTORY TABLE
-- ============================================================================
-- Tracks each file upload with metadata and high-level statistics

CREATE TABLE IF NOT EXISTS file_upload_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization TEXT NOT NULL,
    
    -- File metadata
    filename TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_hash_md5 TEXT, -- MD5 hash for duplicate detection
    file_type TEXT, -- 'FAERS', 'E2B', 'CSV', 'Excel', etc.
    
    -- Upload metadata
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    upload_status TEXT DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    
    -- High-level statistics (calculated in background)
    total_cases INTEGER,
    total_events INTEGER, -- Number of unique reactions/events
    total_drugs INTEGER, -- Number of unique drugs
    total_serious_cases INTEGER,
    total_fatal_cases INTEGER,
    
    -- Date range of cases
    earliest_date DATE,
    latest_date DATE,
    
    -- Source-specific metadata
    source TEXT DEFAULT 'FAERS',
    
    -- Processing metadata
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT, -- Error message if failed
    
    -- Stats calculation status
    stats_calculated_at TIMESTAMP WITH TIME ZONE,
    stats_status TEXT DEFAULT 'pending', -- 'pending', 'calculating', 'completed', 'failed'
    
    -- JSONB for flexible metadata
    metadata JSONB, -- Additional file-specific metadata
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint: Same file (filename + size) can be uploaded multiple times
    -- but we track each upload separately
    UNIQUE(user_id, organization, filename, file_size_bytes, uploaded_at)
);

-- Indexes for fast duplicate detection
CREATE INDEX IF NOT EXISTS idx_file_upload_user_id ON file_upload_history(user_id);
CREATE INDEX IF NOT EXISTS idx_file_upload_organization ON file_upload_history(organization);
CREATE INDEX IF NOT EXISTS idx_file_upload_filename_size ON file_upload_history(user_id, organization, filename, file_size_bytes);
CREATE INDEX IF NOT EXISTS idx_file_upload_uploaded_at ON file_upload_history(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_file_upload_status ON file_upload_history(upload_status);

-- ============================================================================
-- PRE-CALCULATED STATISTICS TABLE
-- ============================================================================
-- Stores commonly queried statistics to avoid recalculation

CREATE TABLE IF NOT EXISTS pre_calculated_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization TEXT NOT NULL,
    
    -- What this stat represents
    stat_type TEXT NOT NULL, -- 'top_drugs', 'top_reactions', 'trends', 'drug_event_matrix', etc.
    stat_key TEXT NOT NULL, -- Composite key identifying this stat (e.g., 'drug:Dupixent', 'reaction:Death')
    
    -- Data scope
    file_upload_ids UUID[], -- Which file uploads this stat is based on
    date_range_start DATE,
    date_range_end DATE,
    
    -- The calculated statistics (stored as JSONB for flexibility)
    stat_data JSONB NOT NULL, -- Actual statistics data
    
    -- Metadata
    calculation_method TEXT, -- How this was calculated
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- When this stat becomes stale
    
    -- Version tracking
    version INTEGER DEFAULT 1, -- Increment when recalculated
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint: One stat per user/org/type/key combination
    UNIQUE(user_id, organization, stat_type, stat_key)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_precalc_stats_user_id ON pre_calculated_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_precalc_stats_organization ON pre_calculated_stats(organization);
CREATE INDEX IF NOT EXISTS idx_precalc_stats_type_key ON pre_calculated_stats(stat_type, stat_key);
CREATE INDEX IF NOT EXISTS idx_precalc_stats_expires ON pre_calculated_stats(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- BACKGROUND JOB QUEUE TABLE
-- ============================================================================
-- Tracks background processing jobs

CREATE TABLE IF NOT EXISTS background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    organization TEXT,
    
    -- Job metadata
    job_type TEXT NOT NULL, -- 'file_upload', 'stats_calculation', 'query_learning', 'assessment'
    job_status TEXT DEFAULT 'queued', -- 'queued', 'running', 'completed', 'failed', 'cancelled'
    
    -- Job input/output
    job_input JSONB, -- Job parameters (file_id, query, etc.)
    job_result JSONB, -- Job results
    job_error TEXT, -- Error message if failed
    
    -- Scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Priority and retry
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Worker tracking
    worker_id TEXT, -- Which worker is processing this
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_bg_jobs_status ON background_jobs(job_status, priority, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_bg_jobs_user_id ON background_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_bg_jobs_type ON background_jobs(job_type);

-- ============================================================================
-- QUERY LEARNING TABLE
-- ============================================================================
-- Tracks user queries to learn patterns and pre-compute results

CREATE TABLE IF NOT EXISTS query_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    organization TEXT,
    
    -- Query information
    query_text TEXT NOT NULL,
    query_filters JSONB, -- Extracted filters
    query_type TEXT, -- 'drug_search', 'reaction_search', 'trend_analysis', etc.
    
    -- Pattern matching
    query_pattern_hash TEXT, -- Hash of query pattern for grouping similar queries
    similar_query_ids UUID[], -- Other similar queries
    
    -- Usage statistics
    execution_count INTEGER DEFAULT 1,
    last_executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    average_execution_time_ms INTEGER,
    
    -- Pre-computation
    should_precompute BOOLEAN DEFAULT FALSE, -- Whether to pre-compute results
    precomputed_result JSONB, -- Pre-computed result (if applicable)
    precomputed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_query_learning_pattern ON query_learning(query_pattern_hash);
CREATE INDEX IF NOT EXISTS idx_query_learning_precompute ON query_learning(should_precompute, organization);
CREATE INDEX IF NOT EXISTS idx_query_learning_frequency ON query_learning(execution_count DESC, last_executed_at DESC);
```

---

### **Phase 2: Upload Flow (Fast & Non-Blocking)**

#### **2.1 Upload Process Flow**

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: User Uploads File                                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Check for Duplicate File (Fast - <1 second)         │
│ - Query: SELECT * FROM file_upload_history                  │
│          WHERE filename = ? AND file_size_bytes = ?         │
│                                                             │
│ IF duplicate found:                                         │
│   → Show warning: "This file was uploaded on [DATE]"        │
│   → User can: Skip / Re-upload anyway                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Create Upload Record (Immediate - <100ms)           │
│ - Insert into file_upload_history                           │
│ - Status: 'processing'                                      │
│ - Return upload_id immediately                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Load File to Memory Buffer (Fast - 2-5 seconds)     │
│ - Parse file (CSV/Excel/FAERS)                              │
│ - Normalize data                                            │
│ - Store in session_state.normalized_data                    │
│                                                             │
│ → User can NOW use the app immediately! ✅                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Queue Background Jobs (Immediate - <100ms)          │
│ - Job 1: Database Storage (background thread)               │
│ - Job 2: Statistics Calculation (background thread)         │
│                                                             │
│ → Insert into background_jobs table                         │
│ → Return immediately (non-blocking)                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Background Worker Processes Jobs                    │
│                                                             │
│ Worker 1: Database Storage                                  │
│   - Read from session buffer or file                        │
│   - Insert into pv_cases table (chunked)                    │
│   - Update file_upload_history.status = 'completed'         │
│                                                             │
│ Worker 2: Statistics Calculation                            │
│   - Calculate high-level stats                              │
│   - Update file_upload_history with stats                   │
│   - Create pre_calculated_stats entries                     │
└─────────────────────────────────────────────────────────────┘
```

#### **2.2 Code Implementation**

```python
# src/pv_storage.py

def check_duplicate_file(user_id: str, organization: str, filename: str, file_size_bytes: int) -> Optional[Dict]:
    """
    Check if file with same filename + size was uploaded before.
    Returns duplicate file info if found, None otherwise.
    """
    sb = get_supabase_db()
    if not sb:
        return None
    
    query = sb.table("file_upload_history").select("*")
    query = query.eq("user_id", user_id)
    query = query.eq("organization", organization)
    query = query.eq("filename", filename)
    query = query.eq("file_size_bytes", file_size_bytes)
    query = query.order("uploaded_at", desc=True)
    query = query.limit(1)
    
    response = query.execute()
    
    if response.data:
        return response.data[0]
    return None


def create_file_upload_record(
    user_id: str,
    organization: str,
    filename: str,
    file_size_bytes: int,
    file_type: str = "FAERS",
    source: str = "FAERS"
) -> str:
    """
    Create file upload history record.
    Returns upload_id immediately (before processing).
    """
    sb = get_supabase_db()
    if not sb:
        raise Exception("Database not available")
    
    # Calculate file hash (optional, for stronger duplicate detection)
    import hashlib
    file_hash = None  # Would calculate from file content
    
    record = {
        "user_id": user_id,
        "organization": organization,
        "filename": filename,
        "file_size_bytes": file_size_bytes,
        "file_hash_md5": file_hash,
        "file_type": file_type,
        "source": source,
        "upload_status": "processing",
        "stats_status": "pending",
        "processing_started_at": datetime.now().isoformat()
    }
    
    response = sb.table("file_upload_history").insert(record).execute()
    
    if response.data:
        return response.data[0]["id"]
    raise Exception("Failed to create upload record")


def queue_background_jobs(upload_id: str, user_id: str, organization: str, df: pd.DataFrame):
    """
    Queue background jobs for database storage and stats calculation.
    Returns immediately (non-blocking).
    """
    sb = get_supabase_db()
    if not sb:
        return
    
    # Job 1: Database Storage
    storage_job = {
        "user_id": user_id,
        "organization": organization,
        "job_type": "file_upload",
        "job_status": "queued",
        "job_input": {
            "upload_id": upload_id,
            "dataframe_size": len(df),
            "columns": list(df.columns)
        },
        "priority": 3  # Medium priority
    }
    
    # Job 2: Statistics Calculation
    stats_job = {
        "user_id": user_id,
        "organization": organization,
        "job_type": "stats_calculation",
        "job_status": "queued",
        "job_input": {
            "upload_id": upload_id,
            "depends_on_job_type": "file_upload"
        },
        "priority": 5  # Lower priority (runs after storage)
    }
    
    sb.table("background_jobs").insert([storage_job, stats_job]).execute()


def store_pv_data_async(df: pd.DataFrame, upload_id: str, user_id: str, organization: str, source: str):
    """
    Store PV data in background thread (non-blocking).
    This is called from background worker, not directly from UI.
    """
    # This runs in background worker thread
    try:
        # Update job status to 'running'
        update_job_status(upload_id, "file_upload", "running")
        
        # Store data in chunks (existing logic from store_pv_data)
        # ... existing storage logic ...
        
        # Update file_upload_history
        update_upload_status(upload_id, "completed", total_cases=len(df))
        
        # Mark job as completed
        update_job_status(upload_id, "file_upload", "completed")
        
    except Exception as e:
        update_upload_status(upload_id, "failed", error=str(e))
        update_job_status(upload_id, "file_upload", "failed", error=str(e))


def calculate_stats_background(upload_id: str, user_id: str, organization: str, df: pd.DataFrame):
    """
    Calculate high-level statistics in background.
    Stores results in file_upload_history and pre_calculated_stats.
    """
    try:
        update_job_status(upload_id, "stats_calculation", "running")
        
        # Calculate statistics
        stats = {
            "total_cases": len(df),
            "total_events": df['reaction'].nunique() if 'reaction' in df.columns else 0,
            "total_drugs": df['drug_name'].nunique() if 'drug_name' in df.columns else 0,
            "total_serious_cases": len(df[df.get('serious', False)]) if 'serious' in df.columns else 0,
            "total_fatal_cases": len(df[df.get('outcome', '').str.contains('Death', case=False, na=False)]) if 'outcome' in df.columns else 0,
            "earliest_date": df['event_date'].min() if 'event_date' in df.columns else None,
            "latest_date": df['event_date'].max() if 'event_date' in df.columns else None,
        }
        
        # Update file_upload_history
        sb = get_supabase_db()
        sb.table("file_upload_history").update({
            **stats,
            "stats_status": "completed",
            "stats_calculated_at": datetime.now().isoformat()
        }).eq("id", upload_id).execute()
        
        # Create pre_calculated_stats entries
        # ... (detailed in next section)
        
        update_job_status(upload_id, "stats_calculation", "completed")
        
    except Exception as e:
        update_job_status(upload_id, "stats_calculation", "failed", error=str(e))
```

---

### **Phase 3: Pre-Calculated Statistics**

#### **3.1 Common Statistics to Pre-Calculate**

1. **Top Drugs** (most reported)
2. **Top Reactions** (most reported)
3. **Drug-Event Matrix** (PRR/ROR for common combinations)
4. **Trend Data** (monthly case counts)
5. **Demographics** (age/sex/country distributions)
6. **Seriousness Breakdown** (serious vs non-serious)
7. **Outcome Distribution** (fatal, hospitalization, etc.)

#### **3.2 Usage in Queries**

```python
# src/pv_storage.py

def get_precalculated_stat(user_id: str, organization: str, stat_type: str, stat_key: str) -> Optional[Dict]:
    """
    Get pre-calculated statistic if available and fresh.
    Returns None if not found or expired.
    """
    sb = get_supabase_db()
    if not sb:
        return None
    
    query = sb.table("pre_calculated_stats").select("*")
    query = query.eq("user_id", user_id)
    query = query.eq("organization", organization)
    query = query.eq("stat_type", stat_type)
    query = query.eq("stat_key", stat_key)
    
    # Check if expired
    query = query.or_("expires_at.is.null,expires_at.gt." + datetime.now().isoformat())
    
    response = query.execute()
    
    if response.data:
        return response.data[0]["stat_data"]
    return None


def use_precalculated_or_calculate(user_id: str, organization: str, stat_type: str, stat_key: str, calculation_func):
    """
    Try to use pre-calculated stat, otherwise calculate and cache.
    """
    # Try to get from cache
    cached = get_precalculated_stat(user_id, organization, stat_type, stat_key)
    if cached:
        return cached
    
    # Calculate fresh
    result = calculation_func()
    
    # Store in cache (background job)
    queue_stats_calculation_job(user_id, organization, stat_type, stat_key, result)
    
    return result
```

---

### **Phase 4: Background Worker System**

#### **4.1 Architecture Options**

**Option A: Python Threading (Simple, for MVP)**
- ✅ No additional infrastructure
- ✅ Easy to implement
- ❌ Limited scalability
- ❌ Single server only

**Option B: Celery + Redis (Production-Grade)**
- ✅ Scalable (multiple workers)
- ✅ Job retry, priority, scheduling
- ❌ Requires Redis server
- ❌ More complex setup

**Option C: Supabase Edge Functions (Serverless)**
- ✅ No infrastructure to manage
- ✅ Auto-scales
- ❌ Cold starts
- ❌ Vendor lock-in

#### **4.2 Recommended: Hybrid Approach**

**Phase 1 (MVP):** Python Threading
- Simple background threads for file uploads
- Queue jobs in database table
- Worker polls database for jobs

**Phase 2 (Production):** Celery + Redis
- Move to Celery for better scalability
- Keep database queue as backup

#### **4.3 Background Worker Implementation**

```python
# src/background/worker.py

import threading
import time
from datetime import datetime
import pandas as pd

class BackgroundWorker:
    """Simple background worker that polls database for jobs."""
    
    def __init__(self, user_id: str = None, organization: str = None):
        self.user_id = user_id
        self.organization = organization
        self.running = False
        self.worker_id = f"worker_{datetime.now().timestamp()}"
    
    def start(self):
        """Start worker in background thread."""
        self.running = True
        thread = threading.Thread(target=self._work_loop, daemon=True)
        thread.start()
    
    def stop(self):
        """Stop worker."""
        self.running = False
    
    def _work_loop(self):
        """Main worker loop - polls for jobs."""
        while self.running:
            try:
                # Get next job from queue
                job = self._get_next_job()
                
                if job:
                    self._process_job(job)
                else:
                    # No jobs, wait a bit
                    time.sleep(5)  # Poll every 5 seconds
                    
            except Exception as e:
                print(f"Worker error: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _get_next_job(self):
        """Get next job from database queue."""
        from src.pv_storage import get_supabase_db
        
        sb = get_supabase_db()
        if not sb:
            return None
        
        # Get highest priority queued job
        query = sb.table("background_jobs").select("*")
        query = query.eq("job_status", "queued")
        
        if self.user_id:
            query = query.eq("user_id", self.user_id)
        if self.organization:
            query = query.eq("organization", self.organization)
        
        query = query.order("priority", desc=False)  # Lower number = higher priority
        query = query.order("scheduled_at", desc=False)  # Oldest first
        query = query.limit(1)
        
        response = query.execute()
        
        if response.data:
            return response.data[0]
        return None
    
    def _process_job(self, job):
        """Process a single job."""
        job_id = job["id"]
        job_type = job["job_type"]
        job_input = job.get("job_input", {})
        
        try:
            # Update status to 'running'
            self._update_job_status(job_id, "running")
            
            # Process based on job type
            if job_type == "file_upload":
                self._process_file_upload(job_input)
            elif job_type == "stats_calculation":
                self._process_stats_calculation(job_input)
            elif job_type == "query_learning":
                self._process_query_learning(job_input)
            elif job_type == "assessment":
                self._process_assessment(job_input)
            
            # Mark as completed
            self._update_job_status(job_id, "completed")
            
        except Exception as e:
            # Handle failure
            retry_count = job.get("retry_count", 0)
            max_retries = job.get("max_retries", 3)
            
            if retry_count < max_retries:
                # Retry
                self._update_job_status(job_id, "queued", retry_count=retry_count + 1)
            else:
                # Failed permanently
                self._update_job_status(job_id, "failed", error=str(e))
    
    def _process_file_upload(self, job_input):
        """Process file upload job."""
        upload_id = job_input.get("upload_id")
        # ... call store_pv_data_async ...
    
    def _process_stats_calculation(self, job_input):
        """Process statistics calculation job."""
        upload_id = job_input.get("upload_id")
        # ... call calculate_stats_background ...
    
    # ... other job processors ...


# Initialize worker on app startup
_global_worker = None

def start_background_worker():
    """Start global background worker."""
    global _global_worker
    if _global_worker is None:
        _global_worker = BackgroundWorker()
        _global_worker.start()

def stop_background_worker():
    """Stop global background worker."""
    global _global_worker
    if _global_worker:
        _global_worker.stop()
```

---

### **Phase 5: Continuous Learning System**

#### **5.1 Query Pattern Recognition**

```python
# src/ai/query_learning.py

def learn_from_query(user_id: str, organization: str, query_text: str, filters: Dict, execution_time_ms: int):
    """
    Learn from user query - store pattern and consider pre-computation.
    """
    # Hash query pattern (normalize variations)
    pattern_hash = _hash_query_pattern(query_text, filters)
    
    # Store in query_learning table
    # ... insert/update query_learning record ...
    
    # If query is executed frequently, mark for pre-computation
    if _is_frequently_used(pattern_hash, organization):
        queue_precomputation_job(user_id, organization, pattern_hash)


def _hash_query_pattern(query_text: str, filters: Dict) -> str:
    """
    Create normalized hash of query pattern.
    Similar queries (different wording, same intent) get same hash.
    """
    # Normalize query (remove specific values, keep structure)
    normalized_query = _normalize_query(query_text)
    
    # Extract filter structure (not values)
    filter_structure = _extract_filter_structure(filters)
    
    # Hash combined pattern
    pattern_string = f"{normalized_query}:{filter_structure}"
    return hashlib.md5(pattern_string.encode()).hexdigest()


def identify_similar_queries(pattern_hash: str, organization: str) -> List[Dict]:
    """
    Find similar queries based on pattern hash.
    """
    # Query query_learning table for same pattern_hash
    # Return list of similar queries
    pass


def auto_run_similar_queries(organization: str):
    """
    Background job: Auto-run frequently used queries and pre-compute results.
    Runs during low peak times.
    """
    # Get frequently used queries
    frequent_queries = get_frequent_queries(organization, min_executions=5)
    
    # For each frequent query, pre-compute result
    for query in frequent_queries:
        queue_precomputation_job(
            query["user_id"],
            query["organization"],
            query["query_pattern_hash"]
        )
```

---

## 📈 Performance Benefits

### **Current Performance:**
- File upload: **10-15 minutes** (blocking)
- Query execution: **2-5 seconds** (recalculates each time)
- Dataset listing: **5-10 seconds** (queries all records)

### **After Optimization:**

#### **Upload Performance:**
- File upload: **2-5 seconds** (buffer only, non-blocking)
- Database storage: **Background** (2-3 minutes, doesn't block)
- Statistics calculation: **Background** (1-2 minutes, doesn't block)
- **User can use app immediately** ✅

#### **Query Performance:**
- Repeated queries: **<100ms** (from pre-calculated stats)
- New queries: **2-5 seconds** (same as before, but results cached)
- Top drugs/reactions: **<50ms** (from cache)

#### **Dataset Listing:**
- List datasets: **<500ms** (from file_upload_history table)
- No need to query pv_cases table

---

## 🔧 Implementation Phases

### **Phase 0: Fix Existing Unused Tables (Week 1 - Priority)**

**Critical:** Fix tables that exist but aren't being used!

#### **0.1 Fix Activity Logs** (Day 1-2)
- ✅ Table exists in database
- ❌ Current: Writes to file only
- **Action:** Update `src/audit_trail.py` to write to `activity_logs` table
- **Impact:** Proper audit trail, compliance, multi-tenant logging

#### **0.2 Fix Query History** (Day 2-3)
- ✅ Table exists in database
- ❌ Current: Stored in session only
- **Action:** Update query interface to persist to database
- **Impact:** Query history persists across sessions

#### **0.3 Fix Saved Queries** (Day 3)
- ✅ Table exists in database
- ❌ Current: Stored in session only
- **Action:** Update query interface to persist to database
- **Impact:** Saved queries persist across sessions

#### **0.4 Add Missing Indexes** (Day 4-5)
- Add composite index: `idx_pv_cases_user_drug_reaction`
- Add date index: `idx_pv_cases_created_at_org`
- Add event date index: `idx_pv_cases_event_date`
- **Impact:** 10-20x faster dataset listing, 2-4x faster queries

**Effort:** 1 week  
**Impact:** Critical - Fixes compliance gaps and improves performance

---

### **Phase 1: File Upload History (Week 2)**
1. ✅ Create `file_upload_history` table
2. ✅ Implement duplicate file detection
3. ✅ Update upload flow to create upload record
4. ✅ Show duplicate warning in UI

**Effort:** 2-3 days  
**Impact:** High - Users can see upload history, prevent duplicates

---

### **Phase 2: Background Database Storage (Week 2)**
1. ✅ Implement background worker (threading)
2. ✅ Queue database storage jobs
3. ✅ Update UI to show "processing" status
4. ✅ Non-blocking upload flow

**Effort:** 3-4 days  
**Impact:** Critical - Uploads become non-blocking

---

### **Phase 3: Background Statistics (Week 3)**
1. ✅ Create `pre_calculated_stats` table
2. ✅ Implement stats calculation in background
3. ✅ Store stats in file_upload_history
4. ✅ Use cached stats in queries

**Effort:** 4-5 days  
**Impact:** High - Queries become much faster

---

### **Phase 4: Query Learning (Week 4-5)**
1. ✅ Create `query_learning` table
2. ✅ Implement pattern recognition
3. ✅ Auto-precompute frequent queries
4. ✅ Background job for learning

**Effort:** 5-7 days  
**Impact:** Medium-High - Proactive optimization

---

### **Phase 5: Production-Grade Workers (Month 2)**
1. ✅ Migrate to Celery + Redis (if needed)
2. ✅ Multiple workers
3. ✅ Job retry/scheduling
4. ✅ Monitoring dashboard

**Effort:** 1-2 weeks  
**Impact:** High - Better scalability

---

## ⚠️ Considerations & Challenges

### **1. Data Consistency**
- **Challenge:** Background jobs might fail, leaving inconsistent state
- **Solution:** 
  - Transactional updates
  - Job retry logic
  - Status tracking

### **2. Cache Invalidation**
- **Challenge:** Pre-calculated stats become stale when new data added
- **Solution:**
  - Version tracking
  - Expiration dates
  - Invalidate on new uploads

### **3. Resource Usage**
- **Challenge:** Background workers consume server resources
- **Solution:**
  - Limit concurrent jobs
  - Priority-based scheduling
  - Resource monitoring

### **4. Streamlit Limitations**
- **Challenge:** Streamlit is synchronous, hard to show real-time job status
- **Solution:**
  - Poll database for status
  - Auto-refresh status indicators
  - Use WebSocket (advanced)

---

## 📝 Summary

### **What You Get:**
1. ✅ **File Upload History** - Track each file separately
2. ✅ **Fast Uploads** - Non-blocking, user can continue immediately
3. ✅ **Pre-Calculated Stats** - Instant query results for common queries
4. ✅ **Background Processing** - Stats calculated in background
5. ✅ **Continuous Learning** - System learns from queries and pre-computes

### **Implementation Difficulty:**
- **Phase 1-2:** Medium (2 weeks)
- **Phase 3:** Medium-High (1 week)
- **Phase 4:** High (2 weeks)
- **Phase 5:** High (2 weeks)

### **Total Timeline:** 6-8 weeks for full implementation

### **Recommended Approach:**
1. Start with **Phase 1-2** (immediate impact, manageable complexity)
2. Then **Phase 3** (big performance gains)
3. **Phase 4-5** can be later (advanced features)

---

This architecture provides a solid foundation for scalable, high-performance data processing while maintaining user experience and system reliability.

---

## 📚 Related Documents

For complete database inventory and current state analysis, see:
- **`DATABASE_INVENTORY_AND_CURRENT_STATE.md`** - Complete list of all tables, views, indexes, and their usage status
- **`AETHERSIGNAL_ENGINEERING_BLUEPRINT.md`** - Section 7.2 (Database Architecture) and Section 17 (Database Strategy Summary)
- **`MIGRATION_TO_V2_STRATEGY.md`** - Database considerations for v2 migration

**Key Findings from Database Inventory:**
- `activity_logs` table exists but NOT being used (logging writes to file only)
- `saved_queries` and `query_history` tables exist but NOT being used (stored in session only)
- `user_data_summary` is a VIEW (not table) - aggregates all data, cannot track individual files
- Missing critical indexes causing 5-10 second dataset listing times
- Need to create 4 new tables for performance optimization
