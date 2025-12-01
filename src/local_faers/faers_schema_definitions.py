"""
FAERS Schema Definitions (CHUNK 7.8 - Part 1)
Defines required columns for each FAERS file type.

Ensures browser-side loaders know what to expect and prevents
corrupted files from crashing the join engine.
"""

FAERS_REQUIRED_SCHEMAS = {
    "DEMO": [
        "primaryid",
        "caseid",
        "caseversion",
        "sex",
        "age",
        "age_cod",
        "wt",
        "wt_cod",
        "e_sub",
        "init_fda_dt",
        "fda_dt",
        "occp_cod",
        "reporter_country"
    ],
    "DRUG": [
        "primaryid",
        "caseid",
        "caseversion",
        "drug_seq",
        "role_cod",
        "drugname",
        "prod_ai",
        "val_vbm",
        "route",
        "dose_amt",
        "dose_unit",
        "dose_form",
        "dose_freq"
    ],
    "REAC": [
        "primaryid",
        "caseid",
        "pt"
    ],
    "OUTC": [
        "primaryid",
        "caseid",
        "outc_cod"
    ],
    "RPSR": [
        "primaryid",
        "caseid",
        "rpsr_cod"
    ],
    "THER": [
        "primaryid",
        "caseid",
        "start_dt",
        "end_dt"
    ],
    "INDI": [
        "primaryid",
        "caseid",
        "indi_pt"
    ]
}

# Optional columns (nice to have but not required)
FAERS_OPTIONAL_COLUMNS = {
    "DEMO": ["age_yrs", "wt_kg", "event_dt", "init_fda_dt"],
    "DRUG": ["drug_char", "drug_dosage_text"],
    "REAC": ["drug_rec_act"],
    "OUTC": ["outc_dt"],
    "THER": ["duration", "duration_unit"],
    "INDI": ["indi_drug_seq"]
}

