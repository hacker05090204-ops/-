"""
Phase-16 Confirmation Parity Tests (TASK-P16-T02)

Verify Cancel/Veto buttons have equal visibility to Confirm.

GOVERNANCE CONSTRAINT:
Cancel/Veto must be equally visible as Confirm — no dark patterns.
"""

import pytest


class TestCancelVetoParity:
    """Verify Cancel/Veto buttons have equal visibility."""
    
    def test_confirmation_dialog_has_cancel(self):
        """Confirmation dialog must have Cancel button."""
        from phase16_ui.confirmation import ConfirmationDialog
        
        dialog = ConfirmationDialog(
            title="Test",
            message="Test message",
        )
        
        assert dialog.has_cancel_button(), "Confirmation dialog must have Cancel button"
    
    def test_confirmation_dialog_has_veto(self):
        """Confirmation dialog must have Veto button."""
        from phase16_ui.confirmation import ConfirmationDialog
        
        dialog = ConfirmationDialog(
            title="Test",
            message="Test message",
        )
        
        assert dialog.has_veto_button(), "Confirmation dialog must have Veto button"
    
    def test_cancel_button_equal_size(self):
        """Cancel button must be same size as Confirm button."""
        from phase16_ui.confirmation import ConfirmationDialog
        
        dialog = ConfirmationDialog(
            title="Test",
            message="Test message",
        )
        
        confirm_size = dialog.get_button_size("confirm")
        cancel_size = dialog.get_button_size("cancel")
        
        assert confirm_size == cancel_size, (
            f"Cancel button size ({cancel_size}) must equal Confirm size ({confirm_size})"
        )
    
    def test_veto_button_equal_size(self):
        """Veto button must be same size as Confirm button."""
        from phase16_ui.confirmation import ConfirmationDialog
        
        dialog = ConfirmationDialog(
            title="Test",
            message="Test message",
        )
        
        confirm_size = dialog.get_button_size("confirm")
        veto_size = dialog.get_button_size("veto")
        
        assert confirm_size == veto_size, (
            f"Veto button size ({veto_size}) must equal Confirm size ({confirm_size})"
        )
    
    def test_no_button_preselected(self):
        """No button may be pre-selected."""
        from phase16_ui.confirmation import ConfirmationDialog
        
        dialog = ConfirmationDialog(
            title="Test",
            message="Test message",
        )
        
        assert not dialog.has_preselected_button(), (
            "No button may be pre-selected in confirmation dialog"
        )
    
    def test_no_default_to_confirm(self):
        """Dialog must not default to Confirm action."""
        from phase16_ui.confirmation import ConfirmationDialog
        
        dialog = ConfirmationDialog(
            title="Test",
            message="Test message",
        )
        
        assert dialog.get_default_action() is None, (
            "Dialog must not have a default action"
        )
    
    def test_cancel_not_hidden(self):
        """Cancel button must not be hidden or de-emphasized."""
        from phase16_ui.confirmation import ConfirmationDialog
        
        dialog = ConfirmationDialog(
            title="Test",
            message="Test message",
        )
        
        assert dialog.is_button_visible("cancel"), "Cancel button must be visible"
        assert not dialog.is_button_deemphasized("cancel"), (
            "Cancel button must not be de-emphasized"
        )
    
    def test_veto_not_hidden(self):
        """Veto button must not be hidden or de-emphasized."""
        from phase16_ui.confirmation import ConfirmationDialog
        
        dialog = ConfirmationDialog(
            title="Test",
            message="Test message",
        )
        
        assert dialog.is_button_visible("veto"), "Veto button must be visible"
        assert not dialog.is_button_deemphasized("veto"), (
            "Veto button must not be de-emphasized"
        )


class TestNoConfirmshaming:
    """Verify no confirmshaming language in dialogs."""
    
    CONFIRMSHAMING_PATTERNS = [
        "are you sure",
        "miss this",
        "miss out",
        "lose this",
        "don't want",
        "no thanks",
        "maybe later",
        "not interested",
        "skip this",
    ]
    
    def test_cancel_label_neutral(self):
        """Cancel button label must be neutral."""
        from phase16_ui.strings import UIStrings
        
        cancel_label = UIStrings.BUTTON_CANCEL.lower()
        
        for pattern in self.CONFIRMSHAMING_PATTERNS:
            assert pattern not in cancel_label, (
                f"Cancel label contains confirmshaming: {pattern}"
            )
    
    def test_dialog_message_no_confirmshaming(self):
        """Dialog messages must not contain confirmshaming."""
        from phase16_ui.strings import UIStrings
        
        messages = [
            UIStrings.MSG_CONFIRM_SUBMISSION,
            UIStrings.MSG_CONFIRM_CVE_FETCH,
        ]
        
        for msg in messages:
            msg_lower = msg.lower()
            for pattern in self.CONFIRMSHAMING_PATTERNS:
                assert pattern not in msg_lower, (
                    f"Dialog message contains confirmshaming: {pattern}"
                )


class TestNoUrgencyIndicators:
    """Verify no urgency indicators in confirmation dialogs."""
    
    URGENCY_PATTERNS = [
        "act now",
        "hurry",
        "urgent",
        "immediately",
        "limited time",
        "expires",
        "deadline",
        "last chance",
        "don't wait",
    ]
    
    def test_no_countdown_timer(self):
        """Confirmation dialog must not have countdown timer."""
        from phase16_ui.confirmation import ConfirmationDialog
        
        dialog = ConfirmationDialog(
            title="Test",
            message="Test message",
        )
        
        assert not dialog.has_countdown(), (
            "Confirmation dialog must not have countdown timer"
        )
    
    def test_no_urgency_in_messages(self):
        """Dialog messages must not contain urgency language."""
        from phase16_ui.strings import UIStrings
        
        messages = [
            UIStrings.MSG_CONFIRM_SUBMISSION,
            UIStrings.MSG_CONFIRM_CVE_FETCH,
            UIStrings.DIALOG_CONFIRM_ACTION,
            UIStrings.DIALOG_CONFIRM_SUBMISSION,
        ]
        
        for msg in messages:
            msg_lower = msg.lower()
            for pattern in self.URGENCY_PATTERNS:
                assert pattern not in msg_lower, (
                    f"Dialog message contains urgency: {pattern}"
                )
