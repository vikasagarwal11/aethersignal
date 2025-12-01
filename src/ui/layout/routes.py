"""
Route Configuration - Defines all pages and navigation structure
"""

from typing import Dict, Any

# Main navigation routes
ROUTES: Dict[str, Any] = {
    "Executive Dashboard": {
        "route": "executive_dashboard",
        "icon": "📈",
        "page": "99_Executive_Dashboard",
        "category": "Dashboards"
    },
    "Safety Intelligence": {
        "route": "safety_intelligence",
        "icon": "🧠",
        "category": "Intelligence",
        "subpages": {
            "Mechanism Explorer": {
                "route": "mechanism_explorer",
                "icon": "🔬",
                "page": "5_Mechanism_Explorer"
            },
            "Knowledge Graph": {
                "route": "knowledge_graph",
                "icon": "🌐",
                "page": "5_Knowledge_Graph"
            },
            "Label Gap Viewer": {
                "route": "label_gap",
                "icon": "📋",
                "page": "5_Label_Gap"
            },
            "Risk Dashboard": {
                "route": "risk_dashboard",
                "icon": "⚠️",
                "page": "6_Risk_Dashboard"
            },
            "Safety Copilot": {
                "route": "safety_copilot",
                "icon": "🤖",
                "page": "4_Safety_Copilot"
            }
        }
    },
    "Evidence Governance": {
        "route": "governance",
        "icon": "🛡️",
        "category": "Governance",
        "subpages": {
            "Lineage Viewer": {
                "route": "lineage_viewer",
                "icon": "🔗",
                "page": "100_Evidence_Governance"
            },
            "Provenance Explorer": {
                "route": "provenance",
                "icon": "🔍",
                "page": "100_Evidence_Governance"
            },
            "Data Quality": {
                "route": "data_quality",
                "icon": "✅",
                "page": "100_Evidence_Governance"
            }
        }
    },
    "Data Explorer": {
        "route": "data_explorer",
        "icon": "🔍",
        "category": "Exploration",
        "subpages": {
            "Quantum PV Explorer": {
                "route": "quantum_pv",
                "icon": "⚛️",
                "page": "1_Quantum_PV_Explorer"
            },
            "AE Explorer": {
                "route": "ae_explorer",
                "icon": "📊",
                "page": "3_AE_Explorer"
            },
            "Social AE Explorer": {
                "route": "social_ae",
                "icon": "🌐",
                "page": "2_Social_AE_Explorer"
            },
            "Multi-Dimensional Explorer": {
                "route": "multi_dimensional",
                "icon": "📈",
                "page": "3_Multi_Dimensional_Explorer"
            }
        }
    },
    "Workflows": {
        "route": "workflows",
        "icon": "📋",
        "category": "Workflows",
        "subpages": {
            "Workflow Dashboard": {
                "route": "workflow_dashboard",
                "icon": "🔄",
                "page": "7_Workflow_Dashboard"
            },
            "Report Builder": {
                "route": "report_builder",
                "icon": "📄",
                "page": "8_Report_Builder"
            }
        }
    }
}

# SuperAdmin-only routes
ADMIN_ROUTES: Dict[str, Any] = {
    "Data Sources": {
        "route": "data_sources",
        "icon": "🔐",
        "page": "98_🔐_Data_Source_Manager",
        "category": "Admin"
    },
    "Settings": {
        "route": "settings",
        "icon": "⚙️",
        "page": "Settings",
        "category": "Admin"
    }
}


def get_page_route(route_name: str) -> Optional[str]:
    """
    Get the Streamlit page path for a route name.
    
    Args:
        route_name: Route identifier
    
    Returns:
        Page path or None
    """
    # Check main routes
    for section, config in ROUTES.items():
        if config.get("route") == route_name:
            return config.get("page")
        
        # Check subpages
        subpages = config.get("subpages", {})
        for subpage_name, subpage_config in subpages.items():
            if subpage_config.get("route") == route_name:
                return subpage_config.get("page")
    
    # Check admin routes
    for section, config in ADMIN_ROUTES.items():
        if config.get("route") == route_name:
            return config.get("page")
    
    return None


def get_route_by_page(page_name: str) -> Optional[str]:
    """
    Get route name from Streamlit page name.
    
    Args:
        page_name: Streamlit page filename (without .py)
    
    Returns:
        Route identifier or None
    """
    # Check main routes
    for section, config in ROUTES.items():
        if config.get("page") == page_name:
            return config.get("route")
        
        # Check subpages
        subpages = config.get("subpages", {})
        for subpage_name, subpage_config in subpages.items():
            if subpage_config.get("page") == page_name:
                return subpage_config.get("route")
    
    # Check admin routes
    for section, config in ADMIN_ROUTES.items():
        if config.get("page") == page_name:
            return config.get("route")
    
    return None

