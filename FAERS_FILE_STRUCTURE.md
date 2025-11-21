# FAERS File Structure Analysis

## Folder Structure

```
faers_ascii_2025q3/
├── ASCII/                          # Main data files folder
│   ├── DEMO25Q3.txt               # Demographics (base table)
│   ├── DRUG25Q3.txt               # Drug information
│   ├── REAC25Q3.txt               # Reactions/Adverse events
│   ├── INDI25Q3.txt               # Indications
│   ├── OUTC25Q3.txt               # Outcomes
│   ├── THER25Q3.txt               # Therapy dates
│   ├── RPSR25Q3.txt               # Report sources
│   ├── ASC_NTS.pdf                # Notes/documentation
│   └── [PDF files for each type]  # Documentation PDFs
├── Deleted/
│   └── DELETE25Q3.txt             # Deleted records
├── Readme.pdf                     # Documentation
└── FAQs.pdf                       # FAQs

```

## File Headers (Column Names)

### 1. DEMO25Q3.txt (Demographics - Base Table)
```
primaryid$caseid$caseversion$i_f_code$event_dt$mfr_dt$init_fda_dt$fda_dt$rept_cod$auth_num$mfr_num$mfr_sndr$lit_ref$age$age_cod$age_grp$sex$e_sub$wt$wt_cod$rept_dt$to_mfr$occp_cod$reporter_country$occr_country
```
- **Key columns:** `primaryid`, `caseid` (both available)
- **Demographics:** age, sex, country, dates, etc.

### 2. DRUG25Q3.txt (Drug Information)
```
primaryid$caseid$drug_seq$role_cod$drugname$prod_ai$val_vbm$route$dose_vbm$cum_dose_chr$cum_dose_unit$dechal$rechal$lot_num$exp_dt$nda_num$dose_amt$dose_unit$dose_form$dose_freq
```
- **Key columns:** `primaryid`, `caseid`
- **Sequence:** `drug_seq` (for counting)
- **Drug name:** `drugname`

### 3. REAC25Q3.txt (Reactions/Adverse Events)
```
primaryid$caseid$pt$drug_rec_act
```
- **Key columns:** `primaryid`, `caseid`
- **Reaction:** `pt` (Preferred Term)
- **No sequence column** - just count rows per case

### 4. INDI25Q3.txt (Indications)
```
primaryid$caseid$indi_drug_seq$indi_pt
```
- **Key columns:** `primaryid`, `caseid`
- **Sequence:** `indi_drug_seq` (different from `drug_seq`)
- **Indication:** `indi_pt`

### 5. OUTC25Q3.txt (Outcomes)
```
primaryid$caseid$outc_cod
```
- **Key columns:** `primaryid`, `caseid`
- **Outcome:** `outc_cod`

### 6. THER25Q3.txt (Therapy Dates)
```
primaryid$caseid$dsg_drug_seq$start_dt$end_dt$dur$dur_cod
```
- **Key columns:** `primaryid`, `caseid`
- **Sequence:** `dsg_drug_seq` (different from `drug_seq`)

### 7. RPSR25Q3.txt (Report Sources)
```
primaryid$caseid$rpsr_cod
```
- **Key columns:** `primaryid`, `caseid`
- **Report source:** `rpsr_cod`

## Key Findings

1. **Key Column:** All files use `primaryid` and/or `caseid` (NOT `ISR` - that's older format)
2. **Delimiter:** All files use `$` (dollar sign) delimiter
3. **Column Names:** Lowercase after normalization (e.g., `primaryid`, `caseid`, `drug_seq`)
4. **Sequence Columns:**
   - DRUG: `drug_seq` ✅
   - REAC: No sequence column (just count rows)
   - INDI: `indi_drug_seq` (different name)
   - THER: `dsg_drug_seq` (different name)

## Issues to Fix

1. **Key Column Detection:** Code looks for `ISR`, but files use `primaryid`/`caseid`
2. **REAC Aggregation:** Tries to use `drug_seq` which doesn't exist in REAC file
3. **Column Name Mapping:** Need to handle `primaryid` as well as `caseid`

