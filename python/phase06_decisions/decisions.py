"""
PHASE 06 — DECISION BOUNDARIES
2026 RE-IMPLEMENTATION

Decision boundaries define points where human decisions must be made.
NO SCORING. NO RANKING. NO AUTOMATION.

⚠️ CRITICAL: This is a 2026 RE-IMPLEMENTATION.

Document ID: GOV-PHASE06-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass
from enum import Enum
from typing import Final


# =============================================================================
# DECISION TYPE ENUM
# =============================================================================

class DecisionType(Enum):
    """Types of decisions that require human input."""
    PROCEED = "proceed"          # Whether to proceed with an action
    ABORT = "abort"              # Whether to abort an operation
    CONFIRM = "confirm"          # General confirmation
    AUTHORIZE = "authorize"      # Security authorization
    ACKNOWLEDGE = "acknowledge"  # Acknowledge risk/warning


class DecisionOutcome(Enum):
    """Outcome of a human decision."""
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    PENDING = "pending"


# =============================================================================
# DECISION POINT
# =============================================================================

@dataclass(frozen=True)
class DecisionPoint:
    """
    A point in the workflow where a human decision is required.
    
    NO SCORING. NO RANKING. Decisions are binary (approved/rejected).
    """
    point_id: str
    description: str
    decision_type: DecisionType
    requires_admin: bool = False


# =============================================================================
# DECISION RECORD
# =============================================================================

@dataclass(frozen=True)
class DecisionRecord:
    """
    Immutable record of a human decision.
    
    All decisions must be made by humans.
    No automated decision-making is permitted.
    """
    record_id: str
    point_id: str
    actor_id: str
    outcome: DecisionOutcome
    reason: str = ""


# =============================================================================
# DECISION VALIDATION
# =============================================================================

def requires_decision(operation_name: str) -> bool:
    """
    Check if an operation requires a human decision.
    
    By default, ALL security operations require a decision.
    
    Args:
        operation_name: Name of the operation
    
    Returns:
        bool: True - all operations require human decision
    """
    # Per governance: ALL operations require human decision
    return True


def is_decision_approved(record: DecisionRecord) -> bool:
    """
    Check if a decision was approved.
    
    Args:
        record: The decision record
    
    Returns:
        bool: True if approved, False otherwise
    """
    return record.outcome == DecisionOutcome.APPROVED


# =============================================================================
# PREDEFINED DECISION POINTS
# =============================================================================

DECISION_SCAN_START: Final[DecisionPoint] = DecisionPoint(
    point_id="scan_start",
    description="Authorize starting a security scan",
    decision_type=DecisionType.AUTHORIZE
)

DECISION_OPERATION_EXECUTE: Final[DecisionPoint] = DecisionPoint(
    point_id="operation_execute",
    description="Authorize executing a security operation",
    decision_type=DecisionType.AUTHORIZE,
    requires_admin=True
)

DECISION_CONTINUE_ON_WARNING: Final[DecisionPoint] = DecisionPoint(
    point_id="continue_on_warning",
    description="Acknowledge warning and decide whether to continue",
    decision_type=DecisionType.ACKNOWLEDGE
)


# =============================================================================
# END OF PHASE-06 DECISIONS
# =============================================================================
