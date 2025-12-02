"""
Mechanism Supervisor - Master orchestrator for mechanism reasoning
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MechanismSupervisor:
    """
    High-level orchestrator for mechanistic reasoning:
    - Causal inference
    - Mechanistic similarity
    - Pathway expansion
    - Literature evidence
    - Toxicology reasoning
    - Cross-drug interaction
    - Novelty detection
    - Mechanistic alerts
    
    This is the engine used by:
    - Executive Dashboard
    - Mechanism Explorer
    - Risk Manager
    - Pathway Maps
    """
    
    def __init__(
        self,
        fusion,
        pathways,
        causal,
        lit,
        toxic,
        inter,
        novelty,
        alerts,
        kg=None,
        router=None
    ):
        """
        Initialize mechanism supervisor.
        
        Args:
            fusion: MechanismEmbeddingFusion instance
            pathways: PathwayExpansionEngine instance
            causal: CausalInferenceEngine instance
            lit: LiteratureSummarizer instance
            toxic: ToxicologyReasoner instance
            inter: CrossDrugInteractionEngine instance
            novelty: NovelSignalDetector instance
            alerts: MechanisticAlerts instance
            kg: Optional KnowledgeGraph instance
            router: Optional KGRouter instance
        """
        self.fusion = fusion
        self.pathways = pathways
        self.causal = causal
        self.lit = lit
        self.toxic = toxic
        self.inter = inter
        self.novelty = novelty
        self.alerts = alerts
        self.kg = kg
        self.router = router
    
    def analyze(
        self,
        drug: str,
        reaction: str,
        social_df: Optional[pd.DataFrame] = None,
        faers_df: Optional[pd.DataFrame] = None,
        lit_papers: Optional[List[str]] = None,
        mech_texts: Optional[List[str]] = None,
        co_medications: Optional[List[str]] = None,
        quantum_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform complete mechanistic analysis.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            social_df: Optional social media DataFrame
            faers_df: Optional FAERS DataFrame
            lit_papers: Optional list of literature papers
            mech_texts: Optional list of mechanism texts
            co_medications: Optional list of co-medications
            quantum_score: Optional quantum score
        
        Returns:
            Complete analysis dictionary
        """
        # Default empty DataFrames if not provided
        if social_df is None:
            social_df = pd.DataFrame()
        if faers_df is None:
            faers_df = pd.DataFrame()
        if lit_papers is None:
            lit_papers = []
        if mech_texts is None:
            mech_texts = []
        if co_medications is None:
            co_medications = []
        
        # 1. Novelty Detection
        try:
            novel_pairs = self.novelty.detect(social_df, faers_df)
            is_novel = any(
                d.get("drug") == drug and d.get("reaction") == reaction
                for d in novel_pairs
            )
        except Exception as e:
            logger.warning(f"Novelty detection error: {e}")
            is_novel = False
            novel_pairs = []
        
        # 2. Causal Analysis
        try:
            if not social_df.empty:
                causal_scores = self.causal.causal_strength(social_df, drug, reaction)
            else:
                causal_scores = {"causal_score": 0.0, "p_rd": 0.0, "counterfactual": 0.0}
        except Exception as e:
            logger.warning(f"Causal analysis error: {e}")
            causal_scores = {"causal_score": 0.0, "p_rd": 0.0, "counterfactual": 0.0}
        
        # 3. Mechanism Fusion
        try:
            fusion_scores = self.fusion.fuse(drug, reaction, mech_texts)
        except Exception as e:
            logger.warning(f"Fusion error: {e}")
            fusion_scores = {"fusion_score": 0.0, "drug_reaction_similarity": 0.0, "mechanism_reaction_similarity": 0.0}
        
        # 4. Pathway Expansion
        try:
            if mech_texts:
                related_pathways = self.pathways.find_related(" ".join(mech_texts), k=5)
            else:
                related_pathways = []
        except Exception as e:
            logger.warning(f"Pathway expansion error: {e}")
            related_pathways = []
        
        # 5. Literature Summary
        try:
            lit_summary = self.lit.summarize(drug, reaction, lit_papers)
        except Exception as e:
            logger.warning(f"Literature summarization error: {e}")
            lit_summary = {"summary": None, "papers_used": 0}
        
        # 6. Toxicology Reasoning
        try:
            tox = self.toxic.evaluate(drug, reaction)
        except Exception as e:
            logger.warning(f"Toxicology reasoning error: {e}")
            tox = {"tox_present": False, "tox_score": 0.0}
        
        # 7. Cross-Drug Interaction
        try:
            interactions = self.inter.evaluate(drug, reaction, co_medications)
        except Exception as e:
            logger.warning(f"Interaction evaluation error: {e}")
            interactions = {"interactions_detected": [], "count": 0, "interaction_score": 0.0}
        
        # 8. Alerts
        try:
            alert_info = self.alerts.evaluate(fusion_scores, is_novel, causal_scores, drug, reaction)
        except Exception as e:
            logger.warning(f"Alert evaluation error: {e}")
            alert_info = {"alert": False, "alert_score": 0.0}
        
        # Compile results
        result = {
            "drug": drug,
            "reaction": reaction,
            "novel": is_novel,
            "novel_pairs": novel_pairs[:5],  # Top 5
            "causal": causal_scores,
            "fusion": fusion_scores,
            "related_pathways": related_pathways,
            "literature": lit_summary,
            "toxicology": tox,
            "interactions": interactions,
            "alert": alert_info
        }
        
        # Add quantum score if provided
        if quantum_score is not None:
            result["quantum_score"] = quantum_score
        
        # Add KG path if available
        if self.router:
            try:
                kg_explanation = self.router.explain(drug, reaction)
                result["kg_path"] = kg_explanation.get("mechanistic_path")
                result["kg_path_details"] = kg_explanation.get("path_details", [])
            except Exception as e:
                logger.debug(f"KG path finding error: {e}")
        
        return result
    
    def batch_analyze(
        self,
        drug_reaction_pairs: List[tuple],
        social_df: Optional[pd.DataFrame] = None,
        faers_df: Optional[pd.DataFrame] = None,
        lit_papers_map: Optional[Dict[tuple, List[str]]] = None,
        mech_texts_map: Optional[Dict[tuple, List[str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple drug-reaction pairs.
        
        Args:
            drug_reaction_pairs: List of (drug, reaction) tuples
            social_df: Optional social media DataFrame
            faers_df: Optional FAERS DataFrame
            lit_papers_map: Optional mapping of (drug, reaction) to papers
            mech_texts_map: Optional mapping of (drug, reaction) to mechanism texts
        
        Returns:
            List of analysis dictionaries
        """
        results = []
        
        for drug, reaction in drug_reaction_pairs:
            lit_papers = lit_papers_map.get((drug, reaction), []) if lit_papers_map else []
            mech_texts = mech_texts_map.get((drug, reaction), []) if mech_texts_map else []
            
            analysis = self.analyze(
                drug=drug,
                reaction=reaction,
                social_df=social_df,
                faers_df=faers_df,
                lit_papers=lit_papers,
                mech_texts=mech_texts
            )
            
            results.append(analysis)
        
        return results

