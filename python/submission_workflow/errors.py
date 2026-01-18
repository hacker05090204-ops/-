"""
Phase-7 Error Hierarchy

All errors for the Human-Authorized Submission Workflow. Includes HARD STOP
errors that halt system operation when critical invariants are violated.

ARCHITECTURAL CONSTRAINTS:
- All errors are logged to audit trail (except AuditLogFailure)
- HARD STOP errors halt all operations immediately
- No silent failures - all errors raise exceptions
"""

from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
import sys

if TYPE_CHECKING:
    from submission_workflow.types import Platform


class SubmissionWorkflowError(Exception):
    """Base error for Phase-7 Human-Authorized Submission Workflow."""
    pass


class DecisionNotFoundError(SubmissionWorkflowError):
    """Referenced HumanDecision not found in Phase-6."""
    
    def __init__(self, decision_id: str):
        self.decision_id = decision_id
        super().__init__(f"Decision not found: {decision_id}")


class InvalidDecisionTypeError(SubmissionWorkflowError):
    """Decision type is not APPROVE."""
    
    def __init__(self, decision_id: str, decision_type: str):
        self.decision_id = decision_id
        self.decision_type = decision_type
        super().__init__(f"Decision {decision_id} is {decision_type}, not APPROVE")


class MissingSeverityError(SubmissionWorkflowError):
    """Decision has no severity assigned."""
    
    def __init__(self, decision_id: str):
        self.decision_id = decision_id
        super().__init__(f"Decision {decision_id} has no severity")


class TokenAlreadyUsedError(SubmissionWorkflowError):
    """
    Confirmation token has already been used.
    
    Each SubmissionConfirmation authorizes exactly ONE network request.
    After the request completes (success or failure), the confirmation
    is invalidated and cannot be reused.
    
    SECURITY: This prevents replay attacks where a malicious actor
    attempts to reuse a confirmation to submit multiple times.
    """
    
    def __init__(self, confirmation_id: str, used_at: datetime):
        self.confirmation_id = confirmation_id
        self.used_at = used_at
        super().__init__(
            f"Confirmation {confirmation_id} already used at {used_at.isoformat()}"
        )


class ReportTamperingDetectedError(SubmissionWorkflowError):
    """
    Report content was modified after confirmation — HARD STOP.
    
    SECURITY: The report hash computed at transmission time does not
    match the hash stored in the SubmissionConfirmation. This indicates
    the report was tampered with after the human confirmed it.
    
    HARD STOP: Network access is denied and the system halts.
    This is a critical security violation that requires investigation.
    """
    
    def __init__(
        self,
        confirmation_id: str,
        expected_hash: str,
        actual_hash: str,
    ):
        self.confirmation_id = confirmation_id
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        # Emit security alert to stderr
        print(
            f"SECURITY_ALERT: Report tampering detected for confirmation "
            f"{confirmation_id}. Expected hash: {expected_hash}, "
            f"Actual hash: {actual_hash}",
            file=sys.stderr,
        )
        super().__init__(
            f"Report tampering detected: confirmation {confirmation_id} "
            f"expected hash {expected_hash[:16]}..., got {actual_hash[:16]}..."
        )


class TokenExpiredError(SubmissionWorkflowError):
    """Confirmation token has expired."""
    
    def __init__(self, token_id: str, expired_at: datetime):
        self.token_id = token_id
        self.expired_at = expired_at
        super().__init__(f"Token {token_id} expired at {expired_at.isoformat()}")


class NetworkAccessDeniedError(SubmissionWorkflowError):
    """Network access attempted without valid confirmation."""
    
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Network access denied: {reason}")


class DuplicateSubmissionError(SubmissionWorkflowError):
    """Submission already exists for this decision/platform."""
    
    def __init__(self, decision_id: str, platform: "Platform"):
        self.decision_id = decision_id
        self.platform = platform
        super().__init__(f"Already submitted {decision_id} to {platform.value}")


class PlatformSubmissionError(SubmissionWorkflowError):
    """Platform rejected or failed to process submission."""
    
    def __init__(self, platform: "Platform", error: str):
        self.platform = platform
        self.error = error
        super().__init__(f"Platform {platform.value} error: {error}")


class PlatformAuthenticationError(SubmissionWorkflowError):
    """Platform credentials are invalid."""
    
    def __init__(self, platform: "Platform", message: str = "Invalid credentials"):
        self.platform = platform
        self.message = message
        super().__init__(f"Platform {platform.value} authentication failed: {message}")


class InsufficientPermissionError(SubmissionWorkflowError):
    """User lacks required role for submission."""
    
    def __init__(self, user_id: str, required_role: str):
        self.user_id = user_id
        self.required_role = required_role
        super().__init__(f"User {user_id} lacks {required_role} role")


class AuditLogFailure(SubmissionWorkflowError):
    """
    Audit log write failed — HARD STOP.
    
    EMERGENCY PROTOCOL:
    - System emits AUDIT_EMERGENCY to stderr
    - All operations halt immediately
    - No submissions can be made until audit is restored
    - Manual intervention required
    
    This is a critical error that prevents the system from continuing
    without a functioning audit trail.
    """
    
    def __init__(
        self,
        original_error: Exception | None = None,
        message: str = "Audit log write failed",
    ):
        self.original_error = original_error
        self.message = message
        # Emit emergency signal to stderr
        print(f"AUDIT_EMERGENCY: {message}", file=sys.stderr)
        if original_error:
            print(f"AUDIT_EMERGENCY: Original error: {original_error}", file=sys.stderr)
        super().__init__(f"AUDIT_EMERGENCY: {message}")


class ArchitecturalViolationError(SubmissionWorkflowError):
    """
    Forbidden action attempted — HARD STOP.
    
    Raised when code attempts to perform an action that violates
    Phase-7 architectural boundaries:
    - auto_submit() — Human's responsibility
    - generate_exploit() — FORBIDDEN (safety)
    - generate_poc() — MCP's responsibility
    - recalculate_severity() — Human assigned in Phase-6
    - reclassify_vulnerability() — MCP's responsibility
    - override_mcp_decision() — MCP is truth engine
    - modify_phase6_audit() — Audit separation principle
    - modify_human_decision() — Phase-6 data is read-only
    
    This error is logged to the audit trail before halting.
    """
    
    def __init__(self, action: str):
        self.action = action
        super().__init__(f"Architectural violation: '{action}' is forbidden in Phase-7")


class InvalidStatusTransitionError(SubmissionWorkflowError):
    """
    Invalid status transition attempted.
    
    SubmissionStatus follows a strict state diagram:
    
    PENDING → CONFIRMED → SUBMITTED → ACKNOWLEDGED
                    ↓           ↓
                 FAILED      REJECTED
    
    Valid transitions:
    - PENDING → CONFIRMED (human confirms)
    - CONFIRMED → SUBMITTED (transmission succeeds)
    - CONFIRMED → FAILED (transmission fails)
    - SUBMITTED → ACKNOWLEDGED (platform acknowledges)
    - SUBMITTED → REJECTED (platform rejects)
    
    Invalid transitions (examples):
    - PENDING → SUBMITTED (must go through CONFIRMED)
    - SUBMITTED → PENDING (no backward transitions)
    - FAILED → SUBMITTED (terminal state)
    
    SECURITY: This prevents bypassing the human confirmation step.
    """
    
    def __init__(
        self,
        from_status: "SubmissionStatus",
        to_status: "SubmissionStatus",
    ):
        from submission_workflow.types import SubmissionStatus
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(
            f"Invalid status transition: {from_status.value} → {to_status.value}"
        )
