"""
FAERS Case Object Builder (CHUNK 7.8 Part 3)
Builds standardized FAERS case objects from indexed data.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from .faers_index_builder import LocalFAERSIndex
from .seriousness_classifier import SeriousnessClassifier


class FAERSCaseBuilder:
    """
    Builds standardized FAERS case objects from indexed tables.
    
    Creates clean, harmonized case records ready for analysis.
    """
    
    def __init__(self, index: LocalFAERSIndex):
        """
        Initialize case builder with index.
        
        Args:
            index: Built FAERS index
        """
        self.index = index
        self.classifier = SeriousnessClassifier()
    
    def build_case(self, primaryid: str) -> Optional[Dict[str, Any]]:
        """
        Build a complete FAERS case object from indexed data.
        
        Args:
            primaryid: Primary ID of the case
            
        Returns:
            Complete case object or None if not found
        """
        # Get DEMO record
        demo = self.index.get_demo(primaryid)
        if not demo:
            return None
        
        # Start with DEMO as base
        case = {
            "case_id": primaryid,
            "primaryid": primaryid,
        }
        
        # Add demographics
        case.update({
            "age": self._extract_age(demo),
            "age_cod": demo.get("age_cod") or demo.get("AGE_COD"),
            "sex": demo.get("sex") or demo.get("SEX"),
            "weight": self._extract_weight(demo),
            "weight_cod": demo.get("wt_cod") or demo.get("WT_COD"),
            "country": demo.get("occr_country") or demo.get("OCCR_COUNTRY"),
            "report_date": self._extract_date(demo.get("fda_dt") or demo.get("FDA_DT")),
            "init_date": self._extract_date(demo.get("init_fda_dt") or demo.get("INIT_FDA_DT")),
        })
        
        # Add drugs
        drugs = self.index.get_drugs(primaryid)
        case["drugs"] = [self._normalize_drug(d) for d in drugs]
        case["drug_count"] = len(drugs)
        if drugs:
            case["primary_drug"] = drugs[0].get("drugname") or drugs[0].get("DRUGNAME")
        
        # Add reactions
        reactions = self.index.get_reactions(primaryid)
        case["reactions"] = [self._normalize_reaction(r) for r in reactions]
        case["reaction_count"] = len(reactions)
        if reactions:
            case["primary_reaction"] = reactions[0].get("pt") or reactions[0].get("PT")
        
        # Add outcomes
        outcomes = self.index.get_outcomes(primaryid)
        outcome_codes = [o.get("outc_cod") or o.get("OUTC_COD") for o in outcomes if o.get("outc_cod") or o.get("OUTC_COD")]
        case["outcomes"] = outcome_codes
        case["outcome_count"] = len(outcome_codes)
        
        # Add therapy dates
        therapies = self.index.get_therapies(primaryid)
        if therapies:
            first_ther = therapies[0]
            case["therapy_start"] = self._extract_date(first_ther.get("start_dt") or first_ther.get("START_DT"))
            case["therapy_end"] = self._extract_date(first_ther.get("end_dt") or first_ther.get("END_DT"))
        
        # Add indications
        indications = self.index.get_indications(primaryid)
        indi_pts = [i.get("indi_pt") or i.get("INDI_PT") for i in indications if i.get("indi_pt") or i.get("INDI_PT")]
        case["indications"] = indi_pts
        case["indication_count"] = len(indi_pts)
        
        # Classify seriousness
        seriousness = self.classifier.classify(case)
        case.update(seriousness)
        
        # Add metadata
        case["_built_timestamp"] = datetime.now().isoformat()
        case["_source"] = "local_faers_engine"
        
        return case
    
    def build_all_cases(self) -> List[Dict[str, Any]]:
        """
        Build all cases from indexed data.
        
        Returns:
            List of all case objects
        """
        cases = []
        for primaryid in self.index.demo_index.keys():
            case = self.build_case(primaryid)
            if case:
                cases.append(case)
        return cases
    
    def _extract_age(self, demo: Dict[str, Any]) -> Optional[float]:
        """Extract age as float."""
        age = demo.get("age") or demo.get("AGE")
        if age:
            try:
                return float(str(age).strip())
            except (ValueError, TypeError):
                pass
        return None
    
    def _extract_weight(self, demo: Dict[str, Any]) -> Optional[float]:
        """Extract weight as float."""
        weight = demo.get("wt") or demo.get("WT") or demo.get("weight") or demo.get("WEIGHT")
        if weight:
            try:
                return float(str(weight).strip())
            except (ValueError, TypeError):
                pass
        return None
    
    def _extract_date(self, date_val: Any) -> Optional[str]:
        """Extract and normalize date."""
        if not date_val:
            return None
        
        date_str = str(date_val).strip()
        if not date_str or date_str.upper() in ["", "NONE", "NULL", "NA"]:
            return None
        
        return date_str
    
    def _normalize_drug(self, drug_row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize drug record."""
        return {
            "drug_name": drug_row.get("drugname") or drug_row.get("DRUGNAME") or "",
            "drug_seq": drug_row.get("drug_seq") or drug_row.get("DRUG_SEQ"),
            "role": drug_row.get("role_cod") or drug_row.get("ROLE_COD"),
            "route": drug_row.get("route") or drug_row.get("ROUTE"),
            "dose": drug_row.get("dose_amt") or drug_row.get("DOSE_AMT"),
            "dose_unit": drug_row.get("dose_unit") or drug_row.get("DOSE_UNIT"),
        }
    
    def _normalize_reaction(self, reac_row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize reaction record."""
        return {
            "reaction_pt": reac_row.get("pt") or reac_row.get("PT") or "",
            "reaction_soc": reac_row.get("soc") or reac_row.get("SOC"),
        }

