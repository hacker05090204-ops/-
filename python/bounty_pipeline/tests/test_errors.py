"""
Property tests for Bounty Pipeline error hierarchy.

**Feature: bounty-pipeline, Property 16: Architectural Boundary Enforcement**
**Validates: Requirements 11.1, 11.3, 11.4, 11.5**
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from bounty_pipeline.errors import (
    BountyPipelineError,
    FindingValidationError,
    ScopeViolationError,
    AuthorizationExpiredError,
    HumanApprovalRequired,
    ArchitecturalViolationError,
    SubmissionFailedError,
    AuditIntegrityError,
    DuplicateDetectionError,
    PlatformError,
    RecoveryError,
    HARD_STOP_ERRORS,
    BLOCKING_ERRORS,
    RECOVERABLE_ERRORS,
    is_hard_stop,
    is_blocking,
    is_recoverable,
)


class TestErrorHierarchy:
    """Test error class hierarchy."""

    def test_all_errors_inherit_from_base(self) -> None:
        """All errors inherit from BountyPipelineError."""
        error_classes = [
            FindingValidationError,
            ScopeViolationError,
            AuthorizationExpiredError,
            HumanApprovalRequired,
            ArchitecturalViolationError,
            SubmissionFailedError,
            AuditIntegrityError,
            DuplicateDetectionError,
            PlatformError,
            RecoveryError,
        ]

        for error_class in error_classes:
            assert issubclass(
                error_class, BountyPipelineError
            ), f"{error_class.__name__} must inherit from BountyPipelineError"

    def test_base_error_inherits_from_exception(self) -> None:
        """BountyPipelineError inherits from Exception."""
        assert issubclass(BountyPipelineError, Exception)


class TestHardStopErrors:
    """
    Property 16: Architectural Boundary Enforcement

    *For any* request to Bounty Pipeline to perform MCP responsibilities
    (classify, prove, compute confidence) or bypass human review,
    the system SHALL refuse with HARD STOP.

    **Validates: Requirements 11.1, 11.3, 11.4, 11.5**
    """

    def test_hard_stop_errors_are_defined(self) -> None:
        """HARD STOP errors are properly defined."""
        expected_hard_stop = {
            FindingValidationError,
            ScopeViolationError,
            AuthorizationExpiredError,
            ArchitecturalViolationError,
            AuditIntegrityError,
        }

        assert set(HARD_STOP_ERRORS) == expected_hard_stop

    def test_finding_validation_is_hard_stop(self) -> None:
        """FindingValidationError causes HARD STOP."""
        error = FindingValidationError("No MCP proof")
        assert is_hard_stop(error) is True
        assert is_blocking(error) is False
        assert is_recoverable(error) is False

    def test_scope_violation_is_hard_stop(self) -> None:
        """ScopeViolationError causes HARD STOP."""
        error = ScopeViolationError("Target outside scope")
        assert is_hard_stop(error) is True
        assert is_blocking(error) is False
        assert is_recoverable(error) is False

    def test_authorization_expired_is_hard_stop(self) -> None:
        """AuthorizationExpiredError causes HARD STOP."""
        error = AuthorizationExpiredError("Authorization expired")
        assert is_hard_stop(error) is True
        assert is_blocking(error) is False
        assert is_recoverable(error) is False

    def test_architectural_violation_is_hard_stop(self) -> None:
        """ArchitecturalViolationError causes HARD STOP."""
        error = ArchitecturalViolationError("Attempted to classify finding")
        assert is_hard_stop(error) is True
        assert is_blocking(error) is False
        assert is_recoverable(error) is False

    def test_audit_integrity_is_hard_stop(self) -> None:
        """AuditIntegrityError causes HARD STOP."""
        error = AuditIntegrityError("Hash chain broken")
        assert is_hard_stop(error) is True
        assert is_blocking(error) is False
        assert is_recoverable(error) is False


class TestBlockingErrors:
    """Test blocking errors that wait for human action."""

    def test_blocking_errors_are_defined(self) -> None:
        """Blocking errors are properly defined."""
        expected_blocking = {HumanApprovalRequired}
        assert set(BLOCKING_ERRORS) == expected_blocking

    def test_human_approval_is_blocking(self) -> None:
        """HumanApprovalRequired blocks until human action."""
        error = HumanApprovalRequired("Awaiting approval")
        assert is_hard_stop(error) is False
        assert is_blocking(error) is True
        assert is_recoverable(error) is False


class TestRecoverableErrors:
    """Test recoverable errors."""

    def test_recoverable_errors_are_defined(self) -> None:
        """Recoverable errors are properly defined."""
        expected_recoverable = {
            SubmissionFailedError,
            DuplicateDetectionError,
            PlatformError,
            RecoveryError,
        }
        assert set(RECOVERABLE_ERRORS) == expected_recoverable

    def test_submission_failed_is_recoverable(self) -> None:
        """SubmissionFailedError is recoverable."""
        error = SubmissionFailedError("API timeout")
        assert is_hard_stop(error) is False
        assert is_blocking(error) is False
        assert is_recoverable(error) is True

    def test_duplicate_detection_is_recoverable(self) -> None:
        """DuplicateDetectionError is recoverable."""
        error = DuplicateDetectionError("Similarity check failed")
        assert is_hard_stop(error) is False
        assert is_blocking(error) is False
        assert is_recoverable(error) is True

    def test_platform_error_is_recoverable(self) -> None:
        """PlatformError is recoverable."""
        error = PlatformError("HackerOne API unavailable")
        assert is_hard_stop(error) is False
        assert is_blocking(error) is False
        assert is_recoverable(error) is True

    def test_recovery_error_is_recoverable(self) -> None:
        """RecoveryError is recoverable."""
        error = RecoveryError("State recovery failed")
        assert is_hard_stop(error) is False
        assert is_blocking(error) is False
        assert is_recoverable(error) is True


class TestErrorClassification:
    """Test error classification functions."""

    @given(message=st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=5000)
    def test_error_classification_is_mutually_exclusive(self, message: str) -> None:
        """Each error is classified as exactly one type."""
        all_errors = [
            FindingValidationError(message),
            ScopeViolationError(message),
            AuthorizationExpiredError(message),
            HumanApprovalRequired(message),
            ArchitecturalViolationError(message),
            SubmissionFailedError(message),
            AuditIntegrityError(message),
            DuplicateDetectionError(message),
            PlatformError(message),
            RecoveryError(message),
        ]

        for error in all_errors:
            classifications = [
                is_hard_stop(error),
                is_blocking(error),
                is_recoverable(error),
            ]
            # Exactly one classification should be True
            assert (
                sum(classifications) == 1
            ), f"{type(error).__name__} should have exactly one classification"

    def test_unknown_error_is_not_classified(self) -> None:
        """Unknown errors are not classified as any type."""
        error = Exception("Unknown error")
        assert is_hard_stop(error) is False
        assert is_blocking(error) is False
        assert is_recoverable(error) is False


class TestArchitecturalViolationScenarios:
    """Test specific architectural violation scenarios."""

    def test_classify_finding_violation(self) -> None:
        """Attempting to classify findings raises ArchitecturalViolationError."""
        # This tests the error type, not the actual violation detection
        # (which will be in the validator)
        error = ArchitecturalViolationError(
            "Bounty Pipeline cannot classify findings - this is MCP's responsibility"
        )
        assert "classify" in str(error).lower()
        assert is_hard_stop(error)

    def test_generate_proof_violation(self) -> None:
        """Attempting to generate proofs raises ArchitecturalViolationError."""
        error = ArchitecturalViolationError(
            "Bounty Pipeline cannot generate proofs - this is MCP's responsibility"
        )
        assert "proof" in str(error).lower()
        assert is_hard_stop(error)

    def test_compute_confidence_violation(self) -> None:
        """Attempting to compute confidence raises ArchitecturalViolationError."""
        error = ArchitecturalViolationError(
            "Bounty Pipeline cannot compute confidence - this is MCP's responsibility"
        )
        assert "confidence" in str(error).lower()
        assert is_hard_stop(error)

    def test_bypass_review_violation(self) -> None:
        """Attempting to bypass human review raises ArchitecturalViolationError."""
        error = ArchitecturalViolationError(
            "Bounty Pipeline cannot bypass human review - approval is mandatory"
        )
        assert "bypass" in str(error).lower() or "review" in str(error).lower()
        assert is_hard_stop(error)

    def test_modify_mcp_violation(self) -> None:
        """Attempting to modify MCP raises ArchitecturalViolationError."""
        error = ArchitecturalViolationError(
            "Bounty Pipeline cannot modify MCP - Phase-1 is frozen"
        )
        assert "mcp" in str(error).lower()
        assert is_hard_stop(error)


class TestErrorMessages:
    """Test that errors have meaningful messages."""

    @given(message=st.text(min_size=1, max_size=100))
    @settings(max_examples=50, deadline=5000)
    def test_error_preserves_message(self, message: str) -> None:
        """Errors preserve their message."""
        error = BountyPipelineError(message)
        assert str(error) == message

    def test_error_docstrings_exist(self) -> None:
        """All error classes have docstrings."""
        error_classes = [
            BountyPipelineError,
            FindingValidationError,
            ScopeViolationError,
            AuthorizationExpiredError,
            HumanApprovalRequired,
            ArchitecturalViolationError,
            SubmissionFailedError,
            AuditIntegrityError,
            DuplicateDetectionError,
            PlatformError,
            RecoveryError,
        ]

        for error_class in error_classes:
            assert (
                error_class.__doc__ is not None
            ), f"{error_class.__name__} must have a docstring"
            assert len(error_class.__doc__) > 10, f"{error_class.__name__} docstring too short"
