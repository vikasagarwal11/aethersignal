# Streamlit Page Routing Debug Guide

## 🔍 Issue
**Problem**: "Page not found" error when accessing `http://localhost:8501/1_Quantum_PV_Explorer` directly

**Error Message**: "The page that you have requested does not seem to exist. Running the app's main page."

---

## 📋 Files Involved in Streamlit Page Routing

### **Core Application Files**
1. **`app.py`** (Main entry point)
   - Line 15-20: `st.set_page_config()` for landing page
   - Line 32: Calls `render_top_nav()`
   - Line 78: Uses `st.switch_page("pages/1_Quantum_PV_Explorer.py")` - **This works**
   - Line 82: Uses `st.switch_page("pages/2_Social_AE_Explorer.py")` - **This works**

2. **`pages/1_Quantum_PV_Explorer.py`** (Quantum PV page)
   - Line 18-23: `st.set_page_config()` 
   - Line 41: Calls `render_top_nav()`
   - **File exists and compiles without errors**

3. **`pages/2_Social_AE_Explorer.py`** (Social AE page)
   - Line 18-23: `st.set_page_config()`
   - Line 41: Calls `render_top_nav()`
   - **File exists and compiles without errors**

### **Navigation Files**
4. **`src/ui/top_nav.py`** (Navigation component)
   - Line 110-114: HTML navigation links
   - Line 113: `<a href="/1_Quantum_PV_Explorer">` - **Direct URL navigation (not working)**
   - Line 114: `<a href="/2_Social_AE_Explorer">` - **Direct URL navigation (not working)**
   - Line 245-270: JavaScript click handlers for navigation
   - **Current issue**: Direct href links don't work, but `st.switch_page()` does work

### **Supporting Files**
5. **`src/styles.py`** (CSS styling)
   - May affect page rendering but not routing

6. **`src/app_helpers.py`** (Session initialization)
   - Called by both page files
   - May affect page loading

---

## 🔑 Key Information for Research

### **Streamlit Version**
- **Version**: 1.47.0
- **Command to check**: `python -c "import streamlit as st; print(st.__version__)"`

### **File Structure**
```
aethersignal/
├── app.py                          # Main entry point (landing page)
├── pages/
│   ├── 1_Quantum_PV_Explorer.py   # Page file (exists, compiles)
│   └── 2_Social_AE_Explorer.py    # Page file (exists, compiles)
└── src/
    └── ui/
        └── top_nav.py              # Navigation component
```

### **What Works vs. What Doesn't**

✅ **WORKS:**
- `st.switch_page("pages/1_Quantum_PV_Explorer.py")` from `app.py` buttons
- Pages load correctly when navigated via `st.switch_page()`
- File syntax is correct (no compilation errors)

❌ **DOESN'T WORK:**
- Direct URL access: `http://localhost:8501/1_Quantum_PV_Explorer`
- HTML `<a href="/1_Quantum_PV_Explorer">` links in navigation bar
- Browser bookmarking of page URLs

---

## 🔎 What to Search For / Ask Gemini

### **Search Terms:**
1. "Streamlit 1.47 page not found direct URL access"
2. "Streamlit pages directory direct URL routing not working"
3. "Streamlit st.switch_page works but direct URL doesn't"
4. "Streamlit pages directory URL format localhost"
5. "Streamlit multi-page app direct URL navigation"

### **Questions to Ask Gemini:**

**Question 1:**
```
I have a Streamlit 1.47.0 multi-page app. The pages are in a `pages/` directory:
- `pages/1_Quantum_PV_Explorer.py`
- `pages/2_Social_AE_Explorer.py`

When I use `st.switch_page("pages/1_Quantum_PV_Explorer.py")` from app.py, it works perfectly. 
But when I try to access the page directly via URL `http://localhost:8501/1_Quantum_PV_Explorer`, 
I get "Page not found" error.

The files exist, compile without errors, and work via st.switch_page(). 
What could cause direct URL access to fail?
```

**Question 2:**
```
In Streamlit, what is the correct URL format to access pages in the `pages/` directory?
Should it be:
- `/1_Quantum_PV_Explorer`
- `/pages/1_Quantum_PV_Explorer`
- `/pages/1_Quantum_PV_Explorer.py`
- Something else?

My Streamlit version is 1.47.0.
```

**Question 3:**
```
How do I make HTML navigation links work with Streamlit pages?
Currently I have:
```html
<a href="/1_Quantum_PV_Explorer">Quantum PV</a>
```

But this shows "Page not found". However, `st.switch_page("pages/1_Quantum_PV_Explorer.py")` works.
What's the correct way to create clickable navigation links for Streamlit pages?
```

**Question 4:**
```
Do Streamlit pages need to be registered or configured somewhere?
I have files in `pages/` directory but direct URL access doesn't work.
Do I need a `.streamlit/config.toml` file or any other configuration?
```

---

## 🛠️ Debugging Steps to Try

### **1. Check Streamlit Server Logs**
- Look at the terminal where `streamlit run app.py` is running
- Check for any errors when accessing the URL directly
- Look for page discovery messages

### **2. Verify Page Discovery**
- Restart Streamlit server completely
- Check if pages appear in Streamlit's sidebar navigation
- If pages don't appear in sidebar, Streamlit isn't discovering them

### **3. Test URL Formats**
Try these URL variations:
- `http://localhost:8501/1_Quantum_PV_Explorer`
- `http://localhost:8501/pages/1_Quantum_PV_Explorer`
- `http://localhost:8501/pages/1_Quantum_PV_Explorer.py`
- `http://localhost:8501/?page=1_Quantum_PV_Explorer`

### **4. Check for Configuration Files**
- Look for `.streamlit/config.toml` in project root
- Check if there's a `pages/__init__.py` file (shouldn't be needed, but check)
- Verify no `.streamlit/` directory with custom config

### **5. Test Minimal Example**
Create a minimal test:
```python
# test_app.py
import streamlit as st
st.write("Main app")

# pages/test_page.py  
import streamlit as st
st.write("Test page")
```
See if direct URL works with minimal setup.

---

## 📝 Code Snippets to Share

### **Current Navigation Code (src/ui/top_nav.py)**
```python
# Line 113-114
<a class="nav-link" href="/1_Quantum_PV_Explorer" data-nav="quantum">⚛️ Quantum PV</a>
<a class="nav-link" href="/2_Social_AE_Explorer" data-nav="social">🌐 Social AE</a>
```

### **Working Navigation (app.py)**
```python
# Line 78 - This works!
if st.button("⚛️ Launch Quantum PV Explorer"):
    st.switch_page("pages/1_Quantum_PV_Explorer.py")
```

### **Page File Structure (pages/1_Quantum_PV_Explorer.py)**
```python
import streamlit as st

st.set_page_config(
    page_title="Quantum PV Explorer – AetherSignal",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ... rest of page code
```

---

## 🎯 Possible Root Causes

1. **Streamlit Page Discovery Issue**
   - Server needs restart after creating pages
   - Pages not being discovered at startup

2. **URL Routing Format**
   - Wrong URL format for direct access
   - Streamlit expects different URL structure

3. **Streamlit Version Bug**
   - Known issue in Streamlit 1.47.0
   - Need to upgrade/downgrade

4. **Configuration Missing**
   - Need `.streamlit/config.toml` for page routing
   - Missing page configuration

5. **JavaScript Navigation Conflict**
   - Custom navigation JavaScript interfering
   - Need to use Streamlit's navigation API

---

## 📚 Relevant Documentation Links

- Streamlit Pages Documentation: https://docs.streamlit.io/develop/concepts/multipage-apps
- Streamlit Navigation API: https://docs.streamlit.io/library/api-reference/utilities/st.switch_page
- Streamlit Configuration: https://docs.streamlit.io/develop/concepts/configuration

---

## ✅ Next Steps

1. **Share this document with Gemini** and ask the questions above
2. **Check Streamlit GitHub issues** for similar problems
3. **Test with minimal example** to isolate the issue
4. **Try different Streamlit versions** (1.46, 1.48) to see if it's version-specific
5. **Check Streamlit community forum** for similar issues

---

**Last Updated**: Based on Streamlit 1.47.0, Windows 10, Python project structure

