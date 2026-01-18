"""
Phase-10: Governance & Friction Layer

This module implements intentional friction mechanisms to reduce human error
while preserving human authority. It does NOT automate any decisions.

CORE PRINCIPLE: Reduce human error, NOT human authority.

FORBIDDEN:
- Auto-approval
- Auto-submission
- Decision inference
- Execution capability
- Network access
- Browser automation
- Severity/bug classification
- Friction bypass or disable switches

USAGE:
    from governance_friction import FrictionCoordinator, FrictionState
    
    coordinator = FrictionCoordinator()
    state = coordinator.start_friction(decision_id, content, context)
    # ... human deliberates for >= 5 seconds ...
    state = coordinator.submit_edit(decision_id, edited_content)
    state = coordinator.submit_challenge_answer(decision_id, answer)
    state = coordinator.complete_deliberation(decision_id, reviewer_id)
    # ... human waits for >= 3 seconds cooldown ...
    state = coordinator.complete_friction(decision_id)
    
    if state.can_proceed:
        # Human has satisfied all friction requirements
        pass
"""

# Types
from governance_friction.types import (
    FrictionState,
    DeliberationRecord,
    ChallengeQuestion,
    RubberStampWarning,
    CooldownState,
    AuditCompleteness,
    FrictionAction,
    WarningLevel,
    AuditEntry,
    MIN_DELIBERATION_SECONDS,
    MIN_COOLDOWN_SECONDS,
    MIN_DECISIONS_FOR_ANALYSIS,
)

# Errors
from governance_friction.errors import (
    Phase10Error,
    DeliberationTimeViolation,
    ForcedEditViolation,
    ChallengeNotAnswered,
    CooldownViolation,
    AuditIncomplete,
    Phase10BoundaryViolation,
    NetworkExecutionAttempt,
    AutomationAttempt,
    FrictionBypassAttempt,
    ReadOnlyViolation,
)

# Components
from governance_friction.boundaries import Phase10BoundaryGuard
from governance_friction.deliberation import DeliberationTimer
from governance_friction.edit_checker import ForcedEditChecker
from governance_friction.challenge import ChallengeQuestionGenerator, ChallengeAnswerValidator
from governance_friction.rubber_stamp import RubberStampDetector
from governance_friction.cooldown import CooldownEnforcer
from governance_friction.audit_completeness import AuditCompletenessChecker
from governance_friction.audit import FrictionAuditLogger
from governance_friction.coordinator import FrictionCoordinator

__all__ = [
    # Types
    "FrictionState",
    "DeliberationRecord",
    "ChallengeQuestion",
    "RubberStampWarning",
    "CooldownState",
    "AuditCompleteness",
    "FrictionAction",
    "WarningLevel",
    "AuditEntry",
    "MIN_DELIBERATION_SECONDS",
    "MIN_COOLDOWN_SECONDS",
    "MIN_DECISIONS_FOR_ANALYSIS",
    # Errors
    "Phase10Error",
    "DeliberationTimeViolation",
    "ForcedEditViolation",
    "ChallengeNotAnswered",
    "CooldownViolation",
    "AuditIncomplete",
    "Phase10BoundaryViolation",
    "NetworkExecutionAttempt",
    "AutomationAttempt",
    "FrictionBypassAttempt",
    "ReadOnlyViolation",
    # Components
    "Phase10BoundaryGuard",
    "DeliberationTimer",
    "ForcedEditChecker",
    "ChallengeQuestionGenerator",
    "ChallengeAnswerValidator",
    "RubberStampDetector",
    "CooldownEnforcer",
    "AuditCompletenessChecker",
    "FrictionAuditLogger",
    "FrictionCoordinator",
]
