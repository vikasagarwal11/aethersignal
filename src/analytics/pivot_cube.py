"""
PivotCube Engine (Phase 3B.1)
In-memory OLAP-style cube for multi-dimensional AE analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from src.storage.federated_query_engine import FederatedQueryEngine

logger = logging.getLogger(__name__)


class PivotCube:
    """
    Multi-dimensional pivot cube for AE analysis.
    
    Dimensions:
    - Drug, Reaction, Source, Severity, Seriousness, Outcome
    - Region, Age group, Sex, Event date, Cluster ID
    - SOC → HLT → PT hierarchy, Drug class/group, Platform
    - Novelty bucket
    
    Measures:
    - AE count, Unique patient/post count, Trend % change
    - Burst score, Quantum score, Consensus score
    - Literature support, Label support, Social signal strength
    - Time-to-onset stats, Multi-AE co-reporting rate
    """
    
    def __init__(self, query_engine: FederatedQueryEngine):
        """
        Initialize pivot cube.
        
        Args:
            query_engine: Federated query engine for data access
        """
        self.query_engine = query_engine
        self.cube_data: Optional[pd.DataFrame] = None
        self.dimensions = {
            "drug": "drug_normalized",
            "reaction": "reaction_normalized",
            "source": "source",
            "severity": "reaction_severity_score",
            "seriousness": "serious",
            "outcome": "outcome",
            "region": "country",
            "age_group": "age_group",
            "sex": "sex",
            "event_date": "event_date",
            "cluster_id": "reaction_cluster_id",
            "drug_group": "drug_group",
            "novelty": "reaction_novelty_score"
        }
        self.measures = {
            "ae_count": "count",
            "quantum_score": "quantum_score",
            "burst_score": "burst_score",
            "consensus_score": "consensus_score",
            "literature_support": "literature_support",
            "label_support": "label_support",
            "social_support": "social_support"
        }
    
    def build_cube(
        self,
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> pd.DataFrame:
        """
        Build pivot cube from query engine.
        
        Args:
            filters: Optional filters (drug, reaction, source, etc.)
            date_range: Optional date range
        
        Returns:
            DataFrame with cube data
        """
        # Query data
        df = self.query_engine.query(
            drug=filters.get("drug") if filters else None,
            reaction=filters.get("reaction") if filters else None,
            sources=filters.get("sources") if filters else None,
            date_range=date_range,
            limit=100000  # Large limit for cube
        )
        
        if df.empty:
            return pd.DataFrame()
        
        # Add computed dimensions
        df = self._add_computed_dimensions(df)
        
        # Add computed measures
        df = self._add_computed_measures(df)
        
        self.cube_data = df
        return df
    
    def _add_computed_dimensions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add computed dimensions to dataframe."""
        df = df.copy()
        
        # Age group
        if "age" in df.columns:
            df["age_group"] = df["age"].apply(self._categorize_age)
        
        # Severity bucket
        if "reaction_severity_score" in df.columns:
            df["severity_bucket"] = df["reaction_severity_score"].apply(self._categorize_severity)
        
        # Novelty bucket
        if "reaction_novelty_score" in df.columns:
            df["novelty_bucket"] = df["reaction_novelty_score"].apply(self._categorize_novelty)
        
        # Date dimensions
        if "event_date" in df.columns:
            df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
            df["year"] = df["event_date"].dt.year
            df["month"] = df["event_date"].dt.month
            df["quarter"] = df["event_date"].dt.quarter
            df["week"] = df["event_date"].dt.isocalendar().week
        
        return df
    
    def _add_computed_measures(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add computed measures to dataframe."""
        df = df.copy()
        
        # Trend % change (if we have historical data)
        # This would require comparing with previous period
        # For now, we'll compute it based on date grouping
        
        return df
    
    def _categorize_age(self, age: Any) -> str:
        """Categorize age into groups."""
        if pd.isna(age):
            return "unknown"
        
        try:
            age_num = float(age)
            if age_num < 18:
                return "pediatric"
            elif age_num < 65:
                return "adult"
            else:
                return "elderly"
        except (ValueError, TypeError):
            return "unknown"
    
    def _categorize_severity(self, score: Any) -> str:
        """Categorize severity score into bucket."""
        if pd.isna(score):
            return "unknown"
        
        try:
            score_num = float(score)
            if score_num >= 0.8:
                return "severe"
            elif score_num >= 0.5:
                return "moderate"
            elif score_num >= 0.2:
                return "mild"
            else:
                return "minimal"
        except (ValueError, TypeError):
            return "unknown"
    
    def _categorize_novelty(self, score: Any) -> str:
        """Categorize novelty score into bucket."""
        if pd.isna(score):
            return "unknown"
        
        try:
            score_num = float(score)
            if score_num >= 0.8:
                return "highly_novel"
            elif score_num >= 0.6:
                return "novel"
            elif score_num >= 0.4:
                return "moderately_novel"
            else:
                return "known"
        except (ValueError, TypeError):
            return "unknown"
    
    def pivot(
        self,
        index: List[str],
        columns: Optional[List[str]] = None,
        values: Optional[List[str]] = None,
        aggfunc: str = "count"
    ) -> pd.DataFrame:
        """
        Create pivot table from cube.
        
        Args:
            index: List of dimension columns for rows
            columns: Optional list of dimension columns for columns
            values: Optional list of measure columns
            aggfunc: Aggregation function (count, sum, mean, etc.)
        
        Returns:
            Pivoted DataFrame
        """
        if self.cube_data is None or self.cube_data.empty:
            return pd.DataFrame()
        
        df = self.cube_data.copy()
        
        # Default values to count
        if values is None:
            values = ["ae_id"] if "ae_id" in df.columns else [df.columns[0]]
        
        # Create pivot
        if columns:
            pivot = pd.pivot_table(
                df,
                index=index,
                columns=columns,
                values=values[0] if len(values) == 1 else values,
                aggfunc=aggfunc,
                fill_value=0
            )
        else:
            # Group by index only
            if aggfunc == "count":
                pivot = df.groupby(index).size().reset_index(name="count")
            elif aggfunc == "sum":
                pivot = df.groupby(index)[values].sum().reset_index()
            elif aggfunc == "mean":
                pivot = df.groupby(index)[values].mean().reset_index()
            else:
                pivot = df.groupby(index)[values].agg(aggfunc).reset_index()
        
        return pivot
    
    def drill_down(
        self,
        filters: Dict[str, Any],
        level: str = "detail"
    ) -> pd.DataFrame:
        """
        Drill down into cube data.
        
        Args:
            filters: Filters to apply (e.g., {"drug": "semaglutide", "reaction": "nausea"})
            level: Detail level (summary, detail, raw)
        
        Returns:
            Filtered DataFrame
        """
        if self.cube_data is None or self.cube_data.empty:
            return pd.DataFrame()
        
        df = self.cube_data.copy()
        
        # Apply filters
        for key, value in filters.items():
            if key in df.columns:
                if isinstance(value, list):
                    df = df[df[key].isin(value)]
                else:
                    df = df[df[key] == value]
        
        # Return appropriate level
        if level == "summary":
            # Return aggregated summary
            return df.groupby(["drug_normalized", "reaction_normalized"]).agg({
                "ae_id": "count",
                "quantum_score": "mean",
                "reaction_severity_score": "mean"
            }).reset_index()
        elif level == "detail":
            # Return detailed records
            return df[["drug_normalized", "reaction_normalized", "source", 
                      "event_date", "quantum_score", "reaction_severity_score"]].copy()
        else:  # raw
            # Return all columns
            return df
    
    def get_trend(
        self,
        drug: Optional[str] = None,
        reaction: Optional[str] = None,
        period: str = "month"
    ) -> pd.DataFrame:
        """
        Get trend data for drug-reaction pair.
        
        Args:
            drug: Optional drug filter
            reaction: Optional reaction filter
            period: Period grouping (day, week, month, quarter, year)
        
        Returns:
            DataFrame with trend data
        """
        if self.cube_data is None or self.cube_data.empty:
            return pd.DataFrame()
        
        df = self.cube_data.copy()
        
        # Apply filters
        if drug:
            df = df[df["drug_normalized"].str.contains(drug, case=False, na=False)]
        if reaction:
            df = df[df["reaction_normalized"] == reaction]
        
        # Group by period
        if period == "day" and "event_date" in df.columns:
            df["period"] = df["event_date"].dt.date
        elif period == "week" and "week" in df.columns:
            df["period"] = df["year"].astype(str) + "-W" + df["week"].astype(str)
        elif period == "month" and "month" in df.columns:
            df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
        elif period == "quarter" and "quarter" in df.columns:
            df["period"] = df["year"].astype(str) + "-Q" + df["quarter"].astype(str)
        elif period == "year" and "year" in df.columns:
            df["period"] = df["year"].astype(str)
        else:
            return pd.DataFrame()
        
        # Aggregate
        trend = df.groupby("period").agg({
            "ae_id": "count",
            "quantum_score": "mean",
            "reaction_severity_score": "mean"
        }).reset_index()
        
        trend.columns = ["period", "count", "avg_quantum_score", "avg_severity"]
        
        return trend
    
    def get_cross_source_comparison(
        self,
        drug: str,
        reaction: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get cross-source comparison for drug-reaction pair.
        
        Args:
            drug: Drug name
            reaction: Optional reaction filter
        
        Returns:
            DataFrame with source breakdown
        """
        if self.cube_data is None or self.cube_data.empty:
            return pd.DataFrame()
        
        df = self.cube_data.copy()
        
        # Filter
        df = df[df["drug_normalized"].str.contains(drug, case=False, na=False)]
        if reaction:
            df = df[df["reaction_normalized"] == reaction]
        
        if df.empty or "source" not in df.columns:
            return pd.DataFrame()
        
        # Group by source
        comparison = df.groupby("source").agg({
            "ae_id": "count",
            "quantum_score": "mean",
            "reaction_severity_score": "mean",
            "consensus_score": "mean",
            "literature_support": "mean",
            "social_support": "mean"
        }).reset_index()
        
        comparison.columns = [
            "source", "case_count", "avg_quantum_score", "avg_severity",
            "avg_consensus", "avg_literature_support", "avg_social_support"
        ]
        
        # Calculate trend (if we have date data)
        if "event_date" in df.columns:
            df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
            recent = df[df["event_date"] >= datetime.now() - timedelta(days=30)]
            comparison["recent_30d"] = recent.groupby("source").size()
            comparison["trend"] = (comparison["recent_30d"] / comparison["case_count"] * 100).fillna(0)
        
        return comparison

