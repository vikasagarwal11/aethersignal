"""
Medical LLM Integration for AetherSignal
Provides unified interface for medical-specialized LLM models.

Supports:
- OpenAI (GPT-4o-mini, GPT-4o) - Primary, cost-effective
- Claude (Opus, Sonnet) - Best for causal reasoning
- BioGPT/Palmyra-Med - Best for biomedical literature
- Extensible architecture for future models
"""

from typing import Dict, Optional, List, Any
import os
import json


def get_available_models() -> Dict[str, List[str]]:
    """
    Get list of available models based on API keys.
    
    Returns:
        Dictionary mapping provider to available models
    """
    available = {}
    
    # Check OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        available["openai"] = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
    
    # Check Anthropic (Claude)
    if os.environ.get("ANTHROPIC_API_KEY"):
        available["anthropic"] = ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
    
    # Check Groq (fast inference, not BioGPT)
    if os.environ.get("GROQ_API_KEY"):
        available["groq"] = ["llama-3.1-70b-versatile", "mixtral-8x7b"]
    
    # Check Hugging Face (for BioGPT and other models)
    if os.environ.get("HUGGINGFACEHUB_API_TOKEN") or os.environ.get("HF_API_KEY"):
        available["huggingface"] = ["microsoft/biogpt", "microsoft/BioGPT-Large"]
    
    # Check Writer (Palmyra-Med)
    if os.environ.get("WRITER_API_KEY"):
        available["writer"] = ["palmyra-med-70b"]
    
    # Check xAI (Grok)
    if os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY"):
        available["xai"] = ["grok-2-1212", "grok-beta", "grok-2-vision-1212"]
    
    return available


def call_medical_llm(
    prompt: str,
    system_prompt: str,
    task_type: str = "general",
    preferred_model: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.3
) -> Optional[str]:
    """
    Unified interface for calling medical LLM models.
    
    Task-specific model selection:
    - "literature": BioGPT/Palmyra-Med preferred, OpenAI fallback
    - "causal_reasoning": Claude Opus preferred, GPT-4o fallback
    - "narrative_analysis": GPT-4o preferred, GPT-4o-mini fallback
    - "meddra_mapping": GPT-4o-mini (cost-effective)
    - "general": GPT-4o-mini (default)
    
    Args:
        prompt: User prompt
        system_prompt: System prompt
        task_type: Type of task (affects model selection)
        preferred_model: Override model selection (format: "provider:model")
        max_tokens: Maximum tokens to generate
        temperature: Temperature (0-1)
        
    Returns:
        Generated text or None if all models fail
    """
    available = get_available_models()
    
    # Determine model priority based on task
    if task_type == "causal_reasoning":
        # Best: Claude Opus, Fallback: GPT-4o, GPT-4o-mini
        model_chain = [
            ("anthropic", "claude-3-opus"),
            ("openai", "gpt-4o"),
            ("openai", "gpt-4o-mini"),
        ]
    elif task_type == "literature":
        # Best: Palmyra-Med, BioGPT (via Hugging Face), Grok, Fallback: GPT-4o, GPT-4o-mini
        model_chain = [
            ("writer", "palmyra-med-70b"),
            ("huggingface", "microsoft/biogpt"),  # BioGPT via Hugging Face
            ("xai", "grok-2-1212"),  # Grok for literature
            ("openai", "gpt-4o"),
            ("openai", "gpt-4o-mini"),
        ]
    elif task_type == "narrative_analysis":
        # Best: GPT-4o, Fallback: GPT-4o-mini, Claude Sonnet
        model_chain = [
            ("openai", "gpt-4o"),
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-sonnet"),
        ]
    else:
        # General: GPT-4o-mini (cost-effective)
        model_chain = [
            ("openai", "gpt-4o-mini"),
            ("openai", "gpt-4o"),
        ]
    
    # Override if preferred_model specified
    if preferred_model:
        provider, model = preferred_model.split(":", 1)
        model_chain = [(provider, model)] + [m for m in model_chain if m != (provider, model)]
    
    # Try each model in priority order
    for provider, model in model_chain:
        if provider not in available or model not in available[provider]:
            continue
        
        try:
            if provider == "openai":
                result = _call_openai(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "anthropic":
                result = _call_anthropic(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "groq":
                result = _call_groq(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "writer":
                result = _call_writer(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "xai":
                result = _call_xai(prompt, system_prompt, model, max_tokens, temperature)
            elif provider == "huggingface":
                result = _call_huggingface(prompt, system_prompt, model, max_tokens, temperature)
            else:
                continue
            
            if result:
                return result
        except Exception:
            continue  # Try next model
    
    return None


def _call_openai(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=30.0)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return response.choices[0].message.content
    except Exception:
        return None


def _call_anthropic(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Anthropic (Claude) API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key, timeout=60.0)
        
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        return response.content[0].text if response.content else None
    except Exception:
        return None


def _call_groq(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Groq API (for BioGPT alternatives)."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key, timeout=30.0)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return response.choices[0].message.content
    except Exception:
        return None


def _call_writer(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Writer API (Palmyra-Med)."""
    api_key = os.environ.get("WRITER_API_KEY")
    if not api_key:
        return None
    
    try:
        import requests
        
        # Writer API endpoint (example - adjust based on actual API)
        url = "https://api.writer.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        pass
    
    return None


def _call_xai(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call xAI (Grok) API."""
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not api_key:
        return None
    
    try:
        import requests
        
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        pass
    
    return None


def _call_huggingface(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Hugging Face Inference API (for BioGPT and other models)."""
    api_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN") or os.environ.get("HF_API_KEY")
    if not api_token:
        return None
    
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(token=api_token, timeout=30.0)
        
        # Combine system prompt and user prompt
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        # Use text generation for BioGPT
        response = client.text_generation(
            full_prompt,
            model=model,
            max_new_tokens=max_tokens,
            temperature=temperature,
            return_full_text=False  # Don't repeat the prompt
        )
        
        return response.strip() if response else None
    except Exception:
        # Fallback: try requests-based API if huggingface_hub not available
        try:
            import requests
            
            url = f"https://api-inference.huggingface.co/models/{model}"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            data = {
                "inputs": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "return_full_text": False
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").strip()
                elif isinstance(result, dict):
                    return result.get("generated_text", "").strip()
        except Exception:
            pass
    
    return None


# =========================================================
# CHUNK 6.11.8: Subgroup Interpretation
# =========================================================

def interpret_subgroup_findings(
    alert_title: str,
    alert_summary: str,
    subgroups: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Produces epidemiological interpretation of subgroup findings (CHUNK 6.11.8).
    
    Args:
        alert_title: Alert title
        alert_summary: Alert summary
        subgroups: Subgroup analysis results dictionary
        
    Returns:
        Dictionary with structured epidemiological interpretation or None if LLM call fails
    """
    # Build subgroup summary for prompt
    subgroup_summary = []
    for subgroup_name, data in subgroups.items():
        top_group = data.get("top_group", "N/A")
        top_value = data.get("top_value", 0)
        top_pct = data.get("top_percentage", 0)
        anomaly_score = data.get("anomaly_score", 1.0)
        
        subgroup_summary.append(
            f"- {subgroup_name}: {top_group} drives {top_value} cases ({top_pct:.1f}% of total, "
            f"anomaly score: {anomaly_score:.2f})"
        )
    
    # Build enhanced summary with statistical tests and PRR/ROR (CHUNK 6.11.11)
    enhanced_summary = []
    for subgroup_name, data in subgroups.items():
        top_group = data.get("top_group", "N/A")
        top_value = data.get("top_value", 0)
        top_pct = data.get("top_percentage", 0)
        anomaly_score = data.get("anomaly_score", 1.0)
        
        summary_line = (
            f"- {subgroup_name}: {top_group} drives {top_value} cases ({top_pct:.1f}% of total, "
            f"anomaly score: {anomaly_score:.2f})"
        )
        
        # Add statistical test results
        stat_tests = data.get("statistical_tests", {})
        if stat_tests:
            p_val = stat_tests.get("p_value_chi2")
            if p_val is not None:
                summary_line += f" [Chi-square p={p_val:.4f}]"
            rr = stat_tests.get("relative_risk")
            if rr:
                summary_line += f" [RR={rr:.2f}×]"
        
        # Add PRR/ROR
        subgroup_prr_ror = data.get("subgroup_prr_ror", {})
        if subgroup_prr_ror:
            prr = subgroup_prr_ror.get("prr")
            if prr:
                summary_line += f" [PRR={prr:.2f}]"
        
        enhanced_summary.append(summary_line)
    
    # Add concomitant drugs if available in the prompt context
    # (This will be passed separately if needed)
    
    system_prompt = """You are a senior pharmacovigilance epidemiologist with expertise in 
signal detection, population subgroup analysis, statistical testing, and risk factor identification. 
Analyze subgroup findings with epidemiological rigor, considering statistical significance, 
and provide actionable insights."""
    
    prompt = f"""You are a senior pharmacovigilance epidemiologist.

Analyze the following enhanced subgroup findings from a safety signal alert and provide structured epidemiological interpretation.

ALERT:
Title: {alert_title}
Summary: {alert_summary}

SUBGROUP FINDINGS (with statistical tests):
{chr(10).join(enhanced_summary)}

REQUIRED OUTPUT (JSON format only, no markdown, valid JSON):
{{
    "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
    "possible_risk_factors": ["Risk factor 1", "Risk factor 2"],
    "demographic_vulnerabilities": "Description of which demographic groups show elevated risk",
    "statistical_significance_notes": "Notes about statistically significant differences between subgroups",
    "indication_specific_notes": "Any indication-specific patterns observed",
    "dose_related_findings": "Any dose-related patterns or findings",
    "concomitant_drug_considerations": "Any notable patterns related to concomitant medications (if applicable)",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
}}

Provide ONLY valid JSON, no additional text before or after."""
    
    try:
        # Call LLM with epidemiological task type
        response = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="causal_reasoning",  # Use causal reasoning for epidemiological analysis
            max_tokens=800,
            temperature=0.3
        )
        
        if not response:
            return None
        
        # Try to parse JSON from response
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        elif response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        # Parse JSON
        try:
            interpretation = json.loads(response_clean)
            
            # Validate structure
            required_keys = [
                "key_findings", "possible_risk_factors", "demographic_vulnerabilities",
                "statistical_significance_notes", "indication_specific_notes", 
                "dose_related_findings", "concomitant_drug_considerations", "recommendations"
            ]
            
            # Ensure all keys exist, fill with defaults if missing
            for key in required_keys:
                if key not in interpretation:
                    if key == "key_findings":
                        interpretation[key] = ["Unable to determine from available data"]
                    elif key == "possible_risk_factors":
                        interpretation[key] = ["Review subgroup distributions for patterns"]
                    elif key == "recommendations":
                        interpretation[key] = ["Further investigation recommended", "Review case narratives"]
                    elif key == "statistical_significance_notes":
                        interpretation[key] = "Review statistical test results for significant subgroup differences."
                    elif key == "concomitant_drug_considerations":
                        interpretation[key] = "Review concomitant medication patterns if available."
                    else:
                        interpretation[key] = "Unable to provide interpretation."
            
            return interpretation
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create basic structure
            return {
                "key_findings": ["Subgroup analysis completed - review distributions"],
                "possible_risk_factors": ["See subgroup distributions"],
                "demographic_vulnerabilities": "Review age, sex, and region distributions",
                "statistical_significance_notes": "Review statistical test results if available",
                "indication_specific_notes": "Review indication patterns if available",
                "dose_related_findings": "Review dose patterns if available",
                "concomitant_drug_considerations": "Review concomitant medication patterns if available",
                "recommendations": ["Review case narratives", "Compare with historical data"]
            }
            
    except Exception:
        # Fail gracefully
        return None


# =========================================================
# CHUNK 6.11.10: Risk Dynamics Interpretation
# =========================================================

def interpret_risk_dynamics(
    alert_title: str,
    alert_summary: str,
    risk_dynamics: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Produces clinical safety interpretation of risk dynamics findings (CHUNK 6.11.10).
    
    Args:
        alert_title: Alert title
        alert_summary: Alert summary
        risk_dynamics: Risk dynamics analysis results dictionary
        
    Returns:
        Dictionary with structured clinical interpretation or None if LLM call fails
    """
    # Build summary for prompt
    vel_acc_summary = ""
    vel_acc = risk_dynamics.get("velocity_acceleration", {})
    if vel_acc:
        acc_score = vel_acc.get("acceleration_score", 0.0)
        trend_class = vel_acc.get("trend_classification", "unknown")
        velocity_ratio = vel_acc.get("velocity_ratio", 1.0)
        vel_acc_summary = (
            f"Acceleration Score: {acc_score:.2f}, "
            f"Classification: {trend_class}, "
            f"Velocity Ratio: {velocity_ratio:.2f}×"
        )
    
    slope_summary = ""
    slope = risk_dynamics.get("incident_rate_slope", {})
    if slope:
        slope_raw = slope.get("slope_raw", 0.0)
        direction = slope.get("direction", "unknown")
        slope_summary = f"Raw Rate Slope: {slope_raw:.3f}, Direction: {direction}"
    
    changepoints_summary = ""
    changepoints_context = risk_dynamics.get("changepoints_with_context", [])
    if changepoints_context:
        cp_details = []
        for cp in changepoints_context[:3]:  # Top 3
            cp_details.append(
                f"{cp.get('period', 'N/A')}: {cp.get('change_ratio', 1.0):.2f}× "
                f"({cp.get('before_mean', 0):.1f} → {cp.get('after_mean', 0):.1f})"
            )
        changepoints_summary = "; ".join(cp_details)
    
    if not vel_acc_summary and not slope_summary and not changepoints_summary:
        return None
    
    system_prompt = """You are a senior pharmacovigilance scientist with expertise in 
risk dynamics, signal acceleration, and structural trend analysis. 
Analyze risk dynamics findings with clinical rigor and provide actionable insights."""
    
    prompt = f"""You are a senior pharmacovigilance scientist.

Analyze the following risk dynamics findings from a safety signal alert.

ALERT:
Title: {alert_title}
Summary: {alert_summary}

RISK DYNAMICS FINDINGS:
Velocity & Acceleration: {vel_acc_summary if vel_acc_summary else "No velocity/acceleration data"}
Incident Rate Slope: {slope_summary if slope_summary else "No slope data"}
Change-Points: {changepoints_summary if changepoints_summary else "No change-points detected"}

REQUIRED OUTPUT (JSON format only, no markdown, valid JSON):
{{
    "clinical_implications": "Brief explanation of what these risk dynamics mean clinically (2-3 sentences)",
    "possible_explanations": ["Explanation 1", "Explanation 2", "Explanation 3"],
    "risk_level": "low/medium/high/critical",
    "recommended_actions": ["Action 1", "Action 2", "Action 3"]
}}

Provide ONLY valid JSON, no additional text before or after."""
    
    try:
        # Call LLM with causal reasoning task type
        response = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="causal_reasoning",  # Use causal reasoning for risk dynamics analysis
            max_tokens=600,
            temperature=0.3
        )
        
        if not response:
            return None
        
        # Try to parse JSON from response
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        elif response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        # Parse JSON
        try:
            interpretation = json.loads(response_clean)
            
            # Validate structure
            required_keys = ["clinical_implications", "possible_explanations", "risk_level", "recommended_actions"]
            
            # Ensure all keys exist, fill with defaults if missing
            for key in required_keys:
                if key not in interpretation:
                    if key == "possible_explanations":
                        interpretation[key] = ["Review risk acceleration patterns", "Investigate structural changes"]
                    elif key == "recommended_actions":
                        interpretation[key] = ["Monitor trend closely", "Review case narratives for patterns"]
                    elif key == "risk_level":
                        interpretation[key] = "medium"
                    else:
                        interpretation[key] = "Unable to provide interpretation."
            
            return interpretation
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create basic structure
            return {
                "clinical_implications": "Risk dynamics analysis completed. Review findings for clinical significance.",
                "possible_explanations": ["Structural change in reporting pattern", "Change in exposure or indication"],
                "risk_level": "medium",
                "recommended_actions": ["Monitor trend closely", "Review case narratives", "Consider signal validation"]
            }
            
    except Exception:
        # Fail gracefully
        return None
        
        # Try to parse JSON from response
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        elif response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        # Parse JSON
        try:
            interpretation = json.loads(response_clean)
            
            # Validate structure (CHUNK 6.11.11: enhanced with statistical significance and concomitants)
            required_keys = [
                "key_findings", "possible_risk_factors", "demographic_vulnerabilities",
                "statistical_significance_notes", "indication_specific_notes", 
                "dose_related_findings", "concomitant_drug_considerations", "recommendations"
            ]
            
            # Ensure all keys exist, fill with defaults if missing
            for key in required_keys:
                if key not in interpretation:
                    if key == "key_findings":
                        interpretation[key] = ["Unable to determine from available data"]
                    elif key == "possible_risk_factors":
                        interpretation[key] = ["Review subgroup distributions for patterns"]
                    elif key == "recommendations":
                        interpretation[key] = ["Further investigation recommended", "Review case narratives"]
                    elif key == "statistical_significance_notes":
                        interpretation[key] = "Review statistical test results for significant subgroup differences."
                    elif key == "concomitant_drug_considerations":
                        interpretation[key] = "Review concomitant medication patterns if available."
                    else:
                        interpretation[key] = "Unable to provide interpretation."
            
            return interpretation
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create basic structure
            return {
                "key_findings": ["Subgroup analysis completed - review distributions"],
                "possible_risk_factors": ["See subgroup distributions"],
                "demographic_vulnerabilities": "Review age, sex, and region distributions",
                "indication_specific_notes": "Review indication patterns if available",
                "dose_related_findings": "Review dose patterns if available",
                "recommendations": ["Review case narratives", "Compare with historical data"]
            }
            
    except Exception:
        # Fail gracefully
        return None


# =========================================================
# CHUNK 6.11.9: Dose-Response Interpretation
# =========================================================

def interpret_dose_response(
    alert_title: str,
    alert_summary: str,
    dose_response: Optional[Dict[str, Any]] = None,
    cumulative_risk: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Produces clinical safety interpretation of dose-response and cumulative risk findings (CHUNK 6.11.9).
    
    Args:
        alert_title: Alert title
        alert_summary: Alert summary
        dose_response: Dose-response analysis results dictionary
        cumulative_risk: Cumulative risk analysis results dictionary
        
    Returns:
        Dictionary with structured clinical interpretation or None if LLM call fails
    """
    # Build summary for prompt
    dose_summary = ""
    if dose_response:
        significance = dose_response.get("significance", 1.0)
        trend_dir = dose_response.get("trend_direction", "unknown")
        dose_range = dose_response.get("dose_range", {})
        dose_summary = (
            f"Dose-Response: Significance score {significance:.2f}×, "
            f"trend direction: {trend_dir}, "
            f"dose range: {dose_range.get('min', 0):.1f}mg - {dose_range.get('max', 0):.1f}mg"
        )
    
    cumulative_summary = ""
    if cumulative_risk:
        total_cases = cumulative_risk.get("total_cases", 0)
        is_increasing = cumulative_risk.get("is_increasing", False)
        recent_slope = cumulative_risk.get("recent_slope", 0.0)
        cumulative_summary = (
            f"Cumulative Risk: {total_cases} total cases, "
            f"trend: {'increasing' if is_increasing else 'stable'}, "
            f"slope: {recent_slope:.2f}"
        )
    
    if not dose_summary and not cumulative_summary:
        return None
    
    system_prompt = """You are a senior pharmacovigilance scientist with expertise in 
dose-response relationships, exposure modeling, and cumulative risk assessment. 
Analyze dose-response findings with clinical rigor and provide actionable insights."""
    
    prompt = f"""You are a senior pharmacovigilance scientist.

Analyze the following dose-response and cumulative risk findings from a safety signal alert.

ALERT:
Title: {alert_title}
Summary: {alert_summary}

DOSE-RESPONSE FINDINGS:
{dose_summary if dose_summary else "No dose-response data available"}

CUMULATIVE RISK FINDINGS:
{cumulative_summary if cumulative_summary else "No cumulative risk data available"}

REQUIRED OUTPUT (JSON format only, no markdown, valid JSON):
{{
    "clinical_implications": "Brief explanation of what these findings mean from a clinical safety perspective (2-3 sentences)",
    "potential_mechanisms": ["Mechanism 1", "Mechanism 2", "Mechanism 3"],
    "risk_management": ["Risk management recommendation 1", "Risk management recommendation 2", "Risk management recommendation 3"]
}}

Provide ONLY valid JSON, no additional text before or after."""
    
    try:
        # Call LLM with causal reasoning task type
        response = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="causal_reasoning",  # Use causal reasoning for dose-response analysis
            max_tokens=600,
            temperature=0.3
        )
        
        if not response:
            return None
        
        # Try to parse JSON from response
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        elif response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        # Parse JSON
        try:
            interpretation = json.loads(response_clean)
            
            # Validate structure
            required_keys = ["clinical_implications", "potential_mechanisms", "risk_management"]
            
            # Ensure all keys exist, fill with defaults if missing
            for key in required_keys:
                if key not in interpretation:
                    if key == "potential_mechanisms":
                        interpretation[key] = ["Dose-dependent effect possible", "Review case narratives for dose patterns"]
                    elif key == "risk_management":
                        interpretation[key] = ["Consider dose adjustment recommendations", "Monitor high-dose patients closely"]
                    else:
                        interpretation[key] = "Unable to provide interpretation."
            
            return interpretation
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create basic structure
            return {
                "clinical_implications": "Dose-response analysis completed. Review findings for clinical significance.",
                "potential_mechanisms": ["Dose-dependent effect", "Exposure-related risk"],
                "risk_management": ["Review dose-response curve", "Consider dose adjustment if clinically significant"]
            }
            
    except Exception:
        # Fail gracefully
        return None


# =========================================================
# CHUNK 6.11.10: Risk Dynamics Interpretation
# =========================================================

def interpret_risk_dynamics(
    alert_title: str,
    alert_summary: str,
    risk_dynamics: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Produces clinical safety interpretation of risk dynamics findings (CHUNK 6.11.10).
    
    Args:
        alert_title: Alert title
        alert_summary: Alert summary
        risk_dynamics: Risk dynamics analysis results dictionary
        
    Returns:
        Dictionary with structured clinical interpretation or None if LLM call fails
    """
    # Build summary for prompt
    vel_acc_summary = ""
    vel_acc = risk_dynamics.get("velocity_acceleration", {})
    if vel_acc:
        acc_score = vel_acc.get("acceleration_score", 0.0)
        trend_class = vel_acc.get("trend_classification", "unknown")
        velocity_ratio = vel_acc.get("velocity_ratio", 1.0)
        vel_acc_summary = (
            f"Acceleration Score: {acc_score:.2f}, "
            f"Classification: {trend_class}, "
            f"Velocity Ratio: {velocity_ratio:.2f}×"
        )
    
    slope_summary = ""
    slope = risk_dynamics.get("incident_rate_slope", {})
    if slope:
        slope_raw = slope.get("slope_raw", 0.0)
        direction = slope.get("direction", "unknown")
        slope_summary = f"Raw Rate Slope: {slope_raw:.3f}, Direction: {direction}"
    
    changepoints_summary = ""
    changepoints_context = risk_dynamics.get("changepoints_with_context", [])
    if changepoints_context:
        cp_details = []
        for cp in changepoints_context[:3]:  # Top 3
            cp_details.append(
                f"{cp.get('period', 'N/A')}: {cp.get('change_ratio', 1.0):.2f}× "
                f"({cp.get('before_mean', 0):.1f} → {cp.get('after_mean', 0):.1f})"
            )
        changepoints_summary = "; ".join(cp_details)
    
    if not vel_acc_summary and not slope_summary and not changepoints_summary:
        return None
    
    system_prompt = """You are a senior pharmacovigilance scientist with expertise in 
risk dynamics, signal acceleration, and structural trend analysis. 
Analyze risk dynamics findings with clinical rigor and provide actionable insights."""
    
    prompt = f"""You are a senior pharmacovigilance scientist.

Analyze the following risk dynamics findings from a safety signal alert.

ALERT:
Title: {alert_title}
Summary: {alert_summary}

RISK DYNAMICS FINDINGS:
Velocity & Acceleration: {vel_acc_summary if vel_acc_summary else "No velocity/acceleration data"}
Incident Rate Slope: {slope_summary if slope_summary else "No slope data"}
Change-Points: {changepoints_summary if changepoints_summary else "No change-points detected"}

REQUIRED OUTPUT (JSON format only, no markdown, valid JSON):
{{
    "clinical_implications": "Brief explanation of what these risk dynamics mean clinically (2-3 sentences)",
    "possible_explanations": ["Explanation 1", "Explanation 2", "Explanation 3"],
    "risk_level": "low/medium/high/critical",
    "recommended_actions": ["Action 1", "Action 2", "Action 3"]
}}

Provide ONLY valid JSON, no additional text before or after."""
    
    try:
        # Call LLM with causal reasoning task type
        response = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="causal_reasoning",  # Use causal reasoning for risk dynamics analysis
            max_tokens=600,
            temperature=0.3
        )
        
        if not response:
            return None
        
        # Try to parse JSON from response
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        elif response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        # Parse JSON
        try:
            interpretation = json.loads(response_clean)
            
            # Validate structure
            required_keys = ["clinical_implications", "possible_explanations", "risk_level", "recommended_actions"]
            
            # Ensure all keys exist, fill with defaults if missing
            for key in required_keys:
                if key not in interpretation:
                    if key == "possible_explanations":
                        interpretation[key] = ["Review risk acceleration patterns", "Investigate structural changes"]
                    elif key == "recommended_actions":
                        interpretation[key] = ["Monitor trend closely", "Review case narratives for patterns"]
                    elif key == "risk_level":
                        interpretation[key] = "medium"
                    else:
                        interpretation[key] = "Unable to provide interpretation."
            
            return interpretation
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create basic structure
            return {
                "clinical_implications": "Risk dynamics analysis completed. Review findings for clinical significance.",
                "possible_explanations": ["Structural change in reporting pattern", "Change in exposure or indication"],
                "risk_level": "medium",
                "recommended_actions": ["Monitor trend closely", "Review case narratives", "Consider signal validation"]
            }
            
    except Exception:
        # Fail gracefully
        return None
        
        # Try to parse JSON from response
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        elif response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        # Parse JSON
        try:
            interpretation = json.loads(response_clean)
            
            # Validate structure
            required_keys = ["clinical_implications", "potential_mechanisms", "risk_management"]
            
            # Ensure all keys exist, fill with defaults if missing
            for key in required_keys:
                if key not in interpretation:
                    if key == "potential_mechanisms":
                        interpretation[key] = ["Dose-dependent effect possible", "Review case narratives for dose patterns"]
                    elif key == "risk_management":
                        interpretation[key] = ["Consider dose adjustment recommendations", "Monitor high-dose patients closely"]
                    else:
                        interpretation[key] = "Unable to provide interpretation."
            
            return interpretation
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create basic structure
            return {
                "clinical_implications": "Dose-response analysis completed. Review findings for clinical significance.",
                "potential_mechanisms": ["Dose-dependent effect", "Exposure-related risk"],
                "risk_management": ["Review dose-response curve", "Consider dose adjustment if clinically significant"]
            }
            
    except Exception:
        # Fail gracefully
        return None# =========================================================
# CHUNK 6.11.12: Narrative Cluster Summarization
# =========================================================

async def summarize_narrative_cluster(
    texts: List[str],
    alert_title: str = "Narrative Cluster",
    alert_summary: str = "A cluster of similar narratives was detected."
) -> Optional[Dict[str, Any]]:
    """
    Summarizes a cluster of narratives into a clinically meaningful label and interpretation (CHUNK 6.11.12).
    
    Args:
        texts: List of narrative texts in the cluster.
        alert_title: Title of the associated alert for context.
        alert_summary: Summary of the associated alert for context.
        
    Returns:
        A dictionary with structured clinical explanation or None if LLM fails.
    """
    try:
        if not texts:
            return None

        prompt = f"""
        You are a senior pharmacovigilance scientist.
        
        Analyze the following case narratives from a detected cluster related to an alert titled \"{alert_title}\" and summarized as \"{alert_summary}\".
        
        Summarize them into a clinically meaningful cluster label and provide a structured interpretation.
        
        NARRATIVES (first 5 examples):
        {json.dumps(texts[:5], indent=2)}
        
        REQUIRED OUTPUT (JSON format only, no markdown, valid JSON):
        {{
            "cluster_label": \"A concise, clinically relevant label for this cluster (e.g., 'Injection Site Reactions with Fever', 'Hepatic Injury with Concomitant Alcohol Use')\",
            "key_symptoms": [\"List 2-3 most prominent symptoms or adverse events observed in this cluster.\"],
            "possible_mechanisms": [\"List 2-3 plausible pharmacological or pathophysiological mechanisms for these events.\"],
            \"clinical_risk\": \"Assess the clinical risk level (e.g., 'High - Life-threatening', 'Moderate - Requires intervention', 'Low - Self-limiting').\",
            \"regulatory_relevance\": \"Briefly explain any potential regulatory impact or reporting considerations.\",
            \"one_sentence_summary\": \"A single sentence summarizing the key finding of this cluster.\"
        }}
        """
        
        system_prompt = "You are an expert pharmacovigilance scientist providing structured interpretations of narrative clusters."
        
        response = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="narrative_analysis",
            max_tokens=700,
            temperature=0.2
        )
        
        if not response:
            return None
        
        # Try to parse JSON from response
        response_clean = response.strip()
        if response_clean.startswith("`json"):
            response_clean = response_clean[7:]
        elif response_clean.startswith("`"):
            response_clean = response_clean[3:]
        if response_clean.endswith("`"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        try:
            interpretation = json.loads(response_clean)
            
            # Validate structure
            required_keys = [
                "cluster_label", "key_symptoms", "possible_mechanisms",
                "clinical_risk", "regulatory_relevance", "one_sentence_summary"
            ]
            
            # Ensure all keys exist, fill with defaults if missing
            for key in required_keys:
                if key not in interpretation:
                    if key == "key_symptoms":
                        interpretation[key] = ["unspecified symptoms"]
                    elif key == "possible_mechanisms":
                        interpretation[key] = ["unknown mechanism"]
                    elif key == "clinical_risk":
                        interpretation[key] = "unknown"
                    elif key == "regulatory_relevance":
                        interpretation[key] = "unknown"
                    elif key == "one_sentence_summary":
                        interpretation[key] = "Narrative cluster detected with uncharacterized patterns."
                    else:
                        interpretation[key] = "Unable to provide interpretation."
            
            return interpretation
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create basic structure
            return {
                "cluster_label": "Uninterpretable Narrative Cluster",
                "key_symptoms": ["review narratives"],
                "possible_mechanisms": ["LLM parsing error"],
                "clinical_risk": "unknown",
                "regulatory_relevance": "unknown",
                "one_sentence_summary": "Narrative cluster detected, but LLM failed to parse interpretation."
            }
            
    except Exception:
        # Fail gracefully
        return None
# =========================================================
# CHUNK 6.11.13: Lot/Batch Alert Interpretation
# =========================================================

async def interpret_lot_alert(
    lot_alert_data: Dict[str, Any],
    alert_title: str = "Lot/Batch Spike Alert",
    alert_summary: str = "A spike in adverse events for a specific lot number was detected."
) -> Optional[Dict[str, Any]]:
    """
    Provides a medical safety interpretation for lot/batch spike alerts (CHUNK 6.11.13).
    
    Args:
        lot_alert_data: Dictionary containing details of the lot alert.
        alert_title: Title of the associated alert for context.
        alert_summary: Summary of the associated alert for context.
        
    Returns:
        A dictionary with structured clinical explanation or None if LLM fails.
    """
    try:
        if not lot_alert_data:
            return None

        prompt = f"""
        You are a senior pharmacovigilance expert.
        
        Analyze the following batch-level spike alert related to an alert titled \"{alert_title}\" and summarized as \"{alert_summary}\".
        
        Provide a structured interpretation focusing on possible manufacturing/storage issues, contamination plausibility, regulatory urgency, and recommended next steps.
        
        LOT ALERT DATA:
        {json.dumps(lot_alert_data, indent=2)}
        
        REQUIRED OUTPUT (JSON format only, no markdown, valid JSON):
        {{
            \"one_sentence_summary\": \"A concise summary of the lot alert and its primary implication.\",
            \"possible_manufacturing_issues\": [\"List 2-3 most plausible manufacturing issues (e.g., 'manufacturing defect', 'quality control failure', 'packaging error').\"],
            \"possible_storage_issues\": [\"List 2-3 most plausible storage/temperature issues (e.g., 'temperature excursion', 'storage condition violation', 'shipping damage').\"],
            \"contamination_likelihood\": \"Assess the plausibility of contamination (e.g., 'Low', 'Medium', 'High') and why.\",
            \"regulatory_urgency\": \"Classify the regulatory urgency (e.g., 'Low', 'Medium', 'High', 'Critical').\",
            \"recommended_next_steps\": [\"List 2-3 concrete, actionable recommendations (e.g., 'Quarantine remaining stock', 'Review manufacturing records', 'Investigate storage conditions').\"]
        }}
        """
        
        system_prompt = "You are an expert pharmacovigilance scientist providing structured interpretations of manufacturing batch-related safety signals."
        
        response = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="causal_reasoning",
            max_tokens=700,
            temperature=0.2
        )
        
        if not response:
            return None
        
        # Try to parse JSON from response
        response_clean = response.strip()
        if response_clean.startswith("`json"):
            response_clean = response_clean[7:]
        elif response_clean.startswith("`"):
            response_clean = response_clean[3:]
        if response_clean.endswith("`"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        try:
            interpretation = json.loads(response_clean)
            
            # Validate structure
            required_keys = [
                "one_sentence_summary", "possible_manufacturing_issues", "possible_storage_issues",
                "contamination_likelihood", "regulatory_urgency", "recommended_next_steps"
            ]
            
            # Ensure all keys exist, fill with defaults if missing
            for key in required_keys:
                if key not in interpretation:
                    if key == "possible_manufacturing_issues":
                        interpretation[key] = ["Review manufacturing process", "Check quality control records"]
                    elif key == "possible_storage_issues":
                        interpretation[key] = ["Check storage conditions", "Review temperature logs"]
                    elif key == "recommended_next_steps":
                        interpretation[key] = ["Investigate lot history", "Assess product quality"]
                    elif key == "contamination_likelihood":
                        interpretation[key] = "unknown"
                    elif key == "regulatory_urgency":
                        interpretation[key] = "medium"
                    else:
                        interpretation[key] = "Unable to provide interpretation."
            
            return interpretation
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create basic structure
            return {
                "one_sentence_summary": "Lot spike detected, but LLM failed to parse interpretation.",
                "possible_manufacturing_issues": ["Review manufacturing records"],
                "possible_storage_issues": ["Check storage conditions"],
                "contamination_likelihood": "unknown",
                "regulatory_urgency": "medium",
                "recommended_next_steps": ["Investigate lot history", "Manual investigation"]
            }
            
    except Exception:
        # Fail gracefully
        return None