"""
Data Source Client Implementations.
All free and paid source clients are defined here.
"""

# Free sources
from .openfda import OpenFDAClient
from .pubmed import PubMedClient
from .clinicaltrials import ClinicalTrialsClient
from .dailymed import DailyMedClient

# Paid sources
from .humanapi import HumanAPIClient
from .metriport import MetriportClient
from .drugbank import DrugBankClient
from .vigibase import VigiBaseClient
from .epic_fhir import EpicFHIRClient
from .cerner_fhir import CernerFHIRClient
from .ohdsi import OHDSIClient

# Social sources (already implemented, will integrate)
# from ..social_ae.social_fetcher import SocialAEClient

__all__ = [
    # Free sources
    "OpenFDAClient",
    "PubMedClient",
    "ClinicalTrialsClient",
    "DailyMedClient",
    # Paid sources
    "HumanAPIClient",
    "MetriportClient",
    "DrugBankClient",
    "VigiBaseClient",
    "EpicFHIRClient",
    "CernerFHIRClient",
    "OHDSIClient",
]

