"""
Reviewer Registry (PART 2)
Dynamic registry supporting unlimited reviewers with CRUD operations, search, and filtering.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from .reviewer import Reviewer


class ReviewerRegistry:
    """
    Dynamic reviewer registry supporting unlimited reviewers.
    
    Provides CRUD operations, skill-based filtering, TA matching,
    and smart search capabilities.
    """
    
    def __init__(self):
        """Initialize empty reviewer registry."""
        self.reviewers: Dict[str, Reviewer] = {}
    
    # ------------------------
    # CRUD OPERATIONS
    # ------------------------
    
    def add_reviewer(self, reviewer: Reviewer) -> bool:
        """
        Add a reviewer to the registry.
        
        Args:
            reviewer: Reviewer instance
            
        Returns:
            True if added successfully
        """
        if not isinstance(reviewer, Reviewer):
            return False
        
        self.reviewers[reviewer.reviewer_id] = reviewer
        reviewer.update_metadata()
        return True
    
    def get_reviewer(self, reviewer_id: str) -> Optional[Reviewer]:
        """Get reviewer by ID."""
        return self.reviewers.get(reviewer_id)
    
    def get_reviewer_by_name(self, name: str) -> Optional[Reviewer]:
        """Get reviewer by name (case-insensitive)."""
        name_lower = name.lower()
        for reviewer in self.reviewers.values():
            if reviewer.name.lower() == name_lower:
                return reviewer
        return None
    
    def update_reviewer(self, reviewer_id: str, **updates) -> bool:
        """
        Update reviewer fields.
        
        Args:
            reviewer_id: Reviewer ID
            **updates: Keyword arguments for fields to update
            
        Returns:
            True if updated successfully
        """
        reviewer = self.get_reviewer(reviewer_id)
        if not reviewer:
            return False
        
        for key, value in updates.items():
            if hasattr(reviewer, key):
                setattr(reviewer, key, value)
        
        reviewer.update_metadata()
        return True
    
    def delete_reviewer(self, reviewer_id: str) -> bool:
        """Delete reviewer from registry."""
        if reviewer_id in self.reviewers:
            del self.reviewers[reviewer_id]
            return True
        return False
    
    # ------------------------
    # SEARCH / FILTERING
    # ------------------------
    
    def find_by_skill(self, skill: str) -> List[Reviewer]:
        """Find reviewers by skill (case-insensitive partial match)."""
        skill_lower = skill.lower()
        return [
            reviewer for reviewer in self.reviewers.values()
            if any(skill_lower in sk.lower() for sk in reviewer.skills)
        ]
    
    def find_by_therapeutic_area(self, ta: str) -> List[Reviewer]:
        """Find reviewers by therapeutic area (case-insensitive partial match)."""
        ta_lower = ta.lower()
        return [
            reviewer for reviewer in self.reviewers.values()
            if any(ta_lower in area.lower() for area in reviewer.therapeutic_areas)
        ]
    
    def find_available(self, month: Optional[str] = None) -> List[Reviewer]:
        """Find reviewers available for a given month."""
        return [
            reviewer for reviewer in self.reviewers.values()
            if reviewer.is_available(month)
        ]
    
    def find_by_capacity(self, min_capacity: int = 0, max_capacity: Optional[int] = None) -> List[Reviewer]:
        """Find reviewers by capacity range."""
        results = []
        for reviewer in self.reviewers.values():
            capacity = reviewer.max_cases_per_week
            if capacity >= min_capacity:
                if max_capacity is None or capacity <= max_capacity:
                    results.append(reviewer)
        return results
    
    def get_lowest_load(self) -> Optional[Reviewer]:
        """Get reviewer with lowest current queue load."""
        if not self.reviewers:
            return None
        
        return min(self.reviewers.values(), key=lambda r: r.current_queue)
    
    def get_least_burdened(self) -> Optional[Reviewer]:
        """Get reviewer with lowest projected burden."""
        if not self.reviewers:
            return None
        
        return min(self.reviewers.values(), key=lambda r: r.projected_burden)
    
    def search(self, query: str) -> List[Reviewer]:
        """
        Smart fuzzy search across name, skills, therapeutic areas, title.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching reviewers
        """
        query_lower = query.lower()
        results = []
        
        for reviewer in self.reviewers.values():
            # Search in name
            if query_lower in reviewer.name.lower():
                results.append(reviewer)
                continue
            
            # Search in title
            if reviewer.title and query_lower in reviewer.title.lower():
                results.append(reviewer)
                continue
            
            # Search in skills
            if any(query_lower in skill.lower() for skill in reviewer.skills):
                results.append(reviewer)
                continue
            
            # Search in therapeutic areas
            if any(query_lower in area.lower() for area in reviewer.therapeutic_areas):
                results.append(reviewer)
                continue
        
        return results
    
    def filter_by_performance(
        self,
        min_quality_score: float = 0.0,
        max_overdue_rate: float = 1.0
    ) -> List[Reviewer]:
        """Filter reviewers by performance metrics."""
        return [
            reviewer for reviewer in self.reviewers.values()
            if reviewer.quality_score >= min_quality_score
            and reviewer.overdue_rate <= max_overdue_rate
        ]
    
    # ------------------------
    # INTERNAL UTILITIES
    # ------------------------
    
    def list_all(self) -> List[Reviewer]:
        """Get all reviewers."""
        return list(self.reviewers.values())
    
    def size(self) -> int:
        """Get total number of reviewers."""
        return len(self.reviewers)
    
    def clear(self):
        """Clear all reviewers from registry."""
        self.reviewers.clear()
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert all reviewers to list of dictionaries."""
        return [reviewer.to_dict() for reviewer in self.reviewers.values()]
    
    def from_dict_list(self, reviewers_data: List[Dict[str, Any]]):
        """Load reviewers from list of dictionaries."""
        self.clear()
        for data in reviewers_data:
            reviewer = Reviewer.from_dict(data)
            self.add_reviewer(reviewer)
    
    def get_total_capacity(self, month: Optional[str] = None) -> float:
        """
        Calculate total capacity across all reviewers for a given month.
        
        Args:
            month: Optional month identifier (e.g., "2025-01")
            
        Returns:
            Total available capacity (cases per week)
        """
        total = 0.0
        for reviewer in self.reviewers.values():
            if reviewer.is_available(month):
                availability = reviewer.get_available_capacity(month)
                total += reviewer.max_cases_per_week * availability
        return total
    
    def get_total_queue_size(self) -> int:
        """Get total current queue size across all reviewers."""
        return sum(reviewer.current_queue for reviewer in self.reviewers.values())
    
    def get_average_quality_score(self) -> float:
        """Get average quality score across all reviewers."""
        if not self.reviewers:
            return 0.0
        
        total = sum(reviewer.quality_score for reviewer in self.reviewers.values())
        return total / len(self.reviewers)

