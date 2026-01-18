"""
Phase-8 Data Access Layer

Provides READ-ONLY access to Phase-6 and Phase-7 data.

SAFETY CONSTRAINTS:
- NO write methods exist
- NO modification of source data
- All data access is strictly read-only
- Data is copied, not referenced (to prevent accidental mutation)

This layer is the ONLY interface between Phase-8 and historical data.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Any
import copy

from intelligence_layer.boundaries import BoundaryGuard


@dataclass
class DataAccessLayer:
    """
    Read-only access to historical data.
    
    SAFETY: This layer provides NO write methods. All data access
    is strictly read-only. Data is deep-copied to prevent accidental
    mutation of source data.
    
    FORBIDDEN METHODS (do not add):
    - write_decision, modify_decision, delete_decision
    - write_submission, modify_submission, delete_submission
    - write_audit, modify_audit, delete_audit
    - Any method that modifies source data
    """
    
    # In-memory storage for testing and demonstration
    # In production, this would connect to actual Phase-6/Phase-7 stores
    _decisions: List[Any]
    _submissions: List[Any]
    _review_sessions: List[Any]
    
    def __init__(
        self,
        decisions: Optional[List[Any]] = None,
        submissions: Optional[List[Any]] = None,
        review_sessions: Optional[List[Any]] = None,
    ):
        """
        Initialize the data access layer.
        
        Args:
            decisions: List of HumanDecision records (or dicts).
            submissions: List of SubmissionRecord records (or dicts).
            review_sessions: List of ReviewSession records (or dicts).
        """
        # Assert read-only mode
        BoundaryGuard.assert_read_only()
        
        # Deep copy all data to prevent mutation of source
        self._decisions = copy.deepcopy(decisions) if decisions else []
        self._submissions = copy.deepcopy(submissions) if submissions else []
        self._review_sessions = copy.deepcopy(review_sessions) if review_sessions else []
    
    def get_decisions(
        self,
        target_id: Optional[str] = None,
        reviewer_id: Optional[str] = None,
        decision_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Any]:
        """
        Read decisions with optional filters.
        
        Args:
            target_id: Filter by target ID.
            reviewer_id: Filter by reviewer ID.
            decision_type: Filter by decision type.
            start_date: Filter by start date (inclusive).
            end_date: Filter by end date (inclusive).
            
        Returns:
            List of decisions matching filters (deep copied).
            
        NOTE: This method is READ-ONLY. It returns copies of data.
        """
        result = []
        for decision in self._decisions:
            # Handle both dict and object access
            if isinstance(decision, dict):
                d_target = decision.get("target_id")
                d_reviewer = decision.get("reviewer_id")
                d_type = decision.get("decision_type")
                d_timestamp = decision.get("timestamp")
            else:
                d_target = getattr(decision, "target_id", None)
                d_reviewer = getattr(decision, "reviewer_id", None)
                d_type = getattr(decision, "decision_type", None)
                d_timestamp = getattr(decision, "timestamp", None)
            
            # Apply filters
            if target_id is not None and d_target != target_id:
                continue
            if reviewer_id is not None and d_reviewer != reviewer_id:
                continue
            if decision_type is not None:
                # Handle enum or string
                d_type_str = d_type.value if hasattr(d_type, "value") else d_type
                if d_type_str != decision_type:
                    continue
            if start_date is not None and d_timestamp is not None:
                if isinstance(d_timestamp, str):
                    d_timestamp = datetime.fromisoformat(d_timestamp)
                if d_timestamp < start_date:
                    continue
            if end_date is not None and d_timestamp is not None:
                if isinstance(d_timestamp, str):
                    d_timestamp = datetime.fromisoformat(d_timestamp)
                if d_timestamp > end_date:
                    continue
            
            result.append(copy.deepcopy(decision))
        
        return result
    
    def get_submissions(
        self,
        decision_id: Optional[str] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Any]:
        """
        Read submissions with optional filters.
        
        Args:
            decision_id: Filter by decision ID.
            platform: Filter by platform.
            status: Filter by submission status.
            start_date: Filter by start date (inclusive).
            end_date: Filter by end date (inclusive).
            
        Returns:
            List of submissions matching filters (deep copied).
            
        NOTE: This method is READ-ONLY. It returns copies of data.
        """
        result = []
        for submission in self._submissions:
            # Handle both dict and object access
            if isinstance(submission, dict):
                s_decision = submission.get("decision_id")
                s_platform = submission.get("platform")
                s_status = submission.get("status")
                s_timestamp = submission.get("submitted_at", submission.get("created_at"))
            else:
                s_decision = getattr(submission, "decision_id", None)
                s_platform = getattr(submission, "platform", None)
                s_status = getattr(submission, "status", None)
                s_timestamp = getattr(submission, "submitted_at", getattr(submission, "created_at", None))
            
            # Apply filters
            if decision_id is not None and s_decision != decision_id:
                continue
            if platform is not None:
                s_platform_str = s_platform.value if hasattr(s_platform, "value") else s_platform
                if s_platform_str != platform:
                    continue
            if status is not None:
                s_status_str = s_status.value if hasattr(s_status, "value") else s_status
                if s_status_str != status:
                    continue
            if start_date is not None and s_timestamp is not None:
                if isinstance(s_timestamp, str):
                    s_timestamp = datetime.fromisoformat(s_timestamp)
                if s_timestamp < start_date:
                    continue
            if end_date is not None and s_timestamp is not None:
                if isinstance(s_timestamp, str):
                    s_timestamp = datetime.fromisoformat(s_timestamp)
                if s_timestamp > end_date:
                    continue
            
            result.append(copy.deepcopy(submission))
        
        return result
    
    def get_review_sessions(
        self,
        reviewer_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Any]:
        """
        Read review sessions with optional filters.
        
        Args:
            reviewer_id: Filter by reviewer ID.
            start_date: Filter by start date (inclusive).
            end_date: Filter by end date (inclusive).
            
        Returns:
            List of review sessions matching filters (deep copied).
            
        NOTE: This method is READ-ONLY. It returns copies of data.
        """
        result = []
        for session in self._review_sessions:
            # Handle both dict and object access
            if isinstance(session, dict):
                s_reviewer = session.get("reviewer_id")
                s_start = session.get("start_time")
            else:
                s_reviewer = getattr(session, "reviewer_id", None)
                s_start = getattr(session, "start_time", None)
            
            # Apply filters
            if reviewer_id is not None and s_reviewer != reviewer_id:
                continue
            if start_date is not None and s_start is not None:
                if isinstance(s_start, str):
                    s_start = datetime.fromisoformat(s_start)
                if s_start < start_date:
                    continue
            if end_date is not None and s_start is not None:
                if isinstance(s_start, str):
                    s_start = datetime.fromisoformat(s_start)
                if s_start > end_date:
                    continue
            
            result.append(copy.deepcopy(session))
        
        return result
    
    def get_decision_count(self) -> int:
        """Return total number of decisions."""
        return len(self._decisions)
    
    def get_submission_count(self) -> int:
        """Return total number of submissions."""
        return len(self._submissions)
    
    def get_session_count(self) -> int:
        """Return total number of review sessions."""
        return len(self._review_sessions)
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    # - write_decision()
    # - modify_decision()
    # - delete_decision()
    # - update_decision()
    # - write_submission()
    # - modify_submission()
    # - delete_submission()
    # - update_submission()
    # - write_audit()
    # - modify_audit()
    # - delete_audit()
    # - Any method that modifies source data
    # ========================================================================
