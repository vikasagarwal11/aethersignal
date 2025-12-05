# 🔍 AetherSignal Navigation & Access Control Assessment

## Executive Summary

This document provides a comprehensive analysis of the current navigation structure, authentication/authorization, role management, and module organization in AetherSignal. It identifies gaps, inconsistencies, and provides recommendations for a cleaner, more secure, and logically organized system.

---

## 1. CURRENT STRUCTURE ANALYSIS

### 1.1 Sidebar Navigation Structure

**Current Sidebar (`src/ui/sidebar.py`):**
- **Controls Section:**
  - Login/Register buttons (if not authenticated)
  - Profile button (if authenticated)
  - Clear Filters & Results
  - Workspace selector (6 options)
  - Processing Mode selector
  - Analytics Tools (conditional)
  - Advanced Search
  - Quantum ranking toggle
  - Social AE signals toggle
  - Performance Stats
  - Audit Trail
  - Usage Statistics
  - Developer Tools

**Issues Identified:**
1. ❌ **No logical grouping** - Everything is flat, no clear hierarchy
2. ❌ **Mixed concerns** - Authentication, workspace, filters, and settings all mixed together
3. ❌ **No role-based visibility** - All users see everything
4. ❌ **No admin/super admin sections** - Admin features scattered

---

### 1.2 Top Navigation Bar

**Current Top Nav (`src/ui/top_nav.py`):**
- Home
- Quantum PV
- Social AE
- Login/Register (or Profile/Logout if authenticated)

**Issues Identified:**
1. ❌ **Not present on all pages** - Missing from Settings, API Keys, and some other pages
2. ❌ **No profile dropdown** - Profile link is just text, not a proper dropdown menu
3. ❌ **Limited navigation** - Only 3 main links, doesn't reflect full app structure
4. ❌ **No role-based visibility** - Same for all users

**Pages WITH Top Nav:**
- ✅ `2_Social_AE_Explorer.py`
- ✅ `1_Quantum_PV_Explorer.py`
- ✅ `3_AE_Explorer.py`
- ✅ `Billing.py`
- ✅ `Onboarding.py`
- ✅ `Demo_Landing.py`
- ✅ `Demo_Home.py`
- ✅ `98_🔐_Data_Source_Manager.py`
- ✅ `Admin_Data_Sources.py`
- ✅ `Profile.py`
- ✅ `Register.py`
- ✅ `Login.py`

**Pages WITHOUT Top Nav:**
- ❌ `Settings.py` - **MISSING**
- ❌ `API_Keys.py` - **MISSING**

---

### 1.3 Route Structure (`src/ui/layout/routes.py`)

**Current Routes:**
```
ROUTES:
├── Executive Dashboard
├── Safety Intelligence
│   ├── Mechanism Explorer
│   ├── Knowledge Graph
│   ├── Label Gap Viewer
│   ├── Risk Dashboard
│   └── Safety Copilot
├── Evidence Governance
│   ├── Lineage Viewer
│   ├── Provenance Explorer
│   └── Data Quality
├── Data Explorer
│   ├── Quantum PV Explorer
│   ├── AE Explorer
│   ├── Social AE Explorer
│   └── Multi-Dimensional Explorer
└── Workflows
    ├── Workflow Dashboard
    └── Report Builder

ADMIN_ROUTES:
├── Data Sources
└── Settings
```

**Issues Identified:**
1. ❌ **Not aligned with user's mental model** - User thinks: "2 main modules (Signal + Social) + Admin"
2. ❌ **Too many top-level categories** - 5 main sections is too many
3. ❌ **Unclear hierarchy** - What's the difference between "Data Explorer" and "Executive Dashboard"?
4. ❌ **Admin routes separate** - Should be integrated with role-based visibility

---

## 2. AUTHENTICATION & AUTHORIZATION GAPS

### 2.1 Current Role System

**Database Schema (`database/schema.sql`):**
```sql
role TEXT DEFAULT 'scientist' CHECK (role IN ('admin', 'scientist', 'viewer'))
```

**Issues:**
1. ❌ **No "super_admin" role** - Only "admin", "scientist", "viewer"
2. ❌ **No organization-level admin** - Can't distinguish between platform owner and org admin
3. ❌ **Role checking inconsistent** - Some places check `role == "admin"`, others check `role == "super_admin"`

### 2.2 API Keys Page Security

**Current State (`pages/API_Keys.py`):**
- ❌ **NO authentication check** - Anyone can access
- ❌ **NO role check** - No super admin requirement
- ❌ **NO top navigation** - Missing top nav bar

**Expected Behavior:**
- ✅ Should require authentication
- ✅ Should require super_admin role
- ✅ Should have top navigation bar

### 2.3 Settings Page Security

**Current State (`pages/Settings.py`):**
- ❌ **NO authentication check** - Anyone can access
- ✅ **Partial role check** - Pricing toggle checks `is_super_admin()`, but page itself is accessible
- ❌ **NO top navigation** - Missing top nav bar

**Expected Behavior:**
- ✅ Should require authentication
- ✅ Should require super_admin role for global settings
- ✅ Should have top navigation bar

---

## 3. MODULE ORGANIZATION ANALYSIS

### 3.1 User's Mental Model

**User's Understanding:**
```
AetherSignal
├── 1. Signal Module (Quantum PV Explorer)
│   └── All signal detection, FAERS analysis, quantum ranking
├── 2. Social AE Module (Social AE Explorer)
│   └── All social media adverse event detection
└── 3. Admin/Profile
    ├── Settings
    ├── API Keys
    ├── Data Sources
    └── User Profile
```

### 3.2 Current Implementation

**Current Structure:**
```
AetherSignal
├── Executive Dashboard (separate)
├── Safety Intelligence (separate)
├── Evidence Governance (separate)
├── Data Explorer
│   ├── Quantum PV Explorer
│   ├── AE Explorer
│   ├── Social AE Explorer
│   └── Multi-Dimensional Explorer
├── Workflows (separate)
└── Admin (separate)
```

**Gap Analysis:**
- ❌ **Too fragmented** - User sees 5+ top-level sections instead of 2 main modules
- ❌ **Unclear boundaries** - Where does "Executive Dashboard" fit? Is it part of Signal or separate?
- ❌ **Safety Intelligence** - Is this part of Signal module or separate?
- ❌ **Evidence Governance** - Is this part of Signal module or separate?
- ❌ **Workflows** - Is this part of Signal module or separate?

---

## 4. PROFILE & USER MANAGEMENT

### 4.1 Current Profile Features

**Top Navigation:**
- Shows user email as text
- "Profile" link (text, not dropdown)
- "Logout" link (text, not dropdown)

**Issues:**
- ❌ **No dropdown menu** - Profile/logout are just links
- ❌ **No profile picture/avatar** - No visual user indicator
- ❌ **No quick access menu** - Can't access settings/profile quickly
- ❌ **No role indicator** - Can't see if you're admin/super_admin

### 4.2 User API Keys

**Current State:**
- ❌ **No user-level API keys** - Only global API keys in Settings
- ❌ **No AI feature configuration** - Users can't provide their own OpenAI keys for Copilot

**Expected Behavior:**
- ✅ Users should be able to provide their own API keys (OpenAI, etc.) in Profile
- ✅ These should override global keys for that user
- ✅ Should be stored per-user, not globally

---

## 5. SUPER ADMIN REQUIREMENTS

### 5.1 What Should Be Super Admin Only?

**Platform-Level Configuration (Super Admin Only):**
1. ✅ **Global API Keys** - Platform-wide API keys (OpenAI, Twitter, etc.)
2. ✅ **Feature Toggles** - Enable/disable features globally
3. ✅ **Pricing System Toggle** - Enable/disable pricing
4. ✅ **Data Source Configuration** - Which sources are enabled
5. ✅ **System Mode** - MVP/Research/Enterprise
6. ✅ **Performance Settings** - Caching, GPU acceleration
7. ✅ **Logging Configuration** - Log levels, destinations

**Organization-Level Configuration (Org Admin):**
1. ✅ **Organization API Keys** - Override global keys for their org
2. ✅ **Organization Feature Toggles** - Enable/disable features for their org
3. ✅ **Organization Settings** - Regulatory config, product config
4. ✅ **User Management** - Add/remove users in their org
5. ✅ **Billing** - View billing for their org

**User-Level Configuration (All Users):**
1. ✅ **Personal API Keys** - Override org/global keys for personal use
2. ✅ **Profile Settings** - Name, email, preferences
3. ✅ **Personal Workspace** - Saved queries, bookmarks

---

## 6. RECOMMENDED STRUCTURE

### 6.1 Simplified Navigation Structure

```
AetherSignal
├── 🏠 Home
├── ⚛️ Signal Explorer (Quantum PV)
│   ├── Signal Detection
│   ├── Executive Dashboard
│   ├── Safety Intelligence
│   │   ├── Mechanism Explorer
│   │   ├── Knowledge Graph
│   │   ├── Label Gap Viewer
│   │   ├── Risk Dashboard
│   │   └── Safety Copilot
│   ├── Evidence Governance
│   │   ├── Lineage Viewer
│   │   ├── Provenance Explorer
│   │   └── Data Quality
│   └── Workflows
│       ├── Workflow Dashboard
│       └── Report Builder
├── 🌐 Social AE Explorer
│   └── (All social media AE features)
└── 👤 Profile & Admin
    ├── Profile
    ├── Settings (if org admin)
    ├── API Keys (if org admin or super admin)
    ├── Data Sources (if super admin)
    └── Billing (if org admin)
```

### 6.2 Role Hierarchy

```
super_admin (Platform Owner - You)
├── Full access to everything
├── Global settings
├── Global API keys
├── Feature toggles
└── Can manage all organizations

org_admin (Organization Admin)
├── Access to Signal + Social AE
├── Organization settings
├── Organization API keys
├── User management (within org)
└── Billing (for org)

scientist (Regular User)
├── Access to Signal + Social AE
├── Personal profile
├── Personal API keys (for AI features)
└── No admin access

viewer (Read-Only User)
├── Read-only access to Signal + Social AE
└── No write/admin access
```

---

## 7. SPECIFIC ISSUES TO FIX

### 7.1 Critical Security Issues

1. **API Keys Page** - ❌ No authentication, no role check
2. **Settings Page** - ❌ No authentication, partial role check
3. **Top Navigation** - ❌ Missing on Settings and API Keys pages

### 7.2 Navigation Issues

1. **Sidebar** - ❌ Too cluttered, no logical grouping
2. **Top Nav** - ❌ Missing on some pages, no profile dropdown
3. **Route Structure** - ❌ Doesn't match user's mental model

### 7.3 Missing Features

1. **Super Admin Role** - ❌ Not properly implemented in database
2. **User API Keys** - ❌ No way for users to provide their own keys
3. **Profile Dropdown** - ❌ No dropdown menu in top nav
4. **Role Indicators** - ❌ No visual indication of user role

---

## 8. RECOMMENDED IMPLEMENTATION PLAN

### Phase 1: Security Fixes (Critical)
1. ✅ Add authentication check to API Keys page
2. ✅ Add super_admin role check to API Keys page
3. ✅ Add authentication check to Settings page
4. ✅ Add super_admin role check to Settings page
5. ✅ Add top navigation to Settings and API Keys pages

### Phase 2: Role System Enhancement
1. ✅ Add "super_admin" role to database schema
2. ✅ Create manual database record for super admin (you)
3. ✅ Update `is_super_admin()` to check for "super_admin" role
4. ✅ Add organization-level admin support

### Phase 3: Navigation Restructure
1. ✅ Simplify sidebar - group by function
2. ✅ Add profile dropdown to top nav
3. ✅ Restructure routes to match user's mental model
4. ✅ Add role-based visibility to navigation items

### Phase 4: User Features
1. ✅ Add user-level API keys in Profile
2. ✅ Add role indicators in UI
3. ✅ Add organization-level settings for org admins

---

## 9. DATABASE CHANGES NEEDED

### 9.1 Add Super Admin Role

```sql
-- Update role constraint to include super_admin
ALTER TABLE user_profiles 
DROP CONSTRAINT IF EXISTS user_profiles_role_check;

ALTER TABLE user_profiles 
ADD CONSTRAINT user_profiles_role_check 
CHECK (role IN ('super_admin', 'admin', 'scientist', 'viewer'));

-- Create super admin record (manually, for you)
-- Replace YOUR_EMAIL and YOUR_USER_ID with your actual values
UPDATE user_profiles 
SET role = 'super_admin' 
WHERE email = 'YOUR_EMAIL';

-- Or insert if doesn't exist:
INSERT INTO user_profiles (id, email, full_name, organization, role)
VALUES (
    'YOUR_USER_ID',  -- Your Supabase auth user ID
    'YOUR_EMAIL',
    'Your Name',
    'AetherSignal Platform',
    'super_admin'
) ON CONFLICT (id) DO UPDATE SET role = 'super_admin';
```

### 9.2 Add User API Keys Table

```sql
-- Table for user-level API keys (overrides global/org keys)
CREATE TABLE IF NOT EXISTS user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    key_name TEXT NOT NULL,  -- e.g., 'OPENAI_API_KEY'
    key_value TEXT NOT NULL,  -- encrypted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, key_name)
);

-- RLS: Users can only see their own keys
ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own keys"
    ON user_api_keys FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own keys"
    ON user_api_keys FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own keys"
    ON user_api_keys FOR UPDATE
    USING (auth.uid() = user_id);
```

---

## 10. SUMMARY OF FINDINGS

### Critical Issues (Fix Immediately)
1. ❌ **API Keys page not password protected** - Security risk
2. ❌ **Settings page not password protected** - Security risk
3. ❌ **Top navigation missing on Settings/API Keys** - UX issue
4. ❌ **No super_admin role in database** - Can't properly restrict access

### High Priority Issues
1. ❌ **Sidebar too cluttered** - Needs logical grouping
2. ❌ **Navigation doesn't match user's mental model** - Too fragmented
3. ❌ **No profile dropdown** - Poor UX
4. ❌ **No user-level API keys** - Users can't provide their own keys

### Medium Priority Issues
1. ⚠️ **Role indicators missing** - Can't see if you're admin
2. ⚠️ **Organization admin not implemented** - Only super admin and regular users
3. ⚠️ **Route structure too complex** - 5 top-level sections is too many

---

## 11. NEXT STEPS

1. **Review this assessment** - Confirm understanding of issues
2. **Prioritize fixes** - Decide what to fix first
3. **Implement security fixes** - Add authentication/authorization to API Keys and Settings
4. **Add super_admin role** - Update database and code
5. **Restructure navigation** - Simplify to match user's mental model
6. **Add user features** - User API keys, profile dropdown, role indicators

---

**Document Created:** 2025-12-02
**Status:** Assessment Complete - Awaiting Implementation Approval

