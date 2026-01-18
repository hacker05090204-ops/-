"""
Bounty Pipeline - Human-in-the-Loop Submission Engine (Phase-3)

This system assists humans. It does not replace them.

CRITICAL CONSTRAINTS:
- MCP (Phase-1) is FROZEN — DO NOT MODIFY
- Cyfer Brain (Phase-2) is FROZEN — DO NOT MODIFY
- NO submission without MCP proof
- NO submission without human approval
- NO confidence scoring (MCP's domain)
- NO auto-earning logic

AUTOMATION BOUNDARY:
The system MAY automate:
- Intake of MCP-proven findings
- Legal scope validation
- Duplicate advisory checks
- Evidence collection and proof packaging
- Platform-specific report drafting
- Status tracking and audit logging

The system MUST:
- STOP before submission
- Present a SubmissionDraft for review
- Require a one-time human approval token
- NEVER log into bounty platforms automatically
- NEVER submit reports automatically
"""

from bounty_pipeline.types import (
    MCPClassification,
    MCPFinding,
    ValidatedFinding,
    SubmissionDraft,
    ProofChain,
    ApprovalToken,
    SubmissionReceipt,
    AuditRecord,
    AuthorizationDocument,
    DuplicateCandidate,
    SubmissionStatus,
    StatusUpdate,
    DraftStatus,
    SourceLinks,
    ReproductionStep,
)
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
    is_hard_stop,
    is_blocking,
    is_recoverable,
)
from bounty_pipeline.validator import FindingValidator
from bounty_pipeline.scope import LegalScopeValidator
from bounty_pipeline.review import HumanReviewGate
from bounty_pipeline.report import ReportGenerator
from bounty_pipeline.audit import AuditTrail
from bounty_pipeline.duplicate import DuplicateDetector
from bounty_pipeline.pipeline import BountyPipeline
from bounty_pipeline.adapters import (
    PlatformType,
    EncryptedCredentials,
    AuthSession,
    PlatformSchema,
    PlatformAdapter,
    HackerOneAdapter,
    BugcrowdAdapter,
    GenericMarkdownAdapter,
    get_adapter,
)
from bounty_pipeline.submission import (
    SubmissionManager,
    QueuedSubmission,
    QueuedSubmissionStatus,
)
from bounty_pipeline.status import (
    StatusTracker,
    TrackedSubmission,
)
from bounty_pipeline.recovery import (
    RecoveryManager,
    PipelineState,
    PendingAction,
    ActionResult,
    ActionType,
    ActionStatus,
)
from bounty_pipeline.program import (
    ProgramManager,
    ProgramPolicy,
    ProgramContext,
    CrossProgramFinding,
)

__version__ = "0.1.0"
__all__ = [
    # Main orchestrator
    "BountyPipeline",
    # Components
    "FindingValidator",
    "LegalScopeValidator",
    "HumanReviewGate",
    "ReportGenerator",
    "AuditTrail",
    "DuplicateDetector",
    "SubmissionManager",
    "StatusTracker",
    "RecoveryManager",
    "ProgramManager",
    # Platform Adapters
    "PlatformType",
    "EncryptedCredentials",
    "AuthSession",
    "PlatformSchema",
    "PlatformAdapter",
    "HackerOneAdapter",
    "BugcrowdAdapter",
    "GenericMarkdownAdapter",
    "get_adapter",
    # Submission
    "QueuedSubmission",
    "QueuedSubmissionStatus",
    # Status
    "TrackedSubmission",
    # Recovery
    "PipelineState",
    "PendingAction",
    "ActionResult",
    "ActionType",
    "ActionStatus",
    # Program
    "ProgramPolicy",
    "ProgramContext",
    "CrossProgramFinding",
    # Types
    "MCPClassification",
    "MCPFinding",
    "ValidatedFinding",
    "SubmissionDraft",
    "ProofChain",
    "ApprovalToken",
    "SubmissionReceipt",
    "AuditRecord",
    "AuthorizationDocument",
    "DuplicateCandidate",
    "SubmissionStatus",
    "StatusUpdate",
    "DraftStatus",
    "SourceLinks",
    "ReproductionStep",
    # Errors
    "BountyPipelineError",
    "FindingValidationError",
    "ScopeViolationError",
    "AuthorizationExpiredError",
    "HumanApprovalRequired",
    "ArchitecturalViolationError",
    "SubmissionFailedError",
    "AuditIntegrityError",
    "DuplicateDetectionError",
    "PlatformError",
    "RecoveryError",
    # Error classification
    "is_hard_stop",
    "is_blocking",
    "is_recoverable",
]
