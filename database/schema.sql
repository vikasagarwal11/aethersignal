-- AetherSignal Multi-Tenant Database Schema
-- Run this SQL in your Supabase SQL Editor to set up the database

-- ============================================================================
-- 1. USER PROFILES TABLE
-- ============================================================================
-- Stores additional user information beyond Supabase Auth

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    organization TEXT NOT NULL,
    role TEXT DEFAULT 'scientist' CHECK (role IN ('admin', 'scientist', 'viewer')),
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_organization ON user_profiles(organization);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

-- ============================================================================
-- 2. PV CASES TABLE (Multi-Tenant)
-- ============================================================================
-- Stores pharmacovigilance case data with company/user isolation

CREATE TABLE IF NOT EXISTS pv_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization TEXT NOT NULL, -- Company/organization identifier
    case_id TEXT,
    primaryid TEXT,
    isr TEXT,
    drug_name TEXT,
    drug_count INTEGER,
    reaction TEXT,
    reaction_count INTEGER,
    age NUMERIC,
    age_yrs NUMERIC,
    sex TEXT,
    gender TEXT,
    country TEXT,
    serious BOOLEAN,
    seriousness TEXT,
    onset_date DATE,
    event_date DATE,
    report_date DATE,
    receive_date DATE,
    outcome TEXT,
    source TEXT DEFAULT 'FAERS', -- FAERS, E2B, Argus, etc.
    raw_data JSONB, -- Store original data as JSON for flexibility
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_pv_cases_user_id ON pv_cases(user_id);
CREATE INDEX IF NOT EXISTS idx_pv_cases_organization ON pv_cases(organization);
CREATE INDEX IF NOT EXISTS idx_pv_cases_drug_name ON pv_cases(drug_name);
CREATE INDEX IF NOT EXISTS idx_pv_cases_reaction ON pv_cases(reaction);
CREATE INDEX IF NOT EXISTS idx_pv_cases_case_id ON pv_cases(case_id);
CREATE INDEX IF NOT EXISTS idx_pv_cases_source ON pv_cases(source);
CREATE INDEX IF NOT EXISTS idx_pv_cases_created_at ON pv_cases(created_at);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_pv_cases_user_drug ON pv_cases(user_id, drug_name);
CREATE INDEX IF NOT EXISTS idx_pv_cases_user_reaction ON pv_cases(user_id, reaction);

-- ============================================================================
-- 3. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id);

-- Policy: Users can insert their own profile (on registration)
CREATE POLICY "Users can insert own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Enable RLS on pv_cases
ALTER TABLE pv_cases ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view their own company's data
CREATE POLICY "Users can view own company data"
    ON pv_cases FOR SELECT
    USING (
        auth.uid() = user_id OR
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.organization = pv_cases.organization
        )
    );

-- Policy: Users can insert their own data
CREATE POLICY "Users can insert own data"
    ON pv_cases FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own data
CREATE POLICY "Users can update own data"
    ON pv_cases FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can delete their own data
CREATE POLICY "Users can delete own data"
    ON pv_cases FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 4. FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for user_profiles
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for pv_cases
CREATE TRIGGER update_pv_cases_updated_at
    BEFORE UPDATE ON pv_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically set organization from user profile on insert
CREATE OR REPLACE FUNCTION set_pv_case_organization()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.organization IS NULL THEN
        SELECT organization INTO NEW.organization
        FROM user_profiles
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to set organization automatically
CREATE TRIGGER set_pv_case_organization_trigger
    BEFORE INSERT ON pv_cases
    FOR EACH ROW
    EXECUTE FUNCTION set_pv_case_organization();

-- ============================================================================
-- 5. HELPER VIEWS (Optional)
-- ============================================================================

-- View for user's data summary
CREATE OR REPLACE VIEW user_data_summary AS
SELECT 
    user_id,
    organization,
    COUNT(*) as total_cases,
    COUNT(DISTINCT drug_name) as unique_drugs,
    COUNT(DISTINCT reaction) as unique_reactions,
    MIN(created_at) as first_upload,
    MAX(created_at) as last_upload
FROM pv_cases
GROUP BY user_id, organization;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. This schema assumes Supabase Auth is already set up
-- 2. Run this in Supabase SQL Editor: https://app.supabase.com/project/YOUR_PROJECT/sql
-- 3. Make sure RLS is enabled in Supabase dashboard
-- 4. Test policies with different user accounts
-- 5. Organization is used as company identifier for multi-tenant isolation

