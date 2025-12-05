# 🔍 Top Navigation Rendering Issues - Diagnosis

**Date:** December 3, 2025  
**Status:** Investigation Complete - Issues Identified

---

## 🐛 **Root Causes Identified**

### **Issue #1: Too Many Columns Created** ⚠️ **CRITICAL**

**Location:** `src/ui/top_nav.py`, line 161

```python
nav_cols = st.columns(max(len(available_routes), 1))
```

**Problem:**
- Creates **one column per route**
- If there are 6 routes → 6 columns
- Each column becomes extremely narrow
- Text wraps vertically in narrow columns

**Current Routes (top/both):**
1. Executive Dashboard (top)
2. Safety Intelligence (both) - has subpages
3. Evidence Governance (both) - likely has subpages  
4. Data Explorer (both) - has subpages
5. Workflows (both) - likely has subpages

**Result:** 5-6 columns in a space that's only 6 units wide (col2 width), making each column ~1 unit wide = **extremely narrow**

---

### **Issue #2: Long Route Names Wrapping** ⚠️ **HIGH**

**Location:** `src/ui/top_nav.py`, lines 170, 197

**Problem:**
- Route names like "Executive Dashboard", "Safety Intelligence", "Evidence Governance" are long
- In narrow columns, text wraps to multiple lines
- Creates vertical button appearance instead of horizontal

**Example:**
```
"Executive Dashboard" → 
  Executive
  Dashboard
```

---

### **Issue #3: Popovers Making It Worse** ⚠️ **MEDIUM**

**Location:** `src/ui/top_nav.py`, line 171

**Problem:**
- Routes with subpages use `st.popover()` 
- Popover label includes full route name: `f"{icon} {route_name}"`
- Popovers add dropdown arrow indicator
- Makes buttons even wider/taller
- Exacerbates text wrapping

**Example:**
```
🧠 Safety Intelligence ▼
```

---

### **Issue #4: No Maximum Column Limit** ⚠️ **MEDIUM**

**Location:** `src/ui/top_nav.py`, line 161

**Problem:**
- No limit on number of columns
- Could create 10+ columns if more routes added
- Should limit to 4-6 visible items max
- Need horizontal scroll or "More" dropdown for overflow

---

### **Issue #5: Column Width Distribution** ⚠️ **LOW**

**Location:** `src/ui/top_nav.py`, line 143

```python
col1, col2, col3 = st.columns([2, 6, 2])
```

**Problem:**
- col2 (middle) has width 6
- But it's divided into many sub-columns
- Each sub-column gets equal width (6 / num_routes)
- With 6 routes: each gets ~1 unit = too narrow

**Better approach:**
- Limit number of visible columns
- Use horizontal scroll or overflow menu
- Or use flexbox/HTML for better control

---

### **Issue #6: No Fixed Positioning** ⚠️ **LOW**

**Location:** `src/ui/top_nav.py`, lines 135-141, 143

**Problem:**
- Navigation renders in normal document flow
- Not a fixed top bar
- Visual container (styled div) is separate from buttons
- Buttons in Streamlit columns render below the container
- Creates disconnected appearance

**Current:**
```
[Styled Container Div]
[Empty space]
[Streamlit Columns with Buttons]
```

**Should be:**
```
[Fixed Top Bar with Buttons Inside]
```

---

## 📊 **Visual Problem Breakdown**

### **What's Happening:**
1. 5-6 routes → 5-6 columns created
2. Each column ~1 unit wide (in 6-unit space)
3. Long text wraps vertically
4. Popovers add extra height
5. Result: Vertical stack of narrow buttons instead of horizontal bar

### **What Should Happen:**
1. Limit to 4-5 visible items
2. Each button gets adequate width
3. Text stays on one line
4. Horizontal layout
5. Overflow items in "More" menu

---

## 🔧 **Recommended Fixes**

### **Fix #1: Limit Number of Columns** (HIGH PRIORITY)
```python
# Instead of:
nav_cols = st.columns(max(len(available_routes), 1))

# Use:
max_visible = min(len(available_routes), 5)  # Max 5 visible
nav_cols = st.columns(max_visible)
```

### **Fix #2: Truncate Long Names** (HIGH PRIORITY)
```python
# Truncate route names for display
display_name = route_name[:15] + "..." if len(route_name) > 15 else route_name
```

### **Fix #3: Use Horizontal Scroll or Overflow Menu** (MEDIUM PRIORITY)
- Show first 4-5 items
- Put rest in "More" dropdown
- Or use horizontal scroll container

### **Fix #4: Better Column Widths** (MEDIUM PRIORITY)
```python
# Instead of equal widths, use weighted distribution
# Or use HTML/CSS flexbox for better control
```

### **Fix #5: Fixed Top Bar** (LOW PRIORITY)
- Use HTML/CSS for fixed positioning
- Or accept normal flow but improve styling

---

## 🎯 **Priority Order**

1. **Limit columns** (prevents narrow buttons)
2. **Truncate names** (prevents wrapping)
3. **Overflow menu** (handles many routes)
4. **Better widths** (improves appearance)
5. **Fixed bar** (nice to have)

---

## 📝 **Code Locations**

**File:** `src/ui/top_nav.py`

**Key Lines:**
- Line 143: Column layout definition
- Line 161: Column creation (PROBLEM)
- Line 170: Popover label (wrapping issue)
- Line 197: Button label (wrapping issue)
- Lines 135-141: Visual container (not connected to buttons)

---

## ✅ **Summary**

**Main Issue:** Creating too many columns (one per route) makes each extremely narrow, causing text to wrap vertically.

**Quick Fix:** Limit to 4-5 visible columns, truncate long names, use overflow menu for rest.

**Better Fix:** Use HTML/CSS flexbox for proper horizontal layout with overflow handling.

---

**Status:** ✅ Diagnosis Complete  
**Next Step:** Implement fixes (when approved)

