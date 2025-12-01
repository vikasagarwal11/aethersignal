-- Reaction Vectors Table for Semantic Similarity Search
-- Uses pgvector extension for efficient similarity search

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create reaction_vectors table
CREATE TABLE IF NOT EXISTS reaction_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    drug TEXT,
    reaction_raw TEXT NOT NULL,
    reaction_norm TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast similarity search
CREATE INDEX IF NOT EXISTS reaction_vectors_embedding_idx 
ON reaction_vectors 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 200);

-- Create index for drug filtering
CREATE INDEX IF NOT EXISTS reaction_vectors_drug_idx ON reaction_vectors(drug);

-- Create index for source filtering
CREATE INDEX IF NOT EXISTS reaction_vectors_source_idx ON reaction_vectors(source);

-- Create RPC function for similarity search
CREATE OR REPLACE FUNCTION find_similar_reactions(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    drug_filter text DEFAULT NULL
)
RETURNS TABLE (
    reaction_raw text,
    reaction_norm text,
    drug text,
    similarity float
)
LANGUAGE sql
AS $$
    SELECT
        reaction_raw,
        reaction_norm,
        drug,
        1 - (embedding <=> query_embedding) as similarity
    FROM reaction_vectors
    WHERE (drug_filter IS NULL OR drug = drug_filter)
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Create reaction_dictionary table (for SuperAdmin management)
CREATE TABLE IF NOT EXISTS reaction_dictionary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pt TEXT NOT NULL UNIQUE,
    synonyms TEXT[],
    patterns TEXT[],
    emoji TEXT[],
    cluster_ids INTEGER[],
    category TEXT,
    llm_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for PT lookup
CREATE INDEX IF NOT EXISTS reaction_dictionary_pt_idx ON reaction_dictionary(pt);

-- Create index for category lookup
CREATE INDEX IF NOT EXISTS reaction_dictionary_category_idx ON reaction_dictionary(category);

