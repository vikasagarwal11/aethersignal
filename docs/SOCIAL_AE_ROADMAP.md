# Social AE Module - Roadmap to Full Vision

## Current State (MVP - Week 0)
✅ **Built:**
- Reddit/X API fetching
- Rule-based cleaning (spam/noise removal)
- Slang → MedDRA mapping (50+ patterns)
- Searchable dashboard UI
- CSV export
- Session-based storage

## Gap Analysis

### Phase 1: Data Persistence (Weeks 1-2)
**Goal:** Store posts in database for historical tracking

**Tasks:**
- [ ] Add PostgreSQL/SQLite database schema
- [ ] Create `social_ae_storage.py` module
- [ ] Store raw + cleaned posts with timestamps
- [ ] Add deduplication (by post_id + platform)
- [ ] Daily pull scheduler (cron/APScheduler)

**Schema:**
```sql
CREATE TABLE social_posts (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20),
    post_id VARCHAR(255),
    raw_text TEXT,
    cleaned_text TEXT,
    created_utc BIGINT,
    drug_match VARCHAR(100),
    reaction VARCHAR(255),
    meddra_pt VARCHAR(255),
    confidence_score FLOAT,
    is_anonymized BOOLEAN,
    fetched_at TIMESTAMP,
    UNIQUE(platform, post_id)
);

CREATE INDEX idx_drug_match ON social_posts(drug_match);
CREATE INDEX idx_reaction ON social_posts(reaction);
CREATE INDEX idx_created_utc ON social_posts(created_utc);
```

### Phase 2: Confidence Scoring (Weeks 3-4)
**Goal:** Add confidence scores for reaction detection

**Tasks:**
- [ ] Implement confidence scoring in `social_mapper.py`
- [ ] Multi-factor scoring:
  - Pattern match strength (exact vs fuzzy)
  - Context indicators (negation detection)
  - Post quality score
- [ ] Display confidence in dashboard
- [ ] Filter by confidence threshold

**Scoring Logic:**
```python
confidence = (
    pattern_match_score * 0.4 +  # Exact match = 1.0, fuzzy = 0.6
    context_score * 0.3 +         # Has drug mention = 1.0
    quality_score * 0.3            # Post quality from cleaner
)
```

### Phase 3: Anonymization (Week 5)
**Goal:** HIPAA-compliant anonymization

**Tasks:**
- [ ] Create `social_anonymizer.py` module
- [ ] Remove PII (names, emails, phone numbers)
- [ ] Hash usernames
- [ ] Remove location-specific details
- [ ] Add anonymization flag to database

### Phase 4: Daily Automation (Week 6)
**Goal:** Automated daily pulls

**Tasks:**
- [ ] Set up scheduled jobs (APScheduler or cron)
- [ ] Default drug watchlist (GLP-1s, Adderall, etc.)
- [ ] Error handling and retry logic
- [ ] Email alerts for failures
- [ ] Pull history tracking

### Phase 5: Tiered Access (Weeks 7-8)
**Goal:** Free/paid access model

**Tasks:**
- [ ] Add user authentication (optional)
- [ ] Free tier: Last 7 days, limited exports
- [ ] Paid tier: Full history, unlimited exports, API access
- [ ] Stripe integration for payments
- [ ] Usage tracking per user

### Phase 6: AI Enhancement Prep (Weeks 9-10)
**Goal:** Prepare for ML fine-tuning

**Tasks:**
- [ ] Export labeled dataset (post + reaction + confidence)
- [ ] Create annotation interface for manual labeling
- [ ] Integrate with MTurk/annotation tools
- [ ] Data quality metrics dashboard

## Quick Wins (Can Do Now)

1. **Add Confidence Scores** (2-3 hours)
   - Enhance `social_mapper.py` with scoring
   - Display in dashboard

2. **Basic Persistence** (4-6 hours)
   - SQLite for local dev
   - Store posts in `data/social_ae/` directory

3. **Anonymization** (3-4 hours)
   - Basic PII removal
   - Username hashing

## Cost Estimates

| Phase | Development | Infrastructure | Total |
|-------|-------------|---------------|-------|
| Phase 1 (Persistence) | $2K | $50/mo (AWS RDS) | $2K + $50/mo |
| Phase 2 (Confidence) | $1K | - | $1K |
| Phase 3 (Anonymization) | $1.5K | - | $1.5K |
| Phase 4 (Automation) | $2K | $20/mo (scheduler) | $2K + $20/mo |
| Phase 5 (Tiered Access) | $5K | $100/mo (Stripe fees) | $5K + $100/mo |
| Phase 6 (AI Prep) | $3K | $50/mo (storage) | $3K + $50/mo |
| **Total** | **$14.5K** | **$220/mo** | **$14.5K + $220/mo** |

## Next Steps

1. **Immediate (This Week):**
   - Add confidence scoring to current module
   - Add basic SQLite persistence
   - Test with GLP-1 keywords

2. **Short-term (Next 2 Weeks):**
   - Set up PostgreSQL
   - Implement daily pull scheduler
   - Add anonymization

3. **Medium-term (Month 2):**
   - Launch public beta
   - Add tiered access
   - Start collecting labeled data

