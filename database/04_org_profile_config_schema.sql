-- Organization Profile Configuration Table
-- Stores per-tenant, per-product regulatory configuration for PSUR/DSUR reports
-- EXECUTION ORDER: 04 (Run AFTER 00_schema.sql - depends on user_profiles table)

CREATE TABLE IF NOT EXISTS org_profile_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization TEXT UNIQUE NOT NULL,  -- Links to user_profiles.organization
    products JSONB DEFAULT '[]'::jsonb,  -- Array of product configurations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_org_profile_config_organization ON org_profile_config(organization);

-- Enable Row Level Security
ALTER TABLE org_profile_config ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view their own organization's config
CREATE POLICY "Users can view own org config"
    ON org_profile_config FOR SELECT
    USING (
        organization = (
            SELECT organization FROM user_profiles 
            WHERE id = auth.uid()
        )
    );

-- Policy: Users can update their own organization's config
CREATE POLICY "Users can update own org config"
    ON org_profile_config FOR UPDATE
    USING (
        organization = (
            SELECT organization FROM user_profiles 
            WHERE id = auth.uid()
        )
    );

-- Policy: Users can insert their own organization's config
CREATE POLICY "Users can insert own org config"
    ON org_profile_config FOR INSERT
    WITH CHECK (
        organization = (
            SELECT organization FROM user_profiles 
            WHERE id = auth.uid()
        )
    );

-- Example products JSONB structure:
-- {
--   "products": [
--     {
--       "product_name": "DrugA",
--       "authorization_status": {
--         "US": "approved (2020-01-15)",
--         "EU": "approved (2020-03-20)",
--         "UK": "pending"
--       },
--       "safety_actions": [
--         {
--           "date": "2025-02-15",
--           "description": "Dear HCP letter issued regarding pancreatitis risk"
--         }
--       ],
--       "rmp_changes": [
--         {
--           "date": "2025-03-20",
--           "description": "Added pancreatitis monitoring"
--         }
--       ],
--       "exposure_estimates": {
--         "2025Q1": "2.1M patient-years",
--         "2025Q2": "2.3M patient-years"
--       },
--       "clinical_program": [
--         {
--           "study_id": "NCT12345678",
--           "phase": "Phase 3",
--           "status": "ongoing",
--           "countries": ["US", "EU"]
--         }
--       ],
--       "pv_system_overview": "Our pharmacovigilance system..."
--     }
--   ]
-- }

