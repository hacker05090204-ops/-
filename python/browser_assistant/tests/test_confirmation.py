"""
Phase-9 Confirmation Gate Tests

Tests for human confirmation functionality.
"""

import pytest
from datetime import datetime, timedelta

from browser_assistant.confirmation import HumanConfirmationGate
from browser_assistant.types import ConfirmationStatus
from browser_assistant.errors import HumanConfirmationRequired


class TestHumanConfirmationGate:
    """Test confirmation gate functionality."""
    
    def test_register_output(self, confirmation_gate):
        """Verify outputs can be registered."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        assert output.output_id is not None
        assert output.output_type == "hint"
        assert output.confirmation_status == ConfirmationStatus.PENDING
    
    def test_output_requires_confirmation(self, confirmation_gate):
        """Verify outputs require confirmation."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        assert output.requires_human_confirmation is True
        assert output.no_auto_action is True
        assert output.is_advisory_only is True
    
    def test_request_confirmation_raises(self, confirmation_gate):
        """Verify request_confirmation raises HumanConfirmationRequired."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        with pytest.raises(HumanConfirmationRequired) as exc_info:
            confirmation_gate.request_confirmation(output.output_id)
        
        assert exc_info.value.output_id == output.output_id
        assert exc_info.value.output_type == "hint"
    
    def test_confirm_approved(self, confirmation_gate):
        """Verify confirmation with YES."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        confirmation = confirmation_gate.confirm(
            output_id=output.output_id,
            confirmed_by="user-001",
            approved=True,
        )
        
        assert confirmation.status == ConfirmationStatus.CONFIRMED
        assert confirmation.confirmed_by == "user-001"
        assert confirmation.is_explicit_human_action is True
        assert confirmation.is_single_use is True
    
    def test_confirm_rejected(self, confirmation_gate):
        """Verify confirmation with NO."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        confirmation = confirmation_gate.confirm(
            output_id=output.output_id,
            confirmed_by="user-001",
            approved=False,
        )
        
        assert confirmation.status == ConfirmationStatus.REJECTED
    
    def test_is_confirmed(self, confirmation_gate):
        """Verify is_confirmed check."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        assert confirmation_gate.is_confirmed(output.output_id) is False
        
        confirmation_gate.confirm(
            output_id=output.output_id,
            confirmed_by="user-001",
            approved=True,
        )
        
        assert confirmation_gate.is_confirmed(output.output_id) is True
    
    def test_is_rejected(self, confirmation_gate):
        """Verify is_rejected check."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        assert confirmation_gate.is_rejected(output.output_id) is False
        
        confirmation_gate.confirm(
            output_id=output.output_id,
            confirmed_by="user-001",
            approved=False,
        )
        
        assert confirmation_gate.is_rejected(output.output_id) is True
    
    def test_is_pending(self, confirmation_gate):
        """Verify is_pending check."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        assert confirmation_gate.is_pending(output.output_id) is True
        
        confirmation_gate.confirm(
            output_id=output.output_id,
            confirmed_by="user-001",
            approved=True,
        )
        
        assert confirmation_gate.is_pending(output.output_id) is False
    
    def test_get_pending_outputs(self, confirmation_gate):
        """Verify pending outputs can be retrieved."""
        for i in range(3):
            confirmation_gate.register_output(
                output_type=f"hint-{i}",
                content={"index": i},
            )
        
        pending = confirmation_gate.get_pending_outputs()
        assert len(pending) == 3
    
    def test_get_confirmation(self, confirmation_gate):
        """Verify confirmation can be retrieved."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        confirmation = confirmation_gate.confirm(
            output_id=output.output_id,
            confirmed_by="user-001",
            approved=True,
        )
        
        retrieved = confirmation_gate.get_confirmation(confirmation.confirmation_id)
        assert retrieved is not None
        assert retrieved.confirmation_id == confirmation.confirmation_id
    
    def test_confirmation_has_hash(self, confirmation_gate):
        """Verify confirmation has integrity hash."""
        output = confirmation_gate.register_output(
            output_type="hint",
            content={"test": "data"},
        )
        
        confirmation = confirmation_gate.confirm(
            output_id=output.output_id,
            confirmed_by="user-001",
            approved=True,
        )
        
        assert confirmation.confirmation_hash is not None
        assert len(confirmation.confirmation_hash) == 64  # SHA-256 hex
    
    def test_clear_all(self, confirmation_gate):
        """Verify all data can be cleared."""
        for i in range(3):
            output = confirmation_gate.register_output(
                output_type=f"hint-{i}",
                content={"index": i},
            )
            if i < 2:
                confirmation_gate.confirm(
                    output_id=output.output_id,
                    confirmed_by="user-001",
                    approved=True,
                )
        
        pending, confs = confirmation_gate.clear_all()
        assert pending == 1  # One still pending
        assert confs == 2    # Two confirmed
        
        assert len(confirmation_gate.get_pending_outputs()) == 0
    
    def test_pending_limit_enforced(self, confirmation_gate):
        """Verify pending output limit is enforced."""
        confirmation_gate._max_pending = 10
        
        for i in range(15):
            confirmation_gate.register_output(
                output_type=f"hint-{i}",
                content={"index": i},
            )
        
        pending = confirmation_gate.get_pending_outputs()
        assert len(pending) == 10


class TestConfirmationGateNoForbiddenMethods:
    """Verify gate has no forbidden methods."""
    
    def test_no_auto_confirm(self, confirmation_gate):
        """Verify auto_confirm method does not exist."""
        assert not hasattr(confirmation_gate, "auto_confirm")
    
    def test_no_bypass_confirmation(self, confirmation_gate):
        """Verify bypass_confirmation method does not exist."""
        assert not hasattr(confirmation_gate, "bypass_confirmation")
    
    def test_no_batch_confirm(self, confirmation_gate):
        """Verify batch_confirm method does not exist."""
        assert not hasattr(confirmation_gate, "batch_confirm")
    
    def test_no_timeout_approve(self, confirmation_gate):
        """Verify timeout_approve method does not exist."""
        assert not hasattr(confirmation_gate, "timeout_approve")
    
    def test_no_skip_confirmation(self, confirmation_gate):
        """Verify skip_confirmation method does not exist."""
        assert not hasattr(confirmation_gate, "skip_confirmation")
    
    def test_no_confirm_all(self, confirmation_gate):
        """Verify confirm_all method does not exist."""
        assert not hasattr(confirmation_gate, "confirm_all")
    
    def test_no_auto_approve(self, confirmation_gate):
        """Verify auto_approve method does not exist."""
        assert not hasattr(confirmation_gate, "auto_approve")
    
    def test_no_default_approve(self, confirmation_gate):
        """Verify default_approve method does not exist."""
        assert not hasattr(confirmation_gate, "default_approve")
