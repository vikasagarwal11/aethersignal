"""
Pricing Tiers Configuration - Wave 6
Commercial tier system for AetherSignal
"""

PRICING_TIERS = {
    "starter": {
        "name": "Starter",
        "price_monthly": 49,
        "price_yearly": 490,  # ~17% discount
        "features": [
            "social_ae",
            "faers_basic",
            "basic_trends",
            "basic_alerts"
        ],
        "limits": {
            "llm_calls_per_month": 100,
            "max_users": 1,
            "api_calls_per_day": 100,
            "data_retention_days": 30,
            "export_limit": 1000
        },
        "description": "Perfect for individual researchers and small teams"
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 199,
        "price_yearly": 1990,  # ~17% discount
        "features": [
            "social_ae",
            "faers_full",
            "executive_dashboard",
            "literature_ai",
            "signal_prioritization",
            "explain_mode",
            "advanced_trends",
            "clustering",
            "novelty_detection",
            "cross_linking"
        ],
        "limits": {
            "llm_calls_per_month": 2000,
            "max_users": 10,
            "api_calls_per_day": 1000,
            "data_retention_days": 365,
            "export_limit": 10000
        },
        "description": "For safety teams and mid-size organizations"
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": None,  # Custom pricing
        "price_yearly": None,
        "features": [
            "all",
            "copilot",
            "psur_generator",
            "workflow_automation",
            "data_api",
            "custom_integrations",
            "dedicated_support",
            "sla_guarantee",
            "audit_logs",
            "sso",
            "rbac"
        ],
        "limits": {
            "llm_calls_per_month": "unlimited",
            "max_users": "unlimited",
            "api_calls_per_day": "unlimited",
            "data_retention_days": "unlimited",
            "export_limit": "unlimited"
        },
        "description": "For large organizations with advanced needs"
    }
}


def get_tier_features(tier: str) -> list:
    """
    Get list of features for a given tier.
    
    Args:
        tier: Tier name ("starter", "pro", "enterprise")
    
    Returns:
        List of feature names
    """
    if tier not in PRICING_TIERS:
        return []
    
    return PRICING_TIERS[tier].get("features", [])


def get_tier_limits(tier: str) -> dict:
    """
    Get limits for a given tier.
    
    Args:
        tier: Tier name
    
    Returns:
        Dictionary of limits
    """
    if tier not in PRICING_TIERS:
        return {}
    
    return PRICING_TIERS[tier].get("limits", {})


def is_feature_in_tier(tier: str, feature: str) -> bool:
    """
    Check if a feature is available in a tier.
    
    Args:
        tier: Tier name
        feature: Feature name
    
    Returns:
        True if feature is available
    """
    # Check if pricing is enabled globally
    try:
        from src.utils.config_loader import get_config_value
        if not get_config_value("enable_pricing", False):
            # Pricing disabled = all features available
            return True
    except Exception:
        # If config loader fails, assume pricing is enabled (default behavior)
        pass
    
    features = get_tier_features(tier)
    
    # Enterprise has "all" which means everything
    if "all" in features:
        return True
    
    return feature in features


def get_tier_info(tier: str) -> dict:
    """
    Get full tier information.
    
    Args:
        tier: Tier name
    
    Returns:
        Complete tier dictionary
    """
    return PRICING_TIERS.get(tier, {})

