"""
Tests for Phase-6 Session Management.

Feature: human-decision-workflow
Property 5: Session Lifecycle Tracking
Property 6: Decision-Session Association
Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from datetime import datetime, timedelta

from decision_workflow.types import Credentials, ReviewSession, Role
from decision_workflow.session import SessionManager
from decision_workflow.audit import AuditLogger
from decision_workflow.errors import AuthenticationError, SessionExpiredError


# ============================================================================
# Unit Tests
# ============================================================================

class TestSessionManagerBasic:
    """Basic unit tests for SessionManager."""
    
    def test_authenticate_creates_session(self):
        """authenticate should create a new session."""
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {"user1": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id="user1", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        
        assert session.reviewer_id == "user1"
        assert session.role == Role.OPERATOR
        assert session.session_id is not None
        assert session.start_time is not None
    
    def test_authenticate_logs_session_start(self):
        """authenticate should log SESSION_START."""
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {"user1": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id="user1", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        
        entries = audit_logger.get_entries_for_session(session.session_id)
        assert len(entries) == 1
        assert entries[0].action == "SESSION_START"
    
    def test_authenticate_with_valid_users(self):
        """authenticate should validate against valid_users."""
        audit_logger = AuditLogger()
        valid_users = {"user1": Role.OPERATOR, "user2": Role.REVIEWER}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        # Valid user
        credentials = Credentials(user_id="user1", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        assert session.reviewer_id == "user1"
        
        # Invalid user
        credentials = Credentials(user_id="unknown", role=Role.OPERATOR)
        with pytest.raises(AuthenticationError):
            manager.authenticate(credentials)
        
        # Role mismatch
        credentials = Credentials(user_id="user1", role=Role.REVIEWER)
        with pytest.raises(AuthenticationError):
            manager.authenticate(credentials)
    
    def test_validate_session_valid(self):
        """validate_session should return True for valid session."""
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {"user1": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id="user1", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        
        assert manager.validate_session(session) is True
    
    def test_validate_session_ended(self):
        """validate_session should return False for ended session."""
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {"user1": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id="user1", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        manager.end_session(session)
        
        assert manager.validate_session(session) is False
    
    def test_validate_session_expired(self):
        """validate_session should return False for expired session."""
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {"user1": Role.OPERATOR}
        manager = SessionManager(audit_logger, session_timeout=timedelta(seconds=0), valid_users=valid_users)
        
        credentials = Credentials(user_id="user1", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        
        # Session should be expired immediately
        assert manager.validate_session(session) is False
    
    def test_require_valid_session_raises(self):
        """require_valid_session should raise for invalid session."""
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {"user1": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id="user1", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        manager.end_session(session)
        
        with pytest.raises(SessionExpiredError) as exc_info:
            manager.require_valid_session(session)
        
        assert exc_info.value.session_id == session.session_id
    
    def test_end_session_logs_session_end(self):
        """end_session should log SESSION_END."""
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {"user1": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id="user1", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        manager.end_session(session)
        
        entries = audit_logger.get_entries_for_session(session.session_id)
        assert len(entries) == 2
        assert entries[0].action == "SESSION_START"
        assert entries[1].action == "SESSION_END"
    
    def test_is_session_ended(self):
        """is_session_ended should check audit log."""
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {"user1": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id="user1", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        
        assert manager.is_session_ended(session) is False
        
        manager.end_session(session)
        
        assert manager.is_session_ended(session) is True


# ============================================================================
# Property Tests
# ============================================================================

class TestSessionLifecycleTracking:
    """
    Feature: human-decision-workflow, Property 5: Session Lifecycle Tracking
    
    For any ReviewSession, it SHALL have session_id, reviewer_id, and start_time
    populated at creation. For any ended ReviewSession, it SHALL have end_time
    and decisions_made_count populated (derived from audit log).
    
    Validates: Requirements 5.2, 5.3
    """
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
        role=st.sampled_from(Role),
    )
    @settings(max_examples=100)
    def test_session_has_required_fields_at_creation(self, user_id: str, role: Role):
        """
        Property 5: Session Lifecycle Tracking - Creation
        Session should have session_id, reviewer_id, and start_time at creation.
        """
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        # For property tests, dynamically create valid_users for the generated user
        valid_users = {user_id: role}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id=user_id, role=role)
        session = manager.authenticate(credentials)
        
        assert session.session_id is not None
        assert len(session.session_id) > 0
        assert session.reviewer_id == user_id
        assert session.start_time is not None
        assert isinstance(session.start_time, datetime)
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
        role=st.sampled_from(Role),
    )
    @settings(max_examples=100)
    def test_session_end_recorded_in_audit(self, user_id: str, role: Role):
        """
        Property 5: Session Lifecycle Tracking - End
        Session end should be recorded in audit log.
        """
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {user_id: role}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id=user_id, role=role)
        session = manager.authenticate(credentials)
        manager.end_session(session)
        
        # Check audit log has SESSION_END
        entries = audit_logger.get_entries_for_session(session.session_id)
        end_entries = [e for e in entries if e.action == "SESSION_END"]
        assert len(end_entries) == 1
        assert end_entries[0].timestamp is not None


class TestDecisionSessionAssociation:
    """
    Feature: human-decision-workflow, Property 6: Decision-Session Association
    
    For any HumanDecision, it SHALL reference a valid, non-expired ReviewSession
    via session_id.
    
    Validates: Requirements 5.4, 5.5
    """
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
        role=st.sampled_from(Role),
    )
    @settings(max_examples=100)
    def test_expired_session_rejected(self, user_id: str, role: Role):
        """
        Property 6: Decision-Session Association - Expired
        Operations on expired sessions should be rejected.
        """
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {user_id: role}
        manager = SessionManager(audit_logger, session_timeout=timedelta(seconds=0), valid_users=valid_users)
        
        credentials = Credentials(user_id=user_id, role=role)
        session = manager.authenticate(credentials)
        
        # Session should be expired
        with pytest.raises(SessionExpiredError):
            manager.require_valid_session(session)
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
        role=st.sampled_from(Role),
    )
    @settings(max_examples=100)
    def test_ended_session_rejected(self, user_id: str, role: Role):
        """
        Property 6: Decision-Session Association - Ended
        Operations on ended sessions should be rejected.
        """
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {user_id: role}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id=user_id, role=role)
        session = manager.authenticate(credentials)
        manager.end_session(session)
        
        # Session should be ended
        with pytest.raises(SessionExpiredError):
            manager.require_valid_session(session)
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
        role=st.sampled_from(Role),
    )
    @settings(max_examples=100)
    def test_valid_session_accepted(self, user_id: str, role: Role):
        """
        Property 6: Decision-Session Association - Valid
        Operations on valid sessions should be accepted.
        """
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {user_id: role}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id=user_id, role=role)
        session = manager.authenticate(credentials)
        
        # Should not raise
        manager.require_valid_session(session)
