"""
Tests for Phase-6 data types.

Validates:
- Role enum completeness (Requirements 9.1)
- Severity enum completeness (Requirements 3.2)
- Data model immutability (Requirements 1.5, 1.6)
- CVSS score range (Requirements 3.3)
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from dataclasses import FrozenInstanceError
from datetime import datetime
import json

from decision_workflow.types import (
    Role,
    DecisionType,
    Severity,
    Action,
    ROLE_PERMISSIONS,
    Credentials,
    ReviewSession,
    DecisionInput,
    HumanDecision,
    AuditEntry,
    QueueItem,
    DecisionReport,
)


# ============================================================================
# Role Enum Tests
# ============================================================================

class TestRoleEnum:
    """
    Feature: human-decision-workflow, Property: Role enum completeness
    Validates: Requirements 9.1
    """
    
    def test_role_enum_contains_operator(self):
        """Role enum must contain OPERATOR."""
        assert Role.OPERATOR in Role
        assert Role.OPERATOR.value == "operator"
    
    def test_role_enum_contains_reviewer(self):
        """Role enum must contain REVIEWER."""
        assert Role.REVIEWER in Role
        assert Role.REVIEWER.value == "reviewer"
    
    def test_role_enum_has_exactly_two_values(self):
        """Role enum must contain exactly OPERATOR and REVIEWER."""
        assert len(Role) == 2
        assert set(Role) == {Role.OPERATOR, Role.REVIEWER}
    
    def test_role_permissions_defined_for_all_roles(self):
        """ROLE_PERMISSIONS must be defined for all roles."""
        for role in Role:
            assert role in ROLE_PERMISSIONS
            assert isinstance(ROLE_PERMISSIONS[role], set)


# ============================================================================
# Severity Enum Tests
# ============================================================================

class TestSeverityEnum:
    """
    Validates: Requirements 3.2
    """
    
    def test_severity_enum_contains_all_levels(self):
        """Severity enum must contain all required levels."""
        expected = {"critical", "high", "medium", "low", "informational"}
        actual = {s.value for s in Severity}
        assert actual == expected
    
    def test_severity_enum_has_exactly_five_values(self):
        """Severity enum must have exactly 5 values."""
        assert len(Severity) == 5


# ============================================================================
# DecisionType Enum Tests
# ============================================================================

class TestDecisionTypeEnum:
    """
    Validates: Requirements 2.1
    """
    
    def test_decision_type_contains_all_types(self):
        """DecisionType enum must contain all required types."""
        expected = {"approve", "reject", "defer", "escalate", "mark_reviewed", "add_note"}
        actual = {d.value for d in DecisionType}
        assert actual == expected


# ============================================================================
# Action Enum Tests
# ============================================================================

class TestActionEnum:
    """
    Validates: Requirements 9.2, 9.3, 9.4
    """
    
    def test_action_enum_contains_all_actions(self):
        """Action enum must contain all required actions."""
        expected = {
            "view_findings", "mark_reviewed", "add_note", "defer",
            "escalate", "assign_severity", "approve", "reject"
        }
        actual = {a.value for a in Action}
        assert actual == expected
    
    def test_operator_permissions_subset_of_reviewer(self):
        """Operator permissions must be a subset of Reviewer permissions."""
        operator_perms = ROLE_PERMISSIONS[Role.OPERATOR]
        reviewer_perms = ROLE_PERMISSIONS[Role.REVIEWER]
        assert operator_perms.issubset(reviewer_perms)
    
    def test_operator_cannot_approve_reject_severity(self):
        """Operator must not have approve, reject, or assign_severity permissions."""
        operator_perms = ROLE_PERMISSIONS[Role.OPERATOR]
        forbidden = {Action.APPROVE, Action.REJECT, Action.ASSIGN_SEVERITY}
        assert operator_perms.isdisjoint(forbidden)
    
    def test_reviewer_can_approve_reject_severity(self):
        """Reviewer must have approve, reject, and assign_severity permissions."""
        reviewer_perms = ROLE_PERMISSIONS[Role.REVIEWER]
        required = {Action.APPROVE, Action.REJECT, Action.ASSIGN_SEVERITY}
        assert required.issubset(reviewer_perms)


# ============================================================================
# Immutability Tests
# ============================================================================

class TestImmutability:
    """
    Feature: human-decision-workflow, Property 1: Input Data Immutability
    Validates: Requirements 1.5, 1.6
    """
    
    def test_credentials_is_frozen(self):
        """Credentials must be immutable."""
        creds = Credentials(user_id="test", role=Role.OPERATOR)
        with pytest.raises(FrozenInstanceError):
            creds.user_id = "modified"
    
    def test_review_session_is_frozen(self):
        """ReviewSession must be immutable."""
        session = ReviewSession(
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            start_time=datetime.now(),
        )
        with pytest.raises(FrozenInstanceError):
            session.session_id = "modified"
    
    def test_decision_input_is_frozen(self):
        """DecisionInput must be immutable."""
        decision = DecisionInput(decision_type=DecisionType.APPROVE, severity=Severity.HIGH)
        with pytest.raises(FrozenInstanceError):
            decision.severity = Severity.LOW
    
    def test_human_decision_is_frozen(self):
        """HumanDecision must be immutable."""
        decision = HumanDecision(
            decision_id="d1",
            finding_id="f1",
            session_id="s1",
            reviewer_id="r1",
            role=Role.REVIEWER,
            decision_type=DecisionType.APPROVE,
            timestamp=datetime.now(),
            severity=Severity.HIGH,
        )
        with pytest.raises(FrozenInstanceError):
            decision.severity = Severity.LOW
    
    def test_audit_entry_is_frozen(self):
        """AuditEntry must be immutable."""
        entry = AuditEntry(
            entry_id="e1",
            timestamp=datetime.now(),
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="test",
        )
        with pytest.raises(FrozenInstanceError):
            entry.action = "modified"
    
    def test_queue_item_is_frozen(self):
        """QueueItem must be immutable."""
        item = QueueItem(
            finding_id="f1",
            endpoint="/api/test",
            signals=(),
        )
        with pytest.raises(FrozenInstanceError):
            item.endpoint = "modified"
    
    def test_decision_report_is_frozen(self):
        """DecisionReport must be immutable."""
        report = DecisionReport(
            report_id="r1",
            session_id="s1",
            reviewer_id="r1",
            role=Role.REVIEWER,
            generated_at=datetime.now(),
            decisions=(),
        )
        with pytest.raises(FrozenInstanceError):
            report.session_id = "modified"


# ============================================================================
# CVSS Score Tests
# ============================================================================

class TestCVSSScore:
    """
    Feature: human-decision-workflow, Property 11: CVSS Score Range
    Validates: Requirements 3.3
    """
    
    @given(cvss_score=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_valid_cvss_scores_accepted(self, cvss_score: float):
        """
        Property 11: CVSS Score Range
        For any CVSS score in [0.0, 10.0], it should be accepted.
        """
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.HIGH,
            cvss_score=cvss_score,
        )
        assert decision.cvss_score == cvss_score
        assert 0.0 <= decision.cvss_score <= 10.0
    
    def test_cvss_score_boundary_zero(self):
        """CVSS score of 0.0 should be valid."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.INFORMATIONAL,
            cvss_score=0.0,
        )
        assert decision.cvss_score == 0.0
    
    def test_cvss_score_boundary_ten(self):
        """CVSS score of 10.0 should be valid."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.CRITICAL,
            cvss_score=10.0,
        )
        assert decision.cvss_score == 10.0
    
    def test_cvss_score_optional(self):
        """CVSS score should be optional."""
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=Severity.HIGH,
        )
        assert decision.cvss_score is None


# ============================================================================
# Serialization Tests
# ============================================================================

class TestSerialization:
    """
    Validates: Requirements 7.4
    """
    
    def test_human_decision_to_dict(self):
        """HumanDecision.to_dict() should return serializable dict."""
        decision = HumanDecision(
            decision_id="d1",
            finding_id="f1",
            session_id="s1",
            reviewer_id="r1",
            role=Role.REVIEWER,
            decision_type=DecisionType.APPROVE,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            severity=Severity.HIGH,
            cvss_score=7.5,
        )
        d = decision.to_dict()
        assert d["decision_id"] == "d1"
        assert d["severity"] == "high"
        assert d["cvss_score"] == 7.5
        # Should be JSON serializable
        json_str = json.dumps(d)
        assert "d1" in json_str
    
    def test_audit_entry_to_dict(self):
        """AuditEntry.to_dict() should return serializable dict."""
        entry = AuditEntry(
            entry_id="e1",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="DECISION",
            decision_type=DecisionType.DEFER,
        )
        d = entry.to_dict()
        assert d["entry_id"] == "e1"
        assert d["decision_type"] == "defer"
        # Should be JSON serializable
        json_str = json.dumps(d)
        assert "e1" in json_str
    
    def test_queue_item_to_dict(self):
        """QueueItem.to_dict() should return serializable dict."""
        item = QueueItem(
            finding_id="f1",
            endpoint="/api/test",
            signals=({"type": "error", "message": "test"},),
            mcp_classification="XSS",
            mcp_confidence=0.85,
        )
        d = item.to_dict()
        assert d["finding_id"] == "f1"
        assert d["mcp_classification"] == "XSS"
        # Should be JSON serializable
        json_str = json.dumps(d)
        assert "f1" in json_str
    
    def test_decision_report_to_dict(self):
        """DecisionReport.to_dict() should return serializable dict."""
        decision = HumanDecision(
            decision_id="d1",
            finding_id="f1",
            session_id="s1",
            reviewer_id="r1",
            role=Role.REVIEWER,
            decision_type=DecisionType.APPROVE,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            severity=Severity.HIGH,
        )
        report = DecisionReport(
            report_id="rep1",
            session_id="s1",
            reviewer_id="r1",
            role=Role.REVIEWER,
            generated_at=datetime(2025, 1, 1, 13, 0, 0),
            decisions=(decision,),
        )
        d = report.to_dict()
        assert d["report_id"] == "rep1"
        assert d["total_decisions"] == 1
        assert len(d["decisions"]) == 1
        # Should be JSON serializable
        json_str = json.dumps(d)
        assert "rep1" in json_str
    
    def test_decision_report_to_json(self):
        """DecisionReport.to_json() should return valid JSON string."""
        report = DecisionReport(
            report_id="rep1",
            session_id="s1",
            reviewer_id="r1",
            role=Role.REVIEWER,
            generated_at=datetime(2025, 1, 1, 13, 0, 0),
            decisions=(),
        )
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["report_id"] == "rep1"


# ============================================================================
# Audit Entry Hash Tests
# ============================================================================

class TestAuditEntryHash:
    """
    Validates: Requirements 4.5
    """
    
    def test_compute_hash_returns_sha256(self):
        """compute_hash() should return a SHA-256 hash (64 hex chars)."""
        entry = AuditEntry(
            entry_id="e1",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="TEST",
        )
        hash_value = entry.compute_hash()
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)
    
    def test_compute_hash_deterministic(self):
        """compute_hash() should be deterministic."""
        entry = AuditEntry(
            entry_id="e1",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="TEST",
        )
        hash1 = entry.compute_hash()
        hash2 = entry.compute_hash()
        assert hash1 == hash2
    
    def test_compute_hash_different_for_different_entries(self):
        """Different entries should have different hashes."""
        entry1 = AuditEntry(
            entry_id="e1",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="TEST",
        )
        entry2 = AuditEntry(
            entry_id="e2",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="TEST",
        )
        assert entry1.compute_hash() != entry2.compute_hash()
