# Reset Session Button - Analysis

## What "Reset Session" Currently Does

**Location:** `src/ui/sidebar.py` (lines 22-25)

```python
if st.button("↺ Reset session", key="reset_session_sidebar", use_container_width=True):
    for k in list(st.session_state.keys()):
        del st.session_state[k]  # ⚠️ Deletes EVERYTHING
    st.rerun()
```

**Current behavior:**
- Clears **ALL** session state keys
- Deletes **everything** in `st.session_state`
- Then reruns the page

---

## What Gets Cleared

### ✅ **Session State (Temporary) - Will be cleared:**
1. **Uploaded file data** (`data`, `normalized_data`)
   - ⚠️ But if user is authenticated, this data is already saved to database
   - After reset, data can be reloaded from database

2. **Query state:**
   - Current query text
   - Query filters
   - Query results (display)
   - Saved queries (not persisted yet)
   - Query history (not persisted yet)

3. **UI state:**
   - Selected filters
   - Active tabs
   - Expanded/collapsed sections
   - Form inputs

4. **Authentication state:**
   - ⚠️ **`user_id`** - Will be cleared
   - ⚠️ **`authenticated`** - Will be cleared
   - ⚠️ **`user_profile`** - Will be cleared
   - ⚠️ **`user_session`** - Will be cleared

### ✅ **Database (Persistent) - Will NOT be cleared:**
- ✅ User profiles (still in database)
- ✅ PV case data (still in database)
- ✅ All uploaded data (still in database)

---

## Current Architecture: Session vs Database

### **Session State (Temporary - In Browser Memory):**
```
┌─────────────────────────────────────┐
│     SESSION STATE (Temporary)       │
├─────────────────────────────────────┤
│ • data (uploaded DataFrame)         │
│ • normalized_data                   │
│ • query_history []                  │
│ • saved_queries []                  │
│ • filters, query_text               │
│ • authentication state              │
│ • UI state (tabs, expanded, etc.)   │
└─────────────────────────────────────┘
        │
        │ "Reset Session" clears this
        ↓
      EMPTY
```

### **Database (Persistent - Supabase):**
```
┌─────────────────────────────────────┐
│      DATABASE (Persistent)          │
├─────────────────────────────────────┤
│ • user_profiles                     │
│ • pv_cases (all uploaded data)      │
│ • (Future: saved_queries, etc.)     │
└─────────────────────────────────────┘
        │
        │ "Reset Session" does NOT touch this
        ↓
      UNCHANGED ✅
```

---

## Is It Still Needed?

### 🤔 **Arguments FOR Keeping It:**

1. **Clears temporary UI state**
   - Filters applied during current session
   - Current query results (which may be outdated)
   - Form inputs that may be stuck

2. **Useful for debugging**
   - Developers can quickly clear state
   - Test data loading from database
   - Reset UI to clean state

3. **Refresh without page reload**
   - Faster than F5/reload
   - Doesn't lose browser state (tabs, etc.)
   - Starts fresh session in same browser tab

4. **Clear stale in-memory data**
   - If data was uploaded but not yet saved
   - If filters/results are from old data
   - Start with clean slate

### ❌ **Arguments AGAINST Keeping It:**

1. **Confusing for users**
   - Users might think it deletes their data
   - Button label doesn't clarify what gets cleared
   - Could cause panic if clicked accidentally

2. **Too aggressive**
   - Clears authentication state too
   - User would need to log in again after reset
   - Clears things that should persist (like auth)

3. **Redundant with logout**
   - "Logout" already clears auth-related state
   - "Reset session" overlaps with logout functionality
   - Two buttons doing similar things

4. **Less relevant now**
   - Data persists in database
   - Can just reload data from DB
   - Session state is less critical

---

## Potential Issues

### ⚠️ **Problem 1: Clears Authentication**

When "Reset session" is clicked:
- ✅ Clears `authenticated` flag
- ✅ Clears `user_id`
- ✅ User will appear logged out
- ✅ But Supabase session is still valid (cookie-based)
- ⚠️ Could cause confusion - user needs to refresh page to see they're still logged in

### ⚠️ **Problem 2: Data Loss Risk**

If user uploaded data but:
- Upload completed
- Data saved to database ✅
- But user clicks "Reset session" before seeing confirmation
- User might think data is lost (but it's actually in DB)

### ⚠️ **Problem 3: No Confirmation**

- Button has no confirmation dialog
- Could be clicked accidentally
- No warning about what will be cleared

---

## Recommendations

### **Option 1: Keep It But Make It Safer** ⭐ (Recommended)

**Changes:**
1. **Add confirmation dialog** - Warn user what will be cleared
2. **Preserve authentication** - Don't clear `user_id`, `authenticated`, `user_profile`
3. **Better label** - "Clear current filters & results" instead of "Reset session"
4. **Reload from database** - After reset, automatically reload data from DB if authenticated

**New behavior:**
```python
if st.button("Clear Filters & Results", ...):
    # Show confirmation
    if confirm:
        # Clear only non-auth state
        keys_to_clear = [
            "data", "normalized_data",
            "query_history", "saved_queries",
            "last_filters", "last_query_text",
            "show_results", "schema_mapping"
        ]
        # Keep: user_id, authenticated, user_profile, etc.
        # Reload data from database if authenticated
```

### **Option 2: Remove It Completely**

**Reasons:**
- Less confusing
- "Logout" handles auth clearing
- Data persists anyway
- Users can just refresh page

### **Option 3: Replace with "Clear Filters" Button**

**New button:** "Clear Filters & Results"
- Only clears query-related state
- Doesn't touch authentication
- Doesn't touch database
- Clearer purpose

---

## Current Status Summary

**What "Reset Session" does now:**
- ✅ Clears all session state (including auth)
- ✅ Does NOT delete database data
- ⚠️ User will appear logged out (until refresh)
- ⚠️ No confirmation before clearing
- ⚠️ Aggressive - clears everything

**What happens after reset:**
1. User clicks "Reset session"
2. All session state deleted
3. Page reruns
4. User appears logged out (but Supabase session still valid)
5. User needs to refresh to see they're still logged in
6. Data can be reloaded from database

---

## My Recommendation

**Keep it, but improve it:**
- Add confirmation dialog
- Preserve authentication state
- Rename to "Clear Filters & Results"
- Auto-reload data from database after clearing

Or **remove it** if you want simpler UX - users can just:
- Refresh the page (F5)
- Use "Logout" if they want to clear auth state
- Data persists in database anyway

**What do you think?** Should we keep it with improvements, remove it, or replace it with a more targeted button?

