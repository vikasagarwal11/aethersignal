"""
Linking Engine - Automatic KG population from data sources
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from .kg_core import KnowledgeGraph
import logging

logger = logging.getLogger(__name__)


class LinkingEngine:
    """
    Automatically populates the KG from:
    - Social AE posts
    - FAERS cases
    - Literature extracted associations
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def ingest_social(self, df: pd.DataFrame):
        """
        Ingest social media AE data into KG.
        
        Args:
            df: DataFrame with columns: drug_match, reaction, confidence, severity
        """
        if df.empty:
            return
        
        count = 0
        for _, row in df.iterrows():
            drug = row.get("drug_match") or row.get("drug")
            reaction = row.get("reaction")
            
            if not drug or not reaction:
                continue
            
            # Add nodes
            self.kg.add_drug(drug)
            self.kg.add_reaction(reaction)
            
            # Calculate weight from confidence and severity
            confidence = row.get("confidence", 0.5)
            severity = row.get("severity", 0.5)
            weight = (confidence + severity) / 2.0
            
            # Link
            self.kg.link_drug_reaction(
                drug,
                reaction,
                weight=weight,
                source="social",
                confidence=confidence,
                severity=severity
            )
            count += 1
        
        logger.info(f"Ingested {count} social AE links into KG")
    
    def ingest_faers(self, df: pd.DataFrame):
        """
        Ingest FAERS data into KG.
        
        Args:
            df: DataFrame with columns: drug, reaction, seriousness
        """
        if df.empty:
            return
        
        count = 0
        for _, row in df.iterrows():
            drug = row.get("drug")
            reaction = row.get("reaction")
            
            if not drug or not reaction:
                continue
            
            # Add nodes
            self.kg.add_drug(drug)
            self.kg.add_reaction(reaction)
            
            # Calculate weight from seriousness
            seriousness = row.get("seriousness", 0)
            weight = 1.0 if seriousness > 0 else 0.7
            
            # Link
            self.kg.link_drug_reaction(
                drug,
                reaction,
                weight=weight,
                source="faers",
                seriousness=seriousness
            )
            count += 1
        
        logger.info(f"Ingested {count} FAERS links into KG")
    
    def ingest_literature(self, df: pd.DataFrame):
        """
        Ingest literature data into KG.
        
        Args:
            df: DataFrame with columns: drug, mechanism, reaction, pathway
        """
        if df.empty:
            return
        
        count = 0
        for _, row in df.iterrows():
            drug = row.get("drug")
            mechanism = row.get("mechanism") or row.get("pathway")
            reaction = row.get("reaction")
            
            if not drug:
                continue
            
            # Add drug
            self.kg.add_drug(drug)
            
            # Add mechanism/pathway if present
            if mechanism:
                self.kg.add_mechanism(mechanism)
                self.kg.link_drug_pathway(drug, mechanism, source="literature")
            
            # Add reaction if present
            if reaction:
                self.kg.add_reaction(reaction)
                
                # Link drug to reaction
                self.kg.link_drug_reaction(drug, reaction, source="literature", weight=0.9)
                
                # Link mechanism to reaction if both present
                if mechanism:
                    self.kg.link_pathway_reaction(mechanism, reaction, source="literature")
            
            count += 1
        
        logger.info(f"Ingested {count} literature links into KG")
    
    def ingest_mechanisms(self, mechanisms: List[Dict[str, Any]]):
        """
        Ingest explicit mechanism data.
        
        Args:
            mechanisms: List of mechanism dictionaries with drug, target, pathway, reaction
        """
        count = 0
        for mech in mechanisms:
            drug = mech.get("drug")
            target = mech.get("target")
            pathway = mech.get("pathway")
            reaction = mech.get("reaction")
            
            if not drug:
                continue
            
            self.kg.add_drug(drug)
            
            if target:
                self.kg.add_target(target)
                self.kg.link_drug_target(drug, target, source=mech.get("source", "manual"))
            
            if pathway:
                self.kg.add_pathway(pathway)
                if target:
                    self.kg.link_target_pathway(target, pathway, source=mech.get("source", "manual"))
                else:
                    self.kg.link_drug_pathway(drug, pathway, source=mech.get("source", "manual"))
            
            if reaction:
                self.kg.add_reaction(reaction)
                if pathway:
                    self.kg.link_pathway_reaction(pathway, reaction, source=mech.get("source", "manual"))
                else:
                    self.kg.link_drug_reaction(drug, reaction, source=mech.get("source", "manual"))
            
            count += 1
        
        logger.info(f"Ingested {count} mechanism links into KG")

