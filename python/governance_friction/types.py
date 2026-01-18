"""
Phase-10: Governance & Friction Layer - Type Definitions

All data models are frozen dataclasses for immutability.
All timing uses monotonic clock (time.monotonic()), NOT wall-clock time.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Any
import time


# =============================================================================
# CONSTANTS
# =============================================================================

# Minimum deliberation time in seconds (HARD minimum, cannot be reduced)
MIN_DELIBERATION_SECONDS: float = 5.0

# Minimum cooldown time in seconds (HARD minimum, cannot be reduced)
MIN_COOLDOWN_SECONDS: float = 3.0

# Minimum decisions required before rubber-stamp analysis
# Cold-start safety: reviewers with fewer decisions get NO warnings
MIN_DECISIONS_FOR_ANALYSIS: int = 5


# =============================================================================
# ENUMS
# =============================================================================

class FrictionAction(Enum):
    """Actions tracked in the friction audit log."""
    DELIBERATION_START = auto()
    DELIBERATION_END = auto()
    EDIT_REQUIRED = auto()
    EDIT_VERIFIED = auto()
    CHALLENGE_PRESENTED = auto()
    CHALLENGE_ANSWERED = auto()
    RUBBER_STAMP_ANALYZED = auto()
    COOLDOWN_START = auto()
    COOLDOWN_END = auto()
    AUDIT_COMPLETENESS_CHECK = auto()
    BOUNDARY_CHECK = auto()
    FRICTION_COMPLETE = auto()


class WarningLevel(Enum):
    """Warning levels for rubber-stamp detection (ADVISORY ONLY)."""
    NONE = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


# =============================================================================
# FROZEN DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class DeliberationRecord:
    """
    Record of a deliberation period.
    
    All timing uses monotonic clock for reliability.
    """
    decision_id: str
    start_monotonic: float  # time.monotonic() at start
    end_monotonic: Optional[float] = None  # time.monotonic() at end
    elapsed_seconds: float = 0.0
    is_complete: bool = False
    
    def with_end(self, end_monotonic: float) -> "DeliberationRecord":
        """Create a new record with end time set."""
        elapsed = end_monotonic - self.start_monotonic
        return DeliberationRecord(
            decision_id=self.decision_id,
            start_monotonic=self.start_monotonic,
            end_monotonic=end_monotonic,
            elapsed_seconds=elapsed,
            is_complete=elapsed >= MIN_DELIBERATION_SECONDS,
        )


@dataclass(frozen=True)
class ChallengeQuestion:
    """
    A challenge question requiring human judgment.
    
    Questions are context-aware and cannot be auto-answered.
    """
    question_id: str
    decision_id: str
    question_text: str
    context_summary: str
    expected_answer_type: str  # e.g., "explanation", "confirmation", "justification"
    answer: Optional[str] = None
    is_answered: bool = False
    
    def with_answer(self, answer: str) -> "ChallengeQuestion":
        """Create a new question with answer set."""
        return ChallengeQuestion(
            question_id=self.question_id,
            decision_id=self.decision_id,
            question_text=self.question_text,
            context_summary=self.context_summary,
            expected_answer_type=self.expected_answer_type,
            answer=answer,
            is_answered=bool(answer and answer.strip()),
        )


@dataclass(frozen=True)
class RubberStampWarning:
    """
    Advisory warning about potential rubber-stamping behavior.
    
    ADVISORY ONLY - does NOT block decisions.
    Cold-start safety: No warnings for reviewers with insufficient history.
    """
    reviewer_id: str
    warning_level: WarningLevel
    reason: str
    decision_count: int
    approval_rate: float
    average_deliberation_seconds: float
    is_cold_start: bool  # True if insufficient data for analysis
    
    @property
    def is_advisory_silent(self) -> bool:
        """Returns True if this warning should be silent (cold-start or no warning)."""
        return self.is_cold_start or self.warning_level == WarningLevel.NONE


@dataclass(frozen=True)
class CooldownState:
    """
    State of a cooldown period.
    
    All timing uses monotonic clock for reliability.
    """
    decision_id: str
    start_monotonic: float  # time.monotonic() at start
    duration_seconds: float
    end_monotonic: Optional[float] = None  # time.monotonic() at end
    is_complete: bool = False
    
    @property
    def remaining_seconds(self) -> float:
        """Calculate remaining cooldown time."""
        if self.is_complete:
            return 0.0
        current = time.monotonic()
        elapsed = current - self.start_monotonic
        remaining = self.duration_seconds - elapsed
        return max(0.0, remaining)
    
    def with_end(self, end_monotonic: float) -> "CooldownState":
        """Create a new state with end time set."""
        return CooldownState(
            decision_id=self.decision_id,
            start_monotonic=self.start_monotonic,
            duration_seconds=self.duration_seconds,
            end_monotonic=end_monotonic,
            is_complete=True,
        )


@dataclass(frozen=True)
class AuditCompleteness:
    """
    Checklist of required audit trail items.
    
    All items must be present for a decision to be valid.
    """
    decision_id: str
    has_deliberation: bool = False
    has_edit: bool = False
    has_challenge: bool = False
    has_cooldown: bool = False
    missing_items: tuple[str, ...] = field(default_factory=tuple)
    
    @property
    def is_complete(self) -> bool:
        """Returns True if all required items are present."""
        return (
            self.has_deliberation
            and self.has_edit
            and self.has_challenge
            and self.has_cooldown
        )


@dataclass(frozen=True)
class FrictionState:
    """
    Complete state of friction mechanisms for a decision.
    
    This is the primary output of the FrictionCoordinator.
    """
    decision_id: str
    deliberation: Optional[DeliberationRecord] = None
    edit_verified: bool = False
    challenge: Optional[ChallengeQuestion] = None
    rubber_stamp_warning: Optional[RubberStampWarning] = None
    cooldown: Optional[CooldownState] = None
    audit_completeness: Optional[AuditCompleteness] = None
    is_friction_complete: bool = False
    
    @property
    def can_proceed(self) -> bool:
        """Returns True if all friction requirements are met."""
        return (
            self.is_friction_complete
            and self.deliberation is not None
            and self.deliberation.is_complete
            and self.edit_verified
            and self.challenge is not None
            and self.challenge.is_answered
            and self.cooldown is not None
            and self.cooldown.is_complete
            and self.audit_completeness is not None
            and self.audit_completeness.is_complete
        )


@dataclass(frozen=True)
class AuditEntry:
    """
    A single entry in the friction audit log.
    
    Entries are immutable and form a hash chain for tamper detection.
    """
    entry_id: str
    decision_id: str
    action: FrictionAction
    timestamp_monotonic: float  # time.monotonic() at creation
    details: tuple[tuple[str, Any], ...] = field(default_factory=tuple)  # Immutable dict alternative
    previous_hash: str = ""
    entry_hash: str = ""
