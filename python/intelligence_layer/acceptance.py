"""
Phase-8 Acceptance Tracker

Tracks historical acceptance rates by platform and vulnerability type.

SAFETY CONSTRAINTS:
- This tracker provides STATISTICS only.
- It does NOT recommend platforms or prioritize findings.
- All data is historical - no predictions.
- Human interprets the data.

FORBIDDEN CAPABILITIES:
- NO platform recommendations
- NO prioritization
- NO predictions
- NO "best platform" suggestions
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict

from intelligence_layer.types import AcceptancePattern
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.boundaries import BoundaryGuard


class AcceptanceTracker:
    """
    Tracks historical acceptance rates by platform and type.
    
    SAFETY: This tracker provides STATISTICS only. It does NOT
    recommend platforms or prioritize findings.
    
    FORBIDDEN METHODS (do not add):
    - recommend_platform()
    - best_platform()
    - prioritize_by_acceptance()
    - should_submit_to()
    - suggest_platform()
    """
    
    def __init__(self, data_access: DataAccessLayer):
        """
        Initialize the acceptance tracker.
        
        Args:
            data_access: Read-only data access layer.
        """
        BoundaryGuard.assert_read_only()
        BoundaryGuard.assert_human_authority()
        
        self._data_access = data_access
    
    def get_acceptance_patterns(
        self,
        platform: Optional[str] = None,
        vulnerability_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AcceptancePattern]:
        """
        Get acceptance patterns with optional filters.
        
        Args:
            platform: Filter by platform.
            vulnerability_type: Filter by vulnerability type.
            severity: Filter by severity.
            start_date: Filter by start date.
            end_date: Filter by end date.
            
        Returns:
            List of AcceptancePattern statistics.
            
        NOTE: This method provides DATA only. Human interprets.
        """
        # Get all submissions
        submissions = self._data_access.get_submissions(
            platform=platform,
            start_date=start_date,
            end_date=end_date,
        )
        
        if not submissions:
            return []
        
        # Group submissions by platform, vulnerability_type, severity
        groups: Dict[tuple, List[Any]] = defaultdict(list)
        
        for submission in submissions:
            if isinstance(submission, dict):
                s_platform = submission.get("platform")
                s_vuln_type = submission.get("vulnerability_type")
                s_severity = submission.get("severity")
            else:
                s_platform = getattr(submission, "platform", None)
                s_vuln_type = getattr(submission, "vulnerability_type", None)
                s_severity = getattr(submission, "severity", None)
            
            # Convert enums to strings
            if hasattr(s_platform, "value"):
                s_platform = s_platform.value
            if hasattr(s_severity, "value"):
                s_severity = s_severity.value
            
            # Apply filters
            if vulnerability_type is not None and s_vuln_type != vulnerability_type:
                continue
            if severity is not None and s_severity != severity:
                continue
            
            key = (s_platform, s_vuln_type, s_severity)
            groups[key].append(submission)
        
        # Compute patterns for each group
        patterns = []
        for (grp_platform, grp_vuln_type, grp_severity), group_submissions in groups.items():
            pattern = self._compute_pattern(
                grp_platform,
                grp_vuln_type,
                grp_severity,
                group_submissions,
                start_date,
                end_date,
            )
            patterns.append(pattern)
        
        return patterns
    
    def get_platform_comparison(
        self,
        vulnerability_type: Optional[str] = None,
    ) -> Dict[str, AcceptancePattern]:
        """
        Get acceptance patterns grouped by platform.
        
        Args:
            vulnerability_type: Optional filter by vulnerability type.
            
        Returns:
            Dictionary mapping platform to AcceptancePattern.
            
        NOTE: This is NOT a recommendation. Human decides platform.
        """
        patterns = self.get_acceptance_patterns(vulnerability_type=vulnerability_type)
        
        # Group by platform
        result: Dict[str, AcceptancePattern] = {}
        for pattern in patterns:
            if pattern.platform not in result:
                result[pattern.platform] = pattern
            else:
                # Merge patterns for same platform
                existing = result[pattern.platform]
                result[pattern.platform] = AcceptancePattern(
                    platform=pattern.platform,
                    vulnerability_type=None,  # Mixed types
                    severity=None,  # Mixed severities
                    total_submissions=existing.total_submissions + pattern.total_submissions,
                    accepted_count=existing.accepted_count + pattern.accepted_count,
                    rejected_count=existing.rejected_count + pattern.rejected_count,
                    pending_count=existing.pending_count + pattern.pending_count,
                    acceptance_rate=self._compute_rate(
                        existing.accepted_count + pattern.accepted_count,
                        existing.total_submissions + pattern.total_submissions,
                    ),
                    average_response_days=None,  # Would need recalculation
                    date_range_start=min(existing.date_range_start, pattern.date_range_start),
                    date_range_end=max(existing.date_range_end, pattern.date_range_end),
                    human_interpretation_required=True,
                    no_accuracy_guarantee="No accuracy guarantee - human expertise required",
                )
        
        return result
    
    def _compute_pattern(
        self,
        platform: str,
        vulnerability_type: Optional[str],
        severity: Optional[str],
        submissions: List[Any],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> AcceptancePattern:
        """Compute acceptance pattern for a group of submissions."""
        total = len(submissions)
        accepted = 0
        rejected = 0
        pending = 0
        response_days: List[float] = []
        
        min_date = datetime.max
        max_date = datetime.min
        
        for submission in submissions:
            if isinstance(submission, dict):
                status = submission.get("status")
                submitted_at = submission.get("submitted_at", submission.get("created_at"))
                responded_at = submission.get("responded_at")
            else:
                status = getattr(submission, "status", None)
                submitted_at = getattr(submission, "submitted_at", getattr(submission, "created_at", None))
                responded_at = getattr(submission, "responded_at", None)
            
            # Convert enum to string
            if hasattr(status, "value"):
                status = status.value
            
            # Count by status
            if status == "acknowledged":
                accepted += 1
            elif status == "rejected":
                rejected += 1
            elif status in ("pending", "confirmed", "submitted"):
                pending += 1
            
            # Track dates
            if submitted_at:
                if isinstance(submitted_at, str):
                    submitted_at = datetime.fromisoformat(submitted_at)
                if submitted_at < min_date:
                    min_date = submitted_at
                if submitted_at > max_date:
                    max_date = submitted_at
                
                # Calculate response time
                if responded_at:
                    if isinstance(responded_at, str):
                        responded_at = datetime.fromisoformat(responded_at)
                    days = (responded_at - submitted_at).days
                    response_days.append(days)
        
        # Handle edge cases for dates
        if min_date == datetime.max:
            min_date = start_date or datetime.now()
        if max_date == datetime.min:
            max_date = end_date or datetime.now()
        
        return AcceptancePattern(
            platform=platform or "unknown",
            vulnerability_type=vulnerability_type,
            severity=severity,
            total_submissions=total,
            accepted_count=accepted,
            rejected_count=rejected,
            pending_count=pending,
            acceptance_rate=self._compute_rate(accepted, total),
            average_response_days=sum(response_days) / len(response_days) if response_days else None,
            date_range_start=min_date,
            date_range_end=max_date,
            human_interpretation_required=True,
            no_accuracy_guarantee="No accuracy guarantee - human expertise required",
        )
    
    def _compute_rate(self, accepted: int, total: int) -> float:
        """Compute acceptance rate."""
        if total == 0:
            return 0.0
        return accepted / total
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    # - recommend_platform()
    # - best_platform()
    # - prioritize_by_acceptance()
    # - should_submit_to()
    # - suggest_platform()
    # - rank_platforms()
    # - optimal_platform()
    # ========================================================================
