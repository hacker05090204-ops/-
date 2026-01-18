"""
Boundary Manager - Enforces exploration boundaries and resource limits

ARCHITECTURAL CONSTRAINTS:
    1. NEVER claims completeness — only reports what was explored
    2. GlobalExplorationBudget is thread-safe with atomic operations
    3. generate_exploration_summary is distinct from MCP's CoverageReport
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from .types import (
    Hypothesis,
    ExplorationBoundary,
    ExplorationStats,
    ExplorationSummary,
    BoundaryStatus,
)

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class AtomicInt:
    """Thread-safe atomic integer for budget tracking."""
    
    def __init__(self, initial: int):
        self._value = initial
        self._lock = threading.Lock()
    
    def get(self) -> int:
        """Get current value."""
        with self._lock:
            return self._value
    
    def decrement(self) -> int:
        """Atomically decrement and return new value."""
        with self._lock:
            self._value -= 1
            return self._value
    
    def try_consume(self) -> bool:
        """Try to consume one unit. Returns False if exhausted."""
        with self._lock:
            if self._value > 0:
                self._value -= 1
                return True
            return False


class GlobalExplorationBudget:
    """Thread-safe global budget shared across all exploration threads.
    
    ARCHITECTURAL CONSTRAINT:
        This budget is shared across parallel threads to prevent
        budget explosion. All threads must check and consume from
        this shared budget.
    """
    
    def __init__(self, boundary: ExplorationBoundary):
        self._boundary = boundary
        self._remaining_actions = AtomicInt(boundary.max_actions)
        self._remaining_submissions = AtomicInt(boundary.max_mcp_submissions)
        self._start_time = _utc_now()
        self._lock = threading.Lock()
    
    def consume_action(self) -> bool:
        """Atomically consume one action.
        
        Returns:
            True if action was consumed, False if budget exhausted
        """
        return self._remaining_actions.try_consume()
    
    def consume_submission(self) -> bool:
        """Atomically consume one MCP submission.
        
        Returns:
            True if submission was consumed, False if budget exhausted
        """
        return self._remaining_submissions.try_consume()
    
    def get_remaining_actions(self) -> int:
        """Get remaining action budget."""
        return self._remaining_actions.get()
    
    def get_remaining_submissions(self) -> int:
        """Get remaining MCP submission budget."""
        return self._remaining_submissions.get()
    
    def get_elapsed_seconds(self) -> float:
        """Get elapsed time since budget creation."""
        return (_utc_now() - self._start_time).total_seconds()
    
    def is_time_exceeded(self) -> bool:
        """Check if time limit is exceeded."""
        return self.get_elapsed_seconds() > self._boundary.max_time_seconds
    
    def is_exhausted(self) -> bool:
        """Check if any budget is exhausted."""
        return (
            self._remaining_actions.get() <= 0 or
            self._remaining_submissions.get() <= 0 or
            self.is_time_exceeded()
        )
    
    def get_status(self) -> BoundaryStatus:
        """Get current boundary status."""
        if self.is_exhausted():
            return BoundaryStatus.EXCEEDED
        
        # Check if approaching limits (within 10%)
        action_ratio = self._remaining_actions.get() / self._boundary.max_actions
        submission_ratio = self._remaining_submissions.get() / self._boundary.max_mcp_submissions
        time_ratio = 1 - (self.get_elapsed_seconds() / self._boundary.max_time_seconds)
        
        min_ratio = min(action_ratio, submission_ratio, time_ratio)
        
        if min_ratio <= 0:
            return BoundaryStatus.LIMIT_REACHED
        elif min_ratio <= 0.1:
            return BoundaryStatus.APPROACHING_LIMIT
        else:
            return BoundaryStatus.WITHIN_BOUNDS


class BoundaryManager:
    """Manages exploration boundaries and resource limits.
    
    ARCHITECTURAL CONSTRAINTS:
        1. NEVER claims completeness
        2. generate_exploration_summary is NOT MCP's CoverageReport
        3. Stops exploration when boundaries reached
    """
    
    def __init__(self, boundary: Optional[ExplorationBoundary] = None):
        self._boundary = boundary or ExplorationBoundary()
        self._budget = GlobalExplorationBudget(self._boundary)
        self._start_time = _utc_now()
    
    @property
    def budget(self) -> GlobalExplorationBudget:
        """Get the global exploration budget."""
        return self._budget
    
    def check_boundaries(self, stats: ExplorationStats) -> BoundaryStatus:
        """Check if exploration boundaries are reached.
        
        Args:
            stats: Current exploration statistics
            
        Returns:
            BoundaryStatus indicating current state
        """
        # Check budget status
        budget_status = self._budget.get_status()
        
        if budget_status in [BoundaryStatus.EXCEEDED, BoundaryStatus.LIMIT_REACHED]:
            return budget_status
        
        # Check depth (if tracked in stats)
        # Note: Depth tracking would be implemented in the main orchestrator
        
        return budget_status
    
    def can_continue(self) -> bool:
        """Check if exploration can continue within boundaries."""
        return not self._budget.is_exhausted()
    
    def consume_action(self) -> bool:
        """Try to consume an action from the budget.
        
        Returns:
            True if action was consumed, False if budget exhausted
        """
        return self._budget.consume_action()
    
    def consume_submission(self) -> bool:
        """Try to consume an MCP submission from the budget.
        
        Returns:
            True if submission was consumed, False if budget exhausted
        """
        return self._budget.consume_submission()
    
    def prioritize_remaining(
        self, 
        hypotheses: List[Hypothesis], 
        remaining_budget: Optional[GlobalExplorationBudget] = None
    ) -> List[Hypothesis]:
        """Prioritize remaining hypotheses within budget.
        
        When budget is limited, prioritize hypotheses with highest
        testability (easiest to test) to maximize coverage.
        
        Args:
            hypotheses: List of hypotheses to prioritize
            remaining_budget: Budget to consider (uses internal if None)
            
        Returns:
            Prioritized list of hypotheses
        """
        budget = remaining_budget or self._budget
        
        # Sort by testability (highest first)
        sorted_hypotheses = sorted(
            hypotheses,
            key=lambda h: h.testability_score,
            reverse=True
        )
        
        # Limit to remaining budget
        remaining_actions = budget.get_remaining_actions()
        remaining_submissions = budget.get_remaining_submissions()
        
        # Each hypothesis needs at least 1 action and 1 submission
        max_hypotheses = min(remaining_actions, remaining_submissions)
        
        return sorted_hypotheses[:max_hypotheses]
    
    def generate_exploration_summary(
        self, 
        stats: ExplorationStats,
        target: str = "",
        hypotheses_tested: Optional[List[str]] = None,
        strategies_used: Optional[List[str]] = None,
        stopped_reason: str = ""
    ) -> ExplorationSummary:
        """Generate summary of what was explored.
        
        CRITICAL: This is an EXPLORATION summary, NOT a coverage report.
        MCP's CoverageReport is authoritative for invariant coverage.
        This summary only reports what Cyfer Brain explored.
        
        IMPORTANT: This summary does NOT claim completeness.
        
        Args:
            stats: Exploration statistics
            target: Target that was explored
            hypotheses_tested: List of hypothesis IDs that were tested
            strategies_used: List of strategy names that were used
            stopped_reason: Reason exploration stopped
            
        Returns:
            ExplorationSummary (NOT claiming completeness)
        """
        return ExplorationSummary(
            target=target,
            stats=stats,
            hypotheses_tested=hypotheses_tested or [],
            strategies_used=strategies_used or [],
            boundary_status=self._budget.get_status(),
            stopped_reason=stopped_reason or self._determine_stop_reason(),
            started_at=self._start_time,
            completed_at=_utc_now(),
            # NOTE: No coverage_percentage — we don't claim completeness
        )
    
    def _determine_stop_reason(self) -> str:
        """Determine why exploration stopped."""
        if self._budget.get_remaining_actions() <= 0:
            return "Action budget exhausted"
        elif self._budget.get_remaining_submissions() <= 0:
            return "MCP submission budget exhausted"
        elif self._budget.is_time_exceeded():
            return "Time limit exceeded"
        else:
            return "Exploration completed within boundaries"
    
    def get_boundary(self) -> ExplorationBoundary:
        """Get the exploration boundary configuration."""
        return self._boundary
    
    def reset(self, boundary: Optional[ExplorationBoundary] = None) -> None:
        """Reset the boundary manager with optional new boundary."""
        self._boundary = boundary or self._boundary
        self._budget = GlobalExplorationBudget(self._boundary)
        self._start_time = _utc_now()
