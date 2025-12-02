"""
Organization Profile Manager
Handles loading and saving organization-specific configuration for PSUR/DSUR reports.
"""

import os
import logging
from typing import Optional, Dict, Any, List
import streamlit as st

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from src.reports.psur_context import OrgProductConfig
from src.auth.user_management import get_user_organization

logger = logging.getLogger(__name__)


def get_supabase_db() -> Optional[Client]:
    """Get Supabase client for database operations."""
    if not SUPABASE_AVAILABLE:
        return None
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        return None
    
    try:
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


def get_current_tenant_id() -> Optional[str]:
    """
    Get current user's organization/tenant ID.
    
    Returns:
        Organization name/ID or None
    """
    # Try session state first
    org = st.session_state.get("user_organization") or st.session_state.get("organization")
    if org:
        return org
    
    # Try from user profile
    user_id = st.session_state.get("user_id")
    if user_id:
        org = get_user_organization(user_id)
        if org:
            return org
    
    return None


def load_org_product_config(
    tenant_id: Optional[str] = None,
    product: Optional[str] = None
) -> Optional[OrgProductConfig]:
    """
    Load organization product configuration from database.
    
    Args:
        tenant_id: Organization identifier (if None, uses current user's org)
        product: Product name (if None, returns first product or None)
    
    Returns:
        OrgProductConfig or None if not found
    """
    if not SUPABASE_AVAILABLE:
        logger.debug("Supabase not available, returning None for org config")
        return None
    
    if tenant_id is None:
        tenant_id = get_current_tenant_id()
    
    if not tenant_id:
        logger.debug("No tenant ID available")
        return None
    
    sb = get_supabase_db()
    if not sb:
        logger.debug("Supabase client not available")
        return None
    
    try:
        # Query org_profile_config table
        query = sb.table("org_profile_config").select("*").eq("organization", tenant_id)
        
        if product:
            # Filter by product name in products JSONB array
            query = query.contains("products", [{"product_name": product}])
        
        result = query.execute()
        
        if result.data:
            org_config_data = result.data[0]
            products = org_config_data.get("products", [])
            
            if not products:
                return None
            
            # Find matching product or use first one
            product_config = None
            if product:
                for p in products:
                    if p.get("product_name", "").lower() == product.lower():
                        product_config = p
                        break
            
            if not product_config and products:
                product_config = products[0]
            
            if product_config:
                return OrgProductConfig.from_dict(product_config)
        
        return None
        
    except Exception as e:
        logger.error(f"Error loading org product config: {e}")
        return None


def save_org_product_config(
    tenant_id: str,
    product_config: OrgProductConfig
) -> bool:
    """
    Save organization product configuration to database.
    
    Args:
        tenant_id: Organization identifier
        product_config: Product configuration to save
    
    Returns:
        True if successful, False otherwise
    """
    if not SUPABASE_AVAILABLE:
        logger.error("Supabase not available, cannot save org config")
        return False
    
    sb = get_supabase_db()
    if not sb:
        logger.error("Supabase client not available")
        return False
    
    try:
        # Check if org config exists
        existing = sb.table("org_profile_config").select("*").eq("organization", tenant_id).execute()
        
        product_dict = product_config.to_dict()
        
        if existing.data:
            # Update existing config
            org_config = existing.data[0]
            products = org_config.get("products", [])
            
            # Update or add product
            updated = False
            for i, p in enumerate(products):
                if p.get("product_name", "").lower() == product_config.product_name.lower():
                    products[i] = product_dict
                    updated = True
                    break
            
            if not updated:
                products.append(product_dict)
            
            sb.table("org_profile_config").update({
                "products": products
            }).eq("organization", tenant_id).execute()
        else:
            # Create new config
            sb.table("org_profile_config").insert({
                "organization": tenant_id,
                "products": [product_dict]
            }).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving org product config: {e}")
        return False


def get_all_org_products(tenant_id: Optional[str] = None) -> List[str]:
    """
    Get list of all products configured for an organization.
    
    Args:
        tenant_id: Organization identifier (if None, uses current user's org)
    
    Returns:
        List of product names
    """
    if tenant_id is None:
        tenant_id = get_current_tenant_id()
    
    if not tenant_id:
        return []
    
    config = load_org_product_config(tenant_id=tenant_id)
    if config:
        # If we have a config, return its product name
        return [config.product_name]
    
    # Try to get all products from database
    if not SUPABASE_AVAILABLE:
        return []
    
    sb = get_supabase_db()
    if not sb:
        return []
    
    try:
        result = sb.table("org_profile_config").select("products").eq("organization", tenant_id).execute()
        if result.data and result.data[0].get("products"):
            return [p.get("product_name", "") for p in result.data[0]["products"] if p.get("product_name")]
    except Exception as e:
        logger.error(f"Error getting org products: {e}")
    
    return []

