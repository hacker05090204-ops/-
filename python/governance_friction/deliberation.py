"""
Phase-10: Governance & Friction Layer - Deliberation Timer

Enforces minimum consideration time before confirmation.
Uses monotonic clock for reliable timing.
"""

import time
import uuid
from typing import Dict, Tuple

from governance_friction.types import (
    DeliberationRecord,
    MIN_DELIBERATION_SECONDS,
)
from governance_friction.errors import DeliberationTimeViolation


class DeliberationTimer:
    """
    Enforces minimum deliberation time before any confirmation.
    
    SECURITY: This timer ensures humans cannot rubber-stamp decisions.
    It NEVER:
    - Auto-approves after timeout
    - Reduces deliberation time
    - Bypasses the requirement
    
    All timing uses monotonic clock (time.monotonic()) for reliability.
    """
    
    def __init__(self, min_seconds: float = MIN_DELIBERATION_SECONDS):
        """
        Initialize the deliberation timer.
        
        Args:
            min_seconds: Minimum deliberation time. Cannot be less than MIN_DELIBERATION_SECONDS.
        """
        # Enforce HARD minimum
        self._min_seconds = max(min_seconds, MIN_DELIBERATION_SECONDS)
        self._active_deliberations: Dict[str, DeliberationRecord] = {}
    
    @property
    def min_deliberation_seconds(self) -> float:
        """Get the minimum deliberation time (always >= MIN_DELIBERATION_SECONDS)."""
        return self._min_seconds
    
    def start_deliberation(self, decision_id: str) -> DeliberationRecord:
        """
        Start a deliberation period for a decision.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            DeliberationRecord with start time recorded
        """
        record = DeliberationRecord(
            decision_id=decision_id,
            start_monotonic=time.monotonic(),
        )
        self._active_deliberations[decision_id] = record
        return record
    
    def check_deliberation(self, decision_id: str) -> Tuple[bool, float]:
        """
        Check if deliberation time has been met.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            Tuple of (is_complete, elapsed_seconds)
            
        Raises:
            KeyError: If decision_id not found
        """
        record = self._active_deliberations.get(decision_id)
        if record is None:
            raise KeyError(f"No active deliberation for decision: {decision_id}")
        
        current = time.monotonic()
        elapsed = current - record.start_monotonic
        is_complete = elapsed >= self._min_seconds
        
        return (is_complete, elapsed)
    
    def get_remaining_time(self, decision_id: str) -> float:
        """
        Get remaining deliberation time.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            Remaining seconds (0.0 if complete)
            
        Raises:
            KeyError: If decision_id not found
        """
        is_complete, elapsed = self.check_deliberation(decision_id)
        if is_complete:
            return 0.0
        return self._min_seconds - elapsed
    
    def end_deliberation(self, decision_id: str) -> DeliberationRecord:
        """
        End a deliberation period and validate timing.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            Updated DeliberationRecord with end time
            
        Raises:
            KeyError: If decision_id not found
            DeliberationTimeViolation: If minimum time not met
        """
        record = self._active_deliberations.get(decision_id)
        if record is None:
            raise KeyError(f"No active deliberation for decision: {decision_id}")
        
        current = time.monotonic()
        elapsed = current - record.start_monotonic
        
        if elapsed < self._min_seconds:
            raise DeliberationTimeViolation(
                decision_id=decision_id,
                elapsed_seconds=elapsed,
                required_seconds=self._min_seconds,
            )
        
        # Create completed record
        completed = record.with_end(current)
        
        # Remove from active deliberations
        del self._active_deliberations[decision_id]
        
        return completed
    
    def cancel_deliberation(self, decision_id: str) -> None:
        """
        Cancel an active deliberation without completing it.
        
        Args:
            decision_id: Unique identifier for the decision
        """
        self._active_deliberations.pop(decision_id, None)
    
    def has_active_deliberation(self, decision_id: str) -> bool:
        """
        Check if a deliberation is active.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            True if deliberation is active
        """
        return decision_id in self._active_deliberations
