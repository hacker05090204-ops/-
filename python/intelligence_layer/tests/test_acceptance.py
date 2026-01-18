"""
Tests for Phase-8 Acceptance Tracker

Verifies that:
- Acceptance patterns are statistics only
- No recommendations are made
- No prioritization
"""

import pytest
from datetime import datetime

from intelligence_layer.acceptance import AcceptanceTracker
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.types import AcceptancePattern
from intelligence_layer.tests.conftest import create_sample_submission


class TestAcceptanceTrackerBasic:
    """Basic tests for acceptance tracker."""
    
    def test_get_acceptance_patterns_returns_list(self, acceptance_tracker):
        """Verify get_acceptance_patterns returns a list."""
        patterns = acceptance_tracker.get_acceptance_patterns()
        
        assert isinstance(patterns, list)
    
    def test_patterns_are_acceptance_pattern_type(self, acceptance_tracker):
        """Verify patterns are AcceptancePattern type."""
        patterns = acceptance_tracker.get_acceptance_patterns()
        
        for pattern in patterns:
            assert isinstance(pattern, AcceptancePattern)
    
    def test_human_interpretation_required_always_true(self, acceptance_tracker):
        """Verify human_interpretation_required is always True."""
        patterns = acceptance_tracker.get_acceptance_patterns()
        
        for pattern in patterns:
            assert pattern.human_interpretation_required is True


class TestAcceptanceTrackerStatistics:
    """Tests for acceptance statistics."""
    
    def test_acceptance_rate_calculation(self):
        """Verify acceptance rate is calculated correctly."""
        submissions = [
            create_sample_submission(submission_id="sub-001", status="acknowledged", platform="hackerone"),
            create_sample_submission(submission_id="sub-002", status="acknowledged", platform="hackerone"),
            create_sample_submission(submission_id="sub-003", status="rejected", platform="hackerone"),
            create_sample_submission(submission_id="sub-004", status="pending", platform="hackerone"),
        ]
        data_access = DataAccessLayer(submissions=submissions)
        tracker = AcceptanceTracker(data_access)
        
        patterns = tracker.get_acceptance_patterns(platform="hackerone")
        
        assert len(patterns) >= 1
        # Find the pattern for hackerone
        hackerone_pattern = next((p for p in patterns if p.platform == "hackerone"), None)
        assert hackerone_pattern is not None
        assert hackerone_pattern.total_submissions == 4
        assert hackerone_pattern.accepted_count == 2
        assert hackerone_pattern.rejected_count == 1
        assert hackerone_pattern.pending_count == 1
        assert hackerone_pattern.acceptance_rate == 0.5  # 2/4
    
    def test_platform_grouping(self):
        """Verify submissions are grouped by platform."""
        submissions = [
            create_sample_submission(submission_id="sub-001", platform="hackerone"),
            create_sample_submission(submission_id="sub-002", platform="bugcrowd"),
            create_sample_submission(submission_id="sub-003", platform="hackerone"),
        ]
        data_access = DataAccessLayer(submissions=submissions)
        tracker = AcceptanceTracker(data_access)
        
        comparison = tracker.get_platform_comparison()
        
        assert "hackerone" in comparison
        assert "bugcrowd" in comparison


class TestAcceptanceTrackerFilters:
    """Tests for acceptance tracker filters."""
    
    def test_filter_by_platform(self):
        """Verify filtering by platform."""
        submissions = [
            create_sample_submission(submission_id="sub-001", platform="hackerone"),
            create_sample_submission(submission_id="sub-002", platform="bugcrowd"),
        ]
        data_access = DataAccessLayer(submissions=submissions)
        tracker = AcceptanceTracker(data_access)
        
        patterns = tracker.get_acceptance_patterns(platform="hackerone")
        
        for pattern in patterns:
            assert pattern.platform == "hackerone"
    
    def test_filter_by_vulnerability_type(self):
        """Verify filtering by vulnerability type."""
        submissions = [
            create_sample_submission(submission_id="sub-001", vulnerability_type="xss"),
            create_sample_submission(submission_id="sub-002", vulnerability_type="sqli"),
        ]
        data_access = DataAccessLayer(submissions=submissions)
        tracker = AcceptanceTracker(data_access)
        
        patterns = tracker.get_acceptance_patterns(vulnerability_type="xss")
        
        for pattern in patterns:
            assert pattern.vulnerability_type == "xss"


class TestAcceptanceTrackerEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_submissions_returns_empty_list(self, empty_data_access):
        """Verify empty submissions returns empty list."""
        tracker = AcceptanceTracker(empty_data_access)
        
        patterns = tracker.get_acceptance_patterns()
        
        assert patterns == []
    
    def test_zero_submissions_zero_rate(self):
        """Verify zero submissions results in zero acceptance rate."""
        data_access = DataAccessLayer(submissions=[])
        tracker = AcceptanceTracker(data_access)
        
        patterns = tracker.get_acceptance_patterns()
        
        assert patterns == []


class TestAcceptanceTrackerNoForbiddenMethods:
    """Tests to verify no forbidden methods exist."""
    
    def test_no_recommend_platform_method(self, acceptance_tracker):
        """Verify recommend_platform method does not exist."""
        assert not hasattr(acceptance_tracker, "recommend_platform")
    
    def test_no_best_platform_method(self, acceptance_tracker):
        """Verify best_platform method does not exist."""
        assert not hasattr(acceptance_tracker, "best_platform")
    
    def test_no_prioritize_by_acceptance_method(self, acceptance_tracker):
        """Verify prioritize_by_acceptance method does not exist."""
        assert not hasattr(acceptance_tracker, "prioritize_by_acceptance")
    
    def test_no_should_submit_to_method(self, acceptance_tracker):
        """Verify should_submit_to method does not exist."""
        assert not hasattr(acceptance_tracker, "should_submit_to")
    
    def test_no_suggest_platform_method(self, acceptance_tracker):
        """Verify suggest_platform method does not exist."""
        assert not hasattr(acceptance_tracker, "suggest_platform")
    
    def test_no_rank_platforms_method(self, acceptance_tracker):
        """Verify rank_platforms method does not exist."""
        assert not hasattr(acceptance_tracker, "rank_platforms")


class TestAcceptancePatternNoForbiddenFields:
    """Tests to verify AcceptancePattern has no forbidden fields."""
    
    def test_no_recommended_platform_field(self, acceptance_tracker):
        """Verify AcceptancePattern has no recommended_platform field."""
        patterns = acceptance_tracker.get_acceptance_patterns()
        
        for pattern in patterns:
            assert not hasattr(pattern, "recommended_platform")
    
    def test_no_recommendation_field(self, acceptance_tracker):
        """Verify AcceptancePattern has no recommendation field."""
        patterns = acceptance_tracker.get_acceptance_patterns()
        
        for pattern in patterns:
            assert not hasattr(pattern, "recommendation")
    
    def test_no_suggested_action_field(self, acceptance_tracker):
        """Verify AcceptancePattern has no suggested_action field."""
        patterns = acceptance_tracker.get_acceptance_patterns()
        
        for pattern in patterns:
            assert not hasattr(pattern, "suggested_action")
    
    def test_no_priority_score_field(self, acceptance_tracker):
        """Verify AcceptancePattern has no priority_score field."""
        patterns = acceptance_tracker.get_acceptance_patterns()
        
        for pattern in patterns:
            assert not hasattr(pattern, "priority_score")
