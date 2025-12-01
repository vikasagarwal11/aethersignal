"""
Local Summary Engine (CHUNK 7.5.11)
Full orchestrator for local (browser) summary generation.
Coordinates all local engines for complete offline analysis.
"""
import pandas as pd
from typing import Dict, Any
from datetime import datetime

from .local_trends import LocalTrendDetector
from .local_rpf import LocalRPF
from .local_subgroups import LocalSubgroupAnalyzer
from .local_signal_strength import LocalSignalStrength
from .local_benefit_risk import LocalBenefitRisk
from .local_capa import LocalCAPAStarter
from .local_label_impact import LocalLabelImpact
from .local_emerging_alerts import LocalEmergingAlerts


class LocalSummaryEngine:
    """
    Complete local summary engine orchestrator.
    
    Coordinates all local analysis engines:
    - Trend detection
    - RPF scoring
    - Subgroup analysis
    - Signal strength
    - Benefit-risk
    - CAPA recommendations
    - Label impact
    - Emerging alerts
    
    All running entirely in browser via Pyodide.
    """
    
    def __init__(self):
        """Initialize Local Summary Engine with all sub-engines."""
        self.trends = LocalTrendDetector()
        self.rpf = LocalRPF()
        self.subgroups = LocalSubgroupAnalyzer()
        self.strength = LocalSignalStrength()
        self.br = LocalBenefitRisk()
        self.capa = LocalCAPAStarter()
        self.label = LocalLabelImpact()
        self.alerts = LocalEmergingAlerts()
    
    def summarize(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate complete local summary.
        
        Args:
            df: Safety data DataFrame
            
        Returns:
            Complete summary dictionary with all local analyses
        """
        try:
            # Detect trends first (needed for alerts)
            trends_result = self.trends.detect_trends(df)
            
            # Run all analyses
            summary = {
                "trends": trends_result,
                "subgroups": self.subgroups.run(df),
                "rpf": self.rpf.compute_rpf(df),
                "strength": self.strength.compute(df),
                "benefit_risk": self.br.draft_summary(df),
                "capa": self.capa.generate(df),
                "label": self.label.detect(df),
                "emerging_alerts": self.alerts.detect(trends_result),
                "metadata": {
                    "engine": "local",
                    "offline": True,
                    "generated_at": datetime.utcnow().isoformat(),
                    "row_count": len(df) if df is not None else 0
                }
            }
            
            return summary
            
        except Exception as e:
            return {
                "error": str(e),
                "metadata": {
                    "engine": "local",
                    "offline": True,
                    "generated_at": datetime.utcnow().isoformat(),
                    "error": True
                }
            }

