# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-6.1, 6.2: Report Submission
# Requirement: 5.1, 5.2 (Report Submission)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""Tests for report submission - governance-enforcing tests."""

import pytest
import tempfile
import time


# =============================================================================
# TASK-6.1: Three-Step Submission Confirmation Tests
# =============================================================================

class TestThreeStepsRequired:
    """Verify exactly 3 confirmation steps (TH-01)."""

    def test_submission_requires_three_steps(self):
        """Submission must require exactly 3 confirmation steps."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            assert submission.REQUIRED_CONFIRMATION_STEPS == 3

    def test_submission_blocked_without_all_steps(self):
        """Submission blocked if fewer than 3 steps completed."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            # Start submission
            draft = submission.create_draft(
                session_id="session-001",
                title="Test Report",
                description="Test description",
            )
            
            # Only complete 2 steps
            submission.confirm_step_1(draft.draft_id, human_input="reviewed")
            time.sleep(0.1)  # Small delay
            submission.confirm_step_2(draft.draft_id, human_input="confirmed")
            
            # Attempt submission without step 3
            result = submission.execute_submission(draft.draft_id)
            
            assert result.success is False
            assert "step" in result.error_message.lower()


class TestEachStepDistinctInput:
    """Verify each step requires different input."""

    def test_step_1_requires_input(self):
        """Step 1 requires human input."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            result = submission.confirm_step_1(draft.draft_id, human_input="")
            
            assert result.success is False

    def test_step_2_requires_input(self):
        """Step 2 requires human input."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            submission.confirm_step_1(draft.draft_id, human_input="reviewed")
            time.sleep(2.1)  # Wait for minimum delay
            
            result = submission.confirm_step_2(draft.draft_id, human_input="")
            
            assert result.success is False

    def test_step_3_requires_input(self):
        """Step 3 requires human input."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            submission.confirm_step_1(draft.draft_id, human_input="reviewed")
            time.sleep(2.1)
            submission.confirm_step_2(draft.draft_id, human_input="confirmed")
            time.sleep(2.1)
            
            result = submission.confirm_step_3(draft.draft_id, human_input="")
            
            assert result.success is False


class TestMinimum2SecondDelay:
    """Verify 2 second minimum between steps (TH-02)."""

    def test_minimum_delay_constant(self):
        """Minimum delay must be 2 seconds."""
        from browser_shell.report import ReportSubmission
        
        assert ReportSubmission.MINIMUM_STEP_DELAY_SECONDS == 2

    def test_fast_step_transition_blocked(self):
        """Steps completed too quickly must be blocked."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            submission.confirm_step_1(draft.draft_id, human_input="reviewed")
            # No delay - immediate step 2
            result = submission.confirm_step_2(draft.draft_id, human_input="confirmed")
            
            assert result.success is False
            assert "timing" in result.error_message.lower() or "delay" in result.error_message.lower()


class TestFastTimingHalts:
    """Verify <2 sec timing triggers halt."""

    def test_fast_timing_flagged(self):
        """Fast timing must be flagged for governance review."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            submission.confirm_step_1(draft.draft_id, human_input="reviewed")
            # Immediate - should be flagged
            result = submission.confirm_step_2(draft.draft_id, human_input="confirmed")
            
            assert result.flagged_timing_violation is True


class TestEachStepAudited:
    """Verify all steps logged."""

    def test_step_1_audited(self):
        """Step 1 must be logged to audit trail."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            submission.confirm_step_1(draft.draft_id, human_input="reviewed")
            
            entries = storage.read_all()
            action_types = [e.action_type for e in entries]
            
            assert "SUBMISSION_STEP_1" in action_types


# =============================================================================
# TASK-6.2: Report Content Controls Tests
# =============================================================================

class TestNoAutoSeverity:
    """Verify no automatic severity assignment."""

    def test_no_auto_severity_method(self):
        """No auto_severity method allowed."""
        from browser_shell.report import ReportSubmission
        
        methods = [m for m in dir(ReportSubmission) if 'auto' in m.lower() and 'severity' in m.lower()]
        assert methods == [], f"Forbidden auto severity methods found: {methods}"

    def test_severity_requires_human_input(self):
        """Severity must be set by human."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            # Draft should not have auto-assigned severity
            assert draft.severity is None or draft.severity == ""


class TestNoAutoFillPrevious:
    """Verify no auto-fill from history."""

    def test_no_auto_fill_method(self):
        """No auto_fill method allowed."""
        from browser_shell.report import ReportSubmission
        
        methods = [m for m in dir(ReportSubmission) if 'auto_fill' in m.lower()]
        assert methods == [], f"Forbidden auto_fill methods found: {methods}"

    def test_no_history_method(self):
        """No get_history or use_history method allowed."""
        from browser_shell.report import ReportSubmission
        
        methods = [m for m in dir(ReportSubmission) if 'history' in m.lower()]
        assert methods == [], f"Forbidden history methods found: {methods}"


class TestTemplatesRequireHumanEdit:
    """Verify templates need human modification."""

    def test_template_marked_as_draft(self):
        """Templates must be marked as requiring human edit."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            template = submission.get_template("vulnerability")
            
            assert template.requires_human_edit is True


class TestSeverityRequiresHumanConfirmation:
    """Verify human sets severity."""

    def test_severity_set_by_human(self):
        """Severity must be explicitly set by human."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            result = submission.set_severity(
                draft_id=draft.draft_id,
                severity="HIGH",
                human_confirmed=True,
            )
            
            assert result.success is True

    def test_severity_rejected_without_confirmation(self):
        """Severity rejected without human confirmation."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            result = submission.set_severity(
                draft_id=draft.draft_id,
                severity="HIGH",
                human_confirmed=False,
            )
            
            assert result.success is False


class TestContentChangesAudited:
    """Verify all changes logged."""

    def test_severity_change_audited(self):
        """Severity changes must be logged."""
        from browser_shell.report import ReportSubmission
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            submission = ReportSubmission(storage=storage, hash_chain=chain)
            
            draft = submission.create_draft(
                session_id="session-001",
                title="Test",
                description="Test",
            )
            
            submission.set_severity(
                draft_id=draft.draft_id,
                severity="HIGH",
                human_confirmed=True,
            )
            
            entries = storage.read_all()
            details = " ".join([e.action_details for e in entries])
            
            assert "severity" in details.lower()


# =============================================================================
# Forbidden Capability Tests
# =============================================================================

class TestNoAutomationInReport:
    """Verify no automation methods in report module."""

    def test_no_auto_methods(self):
        """No auto_* methods allowed."""
        from browser_shell.report import ReportSubmission
        
        methods = [m for m in dir(ReportSubmission) if m.startswith('auto_')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_no_submit_without_confirmation(self):
        """No direct submit method without confirmation."""
        from browser_shell.report import ReportSubmission
        
        # Should not have a simple 'submit' method that bypasses steps
        assert not hasattr(ReportSubmission, 'submit') or \
               'confirm' in str(getattr(ReportSubmission, 'submit', None))

    def test_no_batch_methods(self):
        """No batch_* methods allowed."""
        from browser_shell.report import ReportSubmission
        
        methods = [m for m in dir(ReportSubmission) if m.startswith('batch')]
        assert methods == [], f"Forbidden batch methods found: {methods}"

    def test_no_schedule_methods(self):
        """No schedule_* methods allowed."""
        from browser_shell.report import ReportSubmission
        
        methods = [m for m in dir(ReportSubmission) if m.startswith('schedule')]
        assert methods == [], f"Forbidden schedule methods found: {methods}"
