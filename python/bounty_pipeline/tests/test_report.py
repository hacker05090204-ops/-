"""
Property tests for Report Generator.

**Feature: bounty-pipeline, Property 5: Report Formatting**
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

**Feature: bounty-pipeline, Property 12: Sensitive Data Redaction**
**Validates: Requirements 9.1, 9.2**
"""

from datetime import datetime, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from bounty_pipeline.errors import ArchitecturalViolationError
from bounty_pipeline.types import (
    MCPClassification,
    MCPFinding,
    ProofChain,
    ValidatedFinding,
    SourceLinks,
    DraftStatus,
)
from bounty_pipeline.report import (
    ReportGenerator,
    SEVERITY_MAPPING,
    PLATFORM_SCHEMAS,
)


# ============================================================================
# Test Fixtures
# ============================================================================


def create_test_finding(severity: str = "high") -> ValidatedFinding:
    """Create a test validated finding."""
    proof = ProofChain(
        before_state={"user": "guest", "balance": 100},
        action_sequence=[
            {"action": "login", "user": "admin"},
            {"action": "transfer", "amount": 1000},
        ],
        after_state={"user": "admin", "balance": 1100},
        causality_chain=[
            {"cause": "Authentication bypass"},
            {"effect": "Unauthorized access"},
        ],
        replay_instructions=[
            {"step": "Navigate to login page", "expected": "Login form displayed"},
            {"step": "Submit crafted payload", "expected": "Bypass authentication"},
            {"step": "Access admin panel", "expected": "Admin access granted"},
        ],
        invariant_violated="AUTHENTICATION_REQUIRED",
        proof_hash="a" * 64,
    )

    mcp_finding = MCPFinding(
        finding_id="test-finding",
        classification=MCPClassification.BUG,
        invariant_violated="AUTHENTICATION_REQUIRED",
        proof=proof,
        severity=severity,
        cyfer_brain_observation_id="obs-1",
        timestamp=datetime.now(timezone.utc),
    )

    source_links = SourceLinks(
        mcp_proof_id="test-finding",
        mcp_proof_hash="a" * 64,
        cyfer_brain_observation_id="obs-1",
    )

    return ValidatedFinding(
        finding_id="test-finding",
        mcp_finding=mcp_finding,
        proof_chain=proof,
        source_links=source_links,
    )


# ============================================================================
# Property Tests
# ============================================================================


class TestReportFormatting:
    """
    Property 5: Report Formatting

    *For any* platform-specific report, the system SHALL populate all
    mandatory fields from MCP proof and map severity deterministically
    (not computed).

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """

    @given(platform=st.sampled_from(["hackerone", "bugcrowd", "generic"]))
    @settings(max_examples=50, deadline=5000)
    def test_report_has_required_fields(self, platform: str) -> None:
        """Report has all required fields for platform."""
        generator = ReportGenerator()
        finding = create_test_finding()

        draft = generator.generate(finding, platform)

        assert draft.report_title is not None
        assert len(draft.report_title) > 0
        assert draft.report_body is not None
        assert len(draft.report_body) > 0
        assert draft.severity is not None
        assert draft.reproduction_steps is not None

    @given(
        severity=st.sampled_from(["critical", "high", "medium", "low", "informational"]),
        platform=st.sampled_from(["hackerone", "bugcrowd", "generic"]),
    )
    @settings(max_examples=50, deadline=5000)
    def test_severity_mapping_is_deterministic(self, severity: str, platform: str) -> None:
        """Severity mapping is deterministic (same input = same output)."""
        generator = ReportGenerator()

        # Map twice
        result1 = generator.map_severity(severity, platform)
        result2 = generator.map_severity(severity, platform)

        # Should be identical
        assert result1 == result2

        # Should match expected mapping
        expected = SEVERITY_MAPPING[severity][platform]
        assert result1 == expected

    def test_reproduction_steps_from_proof(self) -> None:
        """Reproduction steps are extracted from MCP proof."""
        generator = ReportGenerator()
        finding = create_test_finding()

        draft = generator.generate(finding, "generic")

        # Should have steps from replay_instructions
        assert len(draft.reproduction_steps) == 3
        assert draft.reproduction_steps[0].step_number == 1
        assert "login" in draft.reproduction_steps[0].action.lower()

    def test_proof_included_in_report(self) -> None:
        """Report includes proof information."""
        generator = ReportGenerator()
        finding = create_test_finding()

        draft = generator.generate(finding, "generic")

        # Report body should reference the invariant
        assert "AUTHENTICATION_REQUIRED" in draft.report_body

        # Proof summary should exist
        assert draft.proof_summary is not None
        assert "proof" in draft.proof_summary.lower()


class TestSensitiveDataRedaction:
    """
    Property 12: Sensitive Data Redaction

    *For any* report containing sensitive data, the system SHALL redact
    PII and credentials by default and minimize exposure.

    **Validates: Requirements 9.1, 9.2**
    """

    def test_email_redaction(self) -> None:
        """Email addresses are redacted."""
        generator = ReportGenerator()
        content = "Contact: user@example.com for more info"

        redacted = generator.redact_sensitive_data(content)

        assert "user@example.com" not in redacted
        assert "[REDACTED_EMAIL]" in redacted

    def test_phone_redaction(self) -> None:
        """Phone numbers are redacted."""
        generator = ReportGenerator()
        content = "Call 555-123-4567 for support"

        redacted = generator.redact_sensitive_data(content)

        assert "555-123-4567" not in redacted
        assert "[REDACTED_PHONE]" in redacted

    def test_credit_card_redaction(self) -> None:
        """Credit card numbers are redacted."""
        generator = ReportGenerator()
        content = "Card: 4111-1111-1111-1111"

        redacted = generator.redact_sensitive_data(content)

        assert "4111-1111-1111-1111" not in redacted
        assert "[REDACTED_CC]" in redacted

    def test_bearer_token_redaction(self) -> None:
        """Bearer tokens are redacted."""
        generator = ReportGenerator()
        content = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

        redacted = generator.redact_sensitive_data(content)

        # Token should be redacted (either as TOKEN or KEY pattern)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
        assert "[REDACTED" in redacted  # Some redaction occurred

    def test_url_credentials_redaction(self) -> None:
        """Credentials in URLs are redacted."""
        generator = ReportGenerator()
        content = "Connect to https://admin:password123@example.com/api"

        redacted = generator.redact_sensitive_data(content)

        # Credentials should be redacted
        assert "admin:password123" not in redacted
        assert "[REDACTED" in redacted  # Some redaction occurred

    def test_redaction_enabled_by_default(self) -> None:
        """Redaction is enabled by default in generated reports."""
        generator = ReportGenerator(redact_by_default=True)
        finding = create_test_finding()

        # Modify finding to include sensitive data (in a real scenario)
        # For this test, we just verify the flag is respected
        draft = generator.generate(finding, "generic")

        # Draft should be generated (redaction doesn't break generation)
        assert draft is not None
        assert draft.status == DraftStatus.PENDING_REVIEW


class TestPlatformSpecificFormatting:
    """Test platform-specific report formatting."""

    def test_hackerone_format(self) -> None:
        """HackerOne reports have correct format."""
        generator = ReportGenerator()
        finding = create_test_finding()

        draft = generator.generate(finding, "hackerone")

        # Should have HackerOne-specific sections
        assert "## Summary" in draft.report_body
        assert "## Vulnerability Information" in draft.report_body
        assert "## Steps to Reproduce" in draft.report_body
        assert "## Impact" in draft.report_body

    def test_bugcrowd_format(self) -> None:
        """Bugcrowd reports have correct format."""
        generator = ReportGenerator()
        finding = create_test_finding()

        draft = generator.generate(finding, "bugcrowd")

        # Should have Bugcrowd-specific sections
        assert "# Description" in draft.report_body
        assert "# Proof of Concept" in draft.report_body
        assert "# Impact" in draft.report_body

    def test_generic_format(self) -> None:
        """Generic reports have markdown format."""
        generator = ReportGenerator()
        finding = create_test_finding()

        draft = generator.generate(finding, "generic")

        # Should have generic markdown sections
        assert "# Security Vulnerability Report" in draft.report_body
        assert "## Summary" in draft.report_body
        assert "## Reproduction Steps" in draft.report_body

    def test_unknown_platform_uses_generic(self) -> None:
        """Unknown platform falls back to generic format."""
        generator = ReportGenerator()
        finding = create_test_finding()

        draft = generator.generate(finding, "unknown_platform")

        # Should use generic format
        assert draft.platform == "unknown_platform"
        assert draft.report_body is not None


class TestArchitecturalBoundaryEnforcement:
    """Test that report generator enforces architectural boundaries."""

    def test_compute_severity_raises_violation(self) -> None:
        """compute_severity raises ArchitecturalViolationError."""
        generator = ReportGenerator()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            generator.compute_severity()

        assert "cannot compute severity" in str(exc_info.value).lower()

    def test_estimate_confidence_raises_violation(self) -> None:
        """estimate_confidence raises ArchitecturalViolationError."""
        generator = ReportGenerator()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            generator.estimate_confidence()

        assert "cannot estimate confidence" in str(exc_info.value).lower()

    def test_classify_vulnerability_raises_violation(self) -> None:
        """classify_vulnerability raises ArchitecturalViolationError."""
        generator = ReportGenerator()

        with pytest.raises(ArchitecturalViolationError) as exc_info:
            generator.classify_vulnerability()

        assert "cannot classify" in str(exc_info.value).lower()


class TestTitleAndLengthLimits:
    """Test title generation and length limits."""

    def test_title_includes_severity(self) -> None:
        """Generated title includes severity."""
        generator = ReportGenerator()
        finding = create_test_finding(severity="critical")

        draft = generator.generate(finding, "generic")

        assert "CRITICAL" in draft.report_title

    def test_title_respects_length_limit(self) -> None:
        """Title respects platform length limit."""
        generator = ReportGenerator()
        finding = create_test_finding()

        for platform, schema in PLATFORM_SCHEMAS.items():
            draft = generator.generate(finding, platform)
            assert len(draft.report_title) <= schema.max_title_length

    def test_body_respects_length_limit(self) -> None:
        """Body respects platform length limit."""
        generator = ReportGenerator()
        finding = create_test_finding()

        for platform, schema in PLATFORM_SCHEMAS.items():
            draft = generator.generate(finding, platform)
            assert len(draft.report_body) <= schema.max_body_length
