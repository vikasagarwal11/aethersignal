"""
Reviewer Capacity Model (CHUNK B9.1)
Base model for reviewer throughput, staffing forecasting, and SLA-driven workload simulation.
"""
from typing import Dict, Any, List, Optional
import math


class ReviewerCapacityModel:
    """
    Base model for reviewer throughput and capacity planning.
    
    Future enhancements (B9.2+) will include:
    - Seasonality modeling
    - Reviewer-specific performance profiles
    - Complexity-weighted queues
    - SLA curves and breach prediction
    - Multi-reviewer team simulation
    """
    
    def __init__(self):
        """
        Initialize capacity model.
        
        Future: Load reviewer performance metrics from DB or uploaded metadata.
        """
        # Base throughput assumptions
        self.base_review_rate = 12  # signals/day (avg reviewer throughput)
        self.working_hours_per_day = 8
        self.working_days_per_week = 5
        self.signals_per_week = self.base_review_rate * self.working_days_per_week
    
    def estimate_hours_per_signal(self, complexity: float = 1.0) -> float:
        """
        Estimate hours required per signal based on complexity.
        
        Args:
            complexity: Complexity multiplier
                1.0 = average complexity
                0.5 = simple (routine monitoring)
                2.0 = complex (high severity, multiple reactions, regulatory urgency)
        
        Returns:
            Estimated hours per signal
        """
        # Base: 8 hours / (12 signals/day) = 0.67 hours per signal
        base_hours = self.working_hours_per_day / self.base_review_rate
        
        return round(base_hours * complexity, 2)
    
    def project_sla_risk(
        self,
        incoming_signals: int,
        reviewers: int,
        time_horizon_days: int = 30
    ) -> Dict[str, Any]:
        """
        Simple M/M/1-inspired projection of SLA breach risk.
        
        Heavy version (B9.2) will include:
        - Seasonality effects
        - Reviewer performance differences
        - Signal complexity weighting
        - SLA deadline distribution
        - Queue prioritization
        
        Args:
            incoming_signals: Expected number of signals in time horizon
            reviewers: Number of available reviewers
            time_horizon_days: Days to forecast ahead
            
        Returns:
            Dictionary with utilization and SLA risk assessment
        """
        # Capacity: reviewers × signals per reviewer per day × days
        daily_capacity = reviewers * self.base_review_rate
        total_capacity = daily_capacity * time_horizon_days
        
        # Utilization rate
        utilization = incoming_signals / total_capacity if total_capacity > 0 else 1.0
        
        # Classify risk
        if utilization > 1.0:
            sla_breach_risk = "CRITICAL"
            risk_score = 100
        elif utilization > 0.85:
            sla_breach_risk = "HIGH"
            risk_score = 75
        elif utilization > 0.70:
            sla_breach_risk = "MEDIUM"
            risk_score = 50
        elif utilization > 0.50:
            sla_breach_risk = "LOW"
            risk_score = 25
        else:
            sla_breach_risk = "MINIMAL"
            risk_score = 10
        
        # Calculate backlog growth
        if utilization > 1.0:
            backlog_growth = incoming_signals - total_capacity
        else:
            backlog_growth = 0
        
        return {
            "incoming_signals": incoming_signals,
            "reviewers": reviewers,
            "time_horizon_days": time_horizon_days,
            "daily_capacity": daily_capacity,
            "total_capacity": total_capacity,
            "utilization": round(utilization, 3),
            "sla_breach_risk": sla_breach_risk,
            "risk_score": risk_score,
            "backlog_growth": max(0, backlog_growth),
            "capacity_deficit": max(0, backlog_growth)  # Signals that can't be processed
        }
    
    def estimate_reviewer_need(
        self,
        incoming_signals: int,
        target_utilization: float = 0.75,
        time_horizon_days: int = 30
    ) -> Dict[str, Any]:
        """
        Estimate how many reviewers are needed to meet target utilization.
        
        Args:
            incoming_signals: Expected number of signals
            target_utilization: Target utilization rate (0.0 - 1.0)
            time_horizon_days: Days to forecast ahead
            
        Returns:
            Dictionary with reviewer requirements
        """
        if target_utilization <= 0:
            target_utilization = 0.75  # Default to 75%
        
        # Required capacity
        required_daily_capacity = incoming_signals / time_horizon_days
        
        # Required reviewers
        required_reviewers = math.ceil(required_daily_capacity / (self.base_review_rate * target_utilization))
        
        # Current capacity check
        actual_capacity = required_reviewers * self.base_review_rate * time_horizon_days
        actual_utilization = incoming_signals / actual_capacity if actual_capacity > 0 else 1.0
        
        return {
            "incoming_signals": incoming_signals,
            "time_horizon_days": time_horizon_days,
            "target_utilization": target_utilization,
            "required_reviewers": required_reviewers,
            "required_daily_capacity": round(required_daily_capacity, 1),
            "actual_utilization": round(actual_utilization, 3),
            "capacity_available": round(actual_capacity - incoming_signals, 0)
        }
    
    def calculate_throughput(
        self,
        reviewers: int,
        complexity_avg: float = 1.0,
        efficiency_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate expected throughput for a reviewer team.
        
        Args:
            reviewers: Number of reviewers
            complexity_avg: Average complexity multiplier
            efficiency_factor: Team efficiency (1.0 = 100%, can be < 1.0 for overhead)
        
        Returns:
            Throughput metrics
        """
        # Adjust review rate by complexity
        adjusted_rate = self.base_review_rate / complexity_avg
        
        # Apply efficiency factor
        effective_rate = adjusted_rate * efficiency_factor
        
        daily_throughput = reviewers * effective_rate
        weekly_throughput = daily_throughput * self.working_days_per_week
        monthly_throughput = daily_throughput * 22  # Approx 22 working days per month
        
        return {
            "reviewers": reviewers,
            "complexity_avg": complexity_avg,
            "efficiency_factor": efficiency_factor,
            "signals_per_reviewer_per_day": round(effective_rate, 1),
            "daily_throughput": round(daily_throughput, 1),
            "weekly_throughput": round(weekly_throughput, 1),
            "monthly_throughput": round(monthly_throughput, 1)
        }
    
    def estimate_backlog_clearance(
        self,
        current_backlog: int,
        reviewers: int,
        new_incoming_rate: float = 0.0  # signals per day
    ) -> Dict[str, Any]:
        """
        Estimate time to clear backlog given current reviewer capacity.
        
        Args:
            current_backlog: Current number of signals in backlog
            reviewers: Number of reviewers available
            new_incoming_rate: New signals arriving per day
        
        Returns:
            Backlog clearance projection
        """
        daily_processing_rate = reviewers * self.base_review_rate
        
        # Net processing rate (after accounting for new arrivals)
        net_daily_rate = daily_processing_rate - new_incoming_rate
        
        if net_daily_rate <= 0:
            # Backlog will grow
            days_to_clear = None
            backlog_will_grow = True
            daily_growth = new_incoming_rate - daily_processing_rate
        else:
            # Backlog will clear
            days_to_clear = math.ceil(current_backlog / net_daily_rate)
            backlog_will_grow = False
            daily_growth = 0
        
        return {
            "current_backlog": current_backlog,
            "reviewers": reviewers,
            "daily_processing_rate": daily_processing_rate,
            "new_incoming_rate": new_incoming_rate,
            "net_daily_rate": round(net_daily_rate, 1) if net_daily_rate > 0 else 0,
            "days_to_clear": days_to_clear,
            "backlog_will_grow": backlog_will_grow,
            "daily_growth": round(daily_growth, 1) if backlog_will_grow else 0,
            "weeks_to_clear": round(days_to_clear / 7, 1) if days_to_clear else None
        }

