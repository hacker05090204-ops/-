"""
Phase-7: Human-Authorized Submission Workflow

This module provides a human-authorized submission interface for transmitting
approved findings to bug bounty platforms. The system enforces explicit human
confirmation before any network activity.

ARCHITECTURAL CONSTRAINTS:
- Network access DISABLED by default
- Every submission requires explicit human confirmation
- No auto-submit, no exploit generation, no PoC generation
- No severity recalculation, no MCP override
- Separate audit log from Phase-6 (no cross-writes)
- Every submission references a HumanDecision.decision_id
- Report hash verified at transmission (tampering detection)

FORBIDDEN IMPORTS:
- execution_layer (Phase-4)
- artifact_scanner (Phase-5)
"""

from submission_workflow.types import (
    Platform,
    SubmissionStatus,
    SubmissionAction,
    SubmissionRequest,
    SubmissionConfirmation,
    SubmissionRecord,
    SubmissionAuditEntry,
    DraftReport,
    SubmissionStatusMachine,
    VALID_STATUS_TRANSITIONS,
)
from submission_workflow.errors import (
    SubmissionWorkflowError,
    TokenAlreadyUsedError,
    TokenExpiredError,
    ReportTamperingDetectedError,
    NetworkAccessDeniedError,
    AuditLogFailure,
    ArchitecturalViolationError,
    InvalidStatusTransitionError,
)
from submission_workflow.registry import ConfirmationRegistry
from submission_workflow.audit import SubmissionAuditLogger
from submission_workflow.network import (
    NetworkTransmitManager,
    verify_report_integrity,
    RequestCountingAdapter,
    PlatformAdapter,
)
from submission_workflow.duplicate import (
    DuplicateSubmissionGuard,
    SubmissionKey,
)

__all__ = [
    # Types
    "Platform",
    "SubmissionStatus",
    "SubmissionAction",
    "SubmissionRequest",
    "SubmissionConfirmation",
    "SubmissionRecord",
    "SubmissionAuditEntry",
    "DraftReport",
    "SubmissionStatusMachine",
    "VALID_STATUS_TRANSITIONS",
    # Errors
    "SubmissionWorkflowError",
    "TokenAlreadyUsedError",
    "TokenExpiredError",
    "ReportTamperingDetectedError",
    "NetworkAccessDeniedError",
    "AuditLogFailure",
    "ArchitecturalViolationError",
    "InvalidStatusTransitionError",
    # Components
    "ConfirmationRegistry",
    "SubmissionAuditLogger",
    "NetworkTransmitManager",
    "verify_report_integrity",
    "RequestCountingAdapter",
    "PlatformAdapter",
    "DuplicateSubmissionGuard",
    "SubmissionKey",
]
