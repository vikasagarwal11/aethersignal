"""
PSUR Context Models
Defines data structures for PSUR/DSUR report generation with multi-tenant support.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class OrgProductConfig:
    """
    Per-tenant, per-product configuration for regulatory sections.
    All of this is organization-owned metadata.
    """
    product_name: str
    authorization_status: Dict[str, str] = field(default_factory=dict)  # {region: status}
    safety_actions: List[Dict[str, Any]] = field(default_factory=list)  # [{date, description}]
    rmp_changes: List[Dict[str, Any]] = field(default_factory=list)  # [{date, description}]
    exposure_estimates: Dict[str, Any] = field(default_factory=dict)  # {"2025Q1": "2M pt-yrs"}
    clinical_program: List[Dict[str, Any]] = field(default_factory=list)  # [{study_id, phase, summary}]
    pv_system_overview: Optional[str] = None  # free-text org description
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrgProductConfig':
        """Create from dictionary (e.g., from database JSONB)."""
        return cls(
            product_name=data.get("product_name", ""),
            authorization_status=data.get("authorization_status", {}),
            safety_actions=data.get("safety_actions", []),
            rmp_changes=data.get("rmp_changes", []),
            exposure_estimates=data.get("exposure_estimates", {}),
            clinical_program=data.get("clinical_program", []),
            pv_system_overview=data.get("pv_system_overview")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "product_name": self.product_name,
            "authorization_status": self.authorization_status,
            "safety_actions": self.safety_actions,
            "rmp_changes": self.rmp_changes,
            "exposure_estimates": self.exposure_estimates,
            "clinical_program": self.clinical_program,
            "pv_system_overview": self.pv_system_overview
        }


@dataclass
class PSURContext:
    """
    The full context needed to generate PSUR/DSUR/Signal reports.
    """
    tenant_id: str  # Organization identifier
    product: str
    org_config: Optional[OrgProductConfig]
    
    # Unified AE + signal data
    unified_ae_data: Any  # DataFrame or dict with FAERS, social, literature data
    signals_summary: Any  # Signal-level KPIs / rankings
    literature_summary: Any  # Optional; can be None
    
    period_start: str  # ISO format date string
    period_end: str  # ISO format date string
    
    def validate(self) -> List[str]:
        """
        Validate context and return list of warnings.
        
        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []
        
        if not self.tenant_id:
            warnings.append("Tenant ID is missing")
        
        if not self.product:
            warnings.append("Product name is missing")
        
        if not self.period_start or not self.period_end:
            warnings.append("Report period dates are missing")
        
        return warnings

