# 📋 Streamlit Auto-Sidebar Explanation

## 🔍 **What is Streamlit Auto-Sidebar?**

Streamlit has a **built-in feature** that automatically creates a navigation sidebar from all files in your `pages/` directory.

### **How It Works:**

1. **Automatic Detection:** Streamlit scans your `pages/` folder
2. **Auto-Generation:** Creates sidebar links for every `.py` file found
3. **No Configuration Needed:** It just happens automatically

### **Example:**

If you have:
```
pages/
├── 1_Quantum_PV_Explorer.py
├── 2_Social_AE_Explorer.py
├── Billing.py
├── Settings.py
└── Login.py
```

Streamlit automatically shows ALL of these in a sidebar navigation, like:
```
📄 1_Quantum_PV_Explorer
📄 2_Social_AE_Explorer
📄 Billing
📄 Settings
📄 Login
```

---

## ⚠️ **The Problem**

You have **TWO sidebars**:

1. **Streamlit's Auto-Generated Sidebar** (built-in, shows all pages)
2. **Your Custom Sidebar** (`src/ui/sidebar.py` - your workspace controls, filters, etc.)

This creates **confusion** because:
- Users see duplicate navigation
- Your custom sidebar (with workspace selection, filters) conflicts with Streamlit's auto-sidebar
- It looks unprofessional

---

## ✅ **Solution: Hide the Auto-Sidebar**

You need to **hide Streamlit's auto-generated sidebar** so only your custom sidebar shows.

### **Two Options:**

#### **Option A: CSS Hide (Recommended - Simpler)**
Hide it with CSS in `src/styles.py`

**Pros:**
- ✅ Simple - just add CSS
- ✅ Works immediately
- ✅ Easy to toggle on/off
- ✅ No config file changes

**Cons:**
- ⚠️ Still generated in DOM (minor performance impact)
- ⚠️ Could break if Streamlit changes CSS selectors (rare)

#### **Option B: Config File (More Robust)**
Disable it via `.streamlit/config.toml`

**Pros:**
- ✅ Official Streamlit setting
- ✅ Won't break with updates
- ✅ Better performance (doesn't generate at all)

**Cons:**
- ⚠️ Requires config file
- ⚠️ Affects entire app globally

---

## 🎯 **My Recommendation: Option A (CSS Hide)**

**Why?**
1. You already have CSS in `src/styles.py` (I can see it)
2. It's simpler - just add a few lines
3. It's reversible - easy to remove if needed
4. It works immediately

**Implementation:**
Add this CSS to `src/styles.py`:

```css
/* Hide Streamlit's auto-generated page navigation sidebar */
section[data-testid="stSidebarNav"] {
    display: none !important;
}

/* Alternative selector if the above doesn't work */
.css-1d391kg {
    display: none !important;
}
```

---

## 📝 **Decision**

**Recommended:** Use **CSS Hide (Option A)** in Phase 2

**When:** Add to `src/styles.py` during Phase 2.4

**Why:** Simple, works immediately, already have CSS infrastructure

---

**Status:** Decision made - CSS Hide approach  
**File to Update:** `src/styles.py`  
**Phase:** 2.4 (Handle Streamlit Auto-Sidebar)

