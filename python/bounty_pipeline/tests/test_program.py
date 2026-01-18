"""
Tests for Program Manager.

**Feature: bounty-pipeline**

Property tests validate:
- Property 14: Program Isolation
  (findings isolated by program, program-specific policies)
- Property 15: Cross-Program Handling
  (require human decision for cross-program findings)
"""

import pytest
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings

from bounty_pipeline.program import (
    ProgramManager,
    ProgramPolicy,
    ProgramContext,
    CrossProgramFinding,
)
from bounty_pipeline.types import (
    AuthorizationDocument,
    ValidatedFinding,
    MCPFinding,
    MCPClassification,
    ProofChain,
    SourceLinks,
)
from bounty_pipeline.errors import (
    HumanApprovalRequired,
    ScopeViolationError,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def make_proof_chain() -> ProofChain:
    """Create a valid proof chain for testing."""
    return ProofChain(
        before_state={"key": "value"},
        action_sequence=[{"action": "test"}],
        after_state={"key": "changed"},
        causality_chain=[{"cause": "effect"}],
        replay_instructions=[{"step": 1}],
        invariant_violated="test_invariant",
        proof_hash="abc123",
    )


def make_mcp_finding(severity: str = "high") -> MCPFinding:
    """Create a valid MCP finding for testing."""
    return MCPFinding(
        finding_id=f"finding-{datetime.now(timezone.utc).timestamp()}",
        classification=MCPClassification.BUG,
        invariant_violated="test_invariant",
        proof=make_proof_chain(),
        severity=severity,
        cyfer_brain_observation_id="obs-001",
        timestamp=datetime.now(timezone.utc),
    )


def make_validated_finding(severity: str = "high") -> ValidatedFinding:
    """Create a validated finding for testing."""
    mcp_finding = make_mcp_finding(severity)
    return ValidatedFinding(
        finding_id=mcp_finding.finding_id,
        mcp_finding=mcp_finding,
        proof_chain=mcp_finding.proof,
        source_links=SourceLinks(
            mcp_proof_id=mcp_finding.finding_id,
            mcp_proof_hash=mcp_finding.proof.proof_hash,
            cyfer_brain_observation_id=mcp_finding.cyfer_brain_observation_id,
        ),
    )


def make_authorization(
    program_name: str,
    valid_days: int = 30,
) -> AuthorizationDocument:
    """Create an authorization document for testing."""
    now = datetime.now(timezone.utc)
    return AuthorizationDocument(
        program_name=program_name,
        authorized_domains=(f"{program_name}.example.com",),
        authorized_ip_ranges=("10.0.0.0/8",),
        excluded_paths=("/admin",),
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=valid_days),
        document_hash=f"hash-{program_name}",
    )


def make_expired_authorization(program_name: str) -> AuthorizationDocument:
    """Create an expired authorization document."""
    now = datetime.now(timezone.utc)
    return AuthorizationDocument(
        program_name=program_name,
        authorized_domains=(f"{program_name}.example.com",),
        authorized_ip_ranges=(),
        excluded_paths=(),
        valid_from=now - timedelta(days=60),
        valid_until=now - timedelta(days=30),
        document_hash=f"hash-{program_name}",
    )


# =============================================================================
# Property 14: Program Isolation Tests
# =============================================================================


class TestProgramIsolation:
    """
    **Property 14: Program Isolation**
    **Validates: Requirements 10.1, 10.2, 10.4**

    For any multi-program configuration, findings SHALL be
    isolated by program and program-specific policies SHALL
    be applied.
    """

    def test_findings_are_isolated_by_program(self):
        """Findings are isolated to their assigned program."""
        manager = ProgramManager()

        auth1 = make_authorization("program-a")
        auth2 = make_authorization("program-b")

        manager.register_program(auth1)
        manager.register_program(auth2)

        finding1 = make_validated_finding()
        finding2 = make_validated_finding()

        manager.add_finding_to_program(finding1, "program-a")
        manager.add_finding_to_program(finding2, "program-b")

        findings_a = manager.get_findings_for_program("program-a")
        findings_b = manager.get_findings_for_program("program-b")

        assert len(findings_a) == 1
        assert len(findings_b) == 1
        assert findings_a[0].finding_id == finding1.finding_id
        assert findings_b[0].finding_id == finding2.finding_id

    @given(
        program_count=st.integers(min_value=1, max_value=5),
        findings_per_program=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=20, deadline=5000)
    def test_multiple_programs_isolated(
        self,
        program_count: int,
        findings_per_program: int,
    ):
        """Multiple programs maintain isolation."""
        manager = ProgramManager()

        # Register programs
        for i in range(program_count):
            auth = make_authorization(f"program-{i}")
            manager.register_program(auth)

        # Add findings to each program
        for i in range(program_count):
            for _ in range(findings_per_program):
                finding = make_validated_finding()
                manager.add_finding_to_program(finding, f"program-{i}")

        # Verify isolation
        for i in range(program_count):
            findings = manager.get_findings_for_program(f"program-{i}")
            assert len(findings) == findings_per_program

    def test_program_specific_policy_applied(self):
        """Program-specific policies are applied."""
        manager = ProgramManager()

        auth = make_authorization("strict-program")
        policy = ProgramPolicy(
            program_name="strict-program",
            min_severity="high",  # Only high and critical
            auto_duplicate_check=True,
            require_poc=True,
            max_submissions_per_day=5,
        )

        manager.register_program(auth, policy)

        # Low severity finding should fail policy
        low_finding = make_validated_finding(severity="low")
        result = manager.apply_policy(low_finding, "strict-program")

        assert not result["passes_policy"]
        assert any("below minimum" in issue for issue in result["issues"])

        # High severity finding should pass
        high_finding = make_validated_finding(severity="high")
        result = manager.apply_policy(high_finding, "strict-program")

        assert result["passes_policy"]

    def test_rate_limiting_per_program(self):
        """Rate limiting is applied per program."""
        manager = ProgramManager()

        auth = make_authorization("rate-limited")
        policy = ProgramPolicy(
            program_name="rate-limited",
            min_severity="low",
            auto_duplicate_check=True,
            require_poc=True,
            max_submissions_per_day=2,
        )

        manager.register_program(auth, policy)

        # First two submissions should be allowed
        manager.record_submission("rate-limited")
        manager.record_submission("rate-limited")

        context = manager.get_program("rate-limited")
        assert not context.can_submit_today

        # Policy check should fail
        finding = make_validated_finding()
        result = manager.apply_policy(finding, "rate-limited")

        assert not result["passes_policy"]
        assert any("limit" in issue.lower() for issue in result["issues"])

    def test_expired_authorization_blocks_findings(self):
        """Expired authorization blocks adding findings."""
        manager = ProgramManager()

        auth = make_expired_authorization("expired-program")
        manager.register_program(auth)

        finding = make_validated_finding()

        with pytest.raises(ScopeViolationError, match="expired"):
            manager.add_finding_to_program(finding, "expired-program")


# =============================================================================
# Property 15: Cross-Program Handling Tests
# =============================================================================


class TestCrossProgramHandling:
    """
    **Property 15: Cross-Program Handling**
    **Validates: Requirements 10.3**

    For any finding that spans multiple programs, the system
    SHALL require human decision on which program to submit to.
    """

    def test_cross_program_detection(self):
        """Cross-program findings are detected."""
        manager = ProgramManager()

        auth1 = make_authorization("program-a")
        auth2 = make_authorization("program-b")

        manager.register_program(auth1)
        manager.register_program(auth2)

        finding = make_validated_finding()
        cross = manager.check_cross_program(finding)

        # Both programs are active, so finding matches both
        assert cross is not None
        assert len(cross.matching_programs) == 2
        assert cross.requires_human_decision

    def test_cross_program_requires_human_decision(self):
        """Cross-program assignment requires human decision."""
        manager = ProgramManager()

        auth1 = make_authorization("program-a")
        auth2 = make_authorization("program-b")

        manager.register_program(auth1)
        manager.register_program(auth2)

        finding = make_validated_finding()

        # Assignment without reason should fail
        with pytest.raises(HumanApprovalRequired, match="human decision"):
            manager.assign_cross_program_finding(
                finding=finding,
                selected_program="program-a",
                decision_reason="",  # Empty reason
                decider_id="human-001",
            )

    def test_cross_program_assignment_with_reason(self):
        """Cross-program assignment succeeds with reason."""
        manager = ProgramManager()

        auth1 = make_authorization("program-a")
        auth2 = make_authorization("program-b")

        manager.register_program(auth1)
        manager.register_program(auth2)

        finding = make_validated_finding()

        # Assignment with reason should succeed
        manager.assign_cross_program_finding(
            finding=finding,
            selected_program="program-a",
            decision_reason="Primary target is in program-a scope",
            decider_id="human-001",
        )

        findings_a = manager.get_findings_for_program("program-a")
        assert len(findings_a) == 1

    def test_single_program_no_cross_detection(self):
        """Single program doesn't trigger cross-program detection."""
        manager = ProgramManager()

        auth = make_authorization("only-program")
        manager.register_program(auth)

        finding = make_validated_finding()
        cross = manager.check_cross_program(finding)

        # Only one program, so no cross-program issue
        assert cross is None


# =============================================================================
# Program Management Tests
# =============================================================================


class TestProgramManagement:
    """Tests for program management functionality."""

    def test_register_program(self):
        """Programs can be registered."""
        manager = ProgramManager()

        auth = make_authorization("test-program")
        context = manager.register_program(auth)

        assert context.program_name == "test-program"
        assert context.authorization == auth
        assert manager.program_count == 1

    def test_register_with_custom_policy(self):
        """Programs can be registered with custom policy."""
        manager = ProgramManager()

        auth = make_authorization("custom-program")
        policy = ProgramPolicy(
            program_name="custom-program",
            min_severity="critical",
            auto_duplicate_check=False,
            require_poc=False,
            max_submissions_per_day=1,
        )

        context = manager.register_program(auth, policy)

        assert context.policy.min_severity == "critical"
        assert context.policy.max_submissions_per_day == 1

    def test_get_program_stats(self):
        """Program statistics are accurate."""
        manager = ProgramManager()

        auth = make_authorization("stats-program")
        manager.register_program(auth)

        finding = make_validated_finding()
        manager.add_finding_to_program(finding, "stats-program")
        manager.record_submission("stats-program")

        stats = manager.get_program_stats("stats-program")

        assert stats["program_name"] == "stats-program"
        assert stats["total_findings"] == 1
        assert stats["submissions_today"] == 1
        assert stats["authorization_active"]

    def test_unknown_program_raises(self):
        """Operations on unknown programs raise ValueError."""
        manager = ProgramManager()

        with pytest.raises(ValueError, match="not found"):
            manager.get_findings_for_program("nonexistent")

        with pytest.raises(ValueError, match="not found"):
            manager.add_finding_to_program(make_validated_finding(), "nonexistent")

        with pytest.raises(ValueError, match="not found"):
            manager.apply_policy(make_validated_finding(), "nonexistent")


# =============================================================================
# Policy Tests
# =============================================================================


class TestProgramPolicy:
    """Tests for program policy functionality."""

    def test_default_policy(self):
        """Default policy has sensible defaults."""
        policy = ProgramPolicy.default("test-program")

        assert policy.program_name == "test-program"
        assert policy.min_severity == "low"
        assert policy.auto_duplicate_check
        assert policy.require_poc
        assert policy.max_submissions_per_day == 10

    def test_severity_ordering(self):
        """Severity ordering is correct in policy checks."""
        manager = ProgramManager()

        auth = make_authorization("severity-test")
        policy = ProgramPolicy(
            program_name="severity-test",
            min_severity="medium",
            auto_duplicate_check=True,
            require_poc=True,
            max_submissions_per_day=10,
        )

        manager.register_program(auth, policy)

        # Test each severity level
        severities = ["informational", "low", "medium", "high", "critical"]
        expected_pass = [False, False, True, True, True]

        for severity, should_pass in zip(severities, expected_pass):
            finding = make_validated_finding(severity=severity)
            result = manager.apply_policy(finding, "severity-test")
            assert result["passes_policy"] == should_pass, \
                f"Severity {severity} should {'pass' if should_pass else 'fail'}"
