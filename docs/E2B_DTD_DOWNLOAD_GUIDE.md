# E2B(R3) DTD/XSD Download Guide

## Automatic Download Status

❌ **Cannot download automatically** - ICH website requires manual navigation and may have access restrictions.

## Manual Download Steps (For You)

### Option 1: ICH Website (Recommended)

1. **Visit**: https://www.ich.org/page/electronic-standards
2. **Navigate to**: "E2B(R3) Implementation Guide" or "Electronic Standards for Transmission of Individual Case Safety Reports"
3. **Download**: 
   - `E2B_R3.dtd` (Document Type Definition)
   - `E2B_R3.xsd` (XML Schema Definition) - **Recommended**
   - Implementation Guide PDF

### Option 2: FDA Website

1. **Visit**: https://www.fda.gov/drugs/guidance-compliance-regulatory-information/electronic-submissions-gateway
2. **Search for**: "E2B(R3)" or "ICSR"
3. **Download**: DTD/XSD files from FDA resources

### Option 3: EMA Website

1. **Visit**: https://www.ema.europa.eu/en/human-regulatory/research-development/scientific-guidelines/ich-guidelines
2. **Search for**: "E2B(R3)" or "ICSR"
3. **Download**: DTD/XSD files from EMA resources

## After Download

### Where to Place Files

1. **Create directory**: `data/e2b/`
2. **Place files**:
   - `data/e2b/E2B_R3.xsd` (or `E2B_R3.dtd`)
   - `data/e2b/E2B_R3_Implementation_Guide.pdf` (optional)

### Integration Steps

Once you have the DTD/XSD file:

1. **Update `src/e2b_export.py`**:
   - Add DTD/XSD validation function
   - Use `lxml` library for validation

2. **Install required library**:
   ```bash
   pip install lxml
   ```

3. **Test validation**:
   - Generate E2B XML
   - Validate against DTD/XSD
   - Display validation errors if any

## Current Status

✅ **E2B Export Works** - Generates valid XML structure
⚠️ **DTD Validation Pending** - Needs manual download of DTD/XSD file
✅ **Basic Validation** - Structural checks implemented

## Alternative: Use Online Validators

If you can't download DTD/XSD:
- Use FDA's ICSR validation tools (online)
- Use EMA's validation services
- Use third-party E2B validators

## Next Steps

1. **You**: Download DTD/XSD from ICH/FDA/EMA
2. **You**: Place in `data/e2b/` directory
3. **Me**: Update code to use DTD/XSD for validation
4. **Test**: Validate generated E2B XML files

