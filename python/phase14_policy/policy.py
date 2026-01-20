"""
PHASE 14 — TEXTUAL POLICY ENFORCEMENT
2026 RE-IMPLEMENTATION

Textual policy definitions and enforcement.

Document ID: GOV-PHASE14-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Final


class PolicyViolationType(Enum):
    """Types of policy violations."""
    UNAUTHORIZED_ACTION = "unauthorized_action"
    MISSING_APPROVAL = "missing_approval"
    SCOPE_EXCEEDED = "scope_exceeded"
    AUDIT_FAILURE = "audit_failure"


@dataclass(frozen=True)
class PolicyRule:
    """A textual policy rule."""
    rule_id: str
    rule_text: str
    is_blocking: bool = True  # If True, violation blocks action


@dataclass(frozen=True)
class PolicyViolation:
    """Record of a policy violation."""
    violation_id: str
    rule_id: str
    violation_type: PolicyViolationType
    description: str
    is_blocking: bool = True


# Core policy rules (textual)
RULE_HUMAN_MUST_AUTHORIZE: Final[PolicyRule] = PolicyRule(
    rule_id="rule_001",
    rule_text="All security operations MUST be explicitly authorized by a human operator.",
    is_blocking=True
)

RULE_NO_AUTOMATED_EXPLOIT: Final[PolicyRule] = PolicyRule(
    rule_id="rule_002",
    rule_text="Automated exploitation is FORBIDDEN. All exploits require manual initiation.",
    is_blocking=True
)

RULE_AUDIT_REQUIRED: Final[PolicyRule] = PolicyRule(
    rule_id="rule_003",
    rule_text="All operations MUST produce an audit trail for compliance.",
    is_blocking=True
)


def check_policy_compliance(has_human_approval: bool, has_audit: bool) -> list[PolicyViolation]:
    """Check compliance with core policies. Returns list of violations."""
    violations = []
    
    if not has_human_approval:
        violations.append(PolicyViolation(
            violation_id="v-001",
            rule_id=RULE_HUMAN_MUST_AUTHORIZE.rule_id,
            violation_type=PolicyViolationType.MISSING_APPROVAL,
            description="Human approval not obtained",
            is_blocking=True
        ))
    
    if not has_audit:
        violations.append(PolicyViolation(
            violation_id="v-002",
            rule_id=RULE_AUDIT_REQUIRED.rule_id,
            violation_type=PolicyViolationType.AUDIT_FAILURE,
            description="Audit trail not established",
            is_blocking=True
        ))
    
    return violations


def is_action_blocked(violations: list[PolicyViolation]) -> bool:
    """Check if any violation blocks the action."""
    return any(v.is_blocking for v in violations)
