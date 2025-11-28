-- Tenant-aware upgrade script for AetherSignal
-- Adds canonical tenants, memberships, and tenant_id columns to core tables.

-- 1) Canonical tenants
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2) User-to-tenant membership with roles
CREATE TABLE IF NOT EXISTS user_tenants (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin','member','viewer')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, tenant_id)
);
CREATE INDEX IF NOT EXISTS idx_user_tenants_tenant ON user_tenants(tenant_id);

-- 3) Add tenant_id to user_profiles if missing
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_tenant ON user_profiles(tenant_id);

-- 4) Add tenant_id to pv_cases if missing
ALTER TABLE pv_cases ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pv_cases_tenant ON pv_cases(tenant_id);

-- 5) Helper function: set tenant_id from membership/profile
CREATE OR REPLACE FUNCTION set_tenant_from_profile()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tenant_id IS NULL THEN
        SELECT tenant_id INTO NEW.tenant_id
        FROM user_profiles
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6) Apply trigger to pv_cases inserts
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'set_pv_case_tenant_trigger'
    ) THEN
        CREATE TRIGGER set_pv_case_tenant_trigger
            BEFORE INSERT ON pv_cases
            FOR EACH ROW
            EXECUTE FUNCTION set_tenant_from_profile();
    END IF;
END$$;

-- 7) Tenant-scoped RLS policies for pv_cases
ALTER TABLE pv_cases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own company data" ON pv_cases;
CREATE POLICY "Tenant members can view pv_cases"
    ON pv_cases FOR SELECT
    USING (
        tenant_id IS NOT NULL AND
        tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Users can insert own data" ON pv_cases;
CREATE POLICY "Tenant members can insert pv_cases"
    ON pv_cases FOR INSERT
    WITH CHECK (
        tenant_id IS NOT NULL AND
        tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Users can update own data" ON pv_cases;
CREATE POLICY "Tenant members can update pv_cases"
    ON pv_cases FOR UPDATE
    USING (
        tenant_id IS NOT NULL AND
        tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Users can delete own data" ON pv_cases;
CREATE POLICY "Tenant members can delete pv_cases"
    ON pv_cases FOR DELETE
    USING (
        tenant_id IS NOT NULL AND
        tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid())
    );

-- 8) Tenant RLS for user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON user_profiles;

CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- 9) Saved queries, history, activity logs: add tenant_id and tenant RLS
ALTER TABLE saved_queries ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_saved_queries_tenant ON saved_queries(tenant_id);

ALTER TABLE query_history ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_query_history_tenant ON query_history(tenant_id);

ALTER TABLE activity_logs ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_tenant ON activity_logs(tenant_id);

-- Helper trigger for tenant_id on generic tables with user_id
CREATE OR REPLACE FUNCTION set_tenant_from_user()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tenant_id IS NULL AND NEW.user_id IS NOT NULL THEN
        SELECT tenant_id INTO NEW.tenant_id
        FROM user_profiles
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='set_saved_queries_tenant_trigger') THEN
        CREATE TRIGGER set_saved_queries_tenant_trigger
            BEFORE INSERT ON saved_queries
            FOR EACH ROW
            EXECUTE FUNCTION set_tenant_from_user();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='set_query_history_tenant_trigger') THEN
        CREATE TRIGGER set_query_history_tenant_trigger
            BEFORE INSERT ON query_history
            FOR EACH ROW
            EXECUTE FUNCTION set_tenant_from_user();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='set_activity_logs_tenant_trigger') THEN
        CREATE TRIGGER set_activity_logs_tenant_trigger
            BEFORE INSERT ON activity_logs
            FOR EACH ROW
            EXECUTE FUNCTION set_tenant_from_user();
    END IF;
END$$;

ALTER TABLE saved_queries ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own company saved queries" ON saved_queries;
DROP POLICY IF EXISTS "Users can insert own saved queries" ON saved_queries;
DROP POLICY IF EXISTS "Users can update own saved queries" ON saved_queries;
DROP POLICY IF EXISTS "Users can delete own saved queries" ON saved_queries;

CREATE POLICY "Tenant members can view saved_queries"
    ON saved_queries FOR SELECT
    USING (tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid()));

CREATE POLICY "Tenant members can insert saved_queries"
    ON saved_queries FOR INSERT
    WITH CHECK (tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid()));

CREATE POLICY "Tenant members can update saved_queries"
    ON saved_queries FOR UPDATE
    USING (tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid()));

CREATE POLICY "Tenant members can delete saved_queries"
    ON saved_queries FOR DELETE
    USING (tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid()));

ALTER TABLE query_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own company query history" ON query_history;
DROP POLICY IF EXISTS "Users can insert own query history" ON query_history;

CREATE POLICY "Tenant members can view query_history"
    ON query_history FOR SELECT
    USING (tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid()));

CREATE POLICY "Tenant members can insert query_history"
    ON query_history FOR INSERT
    WITH CHECK (tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid()));

ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own company activity logs" ON activity_logs;
-- Service role inserts are allowed (bypass RLS); user inserts constrained by tenant
CREATE POLICY "Tenant members can view activity_logs"
    ON activity_logs FOR SELECT
    USING (tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid()));

-- 10) (Optional) helper view for tenant membership
CREATE OR REPLACE VIEW tenant_memberships AS
SELECT 
    ut.user_id,
    ut.tenant_id,
    ut.role,
    t.name as tenant_name
FROM user_tenants ut
JOIN tenants t ON ut.tenant_id = t.id;
