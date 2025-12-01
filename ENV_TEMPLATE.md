# .env Template for AetherSignal

Copy this content to a `.env` file in your project root.

```bash
# ============================================
# AetherSignal Environment Variables Template
# ============================================
# Copy this file to .env and fill in your API keys
# Free sources work without keys, paid sources require keys

# ============================================
# FREE APIs (Optional - work without keys)
# ============================================

# OpenFDA API (free, no key required, but can use key for higher rate limits)
OPENFDA_API_KEY=

# PubMed API (free, no key required, but can use key for higher rate limits)
PUBMED_API_KEY=

# ClinicalTrials.gov API (free, no key required)
CLINICALTRIALS_API_KEY=

# Google Places API (optional - for pharmacy/clinic reviews)
# Get key from: https://console.cloud.google.com/
GOOGLE_PLACES_API_KEY=

# DailyMed API (free, no key required)
DAILYMED_API_KEY=

# ============================================
# PAID APIs (Optional - add keys to enable)
# ============================================

# Human API - Patient health data aggregation
# Get key from: https://www.humanapi.co/
HUMAN_API_KEY=

# Metriport - EHR/claims data integration
# Get key from: https://www.metriport.com/
METRIPORT_API_KEY=

# DrugBank - Drug database and chemical structures
# Get key from: https://go.drugbank.com/
DRUGBANK_KEY=

# VigiBase (WHO) - Global adverse event database
# Get key from: https://www.who-umc.org/
VIGIBASE_KEY=

# Epic FHIR - Hospital EHR integration
# Get key from: Epic MyChart API program
EPIC_FHIR_KEY=

# Cerner FHIR - Hospital EHR integration
# Get key from: Cerner Developer Portal
CERNER_FHIR_KEY=

# OHDSI - Observational Health Data Sciences and Informatics
# Get key from: https://www.ohdsi.org/
OHDSI_KEY=

# ============================================
# SOCIAL MEDIA APIs
# ============================================

# X (Twitter) API v2 Bearer Token
# Get from: https://developer.twitter.com/
X_API_BEARER_TOKEN=

# Reddit API (optional - uses Pushshift by default)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=

# ============================================
# DATABASE CONFIGURATION
# ============================================

# Supabase (for cloud storage)
SUPABASE_URL=
SUPABASE_KEY=

# ============================================
# APPLICATION SETTINGS
# ============================================

# Environment (development, staging, production)
ENVIRONMENT=development

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

## Instructions

1. Copy the content above to a file named `.env` in your project root
2. Fill in API keys for sources you want to enable
3. Free sources work without keys
4. Paid sources require keys to function
5. Never commit `.env` to version control (it's in `.gitignore`)

