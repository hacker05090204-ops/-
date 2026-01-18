"""
Phase-21 Confirmation Tests

Tests verifying human confirmation is always required.
"""

import pytest


class TestHumanConfirmationRequired:
    """Tests verifying human confirmation is required."""

    def test_confirmation_records_human_decision(
        self,
        sample_patch_id: str,
        sample_timestamp: str,
        sample_human_reason: str,
    ) -> None:
        """Confirmation must record human decision."""
        from phase21_patch_covenant.confirmation import record_confirmation
        
        record = record_confirmation(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            confirmed=True,
            reason=sample_human_reason,
        )
        
        assert record.human_confirmed is True
        assert record.human_rejected is False
        assert record.human_reason == sample_human_reason

    def test_confirmation_sets_human_initiated(
        self,
        sample_patch_id: str,
        sample_timestamp: str,
        sample_human_reason: str,
    ) -> None:
        """Confirmation must set human_initiated=True."""
        from phase21_patch_covenant.confirmation import record_confirmation
        
        record = record_confirmation(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            confirmed=True,
            reason=sample_human_reason,
        )
        
        assert record.human_initiated is True

    def test_confirmation_sets_actor_human(
        self,
        sample_patch_id: str,
        sample_timestamp: str,
        sample_human_reason: str,
    ) -> None:
        """Confirmation must set actor='HUMAN'."""
        from phase21_patch_covenant.confirmation import record_confirmation
        
        record = record_confirmation(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            confirmed=True,
            reason=sample_human_reason,
        )
        
        assert record.actor == "HUMAN"


class TestRejectionAlwaysAllowed:
    """Tests verifying rejection is always allowed."""

    def test_rejection_is_recorded(
        self,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Rejection must be recorded."""
        from phase21_patch_covenant.confirmation import record_rejection
        
        record = record_rejection(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            reason="I do not approve this patch.",
        )
        
        assert record.human_rejected is True
        assert record.human_confirmed is False

    def test_rejection_accepts_any_reason(
        self,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Rejection must accept any reason (not analyzed)."""
        from phase21_patch_covenant.confirmation import record_rejection
        
        # Various reasons - all must be accepted
        reasons = [
            "",  # Empty is valid
            "No.",
            "I don't like it.",
            "Security concern.",
            "🚫",  # Emoji
            "a" * 10000,  # Long reason
        ]
        
        for reason in reasons:
            record = record_rejection(
                patch_id=sample_patch_id,
                timestamp=sample_timestamp,
                reason=reason,
            )
            assert record.human_rejected is True
            assert record.human_reason == reason

    def test_rejection_sets_human_initiated(
        self,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Rejection must set human_initiated=True."""
        from phase21_patch_covenant.confirmation import record_rejection
        
        record = record_rejection(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            reason="Rejected.",
        )
        
        assert record.human_initiated is True

    def test_rejection_sets_actor_human(
        self,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Rejection must set actor='HUMAN'."""
        from phase21_patch_covenant.confirmation import record_rejection
        
        record = record_rejection(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            reason="Rejected.",
        )
        
        assert record.actor == "HUMAN"


class TestReasonNotAnalyzed:
    """Tests verifying reason is not analyzed."""

    def test_reason_stored_as_is(
        self,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Reason must be stored exactly as provided."""
        from phase21_patch_covenant.confirmation import record_confirmation
        
        reason = "  Whitespace preserved  \n\ttabs too  "
        
        record = record_confirmation(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            confirmed=True,
            reason=reason,
        )
        
        assert record.human_reason == reason  # Exact match

    def test_empty_reason_accepted(
        self,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Empty reason must be accepted."""
        from phase21_patch_covenant.confirmation import record_confirmation
        
        record = record_confirmation(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            confirmed=True,
            reason="",
        )
        
        assert record.human_reason == ""


class TestNoAutoConfirmation:
    """Tests verifying no auto-confirmation exists."""

    def test_no_auto_confirm_function(self) -> None:
        """No auto_confirm function should exist."""
        import phase21_patch_covenant.confirmation as conf_module
        
        assert not hasattr(conf_module, "auto_confirm")
        assert not hasattr(conf_module, "auto_approve")
        assert not hasattr(conf_module, "auto_accept")

    def test_no_scheduled_confirmation(self) -> None:
        """No scheduled confirmation should exist."""
        import phase21_patch_covenant.confirmation as conf_module
        
        assert not hasattr(conf_module, "schedule_confirmation")
        assert not hasattr(conf_module, "delayed_confirm")

