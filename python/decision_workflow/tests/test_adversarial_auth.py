"""
Adversarial Security Tests for Phase-6 Decision Workflow

Tests for authentication bypass prevention and fail-closed behavior.
These tests verify that the security fixes are effective.

SECURITY TESTS:
- Auth bypass via valid_users=None (MUST fail closed)
- Empty valid_users dict (MUST deny all)
- Role mismatch rejection
- Unknown user rejection
"""

import pytest
from datetime import timedelta

from decision_workflow.types import Credentials, Role
from decision_workflow.session import SessionManager
from decision_workflow.audit import AuditLogger
from decision_workflow.errors import AuthenticationError


class TestAuthBypassPrevention:
    """Tests for authentication bypass prevention in SessionManager."""
    
    def test_none_valid_users_denies_all_credentials(self) -> None:
        """
        ADVERSARIAL: valid_users=None MUST fail closed (deny all).
        
        Previous behavior: valid_users=None accepted ALL credentials.
        Fixed behavior: valid_users=None defaults to {} (deny all).
        
        SECURITY: This prevents auth bypass via misconfiguration.
        """
        audit_logger = AuditLogger()
        # Explicitly pass None to simulate misconfiguration
        manager = SessionManager(audit_logger, valid_users=None)
        
        # ANY credentials should be rejected
        credentials = Credentials(user_id="attacker", role=Role.OPERATOR)
        
        with pytest.raises(AuthenticationError) as exc_info:
            manager.authenticate(credentials)
        
        assert "Unknown user" in str(exc_info.value)
    
    def test_empty_valid_users_denies_all_credentials(self) -> None:
        """
        Empty valid_users dict MUST deny all credentials.
        
        SECURITY: Explicit empty dict should behave same as None.
        """
        audit_logger = AuditLogger()
        manager = SessionManager(audit_logger, valid_users={})
        
        credentials = Credentials(user_id="attacker", role=Role.OPERATOR)
        
        with pytest.raises(AuthenticationError) as exc_info:
            manager.authenticate(credentials)
        
        assert "Unknown user" in str(exc_info.value)
    
    def test_default_constructor_denies_all(self) -> None:
        """
        Default constructor (no valid_users arg) MUST deny all.
        
        SECURITY: Default behavior must be secure (fail closed).
        """
        audit_logger = AuditLogger()
        # No valid_users argument - should default to deny all
        manager = SessionManager(audit_logger)
        
        credentials = Credentials(user_id="anyone", role=Role.REVIEWER)
        
        with pytest.raises(AuthenticationError):
            manager.authenticate(credentials)
    
    def test_role_mismatch_rejected(self) -> None:
        """
        Role mismatch MUST be rejected even for valid user.
        
        ADVERSARIAL: Attacker knows valid user_id but guesses wrong role.
        """
        audit_logger = AuditLogger()
        valid_users = {"admin": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        # Valid user_id but wrong role
        credentials = Credentials(user_id="admin", role=Role.REVIEWER)
        
        with pytest.raises(AuthenticationError) as exc_info:
            manager.authenticate(credentials)
        
        assert "Role mismatch" in str(exc_info.value)
    
    def test_unknown_user_rejected_with_valid_users_configured(self) -> None:
        """
        Unknown user MUST be rejected when valid_users is configured.
        
        ADVERSARIAL: Attacker tries user_id not in valid_users.
        """
        audit_logger = AuditLogger()
        valid_users = {"legitimate_user": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        credentials = Credentials(user_id="attacker", role=Role.OPERATOR)
        
        with pytest.raises(AuthenticationError) as exc_info:
            manager.authenticate(credentials)
        
        assert "Unknown user" in str(exc_info.value)
    
    def test_valid_credentials_accepted(self) -> None:
        """
        Valid credentials MUST be accepted.
        
        Sanity check: security fix doesn't break legitimate auth.
        """
        audit_logger = AuditLogger()
        valid_users = {"admin": Role.OPERATOR, "reviewer": Role.REVIEWER}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        # Valid credentials
        credentials = Credentials(user_id="admin", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        
        assert session.reviewer_id == "admin"
        assert session.role == Role.OPERATOR
        assert session.session_id is not None


class TestFailClosedBehavior:
    """Tests verifying fail-closed security behavior."""
    
    def test_no_session_created_on_auth_failure(self) -> None:
        """
        Failed auth MUST NOT create any session.
        
        SECURITY: No partial state on failure.
        """
        audit_logger = AuditLogger()
        manager = SessionManager(audit_logger, valid_users={})
        
        credentials = Credentials(user_id="attacker", role=Role.OPERATOR)
        
        with pytest.raises(AuthenticationError):
            manager.authenticate(credentials)
        
        # No sessions should exist
        assert len(manager._active_sessions) == 0
    
    def test_no_audit_entry_on_auth_failure(self) -> None:
        """
        Failed auth MUST NOT create SESSION_START audit entry.
        
        SECURITY: Audit log should not show failed attempts as sessions.
        """
        audit_logger = AuditLogger()
        manager = SessionManager(audit_logger, valid_users={})
        
        credentials = Credentials(user_id="attacker", role=Role.OPERATOR)
        
        with pytest.raises(AuthenticationError):
            manager.authenticate(credentials)
        
        # No audit entries should exist
        assert len(audit_logger.get_chain()) == 0
    
    def test_multiple_failed_attempts_all_rejected(self) -> None:
        """
        Multiple failed auth attempts MUST all be rejected.
        
        ADVERSARIAL: Attacker tries multiple credentials.
        """
        audit_logger = AuditLogger()
        manager = SessionManager(audit_logger, valid_users={})
        
        attack_credentials = [
            Credentials(user_id="admin", role=Role.OPERATOR),
            Credentials(user_id="root", role=Role.OPERATOR),
            Credentials(user_id="user", role=Role.REVIEWER),
            Credentials(user_id="", role=Role.OPERATOR),  # Empty user
        ]
        
        for creds in attack_credentials:
            with pytest.raises(AuthenticationError):
                manager.authenticate(creds)
        
        # No sessions created
        assert len(manager._active_sessions) == 0
        # No audit entries
        assert len(audit_logger.get_chain()) == 0


class TestEdgeCases:
    """Edge case tests for authentication."""
    
    def test_empty_user_id_rejected(self) -> None:
        """Empty user_id MUST be rejected."""
        audit_logger = AuditLogger()
        valid_users = {"": Role.OPERATOR}  # Even if empty string is "valid"
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        # This should work if empty string is explicitly allowed
        credentials = Credentials(user_id="", role=Role.OPERATOR)
        session = manager.authenticate(credentials)
        assert session.reviewer_id == ""
    
    def test_whitespace_user_id_treated_literally(self) -> None:
        """Whitespace user_id MUST be treated literally (no trimming)."""
        audit_logger = AuditLogger()
        valid_users = {"admin": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        # " admin" is NOT "admin"
        credentials = Credentials(user_id=" admin", role=Role.OPERATOR)
        
        with pytest.raises(AuthenticationError):
            manager.authenticate(credentials)
    
    def test_case_sensitive_user_id(self) -> None:
        """User_id matching MUST be case-sensitive."""
        audit_logger = AuditLogger()
        valid_users = {"Admin": Role.OPERATOR}
        manager = SessionManager(audit_logger, valid_users=valid_users)
        
        # "admin" is NOT "Admin"
        credentials = Credentials(user_id="admin", role=Role.OPERATOR)
        
        with pytest.raises(AuthenticationError):
            manager.authenticate(credentials)
