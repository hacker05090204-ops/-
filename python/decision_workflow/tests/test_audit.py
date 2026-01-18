"""
Tests for Phase-6 Audit Logger.

Feature: human-decision-workflow
Property 3: Audit Entry Completeness
Property 4: Audit Chain Integrity
Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from datetime import datetime
import uuid

from decision_workflow.types import (
    Role,
    DecisionType,
    Severity,
    AuditEntry,
)
from decision_workflow.audit import AuditLogger, create_audit_entry
from decision_workflow.errors import AuditLogFailure


# ============================================================================
# Unit Tests
# ============================================================================

class TestAuditLoggerBasic:
    """Basic unit tests for AuditLogger."""
    
    def test_empty_log_is_valid(self):
        """Empty audit log should be valid."""
        logger = AuditLogger()
        assert len(logger) == 0
        assert logger.verify_integrity() is True
    
    def test_log_single_entry(self):
        """Should be able to log a single entry."""
        logger = AuditLogger()
        entry = create_audit_entry(
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="TEST",
        )
        
        logged = logger.log(entry)
        
        assert len(logger) == 1
        assert logged.entry_hash is not None
        assert logged.previous_hash is None  # First entry
    
    def test_log_multiple_entries_creates_chain(self):
        """Multiple entries should form a hash chain."""
        logger = AuditLogger()
        
        entry1 = create_audit_entry(
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="ACTION1",
        )
        entry2 = create_audit_entry(
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="ACTION2",
        )
        
        logged1 = logger.log(entry1)
        logged2 = logger.log(entry2)
        
        assert len(logger) == 2
        assert logged1.previous_hash is None
        assert logged2.previous_hash == logged1.entry_hash
    
    def test_get_chain_returns_all_entries(self):
        """get_chain should return all entries."""
        logger = AuditLogger()
        
        for i in range(5):
            entry = create_audit_entry(
                session_id="s1",
                reviewer_id="r1",
                role=Role.OPERATOR,
                action=f"ACTION{i}",
            )
            logger.log(entry)
        
        chain = logger.get_chain()
        assert len(chain) == 5
    
    def test_verify_integrity_valid_chain(self):
        """Valid chain should pass integrity check."""
        logger = AuditLogger()
        
        for i in range(10):
            entry = create_audit_entry(
                session_id="s1",
                reviewer_id="r1",
                role=Role.OPERATOR,
                action=f"ACTION{i}",
            )
            logger.log(entry)
        
        assert logger.verify_integrity() is True
    
    def test_audit_log_failure_on_write(self):
        """Should raise AuditLogFailure when write fails."""
        logger = AuditLogger(fail_on_write=True)
        entry = create_audit_entry(
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="TEST",
        )
        
        with pytest.raises(AuditLogFailure) as exc_info:
            logger.log(entry)
        
        assert "Audit log write failed" in str(exc_info.value)
    
    def test_audit_log_failure_on_callback(self):
        """Should raise AuditLogFailure when callback fails."""
        def failing_callback(entry):
            raise RuntimeError("Callback failed")
        
        logger = AuditLogger(write_callback=failing_callback)
        entry = create_audit_entry(
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="TEST",
        )
        
        with pytest.raises(AuditLogFailure) as exc_info:
            logger.log(entry)
        
        assert "callback failed" in str(exc_info.value).lower()
    
    def test_get_entries_for_session(self):
        """Should filter entries by session."""
        logger = AuditLogger()
        
        # Log entries for different sessions
        for session_id in ["s1", "s2", "s1", "s2", "s1"]:
            entry = create_audit_entry(
                session_id=session_id,
                reviewer_id="r1",
                role=Role.OPERATOR,
                action="TEST",
            )
            logger.log(entry)
        
        s1_entries = logger.get_entries_for_session("s1")
        s2_entries = logger.get_entries_for_session("s2")
        
        assert len(s1_entries) == 3
        assert len(s2_entries) == 2
    
    def test_get_entries_for_finding(self):
        """Should filter entries by finding."""
        logger = AuditLogger()
        
        # Log entries for different findings
        for finding_id in ["f1", "f2", "f1"]:
            entry = create_audit_entry(
                session_id="s1",
                reviewer_id="r1",
                role=Role.OPERATOR,
                action="TEST",
                finding_id=finding_id,
            )
            logger.log(entry)
        
        f1_entries = logger.get_entries_for_finding("f1")
        f2_entries = logger.get_entries_for_finding("f2")
        
        assert len(f1_entries) == 2
        assert len(f2_entries) == 1
    
    def test_count_decisions_for_session(self):
        """Should count DECISION actions for a session."""
        logger = AuditLogger()
        
        # Log various actions
        actions = ["DECISION", "VIEW", "DECISION", "PERMISSION_DENIED", "DECISION"]
        for action in actions:
            entry = create_audit_entry(
                session_id="s1",
                reviewer_id="r1",
                role=Role.OPERATOR,
                action=action,
            )
            logger.log(entry)
        
        count = logger.count_decisions_for_session("s1")
        assert count == 3


# ============================================================================
# Property Tests
# ============================================================================

class TestAuditChainIntegrity:
    """
    Feature: human-decision-workflow, Property 4: Audit Chain Integrity
    
    For any AuditEntry after the first, the entry SHALL contain a previous_hash
    field equal to the entry_hash of the immediately preceding entry.
    The audit log length SHALL only increase (append-only).
    
    Validates: Requirements 4.4, 4.5
    """
    
    @given(
        num_entries=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_chain_integrity_property(self, num_entries: int):
        """
        Property 4: Audit Chain Integrity
        For any sequence of entries, the hash chain should be valid.
        """
        logger = AuditLogger()
        
        for i in range(num_entries):
            entry = create_audit_entry(
                session_id=f"s{i % 3}",
                reviewer_id=f"r{i % 2}",
                role=Role.OPERATOR if i % 2 == 0 else Role.REVIEWER,
                action=f"ACTION{i}",
            )
            logger.log(entry)
        
        # Chain should be valid
        assert logger.verify_integrity() is True
        
        # Length should match
        assert len(logger) == num_entries
    
    @given(
        num_entries=st.integers(min_value=2, max_value=20),
    )
    @settings(max_examples=100)
    def test_previous_hash_links_to_previous_entry(self, num_entries: int):
        """
        Property 4: Audit Chain Integrity - Previous Hash
        Each entry's previous_hash should equal the previous entry's entry_hash.
        """
        logger = AuditLogger()
        
        for i in range(num_entries):
            entry = create_audit_entry(
                session_id="s1",
                reviewer_id="r1",
                role=Role.OPERATOR,
                action=f"ACTION{i}",
            )
            logger.log(entry)
        
        chain = logger.get_chain()
        
        # First entry has no previous hash
        assert chain[0].previous_hash is None
        
        # All subsequent entries link to previous
        for i in range(1, len(chain)):
            assert chain[i].previous_hash == chain[i - 1].entry_hash
    
    @given(
        num_entries=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_append_only_length_increases(self, num_entries: int):
        """
        Property 4: Audit Chain Integrity - Append Only
        Log length should only increase, never decrease.
        """
        logger = AuditLogger()
        previous_length = 0
        
        for i in range(num_entries):
            entry = create_audit_entry(
                session_id="s1",
                reviewer_id="r1",
                role=Role.OPERATOR,
                action=f"ACTION{i}",
            )
            logger.log(entry)
            
            current_length = len(logger)
            assert current_length > previous_length
            previous_length = current_length


class TestAuditEntryCompleteness:
    """
    Feature: human-decision-workflow, Property 3: Audit Entry Completeness
    
    For any HumanDecision created, the corresponding AuditEntry SHALL contain:
    decision_id, finding_id, reviewer_id, decision_type, timestamp,
    and (if present) severity and rationale.
    
    Validates: Requirements 4.1, 4.2, 4.3
    """
    
    @given(
        session_id=st.uuids().map(str),
        reviewer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
        finding_id=st.uuids().map(str),
        decision_id=st.uuids().map(str),
        decision_type=st.sampled_from(DecisionType),
    )
    @settings(max_examples=100)
    def test_audit_entry_contains_required_fields(
        self,
        session_id: str,
        reviewer_id: str,
        finding_id: str,
        decision_id: str,
        decision_type: DecisionType,
    ):
        """
        Property 3: Audit Entry Completeness - Required Fields
        Audit entry should contain all required fields.
        """
        logger = AuditLogger()
        
        entry = create_audit_entry(
            session_id=session_id,
            reviewer_id=reviewer_id,
            role=Role.REVIEWER,
            action="DECISION",
            finding_id=finding_id,
            decision_id=decision_id,
            decision_type=decision_type,
        )
        
        logged = logger.log(entry)
        
        # Required fields
        assert logged.session_id == session_id
        assert logged.reviewer_id == reviewer_id
        assert logged.finding_id == finding_id
        assert logged.decision_id == decision_id
        assert logged.decision_type == decision_type
        assert logged.timestamp is not None
        assert logged.entry_id is not None
    
    @given(
        severity=st.sampled_from(Severity),
    )
    @settings(max_examples=100)
    def test_audit_entry_contains_severity_when_present(self, severity: Severity):
        """
        Property 3: Audit Entry Completeness - Severity
        When severity is present, audit entry should contain it.
        """
        logger = AuditLogger()
        
        entry = create_audit_entry(
            session_id="s1",
            reviewer_id="r1",
            role=Role.REVIEWER,
            action="DECISION",
            finding_id="f1",
            decision_id="d1",
            decision_type=DecisionType.APPROVE,
            severity=severity,
        )
        
        logged = logger.log(entry)
        
        assert logged.severity == severity
    
    @given(
        rationale=st.text(min_size=1, max_size=500),
    )
    @settings(max_examples=100)
    def test_audit_entry_contains_rationale_when_present(self, rationale: str):
        """
        Property 3: Audit Entry Completeness - Rationale
        When rationale is present, audit entry should contain it.
        """
        logger = AuditLogger()
        
        entry = create_audit_entry(
            session_id="s1",
            reviewer_id="r1",
            role=Role.REVIEWER,
            action="DECISION",
            finding_id="f1",
            decision_id="d1",
            decision_type=DecisionType.REJECT,
            rationale=rationale,
        )
        
        logged = logger.log(entry)
        
        assert logged.rationale == rationale


class TestAuditLogFailure:
    """
    Tests for AuditLogFailure HARD STOP behavior.
    
    Validates: Requirements 4.6
    """
    
    def test_audit_log_failure_is_hard_stop(self):
        """AuditLogFailure should be raised and halt operations."""
        logger = AuditLogger(fail_on_write=True)
        entry = create_audit_entry(
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="TEST",
        )
        
        with pytest.raises(AuditLogFailure):
            logger.log(entry)
        
        # Log should be empty (write failed)
        assert len(logger) == 0
    
    def test_audit_log_failure_contains_original_error(self):
        """AuditLogFailure should contain the original error."""
        def failing_callback(entry):
            raise ValueError("Original error message")
        
        logger = AuditLogger(write_callback=failing_callback)
        entry = create_audit_entry(
            session_id="s1",
            reviewer_id="r1",
            role=Role.OPERATOR,
            action="TEST",
        )
        
        with pytest.raises(AuditLogFailure) as exc_info:
            logger.log(entry)
        
        assert exc_info.value.original_error is not None
        assert "Original error message" in str(exc_info.value.original_error)
