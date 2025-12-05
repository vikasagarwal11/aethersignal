# Duplicate Review Workflow - User Control Proposal

## 📋 What the Statement Means

### **Current Statement in UI:**
```
"🔗 Combine with existing data (438,512 cases) - don't replace"
```

**What It Means:**
- **If UNCHECKED:** New file upload will **REPLACE** all existing 438,512 cases
  - Old data is removed from session
  - Only new data remains
  - Example: Upload 50K cases → now you have 50K cases (not 488K)

- **If CHECKED:** New file upload will **MERGE/COMBINE** with existing 438,512 cases
  - Old data stays
  - New data is added
  - Duplicates are automatically removed
  - Example: Upload 50K cases → now you have 488K cases (438K + 50K, minus duplicates)

**This is about IN-MEMORY data (session), not database storage yet!**

---

## 🎯 Your Excellent Idea: User Review Workflow

You're asking: **Should users be able to review duplicate records and decide what to do with them?**

**Answer: YES - This is a BEST PRACTICE for enterprise PV systems!**

---

## 📊 Proposed Enhanced Workflow

### **Phase 1: File-Level Check (Fast, Before Processing)**

**Check:** Filename + File Size  
**Action:** Ask user if they want to skip or re-upload

```
User uploads: "FAERS_Q1_2024.zip" (73.2 MB)

⚠️ This file was already uploaded on 2024-01-15
   - Original upload: 438,512 cases
   - File size: 73.2 MB (matches exactly)

What would you like to do?
[Skip - Use existing data]  [Re-upload anyway]  [Cancel]
```

---

### **Phase 2: Process File**

If user chooses to proceed → process the file normally

---

### **Phase 3: Data-Level Duplicate Detection (After Processing)**

**Check:** Composite signatures (quantum algorithms)  
**Result:** Identifies duplicates

---

### **Phase 4: User Review Panel (NEW - Your Idea!)**

**Show duplicate review interface:**

```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ Duplicate Detection Results                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Total cases processed: 50,000                          │
│                                                         │
│ ✅ New cases (will be saved): 45,000                   │
│ ⚠️ Duplicates found: 5,000                             │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Review Duplicates                                   │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │                                                     │ │
│ │ [ ] Show duplicate details                         │ │
│ │                                                     │ │
│ │ Breakdown:                                          │ │
│ │ • Exact duplicates: 3,000 (same case_id)          │ │
│ │ • Near-duplicates: 2,000 (same patient/event)     │ │
│ │                                                     │ │
│ │ Default action: Skip duplicates                    │ │
│ │                                                     │ │
│ │ [✓] Automatically skip duplicates                  │ │
│ │ [ ] Review each duplicate group                    │ │
│ │ [ ] Save duplicates anyway (keep both copies)      │ │
│ │                                                     │ │
│ │ [Review Duplicates] [Save All] [Skip Duplicates]   │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🎨 User Review Options

### **Option 1: Auto-Skip (Default - Fast)**
```
✅ Automatically skip duplicates
   → System skips all duplicates automatically
   → Shows summary: "5,000 duplicates skipped"
   → User doesn't need to review
   → Fast and simple
```

### **Option 2: Review Each Group (Detailed)**
```
Review each duplicate group
   → Show duplicate groups one by one
   → User can decide per group:
     - Keep existing, skip new
     - Replace existing with new
     - Keep both (save duplicate)
   → More control, slower
```

### **Option 3: Save All (Including Duplicates)**
```
Save duplicates anyway (keep both copies)
   → System saves ALL records, even duplicates
   → Creates duplicate entries in database
   → User can review/merge later
   → Useful for audit/comparison
```

---

## 📋 Detailed Review Interface

### **Review Panel Design:**

```python
# After duplicate detection, show review panel:

if duplicates_found:
    st.warning(f"⚠️ Found {duplicate_count:,} duplicate(s)")
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    col1.metric("New Cases", new_count)
    col2.metric("Duplicates", duplicate_count)
    col3.metric("Total", new_count + duplicate_count)
    
    # Review mode selection
    review_mode = st.radio(
        "How would you like to handle duplicates?",
        [
            "Auto-skip (recommended)",
            "Review each duplicate group",
            "Save all (including duplicates)"
        ],
        index=0
    )
    
    if review_mode == "Auto-skip":
        # Show summary and proceed
        st.info(f"✅ {duplicate_count:,} duplicates will be skipped automatically")
        
    elif review_mode == "Review each duplicate group":
        # Show duplicate groups with details
        st.subheader("📋 Duplicate Groups")
        
        for group in duplicate_groups:
            with st.expander(f"Group {group['id']}: {group['count']} cases"):
                # Show all cases in this group
                st.dataframe(group['cases'])
                
                # User decision per group
                action = st.radio(
                    f"Action for Group {group['id']}:",
                    ["Skip new", "Replace existing", "Keep both"],
                    key=f"group_{group['id']}"
                )
    
    elif review_mode == "Save all":
        st.warning("⚠️ All records (including duplicates) will be saved to database")
        st.info("You can review and merge duplicates later using the Duplicate Detection panel")
```

---

## 💾 Database Storage Decision

### **What Happens for Each Option:**

| Option | New Cases | Duplicates | Database Result |
|--------|-----------|------------|-----------------|
| **Auto-skip** | ✅ Saved | ❌ Skipped | Only unique cases saved |
| **Review each** | ✅ Saved | ⚠️ User decides per group | Based on user choice |
| **Save all** | ✅ Saved | ✅ Saved | All records saved (with duplicates) |

---

## 🎯 Recommended Workflow

### **Default (Fast Path):**
1. Detect duplicates
2. Show summary: "X duplicates found"
3. Auto-skip duplicates
4. Save new cases only
5. User can review later if needed

### **Review Path (User-Requested):**
1. Detect duplicates
2. Show summary: "X duplicates found"
3. User clicks "Review Duplicates"
4. Show duplicate groups with details
5. User makes decision per group
6. Save based on user choices

### **Audit Path (Regulatory Needs):**
1. Detect duplicates
2. User selects "Save all"
3. All records saved (including duplicates)
4. User reviews/merges later using Duplicate Detection panel
5. Audit trail maintained

---

## 📊 Database Schema for Review Tracking

```sql
CREATE TABLE duplicate_review_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    organization TEXT NOT NULL,
    upload_session_id TEXT,
    review_date TIMESTAMP DEFAULT NOW(),
    
    -- Detection results
    total_cases INTEGER,
    new_cases INTEGER,
    duplicate_cases INTEGER,
    exact_duplicates INTEGER,
    near_duplicates INTEGER,
    
    -- User decision
    review_mode TEXT, -- 'auto_skip', 'review_each', 'save_all'
    action_taken TEXT, -- 'skipped', 'saved', 'replaced', 'mixed'
    
    -- Review details (JSONB)
    review_details JSONB, -- { group_id: { action: 'skip', cases: [...] } }
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## ✅ Benefits of User Review

1. **User Control** ✅
   - Users decide what to do with duplicates
   - Not forced to skip automatically
   - Flexibility for different scenarios

2. **Regulatory Compliance** ✅
   - Audit trail of user decisions
   - Documented review process
   - Trackable actions

3. **Quality Assurance** ✅
   - Users can verify duplicates are real
   - Catch false positives
   - Make informed decisions

4. **Flexibility** ✅
   - Fast path: Auto-skip (most users)
   - Detailed path: Review each (power users)
   - Audit path: Save all (compliance needs)

---

## 🎨 UI Flow

```
Upload File
    ↓
File-Level Check (Fast)
    ↓
Process File
    ↓
Data-Level Duplicate Detection
    ↓
┌─────────────────────────────────┐
│ Show Summary                    │
│ • X new cases                   │
│ • Y duplicates found            │
│                                 │
│ [Auto-Skip] [Review] [Save All] │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ If Review Selected:             │
│ • Show duplicate groups         │
│ • User decides per group        │
│ • Save based on decisions       │
└─────────────────────────────────┘
    ↓
Save to Database
```

---

## 💡 Summary

**Your idea is EXCELLENT!** 

**Proposed Implementation:**
1. ✅ File-level check (fast)
2. ✅ Data-level check (sophisticated)
3. ✅ **User review panel (NEW - your idea!)**
   - Auto-skip (default, fast)
   - Review each group (detailed)
   - Save all (audit mode)
4. ✅ Save metadata only (not duplicate data)

**The Statement Explanation:**
- "Combine with existing data" = Merge new file with existing data (don't replace)
- Shows current case count so user knows what they're merging with

This gives users full control while maintaining speed and compliance!

