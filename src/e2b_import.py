"""
E2B(R3) XML Import for AetherSignal
Parses ICH E2B(R3) XML files and converts to AetherSignal standard schema.

E2B(R3) is the ICH standard for electronic transmission of Individual Case Safety Reports (ICSRs).
Used by: Argus, EudraVigilance, VigiBase, and other regulatory systems.
"""

import pandas as pd
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import re
from datetime import datetime

# Try to import lxml for better XML parsing (optional, falls back to xml.etree)
try:
    from lxml import etree as lxml_etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

# E2B(R3) namespace (ICH standard)
E2B_NS = {
    'ich': 'urn:hl7-org:v3',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


def load_e2b_xml(file_path: str, progress_callback=None) -> Optional[pd.DataFrame]:
    """
    Load E2B(R3) XML file and convert to AetherSignal DataFrame.
    
    Args:
        file_path: Path to E2B XML file
        progress_callback: Optional callback function(step_name, progress_percent)
        
    Returns:
        DataFrame with E2B data mapped to AetherSignal schema, or None if parsing fails
    """
    if progress_callback:
        progress_callback("Reading E2B XML file...", 10)
    
    try:
        # Parse XML file
        if LXML_AVAILABLE:
            # Use lxml for better error handling and namespace support
            tree = lxml_etree.parse(file_path)
            root = tree.getroot()
        else:
            # Use built-in xml.etree
            tree = ET.parse(file_path)
            root = tree.getroot()
        
        if progress_callback:
            progress_callback("Parsing E2B structure...", 30)
        
        # Extract all ICSRs from the XML
        icsrs = _extract_icsrs(root)
        
        if not icsrs:
            return None
        
        if progress_callback:
            progress_callback(f"Found {len(icsrs)} ICSR(s), converting to DataFrame...", 60)
        
        # Convert ICSRs to DataFrame
        df = _icsrs_to_dataframe(icsrs)
        
        if progress_callback:
            progress_callback("E2B import complete!", 100)
        
        return df
        
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error parsing E2B XML: {str(e)}")


def _extract_icsrs(root: ET.Element) -> List[Dict[str, Any]]:
    """
    Extract all ICSRs from E2B XML root element.
    
    Args:
        root: XML root element
        
    Returns:
        List of ICSR dictionaries
    """
    icsrs = []
    
    # E2B can have multiple SafetyReport elements or a single one
    # Try to find SafetyReport elements (with or without namespace)
    safety_reports = []
    
    # Try with namespace first
    for ns_prefix, ns_uri in E2B_NS.items():
        safety_reports = root.findall(f'.//{{{ns_uri}}}SafetyReport')
        if safety_reports:
            break
    
    # If not found with namespace, try without
    if not safety_reports:
        safety_reports = root.findall('.//SafetyReport')
        if not safety_reports:
            # Maybe the root itself is a SafetyReport
            if root.tag.endswith('SafetyReport') or 'SafetyReport' in root.tag:
                safety_reports = [root]
    
    # If still not found, try alternative structure (some E2B files have different root)
    if not safety_reports:
        # Look for any element that might contain ICSR data
        for elem in root.iter():
            if 'safety' in elem.tag.lower() or 'icsr' in elem.tag.lower():
                safety_reports = [elem]
                break
    
    # If no SafetyReport found, assume the root contains one ICSR
    if not safety_reports:
        safety_reports = [root]
    
    # Extract each ICSR
    for safety_report in safety_reports:
        icsr_rows = _parse_safety_report(safety_report)
        if icsr_rows:
            # _parse_safety_report returns a list of rows (one per drug-reaction combination)
            icsrs.extend(icsr_rows)
    
    return icsrs


def _parse_safety_report(safety_report: ET.Element) -> List[Dict[str, Any]]:
    """
    Parse a single SafetyReport element into a list of dictionaries.
    Returns one row per drug-reaction combination (denormalized like FAERS).
    
    Args:
        safety_report: SafetyReport XML element
        
    Returns:
        List of dictionaries with ICSR data (one per drug-reaction combination)
    """
    icsr = {
        'source': 'E2B',
        'source_file': 'E2B_XML',
    }
    
    # Extract SafetyReportId (case identifier)
    safety_report_id = _find_element(safety_report, ['SafetyReportId', 'safetyreportid'])
    if safety_report_id is not None:
        icsr['caseid'] = _get_text(safety_report_id)
        icsr['primaryid'] = _get_text(safety_report_id)
        icsr['isr'] = _get_text(safety_report_id)
    
    # Extract PrimarySource (reporter information)
    primary_source = _find_element(safety_report, ['PrimarySource', 'primarysource'])
    if primary_source is not None:
        reporter_type = _find_element(primary_source, ['ReporterType', 'reportertype'])
        if reporter_type is not None:
            icsr['rpsr_cod'] = _get_text(reporter_type)
    
    # Extract Patient information
    patient = _find_element(safety_report, ['Patient', 'patient'])
    if patient is not None:
        # Age
        age = _find_element(patient, ['PatientAge', 'patientage', 'Age', 'age'])
        if age is not None:
            age_value = _find_element(age, ['AgeValue', 'agevalue', 'Value', 'value'])
            age_unit = _find_element(age, ['AgeUnit', 'ageunit', 'Unit', 'unit'])
            if age_value is not None:
                age_text = _get_text(age_value)
                # Convert to years if needed
                if age_unit is not None:
                    unit = _get_text(age_unit).lower()
                    if 'year' in unit or 'yr' in unit:
                        try:
                            icsr['age'] = float(age_text)
                            icsr['age_yrs'] = float(age_text)
                        except (ValueError, TypeError):
                            pass
                    elif 'month' in unit or 'mo' in unit:
                        try:
                            icsr['age'] = float(age_text) / 12.0
                            icsr['age_yrs'] = float(age_text) / 12.0
                        except (ValueError, TypeError):
                            pass
                else:
                    # Assume years if no unit specified
                    try:
                        icsr['age'] = float(age_text)
                        icsr['age_yrs'] = float(age_text)
                    except (ValueError, TypeError):
                        pass
        
        # Sex/Gender
        sex = _find_element(patient, ['PatientSex', 'patientsex', 'Sex', 'sex', 'Gender', 'gender'])
        if sex is not None:
            sex_text = _get_text(sex).upper()
            if 'M' in sex_text or 'MALE' in sex_text:
                icsr['sex'] = 'M'
                icsr['gender'] = 'M'
            elif 'F' in sex_text or 'FEMALE' in sex_text:
                icsr['sex'] = 'F'
                icsr['gender'] = 'F'
        
        # Weight
        weight = _find_element(patient, ['PatientWeight', 'patientweight', 'Weight', 'weight'])
        if weight is not None:
            weight_value = _find_element(weight, ['WeightValue', 'weightvalue', 'Value', 'value'])
            if weight_value is not None:
                try:
                    icsr['wt'] = float(_get_text(weight_value))
                except (ValueError, TypeError):
                    pass
    
    # Extract Reactions (Adverse Events)
    reactions = []
    reaction_elements = _find_elements(safety_report, ['Reaction', 'reaction', 'AdverseEvent', 'adverseevent'])
    for reaction_elem in reaction_elements:
        reaction_pt = _find_element(reaction_elem, ['ReactionMedDRA', 'reactionmeddra', 'MedDRA', 'meddra', 'PT', 'pt', 'PreferredTerm', 'preferredterm'])
        if reaction_pt is not None:
            pt_text = _get_text(reaction_pt)
            if pt_text:
                reactions.append(pt_text)
    
    # Extract Drugs (Medicinal Products)
    drugs = []
    drug_elements = _find_elements(safety_report, ['Drug', 'drug', 'MedicinalProduct', 'medicinalproduct'])
    for drug_elem in drug_elements:
        drug_name = _find_element(drug_elem, ['MedicinalProductName', 'medicinalproductname', 'Name', 'name', 'DrugName', 'drugname'])
        if drug_name is not None:
            drug_text = _get_text(drug_name)
            if drug_text:
                drugs.append(drug_text)
        
        # Drug role (suspect, concomitant, etc.)
        drug_role = _find_element(drug_elem, ['DrugCharacterization', 'drugcharacterization', 'Role', 'role'])
        if drug_role is not None:
            role_text = _get_text(drug_role)
            # Map to standard role codes if needed
            if 'suspect' in role_text.lower():
                icsr.setdefault('role_cod', '1')  # Suspect drug
    
    # Extract Seriousness
    seriousness = _find_element(safety_report, ['Seriousness', 'seriousness', 'Serious', 'serious'])
    if seriousness is not None:
        serious_text = _get_text(seriousness).upper()
        if 'Y' in serious_text or 'YES' in serious_text or '1' in serious_text:
            icsr['serious'] = True
            icsr['seriousness'] = 'Y'
        else:
            icsr['serious'] = False
            icsr['seriousness'] = 'N'
    
    # Extract Outcomes
    outcomes = []
    outcome_elements = _find_elements(safety_report, ['Outcome', 'outcome', 'PatientOutcome', 'patientoutcome'])
    for outcome_elem in outcome_elements:
        outcome_text = _get_text(outcome_elem)
        if outcome_text:
            outcomes.append(outcome_text)
    
    # Extract Dates
    # Event date
    event_date = _find_element(safety_report, ['EventDate', 'eventdate', 'OnsetDate', 'onsetdate', 'Onset', 'onset'])
    if event_date is not None:
        date_text = _get_text(event_date)
        icsr['event_date'] = _parse_date(date_text)
        icsr['onset_date'] = _parse_date(date_text)
    
    # Report date
    report_date = _find_element(safety_report, ['ReportDate', 'reportdate', 'ReceiveDate', 'receivedate'])
    if report_date is not None:
        date_text = _get_text(report_date)
        icsr['report_date'] = _parse_date(date_text)
        icsr['receive_date'] = _parse_date(date_text)
    
    # Extract Country
    country = _find_element(safety_report, ['Country', 'country', 'OccurrenceCountry', 'occurrencecountry'])
    if country is not None:
        icsr['country'] = _get_text(country)
    
    # Extract XEVMPD ID (for deduplication)
    xevmpd_id = _find_element(safety_report, ['XEVMPDId', 'xevmpdid', 'XEVMPD', 'xevmpd'])
    if xevmpd_id is not None:
        icsr['xevmpd_id'] = _get_text(xevmpd_id)
    
    # Create one row per drug-reaction combination (denormalized like FAERS)
    if not drugs:
        drugs = [None]  # At least one row even if no drug
    if not reactions:
        reactions = [None]  # At least one row even if no reaction
    
    # Return list of rows (one per drug-reaction combination)
    rows = []
    for drug in drugs:
        for reaction in reactions:
            row = icsr.copy()
            row['drug_name'] = drug
            row['reaction'] = reaction
            rows.append(row)
    
    # If no drug-reaction combinations, return at least one row
    if not rows:
        rows = [icsr]
    
    # Always return list of rows (for consistency)
    return rows


def _find_element(parent: ET.Element, tag_names: List[str]) -> Optional[ET.Element]:
    """
    Find an element by trying multiple possible tag names.
    
    Args:
        parent: Parent XML element
        tag_names: List of possible tag names to try
        
    Returns:
        Found element or None
    """
    for tag in tag_names:
        # Try with namespace
        for ns_prefix, ns_uri in E2B_NS.items():
            elem = parent.find(f'.//{{{ns_uri}}}{tag}')
            if elem is not None:
                return elem
        
        # Try without namespace
        elem = parent.find(f'.//{tag}')
        if elem is not None:
            return elem
        
        # Try case-insensitive search
        for child in parent.iter():
            if child.tag.lower() == tag.lower() or child.tag.endswith(tag):
                return child
    
    return None


def _find_elements(parent: ET.Element, tag_names: List[str]) -> List[ET.Element]:
    """
    Find all elements matching any of the tag names.
    
    Args:
        parent: Parent XML element
        tag_names: List of possible tag names to try
        
    Returns:
        List of found elements
    """
    elements = []
    found_tags = set()
    
    for tag in tag_names:
        # Try with namespace
        for ns_prefix, ns_uri in E2B_NS.items():
            found = parent.findall(f'.//{{{ns_uri}}}{tag}')
            for elem in found:
                if id(elem) not in found_tags:
                    elements.append(elem)
                    found_tags.add(id(elem))
        
        # Try without namespace
        found = parent.findall(f'.//{tag}')
        for elem in found:
            if id(elem) not in found_tags:
                elements.append(elem)
                found_tags.add(id(elem))
    
    return elements


def _get_text(element: ET.Element) -> str:
    """
    Get text content from an XML element.
    
    Args:
        element: XML element
        
    Returns:
        Text content (stripped)
    """
    if element is None:
        return ''
    
    # Get direct text
    text = element.text or ''
    
    # Also get text from child elements if no direct text
    if not text.strip():
        text = ''.join(element.itertext())
    
    return text.strip()


def _parse_date(date_str: str) -> Optional[str]:
    """
    Parse date string to standard format (YYYY-MM-DD).
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Date string in YYYY-MM-DD format or None
    """
    if not date_str:
        return None
    
    # Common date formats
    date_formats = [
        '%Y-%m-%d',
        '%Y%m%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y-%m',
        '%Y',
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            continue
    
    # Try to extract year-month-day from string
    numbers = re.findall(r'\d+', date_str)
    if len(numbers) >= 3:
        try:
            year = int(numbers[0])
            month = int(numbers[1])
            day = int(numbers[2])
            if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, TypeError):
            pass
    
    return date_str  # Return as-is if can't parse


def _icsrs_to_dataframe(icsrs: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert list of ICSR rows to DataFrame.
    
    Args:
        icsrs: List of ICSR dictionaries (already denormalized, one per drug-reaction)
        
    Returns:
        DataFrame with E2B data
    """
    rows = icsrs  # Already a list of dicts
    
    if not rows:
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Ensure required columns exist
    required_cols = ['caseid', 'primaryid', 'isr', 'drug_name', 'reaction']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    
    # Fill missing case IDs
    if 'caseid' in df.columns:
        df['caseid'] = df['caseid'].fillna(df.get('primaryid', None))
        df['caseid'] = df['caseid'].fillna(df.get('isr', None))
    
    # Count drugs and reactions per case
    if 'caseid' in df.columns:
        df['drug_count'] = df.groupby('caseid')['drug_name'].transform('count')
        df['reaction_count'] = df.groupby('caseid')['reaction'].transform('count')
    
    # Standardize column names to match FAERS format
    df.columns = df.columns.str.lower()
    
    return df


def detect_e2b_file(file_path: str) -> bool:
    """
    Detect if a file is an E2B(R3) XML file.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file appears to be E2B XML
    """
    try:
        # Check file extension
        if not file_path.lower().endswith('.xml'):
            return False
        
        # Try to parse and check for E2B structure
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Check for E2B indicators
        root_tag_lower = root.tag.lower()
        if 'safetyreport' in root_tag_lower or 'icsr' in root_tag_lower:
            return True
        
        # Check for E2B namespace
        if root.tag.startswith('{') and 'safety' in root_tag_lower:
            return True
        
        # Check for common E2B elements
        for elem in root.iter():
            if any(keyword in elem.tag.lower() for keyword in ['safety', 'icsr', 'adverseevent', 'medicinalproduct']):
                return True
        
        return False
        
    except Exception:
        return False

