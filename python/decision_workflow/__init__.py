"""
Phase-6: Human Decision Workflow

A human-in-the-loop decision interface for reviewing Phase-5 scanner signals
and MCP classifications. Captures human decisions with full audit logging
and role-based access control.

ARCHITECTURAL CONSTRAINTS:
- No automation of decisions, severity, or submission
- No network access
- No imports from execution_layer
- Audit logging is append-only with SHA-256 hash chain
- All data models are immutable (frozen dataclasses)
"""

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
from decision_workflow.errors import (
    DecisionWorkflowError,
    AuthenticationError,
    SessionExpiredError,
    InsufficientPermissionError,
    ValidationError,
    AuditLogFailure,
    ArchitecturalViolationError,
)

__all__ = [
    # Types
    "Role",
    "DecisionType",
    "Severity",
    "Action",
    "ROLE_PERMISSIONS",
    "Credentials",
    "ReviewSession",
    "DecisionInput",
    "HumanDecision",
    "AuditEntry",
    "QueueItem",
    "DecisionReport",
    # Errors
    "DecisionWorkflowError",
    "AuthenticationError",
    "SessionExpiredError",
    "InsufficientPermissionError",
    "ValidationError",
    "AuditLogFailure",
    "ArchitecturalViolationError",
]
