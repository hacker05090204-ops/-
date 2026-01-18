"""
Bounty Pipeline Error Hierarchy

All errors that cause HARD STOP are marked as such.
HARD STOP means: refuse to proceed, log the violation, alert human.
"""


class BountyPipelineError(Exception):
    """Base error for Bounty Pipeline."""

    pass


class FindingValidationError(BountyPipelineError):
    """Finding does not meet MCP proof requirements — HARD STOP.

    This error is raised when:
    - Finding lacks MCP BUG classification
    - Finding lacks valid proof chain
    - Finding has SIGNAL, NO_ISSUE, or COVERAGE_GAP classification
    """

    pass


class ScopeViolationError(BountyPipelineError):
    """Action would violate legal scope — HARD STOP.

    This error is raised when:
    - Target is outside authorized scope
    - Authorization document is missing
    - Target domain/IP is explicitly excluded
    """

    pass


class AuthorizationExpiredError(BountyPipelineError):
    """Authorization has expired — HARD STOP until renewed.

    This error is raised when:
    - Authorization document's valid_until date has passed
    - Authorization was revoked
    """

    pass


class HumanApprovalRequired(BountyPipelineError):
    """Submission blocked — human approval required.

    This is NOT a HARD STOP — it blocks until human approves.
    The system waits for human decision before proceeding.
    """

    pass


class ArchitecturalViolationError(BountyPipelineError):
    """Attempted to perform MCP/Cyfer Brain responsibility — HARD STOP.

    This error is raised when Bounty Pipeline is asked to:
    - Classify findings (MCP's responsibility)
    - Generate proofs (MCP's responsibility)
    - Compute confidence scores (MCP's responsibility)
    - Bypass human review
    - Modify MCP or Cyfer Brain code
    - Auto-submit reports
    """

    pass


class SubmissionFailedError(BountyPipelineError):
    """Submission to platform failed after retries.

    This is NOT a HARD STOP — the draft is preserved for retry.
    """

    pass


class AuditIntegrityError(BountyPipelineError):
    """Audit trail integrity compromised — HARD STOP.

    This error is raised when:
    - Hash chain verification fails
    - Audit records appear to be tampered with
    - Audit storage is corrupted
    """

    pass


class DuplicateDetectionError(BountyPipelineError):
    """Error during duplicate detection.

    This is NOT a HARD STOP — requires human decision.
    """

    pass


class PlatformError(BountyPipelineError):
    """Error communicating with bug bounty platform.

    This is NOT a HARD STOP — queued for retry.
    """

    pass


class RecoveryError(BountyPipelineError):
    """Error during state recovery.

    Alerts human with diagnostic information.
    """

    pass


# Error classification for handling
HARD_STOP_ERRORS = (
    FindingValidationError,
    ScopeViolationError,
    AuthorizationExpiredError,
    ArchitecturalViolationError,
    AuditIntegrityError,
)

BLOCKING_ERRORS = (HumanApprovalRequired,)

RECOVERABLE_ERRORS = (
    SubmissionFailedError,
    DuplicateDetectionError,
    PlatformError,
    RecoveryError,
)


def is_hard_stop(error: Exception) -> bool:
    """Check if error requires HARD STOP."""
    return isinstance(error, HARD_STOP_ERRORS)


def is_blocking(error: Exception) -> bool:
    """Check if error blocks until human action."""
    return isinstance(error, BLOCKING_ERRORS)


def is_recoverable(error: Exception) -> bool:
    """Check if error can be recovered from."""
    return isinstance(error, RECOVERABLE_ERRORS)
