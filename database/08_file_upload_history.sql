-- ============================================================================
-- File Upload History Table
-- EXECUTION ORDER: 08 (Run after base schemas)
-- Purpose: Track individual file uploads with metadata and statistics
-- ============================================================================

-- ============================================================================
-- FILE UPLOAD HISTORY TABLE
-- ============================================================================
-- Tracks each file upload separately with metadata and high-level statistics

CREATE TABLE IF NOT EXISTS file_upload_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization TEXT NOT NULL,
    
    -- File metadata
    filename TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_hash_md5 TEXT, -- MD5 hash for duplicate detection
    file_type TEXT, -- 'FAERS', 'E2B', 'CSV', 'Excel', etc.
    
    -- Upload metadata
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    upload_status TEXT DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    
    -- High-level statistics (calculated in background)
    total_cases INTEGER,
    total_events INTEGER, -- Number of unique reactions/events
    total_drugs INTEGER, -- Number of unique drugs
    total_serious_cases INTEGER,
    total_fatal_cases INTEGER,
    
    -- Date range of cases
    earliest_date DATE,
    latest_date DATE,
    
    -- Source-specific metadata
    source TEXT DEFAULT 'FAERS',
    
    -- Processing metadata
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT, -- Error message if failed
    
    -- Stats calculation status
    stats_calculated_at TIMESTAMP WITH TIME ZONE,
    stats_status TEXT DEFAULT 'pending', -- 'pending', 'calculating', 'completed', 'failed'
    
    -- JSONB for flexible metadata
    metadata JSONB DEFAULT '{}'::jsonb, -- Additional file-specific metadata
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    -- Unique constraint: Same file (filename + size) can be uploaded multiple times
    -- but we track each upload separately by including uploaded_at in uniqueness check
    -- Actually, we don't want uniqueness - same file can be uploaded multiple times
    -- We'll detect duplicates via query, not constraint
);

-- Indexes for fast duplicate detection and queries
CREATE INDEX IF NOT EXISTS idx_file_upload_user_id ON file_upload_history(user_id);
CREATE INDEX IF NOT EXISTS idx_file_upload_organization ON file_upload_history(organization);
CREATE INDEX IF NOT EXISTS idx_file_upload_filename_size ON file_upload_history(user_id, organization, filename, file_size_bytes);
CREATE INDEX IF NOT EXISTS idx_file_upload_uploaded_at ON file_upload_history(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_file_upload_status ON file_upload_history(upload_status);
CREATE INDEX IF NOT EXISTS idx_file_upload_source ON file_upload_history(source);

-- Composite index for listing user's uploads
CREATE INDEX IF NOT EXISTS idx_file_upload_user_org_date 
    ON file_upload_history(user_id, organization, uploaded_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on file_upload_history
ALTER TABLE file_upload_history ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own company's file upload history
CREATE POLICY "Users can view own company file upload history"
    ON file_upload_history FOR SELECT
    USING (
        auth.uid() = user_id OR
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.organization = file_upload_history.organization
        )
    );

-- Policy: Users can insert their own file upload history
CREATE POLICY "Users can insert own file upload history"
    ON file_upload_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own file upload history
CREATE POLICY "Users can update own file upload history"
    ON file_upload_history FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can delete their own file upload history
CREATE POLICY "Users can delete own file upload history"
    ON file_upload_history FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_file_upload_history_updated_at
    BEFORE UPDATE ON file_upload_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to set organization automatically from user profile
CREATE TRIGGER set_file_upload_organization_trigger
    BEFORE INSERT ON file_upload_history
    FOR EACH ROW
    EXECUTE FUNCTION set_organization_from_user();

-- ============================================================================
-- HELPER FUNCTION: Check for duplicate files
-- ============================================================================

CREATE OR REPLACE FUNCTION check_duplicate_file(
    p_user_id UUID,
    p_organization TEXT,
    p_filename TEXT,
    p_file_size_bytes BIGINT
)
RETURNS TABLE (
    id UUID,
    filename TEXT,
    file_size_bytes BIGINT,
    uploaded_at TIMESTAMP WITH TIME ZONE,
    total_cases INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fuh.id,
        fuh.filename,
        fuh.file_size_bytes,
        fuh.uploaded_at,
        fuh.total_cases
    FROM file_upload_history fuh
    WHERE fuh.user_id = p_user_id
        AND fuh.organization = p_organization
        AND fuh.filename = p_filename
        AND fuh.file_size_bytes = p_file_size_bytes
    ORDER BY fuh.uploaded_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_duplicate_file IS 
    'Check if a file with the same filename and size was previously uploaded by the user. Returns the most recent upload if found.';

-- ============================================================================
-- NOTES:
-- ============================================================================
-- This table tracks individual file uploads separately, enabling:
-- 1. Duplicate file detection (by filename + size)
-- 2. File-level statistics tracking
-- 3. Upload history per user/organization
-- 4. Processing status tracking
--
-- The table allows the same file to be uploaded multiple times (no unique constraint),
-- but provides a helper function to detect duplicates via query.
--
-- Statistics are calculated in the background and updated asynchronously.
-- ============================================================================

