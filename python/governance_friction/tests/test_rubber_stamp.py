"""
Tests for Phase-10 rubber-stamp detector.

Validates:
- Pattern detection works
- Warnings are ADVISORY ONLY (never block)
- Cold-start safety (no warnings for new reviewers)
"""

import pytest
import time

from governance_friction.rubber_stamp import RubberStampDetector
from governance_friction.types import (
    WarningLevel,
    MIN_DECISIONS_FOR_ANALYSIS,
)


class TestRubberStampDetector:
    """Test rubber-stamp detection functionality."""
    
    def test_record_confirmation(self, reviewer_id, decision_id):
        """record_confirmation should store confirmation data."""
        detector = RubberStampDetector()
        
        detector.record_confirmation(reviewer_id, decision_id, 10.0)
        
        stats = detector.get_reviewer_statistics(reviewer_id)
        assert stats["decision_count"] == 1
    
    def test_cold_start_no_warnings(self, reviewer_id):
        """New reviewers should get NO warnings (cold-start safety)."""
        detector = RubberStampDetector()
        
        # Record fewer than MIN_DECISIONS_FOR_ANALYSIS
        for i in range(MIN_DECISIONS_FOR_ANALYSIS - 1):
            detector.record_confirmation(reviewer_id, f"decision-{i}", 5.0)
        
        warning = detector.analyze_pattern(reviewer_id)
        
        assert warning.is_cold_start is True
        assert warning.warning_level == WarningLevel.NONE
        assert warning.is_advisory_silent is True
    
    def test_normal_pattern_no_warning(self, reviewer_id):
        """Normal confirmation patterns should not trigger warnings."""
        detector = RubberStampDetector()
        
        # Record enough decisions with normal timing and spacing
        import time as time_module
        base_time = time_module.monotonic()
        
        for i in range(MIN_DECISIONS_FOR_ANALYSIS + 5):
            # Simulate confirmations spread out over time (not rapid succession)
            # by manually setting timestamps in the history
            detector._reviewer_history[reviewer_id].append(
                (base_time + i * 15.0, 10.0)  # 15 seconds apart, 10 second deliberation
            )
        
        warning = detector.analyze_pattern(reviewer_id)
        
        assert warning.is_cold_start is False
        assert warning.warning_level == WarningLevel.NONE
    
    def test_rapid_succession_warning(self, reviewer_id):
        """Rapid succession should trigger warning."""
        detector = RubberStampDetector()
        
        # Record enough decisions first
        for i in range(MIN_DECISIONS_FOR_ANALYSIS + 5):
            detector.record_confirmation(reviewer_id, f"decision-{i}", 5.0)
        
        # Now record rapid succession (3+ in < 10 seconds)
        # The detector checks timestamps, so we need to record quickly
        for i in range(3):
            detector.record_confirmation(reviewer_id, f"rapid-{i}", 5.0)
        
        warning = detector.analyze_pattern(reviewer_id)
        
        # Should have some warning level (MEDIUM or HIGH)
        assert warning.warning_level in [WarningLevel.LOW, WarningLevel.MEDIUM, WarningLevel.HIGH]
    
    def test_warning_is_advisory_only(self, reviewer_id):
        """Warnings should be advisory only - never block."""
        detector = RubberStampDetector()
        
        # Create conditions for warning
        for i in range(MIN_DECISIONS_FOR_ANALYSIS + 5):
            detector.record_confirmation(reviewer_id, f"decision-{i}", 5.0)
        
        warning = detector.analyze_pattern(reviewer_id)
        
        # Even with warning, should not block
        # The warning object has no blocking capability
        assert not hasattr(warning, "blocks_confirmation") or warning.warning_level != WarningLevel.NONE
        
        # Verify no blocking methods exist
        assert not hasattr(detector, "block_confirmation")
        assert not hasattr(detector, "reject_confirmation")
    
    def test_get_reviewer_statistics(self, reviewer_id):
        """get_reviewer_statistics should return correct stats."""
        detector = RubberStampDetector()
        
        detector.record_confirmation(reviewer_id, "d1", 5.0)
        detector.record_confirmation(reviewer_id, "d2", 10.0)
        detector.record_confirmation(reviewer_id, "d3", 15.0)
        
        stats = detector.get_reviewer_statistics(reviewer_id)
        
        assert stats["decision_count"] == 3
        assert stats["average_deliberation"] == 10.0
        assert stats["min_deliberation"] == 5.0
        assert stats["max_deliberation"] == 15.0
    
    def test_clear_history(self, reviewer_id):
        """clear_history should remove reviewer data."""
        detector = RubberStampDetector()
        
        detector.record_confirmation(reviewer_id, "d1", 5.0)
        detector.clear_history(reviewer_id)
        
        stats = detector.get_reviewer_statistics(reviewer_id)
        assert stats["decision_count"] == 0


class TestRubberStampDetectorNoBlocking:
    """Test that rubber-stamp detector never blocks."""
    
    def test_no_block_method(self):
        """RubberStampDetector should not have blocking methods."""
        detector = RubberStampDetector()
        
        assert not hasattr(detector, "block_confirmation")
        assert not hasattr(detector, "reject_confirmation")
        assert not hasattr(detector, "deny_confirmation")
        assert not hasattr(detector, "prevent_confirmation")
    
    def test_warning_has_no_block_capability(self, reviewer_id):
        """Warning objects should have no blocking capability."""
        detector = RubberStampDetector()
        
        # Create warning
        for i in range(MIN_DECISIONS_FOR_ANALYSIS + 5):
            detector.record_confirmation(reviewer_id, f"decision-{i}", 5.0)
        
        warning = detector.analyze_pattern(reviewer_id)
        
        # Warning should not have methods to block
        assert not hasattr(warning, "block")
        assert not hasattr(warning, "reject")
        assert not hasattr(warning, "prevent")
        
        # Warning should be purely informational
        assert hasattr(warning, "warning_level")
        assert hasattr(warning, "reason")
        assert hasattr(warning, "is_advisory_silent")


class TestColdStartSafety:
    """Test cold-start safety for new reviewers."""
    
    def test_zero_decisions_no_warning(self, reviewer_id):
        """Reviewer with zero decisions should get no warning."""
        detector = RubberStampDetector()
        
        warning = detector.analyze_pattern(reviewer_id)
        
        assert warning.is_cold_start is True
        assert warning.warning_level == WarningLevel.NONE
    
    def test_exactly_min_decisions_not_cold_start(self, reviewer_id):
        """Reviewer with exactly MIN_DECISIONS should not be cold-start."""
        detector = RubberStampDetector()
        
        for i in range(MIN_DECISIONS_FOR_ANALYSIS):
            detector.record_confirmation(reviewer_id, f"decision-{i}", 10.0)
            time.sleep(0.01)
        
        warning = detector.analyze_pattern(reviewer_id)
        
        assert warning.is_cold_start is False
    
    def test_one_below_min_is_cold_start(self, reviewer_id):
        """Reviewer with MIN_DECISIONS - 1 should be cold-start."""
        detector = RubberStampDetector()
        
        for i in range(MIN_DECISIONS_FOR_ANALYSIS - 1):
            detector.record_confirmation(reviewer_id, f"decision-{i}", 10.0)
        
        warning = detector.analyze_pattern(reviewer_id)
        
        assert warning.is_cold_start is True
