"""
PHASE 12 — ACTION CONSTRAINTS
2026 RE-IMPLEMENTATION

Defines constraints on security actions.

Document ID: GOV-PHASE12-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Final


class ConstraintType(Enum):
    """Types of action constraints."""
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_ADMIN = "requires_admin"
    READ_ONLY = "read_only"
    TIME_LIMITED = "time_limited"
    SCOPE_LIMITED = "scope_limited"


@dataclass(frozen=True)
class ActionConstraint:
    """Constraint that limits an action."""
    constraint_id: str
    constraint_type: ConstraintType
    description: str
    is_mandatory: bool = True


# Predefined mandatory constraints
CONSTRAINT_HUMAN_APPROVAL: Final[ActionConstraint] = ActionConstraint(
    constraint_id="human_approval",
    constraint_type=ConstraintType.REQUIRES_APPROVAL,
    description="All security actions require human approval",
    is_mandatory=True
)

CONSTRAINT_NO_AUTO_EXPLOIT: Final[ActionConstraint] = ActionConstraint(
    constraint_id="no_auto_exploit",
    constraint_type=ConstraintType.REQUIRES_APPROVAL,
    description="Exploitation cannot be automated",
    is_mandatory=True
)


def is_constraint_satisfied(
    constraint: ActionConstraint,
    has_approval: bool = False,
    is_admin: bool = False
) -> bool:
    """Check if a constraint is satisfied."""
    if constraint.constraint_type == ConstraintType.REQUIRES_APPROVAL:
        return has_approval
    if constraint.constraint_type == ConstraintType.REQUIRES_ADMIN:
        return is_admin
    if constraint.constraint_type == ConstraintType.READ_ONLY:
        return True  # Read-only is always satisfied by read operations
    return False


def get_mandatory_constraints() -> list[ActionConstraint]:
    """Get all mandatory constraints that must always be checked."""
    return [CONSTRAINT_HUMAN_APPROVAL, CONSTRAINT_NO_AUTO_EXPLOIT]
