# app.py Modularization Plan

## Current State
- **Total lines**: 1,584
- **Functions**: 7
- **Major UI sections**: 13
- **Main issue**: `display_query_results()` is ~776 lines (49% of file!)

## Modularization Options

### Option 1: Component-Based (Recommended) ⭐
**Structure**: Extract UI components into separate modules

```
src/
├── ui/
│   ├── __init__.py
│   ├── header.py          # Header, hero, banners
│   ├── upload_section.py  # File upload UI
│   ├── query_interface.py # NL query + advanced search tabs
│   ├── results_display.py # display_query_results() + all tabs
│   ├── sidebar.py         # Sidebar filters and controls
│   └── landing_page.py    # Empty state / landing page
├── app_helpers.py         # Helper functions (load_all_files, etc.)
└── app.py                 # Main orchestrator (~200 lines)
```

**Benefits:**
- ✅ Clear separation of concerns
- ✅ Easy to test individual components
- ✅ Reusable UI components
- ✅ Maintainable (each file <300 lines)

**app.py becomes:**
```python
import streamlit as st
from ui import header, upload_section, query_interface, sidebar
from app_helpers import initialize_session, load_all_files

# Configuration
st.set_page_config(...)
apply_theme()
initialize_session()

# Main flow
header.render()
upload_section.render()
if data_loaded:
    query_interface.render()
sidebar.render()
```

---

### Option 2: Feature-Based
**Structure**: Group by feature/functionality

```
src/
├── features/
│   ├── __init__.py
│   ├── data_upload.py     # Upload + schema detection
│   ├── query_processing.py # NL parsing + filter building
│   ├── results_analysis.py # display_query_results + all analysis
│   └── sidebar_controls.py # Sidebar filters
├── app_helpers.py
└── app.py                 # Main orchestrator
```

**Benefits:**
- ✅ Feature-focused organization
- ✅ Easy to add new features
- ✅ Logical grouping

---

### Option 3: Hybrid (UI + Logic Split)
**Structure**: Separate UI from business logic

```
src/
├── ui/
│   ├── components.py      # Reusable UI components
│   ├── pages.py          # Main page sections
│   └── layouts.py        # Layout helpers
├── app_logic/
│   ├── data_handling.py  # File loading, normalization
│   ├── query_handling.py # Query processing
│   └── results_handling.py # Results calculation
├── app_helpers.py
└── app.py                 # Main orchestrator
```

**Benefits:**
- ✅ Clear UI vs logic separation
- ✅ Easy to swap UI frameworks later
- ✅ Business logic is testable

---

### Option 4: Minimal Refactor (Quick Win)
**Structure**: Extract only the largest functions

```
src/
├── ui_components.py       # display_query_results() + render functions
├── app_helpers.py         # Helper functions
└── app.py                 # Main file (~800 lines)
```

**Benefits:**
- ✅ Fastest to implement (1-2 hours)
- ✅ Minimal changes
- ✅ Still reduces complexity

---

## Recommended: Option 1 (Component-Based)

### Detailed Structure

#### 1. `src/ui/header.py` (~50 lines)
```python
def render_header():
    """Render main header with hero section"""
    st.markdown("""<div class="main-hero">...""")
    
def render_banner():
    """Render disclaimer banner"""
    st.markdown("""<div class="inline-banner">...""")
```

#### 2. `src/ui/upload_section.py` (~150 lines)
```python
def render_upload_section():
    """Render file upload UI and handle loading"""
    # File uploader
    # Load button
    # Schema display
    # KPI metrics
```

#### 3. `src/ui/query_interface.py` (~200 lines)
```python
def render_nl_query_tab():
    """Natural language query interface"""
    
def render_advanced_search_tab():
    """Advanced search tab"""
    
def render_query_interface():
    """Main query interface with tabs"""
    query_tab, watchlist_tab, advanced_tab = st.tabs([...])
    with query_tab:
        render_nl_query_tab()
    # etc.
```

#### 4. `src/ui/results_display.py` (~800 lines)
```python
def render_overview_tab(filters, summary, filtered_df, normalized_df):
    """Overview tab with KPIs and summary"""
    
def render_signals_tab(filters, summary, filtered_df, normalized_df):
    """Signals tab with PRR/ROR and subgroup discovery"""
    
def render_trends_tab(filters, summary, filtered_df, normalized_df):
    """Time trends and co-reactions"""
    
def render_cases_tab(filtered_df):
    """Cases table with export"""
    
def render_report_tab(filters, query_text, summary):
    """PDF report generation"""
    
def display_query_results(filters, query_text, normalized_df):
    """Main results display orchestrator"""
    # Create tabs
    # Call individual tab renderers
```

#### 5. `src/ui/sidebar.py` (~200 lines)
```python
def render_sidebar():
    """Render sidebar with filters and controls"""
    # Reset button
    # Advanced search filters
    # Quantum toggle
    # Usage stats
```

#### 6. `src/app_helpers.py` (~200 lines)
```python
def initialize_session():
    """Initialize session state"""
    
def load_all_files(uploaded_files):
    """Load and combine files"""
    
def _cached_detect_and_normalize(raw_df):
    """Cached schema detection"""
    
def _format_reaction_with_meddra(reaction, meddra_pt):
    """Format reaction with MedDRA PT"""
    
def render_filter_chips(filters):
    """Render filter chips"""
```

#### 7. `app.py` (~200 lines)
```python
import streamlit as st
from styles import apply_theme
from app_helpers import initialize_session, load_all_files
from ui import header, upload_section, query_interface, sidebar

# Configuration
st.set_page_config(...)
apply_theme()
initialize_session()

# Main UI
header.render_header()
header.render_banner()

upload_section.render_upload_section()

if st.session_state.data is not None:
    query_interface.render_query_interface()
    
    if st.session_state.show_results:
        from ui.results_display import display_query_results
        display_query_results(
            st.session_state.last_filters,
            st.session_state.last_query_text,
            st.session_state.normalized_data
        )

sidebar.render_sidebar()
```

---

## File Size After Modularization

| File | Current | After Option 1 |
|------|---------|----------------|
| `app.py` | 1,584 | ~200 |
| `src/ui/results_display.py` | - | ~800 |
| `src/ui/query_interface.py` | - | ~200 |
| `src/ui/sidebar.py` | - | ~200 |
| `src/ui/upload_section.py` | - | ~150 |
| `src/ui/header.py` | - | ~50 |
| `src/app_helpers.py` | - | ~200 |

**Total**: Same functionality, better organized!

---

## Implementation Steps

### Phase 1: Extract Helpers (30 min)
1. Create `src/app_helpers.py`
2. Move helper functions
3. Update imports in `app.py`

### Phase 2: Extract Results Display (1 hour)
1. Create `src/ui/results_display.py`
2. Move `display_query_results()` and tab renderers
3. Test results display

### Phase 3: Extract UI Components (1 hour)
1. Create `src/ui/` directory
2. Extract header, upload, query interface, sidebar
3. Update `app.py` to use components

### Phase 4: Testing & Cleanup (30 min)
1. Test all functionality
2. Fix any import issues
3. Update documentation

**Total time**: ~3 hours

---

## Migration Strategy

### Option A: Big Bang (Recommended if confident)
- Extract everything at once
- Test thoroughly
- One commit

### Option B: Incremental (Safer)
1. Extract helpers first → test
2. Extract results display → test
3. Extract UI components → test
4. Final cleanup

---

## Benefits After Modularization

✅ **Maintainability**: Each file has single responsibility
✅ **Testability**: Can test components independently
✅ **Readability**: `app.py` becomes a clear orchestrator
✅ **Reusability**: UI components can be reused
✅ **Collaboration**: Multiple devs can work on different files
✅ **Performance**: Easier to optimize specific components

---

## Recommendation

**Go with Option 1 (Component-Based)** because:
1. Most maintainable long-term
2. Clear structure
3. Easy to extend
4. Industry-standard pattern

**Implementation approach**: Incremental (Option B) for safety

---

## Next Steps

1. Review this plan
2. Choose option (I recommend Option 1)
3. I'll implement it step-by-step
4. Test after each phase

Ready to proceed? 🚀

