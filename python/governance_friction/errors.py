"""
Phase-10: Governance & Friction Layer - Error Types

All errors are non-recoverable (no retry logic).
Phase10BoundaryViolation is a HARD STOP error.
"""


class Phase10Error(Exception):
    """Base class for all Phase-10 errors."""
    pass


class DeliberationTimeViolation(Phase10Error):
    """
    Raised when deliberation time is insufficient.
    
    Minimum deliberation time is 5 seconds (HARD minimum).
    """
    def __init__(self, decision_id: str, elapsed_seconds: float, required_seconds: float):
        self.decision_id = decision_id
        self.elapsed_seconds = elapsed_seconds
        self.required_seconds = required_seconds
        super().__init__(
            f"Deliberation time violation for decision {decision_id}: "
            f"elapsed {elapsed_seconds:.2f}s < required {required_seconds:.2f}s"
        )


class ForcedEditViolation(Phase10Error):
    """
    Raised when no meaningful edit was made.
    
    Whitespace-only changes are NOT sufficient.
    """
    def __init__(self, decision_id: str, reason: str):
        self.decision_id = decision_id
        self.reason = reason
        super().__init__(
            f"Forced edit violation for decision {decision_id}: {reason}"
        )


class ChallengeNotAnswered(Phase10Error):
    """
    Raised when a challenge question was not answered.
    
    Empty or whitespace-only answers are invalid.
    """
    def __init__(self, decision_id: str, question_id: str):
        self.decision_id = decision_id
        self.question_id = question_id
        super().__init__(
            f"Challenge not answered for decision {decision_id}: question {question_id}"
        )


class CooldownViolation(Phase10Error):
    """
    Raised when an action is attempted during cooldown.
    
    Minimum cooldown time is 3 seconds (HARD minimum).
    """
    def __init__(self, decision_id: str, remaining_seconds: float):
        self.decision_id = decision_id
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Cooldown violation for decision {decision_id}: "
            f"{remaining_seconds:.2f}s remaining"
        )


class AuditIncomplete(Phase10Error):
    """
    Raised when audit trail is incomplete.
    
    All required audit items must be present.
    """
    def __init__(self, decision_id: str, missing_items: list[str]):
        self.decision_id = decision_id
        self.missing_items = missing_items
        super().__init__(
            f"Audit incomplete for decision {decision_id}: "
            f"missing {', '.join(missing_items)}"
        )


class Phase10BoundaryViolation(Phase10Error):
    """
    HARD STOP: Raised when Phase-10 boundaries are violated.
    
    This includes:
    - Forbidden imports (network, browser automation)
    - Forbidden actions (auto-approve, auto-submit)
    - Write attempts to read-only phases
    """
    def __init__(self, violation_type: str, details: str):
        self.violation_type = violation_type
        self.details = details
        super().__init__(
            f"HARD STOP - Phase-10 boundary violation ({violation_type}): {details}"
        )


class NetworkExecutionAttempt(Phase10BoundaryViolation):
    """
    HARD STOP: Raised when network execution is attempted.
    
    Phase-10 has NO network capability.
    """
    def __init__(self, module_name: str):
        super().__init__(
            violation_type="network_execution",
            details=f"Attempted to import forbidden network module: {module_name}"
        )


class AutomationAttempt(Phase10BoundaryViolation):
    """
    HARD STOP: Raised when automation is attempted.
    
    Phase-10 has NO automation capability.
    """
    def __init__(self, action: str):
        super().__init__(
            violation_type="automation",
            details=f"Attempted forbidden automation action: {action}"
        )


class FrictionBypassAttempt(Phase10BoundaryViolation):
    """
    HARD STOP: Raised when friction bypass is attempted.
    
    Friction mechanisms cannot be bypassed or disabled.
    """
    def __init__(self, mechanism: str):
        super().__init__(
            violation_type="friction_bypass",
            details=f"Attempted to bypass friction mechanism: {mechanism}"
        )


class ReadOnlyViolation(Phase10BoundaryViolation):
    """
    HARD STOP: Raised when write is attempted to read-only phase.
    
    Phase-10 has READ-ONLY access to Phases 6-9.
    """
    def __init__(self, phase: str, operation: str):
        super().__init__(
            violation_type="read_only",
            details=f"Attempted write operation '{operation}' on read-only phase: {phase}"
        )
