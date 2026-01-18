"""
Phase-7 Confirmation Registry Tests

Tests for the ConfirmationRegistry that ensures:
- A confirmation_id can only be used once
- Reuse raises TokenAlreadyUsedError
- State survives process restart (in-memory + persisted audit check)
- All replay attempts are logged to audit trail

Feature: human-authorized-submission, Property 11: One Confirmation Per Request
Validates: Requirements 4.2, 4.7
"""

from __future__ import annotations
from datetime import datetime, timedelta
import uuid

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from submission_workflow.types import (
    SubmissionConfirmation,
    SubmissionAction,
    UsedConfirmation,
)
from submission_workflow.errors import TokenAlreadyUsedError, TokenExpiredError
from submission_workflow.audit import SubmissionAuditLogger
from submission_workflow.registry import ConfirmationRegistry
from submission_workflow.tests.conftest import make_confirmation


class TestConfirmationRegistryBasic:
    """Basic functionality tests for ConfirmationRegistry."""
    
    def test_new_registry_is_empty(self, registry: ConfirmationRegistry) -> None:
        """A new registry should have no consumed confirmations."""
        assert len(registry) == 0
    
    def test_unused_confirmation_not_in_registry(
        self,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """An unused confirmation should not be in the registry."""
        assert not registry.is_used(sample_confirmation.confirmation_id)
        assert sample_confirmation.confirmation_id not in registry
    
    def test_consume_marks_confirmation_as_used(
        self,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Consuming a confirmation should mark it as used."""
        used = registry.consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
        )
        
        assert registry.is_used(sample_confirmation.confirmation_id)
        assert sample_confirmation.confirmation_id in registry
        assert used.confirmation_id == sample_confirmation.confirmation_id
        assert used.request_id == sample_confirmation.request_id
        assert used.transmission_success is True
    
    def test_consume_records_failure(
        self,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Consuming with failure should record the error."""
        used = registry.consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
            transmission_success=False,
            error_message="Platform rejected submission",
        )
        
        assert registry.is_used(sample_confirmation.confirmation_id)
        assert used.transmission_success is False
        assert used.error_message == "Platform rejected submission"
    
    def test_get_used_confirmation_returns_record(
        self,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """get_used_confirmation should return the usage record."""
        registry.consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
        )
        
        used = registry.get_used_confirmation(sample_confirmation.confirmation_id)
        assert used is not None
        assert used.confirmation_id == sample_confirmation.confirmation_id
    
    def test_get_used_confirmation_returns_none_for_unused(
        self,
        registry: ConfirmationRegistry,
    ) -> None:
        """get_used_confirmation should return None for unused confirmations."""
        assert registry.get_used_confirmation("nonexistent-id") is None


class TestReplayPrevention:
    """Tests for replay attack prevention."""
    
    def test_replay_attempt_raises_token_already_used_error(
        self,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """
        Replay attempt always fails.
        
        Feature: human-authorized-submission, Property 11: One Confirmation Per Request
        Validates: Requirements 4.2, 4.7
        """
        # First use succeeds
        registry.consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
        )
        
        # Second use (replay) fails
        with pytest.raises(TokenAlreadyUsedError) as exc_info:
            registry.consume(
                confirmation=sample_confirmation,
                submitter_id="test-submitter",
            )
        
        assert exc_info.value.confirmation_id == sample_confirmation.confirmation_id
    
    def test_replay_attempt_logged_in_audit(
        self,
        audit_logger: SubmissionAuditLogger,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """
        Replay attempt logged in audit.
        
        Feature: human-authorized-submission, Property 11: One Confirmation Per Request
        Validates: Requirements 4.2, 4.7
        """
        # First use succeeds
        registry.consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
        )
        
        # Second use (replay) fails
        with pytest.raises(TokenAlreadyUsedError):
            registry.consume(
                confirmation=sample_confirmation,
                submitter_id="attacker",
            )
        
        # Check audit log for replay attempt
        replay_entries = audit_logger.find_replay_attempts(
            sample_confirmation.confirmation_id
        )
        assert len(replay_entries) == 1
        assert replay_entries[0].action == SubmissionAction.CONFIRMATION_REPLAY_BLOCKED
        assert replay_entries[0].confirmation_id == sample_confirmation.confirmation_id
        assert replay_entries[0].error_type == "TokenAlreadyUsedError"
    
    def test_multiple_replay_attempts_all_logged(
        self,
        audit_logger: SubmissionAuditLogger,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Multiple replay attempts should all be logged."""
        # First use succeeds
        registry.consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
        )
        
        # Multiple replay attempts
        for i in range(3):
            with pytest.raises(TokenAlreadyUsedError):
                registry.consume(
                    confirmation=sample_confirmation,
                    submitter_id=f"attacker-{i}",
                )
        
        # All replay attempts should be logged
        replay_entries = audit_logger.find_replay_attempts(
            sample_confirmation.confirmation_id
        )
        assert len(replay_entries) == 3
    
    def test_replay_after_failed_transmission_still_blocked(
        self,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """
        Even if transmission failed, confirmation cannot be reused.
        
        This is critical: a confirmation is consumed regardless of
        transmission success/failure to prevent replay attacks.
        """
        # First use fails (transmission error)
        registry.consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
            transmission_success=False,
            error_message="Network error",
        )
        
        # Replay attempt still blocked
        with pytest.raises(TokenAlreadyUsedError):
            registry.consume(
                confirmation=sample_confirmation,
                submitter_id="test-submitter",
            )


class TestPersistence:
    """Tests for state persistence across restarts."""
    
    def test_state_survives_via_audit_log(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """
        State survives process restart via audit log.
        
        Simulates a restart by creating a new registry with the same
        audit logger. The new registry should recognize previously
        consumed confirmations.
        """
        # Create first registry and consume a confirmation
        registry1 = ConfirmationRegistry(audit_logger)
        confirmation = make_confirmation()
        registry1.consume(
            confirmation=confirmation,
            submitter_id="test-submitter",
        )
        
        # Simulate restart: create new registry with same audit logger
        registry2 = ConfirmationRegistry(audit_logger)
        
        # New registry should recognize the consumed confirmation
        assert registry2.is_used(confirmation.confirmation_id)
    
    def test_replay_blocked_after_restart(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """Replay should be blocked even after process restart."""
        # Create first registry and consume a confirmation
        registry1 = ConfirmationRegistry(audit_logger)
        confirmation = make_confirmation()
        registry1.consume(
            confirmation=confirmation,
            submitter_id="test-submitter",
        )
        
        # Simulate restart: create new registry with same audit logger
        registry2 = ConfirmationRegistry(audit_logger)
        
        # Replay attempt should be blocked
        with pytest.raises(TokenAlreadyUsedError):
            registry2.consume(
                confirmation=confirmation,
                submitter_id="attacker",
            )
    
    def test_reconstruct_from_audit(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """Registry can be reconstructed from audit log."""
        # Create first registry and consume multiple confirmations
        registry1 = ConfirmationRegistry(audit_logger)
        confirmations = [make_confirmation() for _ in range(5)]
        for conf in confirmations:
            registry1.consume(
                confirmation=conf,
                submitter_id="test-submitter",
            )
        
        # Create new registry and reconstruct
        registry2 = ConfirmationRegistry(audit_logger)
        count = registry2.reconstruct_from_audit()
        
        assert count == 5
        for conf in confirmations:
            assert registry2.is_used(conf.confirmation_id)


class TestValidateAndConsume:
    """Tests for the validate_and_consume method."""
    
    def test_validate_and_consume_success(
        self,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Valid confirmation should be consumed successfully."""
        used = registry.validate_and_consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
        )
        
        assert used.confirmation_id == sample_confirmation.confirmation_id
        assert registry.is_used(sample_confirmation.confirmation_id)
    
    def test_validate_and_consume_expired_raises(
        self,
        registry: ConfirmationRegistry,
        expired_confirmation: SubmissionConfirmation,
    ) -> None:
        """Expired confirmation should raise TokenExpiredError."""
        with pytest.raises(TokenExpiredError) as exc_info:
            registry.validate_and_consume(
                confirmation=expired_confirmation,
                submitter_id="test-submitter",
            )
        
        assert exc_info.value.token_id == expired_confirmation.confirmation_id
    
    def test_validate_and_consume_replay_raises(
        self,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Replay attempt should raise TokenAlreadyUsedError."""
        # First use
        registry.validate_and_consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
        )
        
        # Replay
        with pytest.raises(TokenAlreadyUsedError):
            registry.validate_and_consume(
                confirmation=sample_confirmation,
                submitter_id="test-submitter",
            )


class TestAuditIntegration:
    """Tests for audit log integration."""
    
    def test_consume_creates_audit_entry(
        self,
        audit_logger: SubmissionAuditLogger,
        registry: ConfirmationRegistry,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Consuming a confirmation should create an audit entry."""
        registry.consume(
            confirmation=sample_confirmation,
            submitter_id="test-submitter",
        )
        
        # Check audit log
        entry = audit_logger.find_confirmation_used(
            sample_confirmation.confirmation_id
        )
        assert entry is not None
        assert entry.action == SubmissionAction.CONFIRMATION_CONSUMED
        assert entry.confirmation_id == sample_confirmation.confirmation_id
        assert entry.request_id == sample_confirmation.request_id
    
    def test_audit_chain_integrity_maintained(
        self,
        audit_logger: SubmissionAuditLogger,
        registry: ConfirmationRegistry,
    ) -> None:
        """Audit chain integrity should be maintained."""
        # Consume multiple confirmations
        for _ in range(5):
            conf = make_confirmation()
            registry.consume(
                confirmation=conf,
                submitter_id="test-submitter",
            )
        
        # Verify chain integrity
        assert audit_logger.verify_integrity()


class TestPropertyBased:
    """Property-based tests for ConfirmationRegistry."""
    
    @given(
        confirmation_ids=st.lists(
            st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
            min_size=1,
            max_size=10,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_property_each_confirmation_used_once(
        self,
        confirmation_ids: list[str],
    ) -> None:
        """
        Property: Each confirmation can only be used once.
        
        Feature: human-authorized-submission, Property 11: One Confirmation Per Request
        Validates: Requirements 4.2, 4.7
        """
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        
        for conf_id in confirmation_ids:
            confirmation = make_confirmation(confirmation_id=conf_id)
            
            # First use should succeed
            registry.consume(
                confirmation=confirmation,
                submitter_id="test-submitter",
            )
            
            # Second use should fail
            with pytest.raises(TokenAlreadyUsedError):
                registry.consume(
                    confirmation=confirmation,
                    submitter_id="test-submitter",
                )
    
    @given(
        num_confirmations=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_property_registry_length_matches_consumed(
        self,
        num_confirmations: int,
    ) -> None:
        """
        Property: Registry length equals number of consumed confirmations.
        """
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        
        for _ in range(num_confirmations):
            confirmation = make_confirmation()
            registry.consume(
                confirmation=confirmation,
                submitter_id="test-submitter",
            )
        
        assert len(registry) == num_confirmations
    
    @given(
        num_replay_attempts=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_property_all_replay_attempts_logged(
        self,
        num_replay_attempts: int,
    ) -> None:
        """
        Property: All replay attempts are logged to audit trail.
        """
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        
        confirmation = make_confirmation()
        
        # First use succeeds
        registry.consume(
            confirmation=confirmation,
            submitter_id="test-submitter",
        )
        
        # All replay attempts should be logged
        for i in range(num_replay_attempts):
            with pytest.raises(TokenAlreadyUsedError):
                registry.consume(
                    confirmation=confirmation,
                    submitter_id=f"attacker-{i}",
                )
        
        replay_entries = audit_logger.find_replay_attempts(
            confirmation.confirmation_id
        )
        assert len(replay_entries) == num_replay_attempts
