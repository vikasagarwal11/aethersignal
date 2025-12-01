# Multi-User Scalability Analysis: Current Architecture

## 🎯 Your Question

**"How can we handle the scenario where multiple users will upload multiple files with heavy data?"**

---

## ⚠️ Current Architecture Limitations

### **Current Design: Server-Side Streamlit**

```
User 1 Browser ──┐
User 2 Browser ──┤
User 3 Browser ──┼──→ Single Streamlit Server Instance
User 4 Browser ──┤     (Python process with limited resources)
User N Browser ──┘
```

### **Critical Bottlenecks:**

#### **1. Memory Constraints (Single Server Process)**

**Current Behavior:**
- Each user session loads data into server RAM
- Each large file (100MB) = ~500K-1M rows in memory
- Pandas DataFrames consume significant memory

**Example Scenario:**
```
10 concurrent users × 100MB files = 1GB RAM just for data
+ Python overhead = ~2-3GB total RAM needed
+ Processing overhead = Additional 1-2GB
= ~4-5GB RAM required for 10 concurrent users
```

**Streamlit Cloud Limits:**
- Free tier: Limited memory (varies)
- Paid tier: Still single process (may scale vertically, but expensive)

#### **2. CPU Constraints (Single-Threaded Processing)**

**Current Behavior:**
- File processing is CPU-intensive (pandas operations)
- Each file upload blocks processing for that user
- Multiple uploads = sequential processing (queue)

**Problem:**
```
User 1 uploads 100MB file → Processes for 5 minutes
User 2 uploads 100MB file → Waits for User 1, then processes for 5 minutes
User 3 uploads 100MB file → Waits for User 1 & 2, then processes...

Total time for 3 users: 15 minutes
```

#### **3. Database Connection Limits**

**Current Implementation:**
- Each upload opens Supabase connection
- Batch inserts are blocking (synchronous)
- 100K rows = 2-5 minutes of database insertion

**Supabase Limits:**
- Connection pool limits (varies by plan)
- Rate limiting on inserts
- RLS policy checks on every insert

#### **4. No Background Processing**

**Current Behavior:**
- All processing happens synchronously
- UI blocks during upload/processing
- User must keep browser open

**Impact:**
- If user closes browser, upload is lost
- No queue system for large uploads
- No progress persistence

---

## 🔴 Real-World Scenarios & What Happens

### **Scenario 1: 5 Users Upload 50MB Files Simultaneously**

**What Happens:**
```
Time 0:00 - All 5 users click "Upload"
Time 0:01 - User 1's file starts processing
Time 1:00 - User 1's file finishes, User 2 starts
Time 2:00 - User 2's file finishes, User 3 starts
Time 3:00 - User 3's file finishes, User 4 starts
Time 4:00 - User 4's file finishes, User 5 starts
Time 5:00 - User 5's file finishes

Result: Sequential processing, not concurrent
Last user waits 5 minutes before processing even starts
```

**Memory Usage:**
- Peak: ~1-2GB RAM (only 1 user processing at a time)
- Database: 5 connections in use sequentially

**User Experience:**
- ❌ Users 2-5 see "waiting" for minutes
- ❌ No visibility into queue position
- ❌ Timeout risk if processing takes too long

---

### **Scenario 2: 10 Users Upload 100MB Files**

**What Happens:**
```
Server RAM: ~4-5GB needed
Processing Time: ~50 minutes total (sequential)
Database: Potential connection pool exhaustion
RLS Overhead: Each insert checks RLS policy

Result: 
- Server may crash (out of memory)
- Database may throttle/block connections
- Users experience timeouts
- Poor user experience
```

---

### **Scenario 3: 1 User Uploads 500MB File (Very Large)**

**What Happens:**
```
File Size: 500MB
Rows: ~2.5M rows
Memory: ~2-3GB RAM needed
Processing: ~15-20 minutes
Database: ~10-15 minutes for batch inserts

Result:
- Single user blocks server for 30+ minutes
- Other users cannot upload during this time
- High risk of timeout/crash
```

---

## ✅ Solutions Within Current Architecture

### **Solution 1: Optimize Database Storage (Immediate)**
**Current Code:** `src/pv_storage.py`

**Changes:**
```python
# Current: Synchronous blocking inserts
with st.spinner("💾 Storing data in database..."):
    result = store_pv_data(normalized, user_id, organization, source)
    # Blocks UI for 2-5 minutes

# Optimized: Async background task
def store_pv_data_async(df, user_id, organization, source):
    # Queue job, return immediately
    # Process in background thread
    # Update status via WebSocket or polling
```

**Benefits:**
- ✅ UI doesn't block during database storage
- ✅ User can continue using app
- ⚠️ Still server-side, but non-blocking

**Implementation Effort:** Medium (2-3 days)

---

### **Solution 2: Chunked File Processing (Medium-term)**
**Current Code:** `src/app_helpers.py` - `load_all_files()`

**Changes:**
```python
# Current: Load entire file into memory
df = pd.read_csv(file)  # Loads 500K rows at once

# Optimized: Process in chunks
chunk_size = 10000
chunks = []
for chunk in pd.read_csv(file, chunksize=chunk_size):
    # Process chunk
    normalized_chunk = normalize(chunk)
    # Store chunk to database immediately
    store_pv_data(normalized_chunk, user_id, org, source)
    chunks.append(chunk)

# Combine chunks for session state (smaller)
df = pd.concat(chunks)
```

**Benefits:**
- ✅ Lower peak memory usage
- ✅ Database writes happen incrementally
- ✅ Progress tracking per chunk
- ✅ Can handle larger files

**Implementation Effort:** Medium (3-5 days)

---

### **Solution 3: Background Job Queue (Long-term)**
**Architecture Change Required**

**New Components:**
- Background job queue (Celery or RQ)
- Redis for job storage
- Worker processes for processing
- Status tracking (Supabase table)

**Flow:**
```
User uploads file
    ↓
Job queued (immediate response)
    ↓
Worker picks up job
    ↓
Process file in background
    ↓
Store to database
    ↓
Update status (ready/complete)
    ↓
User polls or gets notification
```

**Benefits:**
- ✅ True concurrency (multiple workers)
- ✅ User doesn't wait
- ✅ Better resource utilization
- ✅ Handles many concurrent users

**Implementation Effort:** High (2-3 weeks)

**Additional Infrastructure:**
- Redis server
- Worker processes
- Job monitoring

---

### **Solution 4: Streamlit Cloud Scaling (Deployment)**
**Streamlit Cloud Configuration**

**Options:**
1. **Horizontal Scaling (Multiple Instances)**
   - Streamlit Cloud doesn't natively support this
   - Need load balancer + multiple deployments
   - Complex configuration

2. **Vertical Scaling (Larger Instance)**
   - Upgrade Streamlit Cloud plan
   - More RAM/CPU available
   - Still single process, but more resources
   - Cost: Higher monthly fees

**Limitation:**
- Streamlit Cloud is designed for low-to-medium traffic
- Not ideal for high-concurrency scenarios
- Better for: <50 concurrent users

---

## 🏗️ Architectural Solutions (Major Changes)

### **Option A: Migrate to Dedicated Server**

**Architecture:**
```
Multiple Users
    ↓
Load Balancer (Nginx/AWS ELB)
    ↓
Multiple Streamlit Instances (Horizontal Scaling)
    ↓
Shared Database (Supabase)
    ↓
Background Workers (Celery + Redis)
```

**Components:**
- AWS/GCP/Azure server
- Docker containers for Streamlit
- Load balancer
- Redis for job queue
- Celery workers
- Supabase database (can stay)

**Benefits:**
- ✅ True horizontal scaling
- ✅ Handles 100+ concurrent users
- ✅ Better resource utilization
- ✅ Production-grade

**Cost:** $200-500/month (depending on traffic)

**Implementation Effort:** 4-6 weeks

---

### **Option B: Hybrid Architecture (Recommended)**

**Keep Streamlit + Add Background Processing**

**Architecture:**
```
User Browser
    ↓
Streamlit App (UI only)
    ↓
API Server (FastAPI)
    ├─ Background Jobs (Celery)
    ├─ Job Status API
    └─ File Upload API
    ↓
Workers (Process files)
    ↓
Supabase Database
```

**Flow:**
1. User uploads file via Streamlit
2. Streamlit calls FastAPI endpoint
3. FastAPI queues background job
4. Streamlit shows "processing..." status
5. Background worker processes file
6. Streamlit polls status API
7. When complete, data available

**Benefits:**
- ✅ Keep Streamlit UI (familiar)
- ✅ Add scalable backend
- ✅ Non-blocking uploads
- ✅ Better concurrency

**Implementation Effort:** 3-4 weeks

---

### **Option C: Client-Side Processing (ChatGPT's Proposal)**

**See:** `ARCHITECTURE_SHIFT_ANALYSIS.md`

**Summary:**
- Move processing to browser (DuckDB WASM)
- Server only for LLM + Auth
- Better for: <100MB files
- Limitation: Browser memory constraints

**Not Recommended:** See detailed analysis in `ARCHITECTURE_SHIFT_ANALYSIS.md`

---

## 📊 Scalability Comparison

| Solution | Concurrent Users | Implementation | Cost | Complexity |
|----------|-----------------|----------------|------|------------|
| **Current** | 5-10 | ✅ Done | Low | Low |
| **Optimized DB** | 10-15 | 🟡 3 days | Low | Low |
| **Chunked Processing** | 15-25 | 🟡 5 days | Low | Medium |
| **Job Queue** | 25-50 | 🔴 3 weeks | Medium | High |
| **Hybrid (FastAPI)** | 50-100+ | 🔴 4 weeks | Medium | High |
| **Dedicated Server** | 100+ | 🔴 6 weeks | High | Very High |
| **Client-Side** | 20-30 | 🔴 4-6 months | Low | Very High |

---

## 🎯 Recommended Approach

### **Phase 1: Immediate (Week 1)**
1. ✅ **Optimize Database Storage**
   - Make database writes non-blocking
   - Return immediately, process in background
   - Update status via polling

2. ✅ **Add File Size Limits**
   - Warn users about large files
   - Suggest chunked uploads
   - Set reasonable limits (e.g., 200MB)

3. ✅ **Add Progress Tracking**
   - Show upload progress
   - Show processing status
   - Show queue position (if multiple users)

### **Phase 2: Short-term (Weeks 2-4)**
1. ✅ **Implement Chunked Processing**
   - Process files in 10K row chunks
   - Store chunks incrementally
   - Lower memory footprint

2. ✅ **Add Background Jobs**
   - Simple queue system
   - Process uploads asynchronously
   - Better user experience

### **Phase 3: Long-term (Months 2-3)**
1. ✅ **Migrate to Hybrid Architecture**
   - FastAPI backend for heavy operations
   - Keep Streamlit for UI
   - True scalability

---

## 🔍 Current Limitations Summary

| Aspect | Current | Max Capacity | Bottleneck |
|--------|---------|--------------|------------|
| **Concurrent Users** | 5-10 | 10-15 | Memory + CPU |
| **File Size** | 100MB | 200MB | Memory |
| **Total Rows** | 500K | 1M | Memory |
| **Database Inserts** | Blocking | ~1K/sec | Synchronous |
| **Processing Speed** | Sequential | Sequential | Single-threaded |

---

## ⚠️ Critical Issues for Multi-User

### **1. Session State Isolation**
**Current:** ✅ Each user has isolated `st.session_state`
**Problem:** ⚠️ But all share same server memory
**Impact:** If User 1 loads 500MB, less memory for User 2

### **2. Database Connection Pooling**
**Current:** ⚠️ No explicit connection pooling
**Problem:** Each request may create new connection
**Impact:** Connection exhaustion with many users

### **3. File Upload Timeout**
**Current:** ⚠️ No timeout handling
**Problem:** Large files may timeout (30s-2min typical)
**Impact:** Upload fails silently

### **4. Error Recovery**
**Current:** ⚠️ No retry mechanism
**Problem:** Transient failures cause upload loss
**Impact:** User must re-upload

---

## ✅ What Works Well Currently

### **1. Multi-Tenant Isolation**
- ✅ RLS policies work perfectly
- ✅ Users only see their organization's data
- ✅ No cross-tenant data leakage

### **2. Authentication**
- ✅ Supabase Auth handles concurrent logins
- ✅ Session management works
- ✅ No conflicts between users

### **3. Data Persistence**
- ✅ Database storage works for all users
- ✅ RLS ensures proper isolation
- ✅ Data persists across sessions

### **4. Query Processing**
- ✅ Each user's queries are independent
- ✅ Database RLS filters automatically
- ✅ No performance impact between users

---

## 🚀 Immediate Action Plan

### **For Low-Medium Usage (<20 users, <50MB files):**
✅ **Keep current architecture**
- Add file size warnings
- Optimize database storage (async)
- Add progress indicators
- Monitor memory usage

### **For High Usage (>20 users, >100MB files):**
🔴 **Implement Phase 2-3 solutions**
- Background job queue
- Chunked processing
- Consider hybrid architecture
- Monitor and scale

---

## 📝 Code Changes Needed

### **Immediate (Low Effort, High Impact):**

**1. Async Database Storage** (`src/pv_storage.py`)
```python
import threading

def store_pv_data_async(df, user_id, organization, source):
    # Queue job, return immediately
    thread = threading.Thread(
        target=store_pv_data,
        args=(df, user_id, organization, source)
    )
    thread.start()
    return {"status": "queued", "message": "Processing in background"}
```

**2. File Size Limit** (`src/ui/upload_section.py`)
```python
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

if uploaded_file.size > MAX_FILE_SIZE:
    st.error(f"⚠️ File too large ({uploaded_file.size / 1024 / 1024:.1f}MB). Maximum size: 200MB")
    return
```

**3. Progress Tracking** (Add status table to Supabase)
```sql
CREATE TABLE upload_jobs (
    id UUID PRIMARY KEY,
    user_id UUID,
    status TEXT,  -- 'queued', 'processing', 'complete', 'failed'
    progress INTEGER,  -- 0-100
    created_at TIMESTAMP
);
```

---

## 🎯 Conclusion

### **Current Architecture Can Handle:**
- ✅ **5-10 concurrent users** (with current setup)
- ✅ **50-100MB files** (with current setup)
- ✅ **500K-1M rows per file** (with current setup)

### **Current Architecture Cannot Handle Well:**
- ❌ **>20 concurrent users** (needs scaling)
- ❌ **>200MB files** (memory constraints)
- ❌ **>2M rows per file** (processing time)

### **Recommended Path:**
1. **Short-term:** Optimize database storage + add file size limits
2. **Medium-term:** Implement background job queue
3. **Long-term:** Migrate to hybrid architecture if needed

### **Key Takeaway:**
Current architecture is **fine for MVP and early users**. Scale as needed based on actual usage patterns, not hypothetical scenarios.

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Analysis complete, recommendations provided

