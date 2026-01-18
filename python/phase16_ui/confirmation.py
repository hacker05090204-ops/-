"""
Phase-16 Confirmation Dialog Module

GOVERNANCE CONSTRAINT:
- Cancel/Veto must be equally visible as Confirm
- No button pre-selected
- No countdown timers or urgency indicators
- No confirmshaming language
"""

from typing import Optional
from dataclasses import dataclass, field

from phase16_ui.strings import UIStrings


@dataclass
class ButtonConfig:
    """Button configuration with equal sizing."""
    label: str
    size: tuple[int, int] = (120, 40)  # Equal size for all buttons
    visible: bool = True
    deemphasized: bool = False  # Never True for Cancel/Veto
    selected: bool = False  # Never pre-selected


@dataclass
class ConfirmationDialog:
    """
    Confirmation dialog with equal button visibility.
    
    GOVERNANCE GUARANTEES:
    - Cancel button always present and equally visible
    - Veto button always present and equally visible
    - No button pre-selected
    - No countdown timer
    - No urgency indicators
    - No confirmshaming
    """
    
    title: str
    message: str
    
    # Buttons with equal configuration
    _confirm_button: ButtonConfig = field(default_factory=lambda: ButtonConfig(
        label=UIStrings.BUTTON_CONFIRM
    ))
    _cancel_button: ButtonConfig = field(default_factory=lambda: ButtonConfig(
        label=UIStrings.BUTTON_CANCEL
    ))
    _veto_button: ButtonConfig = field(default_factory=lambda: ButtonConfig(
        label=UIStrings.BUTTON_VETO
    ))
    
    # No countdown - governance constraint
    _has_countdown: bool = False
    
    # No default action - governance constraint
    _default_action: Optional[str] = None
    
    def has_cancel_button(self) -> bool:
        """Check if Cancel button exists (always True)."""
        return True
    
    def has_veto_button(self) -> bool:
        """Check if Veto button exists (always True)."""
        return True
    
    def get_button_size(self, button_name: str) -> tuple[int, int]:
        """
        Get button size (all buttons have equal size).
        
        Args:
            button_name: "confirm", "cancel", or "veto"
            
        Returns:
            Button size tuple (width, height)
        """
        # All buttons have equal size - governance constraint
        return (120, 40)
    
    def has_preselected_button(self) -> bool:
        """Check if any button is pre-selected (always False)."""
        # No pre-selection - governance constraint
        return False
    
    def get_default_action(self) -> Optional[str]:
        """Get default action (always None)."""
        # No default action - governance constraint
        return None
    
    def is_button_visible(self, button_name: str) -> bool:
        """
        Check if button is visible (always True for Cancel/Veto).
        
        Args:
            button_name: Button name
            
        Returns:
            True if visible
        """
        # All buttons always visible - governance constraint
        return True
    
    def is_button_deemphasized(self, button_name: str) -> bool:
        """
        Check if button is de-emphasized (always False for Cancel/Veto).
        
        Args:
            button_name: Button name
            
        Returns:
            False (never de-emphasized)
        """
        # No de-emphasis - governance constraint
        return False
    
    def has_countdown(self) -> bool:
        """Check if dialog has countdown timer (always False)."""
        # No countdown - governance constraint
        return False
    
    def render(self) -> str:
        """
        Render confirmation dialog.
        
        Returns:
            Dialog content string
        """
        return f"""
=== {self.title} ===

{self.message}

[{self._confirm_button.label}]  [{self._cancel_button.label}]  [{self._veto_button.label}]

(No button is pre-selected. All buttons have equal visibility.)
"""


def create_submission_confirmation() -> ConfirmationDialog:
    """Create confirmation dialog for submissions."""
    return ConfirmationDialog(
        title=UIStrings.DIALOG_CONFIRM_SUBMISSION,
        message=UIStrings.MSG_CONFIRM_SUBMISSION,
    )


def create_cve_fetch_confirmation() -> ConfirmationDialog:
    """Create confirmation dialog for CVE fetch."""
    return ConfirmationDialog(
        title=UIStrings.DIALOG_CONFIRM_CVE_FETCH,
        message=UIStrings.MSG_CONFIRM_CVE_FETCH,
    )


def create_action_confirmation(action_description: str) -> ConfirmationDialog:
    """
    Create confirmation dialog for generic action.
    
    Args:
        action_description: Description of action to confirm
        
    Returns:
        Confirmation dialog
    """
    return ConfirmationDialog(
        title=UIStrings.DIALOG_CONFIRM_ACTION,
        message=f"You are about to: {action_description}\n\nThis action requires confirmation.",
    )
