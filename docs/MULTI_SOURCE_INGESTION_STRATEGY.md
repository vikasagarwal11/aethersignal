# Multi-Source Signal Detection Strategy - AetherSignal

## Overview

This document outlines the strategy for building AetherSignal as a low-cost SaaS alternative to Oracle Empirica Signal, focusing on **multi-source harmonization** and **complete coverage** of global ICSRs.

## Current Implementation Status

### ✅ Implemented (v1)

1. **FAERS Ingestion** (`src/faers_loader.py`)
   - ✅ ASCII file parsing (DEMO, DRUG, REAC, OUTC, THER, INDI, RPSR)
   - ✅ Automatic schema detection
   - ✅ Case joining on primaryid/caseid
   - ✅ Fixed-width and delimited format support
   - ✅ PDF extraction (basic)
   - **Status:** Production-ready

2. **Flexible Schema Mapping** (`src/pv_schema.py`)
   - ✅ Fuzzy column matching
   - ✅ Vendor-agnostic (works with any format)
   - ✅ Manual mapping UI
   - **Status:** Production-ready

3. **Multi-Format Support**
   - ✅ CSV, Excel, ZIP archives
   - ✅ Text files
   - ✅ PDF files (basic)
   - **Status:** Production-ready

### ⚠️ Partially Implemented

1. **E2B(R3) XML Support** (`src/e2b_export.py`)
   - ✅ Export to E2B format
   - ❌ Import from E2B format (needed for Argus/EudraVigilance)
   - **Status:** Export only, import needed

### ❌ Not Yet Implemented

1. **Argus Safety Exports**
   - ❌ E2B XML import
   - ❌ Argus Interchange format
   - ❌ Argus Mart schema replication

2. **EudraVigilance (EMA)**
   - ❌ EVDAS API integration
   - ❌ E2B XML parsing
   - ❌ XEVMPD ID deduplication

3. **VigiBase (WHO)**
   - ❌ UMC API integration
   - ❌ WHODrug Global code mapping
   - ❌ Subscription management

4. **VAERS (Vaccines)**
   - ❌ VAERS-specific ETL
   - ❌ Vaccine code mapping

5. **PMDA JADER (Japan)**
   - ❌ JADER CSV parsing
   - ❌ JART code mapping

6. **OMOP CDM Harmonization**
   - ❌ OHDSI OMOP CDM schema
   - ❌ RxNorm/ATC drug mapping
   - ❌ Unified data mart

7. **Automated ETL Pipeline**
   - ❌ Apache Airflow orchestration
   - ❌ Scheduled data pulls
   - ❌ Incremental updates

## Recommended Implementation Roadmap

### Phase 1: Enhanced FAERS + Argus Support (3-6 months) ⭐ **HIGHEST PRIORITY**

**Goal:** Support the two most common sources (FAERS + Argus exports)

#### 1.1 E2B(R3) XML Import (`src/e2b_import.py`) - NEW

**Features:**
- Parse E2B(R3) XML files
- Extract ICSR data (drugs, reactions, demographics, dates)
- Map to standard AetherSignal schema
- Handle multiple ICSRs per file
- Support both full E2B and summary formats

**Implementation:**
```python
def parse_e2b_xml(file_path: str) -> pd.DataFrame:
    """
    Parse E2B(R3) XML file and convert to AetherSignal format.
    
    Handles:
    - SafetyReport elements
    - Drug information (substance, dosage, route)
    - Reaction information (preferred terms)
    - Patient demographics
    - Dates (onset, report, receipt)
    """
    # Use lxml or xml.etree.ElementTree
    # Map E2B fields to standard schema
    # Return normalized DataFrame
```

**Files to Create:**
- `src/e2b_import.py` - E2B XML parser
- `src/mapping_templates.py` - E2B → AetherSignal mapping (enhance existing)

**Dependencies:**
- `lxml` or `xml.etree.ElementTree`
- `pandas`

#### 1.2 Argus Interchange Format Support

**Features:**
- Parse Argus export files (CSV/SQL dumps)
- Handle Argus Mart views
- Map Argus-specific fields to standard schema
- Support both ICSR-level and aggregated exports

**Implementation:**
- Extend `src/faers_loader.py` or create `src/argus_loader.py`
- Use existing schema mapping infrastructure
- Add Argus-specific field mappings

#### 1.3 Enhanced Deduplication

**Features:**
- Cross-source deduplication (FAERS + Argus)
- Fuzzy matching on case identifiers
- Age/sex/event-based matching
- ML-based duplicate detection (RecordLinkage)

**Implementation:**
- Enhance `src/quantum_duplicate_detection.py`
- Add cross-source matching logic
- Use existing quantum-inspired algorithms

### Phase 2: EudraVigilance + VigiBase Integration (6-9 months)

#### 2.1 EudraVigilance API Integration

**Features:**
- EVDAS API client
- SOAP/XML parsing
- XEVMPD ID extraction
- ISO 11238 substance ID mapping
- MedDRA/ATC code mapping

**Implementation:**
- Create `src/eudravigilance_client.py`
- Use `requests` for API calls
- Reuse E2B import logic

#### 2.2 VigiBase Integration

**Features:**
- UMC API client
- WHODrug Global code mapping
- Subscription management
- Monthly data pulls

**Implementation:**
- Create `src/vigibase_client.py`
- Map WHODrug to ATC/RxNorm
- Handle subscription authentication

### Phase 3: OMOP CDM Harmonization (9-12 months)

#### 3.1 OHDSI OMOP CDM Schema

**Features:**
- Convert all sources to OMOP CDM format
- Unified drug mapping (RxNorm, ATC)
- Unified reaction mapping (MedDRA)
- Star schema for analytics

**Implementation:**
- Create `src/omop_cdm_converter.py`
- Use OHDSI tools (if available)
- Map all sources to common schema

#### 3.2 Automated ETL Pipeline

**Features:**
- Apache Airflow orchestration
- Scheduled data pulls
- Incremental updates
- Error handling and retries
- Data quality checks

**Implementation:**
- Create `etl/` directory
- Airflow DAGs for each source
- Use existing loaders as tasks

### Phase 4: Additional Sources (12+ months)

- VAERS integration
- PMDA JADER integration
- Clinical trials data
- Literature integration (already partially implemented)
- EHR/Claims data (via OMOP networks)

## Technical Architecture

### Data Flow

```
Source Files (FAERS/Argus/E2B/etc.)
    ↓
ETL Pipeline (Airflow)
    ↓
Schema Detection & Mapping
    ↓
Normalization (drug/reaction mapping)
    ↓
OMOP CDM (optional, for multi-source)
    ↓
Unified Data Mart
    ↓
AetherSignal Analysis Engine
    ↓
Results & Reports
```

### Key Components

1. **Ingestion Layer**
   - `src/faers_loader.py` (existing)
   - `src/e2b_import.py` (new)
   - `src/argus_loader.py` (new)
   - `src/eudravigilance_client.py` (new)
   - `src/vigibase_client.py` (new)

2. **Mapping Layer**
   - `src/pv_schema.py` (existing, enhance)
   - `src/mapping_templates.py` (existing, enhance)
   - `src/drug_name_normalization.py` (existing)
   - `src/utils.py` (MedDRA mapping, existing)

3. **Harmonization Layer**
   - `src/omop_cdm_converter.py` (new)
   - Drug mapping: RxNorm, ATC
   - Reaction mapping: MedDRA
   - Date standardization

4. **Storage Layer**
   - Unified data mart (PostgreSQL/Parquet)
   - Incremental updates
   - Data versioning

5. **Analysis Layer**
   - Existing signal detection (`src/signal_stats.py`)
   - Existing quantum ranking (`src/quantum_ranking.py`)
   - Multi-source signal aggregation

## Cost Optimization Strategy

### Current Costs
- FAERS: Free (public data)
- Processing: <$0.01 per 1K ICSRs (AWS Lambda/S3)

### Target Costs (per source)
- FAERS: Free
- Argus exports: $0.01 per 1K ICSRs (customer upload)
- EudraVigilance: API costs (customer subscription)
- VigiBase: API costs (customer subscription)

### SaaS Pricing Model
- **Tier 1 (Startup):** $10K/year - FAERS + 1 custom source, unlimited runs
- **Tier 2 (Mid-size):** $50K/year - All sources, unlimited runs, priority support
- **Tier 3 (Enterprise):** $100K/year - All sources, dedicated instance, custom integrations

## Competitive Advantages

1. **Cost:** 60-80% cheaper than Oracle Empirica
2. **Speed:** Hours vs. weeks for signal detection
3. **Flexibility:** No vendor lock-in, open-source algorithms
4. **Multi-source:** Native support for all major sources
5. **AI-enhanced:** LLM-powered insights (recently implemented)
6. **Quantum-inspired:** Advanced ranking algorithms

## Next Steps

### Immediate (Week 1-2)
1. ✅ Implement missing NLP features (comparison intent, trend intent, enhanced severity)
2. Create `src/e2b_import.py` for E2B XML import
3. Test with sample Argus E2B exports

### Short-term (Month 1-3)
1. Enhance schema mapping for Argus formats
2. Implement cross-source deduplication
3. Add OMOP CDM converter (basic)

### Medium-term (Month 3-6)
1. EudraVigilance API integration
2. VigiBase API integration
3. Automated ETL pipeline (Airflow)

### Long-term (Month 6-12)
1. Additional sources (VAERS, JADER)
2. Advanced harmonization
3. Real-time data streaming

## Dependencies to Add

```python
# requirements.txt additions
lxml>=4.9.0  # For E2B XML parsing
apache-airflow>=2.7.0  # For ETL orchestration (optional)
ohdsi-tools  # For OMOP CDM (if available)
recordlinkage>=0.16.0  # For advanced deduplication
```

## Testing Strategy

1. **Unit Tests:** Each loader module
2. **Integration Tests:** End-to-end ETL pipeline
3. **Data Quality Tests:** Schema validation, completeness checks
4. **Performance Tests:** Large file handling, incremental updates

---

**Last Updated:** January 2025  
**Status:** Strategy document - Implementation roadmap

