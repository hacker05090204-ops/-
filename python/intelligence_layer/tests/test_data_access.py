"""
Tests for Phase-8 Data Access Layer

Verifies that:
- Data access is read-only
- Source data is not modified
- Filters work correctly
- No write methods exist
"""

import pytest
import copy
from datetime import datetime, timedelta

from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.tests.conftest import (
    create_sample_decision,
    create_sample_submission,
    create_sample_session,
)


class TestDataAccessLayerReadOnly:
    """Tests for read-only data access."""
    
    def test_get_decisions_does_not_modify_source(self):
        """Verify get_decisions does not modify source data."""
        original_decisions = [
            create_sample_decision(decision_id="dec-001"),
            create_sample_decision(decision_id="dec-002"),
        ]
        original_copy = copy.deepcopy(original_decisions)
        
        data_access = DataAccessLayer(decisions=original_decisions)
        _ = data_access.get_decisions()
        
        # Source data should be unchanged
        assert original_decisions == original_copy
    
    def test_get_submissions_does_not_modify_source(self):
        """Verify get_submissions does not modify source data."""
        original_submissions = [
            create_sample_submission(submission_id="sub-001"),
            create_sample_submission(submission_id="sub-002"),
        ]
        original_copy = copy.deepcopy(original_submissions)
        
        data_access = DataAccessLayer(submissions=original_submissions)
        _ = data_access.get_submissions()
        
        # Source data should be unchanged
        assert original_submissions == original_copy
    
    def test_get_review_sessions_does_not_modify_source(self):
        """Verify get_review_sessions does not modify source data."""
        original_sessions = [
            create_sample_session(session_id="sess-001"),
            create_sample_session(session_id="sess-002"),
        ]
        original_copy = copy.deepcopy(original_sessions)
        
        data_access = DataAccessLayer(review_sessions=original_sessions)
        _ = data_access.get_review_sessions()
        
        # Source data should be unchanged
        assert original_sessions == original_copy
    
    def test_returned_data_is_copy(self):
        """Verify returned data is a copy, not a reference."""
        decisions = [create_sample_decision(decision_id="dec-001")]
        data_access = DataAccessLayer(decisions=decisions)
        
        result = data_access.get_decisions()
        
        # Modify returned data
        result[0]["decision_id"] = "modified"
        
        # Original should be unchanged
        assert decisions[0]["decision_id"] == "dec-001"
        
        # Get again should return original
        result2 = data_access.get_decisions()
        assert result2[0]["decision_id"] == "dec-001"


class TestDataAccessLayerFilters:
    """Tests for data access filters."""
    
    def test_filter_decisions_by_target_id(self):
        """Verify filtering decisions by target_id."""
        decisions = [
            create_sample_decision(decision_id="dec-001", target_id="target-001"),
            create_sample_decision(decision_id="dec-002", target_id="target-002"),
            create_sample_decision(decision_id="dec-003", target_id="target-001"),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        
        result = data_access.get_decisions(target_id="target-001")
        
        assert len(result) == 2
        assert all(d["target_id"] == "target-001" for d in result)
    
    def test_filter_decisions_by_reviewer_id(self):
        """Verify filtering decisions by reviewer_id."""
        decisions = [
            create_sample_decision(decision_id="dec-001", reviewer_id="rev-001"),
            create_sample_decision(decision_id="dec-002", reviewer_id="rev-002"),
            create_sample_decision(decision_id="dec-003", reviewer_id="rev-001"),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        
        result = data_access.get_decisions(reviewer_id="rev-001")
        
        assert len(result) == 2
        assert all(d["reviewer_id"] == "rev-001" for d in result)
    
    def test_filter_decisions_by_decision_type(self):
        """Verify filtering decisions by decision_type."""
        decisions = [
            create_sample_decision(decision_id="dec-001", decision_type="approve"),
            create_sample_decision(decision_id="dec-002", decision_type="reject"),
            create_sample_decision(decision_id="dec-003", decision_type="approve"),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        
        result = data_access.get_decisions(decision_type="approve")
        
        assert len(result) == 2
        assert all(d["decision_type"] == "approve" for d in result)
    
    def test_filter_decisions_by_date_range(self):
        """Verify filtering decisions by date range."""
        base_time = datetime(2025, 1, 15)
        decisions = [
            create_sample_decision(decision_id="dec-001", timestamp=datetime(2025, 1, 10)),
            create_sample_decision(decision_id="dec-002", timestamp=datetime(2025, 1, 15)),
            create_sample_decision(decision_id="dec-003", timestamp=datetime(2025, 1, 20)),
        ]
        data_access = DataAccessLayer(decisions=decisions)
        
        result = data_access.get_decisions(
            start_date=datetime(2025, 1, 14),
            end_date=datetime(2025, 1, 16),
        )
        
        assert len(result) == 1
        assert result[0]["decision_id"] == "dec-002"
    
    def test_filter_submissions_by_platform(self):
        """Verify filtering submissions by platform."""
        submissions = [
            create_sample_submission(submission_id="sub-001", platform="hackerone"),
            create_sample_submission(submission_id="sub-002", platform="bugcrowd"),
            create_sample_submission(submission_id="sub-003", platform="hackerone"),
        ]
        data_access = DataAccessLayer(submissions=submissions)
        
        result = data_access.get_submissions(platform="hackerone")
        
        assert len(result) == 2
        assert all(s["platform"] == "hackerone" for s in result)
    
    def test_filter_submissions_by_status(self):
        """Verify filtering submissions by status."""
        submissions = [
            create_sample_submission(submission_id="sub-001", status="acknowledged"),
            create_sample_submission(submission_id="sub-002", status="rejected"),
            create_sample_submission(submission_id="sub-003", status="acknowledged"),
        ]
        data_access = DataAccessLayer(submissions=submissions)
        
        result = data_access.get_submissions(status="acknowledged")
        
        assert len(result) == 2
        assert all(s["status"] == "acknowledged" for s in result)
    
    def test_filter_sessions_by_reviewer_id(self):
        """Verify filtering sessions by reviewer_id."""
        sessions = [
            create_sample_session(session_id="sess-001", reviewer_id="rev-001"),
            create_sample_session(session_id="sess-002", reviewer_id="rev-002"),
            create_sample_session(session_id="sess-003", reviewer_id="rev-001"),
        ]
        data_access = DataAccessLayer(review_sessions=sessions)
        
        result = data_access.get_review_sessions(reviewer_id="rev-001")
        
        assert len(result) == 2
        assert all(s["reviewer_id"] == "rev-001" for s in result)


class TestDataAccessLayerEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_data_returns_empty_list(self):
        """Verify empty data returns empty list."""
        data_access = DataAccessLayer()
        
        assert data_access.get_decisions() == []
        assert data_access.get_submissions() == []
        assert data_access.get_review_sessions() == []
    
    def test_no_matching_filter_returns_empty_list(self):
        """Verify no matching filter returns empty list."""
        decisions = [create_sample_decision(target_id="target-001")]
        data_access = DataAccessLayer(decisions=decisions)
        
        result = data_access.get_decisions(target_id="nonexistent")
        
        assert result == []
    
    def test_count_methods(self):
        """Verify count methods return correct counts."""
        decisions = [create_sample_decision() for _ in range(5)]
        submissions = [create_sample_submission() for _ in range(3)]
        sessions = [create_sample_session() for _ in range(2)]
        
        data_access = DataAccessLayer(
            decisions=decisions,
            submissions=submissions,
            review_sessions=sessions,
        )
        
        assert data_access.get_decision_count() == 5
        assert data_access.get_submission_count() == 3
        assert data_access.get_session_count() == 2


class TestDataAccessLayerNoWriteMethods:
    """Tests to verify no write methods exist."""
    
    def test_no_write_decision_method(self):
        """Verify write_decision method does not exist."""
        data_access = DataAccessLayer()
        assert not hasattr(data_access, "write_decision")
    
    def test_no_modify_decision_method(self):
        """Verify modify_decision method does not exist."""
        data_access = DataAccessLayer()
        assert not hasattr(data_access, "modify_decision")
    
    def test_no_delete_decision_method(self):
        """Verify delete_decision method does not exist."""
        data_access = DataAccessLayer()
        assert not hasattr(data_access, "delete_decision")
    
    def test_no_write_submission_method(self):
        """Verify write_submission method does not exist."""
        data_access = DataAccessLayer()
        assert not hasattr(data_access, "write_submission")
    
    def test_no_modify_submission_method(self):
        """Verify modify_submission method does not exist."""
        data_access = DataAccessLayer()
        assert not hasattr(data_access, "modify_submission")
    
    def test_no_delete_submission_method(self):
        """Verify delete_submission method does not exist."""
        data_access = DataAccessLayer()
        assert not hasattr(data_access, "delete_submission")
    
    def test_no_write_audit_method(self):
        """Verify write_audit method does not exist."""
        data_access = DataAccessLayer()
        assert not hasattr(data_access, "write_audit")
    
    def test_no_modify_audit_method(self):
        """Verify modify_audit method does not exist."""
        data_access = DataAccessLayer()
        assert not hasattr(data_access, "modify_audit")
