"""
Phase-8 Target Profiler

Builds intelligence profiles from historical data.

SAFETY CONSTRAINTS:
- This profiler provides HISTORY only.
- It does NOT predict future vulnerabilities.
- It does NOT recommend testing strategies.
- Human interprets the data.

FORBIDDEN CAPABILITIES:
- NO predictions
- NO recommendations
- NO risk scores
- NO vulnerability forecasts
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict

from intelligence_layer.types import TargetProfile, TimelineEntry
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.boundaries import BoundaryGuard


class TargetProfiler:
    """
    Builds target profiles from historical data.
    
    SAFETY: This profiler provides HISTORY only. It does NOT
    predict or recommend.
    
    FORBIDDEN METHODS (do not add):
    - predict_vulnerabilities()
    - recommend_tests()
    - risk_score()
    - vulnerability_forecast()
    - suggest_focus()
    """
    
    def __init__(self, data_access: DataAccessLayer):
        """
        Initialize the target profiler.
        
        Args:
            data_access: Read-only data access layer.
        """
        BoundaryGuard.assert_read_only()
        BoundaryGuard.assert_human_authority()
        
        self._data_access = data_access
    
    def get_target_profile(self, target_id: str) -> TargetProfile:
        """
        Build a profile for a specific target.
        
        Args:
            target_id: ID of the target.
            
        Returns:
            TargetProfile with historical statistics.
            
        NOTE: This is HISTORICAL data. Human interprets.
        """
        # Get all decisions for this target
        decisions = self._data_access.get_decisions(target_id=target_id)
        
        # Initialize counters
        findings_by_decision: Dict[str, int] = defaultdict(int)
        findings_by_severity: Dict[str, int] = defaultdict(int)
        findings_by_type: Dict[str, int] = defaultdict(int)
        
        first_date: Optional[datetime] = None
        last_date: Optional[datetime] = None
        
        decision_ids = []
        
        for decision in decisions:
            if isinstance(decision, dict):
                d_type = decision.get("decision_type")
                d_severity = decision.get("severity")
                d_vuln_type = decision.get("vulnerability_type", decision.get("classification"))
                d_timestamp = decision.get("timestamp")
                d_id = decision.get("decision_id")
            else:
                d_type = getattr(decision, "decision_type", None)
                d_severity = getattr(decision, "severity", None)
                d_vuln_type = getattr(decision, "vulnerability_type", getattr(decision, "classification", None))
                d_timestamp = getattr(decision, "timestamp", None)
                d_id = getattr(decision, "decision_id", None)
            
            # Convert enums to strings
            if hasattr(d_type, "value"):
                d_type = d_type.value
            if hasattr(d_severity, "value"):
                d_severity = d_severity.value
            
            # Count by decision type
            if d_type:
                findings_by_decision[d_type] += 1
            
            # Count by severity
            if d_severity:
                findings_by_severity[d_severity] += 1
            
            # Count by vulnerability type
            if d_vuln_type:
                findings_by_type[d_vuln_type] += 1
            
            # Track dates
            if d_timestamp:
                if isinstance(d_timestamp, str):
                    d_timestamp = datetime.fromisoformat(d_timestamp)
                if first_date is None or d_timestamp < first_date:
                    first_date = d_timestamp
                if last_date is None or d_timestamp > last_date:
                    last_date = d_timestamp
            
            if d_id:
                decision_ids.append(d_id)
        
        # Get submission data
        submissions_by_platform: Dict[str, int] = defaultdict(int)
        submission_outcomes: Dict[str, int] = defaultdict(int)
        
        for decision_id in decision_ids:
            submissions = self._data_access.get_submissions(decision_id=decision_id)
            for submission in submissions:
                if isinstance(submission, dict):
                    s_platform = submission.get("platform")
                    s_status = submission.get("status")
                else:
                    s_platform = getattr(submission, "platform", None)
                    s_status = getattr(submission, "status", None)
                
                # Convert enums to strings
                if hasattr(s_platform, "value"):
                    s_platform = s_platform.value
                if hasattr(s_status, "value"):
                    s_status = s_status.value
                
                if s_platform:
                    submissions_by_platform[s_platform] += 1
                if s_status:
                    submission_outcomes[s_status] += 1
        
        # Calculate average findings per month
        total_findings = len(decisions)
        avg_per_month = 0.0
        if first_date and last_date and first_date != last_date:
            months = max(1, (last_date - first_date).days / 30)
            avg_per_month = total_findings / months
        
        return TargetProfile(
            target_id=target_id,
            total_findings=total_findings,
            findings_by_decision=dict(findings_by_decision),
            findings_by_severity=dict(findings_by_severity),
            findings_by_type=dict(findings_by_type),
            submissions_by_platform=dict(submissions_by_platform),
            submission_outcomes=dict(submission_outcomes),
            first_finding_date=first_date,
            last_finding_date=last_date,
            average_findings_per_month=avg_per_month,
            human_interpretation_required=True,
            no_accuracy_guarantee="No accuracy guarantee - human expertise required",
        )
    
    def get_target_timeline(
        self,
        target_id: str,
        granularity: str = "month",
    ) -> List[TimelineEntry]:
        """
        Get finding timeline for a target.
        
        Args:
            target_id: ID of the target.
            granularity: Time granularity ("day", "week", "month").
            
        Returns:
            List of TimelineEntry objects.
            
        NOTE: This is HISTORICAL data. No predictions.
        """
        decisions = self._data_access.get_decisions(target_id=target_id)
        
        if not decisions:
            return []
        
        # Group by time period
        periods: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for decision in decisions:
            if isinstance(decision, dict):
                d_timestamp = decision.get("timestamp")
                d_type = decision.get("decision_type")
            else:
                d_timestamp = getattr(decision, "timestamp", None)
                d_type = getattr(decision, "decision_type", None)
            
            if not d_timestamp:
                continue
            
            if isinstance(d_timestamp, str):
                d_timestamp = datetime.fromisoformat(d_timestamp)
            
            # Convert enum to string
            if hasattr(d_type, "value"):
                d_type = d_type.value
            
            # Determine period key
            if granularity == "day":
                period_key = d_timestamp.strftime("%Y-%m-%d")
            elif granularity == "week":
                # ISO week
                period_key = d_timestamp.strftime("%Y-W%W")
            else:  # month
                period_key = d_timestamp.strftime("%Y-%m")
            
            periods[period_key]["total"] += 1
            if d_type:
                periods[period_key][d_type] += 1
        
        # Convert to TimelineEntry objects
        timeline = []
        for period_key in sorted(periods.keys()):
            breakdown = dict(periods[period_key])
            total = breakdown.pop("total", 0)
            timeline.append(TimelineEntry(
                period=period_key,
                count=total,
                breakdown=breakdown,
            ))
        
        return timeline
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    # - predict_vulnerabilities()
    # - recommend_tests()
    # - risk_score()
    # - vulnerability_forecast()
    # - suggest_focus()
    # - future_risk()
    # - expected_vulnerabilities()
    # ========================================================================
