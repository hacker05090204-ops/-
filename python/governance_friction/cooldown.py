"""
Phase-10: Governance & Friction Layer - Cooldown Enforcer

Prevents rapid sequential confirmations.
Uses monotonic clock for reliable timing.
"""

import time
from typing import Dict, Tuple, Optional

from governance_friction.types import (
    CooldownState,
    MIN_COOLDOWN_SECONDS,
)
from governance_friction.errors import CooldownViolation


class CooldownEnforcer:
    """
    Enforces cooldown periods between confirmations.
    
    SECURITY: This enforcer ensures humans cannot rapidly confirm
    multiple items. It NEVER:
    - Auto-approves after cooldown
    - Reduces cooldown time
    - Bypasses the requirement
    
    All timing uses monotonic clock (time.monotonic()) for reliability.
    """
    
    def __init__(self, min_seconds: float = MIN_COOLDOWN_SECONDS):
        """
        Initialize the cooldown enforcer.
        
        Args:
            min_seconds: Minimum cooldown time. Cannot be less than MIN_COOLDOWN_SECONDS.
        """
        # Enforce HARD minimum
        self._min_seconds = max(min_seconds, MIN_COOLDOWN_SECONDS)
        self._active_cooldowns: Dict[str, CooldownState] = {}
    
    @property
    def min_cooldown_seconds(self) -> float:
        """Get the minimum cooldown time (always >= MIN_COOLDOWN_SECONDS)."""
        return self._min_seconds
    
    def start_cooldown(self, decision_id: str) -> CooldownState:
        """
        Start a cooldown period after a confirmation.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            CooldownState with start time recorded
        """
        state = CooldownState(
            decision_id=decision_id,
            start_monotonic=time.monotonic(),
            duration_seconds=self._min_seconds,
        )
        self._active_cooldowns[decision_id] = state
        return state
    
    def check_cooldown(self, decision_id: str) -> Tuple[bool, float]:
        """
        Check if cooldown has expired.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            Tuple of (is_complete, remaining_seconds)
            
        Raises:
            KeyError: If decision_id not found
        """
        state = self._active_cooldowns.get(decision_id)
        if state is None:
            # No cooldown active = cooldown complete
            return (True, 0.0)
        
        current = time.monotonic()
        elapsed = current - state.start_monotonic
        remaining = self._min_seconds - elapsed
        
        if remaining <= 0:
            return (True, 0.0)
        
        return (False, remaining)
    
    def get_remaining_time(self, decision_id: str) -> float:
        """
        Get remaining cooldown time.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            Remaining seconds (0.0 if complete or not found)
        """
        is_complete, remaining = self.check_cooldown(decision_id)
        return remaining
    
    def end_cooldown(self, decision_id: str) -> CooldownState:
        """
        End a cooldown period and validate timing.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            Updated CooldownState with end time
            
        Raises:
            KeyError: If decision_id not found
            CooldownViolation: If cooldown not complete
        """
        state = self._active_cooldowns.get(decision_id)
        if state is None:
            raise KeyError(f"No active cooldown for decision: {decision_id}")
        
        current = time.monotonic()
        elapsed = current - state.start_monotonic
        
        if elapsed < self._min_seconds:
            remaining = self._min_seconds - elapsed
            raise CooldownViolation(
                decision_id=decision_id,
                remaining_seconds=remaining,
            )
        
        # Create completed state
        completed = state.with_end(current)
        
        # Remove from active cooldowns
        del self._active_cooldowns[decision_id]
        
        return completed
    
    def cancel_cooldown(self, decision_id: str) -> None:
        """
        Cancel an active cooldown without completing it.
        
        Args:
            decision_id: Unique identifier for the decision
        """
        self._active_cooldowns.pop(decision_id, None)
    
    def has_active_cooldown(self, decision_id: str) -> bool:
        """
        Check if a cooldown is active.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Returns:
            True if cooldown is active and not expired
        """
        if decision_id not in self._active_cooldowns:
            return False
        
        is_complete, _ = self.check_cooldown(decision_id)
        return not is_complete
    
    def enforce_cooldown(self, decision_id: str) -> None:
        """
        Enforce that cooldown has expired before proceeding.
        
        Args:
            decision_id: Unique identifier for the decision
            
        Raises:
            CooldownViolation: If cooldown not complete
        """
        is_complete, remaining = self.check_cooldown(decision_id)
        
        if not is_complete:
            raise CooldownViolation(
                decision_id=decision_id,
                remaining_seconds=remaining,
            )
