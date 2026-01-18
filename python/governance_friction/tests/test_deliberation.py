"""
Tests for Phase-10 deliberation timer.

Validates:
- Minimum deliberation time is enforced
- Monotonic clock is used
- No auto-approval exists
"""

import pytest
import time

from governance_friction.deliberation import DeliberationTimer
from governance_friction.types import MIN_DELIBERATION_SECONDS, DeliberationRecord
from governance_friction.errors import DeliberationTimeViolation


class TestDeliberationTimer:
    """Test deliberation timer functionality."""
    
    def test_start_deliberation(self, decision_id):
        """start_deliberation should create a record with start time."""
        timer = DeliberationTimer()
        record = timer.start_deliberation(decision_id)
        
        assert record.decision_id == decision_id
        assert record.start_monotonic > 0
        assert record.end_monotonic is None
        assert record.is_complete is False
    
    def test_check_deliberation_returns_elapsed(self, decision_id):
        """check_deliberation should return elapsed time."""
        timer = DeliberationTimer()
        timer.start_deliberation(decision_id)
        
        # Small delay
        time.sleep(0.1)
        
        is_complete, elapsed = timer.check_deliberation(decision_id)
        
        assert elapsed >= 0.1
        assert is_complete is False  # Not enough time
    
    def test_get_remaining_time(self, decision_id):
        """get_remaining_time should return remaining seconds."""
        timer = DeliberationTimer()
        timer.start_deliberation(decision_id)
        
        remaining = timer.get_remaining_time(decision_id)
        
        assert remaining > 0
        assert remaining <= MIN_DELIBERATION_SECONDS
    
    def test_end_deliberation_too_early_raises(self, decision_id):
        """end_deliberation should raise if minimum time not met."""
        timer = DeliberationTimer()
        timer.start_deliberation(decision_id)
        
        # Immediately try to end - should fail
        with pytest.raises(DeliberationTimeViolation) as exc_info:
            timer.end_deliberation(decision_id)
        
        assert exc_info.value.decision_id == decision_id
        assert exc_info.value.elapsed_seconds < MIN_DELIBERATION_SECONDS
        assert exc_info.value.required_seconds == MIN_DELIBERATION_SECONDS
    
    def test_end_deliberation_after_min_time_succeeds(self, decision_id):
        """end_deliberation should succeed after minimum time."""
        timer = DeliberationTimer()
        timer.start_deliberation(decision_id)
        
        # Simulate time passing by adjusting the start time
        import time as time_module
        fake_start = time_module.monotonic() - MIN_DELIBERATION_SECONDS - 0.1
        
        timer._active_deliberations[decision_id] = DeliberationRecord(
            decision_id=decision_id,
            start_monotonic=fake_start,
        )
        
        record = timer.end_deliberation(decision_id)
        
        assert record.is_complete is True
        assert record.elapsed_seconds >= MIN_DELIBERATION_SECONDS
        assert record.end_monotonic is not None
    
    def test_minimum_cannot_be_reduced_below_hard_minimum(self):
        """Minimum time cannot be set below MIN_DELIBERATION_SECONDS."""
        timer = DeliberationTimer(min_seconds=1.0)  # Try to set to 1 second
        
        # Should be enforced to MIN_DELIBERATION_SECONDS
        assert timer.min_deliberation_seconds >= MIN_DELIBERATION_SECONDS
    
    def test_uses_monotonic_clock(self, decision_id):
        """Timer should use monotonic clock, not wall clock."""
        timer = DeliberationTimer()
        record = timer.start_deliberation(decision_id)
        
        # Monotonic time should be positive and reasonable
        assert record.start_monotonic > 0
        
        # Should be close to current monotonic time
        current = time.monotonic()
        assert abs(current - record.start_monotonic) < 1.0
    
    def test_cancel_deliberation(self, decision_id):
        """cancel_deliberation should remove active deliberation."""
        timer = DeliberationTimer()
        timer.start_deliberation(decision_id)
        
        assert timer.has_active_deliberation(decision_id) is True
        
        timer.cancel_deliberation(decision_id)
        
        assert timer.has_active_deliberation(decision_id) is False
    
    def test_unknown_decision_raises_keyerror(self):
        """Operations on unknown decision should raise KeyError."""
        timer = DeliberationTimer()
        
        with pytest.raises(KeyError):
            timer.check_deliberation("unknown")
        
        with pytest.raises(KeyError):
            timer.end_deliberation("unknown")


class TestDeliberationTimerNoAutoApprove:
    """Test that no auto-approval exists."""
    
    def test_no_auto_approve_method(self):
        """DeliberationTimer should not have auto_approve method."""
        timer = DeliberationTimer()
        
        assert not hasattr(timer, "auto_approve")
        assert not hasattr(timer, "auto_approve_on_timeout")
        assert not hasattr(timer, "bypass_deliberation")
        assert not hasattr(timer, "skip_deliberation")
    
    def test_no_timeout_auto_approval(self, decision_id):
        """Timer should not auto-approve after timeout."""
        timer = DeliberationTimer(min_seconds=0.1)
        timer.start_deliberation(decision_id)
        
        # Wait longer than minimum
        time.sleep(0.2)
        
        # Should still require explicit end_deliberation call
        # The record should not be auto-completed
        is_complete, _ = timer.check_deliberation(decision_id)
        
        # check_deliberation returns True for is_complete when time has passed,
        # but the deliberation is still active until end_deliberation is called
        assert timer.has_active_deliberation(decision_id) is True
