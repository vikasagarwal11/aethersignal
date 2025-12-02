# 🎯 **PLACEHOLDER REPLACEMENT IMPLEMENTATION PLAN**

**Date:** Current  
**Status:** Ready for Implementation  
**Approach:** Replace ugly `(placeholder)` with real data OR clear "not connected" messages + input fields

---

## ✅ **AGREEMENT WITH ASSESSMENT**

**Yes, I completely agree with your assessment:**

- ✅ **We CAN fill ~60-70%** with real, data-backed content
- 🟡 **We CAN partially fill ~30-40%** with AI + manual input fields
- ❌ **We CANNOT fill ~3-4 sections** without external data (but can make them clean)

**Goal:** Eliminate ALL ugly `(placeholder)` text from user-visible outputs.

---

## 📋 **SECTION-BY-SECTION BREAKDOWN**

### **PSUR Generator (`src/reports/psur_generator.py`)**

#### **✅ [AUTO] - Can Fill Completely (8 sections)**

| Section | Current Placeholder | Data Source | Implementation |
|---------|-------------------|-------------|----------------|
| **Section 5: Summary of Signals** | Already working! | `data_sources["signals"]` | ✅ Already implemented |
| **Section 6: Benefit-Risk Narrative** | `"Benefit-risk assessment (placeholder - would use AI to generate narrative)"` | FAERS + Social + Lit + LLM | Use `medical_llm.py` + aggregate data |
| **Section 7: Conclusions** | `"Overall conclusions and recommendations (placeholder)"` | All analysis data + LLM | LLM synthesis from signals + trends |
| **Annex A: Line Listings** | `"Line listings (placeholder)"` | FAERS + Social cases | Query unified database, format as table |
| **Annex B: Summary Tabulations** | `"Summary tabulations (placeholder)"` | FAERS + Social data | Generate tables (by age, sex, country, seriousness) |
| **Annex C: Literature Reports** | `"Literature reports (placeholder)"` | PubMed citations | Query literature integration, format citations |
| **Signal Report: Trend Analysis** | `"Trend analysis (placeholder)"` | Time-series engine | Use `timeseries_engine.py` |
| **Signal Report: Severity Distribution** | `"Severity distribution (placeholder)"` | Case severity scores | Aggregate from unified data |

**Status:** ✅ **Ready to implement** - All data sources available

---

#### **🟡 [AUTO+MANUAL] - Can Fill Partially (4 sections)**

| Section | Current Placeholder | Data Available | Missing | Solution |
|---------|-------------------|----------------|---------|----------|
| **Section 2: Safety Actions** | `"Safety actions taken during reporting period (placeholder)"` | FDA MedWatch alerts | Complete company actions | Use alerts + LLM + manual input field |
| **Section 3: RMP Changes** | `"RMP changes during reporting period (placeholder)"` | None | Internal RMP data | LLM template + manual input field |
| **Section 4: Patient Exposure** | `"Patient exposure estimates (placeholder - would use prescription data)"` | Case counts | Prescription data | Use case counts as proxy + manual input field |
| **DSUR Section 3: Safety Info** | `"Safety information from clinical trials and real-world data (placeholder)"` | FAERS + Social + Lit | Internal trial SAE data | Use available data + LLM + note about limitations |

**Status:** 🟡 **Ready to implement** - Will use data + LLM + input fields

---

#### **🔴 [MANUAL] - Cannot Fill Without External Data (4 sections)**

| Section | Current Placeholder | What's Needed | Solution |
|---------|-------------------|---------------|----------|
| **Section 1: Marketing Authorization** | `"Marketing authorization status for {drug} (placeholder - would query regulatory databases)"` | FDA/EMA/MHRA APIs or company data | Replace with: Clear message + structured input fields |
| **Annex D: Exposure Tables** | `"Exposure tables (placeholder)"` | Prescription sales data (IQVIA, Symphony) | Replace with: Clear message + optional manual input |
| **DSUR Section 2: Development Status** | `"Clinical development status (placeholder)"` | Complete clinical trial timeline | Replace with: ClinicalTrials.gov data + LLM + manual input |
| **DSUR Section 4: Risk Summary** | `"Summary of identified risks during reporting period (placeholder)"` | Complete risk assessment | Replace with: Signals data + LLM + note about limitations |

**Status:** 🔴 **Ready to implement** - Will replace with clean UI + input fields

---

### **DSUR Generator (`src/reports/psur_generator.py`)**

#### **✅ [AUTO] - Can Fill Completely (1 section)**

| Section | Current Placeholder | Data Source | Implementation |
|---------|-------------------|-------------|----------------|
| **Section 5: Benefit-Risk** | `"Benefit-risk assessment (placeholder)"` | AE data + LLM | Use `medical_llm.py` + aggregate data |

#### **🟡 [AUTO+MANUAL] - Can Fill Partially (2 sections)**

| Section | Current Placeholder | Data Available | Solution |
|---------|-------------------|----------------|----------|
| **Section 3: Safety Information** | `"Safety information from clinical trials and real-world data (placeholder)"` | FAERS + Social + Lit | Use available data + LLM + note |
| **Section 4: Risk Summary** | `"Summary of identified risks during reporting period (placeholder)"` | Signals + LLM | Use signals + LLM + note |

---

### **Signal Report Generator (`src/reports/psur_generator.py`)**

#### **✅ [AUTO] - Can Fill Completely (1 section)**

| Section | Current Placeholder | Data Source | Implementation |
|---------|-------------------|-------------|----------------|
| **Conclusions** | `"Signal evaluation conclusions (placeholder - would use AI to generate)"` | Signal data + LLM | Use `medical_llm.py` + signal analysis |

---

## 🎯 **IMPLEMENTATION PRIORITY**

### **Phase 1: Kill Ugly Placeholders (High Priority)**

Replace ALL `(placeholder)` text with:
- Real data-backed content (where possible)
- Clear "not connected" messages + input fields (where not possible)

**Sections:**
1. Section 1: Marketing Authorization → Clear message + input fields
2. Section 2: Safety Actions → FDA alerts + LLM + input fields
3. Section 3: RMP Changes → LLM template + input fields
4. Section 4: Exposure → Case counts + LLM + input fields
5. Section 6: Benefit-Risk → LLM + data
6. Section 7: Conclusions → LLM + data
7. Annex A: Line Listings → Query database
8. Annex B: Tabulations → Generate tables
9. Annex C: Literature → Query PubMed
10. Annex D: Exposure Tables → Clear message + input fields
11. Signal Report: Trend Analysis → Use trend engine
12. Signal Report: Severity Distribution → Aggregate data
13. Signal Report: Conclusions → LLM + data

---

### **Phase 2: Maximize Data-Backed Sections (Medium Priority)**

Wire up all data sources to generate rich content:
- Trend analysis from time-series engine
- Severity distribution from case data
- Top signal summaries from quantum engine
- Line listings from unified database
- Summary tables with proper formatting
- Literature citations with proper formatting

---

### **Phase 3: Add Configurable Fields (Low Priority)**

Add admin/config fields for:
- MA status summary (YAML or admin panel)
- Safety actions (manual input)
- Exposure estimates (optional manual input)
- Clinical dev status (optional manual input)

---

## 🔧 **IMPLEMENTATION APPROACH**

### **For [AUTO] Sections:**

1. Query data from unified database
2. Format as tables/text
3. Use LLM for narrative generation
4. Replace placeholder text with real content

### **For [AUTO+MANUAL] Sections:**

1. Query available data
2. Use LLM to generate narrative from available data
3. Add clear note about limitations
4. Add manual input fields for missing data
5. Replace placeholder with: Generated content + input fields

### **For [MANUAL] Sections:**

1. Replace placeholder with professional message:
   ```
   **Marketing Authorization Status**
   
   *(No marketing authorization data connected. Please enter key information below or connect your regulatory system.)*
   
   [Input fields for: Country, Date, Indication, etc.]
   ```
2. Add structured input fields
3. Save user input to report

---

## 📊 **SUMMARY**

| Category | Count | Percentage | Status |
|----------|-------|------------|--------|
| ✅ [AUTO] - Can Fill Completely | 10 | ~60% | Ready to implement |
| 🟡 [AUTO+MANUAL] - Can Fill Partially | 6 | ~35% | Ready to implement |
| 🔴 [MANUAL] - Need External Data | 4 | ~5% | Ready to implement (clean UI) |
| **Total** | **20** | **100%** | **All ready** |

---

## ✅ **NEXT STEPS**

1. **Replace ALL placeholders** with either:
   - Real data-backed content, OR
   - Clear "not connected" messages + input fields

2. **No ugly `(placeholder)` text** anywhere in user-visible outputs

3. **Professional, honest messaging** about what's available vs what's missing

---

**Ready to proceed with implementation?** 🚀

