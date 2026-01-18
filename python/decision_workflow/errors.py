"""
Phase-6 Error Hierarchy

All errors for the Human Decision Workflow. Includes HARD STOP errors
that halt system operation when critical invariants are violated.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import sys

if TYPE_CHECKING:
    from decision_workflow.types import Role, Action


class DecisionWorkflowError(Exception):
    """Base error for Phase-6 Human Decision Workflow."""
    pass


class AuthenticationError(DecisionWorkflowError):
    """Authentication failed - invalid credentials or missing authentication."""
    
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(message)


class SessionExpiredError(DecisionWorkflowError):
    """Session has expired - re-authentication required."""
    
    def __init__(self, session_id: str, message: str = "Session has expired"):
        self.session_id = session_id
        self.message = message
        super().__init__(f"{message}: session_id={session_id}")


class InsufficientPermissionError(DecisionWorkflowError):
    """
    Role does not have permission for the requested action.
    
    This error is raised when an Operator attempts a Reviewer-only action
    (e.g., assign severity, approve, reject).
    """
    
    def __init__(self, role: "Role", action: "Action"):
        from decision_workflow.types import Role, Action
        self.role = role
        self.action = action
        super().__init__(f"Role {role.value} cannot perform action {action.value}")


class ValidationError(DecisionWorkflowError):
    """
    Required field missing or invalid.
    
    Raised when decision validation fails (e.g., approve without severity,
    reject without rationale).
    """
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error on '{field}': {message}")


class AuditLogFailure(DecisionWorkflowError):
    """
    Audit log write failed — HARD STOP.
    
    EMERGENCY PROTOCOL:
    - System emits AUDIT_EMERGENCY to stderr
    - All operations halt immediately
    - No decisions can be recorded until audit is restored
    - Manual intervention required
    
    This is a critical error that prevents the system from continuing
    without a functioning audit trail.
    """
    
    def __init__(self, original_error: Exception | None = None, message: str = "Audit log write failed"):
        self.original_error = original_error
        self.message = message
        # Emit emergency signal to stderr
        print(f"AUDIT_EMERGENCY: {message}", file=sys.stderr)
        if original_error:
            print(f"AUDIT_EMERGENCY: Original error: {original_error}", file=sys.stderr)
        super().__init__(f"AUDIT_EMERGENCY: {message}")


class ArchitecturalViolationError(DecisionWorkflowError):
    """
    Forbidden action attempted — HARD STOP.
    
    Raised when code attempts to perform an action that violates
    Phase-6 architectural boundaries:
    - auto_classify() — MCP's responsibility
    - auto_severity() — Human's responsibility
    - auto_submit() — Human's responsibility
    - trigger_execution() — Phase-4's responsibility
    - trigger_scan() — Phase-5's responsibility
    - make_network_request() — FORBIDDEN (offline principle)
    
    This error is logged to the audit trail before halting.
    """
    
    def __init__(self, action: str):
        self.action = action
        super().__init__(f"Architectural violation: '{action}' is forbidden in Phase-6")
