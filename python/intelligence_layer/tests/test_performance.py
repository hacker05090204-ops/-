"""
Tests for Phase-8 Performance Analyzer

Verifies that:
- Performance metrics are personal only
- No comparisons between reviewers
- No rankings
- No performance targets
"""

import pytest
from datetime import datetime

from intelligence_layer.performance import PerformanceAnalyzer
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.types import PerformanceMetrics
from intelligence_layer.tests.conftest import create_sample_decision, create_sample_session


class TestPerformanceAnalyzerBasic:
    """Basic tests for performance analyzer."""
    
    def test_get_performance_metrics_returns_metrics(self, performance_analyzer):
        """Verify get_performance_metrics returns PerformanceMetrics."""
        metrics = performance_analyzer.get_performance_metrics("reviewer-001")
        
        assert isinstance(metrics, PerformanceMetrics)
    
    def test_metrics_has_correct_reviewer_id(self, performance_analyzer):
        """Verify metrics has correct reviewer_id."""
        metrics = performance_analyzer.get_performance_metrics("reviewer-001")
        
        assert metrics.reviewer_id == "reviewer-001"
    
    def test_human_interpretation_required_always_true(self, performance_analyzer):
        """Verify human_interpretation_required is always True."""
        metrics = performance_analyzer.get_performance_metrics("reviewer-001")
        
        assert metrics.human_interpretation_required is True


class TestPerformanceAnalyzerStatistics:
    """Tests for performance statistics."""
    
    def test_total_decisions_count(self):
        """Verify total decisions count is correct."""
        decisions = [
            create_sample_decision(decision_id=f"dec-{i}", reviewer_id="reviewer-001")
            for i in range(5)
        ]
        data_access = DataAccessLayer(decisions=decisions)
        analyzer = PerformanceAnalyzer(data_access)
        
        metrics = analyzer.get_performance_metrics("reviewer-001")
        
        assert metrics.total_decisions == 5
    
    def test_decisions_by_type(self):
        """Verify decisions are grouped by type."""
        decisions = [
            create_sample_decision(decision_id="dec-001", reviewer_id="reviewer-001", decision_type="approve"),
            create_sample_decision(decision_id="dec-002", reviewer_id="reviewer-001", decision_type="approve"),
            create_sample_decision(decision_id="dec-003", reviewer_id="reviewer-001", decision_type="reject"),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        analyzer = PerformanceAnalyzer(data_access)
        
        metrics = analyzer.get_performance_metrics("reviewer-001")
        
        assert metrics.decisions_by_type.get("approve", 0) == 2
        assert metrics.decisions_by_type.get("reject", 0) == 1
    
    def test_severity_distribution(self):
        """Verify severity distribution is correct."""
        decisions = [
            create_sample_decision(decision_id="dec-001", reviewer_id="reviewer-001", severity="high"),
            create_sample_decision(decision_id="dec-002", reviewer_id="reviewer-001", severity="high"),
            create_sample_decision(decision_id="dec-003", reviewer_id="reviewer-001", severity="medium"),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        analyzer = PerformanceAnalyzer(data_access)
        
        metrics = analyzer.get_performance_metrics("reviewer-001")
        
        assert metrics.severity_distribution.get("high", 0) == 2
        assert metrics.severity_distribution.get("medium", 0) == 1


class TestPerformanceAnalyzerPersonalOnly:
    """Tests to verify metrics are personal only."""
    
    def test_metrics_for_specific_reviewer_only(self):
        """Verify metrics are for specific reviewer only."""
        decisions = [
            create_sample_decision(decision_id="dec-001", reviewer_id="reviewer-001"),
            create_sample_decision(decision_id="dec-002", reviewer_id="reviewer-002"),
            create_sample_decision(decision_id="dec-003", reviewer_id="reviewer-001"),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        analyzer = PerformanceAnalyzer(data_access)
        
        metrics = analyzer.get_performance_metrics("reviewer-001")
        
        # Should only count reviewer-001's decisions
        assert metrics.total_decisions == 2
        assert metrics.reviewer_id == "reviewer-001"


class TestPerformanceAnalyzerEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_history_returns_zero_metrics(self, empty_data_access):
        """Verify empty history returns metrics with zero counts."""
        analyzer = PerformanceAnalyzer(empty_data_access)
        
        metrics = analyzer.get_performance_metrics("nonexistent")
        
        assert metrics.total_decisions == 0
        assert metrics.decisions_by_type == {}
        assert metrics.severity_distribution == {}
    
    def test_no_sessions_zero_review_time(self):
        """Verify no sessions results in zero average review time."""
        decisions = [create_sample_decision(reviewer_id="reviewer-001")]
        data_access = DataAccessLayer(decisions=decisions, review_sessions=[])
        analyzer = PerformanceAnalyzer(data_access)
        
        metrics = analyzer.get_performance_metrics("reviewer-001")
        
        assert metrics.average_review_time_seconds == 0.0


class TestPerformanceAnalyzerNoForbiddenMethods:
    """Tests to verify no forbidden methods exist."""
    
    def test_no_compare_reviewers_method(self, performance_analyzer):
        """Verify compare_reviewers method does not exist."""
        assert not hasattr(performance_analyzer, "compare_reviewers")
    
    def test_no_rank_reviewers_method(self, performance_analyzer):
        """Verify rank_reviewers method does not exist."""
        assert not hasattr(performance_analyzer, "rank_reviewers")
    
    def test_no_set_performance_target_method(self, performance_analyzer):
        """Verify set_performance_target method does not exist."""
        assert not hasattr(performance_analyzer, "set_performance_target")
    
    def test_no_team_average_method(self, performance_analyzer):
        """Verify team_average method does not exist."""
        assert not hasattr(performance_analyzer, "team_average")
    
    def test_no_percentile_method(self, performance_analyzer):
        """Verify percentile method does not exist."""
        assert not hasattr(performance_analyzer, "percentile")
    
    def test_no_reviewer_ranking_method(self, performance_analyzer):
        """Verify reviewer_ranking method does not exist."""
        assert not hasattr(performance_analyzer, "reviewer_ranking")
    
    def test_no_get_all_reviewers_metrics_method(self, performance_analyzer):
        """Verify get_all_reviewers_metrics method does not exist."""
        assert not hasattr(performance_analyzer, "get_all_reviewers_metrics")
    
    def test_no_leaderboard_method(self, performance_analyzer):
        """Verify leaderboard method does not exist."""
        assert not hasattr(performance_analyzer, "leaderboard")


class TestPerformanceMetricsNoForbiddenFields:
    """Tests to verify PerformanceMetrics has no forbidden fields."""
    
    def test_no_rank_field(self, performance_analyzer):
        """Verify PerformanceMetrics has no rank field."""
        metrics = performance_analyzer.get_performance_metrics("reviewer-001")
        
        assert not hasattr(metrics, "rank")
    
    def test_no_percentile_field(self, performance_analyzer):
        """Verify PerformanceMetrics has no percentile field."""
        metrics = performance_analyzer.get_performance_metrics("reviewer-001")
        
        assert not hasattr(metrics, "percentile")
    
    def test_no_comparison_field(self, performance_analyzer):
        """Verify PerformanceMetrics has no comparison field."""
        metrics = performance_analyzer.get_performance_metrics("reviewer-001")
        
        assert not hasattr(metrics, "comparison")
    
    def test_no_team_average_field(self, performance_analyzer):
        """Verify PerformanceMetrics has no team_average field."""
        metrics = performance_analyzer.get_performance_metrics("reviewer-001")
        
        assert not hasattr(metrics, "team_average")
    
    def test_no_performance_target_field(self, performance_analyzer):
        """Verify PerformanceMetrics has no performance_target field."""
        metrics = performance_analyzer.get_performance_metrics("reviewer-001")
        
        assert not hasattr(metrics, "performance_target")
    
    def test_no_other_reviewers_field(self, performance_analyzer):
        """Verify PerformanceMetrics has no other_reviewers field."""
        metrics = performance_analyzer.get_performance_metrics("reviewer-001")
        
        assert not hasattr(metrics, "other_reviewers")
