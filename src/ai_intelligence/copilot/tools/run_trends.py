"""
Trend Analysis Tool - Analyze trends
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class TrendTool:
    """Tool for trend analysis."""
    
    name = "trend"
    description = "Analyze trends from FAERS + social"
    
    def run(self, drug: str, reaction: Optional[str] = None) -> Dict[str, Any]:
        """
        Run trend analysis.
        
        Args:
            drug: Drug name
            reaction: Optional specific reaction
        
        Returns:
            Trend analysis dictionary
        """
        try:
            from src.storage.federated_query_engine import FederatedQueryEngine
            from src.storage.unified_storage import UnifiedStorageEngine
            
            storage = UnifiedStorageEngine()
            query_engine = FederatedQueryEngine(storage)
            
            # Query for data
            query = f"drug:{drug}"
            if reaction:
                query += f" reaction:{reaction}"
            
            results = query_engine.query(query, limit=1000)
            
            if not results:
                return {
                    "tool": self.name,
                    "drug": drug,
                    "reaction": reaction,
                    "trend": "INSUFFICIENT_DATA",
                    "summary": "No data available for trend analysis"
                }
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(results)
            
            # Group by date if available
            if "timestamp" in df.columns:
                df["date"] = pd.to_datetime(df["timestamp"]).dt.date
                daily_counts = df.groupby("date").size()
                
                # Calculate trend
                if len(daily_counts) >= 2:
                    trend_direction = "INCREASING" if daily_counts.iloc[-1] > daily_counts.iloc[0] else "DECREASING"
                    trend_magnitude = abs((daily_counts.iloc[-1] - daily_counts.iloc[0]) / daily_counts.iloc[0]) if daily_counts.iloc[0] > 0 else 0
                else:
                    trend_direction = "STABLE"
                    trend_magnitude = 0
            else:
                trend_direction = "UNKNOWN"
                trend_magnitude = 0
            
            return {
                "tool": self.name,
                "drug": drug,
                "reaction": reaction,
                "trend": trend_direction,
                "trend_magnitude": trend_magnitude,
                "total_count": len(df),
                "summary": f"Trend analysis: {trend_direction} ({trend_magnitude:.1%} change)"
            }
            
        except Exception as e:
            logger.error(f"Trend tool error: {e}")
            return {
                "tool": self.name,
                "error": str(e),
                "drug": drug,
                "reaction": reaction
            }

