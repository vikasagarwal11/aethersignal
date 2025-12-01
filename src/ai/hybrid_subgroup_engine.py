"""
Hybrid Subgroup Engine (CHUNK 7.4.3)
Local compute for subgroup analysis + Server AI for interpretation.
Provides sex-specific, age-specific, weight/BMI, pregnancy/lactation, geriatric/pediatric risk scoring.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json

try:
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


def compute_local_subgroups(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute subgroup analysis entirely locally (fast, no LLM).
    
    Analyzes:
    - Sex-specific risk scoring
    - Age-specific risk scoring (Pediatric, Adult, Middle-aged, Elderly)
    - Weight/BMI risk scoring
    - Pregnancy/lactation risk scoring
    - Geriatric subgroup risk
    - Pediatric subgroup risk
    - Therapy-duration subgroup risk
    - Dose-level subgroup risk
    
    Args:
        df: Safety data DataFrame with required columns
        
    Returns:
        Dictionary with all subgroup analysis results
    """
    if df is None or df.empty:
        return {}
    
    subgroups = {}
    
    # Find key columns
    drug_col = next((col for col in ["drug_normalized", "drug_name", "drug"] if col in df.columns), None)
    reaction_col = next((col for col in ["reaction_normalized", "reaction_pt", "reaction"] if col in df.columns), None)
    case_col = next((col for col in ["primaryid", "caseid", "case_id", "id"] if col in df.columns), None)
    
    if not all([drug_col, reaction_col, case_col]):
        return {}
    
    # 1. Sex-specific risk scoring
    if "sex" in df.columns or "gender" in df.columns:
        sex_col = "sex" if "sex" in df.columns else "gender"
        sex_counts = df.groupby([drug_col, sex_col])[case_col].count().reset_index()
        sex_counts.columns = ["drug", "sex", "count"]
        subgroups["sex"] = sex_counts.to_dict("records")
        
        # Calculate sex-specific risk ratios
        sex_risk_ratios = []
        for drug in df[drug_col].unique():
            drug_df = df[df[drug_col] == drug]
            sex_dist = drug_df[sex_col].value_counts()
            if len(sex_dist) >= 2:
                # Simple ratio: most common / least common
                max_sex = sex_dist.idxmax()
                min_sex = sex_dist.idxmin()
                ratio = sex_dist[max_sex] / max(sex_dist[min_sex], 1)
                sex_risk_ratios.append({
                    "drug": drug,
                    "higher_risk_sex": max_sex,
                    "risk_ratio": round(ratio, 2)
                })
        subgroups["sex_risk_ratios"] = sex_risk_ratios
    
    # 2. Age-specific risk scoring
    age_col = next((col for col in ["age", "age_yrs", "age_years", "age_cod"] if col in df.columns), None)
    if age_col and age_col in df.columns:
        # Convert age to numeric if possible
        df_age = df.copy()
        df_age["age_numeric"] = pd.to_numeric(df_age[age_col], errors="coerce")
        df_age = df_age.dropna(subset=["age_numeric"])
        
        if not df_age.empty:
            # Age groups: Pediatric (0-17), Adult (18-40), Middle-aged (41-64), Elderly (65+)
            df_age["age_group"] = pd.cut(
                df_age["age_numeric"],
                bins=[0, 17, 40, 64, 120],
                labels=["Pediatric", "Adult", "Middle-aged", "Elderly"],
                include_lowest=True
            )
            
            age_counts = df_age.groupby([drug_col, "age_group"])[case_col].count().reset_index()
            age_counts.columns = ["drug", "age_group", "count"]
            subgroups["age"] = age_counts.to_dict("records")
            
            # Calculate age-specific risk (elderly vs. adult)
            age_risk_analysis = []
            for drug in df_age[drug_col].unique():
                drug_age_df = df_age[df_age[drug_col] == drug]
                age_dist = drug_age_df["age_group"].value_counts()
                if "Elderly" in age_dist.index and "Adult" in age_dist.index:
                    elderly_count = age_dist["Elderly"]
                    adult_count = age_dist["Adult"]
                    if adult_count > 0:
                        risk_ratio = elderly_count / adult_count
                        age_risk_analysis.append({
                            "drug": drug,
                            "elderly_to_adult_ratio": round(risk_ratio, 2),
                            "elderly_risk": "Higher" if risk_ratio > 1.5 else "Similar" if risk_ratio > 0.67 else "Lower"
                        })
            subgroups["age_risk_analysis"] = age_risk_analysis
    
    # 3. Weight/BMI risk scoring
    weight_col = next((col for col in ["wt", "weight", "weight_kg", "weight_cod"] if col in df.columns), None)
    if weight_col and weight_col in df.columns:
        df_weight = df.copy()
        df_weight["weight_numeric"] = pd.to_numeric(df_weight[weight_col], errors="coerce")
        df_weight = df_weight.dropna(subset=["weight_numeric"])
        
        if not df_weight.empty:
            # Weight groups: Underweight (<50kg), Normal (50-80kg), Overweight (80-100kg), Obese (>100kg)
            df_weight["weight_group"] = pd.cut(
                df_weight["weight_numeric"],
                bins=[0, 50, 80, 100, 500],
                labels=["Underweight", "Normal", "Overweight", "Obese"],
                include_lowest=True
            )
            
            weight_counts = df_weight.groupby([drug_col, "weight_group"])[case_col].count().reset_index()
            weight_counts.columns = ["drug", "weight_group", "count"]
            subgroups["weight"] = weight_counts.to_dict("records")
    
    # 4. Pregnancy/lactation risk scoring
    if "preg" in df.columns or "pregnancy" in df.columns:
        preg_col = "preg" if "preg" in df.columns else "pregnancy"
        preg_counts = df.groupby([drug_col, preg_col])[case_col].count().reset_index()
        preg_counts.columns = ["drug", "pregnancy_status", "count"]
        subgroups["pregnancy"] = preg_counts.to_dict("records")
    
    # 5. Therapy-duration subgroup risk
    if "therapy_duration_days" in df.columns:
        df_therapy = df.copy()
        df_therapy["therapy_duration_numeric"] = pd.to_numeric(
            df_therapy["therapy_duration_days"], errors="coerce"
        )
        df_therapy = df_therapy.dropna(subset=["therapy_duration_numeric"])
        
        if not df_therapy.empty:
            # Duration groups: Short (<30 days), Medium (30-90 days), Long (>90 days)
            df_therapy["duration_group"] = pd.cut(
                df_therapy["therapy_duration_numeric"],
                bins=[0, 30, 90, 10000],
                labels=["Short-term", "Medium-term", "Long-term"],
                include_lowest=True
            )
            
            duration_counts = df_therapy.groupby([drug_col, "duration_group"])[case_col].count().reset_index()
            duration_counts.columns = ["drug", "duration_group", "count"]
            subgroups["therapy_duration"] = duration_counts.to_dict("records")
            
            # Median therapy duration per drug
            duration_median = df_therapy.groupby(drug_col)["therapy_duration_numeric"].median().reset_index()
            duration_median.columns = ["drug", "median_duration_days"]
            subgroups["therapy_duration_median"] = duration_median.to_dict("records")
    
    # 6. Dose-level subgroup risk
    dose_col = next((col for col in ["dose_amt", "dose", "dose_amt_num"] if col in df.columns), None)
    if dose_col and dose_col in df.columns:
        df_dose = df.copy()
        df_dose["dose_numeric"] = pd.to_numeric(df_dose[dose_col], errors="coerce")
        df_dose = df_dose.dropna(subset=["dose_numeric"])
        
        if not df_dose.empty:
            # Dose quartiles
            dose_quartiles = df_dose["dose_numeric"].quantile([0.25, 0.5, 0.75])
            if len(dose_quartiles) >= 3:
                df_dose["dose_group"] = pd.cut(
                    df_dose["dose_numeric"],
                    bins=[0, dose_quartiles[0.25], dose_quartiles[0.5], dose_quartiles[0.75], 100000],
                    labels=["Low", "Medium-Low", "Medium-High", "High"],
                    include_lowest=True
                )
                
                dose_counts = df_dose.groupby([drug_col, "dose_group"])[case_col].count().reset_index()
                dose_counts.columns = ["drug", "dose_group", "count"]
                subgroups["dose"] = dose_counts.to_dict("records")
    
    # 7. Geriatric-specific risk (age 65+)
    if age_col and age_col in df.columns:
        df_age = df.copy()
        df_age["age_numeric"] = pd.to_numeric(df_age[age_col], errors="coerce")
        geriatric_df = df_age[df_age["age_numeric"] >= 65]
        
        if not geriatric_df.empty:
            geriatric_counts = geriatric_df.groupby([drug_col, reaction_col])[case_col].count().reset_index()
            geriatric_counts.columns = ["drug", "reaction", "count"]
            subgroups["geriatric_signals"] = geriatric_counts.to_dict("records")
    
    # 8. Pediatric-specific risk (age <18)
    if age_col and age_col in df.columns:
        df_age = df.copy()
        df_age["age_numeric"] = pd.to_numeric(df_age[age_col], errors="coerce")
        pediatric_df = df_age[df_age["age_numeric"] < 18]
        
        if not pediatric_df.empty:
            pediatric_counts = pediatric_df.groupby([drug_col, reaction_col])[case_col].count().reset_index()
            pediatric_counts.columns = ["drug", "reaction", "count"]
            subgroups["pediatric_signals"] = pediatric_counts.to_dict("records")
    
    return subgroups


def hybrid_subgroup_interpretation(
    local_subgroups: Dict[str, Any],
    signal_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate AI-powered interpretation of subgroup analysis.
    
    Args:
        local_subgroups: Subgroup analysis results from compute_local_subgroups()
        signal_context: Optional signal-specific context
        
    Returns:
        AI-generated interpretation narrative
    """
    if not local_subgroups:
        return "No subgroup analysis data available for interpretation."
    
    if not LLM_AVAILABLE:
        return _generate_fallback_interpretation(local_subgroups)
    
    prompt = f"""
    You are a pharmacovigilance safety scientist analyzing subgroup safety signals.
    
    Subgroup Analysis Results:
    {json.dumps(local_subgroups, indent=2, default=str)}
    
    Signal Context:
    {json.dumps(signal_context or {}, indent=2, default=str)}
    
    Provide a comprehensive, regulatory-ready interpretation covering:
    
    1. **Key Subgroup Differentials**: Identify which subgroups show higher risk (sex, age, weight, dose, duration)
    
    2. **High-Risk Population Signals**: Highlight any populations that show significantly elevated risk
    
    3. **Dose/Therapy-Duration Concerns**: Analyze if higher doses or longer therapy duration correlates with increased risk
    
    4. **Geriatric/Pediatric Considerations**: Assess age-specific risk patterns
    
    5. **Regulatory Considerations**: Identify any findings that may require:
       - Labeling updates
       - Risk minimization measures
       - Additional monitoring
       - Regulatory reporting
    
    6. **Monitoring Recommendations**: Suggest specific monitoring strategies for high-risk subgroups
    
    Maintain a professional, evidence-based tone suitable for regulatory documentation.
    """
    
    system_prompt = "You are a senior pharmacovigilance safety scientist specializing in subgroup analysis and population-specific risk assessment."
    
    try:
        interpretation = call_medical_llm(
            prompt,
            system_prompt,
            task_type="general",
            max_tokens=1500,
            temperature=0.3
        )
        return interpretation if interpretation else _generate_fallback_interpretation(local_subgroups)
    except Exception:
        return _generate_fallback_interpretation(local_subgroups)


def _generate_fallback_interpretation(local_subgroups: Dict[str, Any]) -> str:
    """Generate fallback interpretation if LLM unavailable."""
    interpretation = "Subgroup Analysis Summary:\n\n"
    
    if "sex_risk_ratios" in local_subgroups:
        interpretation += "Sex-Specific Risk:\n"
        for ratio in local_subgroups["sex_risk_ratios"][:5]:
            interpretation += f"- {ratio.get('drug', 'Unknown')}: Higher risk in {ratio.get('higher_risk_sex', 'N/A')} (ratio: {ratio.get('risk_ratio', 0)})\n"
        interpretation += "\n"
    
    if "age_risk_analysis" in local_subgroups:
        interpretation += "Age-Specific Risk:\n"
        for analysis in local_subgroups["age_risk_analysis"][:5]:
            interpretation += f"- {analysis.get('drug', 'Unknown')}: Elderly risk {analysis.get('elderly_risk', 'N/A')} (ratio: {analysis.get('elderly_to_adult_ratio', 0)})\n"
        interpretation += "\n"
    
    if "geriatric_signals" in local_subgroups:
        interpretation += f"Geriatric Signals: {len(local_subgroups['geriatric_signals'])} signals identified in patients 65+\n"
    
    if "pediatric_signals" in local_subgroups:
        interpretation += f"Pediatric Signals: {len(local_subgroups['pediatric_signals'])} signals identified in patients <18\n"
    
    return interpretation


def compute_subgroup_risk_scores(subgroups: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute quantitative risk scores for each subgroup dimension.
    
    Args:
        subgroups: Subgroup analysis results
        
    Returns:
        Dictionary with risk scores (0-100) for each subgroup category
    """
    risk_scores = {}
    
    # Sex risk score (based on ratio magnitude)
    if "sex_risk_ratios" in subgroups:
        max_ratio = max([r.get("risk_ratio", 1) for r in subgroups["sex_risk_ratios"]], default=1)
        risk_scores["sex_differential"] = min(100, int(max_ratio * 20))  # Scale to 0-100
    
    # Age risk score
    if "age_risk_analysis" in subgroups:
        max_age_ratio = max([a.get("elderly_to_adult_ratio", 1) for a in subgroups["age_risk_analysis"]], default=1)
        risk_scores["age_differential"] = min(100, int(max_age_ratio * 25))
    
    # Geriatric risk score
    if "geriatric_signals" in subgroups:
        geriatric_count = len(subgroups["geriatric_signals"])
        risk_scores["geriatric_risk"] = min(100, geriatric_count * 2)
    
    # Pediatric risk score
    if "pediatric_signals" in subgroups:
        pediatric_count = len(subgroups["pediatric_signals"])
        risk_scores["pediatric_risk"] = min(100, pediatric_count * 2)
    
    return risk_scores
