# 🎯 Exact Verification Steps - API Keys & Settings Pages

## 📍 **Step 1: Restart the Application**

### **Option A: Using Command Line (Recommended)**

1. **Open PowerShell/Terminal** in the project directory:
   ```
   C:\Vikas\Projects\aethersignal
   ```

2. **Stop any running Streamlit process** (if running):
   ```powershell
   # Find and stop Streamlit
   Get-Process | Where-Object {$_.ProcessName -eq "streamlit"} | Stop-Process -Force
   ```

3. **Start the application:**
   ```powershell
   streamlit run app.py
   ```

   **OR use the batch file:**
   ```powershell
   .\scripts\start_server.bat
   ```

4. **Wait for the app to start** - You should see:
   ```
   You can now view your Streamlit app in your browser.
   
   Local URL: http://localhost:8501
   Network URL: http://192.168.x.x:8501
   ```

---

### **Option B: If App is Already Running**

If the app is already running, you can just **refresh your browser** - no need to restart.

---

## 🌐 **Step 2: Open the Application**

1. **Open your web browser** (Chrome, Edge, Firefox, etc.)

2. **Navigate to:**
   ```
   http://localhost:8501
   ```

3. **If port 8501 is busy**, check the terminal for the actual port number (might be 8502, 8503, etc.)

---

## 🔐 **Step 3: Login (If Not Already Logged In)**

1. **Click "Login"** in the top navigation (or go to `/Login`)

2. **Enter your credentials:**
   - Email: `vikasagarwal11@gmail.com`
   - Password: (your password)

3. **Click "Login"**

4. **Verify you're logged in:**
   - Your name should appear in the top navigation
   - You should see your role as `super_admin` (check Profile page if needed)

---

## ✅ **Step 4: Verify API Keys Page**

### **Navigate to API Keys Page:**

**Method 1: Direct URL**
```
http://localhost:8501/API_Keys
```

**Method 2: Via Sidebar**
- Look for "API Keys" or "🔐 API Keys" in the sidebar
- Click it

**Method 3: Type in Browser**
- In the browser address bar, type: `/API_Keys` after `localhost:8501`

---

### **What to Check on API Keys Page:**

1. **Page Title:**
   - ✅ Should see: "🔐 Global API Keys"
   - ✅ Should see caption: "Manage platform-wide API keys..."

2. **Top Navigation:**
   - ✅ Top navigation bar should be visible
   - ✅ Should show your name/email in top right

3. **Access Control:**
   - ✅ **NO "Access Denied" message**
   - ✅ **NO "Please login" warning**
   - ✅ Page loads completely

4. **API Key Manager UI:**
   - ✅ Should see info box about API Key Management
   - ✅ Should see "🆓 Free Data Sources" section with:
     - PubMed API Key field
     - YouTube API Key field
     - Reddit Client ID field
     - Reddit Secret field
   - ✅ Should see "💳 Paid Data Sources" section with:
     - OpenAI API Key field
     - Twitter/X API Key field
     - HumanAPI Key field
     - Metriport Key field
     - DrugBank API Key field
     - VigiBase Key field
     - EudraVigilance API Key field
   - ✅ Should see "🏗️ Infrastructure" section with:
     - Redis Host field
     - Redis Port field
   - ✅ Should see "💾 Save Keys" button
   - ✅ Should see "📊 Key Status" expander

5. **Functionality Test:**
   - ✅ Click on any API key field - should be able to type (fields are password-masked)
   - ✅ Click "💾 Save Keys" button - should show success message
   - ✅ Expand "📊 Key Status" - should show configured/missing keys

---

## ⚙️ **Step 5: Verify Settings Page**

### **Navigate to Settings Page:**

**Method 1: Direct URL**
```
http://localhost:8501/Settings
```

**Method 2: Via Sidebar**
- Look for "Settings" or "⚙️ Settings" in the sidebar
- Click it

**Method 3: Type in Browser**
- In the browser address bar, type: `/Settings` after `localhost:8501`

---

### **What to Check on Settings Page:**

1. **Page Title:**
   - ✅ Should see: "⚙️ Global Platform Settings"
   - ✅ Should see caption: "Configure platform-wide behavior..."

2. **Top Navigation:**
   - ✅ Top navigation bar should be visible
   - ✅ Should show your name/email in top right

3. **Access Control:**
   - ✅ **NO "Access Denied" message**
   - ✅ **NO "Please login" warning**
   - ✅ Page loads completely

4. **Settings UI:**
   - ✅ Should see settings configuration options
   - ✅ Should see pricing toggle (if implemented)
   - ✅ Should see other platform settings

5. **Functionality Test:**
   - ✅ Can interact with settings
   - ✅ Can save changes (if applicable)

---

## 🧪 **Step 6: Test Access Control (Optional)**

### **Test as Regular User:**

1. **Logout:**
   - Click your name in top navigation
   - Click "Logout" (or go to `/Login` and logout)

2. **Try to access `/API_Keys`:**
   - ✅ Should see: "🔒 Access Denied"
   - ✅ Should see: "This page is only available to platform super administrators"
   - ✅ Should NOT see API key fields

3. **Try to access `/Settings`:**
   - ✅ Should see: "🔒 Access Denied"
   - ✅ Should see: "This page is only available to platform super administrators"
   - ✅ Should NOT see settings UI

4. **Login again** as `super_admin` to continue

---

## 📋 **Quick Verification Checklist**

### **API Keys Page:**
- [ ] Page loads at `http://localhost:8501/API_Keys`
- [ ] No "Access Denied" message
- [ ] Top navigation visible
- [ ] All API key sections visible (Free, Paid, Infrastructure)
- [ ] "Save Keys" button works
- [ ] "Key Status" expander works

### **Settings Page:**
- [ ] Page loads at `http://localhost:8501/Settings`
- [ ] No "Access Denied" message
- [ ] Top navigation visible
- [ ] Settings UI visible
- [ ] Can interact with settings

### **Access Control:**
- [ ] Regular users see "Access Denied" on both pages
- [ ] Only `super_admin` can access

---

## 🐛 **Troubleshooting**

### **If API Keys Page Shows "Access Denied":**

1. **Check your role in database:**
   ```sql
   SELECT email, role FROM user_profiles WHERE email = 'vikasagarwal11@gmail.com';
   ```
   - Should show `role = 'super_admin'`

2. **Logout and login again:**
   - Session might be cached with old role
   - Logout completely
   - Login again

3. **Check browser console:**
   - Press F12 → Console tab
   - Look for any JavaScript errors

### **If Page Doesn't Load:**

1. **Check Streamlit is running:**
   - Look at terminal for errors
   - Should see "Running on http://localhost:8501"

2. **Check port number:**
   - If 8501 is busy, Streamlit uses next available port
   - Check terminal for actual URL

3. **Check for Python errors:**
   - Look at terminal output
   - Fix any import or syntax errors

---

## ✅ **Success Criteria**

**Everything is working if:**
- ✅ Both pages load without errors
- ✅ You can see and interact with both pages as `super_admin`
- ✅ Regular users see "Access Denied"
- ✅ Top navigation appears on both pages
- ✅ No errors in browser console (F12)

---

**Created:** 2025-12-02  
**Status:** Ready to execute

