"""
Tests for Phase-8 Data Types

Verifies that all data models are:
- Frozen (immutable)
- Have required fields
- Do NOT have forbidden fields
"""

import pytest
from dataclasses import FrozenInstanceError
from datetime import datetime

from intelligence_layer.types import (
    InsightType,
    DuplicateWarning,
    SimilarFinding,
    AcceptancePattern,
    TargetProfile,
    PerformanceMetrics,
    PatternInsight,
    DataPoint,
    TimelineEntry,
)


class TestInsightType:
    """Tests for InsightType enum."""
    
    def test_all_insight_types_exist(self):
        """Verify all expected insight types exist."""
        assert InsightType.DUPLICATE_WARNING.value == "duplicate_warning"
        assert InsightType.ACCEPTANCE_PATTERN.value == "acceptance_pattern"
        assert InsightType.TARGET_PROFILE.value == "target_profile"
        assert InsightType.PERFORMANCE_METRICS.value == "performance_metrics"
        assert InsightType.PATTERN_INSIGHT.value == "pattern_insight"


class TestSimilarFinding:
    """Tests for SimilarFinding dataclass."""
    
    def test_similar_finding_is_frozen(self):
        """Verify SimilarFinding is immutable."""
        finding = SimilarFinding(
            finding_id="find-001",
            decision_id="dec-001",
            similarity_score=0.85,
            decision_type="approve",
            submission_status="acknowledged",
            submitted_at=datetime.now(),
        )
        
        with pytest.raises(FrozenInstanceError):
            finding.similarity_score = 0.99
    
    def test_similar_finding_has_disclaimer(self):
        """Verify SimilarFinding has score disclaimer."""
        finding = SimilarFinding(
            finding_id="find-001",
            decision_id="dec-001",
            similarity_score=0.85,
            decision_type="approve",
            submission_status=None,
            submitted_at=None,
        )
        
        assert "advisory" in finding.score_disclaimer.lower()
        assert "certainty" in finding.score_disclaimer.lower()


class TestDuplicateWarning:
    """Tests for DuplicateWarning dataclass."""
    
    def test_duplicate_warning_is_frozen(self):
        """Verify DuplicateWarning is immutable."""
        warning = DuplicateWarning(
            finding_id="find-001",
            similar_findings=tuple(),
            highest_similarity=0.0,
            warning_message="No duplicates found",
        )
        
        with pytest.raises(FrozenInstanceError):
            warning.highest_similarity = 1.0
    
    def test_duplicate_warning_human_decision_required_always_true(self):
        """Verify human_decision_required is always True."""
        warning = DuplicateWarning(
            finding_id="find-001",
            similar_findings=tuple(),
            highest_similarity=0.0,
            warning_message="Test",
        )
        
        assert warning.human_decision_required is True
    
    def test_duplicate_warning_is_heuristic_always_true(self):
        """Verify is_heuristic is always True."""
        warning = DuplicateWarning(
            finding_id="find-001",
            similar_findings=tuple(),
            highest_similarity=0.0,
            warning_message="Test",
        )
        
        assert warning.is_heuristic is True
    
    def test_duplicate_warning_has_disclaimer(self):
        """Verify DuplicateWarning has similarity disclaimer."""
        warning = DuplicateWarning(
            finding_id="find-001",
            similar_findings=tuple(),
            highest_similarity=0.0,
            warning_message="Test",
        )
        
        assert "heuristic" in warning.similarity_disclaimer.lower()
        assert "human" in warning.similarity_disclaimer.lower()
    
    def test_duplicate_warning_no_forbidden_fields(self):
        """Verify DuplicateWarning has no forbidden fields."""
        warning = DuplicateWarning(
            finding_id="find-001",
            similar_findings=tuple(),
            highest_similarity=0.0,
            warning_message="Test",
        )
        
        # Forbidden fields that must NOT exist
        assert not hasattr(warning, "block_action")
        assert not hasattr(warning, "auto_reject")
        assert not hasattr(warning, "is_duplicate")
        assert not hasattr(warning, "confirmed_duplicate")
        assert not hasattr(warning, "recommended_action")


class TestAcceptancePattern:
    """Tests for AcceptancePattern dataclass."""
    
    def test_acceptance_pattern_is_frozen(self):
        """Verify AcceptancePattern is immutable."""
        pattern = AcceptancePattern(
            platform="hackerone",
            vulnerability_type="xss",
            severity="high",
            total_submissions=10,
            accepted_count=7,
            rejected_count=2,
            pending_count=1,
            acceptance_rate=0.7,
            average_response_days=5.0,
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
        )
        
        with pytest.raises(FrozenInstanceError):
            pattern.acceptance_rate = 0.99
    
    def test_acceptance_pattern_human_interpretation_required(self):
        """Verify human_interpretation_required is always True."""
        pattern = AcceptancePattern(
            platform="hackerone",
            vulnerability_type=None,
            severity=None,
            total_submissions=0,
            accepted_count=0,
            rejected_count=0,
            pending_count=0,
            acceptance_rate=0.0,
            average_response_days=None,
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
        )
        
        assert pattern.human_interpretation_required is True
    
    def test_acceptance_pattern_no_forbidden_fields(self):
        """Verify AcceptancePattern has no forbidden fields."""
        pattern = AcceptancePattern(
            platform="hackerone",
            vulnerability_type=None,
            severity=None,
            total_submissions=0,
            accepted_count=0,
            rejected_count=0,
            pending_count=0,
            acceptance_rate=0.0,
            average_response_days=None,
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
        )
        
        # Forbidden fields that must NOT exist
        assert not hasattr(pattern, "recommended_platform")
        assert not hasattr(pattern, "recommendation")
        assert not hasattr(pattern, "suggested_action")
        assert not hasattr(pattern, "priority_score")
        assert not hasattr(pattern, "should_submit")
        assert not hasattr(pattern, "best_platform")


class TestTargetProfile:
    """Tests for TargetProfile dataclass."""
    
    def test_target_profile_is_frozen(self):
        """Verify TargetProfile is immutable."""
        profile = TargetProfile(
            target_id="target-001",
            total_findings=10,
            findings_by_decision={},
            findings_by_severity={},
            findings_by_type={},
            submissions_by_platform={},
            submission_outcomes={},
            first_finding_date=None,
            last_finding_date=None,
            average_findings_per_month=0.0,
        )
        
        with pytest.raises(FrozenInstanceError):
            profile.total_findings = 100
    
    def test_target_profile_no_forbidden_fields(self):
        """Verify TargetProfile has no forbidden fields."""
        profile = TargetProfile(
            target_id="target-001",
            total_findings=0,
            findings_by_decision={},
            findings_by_severity={},
            findings_by_type={},
            submissions_by_platform={},
            submission_outcomes={},
            first_finding_date=None,
            last_finding_date=None,
            average_findings_per_month=0.0,
        )
        
        # Forbidden fields that must NOT exist
        assert not hasattr(profile, "predicted_vulnerabilities")
        assert not hasattr(profile, "future_risk")
        assert not hasattr(profile, "recommended_tests")
        assert not hasattr(profile, "suggested_focus")
        assert not hasattr(profile, "vulnerability_forecast")
        assert not hasattr(profile, "risk_score")


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics dataclass."""
    
    def test_performance_metrics_is_frozen(self):
        """Verify PerformanceMetrics is immutable."""
        metrics = PerformanceMetrics(
            reviewer_id="reviewer-001",
            total_decisions=10,
            decisions_by_type={},
            average_review_time_seconds=300.0,
            severity_distribution={},
            submission_outcomes={},
            outcome_correlation=0.8,
            reversal_rate=0.1,
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
        )
        
        with pytest.raises(FrozenInstanceError):
            metrics.total_decisions = 100
    
    def test_performance_metrics_no_forbidden_fields(self):
        """Verify PerformanceMetrics has no forbidden fields."""
        metrics = PerformanceMetrics(
            reviewer_id="reviewer-001",
            total_decisions=0,
            decisions_by_type={},
            average_review_time_seconds=0.0,
            severity_distribution={},
            submission_outcomes={},
            outcome_correlation=0.0,
            reversal_rate=0.0,
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
        )
        
        # Forbidden fields that must NOT exist
        assert not hasattr(metrics, "rank")
        assert not hasattr(metrics, "percentile")
        assert not hasattr(metrics, "comparison")
        assert not hasattr(metrics, "team_average")
        assert not hasattr(metrics, "performance_target")
        assert not hasattr(metrics, "other_reviewers")
        assert not hasattr(metrics, "should_improve")
        assert not hasattr(metrics, "recommendation")


class TestPatternInsight:
    """Tests for PatternInsight dataclass."""
    
    def test_pattern_insight_is_frozen(self):
        """Verify PatternInsight is immutable."""
        insight = PatternInsight(
            insight_type="time_trend",
            description="Test trend",
            data_points=tuple(),
            trend_direction="increasing",
            confidence_note="Based on 10 data points",
        )
        
        with pytest.raises(FrozenInstanceError):
            insight.trend_direction = "decreasing"
    
    def test_pattern_insight_human_interpretation_required(self):
        """Verify human_interpretation_required is always True."""
        insight = PatternInsight(
            insight_type="time_trend",
            description="Test",
            data_points=tuple(),
            trend_direction=None,
            confidence_note="Test",
        )
        
        assert insight.human_interpretation_required is True
    
    def test_pattern_insight_no_forbidden_fields(self):
        """Verify PatternInsight has no forbidden fields."""
        insight = PatternInsight(
            insight_type="time_trend",
            description="Test",
            data_points=tuple(),
            trend_direction=None,
            confidence_note="Test",
        )
        
        # Forbidden fields that must NOT exist
        assert not hasattr(insight, "predicted_value")
        assert not hasattr(insight, "forecast")
        assert not hasattr(insight, "expected_trend")
        assert not hasattr(insight, "recommended_action")
        assert not hasattr(insight, "should_do")
        assert not hasattr(insight, "best_action")


class TestDataPoint:
    """Tests for DataPoint dataclass."""
    
    def test_data_point_is_frozen(self):
        """Verify DataPoint is immutable."""
        point = DataPoint(
            timestamp=datetime.now(),
            value=10.0,
            label="test",
        )
        
        with pytest.raises(FrozenInstanceError):
            point.value = 20.0


class TestTimelineEntry:
    """Tests for TimelineEntry dataclass."""
    
    def test_timeline_entry_is_frozen(self):
        """Verify TimelineEntry is immutable."""
        entry = TimelineEntry(
            period="2025-01",
            count=10,
            breakdown={"approve": 5, "reject": 5},
        )
        
        with pytest.raises(FrozenInstanceError):
            entry.count = 20
