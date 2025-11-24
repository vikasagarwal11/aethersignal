# E2B(R3) DTD Setup Guide

## Where to Get the DTD File

The **ICH E2B(R3) DTD (Document Type Definition)** file is **publicly available** from:

### Official Sources:
1. **ICH Website**: https://www.ich.org/page/electronic-standards
   - Navigate to: ICH E2B(R3) Implementation Guide
   - Download: `E2B_R3.dtd` or `E2B_R3.xsd` (XML Schema Definition)

2. **FDA Website**: https://www.fda.gov/drugs/guidance-compliance-regulatory-information/electronic-submissions-gateway
   - FDA provides E2B(R3) implementation guides and DTD files

3. **EMA Website**: https://www.ema.europa.eu/en/human-regulatory/research-development/scientific-guidelines/ich-guidelines
   - EMA also provides E2B(R3) resources

### Current Implementation Status

✅ **E2B Export is Implemented** (`src/e2b_export.py`)
- Generates E2B(R3) XML structure
- Maps AetherSignal data to E2B fields
- Basic validation (structural checks)

⚠️ **Full DTD Validation Not Yet Integrated**
- Current validation is basic (structure only)
- For production use, integrate official DTD/XSD validation

## How to Add DTD Validation

### Option 1: Download DTD File Manually

1. Download `E2B_R3.dtd` from ICH website
2. Place it in `data/e2b/` directory
3. Update `src/e2b_export.py` to validate against DTD:

```python
from lxml import etree

def validate_e2b_with_dtd(xml_string: str, dtd_path: str) -> tuple[bool, List[str]]:
    """Validate E2B XML against official DTD."""
    try:
        # Parse XML
        xml_doc = etree.parse(BytesIO(xml_string.encode('utf-8')))
        
        # Load DTD
        dtd = etree.DTD(open(dtd_path))
        
        # Validate
        is_valid = dtd.validate(xml_doc)
        errors = [str(e) for e in dtd.error_log.filter_from_errors()]
        
        return is_valid, errors
    except Exception as e:
        return False, [str(e)]
```

### Option 2: Use XSD Schema (Recommended)

XSD (XML Schema Definition) is more modern and provides better validation:

1. Download `E2B_R3.xsd` from ICH website
2. Use `lxml` library for validation:

```python
from lxml import etree

def validate_e2b_with_xsd(xml_string: str, xsd_path: str) -> tuple[bool, List[str]]:
    """Validate E2B XML against official XSD schema."""
    try:
        # Parse XML
        xml_doc = etree.parse(BytesIO(xml_string.encode('utf-8')))
        
        # Load XSD schema
        xsd_doc = etree.parse(xsd_path)
        schema = etree.XMLSchema(xsd_doc)
        
        # Validate
        is_valid = schema.validate(xml_doc)
        errors = [str(e) for e in schema.error_log]
        
        return is_valid, errors
    except Exception as e:
        return False, [str(e)]
```

## Current E2B Implementation

The current implementation (`src/e2b_export.py`) generates E2B(R3) XML with:

✅ **Implemented:**
- Root structure (`ichicsr` element)
- Message header (version, type, format)
- Safety report structure
- Patient information (age, sex, weight)
- Reactions (MedDRA PT mapping)
- Drugs (medicinal products)
- Seriousness mapping
- Outcome mapping
- Dates (onset, report, receipt)
- Sender/Receiver information

⚠️ **Limitations:**
- Uses simplified field mappings
- Some optional E2B fields not populated
- DTD/XSD validation not integrated (basic validation only)
- MedDRA coding validation not performed

## Next Steps for Production Use

1. **Download Official DTD/XSD** from ICH website
2. **Add DTD/XSD validation** to `validate_e2b_xml()` function
3. **Enhance field mappings** for complete E2B compliance
4. **Add MedDRA validation** (verify PTs exist in official dictionary)
5. **Add WHO Drug validation** (if drug coding is required)
6. **Test with sample regulatory submissions**

## Testing

To test E2B export:
1. Run a query in AetherSignal
2. Go to "Cases" tab
3. Click "📋 Export as E2B(R3) XML"
4. Download and validate against official DTD/XSD

## Notes

- **For regulatory submissions**: Always validate against official DTD/XSD before submission
- **Current implementation**: Suitable for exploratory use and pilot testing
- **Production use**: Requires full DTD validation and enhanced field mapping

