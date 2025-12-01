"""
Population Subgroup Analysis Engine for Pharmacovigilance (CHUNK 6.11.8 + 6.11.11)
Provides subgroup-based trend analysis across age, sex, region, indication, dose, weight, onset time,
and concomitant drugs with statistical tests (chi-square, Fisher exact) and subgroup-specific PRR/ROR.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Optional statistical testing imports
try:
    from scipy.stats import chi2_contingency, fisher_exact
    STATS_AVAILABLE = True
except ImportError:
    STATS_AVAILABLE = False


class SubgroupEngine:
    """
    Statistical subgroup analysis engine for PV trend detection.
    Analyzes signals across demographic, geographic, and clinical subgroups.
    """

    def age_buckets(self, age):
        """Convert age to standardized buckets."""
        if pd.isna(age):
            return "Unknown"
        try:
            age = float(age)
            if age < 18: 
                return "<18"
            if age < 30: 
                return "18-29"
            if age < 45: 
                return "30-44"
            if age < 60: 
                return "45-59"
            if age < 75: 
                return "60-74"
            return "75+"
        except (ValueError, TypeError):
            return "Unknown"

    def weight_buckets(self, w):
        """Convert weight to standardized buckets."""
        if pd.isna(w): 
            return "Unknown"
        try:
            w = float(w)
            if w < 50: 
                return "<50kg"
            if w < 70: 
                return "50-69kg"
            if w < 90: 
                return "70-89kg"
            if w < 110: 
                return "90-109kg"
            return "110+ kg"
        except (ValueError, TypeError):
            return "Unknown"

    def onset_buckets(self, days):
        """Convert onset days to standardized buckets."""
        if pd.isna(days): 
            return "Unknown"
        try:
            d = float(days)
            if d <= 1: 
                return "≤1 day"
            if d <= 7: 
                return "2–7 days"
            if d <= 30: 
                return "8–30 days"
            return ">30 days"
        except (ValueError, TypeError):
            return "Unknown"
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column by possible names (case-insensitive)."""
        df_cols_lower = {col.lower(): col for col in df.columns}
        for name in possible_names:
            if name.lower() in df_cols_lower:
                return df_cols_lower[name.lower()]
        return None
    
    def _calculate_onset_days(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Calculate onset days from start_date and onset_date."""
        start_col = self._find_column(df, ["start_date", "start_dt", "drug_start_date"])
        onset_col = self._find_column(df, ["onset_date", "event_date", "onset_dt"])
        
        if not start_col or not onset_col:
            return None
        
        try:
            start_dates = pd.to_datetime(df[start_col], errors="coerce")
            onset_dates = pd.to_datetime(df[onset_col], errors="coerce")
            
            # Calculate difference in days
            diff = (onset_dates - start_dates).dt.days
            return diff
        except Exception:
            return None

    def analyze_subgroups(
        self, 
        df: pd.DataFrame, 
        drug: Optional[str] = None,
        reaction: Optional[str] = None,
        drug_col: str = "drug_name",
        reaction_col: str = "reaction"
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze subgroups across multiple dimensions (CHUNK 6.11.8).
        
        Returns distribution, reporting ratios, and anomalies per subgroup.
        
        Args:
            df: DataFrame with PV data
            drug: Drug name to filter (optional)
            reaction: Reaction name to filter (optional)
            drug_col: Drug column name
            reaction_col: Reaction column name
            
        Returns:
            Dictionary with subgroup analysis results or None if insufficient data
        """
        if df is None or len(df) == 0:
            return None

        filtered = df.copy()
        
        # Filter by drug if specified
        if drug:
            drug_col_actual = self._find_column(filtered, [drug_col, "drug_name", "drug"])
            if drug_col_actual:
                # Handle multi-value drug columns
                filtered = filtered[
                    filtered[drug_col_actual].astype(str).str.contains(str(drug), na=False, regex=False)
                ]
            else:
                return None
        
        # Filter by reaction if specified
        if reaction:
            reaction_col_actual = self._find_column(filtered, [reaction_col, "reaction", "reaction_pt"])
            if reaction_col_actual:
                # Handle multi-value reaction columns
                filtered = filtered[
                    filtered[reaction_col_actual].astype(str).str.contains(str(reaction), na=False, regex=False)
                ]
            else:
                return None

        if filtered.empty:
            return None

        # Prepare subgroup columns with flexible column detection
        # Age buckets
        age_col = self._find_column(filtered, ["age", "age_yrs", "age_years"])
        if age_col:
            filtered["age_bucket"] = filtered[age_col].apply(self.age_buckets)
        
        # Weight buckets
        weight_col = self._find_column(filtered, ["weight_kg", "weight", "wt", "patient_weight"])
        if weight_col:
            filtered["weight_bucket"] = filtered[weight_col].apply(self.weight_buckets)
        
        # Onset buckets
        onset_col = self._find_column(filtered, ["onset_days", "time_to_onset", "tto"])
        if not onset_col:
            # Try to calculate from dates
            onset_series = self._calculate_onset_days(filtered)
            if onset_series is not None:
                filtered["onset_days"] = onset_series
                filtered["onset_bucket"] = filtered["onset_days"].apply(self.onset_buckets)
        else:
            filtered["onset_bucket"] = filtered[onset_col].apply(self.onset_buckets)
        
        # Find region/country column
        region_col = self._find_column(filtered, ["region", "country", "country_code", "country_name"])
        
        # Find indication column
        indication_col = self._find_column(filtered, ["indication", "indi_pt", "indication_pt", "indication_name"])
        
        # Find dose column
        dose_col = self._find_column(filtered, ["dose_amt", "dose", "dose_amount", "dose_strength"])
        
        # Find sex/gender column
        sex_col = self._find_column(filtered, ["sex", "gender", "gndr_cod", "patient_sex"])

        subgroups = {}

        # Analyze across grouping dimensions
        subgroup_configs = [
            ("sex", sex_col),
            ("age_bucket", "age_bucket"),
            ("region", region_col),
            ("indication", indication_col),
            ("dose", dose_col),
            ("weight_bucket", "weight_bucket"),
            ("onset_bucket", "onset_bucket")
        ]

        for subgroup_name, col_name in subgroup_configs:
            # Skip if column not found
            if not col_name or col_name not in filtered.columns:
                continue
            
            try:
                # Get distribution
                dist_series = filtered.groupby(col_name).size().sort_values(ascending=False)
                dist = dist_series.to_dict()
                
                if len(dist) == 0:
                    continue
                
                # Calculate anomaly score: top group / second group (ratio)
                if len(dist) > 1:
                    vals = list(dist.values())
                    anomaly_score = float(vals[0] / (vals[1] + 1e-3))
                else:
                    anomaly_score = 1.0
                
                # Calculate percentage of total
                total_cases = len(filtered)
                top_group = list(dist.keys())[0]
                top_value = list(dist.values())[0]
                top_percentage = (top_value / total_cases * 100) if total_cases > 0 else 0
                
                subgroups[subgroup_name] = {
                    "distribution": {str(k): int(v) for k, v in dist.items()},  # JSON-serializable
                    "top_group": str(top_group),
                    "top_value": int(top_value),
                    "top_percentage": float(top_percentage),
                    "anomaly_score": float(anomaly_score),
                    "total_cases": int(total_cases)
                }
            except Exception:
                # Skip this subgroup if analysis fails
                continue

        return subgroups if subgroups else None
    
    def _calculate_subgroup_prr_ror(
        self,
        df: pd.DataFrame,
        drug: str,
        reaction: str,
        subgroup_filter: pd.Series,
        drug_col: str = "drug_name",
        reaction_col: str = "reaction"
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate PRR/ROR for a specific subgroup (CHUNK 6.11.11).
        
        Args:
            df: Full DataFrame
            drug: Drug name
            reaction: Reaction name
            subgroup_filter: Boolean series indicating subgroup membership
            drug_col: Drug column name
            reaction_col: Reaction column name
            
        Returns:
            Dictionary with PRR/ROR metrics for the subgroup or None
        """
        try:
            from src.signal_stats import calculate_prr_ror
            
            # Filter to subgroup
            subgroup_df = df[subgroup_filter]
            
            if len(subgroup_df) < 3:  # Need minimum cases
                return None
            
            # Calculate PRR/ROR for this subgroup
            prr_ror_result = calculate_prr_ror(drug, reaction, subgroup_df)
            
            return prr_ror_result
        except Exception:
            return None
    
    def _statistical_test_subgroup(
        self,
        df: pd.DataFrame,
        subgroup_col: str,
        subgroup_value: Any,
        drug: str,
        reaction: str,
        drug_col: str = "drug_name",
        reaction_col: str = "reaction"
    ) -> Optional[Dict[str, Any]]:
        """
        Perform chi-square and Fisher exact tests for subgroup (CHUNK 6.11.11).
        
        Tests: Is the drug-reaction signal significantly different in this subgroup vs. others?
        
        Args:
            df: DataFrame
            subgroup_col: Column name for subgroup (e.g., "age_bucket")
            subgroup_value: Value of subgroup (e.g., "45-59")
            drug: Drug name
            reaction: Reaction name
            drug_col: Drug column name
            reaction_col: Reaction column name
            
        Returns:
            Dictionary with test results or None
        """
        if not STATS_AVAILABLE:
            return None
        
        try:
            drug_col_actual = self._find_column(df, [drug_col, "drug_name", "drug"])
            reaction_col_actual = self._find_column(df, [reaction_col, "reaction", "reaction_pt"])
            
            if not drug_col_actual or not reaction_col_actual or subgroup_col not in df.columns:
                return None
            
            # Create binary masks
            drug_mask = df[drug_col_actual].astype(str).str.contains(str(drug), na=False, case=False)
            reaction_mask = df[reaction_col_actual].astype(str).str.contains(str(reaction), na=False, case=False)
            subgroup_mask = df[subgroup_col] == subgroup_value
            
            # Build 2x2 contingency table: [In Subgroup, Not In Subgroup] x [Drug+Reaction, Others]
            a = ((subgroup_mask) & (drug_mask) & (reaction_mask)).sum()  # In subgroup, drug+reaction
            b = ((subgroup_mask) & (drug_mask) & (~reaction_mask)).sum()  # In subgroup, drug only
            c = ((subgroup_mask) & (~drug_mask) & (reaction_mask)).sum()  # In subgroup, reaction only
            d = ((subgroup_mask) & (~drug_mask) & (~reaction_mask)).sum()  # In subgroup, neither
            
            e = ((~subgroup_mask) & (drug_mask) & (reaction_mask)).sum()  # Not in subgroup, drug+reaction
            f = ((~subgroup_mask) & (drug_mask) & (~reaction_mask)).sum()  # Not in subgroup, drug only
            g = ((~subgroup_mask) & (~drug_mask) & (reaction_mask)).sum()  # Not in subgroup, reaction only
            h = ((~subgroup_mask) & (~drug_mask) & (~reaction_mask)).sum()  # Not in subgroup, neither
            
            # 2x2 table: Subgroup vs Others for drug+reaction cases
            subgroup_drug_reaction = a
            subgroup_others = b + c + d
            others_drug_reaction = e
            others_others = f + g + h
            
            # Check if we have enough data
            if (subgroup_drug_reaction + subgroup_others < 5) or (others_drug_reaction + others_others < 5):
                return None
            
            contingency_table = np.array([
                [subgroup_drug_reaction, subgroup_others],
                [others_drug_reaction, others_others]
            ])
            
            # Chi-square test
            try:
                chi2, p_value_chi2, dof, expected = chi2_contingency(contingency_table)
            except Exception:
                chi2, p_value_chi2, dof, expected = None, None, None, None
            
            # Fisher exact test (for small samples)
            try:
                odds_ratio_fisher, p_value_fisher = fisher_exact(contingency_table)
            except Exception:
                odds_ratio_fisher, p_value_fisher = None, None
            
            # Calculate relative risk
            total_subgroup = subgroup_drug_reaction + subgroup_others
            total_others = others_drug_reaction + others_others
            
            risk_subgroup = subgroup_drug_reaction / total_subgroup if total_subgroup > 0 else 0
            risk_others = others_drug_reaction / total_others if total_others > 0 else 0
            
            relative_risk = risk_subgroup / (risk_others + 1e-6) if risk_others > 0 else None
            
            return {
                "chi2": float(chi2) if chi2 is not None else None,
                "p_value_chi2": float(p_value_chi2) if p_value_chi2 is not None else None,
                "degrees_of_freedom": int(dof) if dof is not None else None,
                "odds_ratio_fisher": float(odds_ratio_fisher) if odds_ratio_fisher is not None else None,
                "p_value_fisher": float(p_value_fisher) if p_value_fisher is not None else None,
                "relative_risk": float(relative_risk) if relative_risk is not None else None,
                "risk_subgroup": float(risk_subgroup),
                "risk_others": float(risk_others),
                "contingency_table": {
                    "subgroup": {"drug_reaction": int(subgroup_drug_reaction), "others": int(subgroup_others)},
                    "others": {"drug_reaction": int(others_drug_reaction), "others": int(others_others)}
                }
            }
        except Exception:
            return None
    
    def analyze_concomitant_drugs(
        self,
        df: pd.DataFrame,
        drug: str,
        reaction: Optional[str] = None,
        drug_col: str = "drug_name",
        reaction_col: str = "reaction"
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze concomitant drug patterns and potential drug-drug interactions (CHUNK 6.11.11).
        
        Args:
            df: DataFrame with PV data
            drug: Primary drug of interest
            reaction: Reaction of interest (optional)
            drug_col: Drug column name
            reaction_col: Reaction column name
            
        Returns:
            Dictionary with concomitant drug analysis results or None
        """
        if df is None or len(df) == 0:
            return None
        
        filtered = df.copy()
        
        # Filter by drug
        drug_col_actual = self._find_column(filtered, [drug_col, "drug_name", "drug"])
        if not drug_col_actual:
            return None
        
        filtered = filtered[
            filtered[drug_col_actual].astype(str).str.contains(str(drug), na=False, case=False)
        ]
        
        # Filter by reaction if specified
        if reaction:
            reaction_col_actual = self._find_column(filtered, [reaction_col, "reaction", "reaction_pt"])
            if reaction_col_actual:
                filtered = filtered[
                    filtered[reaction_col_actual].astype(str).str.contains(str(reaction), na=False, case=False)
                ]
        
        if filtered.empty:
            return None
        
        # Find concomitant drug column (could be in drug_name as multi-value, or separate column)
        # Strategy: If drug_name contains multiple drugs (separated by ; or ,), treat others as concomitants
        concomitant_drugs = []
        
        for idx, row in filtered.iterrows():
            drug_value = str(row.get(drug_col_actual, ""))
            if ";" in drug_value or "," in drug_value:
                # Split multi-value drug column
                drugs = [d.strip() for d in drug_value.replace(";", ",").split(",") if d.strip()]
                # Remove primary drug from list
                drugs = [d for d in drugs if str(drug).lower() not in d.lower()]
                concomitant_drugs.extend(drugs)
        
        # Also check for role_cod column (concomitant vs suspect)
        role_col = self._find_column(filtered, ["role_cod", "role_code", "drug_role"])
        if role_col:
            # Get drugs marked as concomitant (role_cod = "C" or "2")
            concomitant_rows = filtered[
                filtered[role_col].astype(str).str.upper().isin(["C", "2", "CONCOMITANT"])
            ]
            if not concomitant_rows.empty:
                # Extract drug names from these rows
                for idx, row in concomitant_rows.iterrows():
                    drug_value = str(row.get(drug_col_actual, ""))
                    if drug_value and drug_value.lower() != str(drug).lower():
                        concomitant_drugs.append(drug_value)
        
        if not concomitant_drugs:
            return None
        
        # Count concomitant drugs
        from collections import Counter
        concomitant_counts = Counter(concomitant_drugs)
        top_concomitants = dict(concomitant_counts.most_common(10))
        
        # Calculate interaction ratios (cases with concomitant vs without)
        cases_with_concomitant = len(filtered[filtered[drug_col_actual].astype(str).str.contains(";|,", na=False, regex=True)])
        cases_without_concomitant = len(filtered) - cases_with_concomitant
        
        return {
            "top_concomitants": {str(k): int(v) for k, v in top_concomitants.items()},
            "total_concomitant_drugs": len(concomitant_counts),
            "cases_with_concomitant": int(cases_with_concomitant),
            "cases_without_concomitant": int(cases_without_concomitant),
            "concomitant_ratio": float(cases_with_concomitant / len(filtered)) if len(filtered) > 0 else 0.0
        }
    
    def analyze_subgroups_enhanced(
        self,
        df: pd.DataFrame,
        drug: Optional[str] = None,
        reaction: Optional[str] = None,
        drug_col: str = "drug_name",
        reaction_col: str = "reaction",
        include_statistical_tests: bool = True,
        include_subgroup_prr_ror: bool = True,
        include_concomitants: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Enhanced subgroup analysis with statistical tests and PRR/ROR (CHUNK 6.11.11).
        
        Args:
            df: DataFrame with PV data
            drug: Drug name to filter (optional)
            reaction: Reaction name to filter (optional)
            drug_col: Drug column name
            reaction_col: Reaction column name
            include_statistical_tests: If True, perform chi-square and Fisher exact tests
            include_subgroup_prr_ror: If True, calculate PRR/ROR per subgroup
            include_concomitants: If True, analyze concomitant drugs
            
        Returns:
            Enhanced dictionary with statistical tests and PRR/ROR per subgroup
        """
        # Start with basic subgroup analysis
        basic_subgroups = self.analyze_subgroups(df, drug, reaction, drug_col, reaction_col)
        
        if not basic_subgroups:
            return None
        
        # Enhance with statistical tests and PRR/ROR
        enhanced_subgroups = {}
        
        for subgroup_name, subgroup_data in basic_subgroups.items():
            enhanced_data = subgroup_data.copy()
            
            # Add statistical tests for top subgroup
            if include_statistical_tests and drug and reaction:
                top_group = subgroup_data.get("top_group")
                col_name = None
                
                # Find the column name for this subgroup
                if subgroup_name == "age_bucket":
                    col_name = "age_bucket"
                elif subgroup_name == "sex":
                    col_name = self._find_column(df, ["sex", "gender", "gndr_cod", "patient_sex"])
                elif subgroup_name == "region":
                    col_name = self._find_column(df, ["region", "country", "country_code", "country_name"])
                elif subgroup_name == "indication":
                    col_name = self._find_column(df, ["indication", "indi_pt", "indication_pt", "indication_name"])
                else:
                    col_name = subgroup_name
                
                if col_name and col_name in df.columns:
                    stat_test_result = self._statistical_test_subgroup(
                        df, col_name, top_group, drug, reaction, drug_col, reaction_col
                    )
                    if stat_test_result:
                        enhanced_data["statistical_tests"] = stat_test_result
            
            # Add subgroup-specific PRR/ROR
            if include_subgroup_prr_ror and drug and reaction:
                col_name = None
                if subgroup_name == "age_bucket":
                    col_name = "age_bucket"
                elif subgroup_name == "sex":
                    col_name = self._find_column(df, ["sex", "gender", "gndr_cod", "patient_sex"])
                elif subgroup_name == "region":
                    col_name = self._find_column(df, ["region", "country", "country_code", "country_name"])
                elif subgroup_name == "indication":
                    col_name = self._find_column(df, ["indication", "indi_pt", "indication_pt", "indication_name"])
                else:
                    col_name = subgroup_name
                
                if col_name and col_name in df.columns:
                    top_group = subgroup_data.get("top_group")
                    subgroup_filter = df[col_name] == top_group
                    
                    prr_ror_result = self._calculate_subgroup_prr_ror(
                        df, drug, reaction, subgroup_filter, drug_col, reaction_col
                    )
                    if prr_ror_result:
                        enhanced_data["subgroup_prr_ror"] = {
                            "prr": prr_ror_result.get("prr"),
                            "ror": prr_ror_result.get("ror"),
                            "prr_ci_lower": prr_ror_result.get("prr_ci_lower"),
                            "prr_ci_upper": prr_ror_result.get("prr_ci_upper"),
                            "ror_ci_lower": prr_ror_result.get("ror_ci_lower"),
                            "ror_ci_upper": prr_ror_result.get("ror_ci_upper"),
                            "p_value": prr_ror_result.get("p_value")
                        }
            
            enhanced_subgroups[subgroup_name] = enhanced_data
        
        # Add concomitant drug analysis
        result = {
            "subgroups": enhanced_subgroups
        }
        
        if include_concomitants and drug:
            concomitant_result = self.analyze_concomitant_drugs(
                df, drug, reaction, drug_col, reaction_col
            )
            if concomitant_result:
                result["concomitants"] = concomitant_result
        
        return result
