"""
Tests for Phase-6 Correctness Properties.

Validates:
- Property 12: Error Propagation (Requirements 8.1, 8.2, 8.3, 8.4, 8.5)
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from datetime import datetime

from decision_workflow.decisions import DecisionCapture
from decision_workflow.types import (
    ReviewSession,
    DecisionInput,
    DecisionType,
    Severity,
    Role,
    Credentials,
)
from decision_workflow.errors import (
    DecisionWorkflowError,
    AuthenticationError,
    SessionExpiredError,
    InsufficientPermissionError,
    ValidationError,
    AuditLogFailure,
    ArchitecturalViolationError,
)
from decision_workflow.audit import AuditLogger
from decision_workflow.roles import RoleEnforcer
from decision_workflow.session import SessionManager
from decision_workflow.boundaries import BoundaryGuard


# ============================================================================
# Property Tests - Error Propagation
# ============================================================================

class TestErrorPropagationProperty:
    """
    Property 12: Error Propagation
    
    For any error condition (missing field, auth failure, audit failure,
    architectural violation), the system SHALL raise an exception
    (not return None or empty result).
    
    Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5
    """
    
    @given(
        decision_type=st.sampled_from([
            DecisionType.APPROVE,
            DecisionType.REJECT,
            DecisionType.DEFER,
            DecisionType.ESCALATE,
            DecisionType.ADD_NOTE,
        ]),
    )
    @settings(max_examples=100)
    def test_missing_required_field_raises_exception(self, decision_type):
        """
        Property: Missing required field raises ValidationError, not None.
        """
        audit_logger = AuditLogger()
        role_enforcer = RoleEnforcer()
        session = ReviewSession(
            session_id="test-session",
            reviewer_id="reviewer-1",
            role=Role.REVIEWER,
            start_time=datetime.now(),
        )
        capture = DecisionCapture(session, audit_logger, role_enforcer)
        
        # Create decision without required fields
        decision = DecisionInput(decision_type=decision_type)
        
        # Should raise ValidationError for types that require fields
        if decision_type in [
            DecisionType.APPROVE,
            DecisionType.REJECT,
            DecisionType.DEFER,
            DecisionType.ESCALATE,
            DecisionType.ADD_NOTE,
        ]:
            with pytest.raises(ValidationError):
                capture.make_decision("finding-1", decision)
    
    @given(
        action=st.sampled_from([
            DecisionType.APPROVE,
            DecisionType.REJECT,
        ]),
    )
    @settings(max_examples=100)
    def test_permission_failure_raises_exception(self, action):
        """
        Property: Permission failure raises InsufficientPermissionError, not None.
        """
        audit_logger = AuditLogger()
        role_enforcer = RoleEnforcer()
        session = ReviewSession(
            session_id="test-session",
            reviewer_id="operator-1",
            role=Role.OPERATOR,  # Operator cannot approve/reject
            start_time=datetime.now(),
        )
        capture = DecisionCapture(session, audit_logger, role_enforcer)
        
        # Create valid decision that operator cannot make
        if action == DecisionType.APPROVE:
            decision = DecisionInput(
                decision_type=DecisionType.APPROVE,
                severity=Severity.HIGH,
            )
        else:
            decision = DecisionInput(
                decision_type=DecisionType.REJECT,
                rationale="False positive",
            )
        
        with pytest.raises(InsufficientPermissionError):
            capture.make_decision("finding-1", decision)
    
    @given(
        forbidden_method=st.sampled_from([
            "auto_classify",
            "auto_severity",
            "auto_submit",
            "trigger_execution",
            "trigger_scan",
            "make_network_request",
        ]),
    )
    @settings(max_examples=100)
    def test_architectural_violation_raises_exception(self, forbidden_method):
        """
        Property: Architectural violation raises ArchitecturalViolationError, not None.
        """
        guard = BoundaryGuard()
        method = getattr(guard, forbidden_method)
        
        with pytest.raises(ArchitecturalViolationError):
            method()
    
    def test_audit_failure_raises_exception(self):
        """
        Property: Audit failure raises AuditLogFailure, not None.
        """
        def failing_callback(entry):
            raise IOError("Disk full")
        
        audit_logger = AuditLogger(write_callback=failing_callback)
        role_enforcer = RoleEnforcer()
        session = ReviewSession(
            session_id="test-session",
            reviewer_id="reviewer-1",
            role=Role.REVIEWER,
            start_time=datetime.now(),
        )
        
        # First, we need to test that the audit logger raises on write
        from decision_workflow.audit import create_audit_entry
        entry = create_audit_entry(
            session_id=session.session_id,
            reviewer_id=session.reviewer_id,
            role=session.role,
            action="TEST",
        )
        
        with pytest.raises(AuditLogFailure):
            audit_logger.log(entry)
    
    def test_session_expired_raises_exception(self):
        """
        Property: Expired session raises SessionExpiredError, not None.
        """
        from datetime import timedelta
        
        audit_logger = AuditLogger()
        # SECURITY: Must provide valid_users - default is fail-closed (deny all)
        valid_users = {"user-1": Role.REVIEWER}
        session_manager = SessionManager(
            audit_logger=audit_logger,
            session_timeout=timedelta(seconds=0),  # Immediate expiry
            valid_users=valid_users,
        )
        
        credentials = Credentials(user_id="user-1", role=Role.REVIEWER)
        session = session_manager.authenticate(credentials)
        
        # Session should be expired immediately
        with pytest.raises(SessionExpiredError):
            session_manager.require_valid_session(session)


# ============================================================================
# Unit Tests - Error Hierarchy
# ============================================================================

class TestErrorHierarchy:
    """Unit tests for error hierarchy."""
    
    def test_all_errors_inherit_from_base(self):
        """All errors inherit from DecisionWorkflowError."""
        error_classes = [
            AuthenticationError,
            SessionExpiredError,
            InsufficientPermissionError,
            ValidationError,
            AuditLogFailure,
            ArchitecturalViolationError,
        ]
        
        for error_class in error_classes:
            assert issubclass(error_class, DecisionWorkflowError)
    
    def test_insufficient_permission_error_has_role_and_action(self):
        """InsufficientPermissionError has role and action attributes."""
        from decision_workflow.types import Action
        
        error = InsufficientPermissionError(Role.OPERATOR, Action.APPROVE)
        
        assert error.role == Role.OPERATOR
        assert error.action == Action.APPROVE
        assert "operator" in str(error).lower()
        assert "approve" in str(error).lower()
    
    def test_validation_error_has_field(self):
        """ValidationError has field attribute."""
        error = ValidationError("severity", "Severity is required")
        
        assert error.field == "severity"
        assert "severity" in str(error).lower()
    
    def test_architectural_violation_error_has_action(self):
        """ArchitecturalViolationError has action attribute."""
        error = ArchitecturalViolationError("auto_classify")
        
        assert error.action == "auto_classify"
        assert "auto_classify" in str(error)
    
    def test_audit_log_failure_has_original_error(self):
        """AuditLogFailure has original_error attribute."""
        original = IOError("Disk full")
        error = AuditLogFailure(original_error=original)
        
        assert error.original_error == original
        assert "Disk full" in str(error) or "Audit log write failed" in str(error)


# ============================================================================
# Unit Tests - Error Messages
# ============================================================================

class TestErrorMessages:
    """Unit tests for error messages."""
    
    def test_insufficient_permission_error_message(self):
        """InsufficientPermissionError has descriptive message."""
        from decision_workflow.types import Action
        
        error = InsufficientPermissionError(Role.OPERATOR, Action.APPROVE)
        
        assert "operator" in str(error).lower()
        assert "approve" in str(error).lower()
    
    def test_validation_error_message(self):
        """ValidationError has descriptive message."""
        error = ValidationError("severity", "Severity is required for APPROVE")
        
        assert "severity" in str(error).lower()
        assert "required" in str(error).lower()
    
    def test_architectural_violation_error_message(self):
        """ArchitecturalViolationError has descriptive message."""
        error = ArchitecturalViolationError("auto_classify")
        
        assert "auto_classify" in str(error)
        assert "forbidden" in str(error).lower()
    
    def test_audit_log_failure_message(self):
        """AuditLogFailure has descriptive message."""
        original = IOError("Disk full")
        error = AuditLogFailure(original_error=original, message="Disk full")
        
        assert "AUDIT_EMERGENCY" in str(error)
