"""
Health Check API - System health monitoring
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def system_health() -> Dict[str, Any]:
    """
    Get system health status.
    
    Returns:
        Health status dictionary
    """
    health = {
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat() + " UTC",
        "services": {}
    }
    
    # Check FAERS
    try:
        from src.faers import faers_engine
        health["services"]["faers"] = "available"
    except Exception as e:
        health["services"]["faers"] = f"unavailable: {str(e)[:50]}"
        health["status"] = "DEGRADED"
    
    # Check Social
    try:
        from src.social_ae import social_fetcher
        health["services"]["social"] = "available"
    except Exception as e:
        health["services"]["social"] = f"unavailable: {str(e)[:50]}"
        health["status"] = "DEGRADED"
    
    # Check Literature
    try:
        from src.literature import lit_ingest
        health["services"]["literature"] = "available"
    except Exception as e:
        health["services"]["literature"] = f"unavailable: {str(e)[:50]}"
        health["status"] = "DEGRADED"
    
    # Check Mechanism AI
    try:
        from src.knowledge_graph import MechanismSupervisor
        health["services"]["mechanism_ai"] = "available"
    except Exception as e:
        health["services"]["mechanism_ai"] = f"unavailable: {str(e)[:50]}"
        health["status"] = "DEGRADED"
    
    # Check Database
    try:
        from src.storage import unified_storage
        health["services"]["database"] = "available"
    except Exception as e:
        health["services"]["database"] = f"unavailable: {str(e)[:50]}"
        health["status"] = "DEGRADED"
    
    # Check Cache
    try:
        from src.mechanism.cache import MechanismCache
        cache = MechanismCache()
        stats = cache.get_stats()
        health["services"]["cache"] = "available" if stats.get("redis_available") or stats.get("local_cache_size", 0) >= 0 else "unavailable"
    except Exception as e:
        health["services"]["cache"] = f"unavailable: {str(e)[:50]}"
    
    return health


def health_json() -> str:
    """
    Get health status as JSON string.
    
    Returns:
        JSON string
    """
    return json.dumps(system_health(), indent=2)


def check_service(service_name: str) -> Dict[str, Any]:
    """
    Check individual service health.
    
    Args:
        service_name: Name of service to check
    
    Returns:
        Service health dictionary
    """
    health = system_health()
    service_status = health["services"].get(service_name, "unknown")
    
    return {
        "service": service_name,
        "status": "OK" if "available" in service_status else "ERROR",
        "details": service_status
    }

