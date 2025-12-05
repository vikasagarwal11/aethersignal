# Archived Navigation Files

## Purpose

These files were archived during the Navigation Architecture Refactoring (December 2025). They are **NOT deleted** - they are preserved here for reference to ensure no features or patterns are missed.

## Files Archived

1. **`topnav.py.archived`** (from `src/ui/layout/topnav.py`)
   - **Original Purpose:** Alternative top navigation implementation using Streamlit-native columns
   - **Features:** Search bar, theme toggle, copilot button
   - **Why Archived:** Unused - `src/ui/top_nav.py` is the active implementation
   - **Status:** Not imported or used anywhere

2. **`layout_sidebar.py.archived`** (from `src/ui/layout/sidebar.py`)
   - **Original Purpose:** Sidebar implementation that uses `routes.py` for navigation structure
   - **Features:** Expandable sections, subpages, admin routes, role-based filtering
   - **Why Archived:** Unused - `src/ui/sidebar.py` is the active implementation
   - **Status:** Not imported or used anywhere
   - **Important:** This file shows how to use `routes.py` - reference for Phase 2 implementation

3. **`components_navigation.py.archived`** (from `src/ui/components/navigation.py`)
   - **Original Purpose:** Alternative navigation component with PAGES dictionary
   - **Features:** Category-based navigation, breadcrumbs, page header rendering
   - **Why Archived:** Unused - not imported or used anywhere
   - **Status:** Not imported or used anywhere

4. **`sidebar_enhanced.py.archived`** (from `src/ui/sidebar_enhanced.py`)
   - **Original Purpose:** Enhanced sidebar with organized sections
   - **Features:** Datasets, Analytics, AI Assistance, Signal Docs, System sections
   - **Why Archived:** Unused - `src/ui/sidebar.py` is the active implementation
   - **Status:** Not imported or used anywhere
   - **Note:** May contain useful UI patterns for future reference

5. **`sidebar_final.py.archived`** (from `src/ui/sidebar_final.py`)
   - **Original Purpose:** Final sidebar design with compact/expanded/inspector modes
   - **Features:** Mode switching, pill badges, inspector-focused view
   - **Why Archived:** Unused - `src/ui/sidebar.py` is the active implementation
   - **Status:** Not imported or used anywhere
   - **Note:** May contain useful UI patterns for future reference

## Verification Checklist

After refactoring is complete, review these files to ensure:

- [ ] No unique features were missed
- [ ] No useful UI patterns were lost
- [ ] All route definitions from `layout_sidebar.py` are in the new implementation
- [ ] All navigation patterns are preserved or intentionally removed
- [ ] No page references are broken

## When to Delete

These files can be safely deleted **ONLY AFTER**:
1. ✅ Phase 4 is complete
2. ✅ All tests pass
3. ✅ Final verification checklist is complete
4. ✅ No features from these files are needed
5. ✅ Team confirms no future reference needed

**Recommendation:** Keep for at least 3 months after refactoring completion.

---

**Archived Date:** 2025-12-03  
**Refactoring Phase:** Pre-Phase 1  
**Status:** Preserved for reference

