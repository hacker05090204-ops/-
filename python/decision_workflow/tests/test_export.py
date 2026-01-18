"""
Tests for Phase-6 Decision Export.

Validates:
- Property 10: Report Completeness (Requirements 7.1, 7.2, 7.3, 7.4)
"""

import pytest
import json
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
    DecisionReport,
)
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
def reviewer_capture(reviewer_session, audit_logger, role_enforcer):
    """Create a decision capture for a reviewer."""
    return DecisionCapture(reviewer_session, audit_logger, role_enforcer)


# ============================================================================
# Unit Tests - Report Generation
# ============================================================================

class TestReportGeneration:
    """Unit tests for report generation."""
    
    def test_empty_report(self, reviewer_capture):
        """Empty session generates empty report."""
        report = reviewer_capture.export_report()
        
        assert report.total_decisions == 0
        assert len(report.decisions) == 0
    
    def test_report_contains_session_info(self, reviewer_capture, reviewer_session):
        """Report contains session information."""
        report = reviewer_capture.export_report()
        
        assert report.session_id == reviewer_session.session_id
        assert report.reviewer_id == reviewer_session.reviewer_id
        assert report.role == reviewer_session.role
    
    def test_report_contains_all_decisions(self, reviewer_capture):
        """Report contains all decisions made in session."""
        decisions = [
            DecisionInput(decision_type=DecisionType.APPROVE, severity=Severity.HIGH),
            DecisionInput(decision_type=DecisionType.REJECT, rationale="False positive"),
            DecisionInput(decision_type=DecisionType.DEFER, defer_reason="Need info"),
        ]
        
        for i, decision in enumerate(decisions):
            reviewer_capture.make_decision(f"finding-{i}", decision)
        
        report = reviewer_capture.export_report()
        
        assert report.total_decisions == 3
        assert len(report.decisions) == 3
    
    def test_report_has_generated_timestamp(self, reviewer_capture):
        """Report has generated_at timestamp."""
        report = reviewer_capture.export_report()
        
        assert report.generated_at is not None
        assert isinstance(report.generated_at, datetime)
    
    def test_report_has_unique_id(self, reviewer_capture):
        """Each report has a unique ID."""
        report1 = reviewer_capture.export_report()
        report2 = reviewer_capture.export_report()
        
        assert report1.report_id != report2.report_id


# ============================================================================
# Unit Tests - JSON Serialization
# ============================================================================

class TestReportSerialization:
    """Unit tests for report JSON serialization."""
    
    def test_report_to_dict(self, reviewer_capture):
        """Report can be converted to dictionary."""
        reviewer_capture.make_decision(
            "finding-1",
            DecisionInput(decision_type=DecisionType.APPROVE, severity=Severity.HIGH),
        )
        
        report = reviewer_capture.export_report()
        report_dict = report.to_dict()
        
        assert isinstance(report_dict, dict)
        assert "report_id" in report_dict
        assert "session_id" in report_dict
        assert "reviewer_id" in report_dict
        assert "role" in report_dict
        assert "generated_at" in report_dict
        assert "decisions" in report_dict
        assert "total_decisions" in report_dict
    
    def test_report_to_json(self, reviewer_capture):
        """Report can be serialized to JSON."""
        reviewer_capture.make_decision(
            "finding-1",
            DecisionInput(decision_type=DecisionType.APPROVE, severity=Severity.HIGH),
        )
        
        report = reviewer_capture.export_report()
        report_dict = report.to_dict()
        
        # Should not raise
        json_str = json.dumps(report_dict)
        
        assert isinstance(json_str, str)
        assert len(json_str) > 0
    
    def test_report_json_roundtrip(self, reviewer_capture):
        """Report can be serialized and deserialized."""
        reviewer_capture.make_decision(
            "finding-1",
            DecisionInput(
                decision_type=DecisionType.APPROVE,
                severity=Severity.HIGH,
                cvss_score=7.5,
            ),
        )
        
        report = reviewer_capture.export_report()
        report_dict = report.to_dict()
        
        json_str = json.dumps(report_dict)
        parsed = json.loads(json_str)
        
        assert parsed["session_id"] == report.session_id
        assert parsed["reviewer_id"] == report.reviewer_id
        assert parsed["total_decisions"] == 1
        assert len(parsed["decisions"]) == 1
    
    def test_report_decisions_contain_all_fields(self, reviewer_capture):
        """Report decisions contain all required fields."""
        reviewer_capture.make_decision(
            "finding-1",
            DecisionInput(
                decision_type=DecisionType.APPROVE,
                severity=Severity.HIGH,
                cvss_score=7.5,
                rationale="Confirmed vulnerability",
            ),
        )
        
        report = reviewer_capture.export_report()
        report_dict = report.to_dict()
        
        decision = report_dict["decisions"][0]
        
        assert "decision_id" in decision
        assert "finding_id" in decision
        assert "session_id" in decision
        assert "reviewer_id" in decision
        assert "role" in decision
        assert "decision_type" in decision
        assert "timestamp" in decision
        assert "severity" in decision
        assert "cvss_score" in decision


# ============================================================================
# Property Tests - Report Completeness
# ============================================================================

class TestReportCompletenessProperty:
    """
    Property 10: Report Completeness
    
    For any DecisionReport generated, it SHALL contain all HumanDecision records
    from the session, and SHALL be JSON-serializable (json.dumps succeeds).
    
    Validates: Requirements 7.1, 7.2, 7.3, 7.4
    """
    
    @given(
        num_decisions=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=100)
    def test_report_contains_all_decisions(self, num_decisions):
        """
        Property: Report contains all decisions from session.
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
        
        # Make decisions
        for i in range(num_decisions):
            decision = DecisionInput(
                decision_type=DecisionType.APPROVE,
                severity=Severity.HIGH,
            )
            capture.make_decision(f"finding-{i}", decision)
        
        # Generate report
        report = capture.export_report()
        
        # Verify completeness
        assert report.total_decisions == num_decisions
        assert len(report.decisions) == num_decisions
    
    @given(
        severity=st.sampled_from(Severity),
        cvss_score=st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        ),
        rationale=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    )
    @settings(max_examples=100)
    def test_report_is_json_serializable(self, severity, cvss_score, rationale):
        """
        Property: Report is always JSON-serializable.
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
        
        # Make a decision
        decision = DecisionInput(
            decision_type=DecisionType.APPROVE,
            severity=severity,
            cvss_score=cvss_score,
            rationale=rationale,
        )
        capture.make_decision("finding-1", decision)
        
        # Generate report
        report = capture.export_report()
        report_dict = report.to_dict()
        
        # Should not raise
        json_str = json.dumps(report_dict)
        
        assert isinstance(json_str, str)
        assert len(json_str) > 0
    
    @given(
        reviewer_id=st.text(min_size=1, max_size=50),
        session_id=st.uuids().map(str),
    )
    @settings(max_examples=100)
    def test_report_contains_reviewer_identity(self, reviewer_id, session_id):
        """
        Property: Report contains reviewer identity.
        """
        audit_logger = AuditLogger()
        role_enforcer = RoleEnforcer()
        session = ReviewSession(
            session_id=session_id,
            reviewer_id=reviewer_id,
            role=Role.REVIEWER,
            start_time=datetime.now(),
        )
        capture = DecisionCapture(session, audit_logger, role_enforcer)
        
        # Generate report
        report = capture.export_report()
        
        # Verify identity
        assert report.reviewer_id == reviewer_id
        assert report.session_id == session_id
        assert report.role == Role.REVIEWER
