"""
Local Emerging Alerts (CHUNK 7.5.10)
Detects emerging alerts from trend data.
Runs entirely in browser via Pyodide.
"""
from typing import List, Dict, Any


class LocalEmergingAlerts:
    """
    Local emerging alerts detection engine.
    
    Detects emerging safety signals from trend analysis.
    """
    
    def detect(self, trends: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect emerging alerts from trends.
        
        Args:
            trends: Trend analysis dictionary from LocalTrendDetector
            
        Returns:
            List of emerging alerts
        """
        alerts = []
        
        try:
            # Extract spikes
            spikes = trends.get("spikes", [])
            if isinstance(spikes, list) and len(spikes) > 0:
                for spike in spikes[:10]:  # Top 10
                    if isinstance(spike, dict):
                        alerts.append({
                            "drug": spike.get("drug", "Unknown"),
                            "reaction": spike.get("reaction", "Unknown"),
                            "yoy_change": spike.get("YOY_DELTA", 0),
                            "yoy_pct": spike.get("YOY_PCT", 0.0),
                            "type": "spike"
                        })
            
            # Extract emerging patterns
            emerging = trends.get("emerging", [])
            if isinstance(emerging, list) and len(emerging) > 0:
                for pattern in emerging[:10]:  # Top 10
                    if isinstance(pattern, dict):
                        alerts.append({
                            "drug": pattern.get("drug", "Unknown"),
                            "reaction": pattern.get("reaction", "Unknown"),
                            "growth_years": pattern.get("growth_years", 0),
                            "total_years": pattern.get("total_years", 0),
                            "type": "emerging"
                        })
            
        except Exception as e:
            alerts.append({
                "error": str(e),
                "type": "error"
            })
        
        return alerts[:10]  # Limit to 10 alerts

