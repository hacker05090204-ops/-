# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-1.1: Define Audit Entry Types
# Requirement: 6.2 (Audit Trail Content)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""Tests for audit entry types - governance-enforcing tests."""

import ast
import inspect
import pytest
from dataclasses import FrozenInstanceError


class TestAuditEntryIsFrozen:
    """Verify AuditEntry cannot be modified after creation."""

    def test_audit_entry_is_frozen_dataclass(self):
        """AuditEntry must be a frozen dataclass."""
        from browser_shell.audit_types import AuditEntry
        
        # Verify it's a dataclass
        assert hasattr(AuditEntry, '__dataclass_fields__')
        
        # Verify frozen=True by attempting modification
        entry = AuditEntry(
            entry_id="test-001",
            timestamp="2026-01-04T00:00:00Z",
            previous_hash="0" * 64,
            action_type="SESSION_START",
            initiator="HUMAN",
            session_id="session-001",
            scope_hash="scope-hash-001",
            action_details="Test action",
            outcome="SUCCESS",
            entry_hash="a" * 64,
        )
        
        with pytest.raises(FrozenInstanceError):
            entry.entry_id = "modified"

    def test_audit_entry_hash_is_immutable(self):
        """Entry hash cannot be modified after creation."""
        from browser_shell.audit_types import AuditEntry
        
        entry = AuditEntry(
            entry_id="test-001",
            timestamp="2026-01-04T00:00:00Z",
            previous_hash="0" * 64,
            action_type="SESSION_START",
            initiator="HUMAN",
            session_id="session-001",
            scope_hash="scope-hash-001",
            action_details="Test action",
            outcome="SUCCESS",
            entry_hash="a" * 64,
        )
        
        with pytest.raises(FrozenInstanceError):
            entry.entry_hash = "b" * 64


class TestAuditEntryHasAllRequiredFields:
    """Verify all fields from Requirement 6.2 are present."""

    def test_all_required_fields_present(self):
        """AuditEntry must have all required fields per Requirement 6.2."""
        from browser_shell.audit_types import AuditEntry
        
        required_fields = {
            'entry_id',
            'timestamp',
            'previous_hash',
            'action_type',
            'initiator',
            'session_id',
            'scope_hash',
            'action_details',
            'outcome',
            'entry_hash',
        }
        
        actual_fields = set(AuditEntry.__dataclass_fields__.keys())
        
        assert required_fields.issubset(actual_fields), (
            f"Missing required fields: {required_fields - actual_fields}"
        )

    def test_field_types_are_strings(self):
        """All fields must be string types for serialization safety."""
        from browser_shell.audit_types import AuditEntry
        
        for field_name, field_info in AuditEntry.__dataclass_fields__.items():
            assert field_info.type == str, (
                f"Field {field_name} must be str, got {field_info.type}"
            )


class TestInitiatorEnumValues:
    """Verify HUMAN and SYSTEM are only valid initiator values."""

    def test_initiator_enum_has_human(self):
        """Initiator enum must have HUMAN value."""
        from browser_shell.audit_types import Initiator
        
        assert hasattr(Initiator, 'HUMAN')
        assert Initiator.HUMAN.value == "HUMAN"

    def test_initiator_enum_has_system(self):
        """Initiator enum must have SYSTEM value."""
        from browser_shell.audit_types import Initiator
        
        assert hasattr(Initiator, 'SYSTEM')
        assert Initiator.SYSTEM.value == "SYSTEM"

    def test_initiator_enum_has_only_two_values(self):
        """Initiator enum must have exactly HUMAN and SYSTEM."""
        from browser_shell.audit_types import Initiator
        
        values = [m.value for m in Initiator]
        assert set(values) == {"HUMAN", "SYSTEM"}, (
            f"Initiator must have exactly HUMAN and SYSTEM, got {values}"
        )


class TestActionTypeEnum:
    """Verify ActionType enum covers all action categories."""

    def test_action_type_enum_exists(self):
        """ActionType enum must exist."""
        from browser_shell.audit_types import ActionType
        
        assert ActionType is not None

    def test_action_type_has_session_actions(self):
        """ActionType must have session-related actions."""
        from browser_shell.audit_types import ActionType
        
        assert hasattr(ActionType, 'SESSION_START')
        assert hasattr(ActionType, 'SESSION_END')

    def test_action_type_has_scope_actions(self):
        """ActionType must have scope-related actions."""
        from browser_shell.audit_types import ActionType
        
        assert hasattr(ActionType, 'SCOPE_DEFINED')
        assert hasattr(ActionType, 'SCOPE_VALIDATED')
        assert hasattr(ActionType, 'SCOPE_VIOLATION')

    def test_action_type_has_evidence_actions(self):
        """ActionType must have evidence-related actions."""
        from browser_shell.audit_types import ActionType
        
        assert hasattr(ActionType, 'EVIDENCE_CAPTURED')
        assert hasattr(ActionType, 'EVIDENCE_BLOCKED')

    def test_action_type_has_decision_actions(self):
        """ActionType must have decision-related actions."""
        from browser_shell.audit_types import ActionType
        
        assert hasattr(ActionType, 'DECISION_POINT')
        assert hasattr(ActionType, 'CONFIRMATION_REQUIRED')
        assert hasattr(ActionType, 'CONFIRMATION_RECEIVED')

    def test_action_type_has_submission_actions(self):
        """ActionType must have submission-related actions."""
        from browser_shell.audit_types import ActionType
        
        assert hasattr(ActionType, 'SUBMISSION_STEP_1')
        assert hasattr(ActionType, 'SUBMISSION_STEP_2')
        assert hasattr(ActionType, 'SUBMISSION_STEP_3')

    def test_action_type_has_halt_actions(self):
        """ActionType must have halt-related actions."""
        from browser_shell.audit_types import ActionType
        
        assert hasattr(ActionType, 'HALT_TRIGGERED')
        assert hasattr(ActionType, 'RECOVERY_STARTED')


class TestNoExecutionMethods:
    """Static analysis confirms no execute_* methods."""

    def test_no_execute_methods_in_audit_entry(self):
        """AuditEntry must not have any execute_* methods."""
        from browser_shell.audit_types import AuditEntry
        
        methods = [m for m in dir(AuditEntry) if m.startswith('execute')]
        assert methods == [], f"Forbidden execute methods found: {methods}"

    def test_no_auto_methods_in_audit_entry(self):
        """AuditEntry must not have any auto_* methods."""
        from browser_shell.audit_types import AuditEntry
        
        methods = [m for m in dir(AuditEntry) if m.startswith('auto')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_no_automation_methods_in_module(self):
        """audit_types module must not have automation methods."""
        import browser_shell.audit_types as module
        
        source = inspect.getsource(module)
        tree = ast.parse(source)
        
        forbidden_prefixes = ['execute_', 'auto_', 'learn_', 'optimize_', 'schedule_']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for prefix in forbidden_prefixes:
                    assert not node.name.startswith(prefix), (
                        f"Forbidden method {node.name} found in audit_types"
                    )


class TestNoAutomationMethods:
    """Verify no automation methods exist in type definitions."""

    def test_no_batch_methods(self):
        """No batch_* methods allowed."""
        from browser_shell.audit_types import AuditEntry
        
        methods = [m for m in dir(AuditEntry) if m.startswith('batch')]
        assert methods == [], f"Forbidden batch methods found: {methods}"

    def test_no_remember_methods(self):
        """No remember_* methods allowed."""
        from browser_shell.audit_types import AuditEntry
        
        methods = [m for m in dir(AuditEntry) if m.startswith('remember')]
        assert methods == [], f"Forbidden remember methods found: {methods}"

    def test_no_background_methods(self):
        """No background_* methods allowed."""
        from browser_shell.audit_types import AuditEntry
        
        methods = [m for m in dir(AuditEntry) if m.startswith('background')]
        assert methods == [], f"Forbidden background methods found: {methods}"
