# 📋 Session Reset Preserve List - Complete Explanation

## 🔍 **What is "Session Reset"?**

When a user clicks **"Clear Filters & Results"** (or "Reset Session"), the app clears all data, filters, and results to start fresh.

### **Current Behavior (Before Fix):**
- ❌ Clears **EVERYTHING** including workspace selection, processing mode, theme settings
- ❌ User loses their workspace choice (e.g., "governance" → back to "explorer")
- ❌ User loses processing mode (e.g., "local" → back to "server")
- ❌ User loses theme settings
- ❌ User loses engine references (have to reinitialize)

### **Desired Behavior (After Fix):**
- ✅ Clears **only data/filters/results**
- ✅ Preserves **workspace selection** (stays on "governance" if that's what they chose)
- ✅ Preserves **processing mode** (stays on "local" if that's what they chose)
- ✅ Preserves **theme settings**
- ✅ Preserves **engine references** (don't have to reinitialize)
- ✅ Preserves **authentication** (doesn't log them out)

---

## 📝 **What is the "Preserve List"?**

The **preserve list** is a list of session state keys that should **NOT be deleted** when the user clicks "Clear Filters & Results".

### **Before (Old List - Only 7 Keys):**
```python
auth_keys_to_preserve = [
    "user_id",
    "user_email",
    "user_session",
    "authenticated",
    "user_profile",
    "user_organization",
    "user_role",
]
```

**Problem:** Only preserved auth keys. Lost everything else!

### **After (New List - 25 Keys):**
```python
preserve_keys = [
    # Authentication (7 keys)
    "user_id", "user_email", "user_session", "authenticated",
    "user_profile", "user_organization", "user_role",
    
    # Navigation & Workspace (6 keys)
    "active_workspace",           # Which workspace user selected
    "processing_mode",            # "server" | "local" | "auto"
    "processing_mode_reason",    # Why this mode was chosen
    "processing_mode_override",   # User override flag
    "sidebar_mode",               # Sidebar state
    "current_page",               # Current page reference
    
    # UX & Theme (4 keys)
    "theme_mode",                 # Light/dark theme
    "debug_mode",                  # Debug mode on/off
    "quantum_enabled",             # Quantum features enabled
    "include_social_ae",           # Include social AE data
    
    # Engine & Heavy Objects (2 keys)
    "hybrid_master_engine",        # Main engine reference (expensive to recreate)
    "browser_capabilities",         # Browser feature detection
    
    # Transient Navigation (4 keys)
    "nav_action",                  # Navigation action in progress
    "show_login",                  # Show login UI flag
    "show_register",               # Show register UI flag
    "show_profile",                # Show profile UI flag
    
    # Memory & Conversation (2 keys)
    "memory_state",                 # Conversation memory
]
```

**Result:** Preserves everything important, only clears data/filters!

---

## 🎯 **What Each Category Does**

### **1. Authentication (7 keys)**
**Why preserve:** User shouldn't be logged out when clearing filters
- `user_id` - User's unique ID
- `user_email` - User's email
- `user_session` - Session token
- `authenticated` - Auth status flag
- `user_profile` - Full user profile
- `user_organization` - User's organization
- `user_role` - User's role (admin, scientist, etc.)

### **2. Navigation & Workspace (6 keys)**
**Why preserve:** User's workspace choice and processing mode shouldn't reset
- `active_workspace` - Current workspace ("explorer", "governance", "inspector", etc.)
- `processing_mode` - Processing mode ("server", "local", "auto")
- `processing_mode_reason` - Why this mode was chosen
- `processing_mode_override` - User override flag
- `sidebar_mode` - Sidebar state (collapsed/expanded)
- `current_page` - Current page reference

### **3. UX & Theme (4 keys)**
**Why preserve:** User's preferences shouldn't reset
- `theme_mode` - Light/dark theme preference
- `debug_mode` - Debug mode on/off
- `quantum_enabled` - Quantum features enabled
- `include_social_ae` - Include social AE data preference

### **4. Engine & Heavy Objects (2 keys)**
**Why preserve:** Expensive to recreate, no need to clear
- `hybrid_master_engine` - Main engine reference (takes time to initialize)
- `browser_capabilities` - Browser feature detection (doesn't change)

### **5. Transient Navigation (4 keys)**
**Why preserve:** Navigation actions in progress shouldn't be lost
- `nav_action` - Navigation action in progress
- `show_login` - Show login UI flag
- `show_register` - Show register UI flag
- `show_profile` - Show profile UI flag

### **6. Memory & Conversation (2 keys)**
**Why preserve:** Conversation context shouldn't be lost
- `memory_state` - Conversation memory (drug, reactions, filters, etc.)

---

## ✅ **What Gets Cleared (Not in Preserve List)**

These keys will be **deleted** when user clicks "Clear Filters & Results":
- `data` - Uploaded data
- `normalized_data` - Normalized data
- `last_filters` - Last applied filters
- `last_query_text` - Last query text
- `last_query_source` - Last query source
- `query_history` - Query history
- `saved_queries` - Saved queries
- `show_results` - Show results flag
- `loading_in_progress` - Loading flag
- `chat_history` - Chat history
- All analysis results, charts, tables, etc.

**This is correct!** User wants to clear data/filters, not lose their workspace/theme/engine.

---

## 🎯 **Result**

**Before Fix:**
- User on "governance" workspace → clicks "Clear Filters" → back to "explorer" ❌
- User with "local" processing mode → clicks "Clear Filters" → back to "server" ❌
- User with dark theme → clicks "Clear Filters" → back to light theme ❌

**After Fix:**
- User on "governance" workspace → clicks "Clear Filters" → stays on "governance" ✅
- User with "local" processing mode → clicks "Clear Filters" → stays on "local" ✅
- User with dark theme → clicks "Clear Filters" → stays on dark theme ✅
- Data/filters cleared as expected ✅

---

## 📝 **Implementation**

**File:** `src/ui/sidebar.py` (lines 75-97)

**Status:** ✅ **UPDATED** - Now preserves 25 keys instead of 7

**Test:** Click "Clear Filters & Results" and verify:
- ✅ Workspace selection preserved
- ✅ Processing mode preserved
- ✅ Theme preserved
- ✅ Auth preserved
- ✅ Data/filters cleared

---

**Updated:** 2025-12-03  
**Keys Preserved:** 25 (was 7)  
**Status:** ✅ Complete

