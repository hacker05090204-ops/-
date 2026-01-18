"""
Tests for Phase-10 cooldown enforcer.

Validates:
- Minimum cooldown time is enforced
- Monotonic clock is used
- No auto-approval exists
"""

import pytest
import time

from governance_friction.cooldown import CooldownEnforcer
from governance_friction.types import MIN_COOLDOWN_SECONDS, CooldownState
from governance_friction.errors import CooldownViolation


class TestCooldownEnforcer:
    """Test cooldown enforcer functionality."""
    
    def test_start_cooldown(self, decision_id):
        """start_cooldown should create a state with start time."""
        enforcer = CooldownEnforcer()
        state = enforcer.start_cooldown(decision_id)
        
        assert state.decision_id == decision_id
        assert state.start_monotonic > 0
        assert state.is_complete is False
    
    def test_check_cooldown_returns_remaining(self, decision_id):
        """check_cooldown should return remaining time."""
        enforcer = CooldownEnforcer()
        enforcer.start_cooldown(decision_id)
        
        is_complete, remaining = enforcer.check_cooldown(decision_id)
        
        assert is_complete is False
        assert remaining > 0
        assert remaining <= MIN_COOLDOWN_SECONDS
    
    def test_get_remaining_time(self, decision_id):
        """get_remaining_time should return remaining seconds."""
        enforcer = CooldownEnforcer()
        enforcer.start_cooldown(decision_id)
        
        remaining = enforcer.get_remaining_time(decision_id)
        
        assert remaining > 0
        assert remaining <= MIN_COOLDOWN_SECONDS
    
    def test_end_cooldown_too_early_raises(self, decision_id):
        """end_cooldown should raise if cooldown not complete."""
        enforcer = CooldownEnforcer()
        enforcer.start_cooldown(decision_id)
        
        # Immediately try to end - should fail
        with pytest.raises(CooldownViolation) as exc_info:
            enforcer.end_cooldown(decision_id)
        
        assert exc_info.value.decision_id == decision_id
        assert exc_info.value.remaining_seconds > 0
    
    def test_end_cooldown_after_min_time_succeeds(self, decision_id):
        """end_cooldown should succeed after minimum time."""
        # Note: min_seconds is enforced to MIN_COOLDOWN_SECONDS (3.0)
        # For testing, we mock the start time instead
        enforcer = CooldownEnforcer()
        state = enforcer.start_cooldown(decision_id)
        
        # Manually adjust the internal state to simulate time passing
        # by replacing the cooldown with one that started earlier
        import time as time_module
        old_start = state.start_monotonic
        fake_start = time_module.monotonic() - MIN_COOLDOWN_SECONDS - 0.1
        
        enforcer._active_cooldowns[decision_id] = CooldownState(
            decision_id=decision_id,
            start_monotonic=fake_start,
            duration_seconds=MIN_COOLDOWN_SECONDS,
        )
        
        completed = enforcer.end_cooldown(decision_id)
        
        assert completed.is_complete is True
        assert completed.end_monotonic is not None
    
    def test_minimum_cannot_be_reduced_below_hard_minimum(self):
        """Minimum time cannot be set below MIN_COOLDOWN_SECONDS."""
        enforcer = CooldownEnforcer(min_seconds=0.5)  # Try to set to 0.5 seconds
        
        # Should be enforced to MIN_COOLDOWN_SECONDS
        assert enforcer.min_cooldown_seconds >= MIN_COOLDOWN_SECONDS
    
    def test_uses_monotonic_clock(self, decision_id):
        """Enforcer should use monotonic clock, not wall clock."""
        enforcer = CooldownEnforcer()
        state = enforcer.start_cooldown(decision_id)
        
        # Monotonic time should be positive and reasonable
        assert state.start_monotonic > 0
        
        # Should be close to current monotonic time
        current = time.monotonic()
        assert abs(current - state.start_monotonic) < 1.0
    
    def test_cancel_cooldown(self, decision_id):
        """cancel_cooldown should remove active cooldown."""
        enforcer = CooldownEnforcer()
        enforcer.start_cooldown(decision_id)
        
        assert enforcer.has_active_cooldown(decision_id) is True
        
        enforcer.cancel_cooldown(decision_id)
        
        assert enforcer.has_active_cooldown(decision_id) is False
    
    def test_enforce_cooldown_raises_if_active(self, decision_id):
        """enforce_cooldown should raise if cooldown not complete."""
        enforcer = CooldownEnforcer()
        enforcer.start_cooldown(decision_id)
        
        with pytest.raises(CooldownViolation):
            enforcer.enforce_cooldown(decision_id)
    
    def test_no_cooldown_means_complete(self, decision_id):
        """No active cooldown should be treated as complete."""
        enforcer = CooldownEnforcer()
        
        # No cooldown started
        is_complete, remaining = enforcer.check_cooldown(decision_id)
        
        assert is_complete is True
        assert remaining == 0.0


class TestCooldownEnforcerNoAutoApprove:
    """Test that no auto-approval exists."""
    
    def test_no_auto_approve_method(self):
        """CooldownEnforcer should not have auto_approve method."""
        enforcer = CooldownEnforcer()
        
        assert not hasattr(enforcer, "auto_approve")
        assert not hasattr(enforcer, "auto_approve_on_expiry")
        assert not hasattr(enforcer, "bypass_cooldown")
        assert not hasattr(enforcer, "skip_cooldown")
    
    def test_no_expiry_auto_approval(self, decision_id):
        """Enforcer should not auto-approve after expiry."""
        enforcer = CooldownEnforcer()
        enforcer.start_cooldown(decision_id)
        
        # Simulate time passing by adjusting the start time
        import time as time_module
        fake_start = time_module.monotonic() - MIN_COOLDOWN_SECONDS - 0.5
        
        enforcer._active_cooldowns[decision_id] = CooldownState(
            decision_id=decision_id,
            start_monotonic=fake_start,
            duration_seconds=MIN_COOLDOWN_SECONDS,
        )
        
        # check_cooldown should show complete
        is_complete, _ = enforcer.check_cooldown(decision_id)
        assert is_complete is True
        
        # But the cooldown is still "tracked" until explicitly ended
        # has_active_cooldown returns False when time has expired
        assert enforcer.has_active_cooldown(decision_id) is False


class TestCooldownTimingEdgeCases:
    """Test timing edge cases."""
    
    def test_exactly_at_boundary(self, decision_id):
        """Test behavior at exact boundary."""
        enforcer = CooldownEnforcer()
        enforcer.start_cooldown(decision_id)
        
        # Simulate exactly minimum time passing
        import time as time_module
        fake_start = time_module.monotonic() - MIN_COOLDOWN_SECONDS
        
        enforcer._active_cooldowns[decision_id] = CooldownState(
            decision_id=decision_id,
            start_monotonic=fake_start,
            duration_seconds=MIN_COOLDOWN_SECONDS,
        )
        
        # Should be complete
        is_complete, remaining = enforcer.check_cooldown(decision_id)
        assert is_complete is True
        assert remaining == 0.0
    
    def test_just_before_boundary(self, decision_id):
        """Test behavior just before boundary."""
        enforcer = CooldownEnforcer()
        enforcer.start_cooldown(decision_id)
        
        # Simulate less than minimum time passing
        import time as time_module
        fake_start = time_module.monotonic() - (MIN_COOLDOWN_SECONDS - 1.0)
        
        enforcer._active_cooldowns[decision_id] = CooldownState(
            decision_id=decision_id,
            start_monotonic=fake_start,
            duration_seconds=MIN_COOLDOWN_SECONDS,
        )
        
        # Should not be complete
        is_complete, remaining = enforcer.check_cooldown(decision_id)
        assert is_complete is False
        assert remaining > 0
