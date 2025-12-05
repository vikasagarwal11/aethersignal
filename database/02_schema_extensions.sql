-- AetherSignal Schema Extensions
-- Additional tables for saved queries, query history, and activity logs
-- EXECUTION ORDER: 02 (Run AFTER 00_schema.sql)

-- ============================================================================
-- 6. SAVED QUERIES TABLE (Multi-Tenant)
-- ============================================================================
-- Stores user-saved queries for reuse

CREATE TABLE IF NOT EXISTS saved_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization TEXT NOT NULL,
    name TEXT NOT NULL,
    query_text TEXT,
    filters JSONB, -- Store filter criteria as JSON
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    UNIQUE(user_id, name) -- User can't have two queries with same name
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_saved_queries_user_id ON saved_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_queries_organization ON saved_queries(organization);
CREATE INDEX IF NOT EXISTS idx_saved_queries_name ON saved_queries(name);

-- ============================================================================
-- 7. QUERY HISTORY TABLE (Multi-Tenant)
-- ============================================================================
-- Stores history of executed queries for audit and reuse

CREATE TABLE IF NOT EXISTS query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization TEXT NOT NULL,
    query_text TEXT,
    filters JSONB,
    source TEXT, -- 'nl' for natural language, 'form' for form-based
    results_count INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_query_history_user_id ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_organization ON query_history(organization);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_history_source ON query_history(source);

-- ============================================================================
-- 8. ACTIVITY LOG TABLE (Multi-Tenant)
-- ============================================================================
-- Comprehensive activity logging for audit trails and analytics

CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    organization TEXT,
    event_type TEXT NOT NULL, -- 'query_executed', 'pdf_generated', 'data_uploaded', 'settings_changed', etc.
    event_details JSONB, -- Store event-specific details as JSON
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for activity logs
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_organization ON activity_logs(organization);
CREATE INDEX IF NOT EXISTS idx_activity_logs_event_type ON activity_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at DESC);

-- ============================================================================
-- RLS POLICIES FOR NEW TABLES
-- ============================================================================

-- Enable RLS on saved_queries
ALTER TABLE saved_queries ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own saved queries and company queries
CREATE POLICY "Users can view own company saved queries"
    ON saved_queries FOR SELECT
    USING (
        auth.uid() = user_id OR
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.organization = saved_queries.organization
        )
    );

-- Policy: Users can insert their own saved queries
CREATE POLICY "Users can insert own saved queries"
    ON saved_queries FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own saved queries
CREATE POLICY "Users can update own saved queries"
    ON saved_queries FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can delete their own saved queries
CREATE POLICY "Users can delete own saved queries"
    ON saved_queries FOR DELETE
    USING (auth.uid() = user_id);

-- Enable RLS on query_history
ALTER TABLE query_history ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own company's query history
CREATE POLICY "Users can view own company query history"
    ON query_history FOR SELECT
    USING (
        auth.uid() = user_id OR
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.organization = query_history.organization
        )
    );

-- Policy: Users can insert their own query history
CREATE POLICY "Users can insert own query history"
    ON query_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Enable RLS on activity_logs
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own company's activity logs
CREATE POLICY "Users can view own company activity logs"
    ON activity_logs FOR SELECT
    USING (
        auth.uid() = user_id OR
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.organization = activity_logs.organization
        )
    );

-- Policy: System can insert activity logs (via service role)
-- Note: This is handled by service role key, which bypasses RLS

-- ============================================================================
-- TRIGGERS FOR NEW TABLES
-- ============================================================================

-- Trigger to update updated_at for saved_queries
CREATE TRIGGER update_saved_queries_updated_at
    BEFORE UPDATE ON saved_queries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Generic function to set organization from user profile (works for any table)
CREATE OR REPLACE FUNCTION set_organization_from_user()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.organization IS NULL AND NEW.user_id IS NOT NULL THEN
        SELECT organization INTO NEW.organization
        FROM user_profiles
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to set organization automatically for saved_queries
CREATE TRIGGER set_saved_query_organization_trigger
    BEFORE INSERT ON saved_queries
    FOR EACH ROW
    EXECUTE FUNCTION set_organization_from_user();

-- Trigger to set organization automatically for query_history
CREATE TRIGGER set_query_history_organization_trigger
    BEFORE INSERT ON query_history
    FOR EACH ROW
    EXECUTE FUNCTION set_organization_from_user();

-- Trigger to set organization automatically for activity_logs
CREATE TRIGGER set_activity_log_organization_trigger
    BEFORE INSERT ON activity_logs
    FOR EACH ROW
    EXECUTE FUNCTION set_organization_from_user();

-- Function to automatically set organization from user profile (reusable)
-- (This function already exists, but we'll reference it)

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. Run this AFTER running the main schema.sql
-- 2. All tables follow the same multi-tenant isolation pattern
-- 3. Saved queries and query history are company-shared (like PV cases)
-- 4. Activity logs track all user actions for audit purposes
-- 5. RLS ensures complete data isolation between companies

