# Navigation System Files - Complete List

This document lists all files related to the navigation system in AetherSignal that need to be reviewed for the duplicate button key issue.

## 🔴 Core Navigation Files (Critical)

### 1. Top Navigation
- **`src/ui/top_nav.py`** ⚠️ **PRIMARY ISSUE HERE**
  - Line 272: Button key uses `f"top_nav_sub_{sub_page}"` which becomes `None` when sub_page is None
  - Contains `_render_subpage_button()` function with the problematic key generation

### 2. Sidebar Navigation
- **`src/ui/sidebar.py`**
  - Handles sidebar navigation and routing
  - Uses route-based keys (should be safe)

### 3. Route Configuration
- **`src/ui/layout/routes.py`** ⚠️ **ROUTE DEFINITIONS HERE**
  - Defines all routes and subpages
  - Many subpages have `"page": None` which causes the duplicate key issue
  - Lines 38-78: Safety Intelligence subpages (some have page: None)
  - This is where subpages are configured

### 4. Navigation Handler
- **`src/ui/nav_handler.py`**
  - Handles navigation actions and routing logic

## 🟡 Main Application Files (Entry Points)

### 5. Main App Entry
- **`app.py`**
  - Line 67: Calls `render_top_nav()` where error occurs
  - Main entry point for Streamlit app

### 6. Quantum PV Explorer Page
- **`pages/1_Quantum_PV_Explorer.py`**
  - Main Signal module page
  - Uses sidebar and top navigation

### 7. Social AE Explorer Page
- **`pages/2_Social_AE_Explorer.py`**
  - Social AE module page

## 🟢 Supporting Navigation Components

### 8. Layout Components
- **`src/ui/layout/base_layout.py`**
- **`src/ui/layout/sidebar.py`** (different from main sidebar.py)
- **`src/ui/layout/topnav.py`** (may be legacy/unused)

### 9. Navigation Components
- **`src/ui/components/navigation.py`**
- **`src/ui/intelligence/navigation.py`**

### 10. Other UI Components
- **`src/ui/workspace_status_bar.py`**
- **`src/ui/status_bar_v2.py`**

## 📋 Route Configuration Details

The issue occurs in `src/ui/layout/routes.py` where subpages are defined. Example:
```python
"subpages": {
    "Knowledge Graph": {
        "route": "knowledge_graph",
        "icon": "🕸️",
        "page": None,  # ← This causes the duplicate key!
        "coming_soon": True,
        ...
    },
}
```

When multiple subpages have `"page": None`, they all get the key `top_nav_sub_None`, causing duplicates.

## 🔧 Fix Required

In `src/ui/top_nav.py` line 272, change from:
```python
key=f"top_nav_sub_{sub_page}"  # Becomes "top_nav_sub_None" for multiple items
```

To something unique like:
```python
key=f"top_nav_sub_{route_name}_{subpage_name}"  # Use route + subpage name for uniqueness
```

Or use the route from subpage_config:
```python
key=f"top_nav_sub_{subpage_config.get('route', subpage_name)}"
```

## 📝 Files to Share for Review

### Essential Files (Must Review):
1. `src/ui/top_nav.py` - The file with the bug
2. `src/ui/layout/routes.py` - Route definitions
3. `src/ui/sidebar.py` - Sidebar implementation
4. `app.py` - Entry point

### Supporting Files (For Context):
5. `pages/1_Quantum_PV_Explorer.py` - Main page
6. `src/ui/nav_handler.py` - Navigation logic
7. `src/ui/components/navigation.py` - Additional nav components

## 🎯 Summary

The root cause is in `src/ui/top_nav.py` where button keys are generated using `sub_page` which can be `None`. When multiple subpages have `page: None`, they all get the same key, causing Streamlit's duplicate key error.

The fix should use a unique identifier like the subpage name or route instead of the page value.
