# 🚀 Restart Application & Verification Steps

## 📍 **Current Status**
✅ Application is **already running** on port 8501 (Process ID: 52072)

---

## 🔄 **Step 1: Restart the Application**

### **Option A: Restart via Terminal (Recommended)**

1. **Open PowerShell** in the project directory:
   ```
   C:\Vikas\Projects\aethersignal
   ```

2. **Stop the current Streamlit process:**
   ```powershell
   Stop-Process -Id 52072 -Force
   ```

3. **Wait 2-3 seconds** for the process to stop

4. **Start the application:**
   ```powershell
   streamlit run app.py
   ```

5. **Wait for startup** - You should see:
   ```
   You can now view your Streamlit app in your browser.
   
   Local URL: http://localhost:8501
   ```

---

### **Option B: Quick Restart (If Already Running)**

If the app is already running and you just want to refresh:
- **Just refresh your browser** (F5 or Ctrl+R)
- No need to restart the server

---

## 🌐 **Step 2: Open Application**

1. **Open your web browser** (Chrome, Edge, Firefox)

2. **Navigate to:**
   ```
   http://localhost:8501
   ```

---

## 🔐 **Step 3: Login**

1. **If not logged in:**
   - Click **"Login"** in top navigation
   - Email: `vikasagarwal11@gmail.com`
   - Password: (your password)
   - Click **"Login"**

2. **Verify you're logged in:**
   - Your name should appear in top navigation
   - You should have `super_admin` role

---

## ✅ **Step 4: Verify API Keys Page**

### **Exact Path:**
```
http://localhost:8501/API_Keys
```

**OR navigate via sidebar:**
- Look for "🔐 API Keys" in the sidebar menu
- Click it

---

### **What You Should See:**

1. **Page Header:**
   - ✅ Title: "🔐 Global API Keys"
   - ✅ Caption: "Manage platform-wide API keys for external services..."

2. **Top Navigation:**
   - ✅ Navigation bar at the top
   - ✅ Your name/email visible

3. **Access Control:**
   - ✅ **NO "Access Denied" message**
   - ✅ **NO "Please login" warning**
   - ✅ Page loads completely

4. **API Key Manager Sections:**
   - ✅ **Info Box:** "API Key Management" information
   - ✅ **🆓 Free Data Sources:**
     - PubMed API Key (password field)
     - YouTube API Key (password field)
     - Reddit Client ID (password field)
     - Reddit Secret (password field)
   - ✅ **💳 Paid Data Sources:**
     - OpenAI API Key (password field)
     - Twitter/X API Key (password field)
     - HumanAPI Key (password field)
     - Metriport Key (password field)
     - DrugBank API Key (password field)
     - VigiBase Key (password field)
     - EudraVigilance API Key (password field)
   - ✅ **🏗️ Infrastructure:**
     - Redis Host (text field)
     - Redis Port (number field, default: 6379)
   - ✅ **💾 Save Keys** button (green/primary button)
   - ✅ **📊 Key Status** expander (click to expand)

5. **Test Functionality:**
   - ✅ Click any API key field → Can type (masked as dots)
   - ✅ Click "💾 Save Keys" → Shows success message
   - ✅ Click "📊 Key Status" → Expands to show configured/missing keys

---

## ⚙️ **Step 5: Verify Settings Page**

### **Exact Path:**
```
http://localhost:8501/Settings
```

**OR navigate via sidebar:**
- Look for "⚙️ Settings" in the sidebar menu
- Click it

---

### **What You Should See:**

1. **Page Header:**
   - ✅ Title: "⚙️ Global Platform Settings"
   - ✅ Caption: "Configure platform-wide behavior, feature toggles..."

2. **Top Navigation:**
   - ✅ Navigation bar at the top
   - ✅ Your name/email visible

3. **Access Control:**
   - ✅ **NO "Access Denied" message**
   - ✅ **NO "Please login" warning**
   - ✅ Page loads completely

4. **Settings UI:**
   - ✅ Settings configuration options visible
   - ✅ Pricing toggle (if implemented)
   - ✅ Other platform settings

5. **Test Functionality:**
   - ✅ Can interact with settings
   - ✅ Can save changes (if applicable)

---

## 🧪 **Step 6: Test Access Control (Optional)**

### **Test as Regular User:**

1. **Logout:**
   - Click your name in top navigation
   - Click "Logout"

2. **Try `/API_Keys`:**
   - ✅ Should see: "🔒 Access Denied"
   - ✅ Should see: "This page is only available to platform super administrators"
   - ✅ Should NOT see API key fields

3. **Try `/Settings`:**
   - ✅ Should see: "🔒 Access Denied"
   - ✅ Should see: "This page is only available to platform super administrators"
   - ✅ Should NOT see settings UI

4. **Login again** as `super_admin` to continue

---

## 📋 **Quick Verification Checklist**

### **API Keys Page (`/API_Keys`):**
- [ ] Page loads without errors
- [ ] No "Access Denied" message
- [ ] Top navigation visible
- [ ] All 3 sections visible (Free, Paid, Infrastructure)
- [ ] "Save Keys" button works
- [ ] "Key Status" expander works

### **Settings Page (`/Settings`):**
- [ ] Page loads without errors
- [ ] No "Access Denied" message
- [ ] Top navigation visible
- [ ] Settings UI visible
- [ ] Can interact with settings

---

## 🐛 **Troubleshooting**

### **If You See "Access Denied":**

1. **Check your role:**
   - Go to Supabase SQL Editor
   - Run: `SELECT email, role FROM user_profiles WHERE email = 'vikasagarwal11@gmail.com';`
   - Should show: `role = 'super_admin'`

2. **Logout and login again:**
   - Session might be cached
   - Logout completely
   - Login again

3. **Check browser console (F12):**
   - Look for JavaScript errors
   - Check Network tab for failed requests

---

### **If Page Doesn't Load:**

1. **Check Streamlit is running:**
   - Look at terminal
   - Should see: "Running on http://localhost:8501"

2. **Check for errors:**
   - Look at terminal output
   - Fix any Python errors

3. **Try different port:**
   - If 8501 is busy, Streamlit uses next available port
   - Check terminal for actual URL

---

## ✅ **Success Criteria**

**Everything works if:**
- ✅ Both pages load at their URLs
- ✅ You can see and interact with both pages
- ✅ No "Access Denied" messages (as super_admin)
- ✅ Top navigation appears on both pages
- ✅ No errors in browser console (F12)

---

## 📍 **Exact URLs to Test**

1. **API Keys Page:**
   ```
   http://localhost:8501/API_Keys
   ```

2. **Settings Page:**
   ```
   http://localhost:8501/Settings
   ```

3. **Login Page (if needed):**
   ```
   http://localhost:8501/Login
   ```

---

**Created:** 2025-12-02  
**Status:** Ready to execute

