# User Account Management Implementation Plan

## Overview

Implementing user account management using **Supabase Authentication** (already integrated). This enables:
- User registration and login
- Multi-tenant data isolation
- User profiles and settings
- Role-based access control (basic)
- Session management
- Password reset and email verification

---

## What Supabase Authentication Provides

### Built-in Features ✅

1. **Authentication Methods**
   - Email/password
   - Magic links (passwordless)
   - OAuth (Google, GitHub, etc.)
   - Phone/SMS (optional)

2. **User Management**
   - User registration
   - Login/logout
   - Password reset
   - Email verification
   - User profiles (metadata)

3. **Security**
   - JWT tokens
   - Session management
   - Password hashing (bcrypt)
   - Rate limiting
   - Email verification

4. **Multi-Tenant Support**
   - Row-Level Security (RLS)
   - User ID in every request
   - Automatic data isolation

---

## Implementation Plan

### Phase 1: Core Authentication (Week 1)

#### 1.1 Authentication Module (`src/auth/`)
- `auth.py` - Main authentication functions
- `user_management.py` - User CRUD operations
- `session_manager.py` - Session handling

#### 1.2 UI Components (`src/ui/auth/`)
- `login.py` - Login page
- `register.py` - Registration page
- `profile.py` - User profile page
- `password_reset.py` - Password reset flow

#### 1.3 Database Schema
```sql
-- Supabase automatically creates auth.users table
-- We need to create user_profiles table for additional data

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    organization TEXT,
    role TEXT DEFAULT 'user', -- 'admin', 'scientist', 'viewer'
    subscription_tier TEXT DEFAULT 'free', -- 'free', 'pro', 'enterprise'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own profile
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

-- Policy: Users can update own profile
CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id);
```

---

### Phase 2: Multi-Tenant Data Isolation (Week 1-2)

#### 2.1 Update PV Data Schema
```sql
-- Add user_id to all data tables
ALTER TABLE pv_cases ADD COLUMN user_id UUID REFERENCES auth.users(id);
ALTER TABLE pv_cases ADD COLUMN created_at TIMESTAMP DEFAULT NOW();

-- Enable RLS on pv_cases
ALTER TABLE pv_cases ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
CREATE POLICY "Users can view own cases"
    ON pv_cases FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own data
CREATE POLICY "Users can insert own cases"
    ON pv_cases FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own data
CREATE POLICY "Users can update own cases"
    ON pv_cases FOR UPDATE
    USING (auth.uid() = user_id);
```

#### 2.2 Update Data Loading
- Modify `load_all_files()` to associate data with current user
- Update `src/pv_storage.py` to include user_id in all operations

---

### Phase 3: UI Integration (Week 2)

#### 3.1 Navigation Updates
- Add "Login" / "Register" buttons to top nav
- Add user menu (profile, settings, logout)
- Show user info in sidebar

#### 3.2 Protected Routes
- Check authentication before showing data
- Redirect to login if not authenticated
- Show different UI based on user role

#### 3.3 User Profile Page
- Display user info
- Edit profile
- Change password
- Subscription info
- Usage statistics

---

### Phase 4: Role-Based Access Control (Week 2-3)

#### 4.1 Roles
- **Admin**: Full access, user management
- **Scientist**: Full analysis features
- **Viewer**: Read-only access

#### 4.2 Permission System
- Check role before allowing actions
- Hide/disable features based on role
- Audit trail for admin actions

---

## File Structure

```
src/
├── auth/
│   ├── __init__.py
│   ├── auth.py              # Authentication functions
│   ├── user_management.py   # User CRUD
│   └── session_manager.py   # Session handling
├── ui/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── login.py         # Login UI
│   │   ├── register.py      # Registration UI
│   │   ├── profile.py       # User profile UI
│   │   └── password_reset.py # Password reset UI
│   └── ... (existing UI files)
└── pv_storage.py            # NEW: PV data persistence with user_id
```

---

## Implementation Steps

### Step 1: Create Authentication Module

**File:** `src/auth/auth.py`
- `login_user(email, password)` - Login function
- `register_user(email, password, full_name)` - Registration
- `logout_user()` - Logout
- `get_current_user()` - Get current user from session
- `reset_password(email)` - Password reset
- `verify_email(token)` - Email verification

### Step 2: Create User Management Module

**File:** `src/auth/user_management.py`
- `get_user_profile(user_id)` - Get user profile
- `update_user_profile(user_id, data)` - Update profile
- `get_user_role(user_id)` - Get user role
- `set_user_role(user_id, role)` - Set user role (admin only)

### Step 3: Create UI Components

**File:** `src/ui/auth/login.py`
- Login form (email, password)
- "Forgot password?" link
- "Register" link
- Error handling

**File:** `src/ui/auth/register.py`
- Registration form (email, password, full_name, organization)
- Terms of service checkbox
- Email verification notice

**File:** `src/ui/auth/profile.py`
- Display user info
- Edit profile form
- Change password form
- Subscription info

### Step 4: Update Main App

**File:** `app.py`
- Check authentication on page load
- Show login/register if not authenticated
- Show main app if authenticated
- Add user menu to navigation

### Step 5: Update Data Loading

**File:** `src/pv_storage.py` (NEW)
- Store data with user_id
- Query data filtered by user_id
- Multi-tenant data isolation

**File:** `src/app_helpers.py`
- Update `load_all_files()` to store in database with user_id
- Query from database instead of session state

---

## Database Schema Details

### Tables Needed

1. **auth.users** (Supabase built-in)
   - id (UUID)
   - email
   - encrypted_password
   - email_confirmed_at
   - created_at
   - updated_at

2. **user_profiles** (Custom)
   - id (UUID, FK to auth.users)
   - email
   - full_name
   - organization
   - role (admin, scientist, viewer)
   - subscription_tier (free, pro, enterprise)
   - created_at
   - updated_at

3. **pv_cases** (Custom - for PV data)
   - id (UUID)
   - user_id (UUID, FK to auth.users)
   - case_id
   - drug_name
   - reaction
   - age
   - sex
   - ... (all PV fields)
   - source
   - created_at
   - updated_at

4. **user_sessions** (Optional - for tracking)
   - id (UUID)
   - user_id (UUID)
   - session_token
   - expires_at
   - created_at

---

## Security Considerations

### Row-Level Security (RLS)
- All tables with user data must have RLS enabled
- Policies ensure users can only access their own data
- Admin users can have special policies

### Password Security
- Supabase handles password hashing (bcrypt)
- Minimum password requirements (8+ chars, complexity)
- Rate limiting on login attempts

### Session Management
- JWT tokens with expiration
- Refresh tokens for long sessions
- Secure cookie storage

### Email Verification
- Require email verification before full access
- Send verification emails automatically
- Handle verification tokens securely

---

## User Flow

### Registration Flow
1. User clicks "Register"
2. Fills form (email, password, name, organization)
3. Submits → Supabase creates user
4. Email verification sent
5. User clicks link in email
6. Account activated → Redirect to login

### Login Flow
1. User clicks "Login"
2. Enters email/password
3. Supabase validates credentials
4. JWT token created
5. Token stored in session
6. User redirected to main app

### Data Access Flow
1. User loads data
2. System checks authentication
3. If authenticated, query database with user_id filter
4. RLS policies ensure only user's data returned
5. Data displayed in UI

---

## Testing Plan

### Unit Tests
- Authentication functions
- User management functions
- RLS policies

### Integration Tests
- Registration flow
- Login flow
- Data isolation (multi-tenant)
- Role-based access

### Security Tests
- RLS policy enforcement
- Password reset security
- Session management
- XSS/CSRF protection

---

## Estimated Timeline

- **Week 1:** Core authentication + database schema
- **Week 2:** UI components + data isolation
- **Week 3:** Role-based access + testing
- **Total:** 2-3 weeks

---

## Next Steps

1. ✅ Create authentication module
2. ✅ Create database schema
3. ✅ Create UI components
4. ✅ Integrate with main app
5. ✅ Update data loading to use database
6. ✅ Add role-based access control
7. ✅ Testing and security audit

---

## Benefits

1. **Multi-Tenant Support**
   - Each user has isolated data
   - Perfect for SaaS model
   - Built-in with RLS

2. **Security**
   - Industry-standard authentication
   - Password hashing
   - Session management
   - Email verification

3. **Scalability**
   - Handles thousands of users
   - Automatic scaling
   - No infrastructure management

4. **User Experience**
   - Simple registration/login
   - Password reset
   - Profile management
   - Role-based features

5. **Business Value**
   - Enables paid subscriptions
   - User tracking and analytics
   - Multi-tenant SaaS ready
   - Enterprise features foundation

