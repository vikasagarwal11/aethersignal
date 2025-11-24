# E2B(R3) ICH Compliance Analysis

**Analysis Date:** January 2025  
**Source:** Official ICH E2B(R3) Implementation Guide v1.10  
**URL:** https://ich.org/page/e2br3-individual-case-safety-report-icsr-specification-and-related-files

## Critical Finding: Our E2B Structure Doesn't Match Official Format

### ❌ **Current Implementation Issue**

Our current `src/e2b_export.py` uses a **simplified structure** that doesn't match the official ICH E2B(R3) format:

**Our Structure (WRONG):**
```xml
<ichicsr>
  <messagenumber>1</messagenumber>
  <safetyreport>
    <safetyreportid>...</safetyreportid>
    <patient>...</patient>
    <reaction>...</reaction>
    <drug>...</drug>
  </safetyreport>
</ichicsr>
```

**Official ICH Structure (CORRECT):**
```xml
<MCCI_IN200100UV01 xmlns="urn:hl7-org:v3">
  <PORR_IN049016UV>
    <controlActProcess>
      <subject>
        <investigationEvent>
          <!-- Case data here -->
        </investigationEvent>
      </subject>
    </controlActProcess>
  </PORR_IN049016UV>
</MCCI_IN200100UV01>
```

### Required Changes

1. **Root Element**: Must be `MCCI_IN200100UV01` (not `ichicsr`)
2. **Namespace**: Must use `urn:hl7-org:v3` (not `http://www.ich.org/e2b`)
3. **Message Structure**: Must follow HL7 v3 message structure
4. **Schema Files**: Must validate against official XSD files in `multicacheschemas/`

## What We Have vs. What's Required

### ✅ **Fields We Can Map (Available in FAERS)**

| E2B Field | FAERS Source | Status |
|-----------|--------------|--------|
| Safety Report ID | `primaryid`/`caseid` | ✅ Available |
| Patient Age | DEMO: `age`, `age_cod` | ✅ Available |
| Patient Sex | DEMO: `sex` | ✅ Available |
| Reaction (MedDRA PT) | REAC: `pt` | ✅ Available |
| Drug Name | DRUG: `drugname` | ✅ Available |
| Seriousness | DEMO: `i_f_code` | ✅ Available |
| Outcome | OUTC: `outc_cod` | ✅ Available |
| Event Date | DEMO: `event_dt` | ✅ Available |
| Report Date | DEMO: `rept_dt`, `fda_dt` | ✅ Available |
| Country | DEMO: `occr_country` | ✅ Available |
| Drug Role | DRUG: `role_cod` | ⚠️ Available but not loaded |
| Reporter Code | DEMO: `rept_cod` | ⚠️ Available but not loaded |
| Indication | INDI: `indi_pt` | ⚠️ Available but not loaded |
| Dosage | DRUG: `dose_amt`, `dose_unit` | ⚠️ Available but not loaded |

### ❌ **Fields We Don't Have (Must Use Defaults)**

| E2B Field | Required? | Our Solution |
|-----------|-----------|-------------|
| Sender Organization | Yes | Use default: "AetherSignal Export" |
| Receiver Organization | Yes | Use default: "Regulatory Authority" |
| MedDRA Version | Yes | Use default: "27.0" (or detect from FAERS) |
| WHO Drug Dictionary | No | Skip (optional) |
| Reporter Name | Optional | Skip if not available |
| Medical History | Optional | Skip if not available |

## Implementation Status

### ✅ **Implemented (But Needs Fixing)**

1. **E2B Export Module** (`src/e2b_export.py`)
   - ✅ Generates XML structure
   - ✅ Maps core fields
   - ❌ **WRONG STRUCTURE** - Doesn't match ICH format
   - ❌ **NO XSD VALIDATION** - Not using official schemas

2. **Export Button** (in `src/ui/results_display.py`)
   - ✅ UI button exists
   - ✅ Downloads XML file
   - ⚠️ Downloads incorrect format

### ❌ **Not Implemented**

1. **XSD Validation**
   - ❌ Not using official ICH XSD files
   - ❌ No validation against `PORR_MT049016UV.xsd` or similar

2. **Code List Validation**
   - ❌ Not validating against E2B code lists (CL1-CL27)
   - ❌ Not using official code values

3. **Reference Instance Compliance**
   - ❌ Not matching official reference instances
   - ❌ Missing required HL7 v3 elements

## Required Actions

### 1. **Update E2B Export Structure** (CRITICAL)

**Priority:** HIGH  
**Effort:** 2-3 days  
**Files:** `src/e2b_export.py`

**Changes Needed:**
- Replace root element with `MCCI_IN200100UV01`
- Use HL7 v3 namespace (`urn:hl7-org:v3`)
- Follow official message structure from reference instances
- Map all fields according to ICH Implementation Guide

### 2. **Add XSD Validation** (HIGH PRIORITY)

**Priority:** HIGH  
**Effort:** 1-2 days  
**Files:** `src/e2b_export.py`

**Changes Needed:**
- Use `lxml` to validate against official XSD files
- Load XSD from `NotToCheckin/IG_Complete_Package_v1_10/IG_Complete_Package_v1_10/4_ICH_ICSR_Schema_Files/multicacheschemas/`
- Display validation errors in UI
- Prevent export if validation fails (optional)

### 3. **Enhance Data Loading** (MEDIUM PRIORITY)

**Priority:** MEDIUM  
**Effort:** 1 day  
**Files:** `src/faers_loader.py`

**Changes Needed:**
- Preserve `role_cod` from DRUG file
- Preserve `rept_cod` from DEMO file
- Preserve `indi_pt` from INDI file
- Preserve `dose_amt`, `dose_unit` from DRUG file

### 4. **Add Code List Validation** (LOW PRIORITY)

**Priority:** LOW  
**Effort:** 2-3 days  
**Files:** `src/e2b_export.py` (new validation module)

**Changes Needed:**
- Load E2B code lists from `7_E2B Bilingual Code Lists v2.10/`
- Validate code values against official lists
- Warn about invalid codes

## Current Limitations

⚠️ **Structural Compliance**: Our XML doesn't match ICH format  
⚠️ **Validation**: No XSD validation  
⚠️ **Code Lists**: Not using official code values  
✅ **Data Mapping**: Core fields are mappable  
✅ **Export Functionality**: Works but generates non-compliant XML

## Recommendations

1. **Immediate**: Update E2B export to match official ICH structure
2. **Short-term**: Add XSD validation
3. **Medium-term**: Enhance data loading to include all E2B fields
4. **Long-term**: Add code list validation

## Testing

After fixes:
1. Generate E2B XML from sample case
2. Validate against official XSD
3. Compare with reference instances
4. Test with FDA/EMA validation tools (if available)

