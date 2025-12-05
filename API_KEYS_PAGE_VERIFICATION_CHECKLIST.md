# ✅ API Keys Page Verification Checklist

## 🎯 **What to Verify on `/API_Keys` Page**

### **1. Access Control (Security)**
- [ ] **As `super_admin` (you):**
  - [ ] Page loads without errors
  - [ ] You can see the full API Key Manager UI
  - [ ] No "Access Denied" message
  - [ ] Top navigation bar is visible

- [ ] **As regular user (test with another account or logout):**
  - [ ] Should see "🔒 Access Denied" error message
  - [ ] Should see "This page is only available to platform super administrators"
  - [ ] Cannot see or edit any API keys

### **2. UI Elements (Visual Check)**
- [ ] **Page Title:** "🔐 Global API Keys"
- [ ] **Caption:** "Manage platform-wide API keys for external services..."
- [ ] **Top Navigation:** Should be visible at the top
- [ ] **Main Content:** API Key Manager interface

### **3. API Key Manager Content**
- [ ] **Info Box:** Shows API Key Management information
- [ ] **Free Data Sources Section:**
  - [ ] PubMed API Key field
  - [ ] YouTube API Key field
  - [ ] Reddit Client ID field
  - [ ] Reddit Secret field

- [ ] **Paid Data Sources Section:**
  - [ ] OpenAI API Key field
  - [ ] Twitter/X API Key field
  - [ ] HumanAPI Key field
  - [ ] Metriport Key field
  - [ ] DrugBank API Key field
  - [ ] VigiBase Key field
  - [ ] EudraVigilance API Key field

- [ ] **Infrastructure Section:**
  - [ ] Redis Host field
  - [ ] Redis Port field (number input)

- [ ] **Save Button:** "💾 Save Keys" button is visible
- [ ] **Key Status Expander:** Can expand to see configured/missing keys

### **4. Functionality Test**
- [ ] **View Keys:** All password fields are masked (showing dots/asterisks)
- [ ] **Edit Keys:** Can type in any field
- [ ] **Save Keys:** Click "Save Keys" button
  - [ ] Should show success message: "API keys updated successfully!"
  - [ ] Should show info: "⚠️ Restart the application for changes to take effect"
- [ ] **Key Status:**
  - [ ] Expand "📊 Key Status" section
  - [ ] See list of configured keys (if any)
  - [ ] See list of missing keys

### **5. Error Handling**
- [ ] **Not Logged In:**
  - [ ] Should show warning: "⚠️ Please login to access API keys."
  - [ ] Should show "Go to Login" button

- [ ] **Wrong Role (if you can test):**
  - [ ] Should show "🔒 Access Denied" error
  - [ ] Should show helpful message about contacting admin

---

## 🧪 **Quick Test Steps**

1. **Open the page:** Navigate to `/API_Keys` in your Streamlit app
2. **Check access:** Verify you can see the page (you're `super_admin`)
3. **Check UI:** Verify all sections are visible
4. **Test save:** Try saving a test key (you can delete it after)
5. **Check status:** Expand "Key Status" to see what's configured

---

## ✅ **Expected Result**

If everything works:
- ✅ Page loads successfully
- ✅ You can see and edit API keys
- ✅ Top navigation is visible
- ✅ No errors in console
- ✅ Save functionality works

---

**Status:** Ready to verify  
**Time:** 2-3 minutes

