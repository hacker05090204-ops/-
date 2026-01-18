"""
Phase-6 Decision Capture

Records human decisions with validation and audit logging.

ARCHITECTURAL CONSTRAINTS:
- No auto-populate of severity
- No suggestion of decisions based on MCP confidence
- All decisions logged to audit trail
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid

from decision_workflow.types import (
    ReviewSession,
    DecisionInput,
    HumanDecision,
    DecisionType,
    Severity,
    Action,
    Role,
    DecisionReport,
)
from decision_workflow.errors import ValidationError, InsufficientPermissionError
from decision_workflow.audit import AuditLogger, create_audit_entry
from decision_workflow.roles import RoleEnforcer


class DecisionCapture:
    """
    Records human decisions with validation and audit logging.
    
    Validates that:
    - APPROVE requires severity
    - REJECT requires rationale
    - DEFER requires defer_reason
    - ESCALATE requires escalation_target
    - ADD_NOTE requires note
    
    Enforces role-based permissions:
    - Operators cannot APPROVE, REJECT, or ASSIGN_SEVERITY
    - Reviewers can perform all actions
    """
    
    def __init__(
        self,
        session: ReviewSession,
        audit_logger: AuditLogger,
        role_enforcer: RoleEnforcer,
    ):
        """
        Initialize decision capture.
        
        Args:
            session: The current review session.
            audit_logger: The audit logger for recording decisions.
            role_enforcer: The role enforcer for permission checks.
        """
        self._session = session
        self._audit_logger = audit_logger
        self._role_enforcer = role_enforcer
        self._decisions: list[HumanDecision] = []
    
    def make_decision(
        self,
        finding_id: str,
        decision: DecisionInput,
    ) -> HumanDecision:
        """
        Validate and record a human decision.
        
        Args:
            finding_id: The finding being decided on.
            decision: The decision input.
            
        Returns:
            The recorded HumanDecision.
            
        Raises:
            ValidationError: If required fields are missing.
            InsufficientPermissionError: If role cannot perform action.
        """
        # Check role permissions (with audit logging on denial)
        action = self._decision_type_to_action(decision.decision_type)
        try:
            self._role_enforcer.check_permission(self._session, action)
        except InsufficientPermissionError as e:
            # Log permission denial before re-raising
            self._log_permission_denial(action, e)
            raise
        
        # If approving, also check ASSIGN_SEVERITY permission
        if decision.decision_type == DecisionType.APPROVE:
            try:
                self._role_enforcer.check_permission(self._session, Action.ASSIGN_SEVERITY)
            except InsufficientPermissionError as e:
                self._log_permission_denial(Action.ASSIGN_SEVERITY, e)
                raise
        
        # Validate decision
        self._validate_decision(decision)
        
        # Create decision record
        decision_id = str(uuid.uuid4())
        human_decision = HumanDecision(
            decision_id=decision_id,
            finding_id=finding_id,
            session_id=self._session.session_id,
            reviewer_id=self._session.reviewer_id,
            role=self._session.role,
            decision_type=decision.decision_type,
            timestamp=datetime.now(),
            severity=decision.severity,
            cvss_score=decision.cvss_score,
            rationale=decision.rationale,
            defer_reason=decision.defer_reason,
            escalation_target=decision.escalation_target,
            note=decision.note,
        )
        
        # Log to audit
        entry = create_audit_entry(
            session_id=self._session.session_id,
            reviewer_id=self._session.reviewer_id,
            role=self._session.role,
            action="DECISION",
            finding_id=finding_id,
            decision_id=decision_id,
            decision_type=decision.decision_type,
            severity=decision.severity,
            rationale=decision.rationale,
        )
        self._audit_logger.log(entry)
        
        # Store decision
        self._decisions.append(human_decision)
        
        return human_decision
    
    def _validate_decision(self, decision: DecisionInput) -> None:
        """
        Validate that required fields are present for the decision type.
        
        Args:
            decision: The decision to validate.
            
        Raises:
            ValidationError: If required fields are missing.
        """
        if decision.decision_type == DecisionType.APPROVE:
            if decision.severity is None:
                raise ValidationError("severity", "Severity is required for APPROVE decisions")
            # Validate CVSS score if provided
            if decision.cvss_score is not None:
                if not (0.0 <= decision.cvss_score <= 10.0):
                    raise ValidationError("cvss_score", "CVSS score must be between 0.0 and 10.0")
        
        elif decision.decision_type == DecisionType.REJECT:
            if not decision.rationale:
                raise ValidationError("rationale", "Rationale is required for REJECT decisions")
        
        elif decision.decision_type == DecisionType.DEFER:
            if not decision.defer_reason:
                raise ValidationError("defer_reason", "Defer reason is required for DEFER decisions")
        
        elif decision.decision_type == DecisionType.ESCALATE:
            if not decision.escalation_target:
                raise ValidationError("escalation_target", "Escalation target is required for ESCALATE decisions")
        
        elif decision.decision_type == DecisionType.ADD_NOTE:
            if not decision.note:
                raise ValidationError("note", "Note is required for ADD_NOTE decisions")
    
    def _decision_type_to_action(self, decision_type: DecisionType) -> Action:
        """Map decision type to action for permission checking."""
        mapping = {
            DecisionType.APPROVE: Action.APPROVE,
            DecisionType.REJECT: Action.REJECT,
            DecisionType.DEFER: Action.DEFER,
            DecisionType.ESCALATE: Action.ESCALATE,
            DecisionType.MARK_REVIEWED: Action.MARK_REVIEWED,
            DecisionType.ADD_NOTE: Action.ADD_NOTE,
        }
        return mapping[decision_type]
    
    def _log_permission_denial(self, action: Action, error: InsufficientPermissionError) -> None:
        """
        Log a permission denial to the audit trail.
        
        Args:
            action: The action that was denied.
            error: The permission error that was raised.
        """
        entry = create_audit_entry(
            session_id=self._session.session_id,
            reviewer_id=self._session.reviewer_id,
            role=self._session.role,
            action="PERMISSION_DENIED",
            error_type="InsufficientPermissionError",
            error_message=f"Role {error.role.value} cannot perform {action.value}",
        )
        self._audit_logger.log(entry)
    
    def get_decisions(self) -> list[HumanDecision]:
        """Get all decisions made in this capture session."""
        return list(self._decisions)
    
    def export_report(self) -> DecisionReport:
        """
        Generate a decision report for the session.
        
        Returns:
            A DecisionReport containing all decisions.
        """
        return DecisionReport(
            report_id=str(uuid.uuid4()),
            session_id=self._session.session_id,
            reviewer_id=self._session.reviewer_id,
            role=self._session.role,
            generated_at=datetime.now(),
            decisions=tuple(self._decisions),
        )
