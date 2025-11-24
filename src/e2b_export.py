"""
E2B(R3) XML Export for AetherSignal
Generates ICH E2B(R3) compliant XML files using official HL7 v3 structure.

Based on ICH E2B(R3) Implementation Guide v1.10
Official structure: MCCI_IN200100UV01 root with HL7 v3 namespace
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from io import BytesIO
import uuid


# ICH E2B(R3) HL7 v3 Namespace
HL7_NAMESPACE = "urn:hl7-org:v3"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

# ICH OIDs (Object Identifiers)
OID_BATCH_NUMBER = "2.16.840.1.113883.3.989.2.1.3.22"
OID_MESSAGE_ID = "2.16.840.1.113883.3.989.2.1.3.1"
OID_WORLDWIDE_CASE_ID = "2.16.840.1.113883.3.989.2.1.3.2"
OID_SENDER_ID = "2.16.840.1.113883.3.989.2.1.3.11"
OID_RECEIVER_ID = "2.16.840.1.113883.3.989.2.1.3.12"
OID_INTERACTION_ID = "2.16.840.1.113883.1.6"
OID_CODE_SYSTEMS = {
    "type_of_message": "2.16.840.1.113883.3.989.2.1.1.1",
    "observation_code": "2.16.840.1.113883.3.989.2.1.1.19",
    "organizer_code": "2.16.840.1.113883.3.989.2.1.1.20",
    "outcome_code": "2.16.840.1.113883.3.989.2.1.1.11",
    "drug_role": "2.16.840.1.113883.3.989.2.1.1.13",
    "route_code": "2.16.840.1.113883.3.989.2.1.1.14",
    "action_code": "2.16.840.1.113883.3.989.2.1.1.15",
    "indication_code": "2.16.840.1.113883.3.989.2.1.1.21",
    "source_code": "2.16.840.1.113883.3.989.2.1.1.22",
    "first_sender_code": "2.16.840.1.113883.3.989.2.1.1.3",
    "primary_source_code": "2.16.840.1.113883.3.989.2.1.1.22",
}
OID_MEDDRA = "2.16.840.1.113883.6.163"
OID_SEX_CODE = "1.0.5218"
OID_COUNTRY_CODE = "1.0.3166.1.2.2"
OID_TRIGGER_EVENT = "2.16.840.1.113883.1.18"
OID_ADVERSE_EVENT = "2.16.840.1.113883.5.4"

# MedDRA Version (default to latest)
MEDDRA_VERSION = "27.0"


def _register_namespaces():
    """Register namespaces for proper XML output."""
    ET.register_namespace("", HL7_NAMESPACE)
    ET.register_namespace("xsi", XSI_NAMESPACE)


def _safe_get_value(row: pd.Series, column: str, default: str = "") -> str:
    """Safely get value from DataFrame row, handling NaN and None."""
    if column not in row.index:
        return default
    value = row[column]
    if pd.isna(value) or value is None:
        return default
    return str(value).strip()


def _format_date_hl7(date_str: Any) -> str:
    """Format date to HL7 v3 format (YYYYMMDDHHMMSS or YYYYMMDD)."""
    if pd.isna(date_str) or date_str is None:
        return ""
    
    try:
        if isinstance(date_str, str):
            from src.utils import parse_date
            parsed = parse_date(date_str)
            if parsed:
                return parsed.strftime("%Y%m%d")
        elif isinstance(date_str, pd.Timestamp):
            return date_str.strftime("%Y%m%d")
        elif isinstance(date_str, datetime):
            return date_str.strftime("%Y%m%d")
    except Exception:
        pass
    
    return ""


def _map_sex_to_code(sex: Any) -> str:
    """Map sex to HL7 administrative gender code."""
    if pd.isna(sex) or sex is None:
        return ""
    
    sex_str = str(sex).upper().strip()
    if sex_str in ["M", "MALE", "1", "MALE"]:
        return "1"  # Male
    elif sex_str in ["F", "FEMALE", "2", "FEMALE"]:
        return "2"  # Female
    return ""


def _map_outcome_to_code(outcome: Any) -> str:
    """Map outcome to E2B outcome code."""
    if pd.isna(outcome) or outcome is None:
        return "3"  # Unknown
    
    outcome_str = str(outcome).lower().strip()
    if any(term in outcome_str for term in ['death', 'died', 'fatal', '1']):
        return "1"  # Fatal
    elif any(term in outcome_str for term in ['recovered', 'recovered/resolved', '2']):
        return "2"  # Recovered/Resolved
    elif any(term in outcome_str for term in ['recovering', 'recovering/resolving', '3']):
        return "3"  # Recovering/Resolving
    elif any(term in outcome_str for term in ['not recovered', 'not recovered/not resolved', '4']):
        return "4"  # Not Recovered/Not Resolved
    elif any(term in outcome_str for term in ['unknown', '5']):
        return "5"  # Unknown
    
    return "3"  # Default to Unknown


def _map_drug_role_to_code(role: Any) -> str:
    """Map drug role to E2B drug role code."""
    if pd.isna(role) or role is None:
        return "1"  # Suspect
    
    role_str = str(role).upper().strip()
    if role_str in ["PS", "PRIMARY SUSPECT", "1"]:
        return "1"  # Suspect
    elif role_str in ["C", "CONCOMITANT", "2"]:
        return "2"  # Concomitant
    elif role_str in ["I", "INTERACTING", "3"]:
        return "3"  # Interacting
    
    return "1"  # Default to Suspect


def _create_element(tag: str, parent: Optional[ET.Element] = None, **attrs) -> ET.Element:
    """Create an element with namespace."""
    elem = ET.Element(f"{{{HL7_NAMESPACE}}}{tag}")
    for key, value in attrs.items():
        if value is not None:
            elem.set(key, value)
    if parent is not None:
        parent.append(elem)
    return elem


def _create_patient_element(parent: ET.Element, row: pd.Series) -> None:
    """Create patient information in HL7 v3 structure."""
    # Patient (player1)
    player1 = _create_element("player1", parent, classCode="PSN", determinerCode="INSTANCE")
    _create_element("name", player1, nullFlavor="MSK")  # Masked for privacy
    
    # Sex
    sex_code = _map_sex_to_code(_safe_get_value(row, "sex", ""))
    if sex_code:
        _create_element("administrativeGenderCode", player1, code=sex_code, codeSystem=OID_SEX_CODE)
    
    # Birth date (if available, otherwise estimate from age)
    birth_date = _format_date_hl7(_safe_get_value(row, "birth_date", ""))
    if not birth_date:
        # Try to estimate from age
        age = _safe_get_value(row, "age", "")
        if age:
            try:
                from src.utils import extract_age
                age_num = extract_age(age)
                if age_num:
                    # Estimate birth year (rough approximation)
                    current_year = datetime.now().year
                    birth_year = current_year - int(age_num)
                    birth_date = f"{birth_year}0101"  # Jan 1 of estimated year
            except Exception:
                pass
    
    if birth_date:
        _create_element("birthTime", player1, value=birth_date)
    
    # Age at onset
    age = _safe_get_value(row, "age", "")
    if age:
        try:
            from src.utils import extract_age
            age_num = extract_age(age)
            if age_num:
                subject_of = _create_element("subjectOf2", parent, typeCode="SBJ")
                observation = _create_element("observation", subject_of, classCode="OBS", moodCode="EVN")
                _create_element("code", observation, code="3", codeSystem=OID_CODE_SYSTEMS["observation_code"])
                value_elem = _create_element("value", observation, value=str(int(age_num)), unit="a")
                value_elem.set(f"{{{XSI_NAMESPACE}}}type", "PQ")
        except Exception:
            pass
    
    # Weight
    weight = _safe_get_value(row, "weight", "")
    if weight:
        try:
            weight_num = float(weight)
            subject_of = _create_element("subjectOf2", parent, typeCode="SBJ")
            observation = _create_element("observation", subject_of, classCode="OBS", moodCode="EVN")
            _create_element("code", observation, code="7", codeSystem=OID_CODE_SYSTEMS["observation_code"])
            value_elem = _create_element("value", observation, value=str(weight_num), unit="kg")
            value_elem.set(f"{{{XSI_NAMESPACE}}}type", "PQ")
        except Exception:
            pass


def _create_reaction_element(parent: ET.Element, reaction: str, row: pd.Series, reaction_id: str) -> None:
    """Create reaction/adverse event element in HL7 v3 structure."""
    subject_of = _create_element("subjectOf2", parent, typeCode="SBJ")
    observation = _create_element("observation", subject_of, classCode="OBS", moodCode="EVN")
    observation.set(f"{{{XSI_NAMESPACE}}}type", "OBS")
    
    # Reaction ID
    _create_element("id", observation, root=reaction_id)
    
    # Reaction code (MedDRA PT)
    _create_element("code", observation, code="29", codeSystem=OID_CODE_SYSTEMS["observation_code"])
    
    # Event start date
    onset_date = _format_date_hl7(_safe_get_value(row, "onset_date", ""))
    effective_time = _create_element("effectiveTime", observation)
    effective_time.set(f"{{{XSI_NAMESPACE}}}type", "IVL_TS")
    if onset_date:
        _create_element("low", effective_time, value=onset_date)
    else:
        _create_element("low", effective_time, nullFlavor="ASKU")
    
    # Reaction value (MedDRA PT - using free text for now, should be MedDRA code)
    # Note: In production, this should map to actual MedDRA codes
    value_elem = _create_element("value", observation)
    value_elem.set(f"{{{XSI_NAMESPACE}}}type", "ST")
    value_elem.text = reaction[:200]
    
    # Outcome
    outcome_code = _map_outcome_to_code(_safe_get_value(row, "outcome", ""))
    outbound_rel = _create_element("outboundRelationship2", observation, typeCode="PERT")
    outcome_obs = _create_element("observation", outbound_rel, classCode="OBS", moodCode="EVN")
    _create_element("code", outcome_obs, code="27", codeSystem=OID_CODE_SYSTEMS["observation_code"])
    value_elem = _create_element("value", outcome_obs, code=outcome_code, codeSystem=OID_CODE_SYSTEMS["outcome_code"])
    value_elem.set(f"{{{XSI_NAMESPACE}}}type", "CE")
    
    # Seriousness criteria (if serious)
    seriousness = _safe_get_value(row, "seriousness", "")
    if seriousness and str(seriousness).lower() in ["1", "yes", "y", "true", "serious"]:
        # Death
        outbound_rel = _create_element("outboundRelationship2", observation, typeCode="PERT")
        death_obs = _create_element("observation", outbound_rel, classCode="OBS", moodCode="EVN")
        _create_element("code", death_obs, code="34", codeSystem=OID_CODE_SYSTEMS["observation_code"])
        death_value = "true" if outcome_code == "1" else "false"
        value_elem = _create_element("value", death_obs, value=death_value)
        value_elem.set(f"{{{XSI_NAMESPACE}}}type", "BL")
        
        # Other seriousness criteria (simplified - would need full mapping)
        for code, label in [("21", "Life Threatening"), ("33", "Hospitalization"), 
                           ("35", "Disabling"), ("12", "Congenital"), ("26", "Other Medically Important")]:
            outbound_rel = _create_element("outboundRelationship2", observation, typeCode="PERT")
            crit_obs = _create_element("observation", outbound_rel, classCode="OBS", moodCode="EVN")
            _create_element("code", crit_obs, code=code, codeSystem=OID_CODE_SYSTEMS["observation_code"])
            value_elem = _create_element("value", crit_obs, nullFlavor="NI")
            value_elem.set(f"{{{XSI_NAMESPACE}}}type", "BL")


def _create_drug_element(parent: ET.Element, drug: str, row: pd.Series, drug_seq: int, role_code: str = "1") -> None:
    """Create drug/substance administration element in HL7 v3 structure."""
    component = _create_element("component", parent, typeCode="COMP")
    substance_admin = _create_element("substanceAdministration", component, classCode="SBADM", moodCode="EVN")
    _create_element("id", substance_admin, root=str(uuid.uuid4()))
    
    # Consumable (medicinal product)
    consumable = _create_element("consumable", substance_admin, typeCode="CSM")
    instance_of = _create_element("instanceOfKind", consumable, classCode="INST")
    kind_of_product = _create_element("kindOfProduct", instance_of, classCode="MMAT", determinerCode="KIND")
    _create_element("name", kind_of_product).text = drug[:200]
    
    # Drug role (causality assessment)
    inbound_rel = _create_element("inboundRelationship", substance_admin, typeCode="CAUS")
    act = _create_element("act", inbound_rel, classCode="ACT", moodCode="EVN")
    _create_element("code", act, code=role_code, codeSystem=OID_CODE_SYSTEMS["drug_role"])
    
    # Indication (if available)
    indication = _safe_get_value(row, "indication", "")
    if indication:
        inbound_rel = _create_element("inboundRelationship", substance_admin, typeCode="RSON")
        indication_obs = _create_element("observation", inbound_rel, classCode="OBS", moodCode="EVN")
        _create_element("code", indication_obs, code="19", codeSystem=OID_CODE_SYSTEMS["observation_code"])
        # Note: Should use MedDRA code for indication
        value_elem = _create_element("value", indication_obs)
        value_elem.set(f"{{{XSI_NAMESPACE}}}type", "ST")
        value_elem.text = indication[:200]
    
    # Dosage (if available)
    dose_amt = _safe_get_value(row, "dose_amt", "")
    dose_unit = _safe_get_value(row, "dose_unit", "mg")
    if dose_amt:
        outbound_rel = _create_element("outboundRelationship2", substance_admin, typeCode="COMP")
        dose_admin = _create_element("substanceAdministration", outbound_rel, classCode="SBADM", moodCode="EVN")
        _create_element("doseQuantity", dose_admin, value=dose_amt, unit=dose_unit or "mg")


def _create_investigation_event(parent: ET.Element, row: pd.Series, case_id: str) -> None:
    """Create investigation event (the main case structure)."""
    subject = _create_element("subject", parent, typeCode="SUBJ")
    investigation_event = _create_element("investigationEvent", subject, classCode="INVSTG", moodCode="EVN")
    
    # Case identifiers
    _create_element("id", investigation_event, extension=case_id, root=OID_MESSAGE_ID)
    _create_element("id", investigation_event, extension=case_id, root=OID_WORLDWIDE_CASE_ID)
    
    # Event code
    _create_element("code", investigation_event, code="PAT_ADV_EVNT", codeSystem=OID_ADVERSE_EVENT)
    
    # Case narrative (simplified)
    narrative = f"Case {case_id}: Patient reported {_safe_get_value(row, 'reaction', 'adverse event')} after taking {_safe_get_value(row, 'drug_name', 'medication')}."
    _create_element("text", investigation_event).text = narrative
    
    # Status
    _create_element("statusCode", investigation_event, code="active")
    
    # Dates
    receipt_date = _format_date_hl7(_safe_get_value(row, "report_date", ""))
    if receipt_date:
        effective_time = _create_element("effectiveTime", investigation_event)
        _create_element("low", effective_time, value=receipt_date)
    
    availability_date = _format_date_hl7(_safe_get_value(row, "report_date", ""))
    if availability_date:
        _create_element("availabilityTime", investigation_event, value=availability_date)
    
    # Adverse event assessment component
    component = _create_element("component", investigation_event, typeCode="COMP")
    adverse_assessment = _create_element("adverseEventAssessment", component, classCode="INVSTG", moodCode="EVN")
    subject1 = _create_element("subject1", adverse_assessment, typeCode="SBJ")
    primary_role = _create_element("primaryRole", subject1, classCode="INVSBJ")
    
    # Patient information
    _create_patient_element(primary_role, row)
    
    # Reactions
    reaction_str = _safe_get_value(row, "reaction", "")
    if reaction_str:
        reaction_list = [r.strip() for r in reaction_str.split(";") if r.strip()]
        for i, reaction in enumerate(reaction_list):
            reaction_id = str(uuid.uuid4())
            _create_reaction_element(primary_role, reaction, row, reaction_id)
    
    # Drugs
    drug_str = _safe_get_value(row, "drug_name", "")
    if drug_str:
        drug_list = [d.strip() for d in drug_str.split(";") if d.strip()]
        # Create drug organizer
        subject_of = _create_element("subjectOf2", primary_role, typeCode="SBJ")
        organizer = _create_element("organizer", subject_of, classCode="CATEGORY", moodCode="EVN")
        _create_element("code", organizer, code="4", codeSystem=OID_CODE_SYSTEMS["organizer_code"])
        
        # Get drug role if available
        role_cod = _safe_get_value(row, "role_cod", "PS")
        
        for i, drug in enumerate(drug_list):
            role_code = _map_drug_role_to_code(role_cod if i == 0 else "C")  # First drug is suspect, others concomitant
            _create_drug_element(organizer, drug, row, i + 1, role_code)


def export_to_e2b(
    df: pd.DataFrame,
    output_format: str = "xml_string",
    sender_id: str = "AETHER",
    receiver_id: str = "REGULATORY"
) -> Union[str, bytes]:
    """
    Export DataFrame to E2B(R3) XML format using official ICH HL7 v3 structure.
    
    Args:
        df: DataFrame with case data (must have standard columns)
        output_format: "xml_string" (default) or "bytes" for file download
        sender_id: Sender identifier (default: "AETHER")
        receiver_id: Receiver identifier (default: "REGULATORY")
    
    Returns:
        E2B(R3) XML as string or bytes (HL7 v3 compliant)
    """
    if df.empty:
        return ""
    
    _register_namespaces()
    
    # Create root element: MCCI_IN200100UV01
    root = _create_element("MCCI_IN200100UV01")
    root.set("ITSVersion", "XML_1.0")
    root.set(f"{{{XSI_NAMESPACE}}}schemaLocation", 
             f"{HL7_NAMESPACE} MCCI_IN200100UV01.xsd")
    root.set("xmlns", HL7_NAMESPACE)
    root.set(f"xmlns:xsi", XSI_NAMESPACE)
    
    # Batch header
    batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    _create_element("id", root, extension=batch_id, root=OID_BATCH_NUMBER)
    _create_element("creationTime", root, value=datetime.now().strftime("%Y%m%d%H%M%S"))
    _create_element("responseModeCode", root, code="D")
    _create_element("interactionId", root, extension="MCCI_IN200100UV01", root=OID_INTERACTION_ID)
    _create_element("name", root, code="1", codeSystem=OID_CODE_SYSTEMS["type_of_message"])
    
    # Create PORR_IN049016UV message for each case
    for idx, row in df.iterrows():
        case_id = _safe_get_value(row, "caseid", "")
        primary_id = _safe_get_value(row, "primaryid", "")
        report_id = primary_id if primary_id else (case_id if case_id else f"ASR{idx+1:08d}")
        
        # Message wrapper
        porr_message = _create_element("PORR_IN049016UV", root)
        message_id = f"{sender_id}-{report_id}"
        _create_element("id", porr_message, extension=message_id, root=OID_MESSAGE_ID)
        _create_element("creationTime", porr_message, value=datetime.now().strftime("%Y%m%d%H%M%S"))
        _create_element("interactionId", porr_message, extension="PORR_IN049016UV", root=OID_INTERACTION_ID)
        _create_element("processingCode", porr_message, code="P")
        _create_element("processingModeCode", porr_message, code="T")
        _create_element("acceptAckCode", porr_message, code="AL")
        
        # Receiver
        receiver = _create_element("receiver", porr_message, typeCode="RCV")
        receiver_device = _create_element("device", receiver, classCode="DEV", determinerCode="INSTANCE")
        _create_element("id", receiver_device, extension=receiver_id, root=OID_RECEIVER_ID)
        
        # Sender
        sender = _create_element("sender", porr_message, typeCode="SND")
        sender_device = _create_element("device", sender, classCode="DEV", determinerCode="INSTANCE")
        _create_element("id", sender_device, extension=sender_id, root=OID_SENDER_ID)
        
        # Control act process
        control_act = _create_element("controlActProcess", porr_message, classCode="CACT", moodCode="EVN")
        _create_element("code", control_act, code="PORR_TE049016UV", codeSystem=OID_TRIGGER_EVENT)
        _create_element("effectiveTime", control_act, value=datetime.now().strftime("%Y%m%d%H%M%S"))
        
        # Investigation event (the actual case)
        _create_investigation_event(control_act, row, report_id)
    
    # Generate XML string
    ET.indent(root, space="  ")
    xml_string = ET.tostring(root, encoding="unicode", xml_declaration=True)
    
    if output_format == "bytes":
        return xml_string.encode("utf-8")
    else:
        return xml_string


def validate_e2b_xml(xml_string: str, xsd_path: Optional[str] = None) -> tuple[bool, List[str]]:
    """
    Validate E2B XML against structure and optionally XSD schema.
    
    Args:
        xml_string: E2B XML string to validate
        xsd_path: Optional path to XSD schema file for full validation
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        root = ET.fromstring(xml_string)
        
        # Check root element
        expected_root = f"{{{HL7_NAMESPACE}}}MCCI_IN200100UV01"
        if root.tag != expected_root:
            errors.append(f"Root element must be 'MCCI_IN200100UV01' (found: {root.tag})")
        
        # Check namespace
        if root.get("xmlns") != HL7_NAMESPACE:
            errors.append(f"Namespace must be '{HL7_NAMESPACE}'")
        
        # Check for PORR messages
        porr_messages = root.findall(f".//{{{HL7_NAMESPACE}}}PORR_IN049016UV")
        if len(porr_messages) == 0:
            errors.append("No PORR_IN049016UV messages found in XML")
        
        # Check for investigation events
        investigation_events = root.findall(f".//{{{HL7_NAMESPACE}}}investigationEvent")
        if len(investigation_events) == 0:
            errors.append("No investigation events found in XML")
        
        # XSD validation (if path provided)
        if xsd_path:
            try:
                from lxml import etree
                schema_doc = etree.parse(xsd_path)
                schema = etree.XMLSchema(schema_doc)
                xml_doc = etree.parse(BytesIO(xml_string.encode('utf-8')))
                if not schema.validate(xml_doc):
                    xsd_errors = [str(e) for e in schema.error_log]
                    errors.extend(xsd_errors)
            except ImportError:
                errors.append("lxml library required for XSD validation. Install: pip install lxml")
            except Exception as e:
                errors.append(f"XSD validation error: {str(e)}")
    
    except ET.ParseError as e:
        errors.append(f"XML parsing error: {str(e)}")
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
    
    return len(errors) == 0, errors
