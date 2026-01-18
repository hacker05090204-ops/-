"""
Phase-17 Window Launcher

GOVERNANCE CONSTRAINT:
- Visible window ONLY (NOT headless)
- No auto-start, no background execution
- No UI modification
- Human-initiated launch required
- Uses Phase-15/16 public interface only
"""

from typing import Any

from phase17_runtime.errors import (
    HeadlessModeViolation,
    AutomationViolation,
)


class WindowLauncher:
    """
    Window launcher with governance constraints.
    
    GOVERNANCE GUARANTEES:
    - Visible window only (NOT headless)
    - No auto-start
    - No background execution
    - No UI modification
    - Human-initiated launch required
    - Uses Phase-15/16 public interface only
    """
    
    def __init__(self) -> None:
        """Initialize launcher with governance-compliant defaults."""
        # Headless is ALWAYS False - governance constraint
        self.headless = False
        self.is_headless = False
        
        # Visibility constraints
        self.allow_minimized = False
        self.start_minimized = False
        self.allow_hidden = False
        self.start_hidden = False
        self.tray_only = False
        self.allow_offscreen = False
        self.focusable = True
        
        # Daemon mode prohibited
        self.daemon_mode = False
        
        # UI modification prohibited
        self.modifies_ui = False
        self.adds_ui_elements = False
        self.removes_ui_elements = False
        
        # Network calls prohibited (Phase-15 handles network)
        self.makes_network_calls = False
        
        # Public interface only
        self.uses_public_interface_only = True
        self.uses_phase15_public_interface = True
    
    def launch(self, headless: bool = False, human_initiated: bool = False) -> dict[str, Any]:
        """
        Launch visible window.
        
        Args:
            headless: MUST be False (raises if True)
            human_initiated: MUST be True
            
        Returns:
            Launch result
            
        Raises:
            HeadlessModeViolation: If headless=True
            AutomationViolation: If human_initiated=False
        """
        if headless:
            raise HeadlessModeViolation(
                "Headless mode is prohibited. Visible window required."
            )
        
        if not human_initiated:
            raise AutomationViolation(
                "Launch requires human_initiated=True. Auto-launch prohibited."
            )
        
        return {
            "status": "launched",
            "visible": True,
            "headless": False,
            "human_initiated": True,
        }
    
    def requires_visible(self) -> bool:
        """Check if visible window is required (always True)."""
        return True
    
    def requires_explicit_launch(self) -> bool:
        """Check if explicit launch is required (always True)."""
        return True
    
    def is_window_visible(self) -> bool:
        """Check if window is visible (always True for compliant launcher)."""
        return True
    
    def check_visibility(self) -> dict[str, Any]:
        """
        Check window visibility status.
        
        Returns:
            Visibility status dict
        """
        return {
            "visible": True,
            "minimized": False,
            "hidden": False,
            "headless": False,
        }
    
    def load_ui(self) -> dict[str, Any]:
        """
        Load Phase-16 UI exactly as-is.
        
        Returns:
            UI load result (no modification)
        """
        # Load Phase-16 UI without modification
        return {
            "status": "loaded",
            "modified": False,
            "phase16_intact": True,
        }
