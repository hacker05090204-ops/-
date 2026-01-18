"""
Tests for Phase-8 Pattern Engine

Verifies that:
- Pattern insights are observations only
- No predictions
- No recommendations
- Human interpretation always required
"""

import pytest
from datetime import datetime, timedelta

from intelligence_layer.patterns import PatternEngine
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.types import PatternInsight, DataPoint
from intelligence_layer.tests.conftest import create_sample_decision, create_sample_submission


class TestPatternEngineBasic:
    """Basic tests for pattern engine."""
    
    def test_get_time_trends_returns_insight(self, pattern_engine):
        """Verify get_time_trends returns PatternInsight."""
        insight = pattern_engine.get_time_trends("findings_count")
        
        assert isinstance(insight, PatternInsight)
    
    def test_human_interpretation_required_always_true(self, pattern_engine):
        """Verify human_interpretation_required is always True."""
        insight = pattern_engine.get_time_trends("findings_count")
        
        assert insight.human_interpretation_required is True
    
    def test_no_accuracy_guarantee_present(self, pattern_engine):
        """Verify no_accuracy_guarantee disclaimer is present."""
        insight = pattern_engine.get_time_trends("findings_count")
        
        assert "no accuracy guarantee" in insight.no_accuracy_guarantee.lower()


class TestPatternEngineTimeTrends:
    """Tests for time trend analysis."""
    
    def test_findings_count_trend(self):
        """Verify findings count trend is computed."""
        base_time = datetime(2025, 1, 1)
        decisions = [
            create_sample_decision(
                decision_id=f"dec-{i}",
                timestamp=base_time + timedelta(days=i * 7),
            )
            for i in range(10)
        ]
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_time_trends("findings_count", granularity="week")
        
        assert insight.insight_type == "time_trend_findings_count"
        assert len(insight.data_points) > 0
    
    def test_severity_distribution_trend(self):
        """Verify severity distribution trend is computed."""
        base_time = datetime(2025, 1, 1)
        decisions = [
            create_sample_decision(
                decision_id=f"dec-{i}",
                timestamp=base_time + timedelta(days=i * 7),
                severity=["critical", "high", "medium", "low"][i % 4],
            )
            for i in range(10)
        ]
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_time_trends("severity_distribution", granularity="week")
        
        assert insight.insight_type == "time_trend_severity_distribution"
    
    def test_granularity_day(self):
        """Verify day granularity works."""
        base_time = datetime(2025, 1, 1)
        decisions = [
            create_sample_decision(
                decision_id=f"dec-{i}",
                timestamp=base_time + timedelta(days=i),
            )
            for i in range(5)
        ]
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_time_trends("findings_count", granularity="day")
        
        assert len(insight.data_points) == 5
    
    def test_granularity_month(self):
        """Verify month granularity works."""
        base_time = datetime(2025, 1, 1)
        decisions = [
            create_sample_decision(
                decision_id=f"dec-{i}",
                timestamp=base_time + timedelta(days=i * 30),
            )
            for i in range(3)
        ]
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_time_trends("findings_count", granularity="month")
        
        assert len(insight.data_points) >= 1


class TestPatternEngineTypeDistribution:
    """Tests for type distribution analysis."""
    
    def test_type_distribution_returns_insight(self, pattern_engine):
        """Verify get_type_distribution_trend returns PatternInsight."""
        insight = pattern_engine.get_type_distribution_trend()
        
        assert isinstance(insight, PatternInsight)
        assert insight.insight_type == "type_distribution"
    
    def test_type_distribution_counts_types(self):
        """Verify type distribution counts vulnerability types."""
        decisions = [
            create_sample_decision(decision_id="dec-001", vulnerability_type="xss"),
            create_sample_decision(decision_id="dec-002", vulnerability_type="xss"),
            create_sample_decision(decision_id="dec-003", vulnerability_type="sqli"),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_type_distribution_trend()
        
        # Should have data points for each type
        labels = [dp.label for dp in insight.data_points]
        assert "xss" in labels
        assert "sqli" in labels


class TestPatternEnginePlatformResponse:
    """Tests for platform response trend analysis."""
    
    def test_platform_response_trend_returns_insight(self, pattern_engine):
        """Verify get_platform_response_trend returns PatternInsight."""
        insight = pattern_engine.get_platform_response_trend()
        
        assert isinstance(insight, PatternInsight)
        assert insight.insight_type == "platform_response_trend"
    
    def test_platform_response_calculates_average(self):
        """Verify platform response calculates average response time."""
        base_time = datetime(2025, 1, 1)
        submissions = [
            create_sample_submission(
                submission_id=f"sub-{i}",
                submitted_at=base_time + timedelta(days=i * 30),
                responded_at=base_time + timedelta(days=i * 30 + 7),
            )
            for i in range(3)
        ]
        data_access = DataAccessLayer(submissions=submissions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_platform_response_trend(granularity="month")
        
        # Should have data points with average response times
        if insight.data_points:
            assert all(dp.value >= 0 for dp in insight.data_points)


class TestPatternEngineTrendDirection:
    """Tests for trend direction computation."""
    
    def test_increasing_trend_detected(self):
        """Verify increasing trend is detected."""
        base_time = datetime(2025, 1, 1)
        # Create increasing pattern: 1, 2, 3, 4, 5 findings per week
        decisions = []
        for week in range(5):
            for i in range(week + 1):
                decisions.append(create_sample_decision(
                    decision_id=f"dec-{week}-{i}",
                    timestamp=base_time + timedelta(weeks=week),
                ))
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_time_trends("findings_count", granularity="week")
        
        assert insight.trend_direction == "increasing"
    
    def test_decreasing_trend_detected(self):
        """Verify decreasing trend is detected."""
        base_time = datetime(2025, 1, 1)
        # Create decreasing pattern: 5, 4, 3, 2, 1 findings per week
        decisions = []
        for week in range(5):
            for i in range(5 - week):
                decisions.append(create_sample_decision(
                    decision_id=f"dec-{week}-{i}",
                    timestamp=base_time + timedelta(weeks=week),
                ))
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_time_trends("findings_count", granularity="week")
        
        assert insight.trend_direction == "decreasing"
    
    def test_stable_trend_detected(self):
        """Verify stable trend is detected."""
        base_time = datetime(2025, 1, 1)
        # Create stable pattern: 3 findings per week
        decisions = []
        for week in range(5):
            for i in range(3):
                decisions.append(create_sample_decision(
                    decision_id=f"dec-{week}-{i}",
                    timestamp=base_time + timedelta(weeks=week),
                ))
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_time_trends("findings_count", granularity="week")
        
        assert insight.trend_direction == "stable"
    
    def test_insufficient_data_no_trend(self):
        """Verify insufficient data returns no trend direction."""
        decisions = [create_sample_decision(decision_id="dec-001")]
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        insight = engine.get_time_trends("findings_count", granularity="week")
        
        # With only one data point, trend direction should be None
        assert insight.trend_direction is None


class TestPatternEngineEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_data_returns_empty_insight(self, empty_data_access):
        """Verify empty data returns insight with no data points."""
        engine = PatternEngine(empty_data_access)
        
        insight = engine.get_time_trends("findings_count")
        
        assert len(insight.data_points) == 0
        assert insight.trend_direction is None
        assert "No data available" in insight.description
    
    def test_empty_submissions_returns_empty_response_trend(self, empty_data_access):
        """Verify empty submissions returns empty response trend."""
        engine = PatternEngine(empty_data_access)
        
        insight = engine.get_platform_response_trend()
        
        assert len(insight.data_points) == 0
        assert "No data available" in insight.description
    
    def test_date_range_filtering(self):
        """Verify date range filtering works."""
        base_time = datetime(2025, 1, 1)
        decisions = [
            create_sample_decision(
                decision_id=f"dec-{i}",
                timestamp=base_time + timedelta(days=i * 30),
            )
            for i in range(6)
        ]
        data_access = DataAccessLayer(decisions=decisions)
        engine = PatternEngine(data_access)
        
        # Filter to first 3 months
        insight = engine.get_time_trends(
            "findings_count",
            granularity="month",
            start_date=base_time,
            end_date=base_time + timedelta(days=90),
        )
        
        # Should have fewer data points than full range
        assert len(insight.data_points) <= 4


class TestPatternEngineNoForbiddenMethods:
    """Tests to verify no forbidden methods exist."""
    
    def test_no_predict_trend_method(self, pattern_engine):
        """Verify predict_trend method does not exist."""
        assert not hasattr(pattern_engine, "predict_trend")
    
    def test_no_recommend_action_method(self, pattern_engine):
        """Verify recommend_action method does not exist."""
        assert not hasattr(pattern_engine, "recommend_action")
    
    def test_no_forecast_method(self, pattern_engine):
        """Verify forecast method does not exist."""
        assert not hasattr(pattern_engine, "forecast")
    
    def test_no_expected_trend_method(self, pattern_engine):
        """Verify expected_trend method does not exist."""
        assert not hasattr(pattern_engine, "expected_trend")
    
    def test_no_should_do_method(self, pattern_engine):
        """Verify should_do method does not exist."""
        assert not hasattr(pattern_engine, "should_do")
    
    def test_no_future_value_method(self, pattern_engine):
        """Verify future_value method does not exist."""
        assert not hasattr(pattern_engine, "future_value")
    
    def test_no_predict_next_period_method(self, pattern_engine):
        """Verify predict_next_period method does not exist."""
        assert not hasattr(pattern_engine, "predict_next_period")


class TestPatternInsightNoForbiddenFields:
    """Tests to verify PatternInsight has no forbidden fields."""
    
    def test_no_predicted_value_field(self, pattern_engine):
        """Verify PatternInsight has no predicted_value field."""
        insight = pattern_engine.get_time_trends("findings_count")
        
        assert not hasattr(insight, "predicted_value")
    
    def test_no_forecast_field(self, pattern_engine):
        """Verify PatternInsight has no forecast field."""
        insight = pattern_engine.get_time_trends("findings_count")
        
        assert not hasattr(insight, "forecast")
    
    def test_no_expected_trend_field(self, pattern_engine):
        """Verify PatternInsight has no expected_trend field."""
        insight = pattern_engine.get_time_trends("findings_count")
        
        assert not hasattr(insight, "expected_trend")
    
    def test_no_recommended_action_field(self, pattern_engine):
        """Verify PatternInsight has no recommended_action field."""
        insight = pattern_engine.get_time_trends("findings_count")
        
        assert not hasattr(insight, "recommended_action")
    
    def test_no_should_do_field(self, pattern_engine):
        """Verify PatternInsight has no should_do field."""
        insight = pattern_engine.get_time_trends("findings_count")
        
        assert not hasattr(insight, "should_do")
    
    def test_no_best_action_field(self, pattern_engine):
        """Verify PatternInsight has no best_action field."""
        insight = pattern_engine.get_time_trends("findings_count")
        
        assert not hasattr(insight, "best_action")
