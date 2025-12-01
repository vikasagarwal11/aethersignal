"""
Tasking & Assignment Engine (Phase 3H.2)
Manages tasks, assignments, and task routing.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class Task:
    """Represents a task in the workflow."""
    
    def __init__(
        self,
        task_id: str,
        title: str,
        task_type: str,
        bundle_id: Optional[str] = None,
        priority: str = "medium"
    ):
        """Initialize task."""
        self.task_id = task_id
        self.title = title
        self.task_type = task_type
        self.bundle_id = bundle_id
        self.priority = priority
        self.status = "not_started"  # not_started, in_progress, blocked, completed
        self.assigned_to: Optional[str] = None
        self.created_at = datetime.now()
        self.due_date: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.ai_assist_enabled = True
        self.description: Optional[str] = None
        self.notes: List[str] = []
    
    def assign(self, user_id: str):
        """Assign task to user."""
        self.assigned_to = user_id
        self.status = "in_progress"
    
    def complete(self):
        """Mark task as completed."""
        self.status = "completed"
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "type": self.task_type,
            "bundle_id": self.bundle_id,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "ai_assist_enabled": self.ai_assist_enabled
        }


class TaskManager:
    """
    Manages tasks and assignments.
    """
    
    def __init__(self):
        """Initialize task manager."""
        self.tasks: Dict[str, Task] = {}
        self.task_routing_rules = {
            "mechanism": "science_team",
            "regulatory": "regulatory_team",
            "review": "pv_reviewers",
            "documentation": "safety_writers",
            "research": "literature_team"
        }
    
    def create_task(
        self,
        title: str,
        task_type: str,
        bundle_id: Optional[str] = None,
        priority: str = "medium",
        due_days: int = 7
    ) -> Task:
        """
        Create a new task.
        
        Args:
            title: Task title
            task_type: Task type (mechanism, regulatory, review, etc.)
            bundle_id: Optional bundle ID
            priority: Priority level
            due_days: Days until due
        
        Returns:
            Task instance
        """
        task_id = str(uuid.uuid4())
        task = Task(task_id, title, task_type, bundle_id, priority)
        task.due_date = datetime.now() + timedelta(days=due_days)
        
        # Auto-assign based on routing rules
        suggested_team = self.task_routing_rules.get(task_type)
        if suggested_team:
            task.description = f"Suggested assignment: {suggested_team}"
        
        self.tasks[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def list_tasks(
        self,
        assigned_to: Optional[str] = None,
        status: Optional[str] = None,
        bundle_id: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[Task]:
        """List tasks with filters."""
        tasks = list(self.tasks.values())
        
        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if bundle_id:
            tasks = [t for t in tasks if t.bundle_id == bundle_id]
        
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        # Sort by priority and due date
        tasks.sort(key=lambda t: (
            {"high": 0, "medium": 1, "low": 2}.get(t.priority, 3),
            t.due_date or datetime.max
        ))
        
        return tasks
    
    def assign_task(self, task_id: str, user_id: str):
        """Assign task to user."""
        task = self.tasks.get(task_id)
        if task:
            task.assign(user_id)
    
    def complete_task(self, task_id: str):
        """Mark task as completed."""
        task = self.tasks.get(task_id)
        if task:
            task.complete()

