"""
Mechanistic Chain Generator (Phase 3D.4B)
Generates drug → target → pathway → AE chains with plausibility scoring.
"""

from typing import Dict, List, Any, Optional
import logging

from .biological_pathway_graph import BiologicalPathwayGraph

logger = logging.getLogger(__name__)


class MechanisticChainGenerator:
    """
    Generates mechanistic chains from drug to AE.
    """
    
    def __init__(self, pathway_graph: Optional[BiologicalPathwayGraph] = None):
        """
        Initialize chain generator.
        
        Args:
            pathway_graph: Optional pathway graph (creates new if not provided)
        """
        self.pathway_graph = pathway_graph or BiologicalPathwayGraph()
        self._load_drug_target_data()
    
    def _load_drug_target_data(self):
        """Load drug-target data from free sources."""
        # This would load from:
        # - DrugBank (free subset)
        # - ChEMBL (free)
        # - KEGG (pathways)
        # - Reactome (open source)
        
        # For now, we'll use a simplified lookup
        self.drug_targets = {
            "semaglutide": ["GLP-1 receptor"],
            "ozempic": ["GLP-1 receptor"],
            "wegovy": ["GLP-1 receptor"],
            "mounjaro": ["GLP-1 receptor", "GIP receptor"],
            "tirzepatide": ["GLP-1 receptor", "GIP receptor"],
            "liraglutide": ["GLP-1 receptor"],
            "dulaglutide": ["GLP-1 receptor"]
        }
        
        self.target_pathways = {
            "GLP-1 receptor": [
                "cAMP signaling pathway",
                "Insulin secretion pathway",
                "Gastric emptying regulation"
            ],
            "GIP receptor": [
                "Glucose homeostasis",
                "Insulin secretion pathway"
            ]
        }
        
        self.pathway_effects = {
            "Gastric emptying regulation": [
                "Delayed gastric emptying",
                "Reduced gastric motility"
            ],
            "cAMP signaling pathway": [
                "Increased insulin secretion",
                "Reduced glucagon secretion"
            ]
        }
        
        self.effect_symptoms = {
            "Delayed gastric emptying": ["Nausea", "Vomiting", "Gastric discomfort"],
            "Reduced gastric motility": ["Nausea", "Bloating", "Early satiety"],
            "Dehydration": ["Tachycardia", "Dizziness", "Fatigue"]
        }
    
    def generate_chain(
        self,
        drug: str,
        reaction: str
    ) -> Dict[str, Any]:
        """
        Generate mechanistic chain for drug-reaction pair.
        
        Args:
            drug: Drug name
            reaction: Reaction name
        
        Returns:
            Dictionary with mechanism chain and metadata
        """
        drug_lower = drug.lower()
        
        # Step 1: Find drug targets
        targets = self.drug_targets.get(drug_lower, [])
        if not targets:
            # Try to find in pathway graph
            targets = self.pathway_graph.get_targets(drug)
        
        if not targets:
            return {
                "drug": drug,
                "reaction": reaction,
                "chain": [],
                "plausibility_score": 0.0,
                "error": "No known targets found for drug"
            }
        
        # Step 2: Find pathways
        pathways = []
        for target in targets:
            target_pathways = self.target_pathways.get(target, [])
            if not target_pathways:
                target_pathways = self.pathway_graph.get_pathways(target)
            pathways.extend(target_pathways)
        
        # Step 3: Find physiological effects
        effects = []
        for pathway in pathways:
            pathway_effects = self.pathway_effects.get(pathway, [])
            effects.extend(pathway_effects)
        
        # Step 4: Map to symptoms/reactions
        chain = []
        chain.append(f"{drug} activates {targets[0]}")
        
        if pathways:
            chain.append(f"which modulates {pathways[0]}")
        
        if effects:
            # Find effect that leads to reaction
            relevant_effect = None
            for effect in effects:
                symptoms = self.effect_symptoms.get(effect, [])
                if reaction in symptoms or any(reaction.lower() in s.lower() for s in symptoms):
                    relevant_effect = effect
                    break
            
            if relevant_effect:
                chain.append(f"leading to {relevant_effect}")
                chain.append(f"which causes {reaction}")
            else:
                # Generic chain
                chain.append(f"which affects physiological processes")
                chain.append(f"potentially leading to {reaction}")
        
        # Calculate plausibility score
        plausibility = self._calculate_plausibility(drug, reaction, targets, pathways, effects)
        
        return {
            "drug": drug,
            "reaction": reaction,
            "chain": chain,
            "targets": targets,
            "pathways": pathways,
            "effects": effects,
            "plausibility_score": plausibility,
            "pathway_ids": self._get_pathway_ids(pathways)
        }
    
    def _calculate_plausibility(
        self,
        drug: str,
        reaction: str,
        targets: List[str],
        pathways: List[str],
        effects: List[str]
    ) -> float:
        """
        Calculate mechanistic plausibility score (0-1).
        
        Args:
            drug: Drug name
            reaction: Reaction name
            targets: List of drug targets
            pathways: List of pathways
            effects: List of physiological effects
        
        Returns:
            Plausibility score (0-1)
        """
        score = 0.0
        
        # Base score from having targets
        if targets:
            score += 0.3
        
        # Pathway evidence
        if pathways:
            score += 0.2
        
        # Direct effect mapping
        for effect in effects:
            symptoms = self.effect_symptoms.get(effect, [])
            if reaction in symptoms or any(reaction.lower() in s.lower() for s in symptoms):
                score += 0.3
                break
        
        # Known drug class patterns (GLP-1 agonists commonly cause GI symptoms)
        drug_lower = drug.lower()
        if any(glp1 in drug_lower for glp1 in ["semaglutide", "liraglutide", "dulaglutide", "mounjaro"]):
            if reaction.lower() in ["nausea", "vomiting", "diarrhea", "gastric"]:
                score += 0.2
        
        return min(score, 1.0)
    
    def _get_pathway_ids(self, pathways: List[str]) -> List[str]:
        """Get KEGG/Reactome pathway IDs (placeholder)."""
        # In production, would map pathway names to KEGG/Reactome IDs
        pathway_id_map = {
            "cAMP signaling pathway": "hsa04024",
            "Insulin secretion pathway": "hsa04911",
            "Gastric emptying regulation": "hsa04972"
        }
        
        return [pathway_id_map.get(p, "") for p in pathways if pathway_id_map.get(p)]

