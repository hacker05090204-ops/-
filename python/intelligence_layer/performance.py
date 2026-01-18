"""
Phase-8 Performance Analyzer

Computes personal reviewer metrics.

SAFETY CONSTRAINTS:
- This analyzer provides PERSONAL metrics only.
- NO comparison between reviewers.
- NO rankings.
- NO performance targets.
- NO recommendations.

FORBIDDEN CAPABILITIES:
- NO compare_reviewers()
- NO rank_reviewers()
- NO set_performance_target()
- NO team_average()
- NO percentile()
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict

from intelligence_layer.types import PerformanceMetrics
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.boundaries import BoundaryGuard


class PerformanceAnalyzer:
    """
    Computes personal performance metrics.
    
    SAFETY: This analyzer provides PERSONAL metrics only.
    - No comparison between reviewers
    - No rankings
    - No performance targets
    - No recommendations
    
    FORBIDDEN METHODS (do not add):
    - compare_reviewers()
    - rank_reviewers()
    - set_performance_target()
    - team_average()
    - percentile()
    - reviewer_ranking()
    """
    
    def __init__(self, data_access: DataAccessLayer):
        """
        Initialize the performance analyzer.
        
        Args:
            data_access: Read-only data access layer.
        """
        BoundaryGuard.assert_read_only()
        BoundaryGuard.assert_human_authority()
        
        self._data_access = data_access
    
    def get_performance_metrics(
        self,
        reviewer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PerformanceMetrics:
        """
        Get personal metrics for a reviewer.
        
        Args:
            reviewer_id: ID of the reviewer.
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            
        Returns:
            PerformanceMetrics for the specified reviewer.
            
        NOTE: This is PERSONAL data. No comparisons.
        """
        # Get decisions for this reviewer
        decisions = self._data_access.get_decisions(
            reviewer_id=reviewer_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Get review sessions for this reviewer
        sessions = self._data_access.get_review_sessions(
            reviewer_id=reviewer_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Initialize counters
        decisions_by_type: Dict[str, int] = defaultdict(int)
        severity_distribution: Dict[str, int] = defaultdict(int)
        
        min_date = datetime.max
        max_date = datetime.min
        
        decision_ids = []
        
        for decision in decisions:
            if isinstance(decision, dict):
                d_type = decision.get("decision_type")
                d_severity = decision.get("severity")
                d_timestamp = decision.get("timestamp")
                d_id = decision.get("decision_id")
            else:
                d_type = getattr(decision, "decision_type", None)
                d_severity = getattr(decision, "severity", None)
                d_timestamp = getattr(decision, "timestamp", None)
                d_id = getattr(decision, "decision_id", None)
            
            # Convert enums to strings
            if hasattr(d_type, "value"):
                d_type = d_type.value
            if hasattr(d_severity, "value"):
                d_severity = d_severity.value
            
            # Count by decision type
            if d_type:
                decisions_by_type[d_type] += 1
            
            # Count by severity
            if d_severity:
                severity_distribution[d_severity] += 1
            
            # Track dates
            if d_timestamp:
                if isinstance(d_timestamp, str):
                    d_timestamp = datetime.fromisoformat(d_timestamp)
                if d_timestamp < min_date:
                    min_date = d_timestamp
                if d_timestamp > max_date:
                    max_date = d_timestamp
            
            if d_id:
                decision_ids.append(d_id)
        
        # Calculate average review time from sessions
        total_review_time = 0.0
        session_count = 0
        
        for session in sessions:
            if isinstance(session, dict):
                s_start = session.get("start_time")
                s_end = session.get("end_time")
            else:
                s_start = getattr(session, "start_time", None)
                s_end = getattr(session, "end_time", None)
            
            if s_start and s_end:
                if isinstance(s_start, str):
                    s_start = datetime.fromisoformat(s_start)
                if isinstance(s_end, str):
                    s_end = datetime.fromisoformat(s_end)
                
                duration = (s_end - s_start).total_seconds()
                total_review_time += duration
                session_count += 1
        
        avg_review_time = total_review_time / session_count if session_count > 0 else 0.0
        
        # Get submission outcomes for this reviewer's decisions
        submission_outcomes: Dict[str, int] = defaultdict(int)
        accepted_count = 0
        approved_count = decisions_by_type.get("approve", 0)
        
        for decision_id in decision_ids:
            submissions = self._data_access.get_submissions(decision_id=decision_id)
            for submission in submissions:
                if isinstance(submission, dict):
                    s_status = submission.get("status")
                else:
                    s_status = getattr(submission, "status", None)
                
                # Convert enum to string
                if hasattr(s_status, "value"):
                    s_status = s_status.value
                
                if s_status:
                    submission_outcomes[s_status] += 1
                    if s_status == "acknowledged":
                        accepted_count += 1
        
        # Calculate outcome correlation (approved findings that were accepted)
        outcome_correlation = 0.0
        if approved_count > 0:
            outcome_correlation = accepted_count / approved_count
        
        # Calculate reversal rate (placeholder - would need senior review data)
        reversal_rate = 0.0  # Not implemented without senior review tracking
        
        # Handle edge cases for dates
        if min_date == datetime.max:
            min_date = start_date or datetime.now()
        if max_date == datetime.min:
            max_date = end_date or datetime.now()
        
        return PerformanceMetrics(
            reviewer_id=reviewer_id,
            total_decisions=len(decisions),
            decisions_by_type=dict(decisions_by_type),
            average_review_time_seconds=avg_review_time,
            severity_distribution=dict(severity_distribution),
            submission_outcomes=dict(submission_outcomes),
            outcome_correlation=outcome_correlation,
            reversal_rate=reversal_rate,
            date_range_start=min_date,
            date_range_end=max_date,
            human_interpretation_required=True,
            no_accuracy_guarantee="No accuracy guarantee - human expertise required",
        )
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    # - compare_reviewers()
    # - rank_reviewers()
    # - set_performance_target()
    # - team_average()
    # - percentile()
    # - reviewer_ranking()
    # - get_all_reviewers_metrics()
    # - leaderboard()
    # ========================================================================
