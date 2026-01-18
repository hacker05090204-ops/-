"""
Tests for Phase-6 Decision Capture.

Validates:
- Property 2: Decision Type Validation (Requirements 2.2, 2.3, 2.4, 2.5, 3.1, 3.6)
- Property 9: Permission Denial Audit (Requirements 9.8)
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
    Action,
    ROLE_PERMISSIONS,
)
from decision_workflow.errors import ValidationError, InsufficientPermissionError
from decision_workflow.audit import AuditLogger
from decision_workflow.roles import RoleEnforcer


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def audit_logger():
    """Create a fresh audit logger."""
    return AuditLogger()


@pytest.fixture
def role_enforcer():
    """Create a role enforcer."""
    return RoleEnforcer()


@pytest.fixture
def reviewer_session():
    """Create a reviewer session."""
    return ReviewSession(
        session_id="test-session-1",
        reviewer_id="reviewer-1",
        role=Role.REVIEWER,
        start_time=datetime.now(),
    )


@pytest.fixture
def operator_session():
    """Create an operator session."""
    return ReviewSession(
        session_id="test-session-2",
        reviewer_id="operator-1",
        role=Role.OPERATOR,
        start_time=datetime.now(),
    )


@pytest.fixture
def reviewer_capture(reviewer_session, audit_logger, role_enforcer):
    """Create a decision capture for a reviewer."""
    return DecisionCapture(reviewer_session, audit_logger, role_enforcer)


@pytest.fixture
def operator_capture(operator_session, audit_logger, role_enforcer):
    """Create a decision capture for an operator."""
    return DecisionCapture(operator_session, audit_logger, role_enforcer)


# ============================================================================
# Unit Tests - Decision Validation
# ============================================================================

class TestDecisionValidation:
    """Unit tests for decision validation."""
    
    def test_approve_requires_severity(self, reviewer_capture):
        """APPROVE without severity raises ValidationError."""
        decision = DecisionInput(decision_type=DecisionType.APPROVE)
        
        with pytest.raises(ValidationError) as exc_info:
            reviewer_capture.make_decision("finding-1", decision)
        
        assert exc_info.value.field == "severity"
    
    def test_approve_with_severity_succeeds(self, reviewer_capture):
        """APPROVE with severity succeeds."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.HIGH,
        )
        
        result = reviewer_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.APPROVE
        assert result.severity == Severity.HIGH
    
    def test_reject_requires_rationale(self, reviewer_capture):
        """REJECT without rationale raises ValidationError."""
        decision = DecisionInput(decision_type=DecisionType.REJECT)
        
        with pytest.raises(ValidationError) as exc_info:
            reviewer_capture.make_decision("finding-1", decision)
        
        assert exc_info.value.field == "rationale"
    
    def test_reject_with_rationale_succeeds(self, reviewer_capture):
        """REJECT with rationale succeeds."""
        decision = DecisionInput(
            decision_type=DecisionType.REJECT,
            rationale="False positive - not exploitable",
        )
        
        result = reviewer_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.REJECT
        assert result.rationale == "False positive - not exploitable"
    
    def test_defer_requires_reason(self, reviewer_capture):
        """DEFER without defer_reason raises ValidationError."""
        decision = DecisionInput(decision_type=DecisionType.DEFER)
        
        with pytest.raises(ValidationError) as exc_info:
            reviewer_capture.make_decision("finding-1", decision)
        
        assert exc_info.value.field == "defer_reason"
    
    def test_defer_with_reason_succeeds(self, reviewer_capture):
        """DEFER with defer_reason succeeds."""
        decision = DecisionInput(
            decision_type=DecisionType.DEFER,
            defer_reason="Need more information",
        )
        
        result = reviewer_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.DEFER
        assert result.defer_reason == "Need more information"
    
    def test_escalate_requires_target(self, reviewer_capture):
        """ESCALATE without escalation_target raises ValidationError."""
        decision = DecisionInput(decision_type=DecisionType.ESCALATE)
        
        with pytest.raises(ValidationError) as exc_info:
            reviewer_capture.make_decision("finding-1", decision)
        
        assert exc_info.value.field == "escalation_target"
    
    def test_escalate_with_target_succeeds(self, reviewer_capture):
        """ESCALATE with escalation_target succeeds."""
        decision = DecisionInput(
            decision_type=DecisionType.ESCALATE,
            escalation_target="security-lead",
        )
        
        result = reviewer_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.ESCALATE
        assert result.escalation_target == "security-lead"
    
    def test_add_note_requires_note(self, reviewer_capture):
        """ADD_NOTE without note raises ValidationError."""
        decision = DecisionInput(decision_type=DecisionType.ADD_NOTE)
        
        with pytest.raises(ValidationError) as exc_info:
            reviewer_capture.make_decision("finding-1", decision)
        
        assert exc_info.value.field == "note"
    
    def test_add_note_with_note_succeeds(self, reviewer_capture):
        """ADD_NOTE with note succeeds."""
        decision = DecisionInput(
            decision_type=DecisionType.ADD_NOTE,
            note="Investigated endpoint, appears legitimate",
        )
        
        result = reviewer_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.ADD_NOTE
        assert result.note == "Investigated endpoint, appears legitimate"
    
    def test_mark_reviewed_succeeds(self, reviewer_capture):
        """MARK_REVIEWED succeeds without additional fields."""
        decision = DecisionInput(decision_type=DecisionType.MARK_REVIEWED)
        
        result = reviewer_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.MARK_REVIEWED
    
    def test_cvss_score_invalid_low(self, reviewer_capture):
        """CVSS score below 0.0 raises ValidationError."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.HIGH,
            cvss_score=-0.1,
        )
        
        with pytest.raises(ValidationError) as exc_info:
            reviewer_capture.make_decision("finding-1", decision)
        
        assert exc_info.value.field == "cvss_score"
    
    def test_cvss_score_invalid_high(self, reviewer_capture):
        """CVSS score above 10.0 raises ValidationError."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.HIGH,
            cvss_score=10.1,
        )
        
        with pytest.raises(ValidationError) as exc_info:
            reviewer_capture.make_decision("finding-1", decision)
        
        assert exc_info.value.field == "cvss_score"
    
    def test_cvss_score_valid_boundary_zero(self, reviewer_capture):
        """CVSS score of 0.0 is valid."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.INFORMATIONAL,
            cvss_score=0.0,
        )
        
        result = reviewer_capture.make_decision("finding-1", decision)
        
        assert result.cvss_score == 0.0
    
    def test_cvss_score_valid_boundary_ten(self, reviewer_capture):
        """CVSS score of 10.0 is valid."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.CRITICAL,
            cvss_score=10.0,
        )
        
        result = reviewer_capture.make_decision("finding-1", decision)
        
        assert result.cvss_score == 10.0


# ============================================================================
# Unit Tests - Role Enforcement
# ============================================================================

class TestDecisionRoleEnforcement:
    """Unit tests for role enforcement in decision capture."""
    
    def test_operator_cannot_approve(self, operator_capture):
        """Operator cannot make APPROVE decisions."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.HIGH,
        )
        
        with pytest.raises(InsufficientPermissionError) as exc_info:
            operator_capture.make_decision("finding-1", decision)
        
        assert exc_info.value.role == Role.OPERATOR
        assert exc_info.value.action == Action.APPROVE
    
    def test_operator_cannot_reject(self, operator_capture):
        """Operator cannot make REJECT decisions."""
        decision = DecisionInput(
            decision_type=DecisionType.REJECT,
            rationale="False positive",
        )
        
        with pytest.raises(InsufficientPermissionError) as exc_info:
            operator_capture.make_decision("finding-1", decision)
        
        assert exc_info.value.role == Role.OPERATOR
        assert exc_info.value.action == Action.REJECT
    
    def test_operator_can_defer(self, operator_capture):
        """Operator can make DEFER decisions."""
        decision = DecisionInput(
            decision_type=DecisionType.DEFER,
            defer_reason="Need more info",
        )
        
        result = operator_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.DEFER
    
    def test_operator_can_escalate(self, operator_capture):
        """Operator can make ESCALATE decisions."""
        decision = DecisionInput(
            decision_type=DecisionType.ESCALATE,
            escalation_target="security-lead",
        )
        
        result = operator_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.ESCALATE
    
    def test_operator_can_add_note(self, operator_capture):
        """Operator can make ADD_NOTE decisions."""
        decision = DecisionInput(
            decision_type=DecisionType.ADD_NOTE,
            note="Investigated this",
        )
        
        result = operator_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.ADD_NOTE
    
    def test_operator_can_mark_reviewed(self, operator_capture):
        """Operator can make MARK_REVIEWED decisions."""
        decision = DecisionInput(decision_type=DecisionType.MARK_REVIEWED)
        
        result = operator_capture.make_decision("finding-1", decision)
        
        assert result.decision_type == DecisionType.MARK_REVIEWED


# ============================================================================
# Unit Tests - Audit Logging
# ============================================================================

class TestDecisionAuditLogging:
    """Unit tests for audit logging of decisions."""
    
    def test_decision_creates_audit_entry(self, reviewer_capture, audit_logger):
        """Making a decision creates an audit entry."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.HIGH,
        )
        
        reviewer_capture.make_decision("finding-1", decision)
        
        chain = audit_logger.get_chain()
        assert len(chain) == 1
        assert chain[0].action == "DECISION"
        assert chain[0].finding_id == "finding-1"
        assert chain[0].decision_type == DecisionType.APPROVE
        assert chain[0].severity == Severity.HIGH
    
    def test_multiple_decisions_create_chain(self, reviewer_capture, audit_logger):
        """Multiple decisions create a hash chain."""
        decisions = [
            DecisionInput(decision_type=DecisionType.APPROVE, severity=Severity.HIGH),
            DecisionInput(decision_type=DecisionType.REJECT, rationale="False positive"),
            DecisionInput(decision_type=DecisionType.DEFER, defer_reason="Need info"),
        ]
        
        for i, decision in enumerate(decisions):
            reviewer_capture.make_decision(f"finding-{i}", decision)
        
        chain = audit_logger.get_chain()
        assert len(chain) == 3
        
        # Verify hash chain
        for i in range(1, len(chain)):
            assert chain[i].previous_hash == chain[i - 1].entry_hash


# ============================================================================
# Property Tests - Decision Type Validation
# ============================================================================

class TestDecisionTypeValidationProperty:
    """
    Property 2: Decision Type Validation
    
    For any decision of type APPROVE, the decision SHALL have a non-None severity.
    For any decision of type REJECT, the decision SHALL have a non-empty rationale.
    For any decision of type DEFER, the decision SHALL have a non-empty defer_reason.
    For any decision of type ESCALATE, the decision SHALL have a non-empty escalation_target.
    
    Validates: Requirements 2.2, 2.3, 2.4, 2.5, 3.1, 3.6
    """
    
    @given(severity=st.sampled_from(Severity))
    @settings(max_examples=100)
    def test_approve_always_has_severity(self, severity):
        """
        Property: APPROVE decisions always have severity.
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
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=severity,
        )
        
        result = capture.make_decision("finding-1", decision)
        
        assert result.severity is not None
        assert result.severity == severity
    
    @given(rationale=st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_reject_always_has_rationale(self, rationale):
        """
        Property: REJECT decisions always have rationale.
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
        decision = DecisionInput(
            decision_type=DecisionType.REJECT,
            rationale=rationale,
        )
        
        result = capture.make_decision("finding-1", decision)
        
        assert result.rationale is not None
        assert len(result.rationale) > 0
    
    @given(defer_reason=st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_defer_always_has_reason(self, defer_reason):
        """
        Property: DEFER decisions always have defer_reason.
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
        decision = DecisionInput(
            decision_type=DecisionType.DEFER,
            defer_reason=defer_reason,
        )
        
        result = capture.make_decision("finding-1", decision)
        
        assert result.defer_reason is not None
        assert len(result.defer_reason) > 0
    
    @given(escalation_target=st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_escalate_always_has_target(self, escalation_target):
        """
        Property: ESCALATE decisions always have escalation_target.
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
        decision = DecisionInput(
            decision_type=DecisionType.ESCALATE,
            escalation_target=escalation_target,
        )
        
        result = capture.make_decision("finding-1", decision)
        
        assert result.escalation_target is not None
        assert len(result.escalation_target) > 0
    
    @given(
        cvss_score=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_cvss_score_in_valid_range(self, cvss_score):
        """
        Property: CVSS scores are always in [0.0, 10.0] range.
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
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.HIGH,
            cvss_score=cvss_score,
        )
        
        result = capture.make_decision("finding-1", decision)
        
        assert result.cvss_score is not None
        assert 0.0 <= result.cvss_score <= 10.0


# ============================================================================
# Property Tests - Permission Denial Audit
# ============================================================================

class TestPermissionDenialAuditProperty:
    """
    Property 9: Permission Denial Audit
    
    For any InsufficientPermissionError raised, an AuditEntry SHALL be created
    with the user identity, role, attempted action, and timestamp.
    
    Validates: Requirements 9.8
    """
    
    @given(
        finding_id=st.uuids().map(str),
    )
    @settings(max_examples=100)
    def test_operator_approve_denial_logged(self, finding_id):
        """
        Property: Operator APPROVE denial is logged.
        """
        audit_logger = AuditLogger()
        role_enforcer = RoleEnforcer()
        session = ReviewSession(
            session_id="test-session",
            reviewer_id="operator-1",
            role=Role.OPERATOR,
            start_time=datetime.now(),
        )
        capture = DecisionCapture(session, audit_logger, role_enforcer)
        
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.HIGH,
        )
        
        with pytest.raises(InsufficientPermissionError):
            capture.make_decision(finding_id, decision)
        
        # Verify denial was logged
        chain = audit_logger.get_chain()
        assert len(chain) == 1
        
        entry = chain[0]
        assert entry.action == "PERMISSION_DENIED"
        assert entry.reviewer_id == "operator-1"
        assert entry.role == Role.OPERATOR
        assert entry.error_type == "InsufficientPermissionError"
        assert "approve" in entry.error_message.lower()
    
    @given(
        finding_id=st.uuids().map(str),
    )
    @settings(max_examples=100)
    def test_operator_reject_denial_logged(self, finding_id):
        """
        Property: Operator REJECT denial is logged.
        """
        audit_logger = AuditLogger()
        role_enforcer = RoleEnforcer()
        session = ReviewSession(
            session_id="test-session",
            reviewer_id="operator-1",
            role=Role.OPERATOR,
            start_time=datetime.now(),
        )
        capture = DecisionCapture(session, audit_logger, role_enforcer)
        
        decision = DecisionInput(
            decision_type=DecisionType.REJECT,
            rationale="False positive",
        )
        
        with pytest.raises(InsufficientPermissionError):
            capture.make_decision(finding_id, decision)
        
        # Verify denial was logged
        chain = audit_logger.get_chain()
        assert len(chain) == 1
        
        entry = chain[0]
        assert entry.action == "PERMISSION_DENIED"
        assert entry.role == Role.OPERATOR
        assert "reject" in entry.error_message.lower()
