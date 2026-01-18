# PHASE-12 GOVERNANCE COMPLIANCE
# This module is part of Phase-12 (Runtime Orchestration Implementation)
#
# FORBIDDEN CAPABILITIES:
# - NO execution logic
# - NO decision logic
# - NO submission logic
# - NO network access
# - NO browser automation
# - NO friction wiring or execution
# - NO auto-approval
# - NO frozen phase modification
#
# MANDATORY DECLARATION:
# Phase-12 implements orchestration without altering execution,
# human authority, governance friction, or audit invariants.

"""
Phase-12 Track 2 Audit Layer Tests

TEST CATEGORY: Per-Track Tests - Track 2 (Priority: MEDIUM)
EXECUTION ORDER: 4 (After Property Tests)

Test IDs:
- TEST-T2-001: Audit log is append-only
- TEST-T2-002: Hash chain integrity is maintained
- TEST-T2-003: No writes to other phase audit logs
- TEST-T2-004: Broken hash chain raises AuditIntegrityError
- TEST-T2-005: Audit entries are immutable
"""

import ast
from dataclasses import FrozenInstanceError
from datetime import datetime
from pathlib import Path

import pytest

from orchestration_layer.audit import (
    GENESIS_HASH,
    compute_entry_hash,
    create_audit_entry,
    get_chain_integrity_status,
    verify_hash_chain,
)
from orchestration_layer.errors import AuditIntegrityError
from orchestration_layer.types import OrchestrationAuditEntry, OrchestrationEventType


@pytest.mark.track2
class TestAuditLogAppendOnly:
    """Test ID: TEST-T2-001 - Requirement: REQ-3.4.4"""
    
    def test_audit_log_append_only(self):
        """Verify audit log only supports append operations."""
        # Create first entry with genesis hash
        entry1 = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={"action": "create"},
            previous_hash=GENESIS_HASH
        )
        
        # Create second entry linked to first
        entry2 = create_audit_entry(
            event_type=OrchestrationEventType.STATE_TRANSITION,
            workflow_id="wf-001",
            details={"from": "initialized", "to": "awaiting_human"},
            previous_hash=entry1.entry_hash
        )
        
        # Verify entries are created (append works)
        assert entry1.entry_id is not None
        assert entry2.entry_id is not None
        assert entry2.previous_hash == entry1.entry_hash
    
    def test_no_delete_operation(self):
        """Verify audit log does not support delete operations."""
        # The audit module only provides create_audit_entry
        # There is no delete function - verify by checking module contents
        import orchestration_layer.audit as audit_module
        
        # Check that no delete-related functions exist
        module_attrs = dir(audit_module)
        forbidden_delete_names = [
            "delete_audit_entry",
            "remove_audit_entry",
            "delete_entry",
            "remove_entry",
            "clear_audit_log",
            "truncate_audit_log"
        ]
        
        for name in forbidden_delete_names:
            assert name not in module_attrs, f"Forbidden delete function found: {name}"
    
    def test_no_update_operation(self):
        """Verify audit log does not support update operations."""
        # The audit module only provides create_audit_entry
        # There is no update function - verify by checking module contents
        import orchestration_layer.audit as audit_module
        
        # Check that no update-related functions exist
        module_attrs = dir(audit_module)
        forbidden_update_names = [
            "update_audit_entry",
            "modify_audit_entry",
            "edit_audit_entry",
            "update_entry",
            "modify_entry"
        ]
        
        for name in forbidden_update_names:
            assert name not in module_attrs, f"Forbidden update function found: {name}"


@pytest.mark.track2
class TestHashChainIntegrity:
    """Test ID: TEST-T2-002 - Requirement: INV-5.2.2"""
    
    def test_hash_chain_maintained(self):
        """Verify hash chain integrity is maintained on append."""
        # Create a chain of entries
        entry1 = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={"action": "create"},
            previous_hash=GENESIS_HASH
        )
        
        entry2 = create_audit_entry(
            event_type=OrchestrationEventType.STATE_TRANSITION,
            workflow_id="wf-001",
            details={"from": "initialized", "to": "awaiting_human"},
            previous_hash=entry1.entry_hash
        )
        
        entry3 = create_audit_entry(
            event_type=OrchestrationEventType.HUMAN_CONFIRMATION_RECEIVED,
            workflow_id="wf-001",
            details={"token": "confirmed"},
            previous_hash=entry2.entry_hash
        )
        
        # Verify chain is valid
        entries = [entry1, entry2, entry3]
        assert verify_hash_chain(entries) is True
    
    def test_previous_hash_links_correctly(self):
        """Verify previous_hash links to prior entry's entry_hash."""
        entry1 = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={},
            previous_hash=GENESIS_HASH
        )
        
        entry2 = create_audit_entry(
            event_type=OrchestrationEventType.STATE_TRANSITION,
            workflow_id="wf-001",
            details={},
            previous_hash=entry1.entry_hash
        )
        
        # Verify linkage
        assert entry1.previous_hash == GENESIS_HASH
        assert entry2.previous_hash == entry1.entry_hash
        assert entry2.previous_hash != GENESIS_HASH
    
    def test_hash_is_deterministic(self):
        """Verify hash computation is deterministic."""
        timestamp = datetime(2026, 1, 3, 12, 0, 0)
        
        hash1 = compute_entry_hash(
            entry_id="test-id",
            timestamp=timestamp,
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={"key": "value"},
            previous_hash=GENESIS_HASH
        )
        
        hash2 = compute_entry_hash(
            entry_id="test-id",
            timestamp=timestamp,
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={"key": "value"},
            previous_hash=GENESIS_HASH
        )
        
        assert hash1 == hash2
    
    def test_empty_chain_is_valid(self):
        """Verify empty chain is considered valid."""
        assert verify_hash_chain([]) is True


@pytest.mark.track2
class TestNoWritesToOtherPhases:
    """Test ID: TEST-T2-003 - Requirement: REQ-3.4.5"""
    
    def test_no_writes_to_other_phase_audit_logs(self):
        """Verify no writes to other phase audit logs."""
        # Verify by AST inspection that audit.py does not import
        # or reference other phase audit modules
        audit_path = Path(__file__).parent.parent / "audit.py"
        
        with open(audit_path, "r") as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        # Check imports for forbidden phase references
        forbidden_imports = [
            "execution_layer",
            "decision_workflow",
            "submission_workflow",
            "intelligence_layer",
            "browser_assistant",
            "governance_friction",
            "bounty_pipeline"
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forbidden in forbidden_imports:
                        assert forbidden not in alias.name, \
                            f"Forbidden import found: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for forbidden in forbidden_imports:
                        assert forbidden not in node.module, \
                            f"Forbidden import found: {node.module}"
    
    def test_no_cross_phase_write_functions(self):
        """Verify no functions that write to other phases exist."""
        import orchestration_layer.audit as audit_module
        
        module_attrs = dir(audit_module)
        
        # Check for forbidden cross-phase write patterns
        forbidden_patterns = [
            "write_to_phase",
            "update_phase",
            "modify_phase",
            "sync_to_phase",
            "push_to_phase"
        ]
        
        for attr in module_attrs:
            for pattern in forbidden_patterns:
                assert pattern not in attr.lower(), \
                    f"Forbidden cross-phase write function found: {attr}"


@pytest.mark.track2
class TestBrokenHashChainError:
    """Test ID: TEST-T2-004 - Requirement: INV-5.2.4"""
    
    def test_broken_hash_chain_raises_error(self):
        """Verify broken hash chain raises AuditIntegrityError."""
        # Create valid entries
        entry1 = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={},
            previous_hash=GENESIS_HASH
        )
        
        entry2 = create_audit_entry(
            event_type=OrchestrationEventType.STATE_TRANSITION,
            workflow_id="wf-001",
            details={},
            previous_hash=entry1.entry_hash
        )
        
        # Create a tampered entry with wrong previous_hash
        tampered_entry = OrchestrationAuditEntry(
            entry_id=entry2.entry_id,
            timestamp=entry2.timestamp,
            event_type=entry2.event_type,
            workflow_id=entry2.workflow_id,
            details=entry2.details,
            previous_hash="wrong_hash_value",  # TAMPERED
            entry_hash=entry2.entry_hash
        )
        
        # Verify broken chain raises error
        with pytest.raises(AuditIntegrityError):
            verify_hash_chain([entry1, tampered_entry])
    
    def test_tampered_entry_hash_raises_error(self):
        """Verify tampered entry_hash raises AuditIntegrityError."""
        entry1 = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={},
            previous_hash=GENESIS_HASH
        )
        
        # Create entry with tampered entry_hash
        tampered_entry = OrchestrationAuditEntry(
            entry_id=entry1.entry_id,
            timestamp=entry1.timestamp,
            event_type=entry1.event_type,
            workflow_id=entry1.workflow_id,
            details=entry1.details,
            previous_hash=entry1.previous_hash,
            entry_hash="tampered_hash_value"  # TAMPERED
        )
        
        with pytest.raises(AuditIntegrityError):
            verify_hash_chain([tampered_entry])
    
    def test_chain_integrity_status_reports_error(self):
        """Verify get_chain_integrity_status reports errors correctly."""
        entry1 = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={},
            previous_hash=GENESIS_HASH
        )
        
        # Create tampered entry
        tampered_entry = OrchestrationAuditEntry(
            entry_id="tampered-id",
            timestamp=entry1.timestamp,
            event_type=entry1.event_type,
            workflow_id=entry1.workflow_id,
            details=entry1.details,
            previous_hash=entry1.entry_hash,
            entry_hash="wrong_hash"
        )
        
        status = get_chain_integrity_status([entry1, tampered_entry])
        
        assert status["is_valid"] is False
        assert status["error"] is not None
        assert "hash mismatch" in status["error"]


@pytest.mark.track2
class TestAuditEntryImmutability:
    """Test ID: TEST-T2-005 - Requirement: REQ-3.4.2"""
    
    def test_audit_entries_are_immutable(self):
        """Verify audit entries are immutable."""
        entry = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={"key": "value"},
            previous_hash=GENESIS_HASH
        )
        
        # Attempt to modify should raise FrozenInstanceError
        with pytest.raises(FrozenInstanceError):
            entry.workflow_id = "modified"
        
        with pytest.raises(FrozenInstanceError):
            entry.entry_hash = "modified"
        
        with pytest.raises(FrozenInstanceError):
            entry.previous_hash = "modified"
    
    def test_audit_entry_human_confirmation_required(self):
        """Verify audit entries have human_confirmation_required=True."""
        entry = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={},
            previous_hash=GENESIS_HASH
        )
        
        assert entry.human_confirmation_required is True
    
    def test_audit_entry_no_auto_action(self):
        """Verify audit entries have no_auto_action=True."""
        entry = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={},
            previous_hash=GENESIS_HASH
        )
        
        assert entry.no_auto_action is True


@pytest.mark.track2
class TestChainIntegrityStatus:
    """Additional tests for get_chain_integrity_status function."""
    
    def test_valid_chain_status(self):
        """Verify status for valid chain."""
        entry1 = create_audit_entry(
            event_type=OrchestrationEventType.WORKFLOW_CREATED,
            workflow_id="wf-001",
            details={},
            previous_hash=GENESIS_HASH
        )
        
        entry2 = create_audit_entry(
            event_type=OrchestrationEventType.STATE_TRANSITION,
            workflow_id="wf-001",
            details={},
            previous_hash=entry1.entry_hash
        )
        
        status = get_chain_integrity_status([entry1, entry2])
        
        assert status["is_valid"] is True
        assert status["entry_count"] == 2
        assert status["first_entry_id"] == entry1.entry_id
        assert status["last_entry_id"] == entry2.entry_id
        assert status["error"] is None
    
    def test_empty_chain_status(self):
        """Verify status for empty chain."""
        status = get_chain_integrity_status([])
        
        assert status["is_valid"] is True
        assert status["entry_count"] == 0
        assert status["first_entry_id"] is None
        assert status["last_entry_id"] is None
        assert status["error"] is None
