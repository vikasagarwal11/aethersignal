-- Supabase Table Setup Script
-- Run this in Supabase Dashboard → SQL Editor

-- Main Social AE table (simplified schema)
CREATE TABLE IF NOT EXISTS social_ae (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  drug_name TEXT,
  reaction TEXT,
  meddra_pt TEXT,
  ae_prob NUMERIC,
  created TIMESTAMP NOT NULL,
  text TEXT NOT NULL,
  subreddit TEXT,
  score INTEGER DEFAULT 0,
  inserted_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_social_created ON social_ae (created);
CREATE INDEX IF NOT EXISTS idx_social_drug ON social_ae (drug_name);
CREATE INDEX IF NOT EXISTS idx_social_reaction ON social_ae (reaction);

-- Pull history table
CREATE TABLE IF NOT EXISTS pull_history (
  id BIGSERIAL PRIMARY KEY,
  pull_date TIMESTAMP DEFAULT NOW(),
  drug_terms TEXT,
  platforms TEXT,
  posts_fetched INTEGER,
  posts_new INTEGER,
  posts_duplicate INTEGER,
  status TEXT,
  error_message TEXT
);

-- Enable Row Level Security (optional, for production)
ALTER TABLE social_ae ENABLE ROW LEVEL SECURITY;

-- Policy: Allow public read access (adjust for your needs)
CREATE POLICY "Allow public read access" ON social_ae
  FOR SELECT USING (true);

-- Policy: Allow service role full access
CREATE POLICY "Allow service role full access" ON social_ae
  FOR ALL USING (auth.role() = 'service_role');

