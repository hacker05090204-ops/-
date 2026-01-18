"""
Phase-16 UI String Registry (LOCKED)

All UI strings MUST come from this registry.
No dynamic string generation based on data content.
No strings implying verification, priority, or recommendation.

GOVERNANCE CONSTRAINT:
- Strings are LOCKED and may not be modified at runtime
- No string may imply verification, confirmation, or authority
- No string may imply priority, importance, or recommendation
"""

from typing import Final


class UIStrings:
    """
    Locked string registry for Phase-16 UI.
    
    All strings are class constants (Final) and cannot be modified.
    """
    
    # === MANDATORY DISCLAIMERS ===
    CVE_DISCLAIMER: Final[str] = (
        "CVE data is reference-only and does not verify, confirm, "
        "or validate vulnerabilities."
    )
    
    NOT_VERIFIED_LABEL: Final[str] = "NOT VERIFIED"
    
    FINDING_DISCLAIMER: Final[str] = (
        "This finding has not been verified. Human review is required."
    )
    
    EVIDENCE_DISCLAIMER: Final[str] = (
        "Evidence is displayed as-is. No analysis or verification has been performed."
    )
    
    # === BUTTON LABELS (EQUAL WEIGHT) ===
    BUTTON_CONFIRM: Final[str] = "Confirm"
    BUTTON_CANCEL: Final[str] = "Cancel"
    BUTTON_VETO: Final[str] = "Veto"
    BUTTON_FETCH_CVE: Final[str] = "Fetch CVE (Manual)"
    BUTTON_BACK: Final[str] = "Back"
    BUTTON_FORWARD: Final[str] = "Forward"
    BUTTON_REFRESH: Final[str] = "Refresh"
    
    # === DIALOG TITLES (NEUTRAL) ===
    DIALOG_CONFIRM_ACTION: Final[str] = "Confirm Action"
    DIALOG_CONFIRM_SUBMISSION: Final[str] = "Confirm Submission"
    DIALOG_CONFIRM_CVE_FETCH: Final[str] = "Confirm CVE Fetch"
    
    # === DIALOG MESSAGES (NEUTRAL, NO URGENCY) ===
    MSG_CONFIRM_SUBMISSION: Final[str] = (
        "You are about to submit. This action cannot be undone. "
        "The finding has NOT been verified."
    )
    
    MSG_CONFIRM_CVE_FETCH: Final[str] = (
        "You are about to fetch CVE data. "
        "CVE data is reference-only and does not verify vulnerabilities."
    )
    
    MSG_ACTION_BLOCKED: Final[str] = (
        "This action is blocked by governance rules."
    )
    
    MSG_API_KEY_MISSING: Final[str] = (
        "CVE API key not configured. "
        "Please set CVE_API_KEY environment variable."
    )
    
    # === ERROR MESSAGES (NEUTRAL) ===
    ERROR_GOVERNANCE_VIOLATION: Final[str] = (
        "A governance violation was detected. "
        "Human investigation is required."
    )
    
    ERROR_PHASE15_BLOCKED: Final[str] = (
        "Action blocked by Phase-15 enforcement."
    )
    
    # === LABELS (NEUTRAL) ===
    LABEL_CVE_ID: Final[str] = "CVE ID"
    LABEL_DESCRIPTION: Final[str] = "Description"
    LABEL_EVIDENCE: Final[str] = "Evidence"
    LABEL_FINDING: Final[str] = "Finding"
    
    # Forbidden strings that MUST NOT appear in user-facing UI text
    # Note: "recommended" is the full word to check
    FORBIDDEN_STRINGS: Final[tuple[str, ...]] = (
        "verified",
        "confirmed",
        "validated",
        "recommend",
        "suggested",
        "likely",
        "probably",
        "important",
        "critical",
        "high priority",
        "low priority",
        "score",
        "rank",
        "severity",
        "confidence",
        "accuracy",
        "intelligent",
        "smart",
        "ai-powered",
        "ai powered",
        "machine learning",
        "act now",
        "limited time",
        "urgent",
        "hurry",
    )
    
    @classmethod
    def validate_no_forbidden(cls, text: str) -> bool:
        """
        Check that text contains no forbidden strings.
        
        Args:
            text: Text to validate
            
        Returns:
            True if text is valid (no forbidden strings)
        """
        text_lower = text.lower()
        for forbidden in cls.FORBIDDEN_STRINGS:
            if forbidden.lower() in text_lower:
                return False
        return True
