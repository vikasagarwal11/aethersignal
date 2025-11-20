# Supabase Setup Guide

## ✅ **Supabase Database Configured!**

Your Supabase database is ready:
- **URL**: `https://scrksfxnkxmvvdzwmqnc.supabase.co`
- **Key**: Configured in code (use environment variables for production)

---

## 📋 **Step 1: Create Tables in Supabase**

Go to your Supabase dashboard → SQL Editor and run:

```sql
-- Main Social AE table
CREATE TABLE IF NOT EXISTS social_ae (
    id BIGSERIAL PRIMARY KEY,
    platform TEXT NOT NULL,
    post_id TEXT NOT NULL,
    post_url TEXT,
    raw_text TEXT NOT NULL,
    cleaned_text TEXT,
    created_utc BIGINT,
    created_date TIMESTAMP,
    drug_name TEXT,
    drug_match TEXT,
    reaction TEXT,
    meddra_pt TEXT,
    meddra_pt_code TEXT,
    confidence_score REAL,
    ae_prob REAL,
    subreddit TEXT,
    author_hash TEXT,
    score INTEGER,
    is_anonymized BOOLEAN DEFAULT FALSE,
    source_context TEXT,
    engagement_score INTEGER,
    seriousness BOOLEAN DEFAULT FALSE,
    outcome TEXT,
    report_date TIMESTAMP,
    inserted_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(platform, post_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_drug_name ON social_ae(drug_name);
CREATE INDEX IF NOT EXISTS idx_reaction ON social_ae(reaction);
CREATE INDEX IF NOT EXISTS idx_created_utc ON social_ae(created_utc);
CREATE INDEX IF NOT EXISTS idx_created_date ON social_ae(created_date);
CREATE INDEX IF NOT EXISTS idx_platform_post_id ON social_ae(platform, post_id);

-- Pull history table (optional)
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
```

---

## 🔐 **Step 2: Environment Variables (Optional)**

For production, set these in your environment or Streamlit secrets:

```bash
SUPABASE_URL=https://scrksfxnkxmvvdzwmqnc.supabase.co
SUPABASE_KEY=your_anon_key_here
```

Or in Streamlit `.streamlit/secrets.toml`:
```toml
[supabase]
url = "https://scrksfxnkxmvvdzwmqnc.supabase.co"
key = "your_anon_key_here"
```

---

## ✅ **Step 3: Test Connection**

The code will automatically:
1. Try Supabase first
2. Fallback to SQLite if Supabase unavailable
3. Show errors if connection fails

---

## 🚀 **Usage**

Once tables are created:
- Posts are automatically stored to Supabase when "💾 Store in database" is enabled
- Query from Supabase in "📊 Database" tab
- Social AE signals automatically merge with FAERS when "Include Social AE signals" is enabled

---

## 📊 **Monitoring**

Check your Supabase dashboard to:
- View stored posts
- Monitor database size
- Check pull history
- Run custom queries

---

## ⚠️ **Important Notes**

- **Free tier limits**: 500MB database, 2GB bandwidth
- **Rate limits**: Respect API limits
- **Backup**: Supabase handles backups automatically
- **Security**: Use Row Level Security (RLS) for production

---

## 🎉 **You're Ready!**

After creating the tables, the system will automatically use Supabase for storage!

