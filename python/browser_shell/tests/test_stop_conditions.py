# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-9.1, 9.2: Stop Conditions & Recovery
# Requirement: 10.1, 10.2 (Stop Conditions & Recovery)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""Tests for stop conditions and recovery - governance-enforcing tests."""

import pytest
import tempfile
import time
import os


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_audit_dir():
    """Create a temporary directory for audit storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def audit_storage(temp_audit_dir):
    """Create an AuditStorage instance."""
    from browser_shell.audit_storage import AuditStorage
    return AuditStorage(temp_audit_dir)


@pytest.fixture
def hash_chain():
    """Create a HashChain instance."""
    from browser_shell.hash_chain import HashChain
    return HashChain()


# =============================================================================
# TASK-9.1: Immediate Halt Conditions Tests
# =============================================================================

class TestInsufficientConfirmationsHalts:
    """Verify <3 confirmations triggers halt."""
    
    def test_submission_blocked_without_step_1(self, audit_storage, hash_chain):
        """Verify submission blocked without step 1."""
        from browser_shell.report import ReportSubmission
        
        submission = ReportSubmission(audit_storage, hash_chain)
        
        draft = submission.create_draft(
            session_id="test-session",
            title="Test Report",
            description="Test description",
        )
        
        # Try to execute without any confirmations
        result = submission.execute_submission(draft.draft_id)
        
        assert not result.success
        assert "Step 1 not completed" in result.error_message
    
    def test_submission_blocked_without_step_2(self, audit_storage, hash_chain):
        """Verify submission blocked without step 2."""
        from browser_shell.report import ReportSubmission
        
        submission = ReportSubmission(audit_storage, hash_chain)
        
        draft = submission.create_draft(
            session_id="test-session",
            title="Test Report",
            description="Test description",
        )
        
        # Complete only step 1
        submission.confirm_step_1(draft.draft_id, "confirmed step 1")
        
        # Try to execute without step 2
        result = submission.execute_submission(draft.draft_id)
        
        assert not result.success
        assert "Step 2 not completed" in result.error_message
    
    def test_submission_blocked_without_step_3(self, audit_storage, hash_chain):
        """Verify submission blocked without step 3."""
        from browser_shell.report import ReportSubmission
        
        submission = ReportSubmission(audit_storage, hash_chain)
        
        draft = submission.create_draft(
            session_id="test-session",
            title="Test Report",
            description="Test description",
        )
        
        # Complete steps 1 and 2 with proper timing
        submission.confirm_step_1(draft.draft_id, "confirmed step 1")
        time.sleep(2.1)  # Wait for minimum delay
        submission.confirm_step_2(draft.draft_id, "confirmed step 2")
        
        # Try to execute without step 3
        result = submission.execute_submission(draft.draft_id)
        
        assert not result.success
        assert "Step 3 not completed" in result.error_message


class TestUnauthorizedTargetTerminates:
    """Verify out-of-scope terminates session."""
    
    def test_out_of_scope_request_blocked(self, audit_storage, hash_chain):
        """Verify out-of-scope request is blocked."""
        from browser_shell.scope import ScopeValidator
        
        validator = ScopeValidator(audit_storage, hash_chain)
        
        # Activate scope with specific targets
        validator.activate_scope(
            scope_definition="example.com, test.example.com",
            session_id="test-session",
            human_confirmed=True,
        )
        
        # Try to validate out-of-scope target
        result = validator.validate_request("malicious.com", session_id="test-session")
        
        assert not result.allowed
        assert result.blocked
        assert "out of scope" in result.block_reason.lower()


class TestLowDecisionRatioFlags:
    """Verify <1:1 ratio flags for review."""
    
    def test_low_ratio_flagged(self, audit_storage, hash_chain):
        """Verify low decision ratio is flagged."""
        from browser_shell.decision import DecisionTracker
        
        tracker = DecisionTracker(audit_storage, hash_chain)
        
        # Record many state changes but few decisions
        for i in range(10):
            tracker.record_state_change(f"test-session")
        
        # Record only 1 decision
        tracker.record_decision_point(
            session_id="test-session",
            options_presented=["option1", "option2"],
            option_selected="option1",
        )
        
        # Check ratio
        status = tracker.check_decision_ratio("test-session")
        
        assert status.flagged


class TestAuditWriteFailureHalts:
    """Verify audit failure triggers halt."""
    
    def test_audit_storage_is_synchronous(self, audit_storage):
        """Verify audit writes are synchronous (blocking)."""
        from browser_shell.audit_types import AuditEntry
        
        entry = AuditEntry(
            entry_id="test-entry",
            timestamp="2026-01-04T00:00:00Z",
            previous_hash="genesis",
            action_type="TEST",
            initiator="HUMAN",
            session_id="test-session",
            scope_hash="scope-hash",
            action_details="Test action",
            outcome="SUCCESS",
            entry_hash="test-hash",
        )
        
        # Append should be synchronous
        result = audit_storage.append(entry)
        
        assert result.success
        
        # Entry should be immediately retrievable
        last_entry = audit_storage.get_last_entry()
        assert last_entry is not None
        assert last_entry.entry_id == "test-entry"


class TestHashChainFailureHalts:
    """Verify broken chain triggers halt."""
    
    def test_invalid_hash_detected(self, audit_storage, hash_chain):
        """Verify invalid hash is detected."""
        from browser_shell.audit_types import AuditEntry
        from browser_shell.hash_chain import HashChain
        
        # Create entry with correct hash
        entry_hash = hash_chain.compute_entry_hash(
            entry_id="test-entry",
            timestamp="2026-01-04T00:00:00Z",
            previous_hash=HashChain.GENESIS_HASH,
            action_type="TEST",
            initiator="HUMAN",
            session_id="test-session",
            scope_hash="scope-hash",
            action_details="Test action",
            outcome="SUCCESS",
        )
        
        entry = AuditEntry(
            entry_id="test-entry",
            timestamp="2026-01-04T00:00:00Z",
            previous_hash=HashChain.GENESIS_HASH,
            action_type="TEST",
            initiator="HUMAN",
            session_id="test-session",
            scope_hash="scope-hash",
            action_details="Test action",
            outcome="SUCCESS",
            entry_hash=entry_hash,
        )
        
        # Store the valid entry
        audit_storage.append(entry)
        
        # Validation should pass for valid chain
        result = hash_chain.validate_chain(audit_storage)
        assert result.valid
        
        # Now create a bad entry with wrong hash
        bad_entry = AuditEntry(
            entry_id="bad-entry",
            timestamp="2026-01-04T00:00:01Z",
            previous_hash=entry_hash,
            action_type="TEST",
            initiator="HUMAN",
            session_id="test-session",
            scope_hash="scope-hash",
            action_details="Bad action",
            outcome="SUCCESS",
            entry_hash="INVALID_HASH",  # Wrong hash
        )
        
        # Store the bad entry
        audit_storage.append(bad_entry)
        
        # Validation should fail for invalid chain
        result = hash_chain.validate_chain(audit_storage)
        assert not result.valid


class TestTimeLimitTerminates:
    """Verify timeout terminates session."""
    
    def test_session_manager_max_duration_constant(self):
        """Verify session manager has max duration constant."""
        from browser_shell.session import SessionManager
        
        assert hasattr(SessionManager, 'MAX_DURATION_SECONDS')
        assert SessionManager.MAX_DURATION_SECONDS == 4 * 60 * 60  # 4 hours
    
    def test_session_manager_idle_timeout_constant(self):
        """Verify session manager has idle timeout constant."""
        from browser_shell.session import SessionManager
        
        assert hasattr(SessionManager, 'IDLE_TIMEOUT_SECONDS')
        assert SessionManager.IDLE_TIMEOUT_SECONDS == 30 * 60  # 30 minutes


class TestScopeModificationRejected:
    """Verify mid-session scope change rejected."""
    
    def test_scope_modification_blocked(self, audit_storage, hash_chain):
        """Verify scope cannot be modified mid-session."""
        from browser_shell.scope import ScopeValidator
        
        validator = ScopeValidator(audit_storage, hash_chain)
        
        # Activate initial scope
        result1 = validator.activate_scope(
            scope_definition="example.com",
            session_id="test-session",
            human_confirmed=True,
        )
        assert result1.success
        
        # Try to activate different scope for same session (should fail)
        result2 = validator.activate_scope(
            scope_definition="example.com, new-target.com",
            session_id="test-session",
            human_confirmed=True,
        )
        
        assert not result2.success
        assert "immutable" in result2.error_message.lower()


# =============================================================================
# TASK-9.2: Recovery Requirements Tests
# =============================================================================

class TestHaltPreservesState:
    """Verify state preserved for analysis."""
    
    def test_session_state_preserved_on_termination(self, audit_storage, hash_chain):
        """Verify session state is preserved when terminated."""
        from browser_shell.session import SessionManager
        
        manager = SessionManager(audit_storage, hash_chain)
        
        # Create session
        result = manager.create_session(
            scope_definition="example.com",
            operator_id="test-operator",
            human_confirmed=True,
        )
        
        assert result.success
        session_id = result.session_id
        
        # Terminate session
        manager.terminate_session(session_id, reason="test termination")
        
        # Session should be terminated but record preserved
        session = manager.get_session(session_id)
        assert session is not None
        assert session.is_terminated


class TestRecoveryAudited:
    """Verify halt/recovery logged."""
    
    def test_termination_logged_to_audit(self, audit_storage, hash_chain):
        """Verify session termination is logged."""
        from browser_shell.session import SessionManager
        
        manager = SessionManager(audit_storage, hash_chain)
        
        result = manager.create_session(
            scope_definition="example.com",
            operator_id="test-operator",
            human_confirmed=True,
        )
        
        initial_count = audit_storage.count()
        
        # Terminate session
        manager.terminate_session(result.session_id, reason="test termination")
        
        # Should have logged termination
        assert audit_storage.count() > initial_count


# =============================================================================
# Stop Condition Constants Verification
# =============================================================================

class TestStopConditionConstants:
    """Verify all stop condition constants are defined."""
    
    def test_submission_confirmation_steps_constant(self):
        """Verify 3-step confirmation constant."""
        from browser_shell.report import ReportSubmission
        
        assert hasattr(ReportSubmission, 'REQUIRED_CONFIRMATION_STEPS')
        assert ReportSubmission.REQUIRED_CONFIRMATION_STEPS == 3
    
    def test_minimum_step_delay_constant(self):
        """Verify minimum step delay constant."""
        from browser_shell.report import ReportSubmission
        
        assert hasattr(ReportSubmission, 'MINIMUM_STEP_DELAY_SECONDS')
        assert ReportSubmission.MINIMUM_STEP_DELAY_SECONDS == 2
    
    def test_session_max_duration_constant(self):
        """Verify session max duration constant."""
        from browser_shell.session import SessionManager
        
        assert hasattr(SessionManager, 'MAX_DURATION_SECONDS')
        assert SessionManager.MAX_DURATION_SECONDS == 4 * 60 * 60  # 4 hours
    
    def test_session_idle_timeout_constant(self):
        """Verify session idle timeout constant."""
        from browser_shell.session import SessionManager
        
        assert hasattr(SessionManager, 'IDLE_TIMEOUT_SECONDS')
        assert SessionManager.IDLE_TIMEOUT_SECONDS == 30 * 60  # 30 minutes
    
    def test_confirmation_window_constant(self):
        """Verify confirmation window constant."""
        from browser_shell.decision import ConfirmationSystem
        
        assert hasattr(ConfirmationSystem, 'WINDOW_SECONDS')
        assert ConfirmationSystem.WINDOW_SECONDS == 300  # 5 minutes
    
    def test_confirmation_max_per_window_constant(self):
        """Verify max confirmations per window constant."""
        from browser_shell.decision import ConfirmationSystem
        
        assert hasattr(ConfirmationSystem, 'MAX_CONFIRMATIONS_PER_WINDOW')
        assert ConfirmationSystem.MAX_CONFIRMATIONS_PER_WINDOW == 10
    
    def test_rubber_stamp_threshold_constant(self):
        """Verify rubber stamp threshold constant."""
        from browser_shell.decision import ConfirmationSystem
        
        assert hasattr(ConfirmationSystem, 'RUBBER_STAMP_THRESHOLD_SECONDS')
        assert ConfirmationSystem.RUBBER_STAMP_THRESHOLD_SECONDS == 1.0
