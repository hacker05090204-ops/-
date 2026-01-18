"""
Phase-8 Pattern Engine

Surfaces trend observations from historical data.

SAFETY CONSTRAINTS:
- This engine provides OBSERVATIONS only.
- NO predictions.
- NO recommendations.
- NO automated actions.
- Human interprets the data.

FORBIDDEN CAPABILITIES:
- NO predict_trend()
- NO recommend_action()
- NO forecast()
- NO expected_trend()
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict

from intelligence_layer.types import PatternInsight, DataPoint
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.boundaries import BoundaryGuard


class PatternEngine:
    """
    Surfaces trend observations from historical data.
    
    SAFETY: This engine provides OBSERVATIONS only.
    - No predictions
    - No recommendations
    - No automated actions
    
    FORBIDDEN METHODS (do not add):
    - predict_trend()
    - recommend_action()
    - forecast()
    - expected_trend()
    - should_do()
    """
    
    def __init__(self, data_access: DataAccessLayer):
        """
        Initialize the pattern engine.
        
        Args:
            data_access: Read-only data access layer.
        """
        BoundaryGuard.assert_read_only()
        BoundaryGuard.assert_human_authority()
        
        self._data_access = data_access
    
    def get_time_trends(
        self,
        metric: str,
        granularity: str = "week",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PatternInsight:
        """
        Get time-based trend for a metric.
        
        Args:
            metric: Metric to analyze ("findings_count", "severity_distribution", etc.).
            granularity: Time granularity ("day", "week", "month").
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            
        Returns:
            PatternInsight with trend observation.
            
        NOTE: This is an OBSERVATION. Human interprets.
        """
        # Get all decisions
        decisions = self._data_access.get_decisions(
            start_date=start_date,
            end_date=end_date,
        )
        
        if not decisions:
            return PatternInsight(
                insight_type=f"time_trend_{metric}",
                description=f"No data available for {metric} trend analysis.",
                data_points=tuple(),
                trend_direction=None,
                confidence_note="Based on 0 data points",
                human_interpretation_required=True,
                no_accuracy_guarantee="No accuracy guarantee - human expertise required",
            )
        
        # Group by time period
        periods: Dict[str, float] = defaultdict(float)
        
        for decision in decisions:
            if isinstance(decision, dict):
                d_timestamp = decision.get("timestamp")
                d_severity = decision.get("severity")
            else:
                d_timestamp = getattr(decision, "timestamp", None)
                d_severity = getattr(decision, "severity", None)
            
            if not d_timestamp:
                continue
            
            if isinstance(d_timestamp, str):
                d_timestamp = datetime.fromisoformat(d_timestamp)
            
            # Determine period key
            if granularity == "day":
                period_key = d_timestamp.strftime("%Y-%m-%d")
            elif granularity == "week":
                period_key = d_timestamp.strftime("%Y-W%W")
            else:  # month
                period_key = d_timestamp.strftime("%Y-%m")
            
            # Count based on metric
            if metric == "findings_count":
                periods[period_key] += 1
            elif metric == "severity_distribution":
                # Convert severity to numeric value for trend
                if hasattr(d_severity, "value"):
                    d_severity = d_severity.value
                severity_values = {
                    "critical": 5,
                    "high": 4,
                    "medium": 3,
                    "low": 2,
                    "informational": 1,
                }
                periods[period_key] += severity_values.get(d_severity, 0)
            else:
                periods[period_key] += 1
        
        # Convert to data points
        data_points = []
        sorted_periods = sorted(periods.keys())
        
        for period_key in sorted_periods:
            # Parse period key back to datetime
            try:
                if granularity == "day":
                    ts = datetime.strptime(period_key, "%Y-%m-%d")
                elif granularity == "week":
                    ts = datetime.strptime(period_key + "-1", "%Y-W%W-%w")
                else:
                    ts = datetime.strptime(period_key + "-01", "%Y-%m-%d")
            except ValueError:
                ts = datetime.now()
            
            data_points.append(DataPoint(
                timestamp=ts,
                value=periods[period_key],
                label=period_key,
            ))
        
        # Determine trend direction (simple linear comparison)
        trend_direction = self._compute_trend_direction(data_points)
        
        return PatternInsight(
            insight_type=f"time_trend_{metric}",
            description=f"Historical trend for {metric} by {granularity}.",
            data_points=tuple(data_points),
            trend_direction=trend_direction,
            confidence_note=f"Based on {len(data_points)} data points",
            human_interpretation_required=True,
            no_accuracy_guarantee="No accuracy guarantee - human expertise required",
        )
    
    def get_type_distribution_trend(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PatternInsight:
        """
        Get vulnerability type distribution over time.
        
        Args:
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            
        Returns:
            PatternInsight with distribution observation.
            
        NOTE: This is HISTORICAL data. No predictions.
        """
        decisions = self._data_access.get_decisions(
            start_date=start_date,
            end_date=end_date,
        )
        
        if not decisions:
            return PatternInsight(
                insight_type="type_distribution",
                description="No data available for type distribution analysis.",
                data_points=tuple(),
                trend_direction=None,
                confidence_note="Based on 0 data points",
                human_interpretation_required=True,
                no_accuracy_guarantee="No accuracy guarantee - human expertise required",
            )
        
        # Count by vulnerability type
        type_counts: Dict[str, int] = defaultdict(int)
        
        for decision in decisions:
            if isinstance(decision, dict):
                d_type = decision.get("vulnerability_type", decision.get("classification"))
            else:
                d_type = getattr(decision, "vulnerability_type", getattr(decision, "classification", None))
            
            if d_type:
                type_counts[d_type] += 1
        
        # Convert to data points
        data_points = []
        for vuln_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            data_points.append(DataPoint(
                timestamp=datetime.now(),  # Distribution is current snapshot
                value=float(count),
                label=vuln_type,
            ))
        
        return PatternInsight(
            insight_type="type_distribution",
            description="Distribution of vulnerability types in historical data.",
            data_points=tuple(data_points),
            trend_direction=None,  # Distribution doesn't have a direction
            confidence_note=f"Based on {len(decisions)} findings",
            human_interpretation_required=True,
            no_accuracy_guarantee="No accuracy guarantee - human expertise required",
        )
    
    def get_platform_response_trend(
        self,
        granularity: str = "month",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PatternInsight:
        """
        Get platform response time trends.
        
        Args:
            granularity: Time granularity ("day", "week", "month").
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            
        Returns:
            PatternInsight with response time observation.
            
        NOTE: This is HISTORICAL data. No predictions.
        """
        submissions = self._data_access.get_submissions(
            start_date=start_date,
            end_date=end_date,
        )
        
        if not submissions:
            return PatternInsight(
                insight_type="platform_response_trend",
                description="No data available for platform response trend analysis.",
                data_points=tuple(),
                trend_direction=None,
                confidence_note="Based on 0 data points",
                human_interpretation_required=True,
                no_accuracy_guarantee="No accuracy guarantee - human expertise required",
            )
        
        # Group response times by period
        periods: Dict[str, List[float]] = defaultdict(list)
        
        for submission in submissions:
            if isinstance(submission, dict):
                s_submitted = submission.get("submitted_at", submission.get("created_at"))
                s_responded = submission.get("responded_at")
            else:
                s_submitted = getattr(submission, "submitted_at", getattr(submission, "created_at", None))
                s_responded = getattr(submission, "responded_at", None)
            
            if not s_submitted or not s_responded:
                continue
            
            if isinstance(s_submitted, str):
                s_submitted = datetime.fromisoformat(s_submitted)
            if isinstance(s_responded, str):
                s_responded = datetime.fromisoformat(s_responded)
            
            # Calculate response time in days
            response_days = (s_responded - s_submitted).days
            
            # Determine period key
            if granularity == "day":
                period_key = s_submitted.strftime("%Y-%m-%d")
            elif granularity == "week":
                period_key = s_submitted.strftime("%Y-W%W")
            else:
                period_key = s_submitted.strftime("%Y-%m")
            
            periods[period_key].append(response_days)
        
        # Calculate average response time per period
        data_points = []
        for period_key in sorted(periods.keys()):
            avg_response = sum(periods[period_key]) / len(periods[period_key])
            
            try:
                if granularity == "day":
                    ts = datetime.strptime(period_key, "%Y-%m-%d")
                elif granularity == "week":
                    ts = datetime.strptime(period_key + "-1", "%Y-W%W-%w")
                else:
                    ts = datetime.strptime(period_key + "-01", "%Y-%m-%d")
            except ValueError:
                ts = datetime.now()
            
            data_points.append(DataPoint(
                timestamp=ts,
                value=avg_response,
                label=period_key,
            ))
        
        trend_direction = self._compute_trend_direction(data_points)
        
        return PatternInsight(
            insight_type="platform_response_trend",
            description=f"Average platform response time by {granularity}.",
            data_points=tuple(data_points),
            trend_direction=trend_direction,
            confidence_note=f"Based on {len(data_points)} periods",
            human_interpretation_required=True,
            no_accuracy_guarantee="No accuracy guarantee - human expertise required",
        )
    
    def _compute_trend_direction(self, data_points: List[DataPoint]) -> Optional[str]:
        """
        Compute simple trend direction from data points.
        
        Returns:
            "increasing", "decreasing", "stable", or None if insufficient data.
            
        NOTE: This is a simple heuristic, not a prediction.
        """
        if len(data_points) < 2:
            return None
        
        # Compare first half average to second half average
        mid = len(data_points) // 2
        first_half = data_points[:mid]
        second_half = data_points[mid:]
        
        first_avg = sum(dp.value for dp in first_half) / len(first_half)
        second_avg = sum(dp.value for dp in second_half) / len(second_half)
        
        # Use 10% threshold for "stable"
        if first_avg == 0:
            if second_avg > 0:
                return "increasing"
            return "stable"
        
        change_ratio = (second_avg - first_avg) / first_avg
        
        if change_ratio > 0.1:
            return "increasing"
        elif change_ratio < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    # - predict_trend()
    # - recommend_action()
    # - forecast()
    # - expected_trend()
    # - should_do()
    # - future_value()
    # - predict_next_period()
    # ========================================================================
