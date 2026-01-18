"""
Phase-9 Error Hierarchy

All errors for the Browser-Integrated Assisted Hunting Layer.

ERROR POLICY:
- ArchitecturalViolationError: HARD STOP - code fix required
- AutomationAttemptError: HARD STOP - code fix required
- NetworkExecutionAttemptError: HARD STOP - code fix required
- HumanConfirmationRequired: BLOCKING - human must confirm
- InvalidObservationError: Recoverable - return error message

Phase-9 MUST NOT:
- Execute any automated actions
- Bypass human confirmation
- Modify any data in earlier phases
"""

from __future__ import annotations


class BrowserAssistantError(Exception):
    """Base error for Phase-9 Browser Assistant."""
    pass


class ArchitecturalViolationError(BrowserAssistantError):
    """
    Forbidden action attempted — HARD STOP.
    
    Raised when code attempts to:
    - Import forbidden modules
    - Write to Phase-4 through Phase-8 data
    - Execute automated actions
    - Bypass human confirmation
    - Classify bugs
    - Assign severity
    - Submit reports
    
    This error requires a code fix to resolve.
    """
    
    def __init__(self, action: str):
        self.action = action
        super().__init__(
            f"Architectural violation: '{action}' is forbidden in Phase-9. "
            f"Phase-9 is ASSISTIVE ONLY with NO automation, NO classification, "
            f"NO submission authority. Human always clicks YES/NO."
        )


class AutomationAttemptError(BrowserAssistantError):
    """
    Automation attempted — HARD STOP.
    
    Raised when code attempts to:
    - Auto-confirm findings
    - Auto-generate PoCs
    - Auto-record video
    - Auto-submit reports
    - Auto-chain findings
    - Execute payloads
    - Inject traffic
    - Modify requests
    
    This error requires a code fix to resolve.
    """
    
    def __init__(self, action: str):
        self.action = action
        super().__init__(
            f"Automation forbidden: '{action}' is not allowed in Phase-9. "
            f"Phase-9 provides HINTS ONLY. Human must perform all actions."
        )


class NetworkExecutionAttemptError(BrowserAssistantError):
    """
    Network execution attempted — HARD STOP.
    
    Raised when code attempts to:
    - Execute HTTP requests
    - Inject payloads
    - Modify network traffic
    - Send data to external services
    
    Phase-9 OBSERVES network activity but NEVER executes.
    This error requires a code fix to resolve.
    """
    
    def __init__(self, action: str):
        self.action = action
        super().__init__(
            f"Network execution forbidden: '{action}' is not allowed in Phase-9. "
            f"Phase-9 OBSERVES only. It does NOT execute network requests."
        )


class HumanConfirmationRequired(BrowserAssistantError):
    """
    Human confirmation required before proceeding.
    
    This is a BLOCKING error that requires human interaction.
    The assistant MUST wait for explicit human confirmation
    before any output is acted upon.
    
    This is NOT an error condition - it is the normal flow.
    Every assistant output requires human confirmation.
    """
    
    def __init__(self, output_id: str, output_type: str):
        self.output_id = output_id
        self.output_type = output_type
        super().__init__(
            f"Human confirmation required for {output_type} (ID: {output_id}). "
            f"Human must click YES or NO to proceed."
        )


class InvalidObservationError(BrowserAssistantError):
    """
    Invalid or malformed observation data.
    
    This is a recoverable error. The caller should handle this
    by logging the error and continuing with other observations.
    
    Phase-9 MUST NOT block on invalid observations.
    """
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Invalid observation: {message}")


class ReadOnlyViolationError(BrowserAssistantError):
    """
    Attempt to write to read-only data — HARD STOP.
    
    Raised when code attempts to modify data from:
    - Phase-4 (Execution Layer)
    - Phase-5 (Artifact Scanner)
    - Phase-6 (Decision Workflow)
    - Phase-7 (Submission Workflow)
    - Phase-8 (Intelligence Layer)
    
    Phase-9 has READ-ONLY access to all earlier phases.
    This error requires a code fix to resolve.
    """
    
    def __init__(self, phase: str, action: str):
        self.phase = phase
        self.action = action
        super().__init__(
            f"Read-only violation: Cannot '{action}' in {phase}. "
            f"Phase-9 has READ-ONLY access to all earlier phases."
        )
