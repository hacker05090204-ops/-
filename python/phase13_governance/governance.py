"""
PHASE 13 — GOVERNANCE PRIMITIVES
2026 RE-IMPLEMENTATION

Core governance primitives for the system.

Document ID: GOV-PHASE13-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Final
import uuid


class GovernanceStatus(Enum):
    """Status of governance compliance."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    WAIVED = "waived"


@dataclass(frozen=True)
class GovernanceRecord:
    """Immutable record of a governance decision."""
    record_id: str
    action_description: str
    actor_id: str
    status: GovernanceStatus
    justification: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class GovernancePolicy:
    """Definition of a governance policy."""
    policy_id: str
    name: str
    description: str
    is_mandatory: bool = True


# Core governance policies
POLICY_HUMAN_AUTHORITY: Final[GovernancePolicy] = GovernancePolicy(
    policy_id="human_authority",
    name="Human Authority Required",
    description="All security operations require human authorization",
    is_mandatory=True
)

POLICY_AUDIT_TRAIL: Final[GovernancePolicy] = GovernancePolicy(
    policy_id="audit_trail",
    name="Audit Trail Required",
    description="All operations must produce an audit trail",
    is_mandatory=True
)


def create_governance_record(
    action_description: str,
    actor_id: str,
    status: GovernanceStatus,
    justification: str
) -> GovernanceRecord:
    """Create a governance record."""
    if not action_description:
        raise ValueError("action_description cannot be empty")
    
    return GovernanceRecord(
        record_id=str(uuid.uuid4()),
        action_description=action_description,
        actor_id=actor_id,
        status=status,
        justification=justification
    )


def is_governance_compliant(record: GovernanceRecord) -> bool:
    """Check if a governance record shows compliance."""
    return record.status == GovernanceStatus.COMPLIANT
