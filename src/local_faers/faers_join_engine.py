"""
FAERS Join Engine (CHUNK 7.8 - Part 4)
Performs joins between FAERS tables to create flattened case records.

This engine works with lightweight FaersTable models (list-of-dicts)
instead of pandas DataFrames for Pyodide/browser compatibility.
"""
from typing import Dict, List, Any, Optional
from collections import defaultdict
from .faers_models import FaersTable, FaersJoinedTable


class FaersJoinEngine:
    """
    Joins multiple FAERS tables into flattened case records.
    
    Handles:
    - DEMO (base) + DRUG → Cases with drug info
    - + REAC → Cases with reactions
    - + OUTC → Cases with outcomes
    - + THER → Cases with therapy dates
    - + INDI → Cases with indications
    
    Returns flattened case records ready for local processing.
    """
    
    def __init__(self, tables: Dict[str, FaersTable]):
        """
        Initialize join engine with loaded tables.
        
        Args:
            tables: Dictionary mapping table names to FaersTable instances
        """
        self.tables = tables
    
    def join(self) -> FaersJoinedTable:
        """
        Join all tables into flattened case records.
        
        Returns:
            FaersJoinedTable with joined/flattened cases
            
        Raises:
            ValueError: If DEMO table is missing
        """
        demo_table = self.tables.get("DEMO")
        
        if demo_table is None or len(demo_table) == 0:
            raise ValueError("DEMO table is required for joining")
        
        # Start with DEMO as base
        flattened_cases = []
        
        # Process each case in DEMO
        for demo_row in demo_table.rows:
            primaryid = demo_row.get("primaryid") or demo_row.get("PRIMARYID")
            caseid = demo_row.get("caseid") or demo_row.get("CASEID")
            
            if not primaryid:
                continue  # Skip rows without primary ID
            
            # Start with DEMO fields
            case_record = dict(demo_row)
            
            # Normalize primaryid/caseid keys (handle case variations)
            case_record["primaryid"] = str(primaryid)
            case_record["caseid"] = str(caseid) if caseid else ""
            
            # Join DRUG table (may have multiple drugs per case)
            drug_table = self.tables.get("DRUG")
            if drug_table:
                drugs = drug_table.get_rows_by_key("primaryid", primaryid)
                if drugs:
                    # Handle multiple drugs - create drug lists
                    drug_names = []
                    drug_seqs = []
                    drug_roles = []
                    
                    for drug_row in drugs:
                        drug_name = drug_row.get("drugname") or drug_row.get("DRUGNAME", "")
                        drug_seq = drug_row.get("drug_seq") or drug_row.get("DRUG_SEQ", "")
                        drug_role = drug_row.get("role_cod") or drug_row.get("ROLE_COD", "")
                        
                        if drug_name:
                            drug_names.append(str(drug_name))
                            drug_seqs.append(str(drug_seq))
                            drug_roles.append(str(drug_role))
                    
                    # Store as lists (or first drug if only one)
                    case_record["drug_name"] = drug_names[0] if drug_names else ""
                    case_record["drug_names"] = drug_names  # All drugs
                    case_record["drug_seq"] = drug_seqs[0] if drug_seqs else ""
                    case_record["drug_role"] = drug_roles[0] if drug_roles else ""
            
            # Join REAC table (may have multiple reactions per case)
            reac_table = self.tables.get("REAC")
            if reac_table:
                reactions = reac_table.get_rows_by_key("primaryid", primaryid)
                if reactions:
                    # Handle multiple reactions
                    reaction_pts = []
                    for reac_row in reactions:
                        pt = reac_row.get("pt") or reac_row.get("PT", "")
                        if pt:
                            reaction_pts.append(str(pt))
                    
                    # Store first reaction and all reactions
                    case_record["reaction"] = reaction_pts[0] if reaction_pts else ""
                    case_record["reactions"] = reaction_pts  # All reactions
                    case_record["reaction_count"] = len(reaction_pts)
            
            # Join OUTC table (may have multiple outcomes per case)
            outc_table = self.tables.get("OUTC")
            if outc_table:
                outcomes = outc_table.get_rows_by_key("primaryid", primaryid)
                if outcomes:
                    outcome_codes = []
                    for outc_row in outcomes:
                        outc_cod = outc_row.get("outc_cod") or outc_row.get("OUTC_COD", "")
                        if outc_cod:
                            outcome_codes.append(str(outc_cod))
                    
                    case_record["outcome"] = outcome_codes[0] if outcome_codes else ""
                    case_record["outcomes"] = outcome_codes
                    case_record["serious"] = any(
                        code in ["DE", "LT", "HO", "DS", "CA", "RI", "OT"]
                        for code in outcome_codes
                    )
            
            # Join THER table (therapy dates)
            ther_table = self.tables.get("THER")
            if ther_table:
                therapies = ther_table.get_rows_by_key("primaryid", primaryid)
                if therapies:
                    # Get first therapy date info
                    first_ther = therapies[0]
                    case_record["therapy_start_dt"] = first_ther.get("start_dt") or first_ther.get("START_DT", "")
                    case_record["therapy_end_dt"] = first_ther.get("end_dt") or first_ther.get("END_DT", "")
            
            # Join INDI table (indications)
            indi_table = self.tables.get("INDI")
            if indi_table:
                indications = indi_table.get_rows_by_key("primaryid", primaryid)
                if indications:
                    indi_pts = []
                    for indi_row in indications:
                        indi_pt = indi_row.get("indi_pt") or indi_row.get("INDI_PT", "")
                        if indi_pt:
                            indi_pts.append(str(indi_pt))
                    
                    case_record["indication"] = indi_pts[0] if indi_pts else ""
                    case_record["indications"] = indi_pts
            
            # Add case metadata
            case_record["_joined"] = True
            case_record["_join_timestamp"] = "2025-01-01"  # Placeholder
            
            flattened_cases.append(case_record)
        
        return FaersJoinedTable(rows=flattened_cases)
    
    def join_to_dataframe(self) -> Any:
        """
        Join tables and convert to pandas DataFrame (if pandas available).
        
        Returns:
            pandas DataFrame with joined cases, or list of dicts if pandas unavailable
        """
        joined_table = self.join()
        
        try:
            import pandas as pd
            return pd.DataFrame(joined_table.rows)
        except ImportError:
            # Return list of dicts if pandas not available
            return joined_table.rows

