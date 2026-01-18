"""
Phase-6 Role Enforcement

Enforces Operator vs Reviewer permissions. Operators can triage and review,
but cannot approve, reject, or assign severity. Reviewers have full permissions.

ARCHITECTURAL CONSTRAINTS:
- No auto-assignment of roles
- No auto-escalation from Operator to Reviewer
- All permission denials are logged to audit
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from decision_workflow.types import Role, Action, ROLE_PERMISSIONS, ReviewSession
from decision_workflow.errors import InsufficientPermissionError

if TYPE_CHECKING:
    from decision_workflow.audit import AuditLogger


class RoleEnforcer:
    """
    Enforces role-based permissions for the decision workflow.
    
    Operators can:
    - View findings
    - Mark as reviewed
    - Add notes
    - Defer findings
    - Escalate to Reviewer
    
    Reviewers can do everything Operators can, plus:
    - Assign severity
    - Approve findings
    - Reject findings
    """
    
    def __init__(self, audit_logger: "AuditLogger | None" = None):
        """
        Initialize role enforcer.
        
        Args:
            audit_logger: Optional audit logger for logging permission denials.
        """
        self._audit_logger = audit_logger
    
    def check_permission(self, session: ReviewSession, action: Action) -> None:
        """
        Check if the session's role has permission for the action.
        
        Args:
            session: The current review session.
            action: The action being attempted.
            
        Raises:
            InsufficientPermissionError: If the role cannot perform the action.
        """
        allowed_actions = self.get_allowed_actions(session.role)
        
        if action not in allowed_actions:
            # Log the permission denial if audit logger is available
            if self._audit_logger is not None:
                from datetime import datetime
                import uuid
                from decision_workflow.types import AuditEntry
                
                entry = AuditEntry(
                    entry_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    session_id=session.session_id,
                    reviewer_id=session.reviewer_id,
                    role=session.role,
                    action="PERMISSION_DENIED",
                    error_type="InsufficientPermissionError",
                    error_message=f"Role {session.role.value} cannot perform {action.value}",
                )
                self._audit_logger.log(entry)
            
            raise InsufficientPermissionError(session.role, action)
    
    def get_allowed_actions(self, role: Role) -> set[Action]:
        """
        Get the set of actions allowed for a role.
        
        Args:
            role: The role to check.
            
        Returns:
            Set of allowed actions for the role.
        """
        return ROLE_PERMISSIONS.get(role, set())
    
    def can_perform(self, session: ReviewSession, action: Action) -> bool:
        """
        Check if the session's role can perform the action without raising.
        
        Args:
            session: The current review session.
            action: The action being attempted.
            
        Returns:
            True if the action is allowed, False otherwise.
        """
        return action in self.get_allowed_actions(session.role)
    
    def is_operator(self, session: ReviewSession) -> bool:
        """Check if the session is for an Operator."""
        return session.role == Role.OPERATOR
    
    def is_reviewer(self, session: ReviewSession) -> bool:
        """Check if the session is for a Reviewer."""
        return session.role == Role.REVIEWER
