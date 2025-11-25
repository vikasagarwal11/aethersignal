# AetherSignal - Prioritized Next Steps

**Date:** January 2025  
**Context:** After fixing runtime issues (watchlist analytics, audit logging, landing CSS, Docker CMD)  
**Status:** Action Plan

---

## 🎯 Immediate Next Steps (This Week)

### 1. ✅ **Verify Fixes Are Working** (30 minutes)
**Priority:** CRITICAL  
**Action Items:**
- [ ] Test watchlist tab - verify analytics logging works
- [ ] Test audit trail - verify match counts are captured
- [ ] Test landing page - verify CTA buttons render correctly
- [ ] Test Docker API startup - verify Social AE API starts properly
- [ ] Run syntax check: `python -m py_compile app.py pages/*.py src/ui/*.py src/*.py`

**Why:** Ensure all fixes are working before moving forward.

---

### 2. **Update Documentation** (2-3 hours)
**Priority:** HIGH  
**Action Items:**
- [ ] Update `ACTUAL_IMPLEMENTATION_STATUS.md` - mark E2B export as ✅ IMPLEMENTED
- [ ] Update `FEATURE_BACKLOG.md` - remove completed features from backlog
- [ ] Update `CODEBASE_INTEGRITY_ANALYSIS.md` - note the runtime fixes you made
- [ ] Create `CHANGELOG.md` - document the fixes (watchlist analytics, audit logging, CSS, Docker)

**Why:** Documentation drift causes confusion. Quick win with high impact.

**Files to Update:**
- `ACTUAL_IMPLEMENTATION_STATUS.md` (line 97-101: E2B status)
- `FEATURE_BACKLOG.md` (remove completed items)
- `CODEBASE_INTEGRITY_ANALYSIS.md` (add note about runtime fixes)

---

### 3. **Improve Feature Discoverability** (1-2 days)
**Priority:** MEDIUM-HIGH  
**Action Items:**

#### A. Add Tooltips/Help Text
- [ ] Add tooltips to Literature Integration section
- [ ] Add tooltips to Exposure Normalization toggle
- [ ] Add tooltips to Case Processing expandable sections
- [ ] Add "What is this?" help buttons for advanced features

#### B. Create Features Guide
- [ ] Add "Features" section in sidebar or landing page
- [ ] List all available features with brief descriptions
- [ ] Link to relevant sections

#### C. Make Advanced Features More Visible
- [ ] Consider moving Literature Integration to a dedicated tab or prominent section
- [ ] Add visual indicators when exposure normalization is active
- [ ] Make case processing features more discoverable

**Why:** Users may not know about powerful features that are buried in expandable sections.

**Files to Modify:**
- `src/ui/results_display.py` (add tooltips, help text)
- `src/ui/sidebar.py` (add features guide)
- `app.py` (add features section to landing)

---

## 🔧 Short-Term Improvements (Next 2 Weeks)

### 4. **Refactor Large Files** (2-3 days)
**Priority:** MEDIUM  
**Action Items:**

#### Split `src/ui/results_display.py` (2077 lines)
Create separate files:
- [ ] `src/ui/results/overview.py` - Overview tab logic
- [ ] `src/ui/results/signals.py` - Signals tab logic
- [ ] `src/ui/results/trends.py` - Trends tab logic
- [ ] `src/ui/results/cases.py` - Cases tab logic
- [ ] `src/ui/results/report.py` - Report tab logic
- [ ] `src/ui/results/__init__.py` - Main display function that imports from submodules

**Benefits:**
- Easier to maintain
- Faster to navigate
- Better code organization
- Easier for multiple developers

**Files to Create:**
```
src/ui/results/
  __init__.py
  overview.py
  signals.py
  trends.py
  cases.py
  report.py
```

**Files to Modify:**
- `src/ui/results_display.py` → Split into above modules
- `pages/1_Quantum_PV_Explorer.py` → Update import if needed

---

### 5. **Clean Up Imports** (1 day)
**Priority:** MEDIUM  
**Action Items:**
- [ ] Organize imports in `src/ui/results_display.py` (or new split files)
- [ ] Group: standard library → third-party → local
- [ ] Remove unused imports
- [ ] Use `isort` or similar for consistent ordering

**Why:** 67 lines of imports is hard to manage. Clean imports improve readability.

**Command:**
```bash
pip install isort
isort src/ui/results_display.py
```

---

### 6. **Add Exposure/Incidence Metrics UI** (1-2 days)
**Priority:** MEDIUM  
**Decision Needed:** Should exposure/incidence metrics surface in UI?

**If YES:**
- [ ] Add toggle in sidebar: "Show incidence rates"
- [ ] Display incidence rates in Signals tab when exposure data available
- [ ] Add visual indicator when exposure normalization is active
- [ ] Show population-adjusted metrics alongside raw counts

**If NO:**
- [ ] Document that exposure normalization exists but is advanced feature
- [ ] Keep current implementation (available but not prominently displayed)

**Files to Modify:**
- `src/ui/sidebar.py` (add toggle)
- `src/ui/results_display.py` (or `signals.py` after refactor) (display metrics)

---

### 7. **Add Multi-Value Column Hints** (1 day)
**Priority:** MEDIUM  
**Decision Needed:** Should multi-value column hints surface in UI?

**If YES:**
- [ ] Add info badge in schema mapper showing which columns contain semicolon-separated values
- [ ] Add tooltip explaining how multi-value columns are handled
- [ ] Show example: "Drug1; Drug2" → split into separate rows

**If NO:**
- [ ] Keep current behavior (automatic splitting, no UI indication)

**Files to Modify:**
- `src/ui/schema_mapper.py` (add hints)
- `src/ui/upload_section.py` (add info display)

---

## 🚀 Medium-Term Enhancements (Next Month)

### 8. **Performance Optimizations** (3-4 days)
**Priority:** MEDIUM  
**Action Items:**
- [ ] Add pagination for large result sets (>10K rows)
- [ ] Implement caching for expensive operations (signal calculations)
- [ ] Add progress indicators for long-running queries
- [ ] Optimize dataframe operations (use vectorization where possible)

**Why:** Improves user experience with large datasets.

**Files to Modify:**
- `src/ui/results_display.py` (or split files) (add pagination)
- `src/app_helpers.py` (add caching)
- `src/signal_stats.py` (optimize calculations)

---

### 9. **Add Email Alerts for Watchlist** (3-4 days + service setup)
**Priority:** HIGH (converts free to paid)  
**Action Items:**
- [ ] Choose email service (SendGrid, AWS SES, Mailgun)
- [ ] Set up email service account and API keys
- [ ] Create `src/email_alerts.py` module
- [ ] Add email templates for watchlist alerts
- [ ] Create scheduled job system (or use existing scheduler)
- [ ] Add UI for email preferences in watchlist tab

**Dependencies:**
- Email service account
- Environment variables for API keys
- Background job scheduler (or cron)

**Files to Create:**
- `src/email_alerts.py`
- `src/scheduler.py` (if not exists)

**Files to Modify:**
- `src/watchlist_tab.py` (add email preferences UI)
- `src/social_ae/social_ae_scheduler.py` (or create new scheduler)

---

### 10. **Enhance Error Handling** (2-3 days)
**Priority:** MEDIUM  
**Action Items:**
- [ ] Add comprehensive edge case handling
- [ ] Improve error messages (user-friendly, actionable)
- [ ] Add validation for all user inputs
- [ ] Add logging for errors (not just silent failures)

**Why:** Improves robustness and user experience.

**Files to Modify:**
- All modules (add better error handling)
- `src/utils.py` (add validation helpers)

---

## 📋 Long-Term Enhancements (Next Quarter)

### 11. **Enterprise Features** (4-6 weeks)
**Priority:** HIGH (unlocks enterprise sales)  
**Action Items:**
- [ ] Implement RBAC (Role-Based Access Control)
- [ ] Complete 21 CFR Part 11 compliance features
- [ ] Add SSO integration (SAML/OIDC)
- [ ] Add audit trail enhancements

**Why:** Required for enterprise customers.

---

### 12. **Advanced Features** (2-3 weeks)
**Priority:** MEDIUM  
**Action Items:**
- [ ] Full query template library
- [ ] Persistent mapping templates
- [ ] Advanced visualizations (Sankey, timelines, bubble maps)
- [ ] Multi-drug interaction explorer

**Why:** Competitive differentiation.

---

## 🎯 Recommended Immediate Action Plan

### Week 1 (This Week)
1. ✅ **Verify all fixes work** (30 min)
2. **Update documentation** (2-3 hours)
3. **Start feature discoverability improvements** (1 day)

### Week 2
4. **Continue feature discoverability** (1 day)
5. **Decide on exposure/incidence metrics UI** (1 hour decision)
6. **Decide on multi-value column hints** (1 hour decision)
7. **Start refactoring large files** (if decided)

### Week 3-4
8. **Complete file refactoring** (if started)
9. **Clean up imports**
10. **Add exposure/incidence UI** (if decided)
11. **Add multi-value hints** (if decided)

### Month 2
12. **Performance optimizations**
13. **Email alerts implementation**
14. **Enhanced error handling**

---

## 💡 Decision Points

### 1. Exposure/Incidence Metrics UI
**Question:** Should exposure/incidence metrics be prominently displayed in UI?

**Considerations:**
- ✅ **YES** - Makes feature discoverable, shows value
- ❌ **NO** - Keeps UI clean, advanced users can find it

**Recommendation:** **YES** - Add toggle in sidebar, show when data available. Low effort, high value.

---

### 2. Multi-Value Column Hints
**Question:** Should multi-value column hints be shown in UI?

**Considerations:**
- ✅ **YES** - Helps users understand data structure
- ❌ **NO** - Automatic splitting works, no need to explain

**Recommendation:** **YES** - Add info badge in schema mapper. Very low effort, helps users.

---

### 3. File Refactoring Priority
**Question:** Should we refactor `results_display.py` now or later?

**Considerations:**
- ✅ **NOW** - Easier to maintain going forward
- ❌ **LATER** - Works fine as-is, can wait

**Recommendation:** **NOW** - Do it before adding more features. Prevents technical debt.

---

## 📊 Impact vs Effort Matrix

| Task | Impact | Effort | Priority |
|------|--------|--------|----------|
| Verify fixes | HIGH | LOW | 🔴 CRITICAL |
| Update docs | HIGH | LOW | 🔴 HIGH |
| Feature discoverability | MEDIUM | MEDIUM | 🟡 MEDIUM-HIGH |
| File refactoring | MEDIUM | MEDIUM | 🟡 MEDIUM |
| Clean imports | LOW | LOW | 🟢 LOW |
| Exposure metrics UI | MEDIUM | LOW | 🟡 MEDIUM |
| Multi-value hints | LOW | LOW | 🟢 LOW |
| Performance optimizations | MEDIUM | HIGH | 🟡 MEDIUM |
| Email alerts | HIGH | MEDIUM | 🔴 HIGH |
| Error handling | MEDIUM | MEDIUM | 🟡 MEDIUM |

---

## ✅ Quick Wins (Do First)

1. **Verify fixes** (30 min) - Ensure everything works
2. **Update documentation** (2-3 hours) - Fix drift, high impact
3. **Add tooltips** (2-3 hours) - Improve discoverability, low effort
4. **Add exposure metrics toggle** (if decided, 2-3 hours) - Low effort, medium impact
5. **Add multi-value hints** (if decided, 1 hour) - Very low effort, helps users

---

## 🚀 Next Step Recommendation

**Start with:** Verify fixes → Update documentation → Add tooltips

**Then decide on:**
- Exposure/incidence metrics UI (recommend YES)
- Multi-value column hints (recommend YES)
- File refactoring timing (recommend NOW, but can wait if busy)

**After decisions:** Proceed with chosen improvements in priority order.

---

**Last Updated:** January 2025  
**Next Review:** After completing Week 1 tasks

