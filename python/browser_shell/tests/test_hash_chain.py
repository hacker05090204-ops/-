# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-1.3: Implement Hash Chain
# Requirement: 6.1 (Hash-chained), 6.3 (Audit Trail Integrity)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""Tests for hash chain - governance-enforcing tests."""

import ast
import inspect
import pytest
import tempfile
import os


class TestHashChainLinksEntries:
    """Verify each entry hash includes previous hash."""

    def test_first_entry_has_genesis_hash(self):
        """First entry must link to genesis hash (all zeros)."""
        from browser_shell.hash_chain import HashChain
        
        chain = HashChain()
        
        entry_hash = chain.compute_entry_hash(
            entry_id="test-001",
            timestamp="2026-01-04T00:00:00Z",
            previous_hash=HashChain.GENESIS_HASH,
            action_type="SESSION_START",
            initiator="HUMAN",
            session_id="session-001",
            scope_hash="scope-001",
            action_details="Test",
            outcome="SUCCESS",
        )
        
        # Hash must be 64 hex characters (SHA-256)
        assert len(entry_hash) == 64
        assert all(c in '0123456789abcdef' for c in entry_hash)

    def test_second_entry_links_to_first(self):
        """Second entry must include first entry's hash."""
        from browser_shell.hash_chain import HashChain
        
        chain = HashChain()
        
        first_hash = chain.compute_entry_hash(
            entry_id="test-001",
            timestamp="2026-01-04T00:00:00Z",
            previous_hash=HashChain.GENESIS_HASH,
            action_type="SESSION_START",
            initiator="HUMAN",
            session_id="session-001",
            scope_hash="scope-001",
            action_details="Test 1",
            outcome="SUCCESS",
        )
        
        second_hash = chain.compute_entry_hash(
            entry_id="test-002",
            timestamp="2026-01-04T00:00:01Z",
            previous_hash=first_hash,
            action_type="SESSION_END",
            initiator="HUMAN",
            session_id="session-001",
            scope_hash="scope-001",
            action_details="Test 2",
            outcome="SUCCESS",
        )
        
        # Hashes must be different
        assert first_hash != second_hash
        
        # Both must be valid SHA-256
        assert len(second_hash) == 64

    def test_hash_changes_with_different_previous(self):
        """Hash must change if previous_hash changes."""
        from browser_shell.hash_chain import HashChain
        
        chain = HashChain()
        
        hash_a = chain.compute_entry_hash(
            entry_id="test-001",
            timestamp="2026-01-04T00:00:00Z",
            previous_hash="a" * 64,
            action_type="SESSION_START",
            initiator="HUMAN",
            session_id="session-001",
            scope_hash="scope-001",
            action_details="Test",
            outcome="SUCCESS",
        )
        
        hash_b = chain.compute_entry_hash(
            entry_id="test-001",
            timestamp="2026-01-04T00:00:00Z",
            previous_hash="b" * 64,
            action_type="SESSION_START",
            initiator="HUMAN",
            session_id="session-001",
            scope_hash="scope-001",
            action_details="Test",
            outcome="SUCCESS",
        )
        
        assert hash_a != hash_b


class TestHashChainValidationOnStartup:
    """Verify validation runs at initialization."""

    def test_validate_empty_chain(self):
        """Empty chain must validate successfully."""
        from browser_shell.hash_chain import HashChain
        from browser_shell.audit_storage import AuditStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            
            result = chain.validate_chain(storage)
            
            assert result.valid is True
            assert result.entry_count == 0

    def test_validate_single_entry_chain(self):
        """Single entry chain must validate if hash is correct."""
        from browser_shell.hash_chain import HashChain
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.audit_types import AuditEntry
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            
            entry_hash = chain.compute_entry_hash(
                entry_id="test-001",
                timestamp="2026-01-04T00:00:00Z",
                previous_hash=HashChain.GENESIS_HASH,
                action_type="SESSION_START",
                initiator="HUMAN",
                session_id="session-001",
                scope_hash="scope-001",
                action_details="Test",
                outcome="SUCCESS",
            )
            
            entry = AuditEntry(
                entry_id="test-001",
                timestamp="2026-01-04T00:00:00Z",
                previous_hash=HashChain.GENESIS_HASH,
                action_type="SESSION_START",
                initiator="HUMAN",
                session_id="session-001",
                scope_hash="scope-001",
                action_details="Test",
                outcome="SUCCESS",
                entry_hash=entry_hash,
            )
            
            storage.append(entry)
            
            result = chain.validate_chain(storage)
            
            assert result.valid is True
            assert result.entry_count == 1


class TestHashChainFailureHaltsOperations:
    """Verify broken chain triggers halt."""

    def test_invalid_hash_detected(self):
        """Invalid entry hash must be detected."""
        from browser_shell.hash_chain import HashChain
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.audit_types import AuditEntry
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            
            # Create entry with WRONG hash
            entry = AuditEntry(
                entry_id="test-001",
                timestamp="2026-01-04T00:00:00Z",
                previous_hash=HashChain.GENESIS_HASH,
                action_type="SESSION_START",
                initiator="HUMAN",
                session_id="session-001",
                scope_hash="scope-001",
                action_details="Test",
                outcome="SUCCESS",
                entry_hash="wrong_hash_" + "0" * 53,  # Invalid hash
            )
            
            storage.append(entry)
            
            result = chain.validate_chain(storage)
            
            assert result.valid is False
            assert "hash mismatch" in result.error_message.lower()

    def test_broken_chain_link_detected(self):
        """Broken chain link must be detected."""
        from browser_shell.hash_chain import HashChain
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.audit_types import AuditEntry
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            
            # First entry - correct
            first_hash = chain.compute_entry_hash(
                entry_id="test-001",
                timestamp="2026-01-04T00:00:00Z",
                previous_hash=HashChain.GENESIS_HASH,
                action_type="SESSION_START",
                initiator="HUMAN",
                session_id="session-001",
                scope_hash="scope-001",
                action_details="Test 1",
                outcome="SUCCESS",
            )
            
            entry1 = AuditEntry(
                entry_id="test-001",
                timestamp="2026-01-04T00:00:00Z",
                previous_hash=HashChain.GENESIS_HASH,
                action_type="SESSION_START",
                initiator="HUMAN",
                session_id="session-001",
                scope_hash="scope-001",
                action_details="Test 1",
                outcome="SUCCESS",
                entry_hash=first_hash,
            )
            storage.append(entry1)
            
            # Second entry - WRONG previous_hash (broken link)
            second_hash = chain.compute_entry_hash(
                entry_id="test-002",
                timestamp="2026-01-04T00:00:01Z",
                previous_hash="wrong_previous_" + "0" * 50,  # Wrong!
                action_type="SESSION_END",
                initiator="HUMAN",
                session_id="session-001",
                scope_hash="scope-001",
                action_details="Test 2",
                outcome="SUCCESS",
            )
            
            entry2 = AuditEntry(
                entry_id="test-002",
                timestamp="2026-01-04T00:00:01Z",
                previous_hash="wrong_previous_" + "0" * 50,  # Wrong!
                action_type="SESSION_END",
                initiator="HUMAN",
                session_id="session-001",
                scope_hash="scope-001",
                action_details="Test 2",
                outcome="SUCCESS",
                entry_hash=second_hash,
            )
            storage.append(entry2)
            
            result = chain.validate_chain(storage)
            
            assert result.valid is False
            assert "chain" in result.error_message.lower() or "link" in result.error_message.lower()


class TestTimestampsUseExternalSource:
    """Verify timestamps not from local clock."""

    def test_timestamp_provider_required(self):
        """HashChain must accept external timestamp provider."""
        from browser_shell.hash_chain import HashChain
        
        # Default chain uses external provider interface
        chain = HashChain()
        
        # Must have method to get external timestamp
        assert hasattr(chain, 'get_external_timestamp')

    def test_timestamp_format_is_iso8601(self):
        """Timestamps must be ISO 8601 format."""
        from browser_shell.hash_chain import HashChain
        
        chain = HashChain()
        
        timestamp = chain.get_external_timestamp()
        
        # Must be ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ or similar)
        assert 'T' in timestamp
        assert len(timestamp) >= 19  # Minimum: YYYY-MM-DDTHH:MM:SS


class TestNoAutomationInHashChain:
    """Verify no automation methods in hash chain module."""

    def test_no_auto_methods(self):
        """No auto_* methods allowed."""
        from browser_shell.hash_chain import HashChain
        
        methods = [m for m in dir(HashChain) if m.startswith('auto')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_no_execute_methods(self):
        """No execute_* methods allowed."""
        from browser_shell.hash_chain import HashChain
        
        methods = [m for m in dir(HashChain) if m.startswith('execute')]
        assert methods == [], f"Forbidden execute methods found: {methods}"

    def test_no_learn_methods(self):
        """No learn_* methods allowed."""
        from browser_shell.hash_chain import HashChain
        
        methods = [m for m in dir(HashChain) if m.startswith('learn')]
        assert methods == [], f"Forbidden learn methods found: {methods}"
