"""
Reviewer Data Model (PART 2)
Enterprise-grade reviewer model supporting unlimited reviewers with skills, capacity, and performance metrics.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


@dataclass
class Reviewer:
    """
    Reviewer model with capacity, skills, performance, and conflict-of-interest metadata.
    
    Supports unlimited reviewers with dynamic capacity and skill sets.
    """
    reviewer_id: str
    name: str
    title: Optional[str] = None
    
    # Skill/TA mapping
    therapeutic_areas: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    
    # Capacity model
    max_cases_per_week: int = 25  # Default: 25 cases/week
    max_signals_per_week: int = 3  # For safety leads
    availability: Dict[str, float] = field(default_factory=dict)  # Month -> availability (0.0-1.0)
    timezone: Optional[str] = "UTC"
    
    # Historical performance metadata
    avg_turnaround_days: float = 5.0
    overdue_rate: float = 0.05  # Percentage (0.05 = 5%)
    quality_score: float = 0.90  # Accuracy score (0.0-1.0)
    
    # Conflict of interest metadata
    restricted_products: List[str] = field(default_factory=list)
    competing_products: List[str] = field(default_factory=list)
    
    # For simulations + workload forecasts
    current_queue: int = 0
    projected_burden: int = 0
    last_assigned: Optional[str] = None  # ISO format datetime string
    
    # Custom info
    notes: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None
    
    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if not self.reviewer_id:
            self.reviewer_id = str(uuid.uuid4())
        
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
        
        # Ensure availability is normalized
        if self.availability:
            normalized_avail = {}
            for key, value in self.availability.items():
                # Normalize to 0.0-1.0 range
                if isinstance(value, (int, float)):
                    normalized_avail[key] = max(0.0, min(1.0, float(value)))
                else:
                    normalized_avail[key] = 1.0
            self.availability = normalized_avail
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reviewer to dictionary for storage/serialization."""
        return {
            "reviewer_id": self.reviewer_id,
            "name": self.name,
            "title": self.title,
            "therapeutic_areas": self.therapeutic_areas,
            "skills": self.skills,
            "max_cases_per_week": self.max_cases_per_week,
            "max_signals_per_week": self.max_signals_per_week,
            "availability": self.availability,
            "timezone": self.timezone,
            "avg_turnaround_days": self.avg_turnaround_days,
            "overdue_rate": self.overdue_rate,
            "quality_score": self.quality_score,
            "restricted_products": self.restricted_products,
            "competing_products": self.competing_products,
            "current_queue": self.current_queue,
            "projected_burden": self.projected_burden,
            "last_assigned": self.last_assigned,
            "notes": self.notes,
            "email": self.email,
            "organization": self.organization,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reviewer':
        """Create reviewer from dictionary (deserialization)."""
        return cls(
            reviewer_id=data.get("reviewer_id", str(uuid.uuid4())),
            name=data.get("name", "Unknown"),
            title=data.get("title"),
            therapeutic_areas=data.get("therapeutic_areas", []),
            skills=data.get("skills", []),
            max_cases_per_week=data.get("max_cases_per_week", 25),
            max_signals_per_week=data.get("max_signals_per_week", 3),
            availability=data.get("availability", {}),
            timezone=data.get("timezone", "UTC"),
            avg_turnaround_days=data.get("avg_turnaround_days", 5.0),
            overdue_rate=data.get("overdue_rate", 0.05),
            quality_score=data.get("quality_score", 0.90),
            restricted_products=data.get("restricted_products", []),
            competing_products=data.get("competing_products", []),
            current_queue=data.get("current_queue", 0),
            projected_burden=data.get("projected_burden", 0),
            last_assigned=data.get("last_assigned"),
            notes=data.get("notes"),
            email=data.get("email"),
            organization=data.get("organization"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def update_metadata(self):
        """Update timestamp when reviewer is modified."""
        self.updated_at = datetime.now().isoformat()
    
    def is_available(self, month: Optional[str] = None) -> bool:
        """Check if reviewer is available for a given month."""
        if not self.availability:
            return True  # Default to available
        
        if month:
            avail = self.availability.get(month, 1.0)
            return avail > 0.0
        
        # Check overall availability
        if self.availability:
            # If any month has availability > 0, reviewer is available
            return any(v > 0.0 for v in self.availability.values())
        
        return True
    
    def get_available_capacity(self, month: Optional[str] = None) -> float:
        """Get available capacity for a given month (0.0-1.0)."""
        if month and month in self.availability:
            return self.availability[month]
        elif self.availability:
            # Average availability
            return sum(self.availability.values()) / len(self.availability)
        else:
            return 1.0  # Fully available if not specified

