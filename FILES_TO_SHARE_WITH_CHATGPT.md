# Files to Share with ChatGPT for Navigation Duplicate Key Issue

## 🔴 Critical Files (Must Share)

1. **`src/ui/top_nav.py`** - Contains the bug at line 272
2. **`src/ui/layout/routes.py`** - Defines routes with subpages that have `page: None`
3. **`src/ui/sidebar.py`** - Sidebar navigation implementation
4. **`app.py`** - Entry point that calls render_top_nav()

## 📋 Error Details

**Error Message:**
```
Top nav error: There are multiple elements with the same key='top_nav_sub_None'
```

**Root Cause:**
In `src/ui/top_nav.py` line 272, the button key is generated as:
```python
key=f"top_nav_sub_{sub_page}"
```

When multiple subpages have `"page": None` in `src/ui/layout/routes.py`, they all get the same key `top_nav_sub_None`.

**Example from routes.py:**
- "Knowledge Graph": `page: None`
- "Label Gap Viewer": `page: None`
- "Risk Dashboard": `page: None`
- "Safety Copilot": `page: None`

All of these create buttons with key `top_nav_sub_None`, causing duplicates.

## 🔧 Suggested Fix

Change the key generation in `_render_subpage_button()` to use a unique identifier:

Option 1: Use subpage name
```python
key=f"top_nav_sub_{subpage_name}"
```

Option 2: Use route from config (preferred)
```python
key=f"top_nav_sub_{subpage_config.get('route', subpage_name)}"
```

Option 3: Use route_name + subpage_name for full uniqueness
```python
key=f"top_nav_{route_name}_{subpage_config.get('route', subpage_name)}"
```

## 📁 Supporting Files (For Full Context - Optional)

5. `pages/1_Quantum_PV_Explorer.py`
6. `src/ui/nav_handler.py`
7. `src/ui/components/navigation.py`

## 🎯 Quick Summary for ChatGPT

The navigation system has a duplicate key error because button keys are generated using the `page` value, which is `None` for multiple "coming soon" subpages. The fix should use a unique identifier like the subpage route or name instead.

