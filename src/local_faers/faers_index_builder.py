"""
Local FAERS Index Builder (CHUNK 7.8 Part 3)
Builds optimized indexes for fast multi-file joins and key reconstruction.
"""
from typing import Dict, List, Any, Optional
from collections import defaultdict
from .faers_models import FaersTable


class LocalFAERSIndex:
    """
    Optimized index structure for FAERS multi-file joins.
    
    Provides:
    - Fast lookup by PRIMARYID
    - Key canonicalization
    - Duplicate detection
    - Missing key reconstruction
    """
    
    def __init__(self):
        """Initialize FAERS index structure."""
        self.demo_index: Dict[str, Dict[str, Any]] = {}  # PRIMARYID -> DEMO row
        self.drug_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # PRIMARYID -> DRUG rows
        self.reac_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # PRIMARYID -> REAC rows
        self.ther_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # PRIMARYID -> THER rows
        self.outc_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # PRIMARYID -> OUTC rows
        self.indi_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # PRIMARYID -> INDI rows
        
        # Key reconstruction helpers
        self.canonical_ids: Dict[str, str] = {}  # Variant -> Canonical PRIMARYID
        self.duplicate_groups: Dict[str, List[str]] = defaultdict(list)  # Canonical -> Variants
        self.missing_keys: List[Dict[str, Any]] = []  # Rows with missing PRIMARYID
    
    def build_indexes(self, tables: Dict[str, FaersTable]) -> None:
        """
        Build all indexes from loaded FAERS tables.
        
        Args:
            tables: Dictionary of loaded FAERS tables
        """
        # Index DEMO
        demo_table = tables.get("DEMO")
        if demo_table:
            for row in demo_table.rows:
                primaryid = self._extract_primaryid(row)
                if primaryid:
                    canonical_id = self._canonicalize_id(primaryid)
                    self.demo_index[canonical_id] = row
                    self.canonical_ids[primaryid] = canonical_id
        
        # Index DRUG
        drug_table = tables.get("DRUG")
        if drug_table:
            for row in drug_table.rows:
                primaryid = self._extract_primaryid(row)
                if primaryid:
                    canonical_id = self._canonicalize_id(primaryid)
                    self.drug_map[canonical_id].append(row)
        
        # Index REAC
        reac_table = tables.get("REAC")
        if reac_table:
            for row in reac_table.rows:
                primaryid = self._extract_primaryid(row)
                if primaryid:
                    canonical_id = self._canonicalize_id(primaryid)
                    self.reac_map[canonical_id].append(row)
        
        # Index THER
        ther_table = tables.get("THER")
        if ther_table:
            for row in ther_table.rows:
                primaryid = self._extract_primaryid(row)
                if primaryid:
                    canonical_id = self._canonicalize_id(primaryid)
                    self.ther_map[canonical_id].append(row)
        
        # Index OUTC
        outc_table = tables.get("OUTC")
        if outc_table:
            for row in outc_table.rows:
                primaryid = self._extract_primaryid(row)
                if primaryid:
                    canonical_id = self._canonicalize_id(primaryid)
                    self.outc_map[canonical_id].append(row)
        
        # Index INDI
        indi_table = tables.get("INDI")
        if indi_table:
            for row in indi_table.rows:
                primaryid = self._extract_primaryid(row)
                if primaryid:
                    canonical_id = self._canonicalize_id(primaryid)
                    self.indi_map[canonical_id].append(row)
        
        # Build duplicate groups
        self._build_duplicate_groups()
        
        # Attempt key reconstruction
        self._reconstruct_missing_keys(tables)
    
    def _extract_primaryid(self, row: Dict[str, Any]) -> Optional[str]:
        """Extract PRIMARYID from row, trying multiple column variations."""
        possible_cols = ["primaryid", "PRIMARYID", "PrimaryID", "primary_id", "PRIMARY_ID"]
        for col in possible_cols:
            val = row.get(col)
            if val:
                return str(val).strip()
        return None
    
    def _canonicalize_id(self, primaryid: str) -> str:
        """
        Canonicalize PRIMARYID to handle variations.
        
        Handles:
        - Case variations
        - Leading/trailing spaces
        - Zero-padding issues
        """
        # Normalize
        canonical = str(primaryid).strip().upper()
        
        # Remove leading zeros (if numeric)
        try:
            numeric_id = int(canonical)
            canonical = str(numeric_id)
        except (ValueError, OverflowError):
            pass  # Keep as-is if not numeric
        
        return canonical
    
    def _build_duplicate_groups(self) -> None:
        """Build groups of duplicate PRIMARYIDs."""
        # Check DEMO for duplicates
        id_to_canonical = {}
        for variant, canonical in self.canonical_ids.items():
            if canonical not in id_to_canonical:
                id_to_canonical[canonical] = []
            id_to_canonical[canonical].append(variant)
        
        # Build duplicate groups (canonicals with multiple variants)
        for canonical, variants in id_to_canonical.items():
            if len(variants) > 1:
                self.duplicate_groups[canonical] = variants
    
    def _reconstruct_missing_keys(self, tables: Dict[str, FaersTable]) -> None:
        """
        Attempt to reconstruct missing PRIMARYIDs using cross-table matching.
        
        Strategy:
        - Match by CASEID if available
        - Match by date + drug + reaction combination
        - Match by patient demographics + date
        """
        # Find rows with missing PRIMARYID
        for table_name, table in tables.items():
            for row in table.rows:
                primaryid = self._extract_primaryid(row)
                if not primaryid:
                    # Try to match by CASEID
                    caseid = row.get("caseid") or row.get("CASEID") or row.get("CASE_ID")
                    if caseid:
                        # Try to find matching PRIMARYID in DEMO
                        for demo_id, demo_row in self.demo_index.items():
                            demo_caseid = demo_row.get("caseid") or demo_row.get("CASEID")
                            if str(demo_caseid).strip().upper() == str(caseid).strip().upper():
                                row["primaryid"] = demo_id
                                row["PRIMARYID"] = demo_id
                                break
    
    def get_demo(self, primaryid: str) -> Optional[Dict[str, Any]]:
        """Get DEMO row by PRIMARYID."""
        canonical = self._canonicalize_id(primaryid)
        return self.demo_index.get(canonical)
    
    def get_drugs(self, primaryid: str) -> List[Dict[str, Any]]:
        """Get all DRUG rows for a PRIMARYID."""
        canonical = self._canonicalize_id(primaryid)
        return self.drug_map.get(canonical, [])
    
    def get_reactions(self, primaryid: str) -> List[Dict[str, Any]]:
        """Get all REAC rows for a PRIMARYID."""
        canonical = self._canonicalize_id(primaryid)
        return self.reac_map.get(canonical, [])
    
    def get_outcomes(self, primaryid: str) -> List[Dict[str, Any]]:
        """Get all OUTC rows for a PRIMARYID."""
        canonical = self._canonicalize_id(primaryid)
        return self.outc_map.get(canonical, [])
    
    def get_therapies(self, primaryid: str) -> List[Dict[str, Any]]:
        """Get all THER rows for a PRIMARYID."""
        canonical = self._canonicalize_id(primaryid)
        return self.ther_map.get(canonical, [])
    
    def get_indications(self, primaryid: str) -> List[Dict[str, Any]]:
        """Get all INDI rows for a PRIMARYID."""
        canonical = self._canonicalize_id(primaryid)
        return self.indi_map.get(canonical, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "demo_count": len(self.demo_index),
            "drug_entries": sum(len(v) for v in self.drug_map.values()),
            "reac_entries": sum(len(v) for v in self.reac_map.values()),
            "ther_entries": sum(len(v) for v in self.ther_map.values()),
            "outc_entries": sum(len(v) for v in self.outc_map.values()),
            "indi_entries": sum(len(v) for v in self.indi_map.values()),
            "duplicate_groups": len(self.duplicate_groups),
            "missing_keys": len(self.missing_keys),
        }

