# PHASE-13 GOVERNANCE COMPLIANCE
# This module is part of Phase-13 (Controlled Bug Bounty Browser Shell)
#
# FORBIDDEN CAPABILITIES:
# - NO automation logic
# - NO execution authority
# - NO decision authority
# - NO learning or personalization
# - NO audit modification
# - NO scope expansion
# - NO session extension
# - NO batch approvals
# - NO scheduled actions
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""Phase-13 Controlled Bug Bounty Browser Shell."""

# Track 1: Audit Trail Foundation
from browser_shell.audit_types import AuditEntry, Initiator, ActionType
from browser_shell.audit_storage import AuditStorage
from browser_shell.hash_chain import HashChain

# Track 2: Session Management
from browser_shell.session import Session, SessionManager

# Track 3: Scope Enforcement
from browser_shell.scope import ScopeParser, ScopeValidator, ScopeParseResult, ScopeActivationResult, ValidationResult

# Track 4: Human Decision Framework
from browser_shell.decision import (
    DecisionTracker,
    ConfirmationSystem,
    AttributionValidator,
    DecisionResult,
    RatioStatus,
    RepetitionStatus,
    ConfirmationResult,
    FrequencyStatus,
    AttributionResult,
)

# Track 5: Evidence Capture
from browser_shell.evidence import (
    EvidenceCapture,
    CaptureResult,
    EvidencePreview,
    StorageResult,
    BudgetStatus,
)

# Track 6: Report Submission
from browser_shell.report import (
    ReportSubmission,
    DraftResult,
    StepResult,
    SubmissionResult,
    SeverityResult,
    Template,
)

# Track 7: Suggestion System
from browser_shell.suggestion import (
    SuggestionSystem,
    Suggestion,
)

__all__ = [
    # Track 1
    "AuditEntry",
    "Initiator",
    "ActionType",
    "AuditStorage",
    "HashChain",
    # Track 2
    "Session",
    "SessionManager",
    # Track 3
    "ScopeParser",
    "ScopeValidator",
    "ScopeParseResult",
    "ScopeActivationResult",
    "ValidationResult",
    # Track 4
    "DecisionTracker",
    "ConfirmationSystem",
    "AttributionValidator",
    "DecisionResult",
    "RatioStatus",
    "RepetitionStatus",
    "ConfirmationResult",
    "FrequencyStatus",
    "AttributionResult",
    # Track 5
    "EvidenceCapture",
    "CaptureResult",
    "EvidencePreview",
    "StorageResult",
    "BudgetStatus",
    # Track 6
    "ReportSubmission",
    "DraftResult",
    "StepResult",
    "SubmissionResult",
    "SeverityResult",
    "Template",
    # Track 7
    "SuggestionSystem",
    "Suggestion",
]
