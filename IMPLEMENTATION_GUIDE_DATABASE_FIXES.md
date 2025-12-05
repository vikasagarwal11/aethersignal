# Database Fixes Implementation Guide
## Exact Code Changes Needed

**Date:** December 2024  
**Purpose:** Step-by-step guide for integrating database fixes

---

## ✅ What's Already Done

1. ✅ SQL migration files created
2. ✅ Audit trail updated to write to database
3. ✅ Helper functions created (`file_upload_history.py`, `query_persistence.py`)

---

## 🔧 Integration Points

### **Integration Point 1: Duplicate File Check (Upload Section)**

**Location:** `src/ui/upload_section.py` - Before file processing starts

**Add this code BEFORE processing files (around line 880):**

```python
# After: if load_clicked and uploaded_files:
# Before: raw_df = load_all_files(...)

# Check for duplicate files (NEW)
try:
    from src.auth.auth import is_authenticated, get_current_user
    from src.file_upload_history import check_duplicate_file
    
    if is_authenticated():
        user = get_current_user()
        if user:
            user_id = user.get('user_id')
            organization = user.get('organization', '')
            
            # Check each uploaded file for duplicates
            duplicate_warnings = []
            for file in uploaded_files:
                duplicate = check_duplicate_file(
                    user_id, organization, file.name, file.size
                )
                if duplicate:
                    upload_date = duplicate.get('uploaded_at', '')
                    case_count = duplicate.get('total_cases', 0)
                    duplicate_warnings.append({
                        'filename': file.name,
                        'size_mb': file.size / (1024 * 1024),
                        'uploaded_at': upload_date,
                        'cases': case_count
                    })
            
            # Show duplicate warnings if any
            if duplicate_warnings:
                st.warning("⚠️ **Potential Duplicate Files Detected:**")
                for dup in duplicate_warnings:
                    st.info(
                        f"📄 **{dup['filename']}** ({dup['size_mb']:.1f} MB) - "
                        f"Previously uploaded on {dup['uploaded_at'][:10] if dup['uploaded_at'] else 'unknown date'} "
                        f"with {dup['cases']:,} cases. "
                        "This file will be processed anyway, but you can skip it if it's a duplicate."
                    )
except Exception:
    pass  # Don't break upload if duplicate check fails
```

---

### **Integration Point 2: Create File Upload Record**

**Location:** `src/ui/upload_section.py` - After files are loaded but before database storage

**Add this code AFTER file processing completes (around line 1238, after raw_df is loaded):**

```python
# After: raw_df = load_all_files(...)
# Before: normalized = cached_detect_and_normalize(...)

upload_ids = []  # Store upload IDs for each file

# Create file upload history records (NEW)
try:
    from src.auth.auth import is_authenticated, get_current_user
    from src.file_upload_history import create_file_upload_record
    
    if is_authenticated() and uploaded_files:
        user = get_current_user()
        if user:
            user_id = user.get('user_id')
            organization = user.get('organization', '')
            
            # Detect file type
            source = 'FAERS'  # Default
            file_type = 'FAERS'
            for file in uploaded_files:
                if file.name.lower().endswith('.xml'):
                    source = 'E2B'
                    file_type = 'E2B'
                elif file.name.lower().endswith('.csv'):
                    file_type = 'CSV'
                elif file.name.lower().endswith(('.xlsx', '.xls')):
                    file_type = 'Excel'
            
            # Create upload record for each file
            for file in uploaded_files:
                upload_id = create_file_upload_record(
                    user_id=user_id,
                    organization=organization,
                    filename=file.name,
                    file_size_bytes=file.size,
                    file_type=file_type,
                    source=source
                )
                if upload_id:
                    upload_ids.append(upload_id)
                    st.session_state[f"upload_id_{file.name}"] = upload_id
except Exception:
    pass  # Don't break upload if record creation fails
```

---

### **Integration Point 3: Update File Upload Status After Storage**

**Location:** `src/ui/upload_section.py` - After `store_pv_data()` succeeds

**Add this code AFTER successful database storage (around line 1469):**

```python
# After: st.success("✅ Data stored in database...")
# Add this:

# Update file upload history with statistics (NEW)
try:
    from src.file_upload_history import update_file_upload_status, update_file_upload_stats
    import pandas as pd
    
    if upload_ids and normalized is not None and not normalized.empty:
        # Calculate statistics
        total_cases = len(normalized)
        total_events = normalized['reaction'].nunique() if 'reaction' in normalized.columns else 0
        total_drugs = normalized['drug_name'].nunique() if 'drug_name' in normalized.columns else 0
        total_serious = len(normalized[normalized.get('serious', False) == True]) if 'serious' in normalized.columns else 0
        total_fatal = len(normalized[normalized.get('outcome', '').str.contains('Death', case=False, na=False)]) if 'outcome' in normalized.columns else 0
        
        earliest_date = None
        latest_date = None
        if 'event_date' in normalized.columns:
            dates = pd.to_datetime(normalized['event_date'], errors='coerce').dropna()
            if not dates.empty:
                earliest_date = dates.min().strftime('%Y-%m-%d')
                latest_date = dates.max().strftime('%Y-%m-%d')
        
        # Update each upload record
        for upload_id in upload_ids:
            # Update status to completed
            update_file_upload_status(upload_id, status="completed", total_cases=total_cases)
            
            # Update statistics
            update_file_upload_stats(
                upload_id=upload_id,
                total_cases=total_cases,
                total_events=total_events,
                total_drugs=total_drugs,
                total_serious_cases=total_serious,
                total_fatal_cases=total_fatal,
                earliest_date=earliest_date,
                latest_date=latest_date
            )
except Exception:
    pass  # Don't break if stats update fails
```

---

### **Integration Point 4: Persist Query History**

**Location:** `src/ui/query_interface.py` - After query execution (around line 668)

**Replace existing query history storage:**

```python
# FIND THIS (around line 661-668):
# Save to query history
history = st.session_state.get("query_history", [])
history.append({
    "query_text": query,
    "timestamp": datetime.now().isoformat(),
    "source": "chat_fast",
})
st.session_state.query_history = history[-10:]

# REPLACE WITH:
# Save to query history (session + database)
history = st.session_state.get("query_history", [])
history.append({
    "query_text": query,
    "timestamp": datetime.now().isoformat(),
    "source": "chat_fast",
})
st.session_state.query_history = history[-10:]

# Also persist to database
try:
    from src.auth.auth import is_authenticated, get_current_user
    from src.query_persistence import save_query_to_history
    import time
    
    if is_authenticated():
        user = get_current_user()
        if user:
            user_id = user.get('user_id')
            organization = user.get('organization', '')
            
            # Calculate execution time if available
            execution_time_ms = None
            if "query_start_time" in st.session_state:
                execution_time_ms = int((time.time() - st.session_state.query_start_time) * 1000)
            
            save_query_to_history(
                user_id=user_id,
                organization=organization,
                query_text=query,
                filters=st.session_state.get("last_filters"),
                source="nl",
                results_count=len(filtered_df) if 'filtered_df' in locals() else None,
                execution_time_ms=execution_time_ms
            )
except Exception:
    pass  # Don't break query execution if persistence fails
```

---

### **Integration Point 5: Load Query History from Database**

**Location:** `src/ui/query_interface.py` - At the start of `render_nl_query_tab()` function

**Add this code at the beginning of the function (around line 427):**

```python
# At the start of render_nl_query_tab(), after chat_history initialization
# Add this:

# Load query history from database if authenticated (NEW)
try:
    from src.auth.auth import is_authenticated, get_current_user
    from src.query_persistence import load_query_history
    
    if is_authenticated():
        user = get_current_user()
        if user:
            user_id = user.get('user_id')
            organization = user.get('organization', '')
            
            # Load from database
            db_history = load_query_history(user_id, organization, limit=20)
            
            if db_history:
                # Convert database format to session format
                session_history = []
                for record in db_history:
                    session_history.append({
                        "query_text": record.get("query_text", ""),
                        "timestamp": record.get("created_at", ""),
                        "source": record.get("source", "nl"),
                        "filters": record.get("filters")
                    })
                
                # Merge with existing session history (avoid duplicates)
                existing = st.session_state.get("query_history", [])
                existing_texts = {h.get("query_text", "") for h in existing}
                
                for h in session_history:
                    if h.get("query_text", "") not in existing_texts:
                        existing.append(h)
                
                # Keep most recent 20
                st.session_state.query_history = existing[-20:]
except Exception:
    pass  # Continue with session-only history if database load fails
```

---

### **Integration Point 6: Persist Saved Queries**

**Location:** `src/ui/query_interface.py` - Where saved queries are stored (around line 1738)

**Replace existing saved query storage:**

```python
# FIND THIS (around line 1738):
saved.append({
    "name": name,
    "query_text": st.session_state.get("last_query_text", ""),
    "filters": st.session_state.get("last_filters", {}),
})
st.session_state.saved_queries = saved[-15:]

# REPLACE WITH:
saved.append({
    "name": name,
    "query_text": st.session_state.get("last_query_text", ""),
    "filters": st.session_state.get("last_filters", {}),
})
st.session_state.saved_queries = saved[-15:]

# Also persist to database
try:
    from src.auth.auth import is_authenticated, get_current_user
    from src.query_persistence import save_query
    
    if is_authenticated():
        user = get_current_user()
        if user:
            user_id = user.get('user_id')
            organization = user.get('organization', '')
            
            save_query(
                user_id=user_id,
                organization=organization,
                name=name,
                query_text=st.session_state.get("last_query_text", ""),
                filters=st.session_state.get("last_filters", {}),
                description=None
            )
except Exception:
    pass  # Don't break if database save fails
```

---

### **Integration Point 7: Load Saved Queries from Database**

**Location:** `src/ui/query_interface.py` - At the start of `render_nl_query_tab()` function

**Add this code after loading query history:**

```python
# After loading query history, add this:

# Load saved queries from database if authenticated (NEW)
try:
    from src.auth.auth import is_authenticated, get_current_user
    from src.query_persistence import load_saved_queries
    
    if is_authenticated():
        user = get_current_user()
        if user:
            user_id = user.get('user_id')
            organization = user.get('organization', '')
            
            # Load from database
            db_saved = load_saved_queries(user_id, organization, limit=50)
            
            if db_saved:
                # Convert database format to session format
                session_saved = []
                for record in db_saved:
                    session_saved.append({
                        "name": record.get("name", ""),
                        "query_text": record.get("query_text", ""),
                        "filters": record.get("filters"),
                        "description": record.get("description"),
                        "usage_count": record.get("usage_count", 0),
                        "last_used_at": record.get("last_used_at")
                    })
                
                # Merge with existing session saved queries (avoid duplicates)
                existing = st.session_state.get("saved_queries", [])
                existing_names = {sq.get("name", "") for sq in existing if isinstance(sq, dict)}
                
                for sq in session_saved:
                    if sq.get("name", "") not in existing_names:
                        existing.append(sq)
                
                # Keep most recent 50
                st.session_state.saved_queries = existing[-50:]
except Exception:
    pass  # Continue with session-only saved queries if database load fails
```

---

## 📋 Implementation Checklist

- [ ] Add duplicate file check in upload_section.py (Integration Point 1)
- [ ] Add file upload record creation (Integration Point 2)
- [ ] Add file upload status/stats updates (Integration Point 3)
- [ ] Update query history persistence (Integration Point 4)
- [ ] Load query history from database (Integration Point 5)
- [ ] Update saved queries persistence (Integration Point 6)
- [ ] Load saved queries from database (Integration Point 7)

---

## 🚀 Next Steps After Integration

1. **Run SQL Migrations:**
   - Execute `database/07_performance_indexes.sql` in Supabase SQL Editor
   - Execute `database/08_file_upload_history.sql` in Supabase SQL Editor

2. **Test:**
   - Upload a file and verify duplicate detection works
   - Check `file_upload_history` table has records
   - Run a query and verify `query_history` table has records
   - Save a query and verify `saved_queries` table has records
   - Verify `activity_logs` table is being written to

---

**This guide provides exact code locations and snippets for integration!**

