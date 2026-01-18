"""
Phase-17 Runtime Configuration

GOVERNANCE CONSTRAINT:
- No headless mode
- No auto-start
- No minimized/hidden start
- No tray-only mode
- Visible window required
"""

from typing import Any

from phase17_runtime.errors import (
    HeadlessModeViolation,
    AutomationViolation,
    SilentStartupViolation,
)


class RuntimeConfig:
    """
    Runtime configuration with governance constraints.
    
    GOVERNANCE GUARANTEES:
    - headless=False (always)
    - visible=True (always)
    - No auto-start
    - No minimized/hidden start
    - No tray-only mode
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize runtime config.
        
        Raises:
            HeadlessModeViolation: If headless=True
            AutomationViolation: If auto_start=True
            SilentStartupViolation: If start_minimized/hidden/tray_only=True
        """
        # Check for forbidden options
        if kwargs.get("headless", False):
            raise HeadlessModeViolation(
                "Headless mode is prohibited. Visible window required."
            )
        
        if kwargs.get("auto_start", False):
            raise AutomationViolation(
                "Auto-start is prohibited. Explicit user launch required."
            )
        
        if kwargs.get("start_minimized", False):
            raise SilentStartupViolation(
                "Minimized start is prohibited. Visible window required."
            )
        
        if kwargs.get("start_hidden", False):
            raise SilentStartupViolation(
                "Hidden start is prohibited. Visible window required."
            )
        
        if kwargs.get("tray_only", False):
            raise SilentStartupViolation(
                "Tray-only mode is prohibited. Visible window required."
            )
        
        # Set governance-compliant defaults
        self.headless = False
        self.visible = True
        self.auto_start = False
        self.start_minimized = False
        self.start_hidden = False
        self.tray_only = False
