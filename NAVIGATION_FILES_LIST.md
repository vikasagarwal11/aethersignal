# Files Involved in Navigation & Sidebar Setup

This document lists all files that affect the top navigation bar and sidebar behavior in AetherSignal.

## Core Navigation Files

### 1. `src/ui/top_nav.py`
- **Purpose**: Renders the fixed top navigation bar
- **Key Features**:
  - Fixed dark blue navigation bar at top
  - Navigation links: Home, Quantum PV, Social AE
  - Active page highlighting via JavaScript
  - Hides Streamlit's default header
- **Issues**: Navigation clicks not working properly, buttons positioning

### 2. `app.py`
- **Purpose**: Landing page (Home)
- **Key Features**:
  - Calls `render_top_nav()` at line 32
  - Sets `initial_sidebar_state="expanded"`
  - Landing page content with CTA buttons

### 3. `pages/1_Quantum_PV_Explorer.py`
- **Purpose**: Quantum PV Explorer page
- **Key Features**:
  - Calls `render_top_nav()` at line 41
  - Sets `initial_sidebar_state="expanded"` (sidebar always visible)
  - Main application functionality

### 4. `pages/2_Social_AE_Explorer.py`
- **Purpose**: Social AE Explorer page
- **Key Features**:
  - Calls `render_top_nav()` at line 41
  - Sets `initial_sidebar_state="expanded"` (changed from "collapsed")
  - Sidebar toggle should be visible but currently missing

## Styling Files

### 5. `src/styles.py`
- **Purpose**: Centralized CSS styling
- **Key Features**:
  - Line 24-27: Padding for fixed nav bar
  - Line 30-48: Hides Streamlit Deploy button
  - Line 622-636: Sidebar styling
  - Line 43-48: Sidebar toggle visibility rules (recently added)

## Supporting Files

### 6. `src/ui/header.py`
- **Purpose**: Page headers/hero sections
- **Key Features**:
  - `render_header(page_type="quantum"|"social")` - Different headers per page
  - `render_banner()` - Disclaimer banner
  - Not directly related to navigation, but affects page layout

## Current Issues

1. **Top Navigation Not Working**:
   - Buttons in `src/ui/top_nav.py` use `onclick="window.location.href='...'"`
   - Streamlit's routing may not work with direct JavaScript navigation
   - Need to use `st.switch_page()` or proper Streamlit routing

2. **Sidebar Toggle Missing**:
   - Sidebar toggle button disappears on Social AE page
   - CSS in `src/styles.py` may be hiding it
   - `initial_sidebar_state="expanded"` should keep toggle visible

3. **Button Positioning**:
   - Navigation buttons appearing below the nav bar instead of inside it
   - CSS positioning issues in `src/ui/top_nav.py`

## Recommended Fixes

1. **Navigation**: Use Streamlit's native `st.switch_page()` with buttons instead of HTML onclick
2. **Sidebar**: Ensure CSS doesn't hide the toggle button, check Streamlit's sidebar toggle selector
3. **Positioning**: Use proper CSS flexbox/grid or absolute positioning for nav buttons

## File Dependencies

```
app.py
  └─> src/ui/top_nav.py
  └─> src/styles.py (via apply_theme())

pages/1_⚛️_Quantum_PV_Explorer.py
  └─> src/ui/top_nav.py
  └─> src/styles.py (via apply_theme())
  └─> src/ui/header.py

pages/2_🌐_Social_AE_Explorer.py
  └─> src/ui/top_nav.py
  └─> src/styles.py (via apply_theme())
  └─> src/ui/header.py
```

