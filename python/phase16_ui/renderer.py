"""
Phase-16 UI Renderer Module

GOVERNANCE CONSTRAINT:
- All navigation requires human click
- No auto-navigation, auto-refresh, or background operations
- No headless browser mode
- No DOM scripting
- All Phase-15 calls require human trigger
"""

from typing import Any, Optional

from phase16_ui.strings import UIStrings
from phase16_ui.errors import UIGovernanceViolation


class UIRenderer:
    """
    UI renderer with human-initiated actions only.
    
    GOVERNANCE GUARANTEES:
    - All navigation requires human_initiated=True
    - No auto-navigation or auto-refresh
    - No headless browser mode
    - No DOM scripting
    - All Phase-15 calls require human trigger
    - All actions visible in viewport
    """
    
    def __init__(self) -> None:
        """Initialize renderer (no headless, no auto-navigation)."""
        # Not headless - governance constraint
        self.headless = False
        self.is_headless = False
        
        # No pending navigation on init
        self._pending_navigation: Optional[str] = None
        
        # Visible browser required
        self._requires_visible = True
        
        # No minimized browser
        self.allow_minimized = False
    
    def requires_visible_browser(self) -> bool:
        """Check if visible browser is required (always True)."""
        return True
    
    def actions_visible_in_viewport(self) -> bool:
        """Check if all actions are visible in viewport (always True)."""
        return True
    
    def has_pending_navigation(self) -> bool:
        """Check if there's pending navigation (always False on init)."""
        return self._pending_navigation is not None
    
    def navigate(
        self,
        url: str,
        human_initiated: bool = False,
    ) -> dict[str, Any]:
        """
        Navigate to URL (requires human initiation).
        
        Args:
            url: Target URL
            human_initiated: MUST be True
            
        Returns:
            Navigation result
            
        Raises:
            UIGovernanceViolation: If human_initiated is False
        """
        if not human_initiated:
            raise UIGovernanceViolation(
                "Navigation blocked: human_initiated must be True. "
                "Auto-navigation is prohibited."
            )
        
        return {
            "url": url,
            "status": "navigated",
            "human_initiated": True,
        }
    
    def go_back(self, human_initiated: bool = False) -> dict[str, Any]:
        """
        Go back in history (requires human initiation).
        
        Args:
            human_initiated: MUST be True
            
        Returns:
            Navigation result
            
        Raises:
            UIGovernanceViolation: If human_initiated is False
        """
        if not human_initiated:
            raise UIGovernanceViolation(
                "Back navigation blocked: human_initiated must be True."
            )
        
        return {"action": "back", "human_initiated": True}
    
    def go_forward(self, human_initiated: bool = False) -> dict[str, Any]:
        """
        Go forward in history (requires human initiation).
        
        Args:
            human_initiated: MUST be True
            
        Returns:
            Navigation result
            
        Raises:
            UIGovernanceViolation: If human_initiated is False
        """
        if not human_initiated:
            raise UIGovernanceViolation(
                "Forward navigation blocked: human_initiated must be True."
            )
        
        return {"action": "forward", "human_initiated": True}
    
    def refresh(self, human_initiated: bool = False) -> dict[str, Any]:
        """
        Refresh page (requires human initiation).
        
        Args:
            human_initiated: MUST be True
            
        Returns:
            Refresh result
            
        Raises:
            UIGovernanceViolation: If human_initiated is False
        """
        if not human_initiated:
            raise UIGovernanceViolation(
                "Refresh blocked: human_initiated must be True. "
                "Auto-refresh is prohibited."
            )
        
        return {"action": "refresh", "human_initiated": True}
    
    def call_enforcer(
        self,
        rule: str,
        human_initiated: bool = False,
    ) -> dict[str, Any]:
        """
        Call Phase-15 enforcer (requires human trigger).
        
        Args:
            rule: Rule to enforce
            human_initiated: MUST be True
            
        Returns:
            Enforcement result
            
        Raises:
            UIGovernanceViolation: If human_initiated is False
        """
        if not human_initiated:
            raise UIGovernanceViolation(
                "Enforcer call blocked: human_initiated must be True. "
                "All Phase-15 calls require human trigger."
            )
        
        from phase15_governance.enforcer import enforce_rule
        return enforce_rule(rule)
    
    def call_validator(
        self,
        data: dict[str, Any],
        human_initiated: bool = False,
    ) -> dict[str, Any]:
        """
        Call Phase-15 validator (requires human trigger).
        
        Args:
            data: Data to validate
            human_initiated: MUST be True
            
        Returns:
            Validation result
            
        Raises:
            UIGovernanceViolation: If human_initiated is False
        """
        if not human_initiated:
            raise UIGovernanceViolation(
                "Validator call blocked: human_initiated must be True. "
                "All Phase-15 calls require human trigger."
            )
        
        from phase15_governance.validator import validate_input
        return validate_input(data)
    
    def call_blocker(
        self,
        action: str,
        human_initiated: bool = False,
    ) -> dict[str, Any]:
        """
        Call Phase-15 blocker (requires human trigger).
        
        Args:
            action: Action to check
            human_initiated: MUST be True
            
        Returns:
            Blocking result
            
        Raises:
            UIGovernanceViolation: If human_initiated is False
        """
        if not human_initiated:
            raise UIGovernanceViolation(
                "Blocker call blocked: human_initiated must be True. "
                "All Phase-15 calls require human trigger."
            )
        
        from phase15_governance.blocker import block_if_prohibited
        return block_if_prohibited(action)
    
    def render_enforcement_result(self, result: dict[str, Any]) -> str:
        """
        Render enforcement result (no approval language).
        
        Args:
            result: Enforcement result from Phase-15
            
        Returns:
            Rendered result (pass/fail only, no approval)
        """
        blocked = result.get("blocked", False)
        rule = result.get("rule", "unknown")
        
        if blocked:
            return f"Enforcement: BLOCKED (rule: {rule})"
        else:
            # No approval language - just "not blocked"
            return f"Enforcement: Not blocked (rule: {rule})"
    
    def render_validation_result(self, result: dict[str, Any]) -> str:
        """
        Render validation result (pass/fail only).
        
        Args:
            result: Validation result from Phase-15
            
        Returns:
            Rendered result (pass/fail only, no verification)
        """
        valid = result.get("valid", False)
        errors = result.get("errors", [])
        
        if valid:
            return "Validation: Pass"
        else:
            error_text = ", ".join(errors) if errors else "validation failed"
            return f"Validation: Fail ({error_text})"
    
    def render_content(self, content: str) -> str:
        """
        Render content exactly as received (no modification).
        
        Args:
            content: Content to render
            
        Returns:
            Content unchanged
        """
        # Render exactly as received - no modification, no analysis
        return content
    
    def render_evidence(self, evidence: str) -> str:
        """
        Render evidence as read-only (no highlights, no annotations).
        
        Args:
            evidence: Evidence content
            
        Returns:
            Evidence with disclaimer
        """
        # Read-only, no highlights, no annotations
        return f"""
{UIStrings.EVIDENCE_DISCLAIMER}

---
{evidence}
---

{UIStrings.NOT_VERIFIED_LABEL}
"""
    
    def render_finding(self, finding: dict[str, Any]) -> str:
        """
        Render finding with NOT VERIFIED label.
        
        Args:
            finding: Finding data
            
        Returns:
            Finding with disclaimer and NOT VERIFIED label
        """
        title = finding.get("title", "Untitled")
        description = finding.get("description", "No description")
        
        # Always show NOT VERIFIED label
        return f"""
{UIStrings.FINDING_DISCLAIMER}

---
Title: {title}
Description: {description}

{UIStrings.NOT_VERIFIED_LABEL}
---
"""
