"""
Route configuration for top navigation and sidebar.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

PAGES_DIR = Path("pages")


def page_exists(page_name: Optional[str]) -> bool:
    """Return True when a Streamlit page file actually exists on disk."""
    if not page_name:
        return False
    return (PAGES_DIR / f"{page_name}.py").exists()


# Main navigation routes (top + sidebar)
ROUTES: Dict[str, Any] = {
    "Executive Dashboard": {
        "route": "executive_dashboard",
        "icon": "📊",
        "page": "99_Executive_Dashboard",
        "category": "Dashboards",
        "requires_auth": True,
        "visible_in_nav": True,
        "roles": [],
        "nav_location": "top",
    },
    "Safety Intelligence": {
        "route": "safety_intelligence",
        "icon": "🧠",
        "category": "Intelligence",
        "requires_auth": True,
        "visible_in_nav": True,
        "roles": [],
        "nav_location": "both",
        "subpages": {
            "Mechanism Explorer": {
                "route": "mechanism_explorer",
                "icon": "🧬",
                "page": "mechanism_explorer",
                "requires_auth": True,
                "visible_in_nav": True,
            },
            "Knowledge Graph": {
                "route": "knowledge_graph",
                "icon": "🕸️",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
            "Label Gap Viewer": {
                "route": "label_gap",
                "icon": "🏷️",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
            "Risk Dashboard": {
                "route": "risk_dashboard",
                "icon": "⚠️",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
            "Safety Copilot": {
                "route": "safety_copilot",
                "icon": "🤖",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
        },
    },
    "Evidence Governance": {
        "route": "governance",
        "icon": "🛡️",
        "category": "Governance",
        "requires_auth": True,
        "visible_in_nav": True,
        "roles": [],
        "nav_location": "both",
        "subpages": {
            "Lineage Viewer": {
                "route": "lineage_viewer",
                "icon": "🧬",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
            "Provenance Explorer": {
                "route": "provenance",
                "icon": "🛰️",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
            "Data Quality": {
                "route": "data_quality",
                "icon": "🧹",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
        },
    },
    "Data Explorer": {
        "route": "data_explorer",
        "icon": "🔍",
        "category": "Exploration",
        "requires_auth": False,
        "visible_in_nav": True,
        "roles": [],
        "nav_location": "both",
        "subpages": {
            "Quantum PV Explorer": {
                "route": "quantum_pv",
                "icon": "🧪",
                "page": "1_Quantum_PV_Explorer",
                "requires_auth": True,
                "visible_in_nav": True,
            },
            "AE Explorer": {
                "route": "ae_explorer",
                "icon": "📈",
                "page": "3_AE_Explorer",
                "requires_auth": True,
                "visible_in_nav": True,
            },
            "Social AE Explorer": {
                "route": "social_ae",
                "icon": "🌐",
                "page": "2_Social_AE_Explorer",
                "requires_auth": False,
                "visible_in_nav": True,
            },
            "Multi-Dimensional Explorer": {
                "route": "multi_dimensional",
                "icon": "🧭",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
        },
    },
    "Workflows": {
        "route": "workflows",
        "icon": "🗂️",
        "category": "Workflows",
        "requires_auth": True,
        "visible_in_nav": True,
        "roles": [],
        "nav_location": "both",
        "subpages": {
            "Workflow Dashboard": {
                "route": "workflow_dashboard",
                "icon": "📋",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
            "Report Builder": {
                "route": "report_builder",
                "icon": "📝",
                "page": None,
                "coming_soon": True,
                "requires_auth": True,
                "visible_in_nav": True,
            },
        },
    },
}

# Super-admin routes
ADMIN_ROUTES: Dict[str, Any] = {
    "Data Sources": {
        "route": "data_sources",
        "icon": "🗄️",
        "page": "98_Data_Source_Manager",
        "category": "Admin",
        "requires_auth": True,
        "visible_in_nav": True,
        "roles": ["super_admin"],
        "nav_location": "top",
    },
    "Settings": {
        "route": "settings",
        "icon": "⚙️",
        "page": "Settings",
        "category": "Admin",
        "requires_auth": True,
        "visible_in_nav": True,
        "roles": ["super_admin"],
        "nav_location": "top",
    },
    "API Keys": {
        "route": "api_keys",
        "icon": "🔑",
        "page": "API_Keys",
        "category": "Admin",
        "requires_auth": True,
        "visible_in_nav": True,
        "roles": ["super_admin"],
        "nav_location": "top",
    },
    "Billing": {
        "route": "billing",
        "icon": "💳",
        "page": "Billing",
        "category": "Admin",
        "requires_auth": True,
        "visible_in_nav": True,
        "roles": ["admin", "super_admin"],
        "nav_location": "top",
    },
    "System Diagnostics": {
        "route": "system_diagnostics",
        "icon": "🩺",
        "page": "System_Diagnostics",
        "category": "Admin",
        "requires_auth": True,
        "visible_in_nav": True,
        "roles": ["super_admin"],
        "nav_location": "top",
    },
}


def get_page_route(route_name: str) -> Optional[str]:
    for config in ROUTES.values():
        if config.get("route") == route_name and page_exists(config.get("page")):
            return config.get("page")

        for subpage_config in config.get("subpages", {}).values():
            if subpage_config.get("route") == route_name and page_exists(subpage_config.get("page")):
                return subpage_config.get("page")

    for config in ADMIN_ROUTES.values():
        if config.get("route") == route_name and page_exists(config.get("page")):
            return config.get("page")

    return None


def get_route_by_page(page_name: str) -> Optional[str]:
    for config in ROUTES.values():
        if config.get("page") == page_name:
            return config.get("route")

        for subpage_config in config.get("subpages", {}).values():
            if subpage_config.get("page") == page_name:
                return subpage_config.get("route")

    for config in ADMIN_ROUTES.values():
        if config.get("page") == page_name:
            return config.get("route")

    return None


def get_primary_routes(require_auth: Optional[bool] = None, user_roles: Optional[List[str]] = None) -> Dict[str, Any]:
    filtered: Dict[str, Any] = {}

    for route_name, route_config in ROUTES.items():
        route_requires_auth = route_config.get("requires_auth", True)
        if require_auth is not None:
            if require_auth and not route_requires_auth:
                continue
            if not require_auth and route_requires_auth:
                continue

        route_roles = route_config.get("roles", [])
        if route_roles:
            if not user_roles or not any(role in user_roles for role in route_roles):
                continue

        if not route_config.get("visible_in_nav", True):
            continue

        filtered[route_name] = route_config

    return filtered


def get_admin_routes(user_roles: Optional[List[str]] = None) -> Dict[str, Any]:
    filtered: Dict[str, Any] = {}

    for route_name, route_config in ADMIN_ROUTES.items():
        if not route_config.get("visible_in_nav", True):
            continue

        route_roles = route_config.get("roles", [])
        if route_roles:
            if not user_roles or not any(role in user_roles for role in route_roles):
                continue

        filtered[route_name] = route_config

    return filtered
