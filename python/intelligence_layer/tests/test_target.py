"""
Tests for Phase-8 Target Profiler

Verifies that:
- Target profiles are historical only
- No predictions
- No recommendations
"""

import pytest
from datetime import datetime

from intelligence_layer.target import TargetProfiler
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.types import TargetProfile, TimelineEntry
from intelligence_layer.tests.conftest import create_sample_decision, create_sample_submission


class TestTargetProfilerBasic:
    """Basic tests for target profiler."""
    
    def test_get_target_profile_returns_profile(self, target_profiler):
        """Verify get_target_profile returns a TargetProfile."""
        profile = target_profiler.get_target_profile("target-001")
        
        assert isinstance(profile, TargetProfile)
    
    def test_profile_has_correct_target_id(self, target_profiler):
        """Verify profile has correct target_id."""
        profile = target_profiler.get_target_profile("target-001")
        
        assert profile.target_id == "target-001"
    
    def test_human_interpretation_required_always_true(self, target_profiler):
        """Verify human_interpretation_required is always True."""
        profile = target_profiler.get_target_profile("target-001")
        
        assert profile.human_interpretation_required is True


class TestTargetProfilerStatistics:
    """Tests for target profile statistics."""
    
    def test_total_findings_count(self):
        """Verify total findings count is correct."""
        decisions = [
            create_sample_decision(decision_id=f"dec-{i}", target_id="target-001")
            for i in range(5)
        ]
        data_access = DataAccessLayer(decisions=decisions)
        profiler = TargetProfiler(data_access)
        
        profile = profiler.get_target_profile("target-001")
        
        assert profile.total_findings == 5
    
    def test_findings_by_decision_type(self):
        """Verify findings are grouped by decision type."""
        decisions = [
            create_sample_decision(decision_id="dec-001", target_id="target-001", decision_type="approve"),
            create_sample_decision(decision_id="dec-002", target_id="target-001", decision_type="approve"),
            create_sample_decision(decision_id="dec-003", target_id="target-001", decision_type="reject"),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        profiler = TargetProfiler(data_access)
        
        profile = profiler.get_target_profile("target-001")
        
        assert profile.findings_by_decision.get("approve", 0) == 2
        assert profile.findings_by_decision.get("reject", 0) == 1
    
    def test_findings_by_severity(self):
        """Verify findings are grouped by severity."""
        decisions = [
            create_sample_decision(decision_id="dec-001", target_id="target-001", severity="high"),
            create_sample_decision(decision_id="dec-002", target_id="target-001", severity="high"),
            create_sample_decision(decision_id="dec-003", target_id="target-001", severity="medium"),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        profiler = TargetProfiler(data_access)
        
        profile = profiler.get_target_profile("target-001")
        
        assert profile.findings_by_severity.get("high", 0) == 2
        assert profile.findings_by_severity.get("medium", 0) == 1


class TestTargetProfilerTimeline:
    """Tests for target timeline."""
    
    def test_get_target_timeline_returns_list(self, target_profiler):
        """Verify get_target_timeline returns a list."""
        timeline = target_profiler.get_target_timeline("target-001")
        
        assert isinstance(timeline, list)
    
    def test_timeline_entries_are_correct_type(self, target_profiler):
        """Verify timeline entries are TimelineEntry type."""
        timeline = target_profiler.get_target_timeline("target-001")
        
        for entry in timeline:
            assert isinstance(entry, TimelineEntry)
    
    def test_timeline_granularity_month(self):
        """Verify timeline respects month granularity."""
        decisions = [
            create_sample_decision(
                decision_id="dec-001",
                target_id="target-001",
                timestamp=datetime(2025, 1, 15),
            ),
            create_sample_decision(
                decision_id="dec-002",
                target_id="target-001",
                timestamp=datetime(2025, 2, 15),
            ),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        profiler = TargetProfiler(data_access)
        
        timeline = profiler.get_target_timeline("target-001", granularity="month")
        
        assert len(timeline) == 2
        assert timeline[0].period == "2025-01"
        assert timeline[1].period == "2025-02"


class TestTargetProfilerEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_history_returns_empty_profile(self, empty_data_access):
        """Verify empty history returns profile with zero counts."""
        profiler = TargetProfiler(empty_data_access)
        
        profile = profiler.get_target_profile("nonexistent")
        
        assert profile.total_findings == 0
        assert profile.findings_by_decision == {}
        assert profile.findings_by_severity == {}
    
    def test_empty_timeline_for_nonexistent_target(self, empty_data_access):
        """Verify empty timeline for nonexistent target."""
        profiler = TargetProfiler(empty_data_access)
        
        timeline = profiler.get_target_timeline("nonexistent")
        
        assert timeline == []


class TestTargetProfilerNoForbiddenMethods:
    """Tests to verify no forbidden methods exist."""
    
    def test_no_predict_vulnerabilities_method(self, target_profiler):
        """Verify predict_vulnerabilities method does not exist."""
        assert not hasattr(target_profiler, "predict_vulnerabilities")
    
    def test_no_recommend_tests_method(self, target_profiler):
        """Verify recommend_tests method does not exist."""
        assert not hasattr(target_profiler, "recommend_tests")
    
    def test_no_risk_score_method(self, target_profiler):
        """Verify risk_score method does not exist."""
        assert not hasattr(target_profiler, "risk_score")
    
    def test_no_vulnerability_forecast_method(self, target_profiler):
        """Verify vulnerability_forecast method does not exist."""
        assert not hasattr(target_profiler, "vulnerability_forecast")
    
    def test_no_suggest_focus_method(self, target_profiler):
        """Verify suggest_focus method does not exist."""
        assert not hasattr(target_profiler, "suggest_focus")


class TestTargetProfileNoForbiddenFields:
    """Tests to verify TargetProfile has no forbidden fields."""
    
    def test_no_predicted_vulnerabilities_field(self, target_profiler):
        """Verify TargetProfile has no predicted_vulnerabilities field."""
        profile = target_profiler.get_target_profile("target-001")
        
        assert not hasattr(profile, "predicted_vulnerabilities")
    
    def test_no_future_risk_field(self, target_profiler):
        """Verify TargetProfile has no future_risk field."""
        profile = target_profiler.get_target_profile("target-001")
        
        assert not hasattr(profile, "future_risk")
    
    def test_no_recommended_tests_field(self, target_profiler):
        """Verify TargetProfile has no recommended_tests field."""
        profile = target_profiler.get_target_profile("target-001")
        
        assert not hasattr(profile, "recommended_tests")
    
    def test_no_suggested_focus_field(self, target_profiler):
        """Verify TargetProfile has no suggested_focus field."""
        profile = target_profiler.get_target_profile("target-001")
        
        assert not hasattr(profile, "suggested_focus")
