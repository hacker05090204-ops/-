# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-1.2: Implement Append-Only Audit Storage
# Requirement: 6.1 (Audit Trail Properties)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""Tests for append-only audit storage - governance-enforcing tests."""

import ast
import inspect
import pytest
import tempfile
import os


class TestAuditStorageNoDelete:
    """Verify no delete method exists."""

    def test_no_delete_method(self):
        """AuditStorage must not have any delete method."""
        from browser_shell.audit_storage import AuditStorage
        
        forbidden = ['delete', 'remove', 'erase', 'clear', 'purge', 'wipe']
        methods = [m for m in dir(AuditStorage) 
                   if any(f in m.lower() for f in forbidden)]
        
        assert methods == [], f"Forbidden delete methods found: {methods}"

    def test_no_delete_in_source(self):
        """Source code must not contain delete operations."""
        import browser_shell.audit_storage as module
        
        source = inspect.getsource(module)
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                assert 'delete' not in node.name.lower(), (
                    f"Forbidden delete method: {node.name}"
                )


class TestAuditStorageNoUpdate:
    """Verify no update method exists."""

    def test_no_update_method(self):
        """AuditStorage must not have any update method."""
        from browser_shell.audit_storage import AuditStorage
        
        forbidden = ['update', 'modify', 'change', 'edit', 'alter', 'mutate']
        methods = [m for m in dir(AuditStorage) 
                   if any(f in m.lower() for f in forbidden)]
        
        assert methods == [], f"Forbidden update methods found: {methods}"


class TestAuditStorageNoTruncate:
    """Verify no truncate method exists."""

    def test_no_truncate_method(self):
        """AuditStorage must not have any truncate method."""
        from browser_shell.audit_storage import AuditStorage
        
        forbidden = ['truncate', 'trim', 'cut', 'shorten', 'limit']
        methods = [m for m in dir(AuditStorage) 
                   if any(f in m.lower() for f in forbidden)]
        
        assert methods == [], f"Forbidden truncate methods found: {methods}"


class TestAuditWriteIsSynchronous:
    """Verify write completes before return."""

    def test_append_is_synchronous(self):
        """Append must complete before returning."""
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.audit_types import AuditEntry
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            
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
            
            # Append should return only after write is confirmed
            result = storage.append(entry)
            
            # Result must indicate success
            assert result.success is True
            
            # Entry must be immediately readable
            entries = storage.read_all()
            assert len(entries) == 1
            assert entries[0].entry_id == "test-001"

    def test_append_blocks_until_confirmed(self):
        """Append must block until write is confirmed on disk."""
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.audit_types import AuditEntry
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            
            entry = AuditEntry(
                entry_id="test-002",
                timestamp="2026-01-04T00:00:01Z",
                previous_hash="a" * 64,
                action_type="SESSION_END",
                initiator="HUMAN",
                session_id="session-001",
                scope_hash="scope-hash-001",
                action_details="Test action 2",
                outcome="SUCCESS",
                entry_hash="b" * 64,
            )
            
            result = storage.append(entry)
            
            # File must exist on disk after append returns
            audit_file = os.path.join(tmpdir, "audit_trail.jsonl")
            assert os.path.exists(audit_file)
            
            # File must contain the entry
            with open(audit_file, 'r') as f:
                content = f.read()
                assert "test-002" in content


class TestAuditDisableImpossible:
    """Verify no disable mechanism exists."""

    def test_no_disable_method(self):
        """AuditStorage must not have any disable method."""
        from browser_shell.audit_storage import AuditStorage
        
        forbidden = ['disable', 'stop', 'pause', 'suspend', 'skip', 'bypass']
        methods = [m for m in dir(AuditStorage) 
                   if any(f in m.lower() for f in forbidden)]
        
        assert methods == [], f"Forbidden disable methods found: {methods}"

    def test_no_enabled_flag(self):
        """AuditStorage must not have an enabled/disabled flag."""
        from browser_shell.audit_storage import AuditStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            
            # Check for enabled/disabled attributes
            forbidden_attrs = ['enabled', 'disabled', 'active', 'paused']
            for attr in forbidden_attrs:
                assert not hasattr(storage, attr), (
                    f"Forbidden attribute {attr} found"
                )
                assert not hasattr(storage, f'_{attr}'), (
                    f"Forbidden private attribute _{attr} found"
                )
                assert not hasattr(storage, f'__{attr}'), (
                    f"Forbidden private attribute __{attr} found"
                )


class TestAuditStorageSeparation:
    """Verify audit storage is separate from application storage."""

    def test_dedicated_storage_path(self):
        """AuditStorage must use a dedicated path."""
        from browser_shell.audit_storage import AuditStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = os.path.join(tmpdir, "audit")
            storage = AuditStorage(storage_path=audit_path)
            
            # Audit storage must create its own directory
            assert os.path.exists(audit_path)


class TestNoAutomationInStorage:
    """Verify no automation methods in storage module."""

    def test_no_auto_methods(self):
        """No auto_* methods allowed."""
        from browser_shell.audit_storage import AuditStorage
        
        methods = [m for m in dir(AuditStorage) if m.startswith('auto')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_no_execute_methods(self):
        """No execute_* methods allowed."""
        from browser_shell.audit_storage import AuditStorage
        
        methods = [m for m in dir(AuditStorage) if m.startswith('execute')]
        assert methods == [], f"Forbidden execute methods found: {methods}"

    def test_no_schedule_methods(self):
        """No schedule_* methods allowed."""
        from browser_shell.audit_storage import AuditStorage
        
        methods = [m for m in dir(AuditStorage) if m.startswith('schedule')]
        assert methods == [], f"Forbidden schedule methods found: {methods}"

    def test_no_background_methods(self):
        """No background_* methods allowed."""
        from browser_shell.audit_storage import AuditStorage
        
        methods = [m for m in dir(AuditStorage) if m.startswith('background')]
        assert methods == [], f"Forbidden background methods found: {methods}"
