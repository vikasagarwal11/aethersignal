-- ============================================
-- Public AE Data Table Schema
-- ============================================
-- This table stores publicly accessible AE data
-- No user_id or organization - generic public data
-- Used for public data platform pages

CREATE TABLE IF NOT EXISTS public_ae_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drug_name TEXT NOT NULL,
    reaction TEXT,
    source TEXT NOT NULL,  -- 'reddit', 'openfda', 'pubmed', 'medsafety_alerts', 'clinicaltrials', 'dailymed'
    text TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    confidence FLOAT DEFAULT 0.5,
    severity FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_public_ae_drug ON public_ae_data(drug_name);
CREATE INDEX IF NOT EXISTS idx_public_ae_reaction ON public_ae_data(reaction);
CREATE INDEX IF NOT EXISTS idx_public_ae_source ON public_ae_data(source);
CREATE INDEX IF NOT EXISTS idx_public_ae_timestamp ON public_ae_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_public_ae_created ON public_ae_data(created_at DESC);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_public_ae_drug_source ON public_ae_data(drug_name, source);
CREATE INDEX IF NOT EXISTS idx_public_ae_drug_timestamp ON public_ae_data(drug_name, timestamp DESC);

-- No RLS needed - this is public data
-- Anyone can read, only system/service role can write

-- Grant read access to authenticated and anonymous users
GRANT SELECT ON public_ae_data TO authenticated;
GRANT SELECT ON public_ae_data TO anon;

-- Only service role can insert/update/delete
-- (This is handled by your application using service key)

COMMENT ON TABLE public_ae_data IS 'Publicly accessible adverse event data from all sources. No user_id or organization - generic public data for public data platform.';
COMMENT ON COLUMN public_ae_data.drug_name IS 'Drug name (normalized)';
COMMENT ON COLUMN public_ae_data.reaction IS 'Adverse reaction (MedDRA PT if available)';
COMMENT ON COLUMN public_ae_data.source IS 'Data source: reddit, openfda, pubmed, medsafety_alerts, clinicaltrials, dailymed';
COMMENT ON COLUMN public_ae_data.confidence IS 'Confidence score (0.0-1.0)';
COMMENT ON COLUMN public_ae_data.severity IS 'Severity score (0.0-1.0)';
COMMENT ON COLUMN public_ae_data.metadata IS 'Source-specific metadata (JSON)';

