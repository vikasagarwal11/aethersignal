"""
Source Registry - Auto-discovers and instantiates all data sources.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .base import SourceClientBase

logger = logging.getLogger(__name__)

# Default config path
CONFIG_PATH = Path("data_source_config.yaml")


class SourceRegistry:
    """
    Loads config, instantiates data sources, provides lookup.
    Auto-discovers which sources are available.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize source registry.
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config_path = config_path or CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self.sources: Dict[str, SourceClientBase] = {}
        self._load_config()
        self._load_sources()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}. Using empty config.")
            self.config = {"sources": {}}
            return
        
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f) or {"sources": {}}
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            self.config = {"sources": {}}
    
    def _load_sources(self):
        """Instantiate all source clients."""
        sources_config = self.config.get("sources", {})
        
        # Import source clients
        try:
            # Free sources
            from .sources.openfda import OpenFDAClient
            from .sources.pubmed import PubMedClient
            from .sources.clinicaltrials import ClinicalTrialsClient
            from .sources.dailymed import DailyMedClient
            from .sources.medsafety_alerts import MedSafetyAlertsClient
            
            # Paid sources
            from .sources.humanapi import HumanAPIClient
            from .sources.metriport import MetriportClient
            from .sources.drugbank import DrugBankClient
            from .sources.vigibase import VigiBaseClient
            from .sources.epic_fhir import EpicFHIRClient
            from .sources.cerner_fhir import CernerFHIRClient
            from .sources.ohdsi import OHDSIClient
        except ImportError as e:
            logger.warning(f"Could not import some source clients: {str(e)}")
            return
        
        # Free sources
        if "openfda" in sources_config:
            try:
                self.sources["openfda"] = OpenFDAClient("openfda", sources_config["openfda"])
            except Exception as e:
                logger.error(f"Error loading OpenFDA client: {str(e)}")
        
        if "pubmed" in sources_config:
            try:
                self.sources["pubmed"] = PubMedClient("pubmed", sources_config["pubmed"])
            except Exception as e:
                logger.error(f"Error loading PubMed client: {str(e)}")
        
        if "clinicaltrials" in sources_config:
            try:
                self.sources["clinicaltrials"] = ClinicalTrialsClient("clinicaltrials", sources_config["clinicaltrials"])
            except Exception as e:
                logger.error(f"Error loading ClinicalTrials client: {str(e)}")
        
        if "dailymed" in sources_config:
            try:
                self.sources["dailymed"] = DailyMedClient("dailymed", sources_config["dailymed"])
            except Exception as e:
                logger.error(f"Error loading DailyMed client: {str(e)}")
        
        if "medsafety_alerts" in sources_config:
            try:
                self.sources["medsafety_alerts"] = MedSafetyAlertsClient("medsafety_alerts", sources_config["medsafety_alerts"])
            except Exception as e:
                logger.error(f"Error loading MedSafetyAlerts client: {str(e)}")
        
        # Paid sources (with auto-enable logic)
        if "human_api" in sources_config:
            try:
                config = sources_config["human_api"]
                # Auto-enable if key present
                if config.get("enabled") == "auto":
                    import os
                    config["enabled"] = bool(os.getenv("HUMAN_API_KEY", ""))
                self.sources["human_api"] = HumanAPIClient("human_api", config)
            except Exception as e:
                logger.error(f"Error loading HumanAPI client: {str(e)}")
        
        if "metriport" in sources_config:
            try:
                config = sources_config["metriport"]
                if config.get("enabled") == "auto":
                    import os
                    config["enabled"] = bool(os.getenv("METRIPORT_API_KEY", ""))
                self.sources["metriport"] = MetriportClient("metriport", config)
            except Exception as e:
                logger.error(f"Error loading Metriport client: {str(e)}")
        
        if "drugbank" in sources_config:
            try:
                config = sources_config["drugbank"]
                if config.get("enabled") == "auto":
                    import os
                    config["enabled"] = bool(os.getenv("DRUGBANK_KEY", ""))
                self.sources["drugbank"] = DrugBankClient("drugbank", config)
            except Exception as e:
                logger.error(f"Error loading DrugBank client: {str(e)}")
        
        if "vigibase" in sources_config:
            try:
                config = sources_config["vigibase"]
                if config.get("enabled") == "auto":
                    import os
                    config["enabled"] = bool(os.getenv("VIGIBASE_KEY", ""))
                self.sources["vigibase"] = VigiBaseClient("vigibase", config)
            except Exception as e:
                logger.error(f"Error loading VigiBase client: {str(e)}")
        
        if "epic_fhir" in sources_config:
            try:
                config = sources_config["epic_fhir"]
                if config.get("enabled") == "auto":
                    import os
                    config["enabled"] = bool(os.getenv("EPIC_FHIR_KEY", "") or os.getenv("EPIC_FHIR_CLIENT_ID", ""))
                self.sources["epic_fhir"] = EpicFHIRClient("epic_fhir", config)
            except Exception as e:
                logger.error(f"Error loading Epic FHIR client: {str(e)}")
        
        if "cerner_fhir" in sources_config:
            try:
                config = sources_config["cerner_fhir"]
                if config.get("enabled") == "auto":
                    import os
                    config["enabled"] = bool(os.getenv("CERNER_FHIR_KEY", "") or os.getenv("CERNER_FHIR_CLIENT_ID", ""))
                self.sources["cerner_fhir"] = CernerFHIRClient("cerner_fhir", config)
            except Exception as e:
                logger.error(f"Error loading Cerner FHIR client: {str(e)}")
        
        if "ohdsi" in sources_config:
            try:
                config = sources_config["ohdsi"]
                if config.get("enabled") == "auto":
                    import os
                    config["enabled"] = bool(os.getenv("OHDSI_KEY", ""))
                self.sources["ohdsi"] = OHDSIClient("ohdsi", config)
            except Exception as e:
                logger.error(f"Error loading OHDSI client: {str(e)}")
        
        # Reddit (uses existing social_ae module)
        if "reddit" in sources_config:
            # Reddit is handled by social_ae module, not a separate client
            # Will integrate in unified pipeline
            pass
        
        logger.info(f"Loaded {len(self.sources)} data sources from registry")
    
    def get_enabled_sources(self) -> List[SourceClientBase]:
        """Get all enabled sources, sorted by priority."""
        enabled = [s for s in self.sources.values() if s.enabled]
        return sorted(enabled, key=lambda x: x.priority, reverse=True)
    
    def get_all_sources(self) -> List[SourceClientBase]:
        """Get all sources (enabled and disabled), sorted by priority."""
        return sorted(self.sources.values(), key=lambda x: x.priority, reverse=True)
    
    def get(self, source_name: str) -> Optional[SourceClientBase]:
        """Get a specific source by name."""
        return self.sources.get(source_name)
    
    def register(self, source_name: str, client: SourceClientBase):
        """Register a new source client."""
        self.sources[source_name] = client
        logger.info(f"Registered source: {source_name}")
    
    def is_available(self, source_name: str) -> bool:
        """Check if a source is available (registered)."""
        return source_name in self.sources

