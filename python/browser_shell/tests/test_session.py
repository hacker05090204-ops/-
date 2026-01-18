# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-2.1, 2.2, 2.3: Session Management
# Requirement: 1.1, 1.2, 1.3 (Session Management)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""Tests for session management - governance-enforcing tests."""

import ast
import inspect
import pytest
import tempfile
import time


# =============================================================================
# TASK-2.1: Session Creation Tests
# =============================================================================

class TestSessionRequiresScope:
    """Verify session creation fails without scope."""

    def test_session_creation_requires_scope(self):
        """Session cannot be created without scope definition."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            # Attempt to create session without scope
            result = manager.create_session(
                scope_definition=None,
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            assert result.success is False
            assert "scope" in result.error_message.lower()

    def test_session_creation_requires_non_empty_scope(self):
        """Session cannot be created with empty scope."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            assert result.success is False


class TestSessionRequiresHumanConfirmation:
    """Verify confirmation step required."""

    def test_session_requires_human_confirmation_flag(self):
        """Session cannot be created without human_confirmed=True."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=False,  # Not confirmed!
            )
            
            assert result.success is False
            assert "confirm" in result.error_message.lower()


class TestSessionIdContainsScopeHash:
    """Verify session ID structure."""

    def test_session_id_contains_scope_hash(self):
        """Session ID must include scope hash."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        import hashlib
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            scope = "example.com"
            result = manager.create_session(
                scope_definition=scope,
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            assert result.success is True
            
            # Session ID should contain scope hash prefix
            scope_hash = hashlib.sha256(scope.encode()).hexdigest()[:8]
            assert scope_hash in result.session_id

    def test_session_id_contains_timestamp(self):
        """Session ID must include start timestamp."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            assert result.success is True
            # Session ID should contain timestamp component
            assert len(result.session_id) > 20  # Has multiple components


class TestSessionCreationAudited:
    """Verify audit entry created before operations."""

    def test_session_creation_logged_to_audit(self):
        """Session creation must be logged to audit trail."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            assert result.success is True
            
            # Check audit trail
            entries = storage.read_all()
            assert len(entries) >= 1
            
            # First entry should be session start
            assert entries[0].action_type == "SESSION_START"
            assert entries[0].initiator == "HUMAN"


class TestNoAutoSessionCreation:
    """Verify no automatic session creation path."""

    def test_no_auto_create_method(self):
        """SessionManager must not have auto_create method."""
        from browser_shell.session import SessionManager
        
        methods = [m for m in dir(SessionManager) if m.startswith('auto')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_no_background_session_creation(self):
        """SessionManager must not have background creation."""
        from browser_shell.session import SessionManager
        
        methods = [m for m in dir(SessionManager) if 'background' in m.lower()]
        assert methods == [], f"Forbidden background methods found: {methods}"


# =============================================================================
# TASK-2.2: Session Boundaries Tests
# =============================================================================

class TestSessionMaxDuration:
    """Verify session terminates at 4 hours (TH-06)."""

    def test_session_has_max_duration_constant(self):
        """Session must have MAX_DURATION_SECONDS constant."""
        from browser_shell.session import SessionManager
        
        assert hasattr(SessionManager, 'MAX_DURATION_SECONDS')
        assert SessionManager.MAX_DURATION_SECONDS == 4 * 60 * 60  # 4 hours

    def test_session_expired_check(self):
        """Session must detect when max duration exceeded."""
        from browser_shell.session import SessionManager, Session
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        from datetime import datetime, timezone, timedelta
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            # Create session
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            session = manager.get_session(result.session_id)
            
            # Simulate time passing (5 hours ago start)
            old_start = datetime.now(timezone.utc) - timedelta(hours=5)
            session._start_time = old_start
            
            assert session.is_expired() is True


class TestSessionIdleTimeout:
    """Verify session terminates after 30 min idle (TH-07)."""

    def test_session_has_idle_timeout_constant(self):
        """Session must have IDLE_TIMEOUT_SECONDS constant."""
        from browser_shell.session import SessionManager
        
        assert hasattr(SessionManager, 'IDLE_TIMEOUT_SECONDS')
        assert SessionManager.IDLE_TIMEOUT_SECONDS == 30 * 60  # 30 minutes

    def test_session_idle_check(self):
        """Session must detect when idle timeout exceeded."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        from datetime import datetime, timezone, timedelta
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            session = manager.get_session(result.session_id)
            
            # Simulate idle (35 minutes since last activity)
            old_activity = datetime.now(timezone.utc) - timedelta(minutes=35)
            session._last_activity = old_activity
            
            assert session.is_idle() is True


class TestSessionSingleScope:
    """Verify session cannot have multiple scopes."""

    def test_session_scope_is_immutable(self):
        """Session scope cannot be changed after creation."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            session = manager.get_session(result.session_id)
            
            # Attempt to change scope should fail
            with pytest.raises(AttributeError):
                session.scope_definition = "other.com"


class TestSessionSingleOperator:
    """Verify session cannot transfer operators."""

    def test_session_operator_is_immutable(self):
        """Session operator cannot be changed after creation."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            session = manager.get_session(result.session_id)
            
            # Attempt to change operator should fail
            with pytest.raises(AttributeError):
                session.operator_id = "operator-002"


# =============================================================================
# TASK-2.3: Session Termination Tests
# =============================================================================

class TestTerminationInvalidatesState:
    """Verify all state cleared on termination."""

    def test_session_terminated_flag(self):
        """Terminated session must be marked as terminated."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            session = manager.get_session(result.session_id)
            assert session.is_terminated is False
            
            manager.terminate_session(result.session_id, reason="Test termination")
            
            assert session.is_terminated is True


class TestTerminationDestroysTokens:
    """Verify tokens unusable after termination."""

    def test_session_not_retrievable_after_termination(self):
        """Terminated session should not be usable."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            manager.terminate_session(result.session_id, reason="Test")
            
            # Session should be marked terminated
            session = manager.get_session(result.session_id)
            assert session is None or session.is_terminated is True


class TestNoCrossSessionPersistence:
    """Verify no data leaks to future sessions."""

    def test_new_session_has_no_previous_state(self):
        """New session must not inherit state from previous session."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            # Create and terminate first session
            result1 = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            manager.terminate_session(result1.session_id, reason="Test")
            
            # Create second session
            result2 = manager.create_session(
                scope_definition="other.com",
                operator_id="operator-002",
                human_confirmed=True,
            )
            
            session2 = manager.get_session(result2.session_id)
            
            # Second session must have its own scope
            assert session2.scope_definition == "other.com"
            assert session2.operator_id == "operator-002"
            assert result2.session_id != result1.session_id


class TestTerminationAudited:
    """Verify termination logged with reason."""

    def test_termination_logged_to_audit(self):
        """Session termination must be logged to audit trail."""
        from browser_shell.session import SessionManager
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            manager = SessionManager(storage=storage, hash_chain=chain)
            
            result = manager.create_session(
                scope_definition="example.com",
                operator_id="operator-001",
                human_confirmed=True,
            )
            
            manager.terminate_session(result.session_id, reason="User requested")
            
            entries = storage.read_all()
            
            # Should have SESSION_START and SESSION_END
            action_types = [e.action_type for e in entries]
            assert "SESSION_START" in action_types
            assert "SESSION_END" in action_types
            
            # Termination entry should have reason
            end_entry = [e for e in entries if e.action_type == "SESSION_END"][0]
            assert "User requested" in end_entry.action_details


class TestNoAutomationInSession:
    """Verify no automation methods in session module."""

    def test_no_auto_methods(self):
        """No auto_* methods allowed."""
        from browser_shell.session import SessionManager
        
        methods = [m for m in dir(SessionManager) if m.startswith('auto')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_no_execute_methods(self):
        """No execute_* methods allowed."""
        from browser_shell.session import SessionManager
        
        methods = [m for m in dir(SessionManager) if m.startswith('execute')]
        assert methods == [], f"Forbidden execute methods found: {methods}"

    def test_no_extend_methods(self):
        """No extend_* methods allowed (no session extension)."""
        from browser_shell.session import SessionManager
        
        methods = [m for m in dir(SessionManager) if m.startswith('extend')]
        assert methods == [], f"Forbidden extend methods found: {methods}"
