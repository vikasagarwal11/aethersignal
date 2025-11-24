# E2B(R3) Field Analysis: What We Have vs. What's Required

## Executive Summary

✅ **We CAN generate E2B(R3) XML** with current data, but with **limitations**:
- **Core fields**: ✅ Available (case ID, patient, drugs, reactions, dates)
- **Reporter info**: ⚠️ Available in FAERS but may not be in normalized_df
- **MedDRA coding**: ⚠️ We have PT (Preferred Term) but may not be validated
- **WHO Drug coding**: ❌ Not available (optional in E2B R3)
- **Sender/Receiver**: ⚠️ Can use defaults but not case-specific

## E2B(R3) Mandatory Fields (Minimum ICSR)

### ✅ **Fields We HAVE (from FAERS)**

| E2B Field | FAERS Source | Our Column | Status |
|----------|--------------|------------|--------|
| **Safety Report ID** | `primaryid` or `caseid` | `caseid`, `primaryid` | ✅ Available |
| **Patient Age** | DEMO: `age`, `age_cod` | `age`, `age_yrs` | ✅ Available |
| **Patient Sex** | DEMO: `sex` | `sex`, `gender` | ✅ Available |
| **Reaction (PT)** | REAC: `pt` | `reaction`, `reaction_meddra` | ✅ Available |
| **Drug Name** | DRUG: `drugname` | `drug_name` | ✅ Available |
| **Seriousness** | DEMO: `i_f_code` | `seriousness`, `serious` | ✅ Available |
| **Outcome** | OUTC: `outc_cod` | `outcome`, `outc_cod` | ✅ Available |
| **Event Date** | DEMO: `event_dt` | `onset_date`, `event_date` | ✅ Available |
| **Report Date** | DEMO: `rept_dt`, `fda_dt` | `report_date`, `receive_date` | ✅ Available |
| **Country** | DEMO: `occr_country`, `reporter_country` | `country` | ✅ Available |

### ⚠️ **Fields We HAVE in FAERS but May Not Be Loaded**

| E2B Field | FAERS Source | Our Column | Action Needed |
|----------|--------------|------------|---------------|
| **Reporter Type** | DEMO: `rept_cod` | ❌ Not in normalized_df | Need to load from DEMO |
| **Reporter Country** | DEMO: `reporter_country` | ❌ Not in normalized_df | Need to load from DEMO |
| **Report Source** | RPSR: `rpsr_cod` | ❌ Not in normalized_df | Need to load from RPSR |
| **Manufacturer Sender** | DEMO: `mfr_sndr` | ❌ Not in normalized_df | Need to load from DEMO |
| **Authorization Number** | DEMO: `auth_num` | ❌ Not in normalized_df | Need to load from DEMO |
| **Manufacturer Number** | DEMO: `mfr_num` | ❌ Not in normalized_df | Need to load from DEMO |
| **Indication** | INDI: `indi_pt` | ❌ Not in normalized_df | Need to load from INDI |
| **Drug Role** | DRUG: `role_cod` | ❌ Not in normalized_df | Need to load from DRUG |
| **Dosage** | DRUG: `dose_amt`, `dose_unit` | ❌ Not in normalized_df | Need to load from DRUG |

### ❌ **Fields We DON'T HAVE (Must Use Defaults)**

| E2B Field | Required? | Our Solution |
|-----------|-----------|--------------|
| **Sender Organization** | Yes | Use default: "AetherSignal Export" |
| **Sender Type** | Yes | Use default: "Regulatory Authority" (1) |
| **Receiver Organization** | Yes | Use default: "Regulatory Authority" |
| **Receiver Type** | Yes | Use default: "Manufacturer" (2) |
| **MedDRA Version** | Yes | Use default: "27.0" (latest) |
| **WHO Drug Dictionary** | No (optional) | Skip if not available |
| **Reporter Name** | Optional | Skip if not available |
| **Reporter Qualification** | Optional | Skip if not available |

## Can We Generate E2B(R3) Without MedDRA/WHO Drug Coding?

### ✅ **YES - E2B(R3) Requirements:**

1. **MedDRA PT (Preferred Term)**: 
   - ✅ **We HAVE this** - FAERS REAC file contains `pt` (MedDRA Preferred Term)
   - ⚠️ **Validation**: We don't validate against official MedDRA dictionary, but we have the PT values
   - **Solution**: Use PT as-is, add warning that validation recommended

2. **WHO Drug Coding**:
   - ❌ **Not required** - E2B(R3) allows free-text drug names
   - ✅ **We can use** `drugname` from FAERS DRUG file
   - **Solution**: Use drug name as-is, WHO Drug is optional enhancement

3. **MedDRA Version**:
   - ✅ **Required field** - Must specify version
   - **Solution**: Use default "27.0" (latest) or detect from FAERS metadata

### ⚠️ **Limitations Without Full Coding:**

- **Regulatory Acceptance**: Some regulators may require validated MedDRA/WHO Drug codes
- **Data Quality**: Free-text drug names may not match official dictionaries
- **Interoperability**: Other systems may expect coded values

### ✅ **What We CAN Do:**

1. Generate **structurally valid** E2B(R3) XML
2. Include **all mandatory fields** (with defaults where needed)
3. Use **FAERS PT values** (which are MedDRA Preferred Terms)
4. Use **free-text drug names** (allowed in E2B R3)
5. Add **warnings** about validation requirements

## Recommended Actions

### 1. **Enhance Data Loading** (High Priority)

Update `src/faers_loader.py` to include reporter and additional fields:

```python
# In load_faers_folder(), ensure these fields are preserved:
- rept_cod (reporter code)
- reporter_country
- rpsr_cod (report source)
- mfr_sndr (manufacturer sender)
- role_cod (drug role: PS, C, I, etc.)
- dose_amt, dose_unit (dosage)
- indi_pt (indication)
```

### 2. **Update E2B Export** (Medium Priority)

Enhance `src/e2b_export.py` to:
- Use reporter fields if available
- Add MedDRA version detection
- Add validation warnings
- Use drug role codes (PS=Primary Suspect, C=Concomitant, etc.)

### 3. **Add Validation Warnings** (Low Priority)

Display warnings in UI:
- "MedDRA PT values not validated against official dictionary"
- "WHO Drug coding not applied (optional)"
- "Reporter information may be incomplete"

## Current Implementation Status

✅ **Implemented:**
- Basic E2B(R3) XML generation
- Core patient, drug, reaction fields
- Seriousness and outcome mapping
- Date formatting

⚠️ **Needs Enhancement:**
- Reporter information (available in FAERS, not loaded)
- Drug role codes (available in FAERS, not loaded)
- Dosage information (available in FAERS, not loaded)
- Indication (available in FAERS, not loaded)

❌ **Not Available:**
- WHO Drug coding (optional, not in FAERS)
- Full MedDRA validation (have PT, but not validated)
- Reporter names (not in FAERS)

## Conclusion

**YES, we can generate E2B(R3) reports** with current data, but we should:
1. ✅ Load additional FAERS fields (reporter, role, dosage, indication)
2. ✅ Enhance E2B export to use these fields
3. ⚠️ Add warnings about validation requirements
4. ✅ Use defaults for sender/receiver (acceptable for exploratory use)

**For regulatory submission**, users should:
- Validate MedDRA PTs against official dictionary
- Consider WHO Drug coding for better interoperability
- Verify all reporter information is complete

