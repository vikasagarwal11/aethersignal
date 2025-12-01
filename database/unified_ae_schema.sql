-- ============================================================
-- PHASE 3A: Unified AE Database Schema
-- Global unified schema for all adverse event sources
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- For pgvector embeddings

-- ============================================================
-- 3A.1: Unified AE Events Table
-- ============================================================

CREATE TABLE IF NOT EXISTS ae_events (
    -- Primary key
    ae_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source identification
    source TEXT NOT NULL CHECK (source IN (
        'faers', 'openfda', 'social', 'reddit', 'x', 'twitter',
        'pubmed', 'literature', 'clinicaltrials', 'dailymed',
        'ema', 'yellowcard', 'health_canada', 'tga', 'google',
        'humanapi', 'metriport', 'drugbank', 'vigibase', 'epic_fhir',
        'cerner_fhir', 'ohdsi', 'other'
    )),
    source_id TEXT,  -- Source-specific primary key
    source_url TEXT,  -- Link to original source
    
    -- Drug information
    drug_raw TEXT,
    drug_normalized TEXT NOT NULL,
    drug_group TEXT,  -- GLP-1, SSRIs, Statins, etc.
    drug_synonyms TEXT[],  -- Array of synonyms
    
    -- Reaction information
    reaction_raw TEXT,
    reaction_normalized TEXT NOT NULL,  -- PT from Phase 2B
    reaction_category TEXT,  -- Gastrointestinal, Neurological, etc.
    reaction_cluster_id INTEGER,  -- From Phase 2A clustering
    reaction_severity_score REAL CHECK (reaction_severity_score >= 0 AND reaction_severity_score <= 1),
    reaction_novelty_score REAL CHECK (reaction_novelty_score >= 0 AND reaction_novelty_score <= 1),
    
    -- Patient demographics (nullable)
    age INTEGER,
    age_group TEXT,  -- pediatric, adult, elderly
    sex TEXT CHECK (sex IN ('M', 'F', 'U', NULL)),
    country TEXT,
    
    -- Event details (nullable)
    dose TEXT,
    dose_amount REAL,
    dose_unit TEXT,
    duration TEXT,
    onset_time TEXT,
    route TEXT,
    
    -- Seriousness and outcome
    seriousness_flags JSONB,  -- {death: false, hospitalization: true, ...}
    outcome TEXT,
    serious BOOLEAN DEFAULT FALSE,
    
    -- Dates
    event_date TIMESTAMPTZ,
    report_date TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Text content
    full_text TEXT,
    text_snippet TEXT,  -- First 500 chars
    
    -- Embeddings (vector store)
    embedding_vector vector(1536),  -- OpenAI text-embedding-3-small
    
    -- Scoring (from Phase 2D)
    quantum_score REAL CHECK (quantum_score >= 0 AND quantum_score <= 1),
    burst_score REAL CHECK (burst_score >= 0 AND burst_score <= 1),
    consensus_score REAL CHECK (consensus_score >= 0 AND consensus_score <= 1),
    
    -- Source support scores
    literature_support REAL CHECK (literature_support >= 0 AND literature_support <= 1),
    clinical_support REAL CHECK (clinical_support >= 0 AND clinical_support <= 1),
    label_support REAL CHECK (label_support >= 0 AND label_support <= 1),
    social_support REAL CHECK (social_support >= 0 AND social_support <= 1),
    
    -- Metadata (flexible JSONB)
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 3A.2: Unified Drugs Table
-- ============================================================

CREATE TABLE IF NOT EXISTS drugs (
    drug_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_normalized TEXT NOT NULL UNIQUE,
    generic_name TEXT,
    brand_names TEXT[],  -- Array of brand names
    synonyms TEXT[],  -- Array of synonyms
    drug_group TEXT,  -- GLP-1, SSRIs, Statins, etc.
    mechanism_of_action TEXT,
    atc_code TEXT,  -- Anatomical Therapeutic Chemical code
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 3A.3: Unified Reactions Table (from Phase 2B)
-- ============================================================

CREATE TABLE IF NOT EXISTS reactions (
    reaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reaction_normalized TEXT NOT NULL UNIQUE,  -- PT
    canonical_form TEXT,  -- Standardized form
    cluster_id INTEGER,  -- From Phase 2A clustering
    synonyms TEXT[],  -- Array of synonyms
    severity_keywords TEXT[],  -- Keywords for severity detection
    emoji_keywords TEXT[],  -- Emoji mappings
    category TEXT,  -- SOC-like category
    soc TEXT,  -- System Organ Class (if MedDRA available)
    hlt TEXT,  -- High Level Term (if MedDRA available)
    pt TEXT,  -- Preferred Term (same as reaction_normalized)
    llt TEXT[],  -- Lower Level Terms (if MedDRA available)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Indexes for Performance (3A.6)
-- ============================================================

-- AE Events indexes
CREATE INDEX IF NOT EXISTS idx_ae_drug_normalized ON ae_events(drug_normalized);
CREATE INDEX IF NOT EXISTS idx_ae_reaction_normalized ON ae_events(reaction_normalized);
CREATE INDEX IF NOT EXISTS idx_ae_source ON ae_events(source);
CREATE INDEX IF NOT EXISTS idx_ae_event_date ON ae_events(event_date);
CREATE INDEX IF NOT EXISTS idx_ae_drug_reaction ON ae_events(drug_normalized, reaction_normalized);
CREATE INDEX IF NOT EXISTS idx_ae_quantum_score ON ae_events(quantum_score DESC);
CREATE INDEX IF NOT EXISTS idx_ae_created_at ON ae_events(created_at DESC);

-- Vector index for similarity search
CREATE INDEX IF NOT EXISTS idx_ae_embedding_vector ON ae_events 
    USING ivfflat (embedding_vector vector_cosine_ops)
    WITH (lists = 200);

-- GIN indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_ae_seriousness_flags ON ae_events USING GIN (seriousness_flags);
CREATE INDEX IF NOT EXISTS idx_ae_metadata ON ae_events USING GIN (metadata);

-- Drugs indexes
CREATE INDEX IF NOT EXISTS idx_drugs_normalized ON drugs(drug_normalized);
CREATE INDEX IF NOT EXISTS idx_drugs_group ON drugs(drug_group);
CREATE INDEX IF NOT EXISTS idx_drugs_atc ON drugs(atc_code);

-- Reactions indexes
CREATE INDEX IF NOT EXISTS idx_reactions_normalized ON reactions(reaction_normalized);
CREATE INDEX IF NOT EXISTS idx_reactions_category ON reactions(category);
CREATE INDEX IF NOT EXISTS idx_reactions_cluster ON reactions(cluster_id);

-- ============================================================
-- Views for Common Queries
-- ============================================================

-- View: Drug-Reaction Summary
CREATE OR REPLACE VIEW drug_reaction_summary AS
SELECT
    drug_normalized,
    reaction_normalized,
    source,
    COUNT(*) as case_count,
    AVG(quantum_score) as avg_quantum_score,
    AVG(reaction_severity_score) as avg_severity,
    AVG(consensus_score) as avg_consensus,
    MIN(event_date) as first_event,
    MAX(event_date) as last_event
FROM ae_events
GROUP BY drug_normalized, reaction_normalized, source;

-- View: Source Statistics
CREATE OR REPLACE VIEW source_statistics AS
SELECT
    source,
    COUNT(*) as total_events,
    COUNT(DISTINCT drug_normalized) as unique_drugs,
    COUNT(DISTINCT reaction_normalized) as unique_reactions,
    AVG(quantum_score) as avg_quantum_score,
    MIN(event_date) as first_event,
    MAX(event_date) as last_event
FROM ae_events
GROUP BY source;

-- ============================================================
-- Functions for Common Operations
-- ============================================================

-- Function: Find similar reactions using embeddings
CREATE OR REPLACE FUNCTION find_similar_reactions(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    drug_filter text DEFAULT NULL
)
RETURNS TABLE (
    ae_id UUID,
    drug_normalized TEXT,
    reaction_normalized TEXT,
    source TEXT,
    similarity REAL
)
LANGUAGE sql
AS $$
    SELECT
        ae_id,
        drug_normalized,
        reaction_normalized,
        source,
        1 - (embedding_vector <=> query_embedding) as similarity
    FROM ae_events
    WHERE embedding_vector IS NOT NULL
        AND (drug_filter IS NULL OR drug_normalized = drug_filter)
    ORDER BY embedding_vector <=> query_embedding
    LIMIT match_count;
$$;

-- Function: Get cross-source consensus
CREATE OR REPLACE FUNCTION get_consensus(
    p_drug TEXT,
    p_reaction TEXT
)
RETURNS TABLE (
    source TEXT,
    case_count BIGINT,
    avg_quantum_score REAL,
    avg_severity REAL
)
LANGUAGE sql
AS $$
    SELECT
        source,
        COUNT(*) as case_count,
        AVG(quantum_score) as avg_quantum_score,
        AVG(reaction_severity_score) as avg_severity
    FROM ae_events
    WHERE drug_normalized = p_drug
        AND reaction_normalized = p_reaction
    GROUP BY source
    ORDER BY case_count DESC;
$$;

