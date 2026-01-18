"""
Phase-7 Submission Audit Logger Tests

Tests for the SubmissionAuditLogger that ensures:
- Append-only audit log with SHA-256 hash chain
- HARD STOP on audit failure
- Separate from Phase-6 audit log

Feature: human-authorized-submission, Property 5: Audit Chain Integrity
Validates: Requirements 5.5, 5.6
"""

from __future__ import annotations
from datetime import datetime
import uuid

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from submission_workflow.types import (
    SubmissionAction,
    SubmissionAuditEntry,
    Platform,
)
from submission_workflow.errors import AuditLogFailure
from submission_workflow.audit import (
    SubmissionAuditLogger,
    create_audit_entry,
)


class TestSubmissionAuditLoggerBasic:
    """Basic functionality tests for SubmissionAuditLogger."""
    
    def test_new_logger_is_empty(self) -> None:
        """A new logger should have no entries."""
        logger = SubmissionAuditLogger()
        assert len(logger) == 0
        assert logger.get_chain() == []
    
    def test_log_entry_adds_to_chain(self) -> None:
        """Logging an entry should add it to the chain."""
        logger = SubmissionAuditLogger()
        entry = create_audit_entry(
            submitter_id="test-submitter",
            action=SubmissionAction.REQUEST_CREATED,
        )
        
        logged = logger.log(entry)
        
        assert len(logger) == 1
        assert logged.entry_id == entry.entry_id
        assert logged.entry_hash is not None
    
    def test_first_entry_has_no_previous_hash(self) -> None:
        """First entry should have no previous hash."""
        logger = SubmissionAuditLogger()
        entry = create_audit_entry(
            submitter_id="test-submitter",
            action=SubmissionAction.REQUEST_CREATED,
        )
        
        logged = logger.log(entry)
        
        assert logged.previous_hash is None
    
    def test_subsequent_entries_have_previous_hash(self) -> None:
        """Subsequent entries should have previous hash."""
        logger = SubmissionAuditLogger()
        
        entry1 = create_audit_entry(
            submitter_id="test-submitter",
            action=SubmissionAction.REQUEST_CREATED,
        )
        logged1 = logger.log(entry1)
        
        entry2 = create_audit_entry(
            submitter_id="test-submitter",
            action=SubmissionAction.CONFIRMED,
        )
        logged2 = logger.log(entry2)
        
        assert logged2.previous_hash == logged1.entry_hash


class TestHashChainIntegrity:
    """Tests for hash chain integrity."""
    
    def test_verify_integrity_empty_log(self) -> None:
        """Empty log should have valid integrity."""
        logger = SubmissionAuditLogger()
        assert logger.verify_integrity()
    
    def test_verify_integrity_single_entry(self) -> None:
        """Single entry log should have valid integrity."""
        logger = SubmissionAuditLogger()
        entry = create_audit_entry(
            submitter_id="test-submitter",
            action=SubmissionAction.REQUEST_CREATED,
        )
        logger.log(entry)
        
        assert logger.verify_integrity()
    
    def test_verify_integrity_multiple_entries(self) -> None:
        """Multiple entry log should have valid integrity."""
        logger = SubmissionAuditLogger()
        
        for action in [
            SubmissionAction.REQUEST_CREATED,
            SubmissionAction.CONFIRMED,
            SubmissionAction.NETWORK_ACCESS_GRANTED,
            SubmissionAction.TRANSMITTED,
        ]:
            entry = create_audit_entry(
                submitter_id="test-submitter",
                action=action,
            )
            logger.log(entry)
        
        assert logger.verify_integrity()
    
    def test_hash_chain_links_entries(self) -> None:
        """Hash chain should link all entries."""
        logger = SubmissionAuditLogger()
        
        entries = []
        for i in range(5):
            entry = create_audit_entry(
                submitter_id="test-submitter",
                action=SubmissionAction.REQUEST_CREATED,
            )
            logged = logger.log(entry)
            entries.append(logged)
        
        # Verify chain links
        for i in range(1, len(entries)):
            assert entries[i].previous_hash == entries[i - 1].entry_hash


class TestAuditLogFailure:
    """Tests for audit log failure handling."""
    
    def test_fail_on_write_raises_audit_log_failure(self) -> None:
        """Simulated write failure should raise AuditLogFailure."""
        logger = SubmissionAuditLogger(fail_on_write=True)
        entry = create_audit_entry(
            submitter_id="test-submitter",
            action=SubmissionAction.REQUEST_CREATED,
        )
        
        with pytest.raises(AuditLogFailure) as exc_info:
            logger.log(entry)
        
        assert "Simulated write failure" in str(exc_info.value.original_error)
    
    def test_callback_failure_raises_audit_log_failure(self) -> None:
        """Callback failure should raise AuditLogFailure."""
        def failing_callback(entry: SubmissionAuditEntry) -> None:
            raise RuntimeError("Callback failed")
        
        logger = SubmissionAuditLogger(write_callback=failing_callback)
        entry = create_audit_entry(
            submitter_id="test-submitter",
            action=SubmissionAction.REQUEST_CREATED,
        )
        
        with pytest.raises(AuditLogFailure) as exc_info:
            logger.log(entry)
        
        assert "Callback failed" in str(exc_info.value.original_error)


class TestAuditQueries:
    """Tests for audit log query methods."""
    
    def test_find_confirmation_used(self) -> None:
        """Should find confirmation consumed entry."""
        logger = SubmissionAuditLogger()
        
        confirmation_id = str(uuid.uuid4())
        entry = create_audit_entry(
            submitter_id="test-submitter",
            action=SubmissionAction.CONFIRMATION_CONSUMED,
            confirmation_id=confirmation_id,
        )
        logger.log(entry)
        
        found = logger.find_confirmation_used(confirmation_id)
        assert found is not None
        assert found.confirmation_id == confirmation_id
    
    def test_find_confirmation_used_not_found(self) -> None:
        """Should return None if confirmation not found."""
        logger = SubmissionAuditLogger()
        
        found = logger.find_confirmation_used("nonexistent")
        assert found is None
    
    def test_find_replay_attempts(self) -> None:
        """Should find all replay attempt entries."""
        logger = SubmissionAuditLogger()
        
        confirmation_id = str(uuid.uuid4())
        
        # Log multiple replay attempts
        for _ in range(3):
            entry = create_audit_entry(
                submitter_id="attacker",
                action=SubmissionAction.CONFIRMATION_REPLAY_BLOCKED,
                confirmation_id=confirmation_id,
            )
            logger.log(entry)
        
        attempts = logger.find_replay_attempts(confirmation_id)
        assert len(attempts) == 3


class TestPropertyBased:
    """Property-based tests for SubmissionAuditLogger."""
    
    @given(
        num_entries=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_property_audit_chain_integrity(
        self,
        num_entries: int,
    ) -> None:
        """
        Property: Audit chain integrity is always maintained.
        
        Feature: human-authorized-submission, Property 5: Audit Chain Integrity
        Validates: Requirements 5.5, 5.6
        """
        logger = SubmissionAuditLogger()
        
        for _ in range(num_entries):
            entry = create_audit_entry(
                submitter_id="test-submitter",
                action=SubmissionAction.REQUEST_CREATED,
            )
            logger.log(entry)
        
        assert logger.verify_integrity()
        assert len(logger) == num_entries
    
    @given(
        num_entries=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_property_audit_log_append_only(
        self,
        num_entries: int,
    ) -> None:
        """
        Property: Audit log length only increases (append-only).
        
        Feature: human-authorized-submission, Property 5: Audit Chain Integrity
        Validates: Requirements 5.5, 5.6
        """
        logger = SubmissionAuditLogger()
        
        previous_length = 0
        for i in range(num_entries):
            entry = create_audit_entry(
                submitter_id="test-submitter",
                action=SubmissionAction.REQUEST_CREATED,
            )
            logger.log(entry)
            
            current_length = len(logger)
            assert current_length > previous_length
            previous_length = current_length
