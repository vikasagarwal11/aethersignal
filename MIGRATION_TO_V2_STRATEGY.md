# 🚀 AetherSignal v2 Migration Strategy

## Overview

This document outlines the strategy for migrating from the current Streamlit-based architecture to a modern FastAPI + React/Next.js architecture.

---

## 📁 Recommended Folder Structure

```
aethersignal/
├── backup/                          # Current working Streamlit app (DO NOT MODIFY)
│   ├── app.py
│   ├── pages/
│   ├── src/
│   ├── requirements.txt
│   └── ... (all current files)
│
├── v2/                              # New architecture (fresh start)
│   ├── backend/                     # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── v1/
│   │   │   │       ├── endpoints/
│   │   │   │       │   ├── signals.py
│   │   │   │       │   ├── upload.py
│   │   │   │       │   ├── social_ae.py
│   │   │   │       │   ├── copilot.py
│   │   │   │       │   └── mechanism.py
│   │   │   │       └── router.py
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   ├── security.py
│   │   │   │   └── dependencies.py
│   │   │   ├── services/            # Business logic (copy from backup/src/)
│   │   │   │   ├── signal_service.py
│   │   │   │   ├── query_service.py
│   │   │   │   ├── normalization_service.py
│   │   │   │   └── ...
│   │   │   ├── models/              # Pydantic models
│   │   │   │   ├── schemas.py
│   │   │   │   └── database.py
│   │   │   └── repositories/        # Data access
│   │   │       ├── case_repository.py
│   │   │       └── ...
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── main.py
│   │
│   ├── frontend/                    # React/Next.js frontend
│   │   ├── app/                     # Next.js app directory
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── dashboard/
│   │   │   ├── signals/
│   │   │   ├── social-ae/
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── TopNav.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Upload.tsx
│   │   │   ├── QueryInterface.tsx
│   │   │   └── ...
│   │   ├── lib/
│   │   │   ├── api-client.ts
│   │   │   └── ...
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── shared/                      # Shared types/utilities
│   │   └── types/
│   │       └── index.ts
│   │
│   └── infrastructure/              # Deployment configs
│       ├── docker/
│       ├── kubernetes/
│       └── terraform/
│
└── docs/                            # Documentation
    ├── AETHERSIGNAL_ENGINEERING_BLUEPRINT.md
    ├── ARCHITECTURAL_REBUILD_RECOMMENDATIONS.md
    └── MIGRATION_TO_V2_STRATEGY.md (this file)
```

---

## ✅ Why This Approach Works

### Advantages:

1. **✅ Clean Slate**
   - No legacy code constraints
   - Modern architecture from day one
   - Best practices from the start

2. **✅ Easy Reference**
   - Copy code from `backup/src/` as needed
   - Understand existing logic before adapting
   - No risk of breaking working code

3. **✅ Parallel Development**
   - Keep current app running (backup/)
   - Develop v2 alongside (v2/)
   - Test new architecture without risk

4. **✅ Gradual Migration**
   - Migrate features one by one
   - Test each feature independently
   - Roll back easily if needed

5. **✅ Team Collaboration**
   - Clear separation of old vs new
   - Easy to onboard new developers
   - No confusion about which code to modify

---

## 🎯 Migration Strategy

### Phase 1: Setup (Week 1)

**1. Create Backup:**
```bash
# In project root
mkdir backup
cp -r . backup/  # Copy everything except backup itself
# Or use git:
git checkout -b backup/streamlit-v1
```

**2. Create v2 Structure:**
```bash
mkdir -p v2/backend v2/frontend v2/shared v2/infrastructure
```

**3. Initialize Backend:**
```bash
cd v2/backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install fastapi uvicorn pydantic sqlalchemy
```

**4. Initialize Frontend:**
```bash
cd v2/frontend
npx create-next-app@latest . --typescript --tailwind --app
```

### Phase 2: Backend Skeleton (Weeks 2-3)

**1. Create FastAPI Structure:**
- Set up `main.py` with basic FastAPI app
- Create API router structure
- Set up authentication (Supabase Auth)
- Create health check endpoint

**2. Migrate First Service:**
- Start with `signal_stats.py` → `services/signal_service.py`
- Wrap in FastAPI endpoint: `POST /api/v1/signals/query`
- Test with Postman/curl

**3. Add Database Layer:**
- Set up SQLAlchemy models
- Create repository pattern
- Connect to Supabase PostgreSQL

**Example:**
```python
# v2/backend/app/services/signal_service.py
# Copy logic from backup/src/signal_stats.py
# Adapt to be pure Python (no Streamlit dependencies)

from typing import Dict, List
import pandas as pd

class SignalService:
    def __init__(self):
        # Initialize any dependencies
        pass
    
    def calculate_signals(self, df: pd.DataFrame, filters: Dict) -> List[Dict]:
        """
        Calculate PRR/ROR signals.
        Copied from backup/src/signal_stats.py, adapted for service layer.
        """
        # Copy logic from backup/src/signal_stats.py
        # Remove Streamlit dependencies (st.session_state, etc.)
        # Return pure Python objects
        pass
```

### Phase 3: Frontend Shell (Weeks 4-5)

**1. Create Layout:**
- `app/layout.tsx` - Root layout
- `components/TopNav.tsx` - Top navigation
- `components/Sidebar.tsx` - Sidebar navigation

**2. Create First Page:**
- `app/signals/page.tsx` - Signal explorer page
- `components/Upload.tsx` - File upload component
- `components/QueryInterface.tsx` - Query interface

**3. Connect to Backend:**
- `lib/api-client.ts` - API client
- Call `/api/v1/signals/query` endpoint
- Display results

### Phase 4: Feature Migration (Weeks 6-12)

**Migrate features one by one:**

1. **File Upload** (Week 6)
   - Copy `backup/src/ui/upload_section.py` logic
   - Adapt to FastAPI endpoint
   - Create React upload component

2. **Query Interface** (Week 7)
   - Copy `backup/src/nl_query_parser.py`
   - Create `services/query_service.py`
   - Build React query interface

3. **Signal Detection** (Week 8)
   - Copy `backup/src/signal_stats.py`
   - Create `services/signal_service.py`
   - Display results in React

4. **Social AE** (Week 9)
   - Copy `backup/src/social_ae/*`
   - Create API endpoints
   - Build React dashboard

5. **Copilot** (Week 10)
   - Copy `backup/src/copilot/*`
   - Create API endpoints
   - Build React chat interface

6. **Mechanism AI** (Week 11)
   - Copy `backup/src/mechanism/*`
   - Create API endpoints
   - Build React interface

7. **Reports** (Week 12)
   - Copy `backup/src/reports/*`
   - Create API endpoints
   - Build React report generator

---

## 📋 Code Migration Checklist

When copying code from `backup/` to `v2/`:

### ✅ Do:
- Copy business logic (pure Python functions)
- Adapt to service layer pattern
- Remove Streamlit dependencies (`st.*`)
- Add type hints (Pydantic models)
- Add error handling
- Add logging
- Write tests

### ❌ Don't:
- Copy Streamlit UI code directly
- Keep `st.session_state` dependencies
- Keep Streamlit-specific imports
- Copy without understanding the logic
- Skip testing

### 🔄 Adaptation Pattern:

**Before (Streamlit):**
```python
# backup/src/signal_stats.py
import streamlit as st

def calculate_prr(df, drug, reaction):
    # Uses st.session_state
    data = st.session_state.get("normalized_data")
    # ...
    st.write("PRR:", prr_value)
```

**After (FastAPI Service):**
```python
# v2/backend/app/services/signal_service.py
from typing import Dict, Optional
import pandas as pd

class SignalService:
    def calculate_prr(
        self, 
        df: pd.DataFrame, 
        drug: str, 
        reaction: str
    ) -> Dict[str, float]:
        """
        Calculate PRR for drug-reaction combination.
        Returns dictionary with PRR value and confidence interval.
        """
        # Same logic, but returns data instead of displaying
        prr_value = ...
        return {
            "prr": prr_value,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper
        }
```

---

## 🔗 Reference Strategy

### How to Reference Backup Code:

**1. Read First:**
```bash
# Understand the logic
cat backup/src/signal_stats.py
```

**2. Copy Logic:**
```python
# v2/backend/app/services/signal_service.py
# Adapted from backup/src/signal_stats.py
# Removed Streamlit dependencies
```

**3. Test:**
```python
# v2/backend/tests/test_signal_service.py
def test_calculate_prr():
    # Test the migrated logic
    pass
```

**4. Document:**
```python
# Add comment linking to original
# Original: backup/src/signal_stats.py:calculate_prr()
```

---

## 🚦 Development Workflow

### Daily Workflow:

1. **Morning:**
   - Check `backup/` for any bug fixes
   - If critical, apply to `v2/` as well

2. **Development:**
   - Work in `v2/` folder
   - Reference `backup/` when needed
   - Copy and adapt code

3. **Testing:**
   - Test new features in `v2/`
   - Compare results with `backup/` if needed
   - Ensure feature parity

4. **Deployment:**
   - Deploy `v2/` to staging
   - Test thoroughly
   - Deploy to production when ready

---

## 📊 Progress Tracking

### Migration Status:

| Feature | Status | Notes |
|---------|--------|-------|
| Backend Setup | ⬜ Not Started | FastAPI structure |
| Signal Service | ⬜ Not Started | Core business logic |
| Upload Service | ⬜ Not Started | File handling |
| Query Service | ⬜ Not Started | NL parsing |
| Frontend Layout | ⬜ Not Started | React components |
| Signal UI | ⬜ Not Started | Results display |
| Social AE | ⬜ Not Started | Social dashboard |
| Copilot | ⬜ Not Started | AI assistant |
| Mechanism AI | ⬜ Not Started | Pathway analysis |
| Reports | ⬜ Not Started | PSUR/DSUR |

**Status Legend:**
- ⬜ Not Started
- 🟡 In Progress
- ✅ Complete
- ❌ Blocked

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- ✅ FastAPI backend running
- ✅ One endpoint working (`/api/v1/signals/query`)
- ✅ Can call from Postman/curl
- ✅ Returns correct results

### Phase 2 Complete When:
- ✅ React frontend running
- ✅ Can upload file
- ✅ Can query signals
- ✅ Results display correctly

### Phase 3 Complete When:
- ✅ All major features migrated
- ✅ Feature parity with backup/
- ✅ Performance acceptable
- ✅ Tests passing
- ✅ Ready for production

---

## 🚨 Important Notes

### Do NOT:
- ❌ Modify `backup/` folder (it's your reference)
- ❌ Delete `backup/` (keep it forever)
- ❌ Copy code without understanding
- ❌ Skip testing
- ❌ Deploy v2 before it's ready

### DO:
- ✅ Keep `backup/` as reference
- ✅ Test each migrated feature
- ✅ Document what you copy
- ✅ Maintain feature parity
- ✅ Ask for help when stuck

---

## 📚 Resources

### Reference Documents:
- `AETHERSIGNAL_ENGINEERING_BLUEPRINT.md` - Complete system documentation
- `ARCHITECTURAL_REBUILD_RECOMMENDATIONS.md` - Architecture recommendations
- `DATABASE_INVENTORY_AND_CURRENT_STATE.md` - Complete database inventory and current state
- `COMPREHENSIVE_PERFORMANCE_OPTIMIZATION_ANALYSIS.md` - Performance optimization strategy

### Code References:
- `backup/src/` - All existing business logic
- `backup/pages/` - UI patterns (for reference, not copy)

---

## 🗄️ Database Considerations for v2 Migration

### Current Database State

**See:** `DATABASE_INVENTORY_AND_CURRENT_STATE.md` for complete details

**Key Findings:**
1. **Tables That Exist But Are NOT Used:**
   - `activity_logs` - Table exists but NOT WRITTEN TO (logging writes to file only)
   - `saved_queries` - Table exists but NOT WRITTEN TO (stored in session only)
   - `query_history` - Table exists but NOT WRITTEN TO (stored in session only)

2. **Missing Critical Tables:**
   - `file_upload_history` - Track individual file uploads
   - `pre_calculated_stats` - Cache common query results
   - `background_jobs` - Job queue for background processing
   - `query_learning` - Learn from user queries

3. **Missing Critical Indexes:**
   - `idx_pv_cases_user_drug_reaction` - For common queries (10-20x faster)
   - `idx_pv_cases_created_at_org` - For dataset listing (<500ms vs 5-10s)
   - `idx_pv_cases_event_date` - For trend analysis

### Database Tasks for v2

**Before Migration:**
- [ ] Fix `activity_logs` table usage (write to database, not file)
- [ ] Fix `saved_queries` table usage (persist to database)
- [ ] Fix `query_history` table usage (persist to database)
- [ ] Add missing critical indexes to `pv_cases`
- [ ] Create `file_upload_history` table
- [ ] Create `pre_calculated_stats` table

**During Migration:**
- Keep all existing database schema
- Add new tables as needed
- Migrate session state data to database where applicable
- Ensure RLS policies work correctly

**After Migration:**
- Monitor query performance
- Add additional indexes based on query patterns
- Implement background jobs system
- Implement query learning system

---

## 🎉 Next Steps

1. **Create backup folder** (if not done)
2. **Create v2 folder structure**
3. **Initialize FastAPI backend**
4. **Initialize Next.js frontend**
5. **Start with Phase 1: Backend Skeleton**

**Ready to start? Let's begin with Phase 1!**

---

**Last Updated:** January 2025  
**Status:** Ready to Begin

