# 🏢 **SAAS MULTI-TENANT ARCHITECTURE - AetherSignal**

**Date:** Current  
**Status:** Architecture Confirmation  
**Purpose:** Define organization-level configuration for SaaS PV platform

---

## ✅ **ARCHITECTURE CONFIRMATION**

**YES - I completely agree with this approach.**

For AetherSignal as a SaaS platform:

- ✅ **Organization-specific data MUST be stored at Tenant/Profile/Org level**
- ✅ **Auto-fill sections from FAERS/Social/Literature (not org-specific)**
- ✅ **Org-specific sections require tenant configuration**
- ✅ **NEVER show raw placeholders - use clean "not configured" messages**

---

## 🎯 **SECTION CATEGORIZATION**

### **✅ [AUTO-FILL] - Not Org-Specific (Can Fill from Your Data)**

These come from FAERS, Social AE, Literature, and your engines:

| Section | Source | Status |
|---------|--------|--------|
| **Identified Risks** | Signal Engine | ✅ Auto-fill |
| **Trend Analysis** | FAERS/Lit/Social | ✅ Auto-fill |
| **Severity Distribution** | Stored AE data | ✅ Auto-fill |
| **Novelty Assessment** | Cross-source engine | ✅ Auto-fill |
| **Social vs FAERS Alignment** | Unified data | ✅ Auto-fill |
| **Mechanism/Hypothesis** | LLM + Mechanism engine | ✅ Auto-fill |
| **Drug-AE Line Listings** | Database | ✅ Auto-fill |
| **Tabulations** | DataFrame → Table | ✅ Auto-fill |
| **Benefit-Risk AI Summary** | LLM based on above | ✅ Auto-fill |

**These are NOT organization-specific** - same data for all tenants.

---

### **🔴 [ORG-CONFIG] - Organization-Specific (MUST be Tenant Config)**

These vary by company and MUST be configured per tenant:

| PSUR/DSUR Section | Why Org-Specific? | Needs Tenant Config? |
|-------------------|-------------------|---------------------|
| **Marketing Authorization Status** | Varies by company's approvals worldwide | ✅ **YES** |
| **Safety Actions Taken** | Only company knows letters/labeling actions | ✅ **YES** |
| **RMP Changes** | RMP is owned by the MAH | ✅ **YES** |
| **Patient Exposure Estimates** | Based on their sales/prescriptions | ✅ **YES** |
| **Clinical Development Status** | Depends on their pipeline | ✅ **YES** |
| **Regulatory Strategy Summary** | Internal regulatory decisions | ✅ **YES** |
| **Pharmacovigilance System Summary** | Each company has its own QMS | ✅ **YES** |
| **Product Portfolio** | Each tenant has different products | ✅ **YES** |
| **Label Change Plans** | Depends on their product | ✅ **YES** |

**These MUST be configurable at the org level.**

---

## 🏗️ **ORG PROFILE SCHEMA**

### **Database Structure**

```sql
-- Organization Profile Configuration
CREATE TABLE org_profile_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id VARCHAR(255) UNIQUE NOT NULL,
    org_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Products configuration (JSONB)
    products JSONB DEFAULT '[]'::jsonb,
    
    -- Regulatory settings (JSONB)
    regulatory_config JSONB DEFAULT '{}'::jsonb,
    
    -- Safety actions (JSONB)
    safety_actions JSONB DEFAULT '[]'::jsonb,
    
    -- RMP configuration (JSONB)
    rmp_config JSONB DEFAULT '{}'::jsonb,
    
    -- Clinical development (JSONB)
    clinical_program JSONB DEFAULT '[]'::jsonb,
    
    -- Exposure estimates (JSONB)
    exposure_estimates JSONB DEFAULT '{}'::jsonb
);

-- Example products JSONB structure:
{
  "products": [
    {
      "name": "DrugA",
      "route": "oral",
      "atc": "A10BX",
      "authorization_status": {
        "us": {
          "status": "approved",
          "date": "2020-01-15",
          "indication": "Type 2 diabetes"
        },
        "eu": {
          "status": "approved",
          "date": "2020-03-20",
          "indication": "Type 2 diabetes"
        },
        "uk": {
          "status": "pending",
          "submission_date": "2024-12-01"
        }
      },
      "exposure_estimates": {
        "q1_2025": "2.1M patient-years",
        "q2_2025": "2.3M patient-years"
      },
      "rmp_updates": [
        {
          "date": "2025-03-20",
          "change": "Added pancreatitis monitoring",
          "rationale": "Based on signal analysis"
        }
      ],
      "safety_actions": [
        {
          "date": "2025-02-15",
          "action": "Dear HCP letter issued",
          "type": "communication",
          "description": "Updated safety information regarding pancreatitis risk"
        }
      ],
      "clinical_program": [
        {
          "trial_id": "NCT12345678",
          "phase": "Phase 3",
          "status": "ongoing",
          "countries": ["US", "EU"],
          "indication": "Extended indication"
        }
      ]
    }
  ]
}
```

---

## 🔧 **IMPLEMENTATION APPROACH**

### **Option C: Hybrid Approach (Recommended)**

**Build Org Profile infrastructure + Replace placeholders simultaneously**

1. **Create Org Profile Schema**
   - Database tables
   - Configuration storage
   - API endpoints

2. **Create Org Profile UI**
   - Admin settings page
   - Regulatory config page
   - Product management

3. **Update PSUR/DSUR Generator**
   - Query org config for org-specific sections
   - Auto-fill from data for non-org sections
   - Clean fallback messages if config missing

4. **Replace All Placeholders**
   - Real data where available
   - Org config where needed
   - Clean "not configured" messages

---

## 📋 **CLEAN FALLBACK BEHAVIOR**

### **❌ NEVER Show:**

```
"Marketing authorization status (placeholder - would query regulatory databases)"
```

### **✅ ALWAYS Show:**

```
**Marketing Authorization Status**

No organization-specific regulatory data provided. 

Please update your Org Profile > Regulatory Settings to enable this section.

[Link to Org Profile Settings]
```

---

## 🎯 **IMPLEMENTATION PRIORITY**

### **Phase 1: Org Profile Infrastructure**
1. Create `org_profile_config` table
2. Create `OrgProfileManager` class
3. Create org profile API endpoints
4. Create org profile UI page

### **Phase 2: Update PSUR/DSUR Generator**
1. Query org config for org-specific sections
2. Auto-fill non-org sections from data
3. Replace all placeholders with clean logic
4. Add fallback messages

### **Phase 3: Replace All Placeholders**
1. Section 1: Marketing Auth → Query org config
2. Section 2: Safety Actions → Query org config + FDA alerts
3. Section 3: RMP Changes → Query org config
4. Section 4: Exposure → Query org config + case counts
5. Section 5: Signals → Auto-fill from data
6. Section 6: Benefit-Risk → Auto-fill from data + LLM
7. Section 7: Conclusions → Auto-fill from data + LLM
8. Annexes → Auto-fill from data

---

## ✅ **CONFIRMED ARCHITECTURE**

- ✅ **Multi-tenant SaaS architecture**
- ✅ **Per-org configuration storage**
- ✅ **Auto-filled analytical content**
- ✅ **Manual/config-driven regulatory sections**
- ✅ **Clean fallback text - NO placeholders**

---

**Ready to implement Option C (Hybrid Approach)?** 🚀

