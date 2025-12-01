"""
Reviewer Storage Engine (PART 3)
Hybrid 3-tier storage: Session State → Browser IndexedDB → Supabase
Automatic fallback and conflict resolution.
"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

import streamlit as st

try:
    from src.models.reviewer import Reviewer
    from src.models.reviewer_registry import ReviewerRegistry
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    Reviewer = None
    ReviewerRegistry = None

# Optional Supabase support - try multiple import paths
SUPABASE_AVAILABLE = False
get_supabase_client = None

try:
    from src.social_ae.supabase_client import get_supabase
    get_supabase_client = get_supabase
    SUPABASE_AVAILABLE = True
except ImportError:
    try:
        from src.pv_storage import get_supabase_db
        get_supabase_client = lambda: get_supabase_db(use_service_key=True)
        SUPABASE_AVAILABLE = True
    except ImportError:
        try:
            from src.social_ae.social_ae_supabase import get_supabase_client
            SUPABASE_AVAILABLE = True
        except ImportError:
            SUPABASE_AVAILABLE = False


class ReviewerStorage:
    """
    Hybrid storage engine supporting 3 tiers:
    1. Streamlit session_state (always available, fastest)
    2. Browser IndexedDB (local persistence, offline-capable)
    3. Supabase cloud storage (enterprise persistence, multi-user)
    
    Automatic fallback: Supabase → Browser → Session
    """
    
    SESSION_KEY = "reviewer_registry"
    BROWSER_KEY = "aether_reviewers"
    SUPABASE_TABLE = "reviewers"
    
    def __init__(self):
        """Initialize storage engine with session state registry."""
        if not MODELS_AVAILABLE:
            raise ImportError("Reviewer models not available. Install required dependencies.")
        
        # Initialize session state registry if not exists
        if ReviewerStorage.SESSION_KEY not in st.session_state:
            st.session_state[ReviewerStorage.SESSION_KEY] = ReviewerRegistry()
        
        self.registry: ReviewerRegistry = st.session_state[ReviewerStorage.SESSION_KEY]
    
    # ------------------------------------------------------------------
    # Core CRUD Operations (operates on session registry)
    # ------------------------------------------------------------------
    
    def add_reviewer(self, reviewer: Reviewer) -> bool:
        """
        Add a reviewer to the registry.
        
        Args:
            reviewer: Reviewer instance or dictionary
            
        Returns:
            True if added successfully
        """
        if isinstance(reviewer, dict):
            reviewer = Reviewer.from_dict(reviewer)
        
        if not isinstance(reviewer, Reviewer):
            return False
        
        success = self.registry.add_reviewer(reviewer)
        return success
    
    def get_reviewer(self, reviewer_id: str) -> Optional[Reviewer]:
        """Get reviewer by ID."""
        return self.registry.get_reviewer(reviewer_id)
    
    def get_all_reviewers(self) -> List[Reviewer]:
        """Get all reviewers."""
        return self.registry.list_all()
    
    def update_reviewer(self, reviewer_id: str, **updates) -> bool:
        """
        Update reviewer fields.
        
        Args:
            reviewer_id: Reviewer ID
            **updates: Keyword arguments for fields to update
            
        Returns:
            True if updated successfully
        """
        return self.registry.update_reviewer(reviewer_id, **updates)
    
    def delete_reviewer(self, reviewer_id: str) -> bool:
        """Delete reviewer from registry."""
        return self.registry.delete_reviewer(reviewer_id)
    
    # ------------------------------------------------------------------
    # Serialization Utilities
    # ------------------------------------------------------------------
    
    def serialize(self, reviewer: Reviewer) -> Dict[str, Any]:
        """Convert reviewer to dictionary for storage."""
        return reviewer.to_dict()
    
    def deserialize(self, data: Dict[str, Any]) -> Reviewer:
        """Create reviewer from dictionary."""
        return Reviewer.from_dict(data)
    
    # ------------------------------------------------------------------
    # Browser IndexedDB Storage (Client-side)
    # ------------------------------------------------------------------
    
    def export_for_browser(self) -> List[Dict[str, Any]]:
        """
        Export reviewers to JSON format for browser storage.
        
        Returns:
            List of reviewer dictionaries ready for JSON serialization
        """
        return [
            self.serialize(reviewer)
            for reviewer in self.registry.list_all()
        ]
    
    def import_from_browser(self, browser_json: List[Dict[str, Any]]) -> int:
        """
        Import reviewers from browser JSON.
        
        Args:
            browser_json: List of reviewer dictionaries from browser storage
            
        Returns:
            Number of reviewers imported
        """
        count = 0
        for data in browser_json:
            try:
                reviewer = self.deserialize(data)
                if self.registry.add_reviewer(reviewer):
                    count += 1
            except Exception as e:
                # Skip invalid entries
                continue
        return count
    
    def save_to_browser_storage(self) -> bool:
        """
        Save reviewers to browser local storage via JavaScript injection.
        
        Returns:
            True if save initiated (actual save happens in browser)
        """
        try:
            browser_data = self.export_for_browser()
            json_str = json.dumps(browser_data)
            
            # Inject JavaScript to save to localStorage
            script = f"""
            <script>
                localStorage.setItem('{ReviewerStorage.BROWSER_KEY}', {json.dumps(json_str)});
            </script>
            """
            st.components.v1.html(script, height=0)
            
            return True
        except Exception:
            return False
    
    def load_from_browser_storage(self) -> int:
        """
        Load reviewers from browser local storage via JavaScript.
        
        Returns:
            Number of reviewers loaded
        """
        try:
            # Use JavaScript to read from localStorage
            script = f"""
            <script>
                const data = localStorage.getItem('{ReviewerStorage.BROWSER_KEY}');
                window.parent.postMessage({{type: 'reviewer_data', data: data}}, '*');
            </script>
            """
            
            # In a real implementation, we'd use Streamlit's JavaScript bridge
            # For now, return 0 (will be enhanced with proper browser communication)
            return 0
        except Exception:
            return 0
    
    # ------------------------------------------------------------------
    # Supabase Sync Layer (Enterprise)
    # ------------------------------------------------------------------
    
    def sync_to_supabase(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Push all reviewers to Supabase cloud storage.
        
        Args:
            organization_id: Optional organization ID for multi-tenancy
            
        Returns:
            Dictionary with sync status and count
        """
        if not SUPABASE_AVAILABLE or get_supabase_client is None:
            return {
                "status": "error",
                "message": "Supabase not available or not configured"
            }
        
        try:
            supabase = get_supabase_client()
            if not supabase:
                return {
                    "status": "error",
                    "message": "Could not connect to Supabase"
                }
            
            # Serialize all reviewers
            records = []
            for reviewer in self.registry.list_all():
                reviewer_dict = self.serialize(reviewer)
                
                # Add organization_id for multi-tenancy
                if organization_id:
                    reviewer_dict["organization_id"] = organization_id
                
                # Ensure updated_at is current
                reviewer_dict["updated_at"] = datetime.now().isoformat()
                
                records.append(reviewer_dict)
            
            if not records:
                return {
                    "status": "ok",
                    "synced": 0,
                    "message": "No reviewers to sync"
                }
            
            # Upsert to Supabase (update if exists, insert if new)
            resp = supabase.table(self.SUPABASE_TABLE).upsert(records).execute()
            
            return {
                "status": "ok",
                "synced": len(records),
                "message": f"Successfully synced {len(records)} reviewer(s) to Supabase"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Supabase sync error: {str(e)}"
            }
    
    def pull_from_supabase(self, organization_id: Optional[str] = None) -> int:
        """
        Load reviewers from Supabase into registry.
        
        Args:
            organization_id: Optional organization ID for filtering
            
        Returns:
            Number of reviewers loaded
        """
        if not SUPABASE_AVAILABLE or get_supabase_client is None:
            return 0
        
        try:
            supabase = get_supabase_client()
            if not supabase:
                return 0
            
            # Build query
            query = supabase.table(self.SUPABASE_TABLE).select("*")
            
            # Filter by organization if provided
            if organization_id:
                query = query.eq("organization_id", organization_id)
            
            resp = query.execute()
            
            if not resp.data:
                return 0
            
            count = 0
            for row in resp.data:
                try:
                    # Remove organization_id before deserializing
                    reviewer_data = {k: v for k, v in row.items() if k != "organization_id"}
                    reviewer = self.deserialize(reviewer_data)
                    
                    if self.registry.add_reviewer(reviewer):
                        count += 1
                except Exception:
                    # Skip invalid entries
                    continue
            
            return count
        except Exception as e:
            return 0
    
    # ------------------------------------------------------------------
    # Conflict Resolution & Merging
    # ------------------------------------------------------------------
    
    def merge_sources(
        self,
        session_reviewers: List[Reviewer],
        browser_reviewers: Optional[List[Reviewer]] = None,
        supabase_reviewers: Optional[List[Reviewer]] = None
    ) -> ReviewerRegistry:
        """
        Merge reviewers from multiple sources using priority: Supabase > Browser > Session.
        
        Args:
            session_reviewers: Reviewers from session state
            browser_reviewers: Reviewers from browser storage (optional)
            supabase_reviewers: Reviewers from Supabase (optional)
            
        Returns:
            Merged ReviewerRegistry
        """
        merged = ReviewerRegistry()
        
        # Convert lists to dictionaries by reviewer_id
        all_reviewers = {}
        
        # Priority order: Supabase (highest) > Browser > Session (lowest)
        sources = []
        if supabase_reviewers:
            sources.append(supabase_reviewers)
        if browser_reviewers:
            sources.append(browser_reviewers)
        sources.append(session_reviewers)
        
        # Merge with priority (later sources override earlier ones for same ID)
        for source_list in reversed(sources):  # Reverse to give Supabase highest priority
            for reviewer in source_list:
                all_reviewers[reviewer.reviewer_id] = reviewer
        
        # Add all merged reviewers
        for reviewer in all_reviewers.values():
            merged.add_reviewer(reviewer)
        
        return merged
    
    def sync_all_sources(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync all storage sources (pull from Supabase, merge with session/browser).
        
        Args:
            organization_id: Optional organization ID for Supabase filtering
            
        Returns:
            Sync status dictionary
        """
        # Get current session reviewers
        session_reviewers = self.registry.list_all()
        
        # Try to pull from Supabase
        supabase_count = self.pull_from_supabase(organization_id)
        supabase_reviewers = self.registry.list_all()
        
        # Browser reviewers would be loaded separately if browser storage is implemented
        browser_reviewers = None  # Placeholder for future browser storage implementation
        
        # Merge all sources
        merged_registry = self.merge_sources(
            session_reviewers=session_reviewers,
            browser_reviewers=browser_reviewers,
            supabase_reviewers=supabase_reviewers if supabase_count > 0 else None
        )
        
        # Update session state with merged registry
        st.session_state[ReviewerStorage.SESSION_KEY] = merged_registry
        self.registry = merged_registry
        
        return {
            "status": "ok",
            "session_count": len(session_reviewers),
            "supabase_count": supabase_count,
            "merged_count": merged_registry.size(),
            "message": f"Merged {merged_registry.size()} reviewers from all sources"
        }
    
    # ------------------------------------------------------------------
    # Export/Import Utilities
    # ------------------------------------------------------------------
    
    def export_to_json(self) -> str:
        """Export all reviewers to JSON string."""
        reviewers_data = self.export_for_browser()
        return json.dumps(reviewers_data, indent=2, default=str)
    
    def import_from_json(self, json_str: str) -> int:
        """Import reviewers from JSON string."""
        try:
            reviewers_data = json.loads(json_str)
            if isinstance(reviewers_data, list):
                return self.import_from_browser(reviewers_data)
            return 0
        except Exception:
            return 0
    
    def export_to_csv(self) -> str:
        """Export reviewers to CSV format (for Excel compatibility)."""
        import pandas as pd
        
        reviewers_data = [self.serialize(r) for r in self.registry.list_all()]
        
        if not reviewers_data:
            return ""
        
        # Flatten nested lists (skills, therapeutic_areas) for CSV
        for data in reviewers_data:
            if isinstance(data.get("skills"), list):
                data["skills"] = ", ".join(data["skills"])
            if isinstance(data.get("therapeutic_areas"), list):
                data["therapeutic_areas"] = ", ".join(data["therapeutic_areas"])
            if isinstance(data.get("restricted_products"), list):
                data["restricted_products"] = ", ".join(data["restricted_products"])
        
        df = pd.DataFrame(reviewers_data)
        return df.to_csv(index=False)
    
    def import_from_csv(self, csv_str: str) -> int:
        """Import reviewers from CSV format."""
        import pandas as pd
        
        try:
            df = pd.read_csv(csv_str)
            
            # Convert comma-separated strings back to lists
            if "skills" in df.columns:
                df["skills"] = df["skills"].apply(
                    lambda x: [s.strip() for s in str(x).split(",")] if pd.notna(x) else []
                )
            if "therapeutic_areas" in df.columns:
                df["therapeutic_areas"] = df["therapeutic_areas"].apply(
                    lambda x: [s.strip() for s in str(x).split(",")] if pd.notna(x) else []
                )
            if "restricted_products" in df.columns:
                df["restricted_products"] = df["restricted_products"].apply(
                    lambda x: [s.strip() for s in str(x).split(",")] if pd.notna(x) else []
                )
            
            reviewers_data = df.to_dict(orient="records")
            return self.import_from_browser(reviewers_data)
        except Exception:
            return 0

