# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-5.1, 5.2, 5.3: Evidence Capture
# Requirement: 4.1, 4.2, 4.3 (Evidence Capture)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""Tests for evidence capture - governance-enforcing tests."""

import pytest
import tempfile


# =============================================================================
# TASK-5.1: Human-Initiated Evidence Capture Tests
# =============================================================================

class TestNoAutoEvidenceCapture:
    """Verify no automatic capture path exists."""

    def test_no_auto_capture_method(self):
        """No auto_capture method allowed."""
        from browser_shell.evidence import EvidenceCapture
        
        methods = [m for m in dir(EvidenceCapture) if m.startswith('auto')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_capture_requires_human_initiation(self):
        """Evidence capture requires human_initiated flag."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Attempt capture without human initiation
            result = capture.capture_screenshot(
                session_id="session-001",
                data=b"fake_screenshot_data",
                human_initiated=False,
            )
            
            assert result.success is False
            assert "human" in result.error_message.lower()


class TestEvidenceDisplayedBeforeStorage:
    """Verify human sees evidence first."""

    def test_capture_returns_preview(self):
        """Capture must return preview for human review."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Initiate capture (returns preview, not stored yet)
            preview = capture.initiate_capture(
                session_id="session-001",
                evidence_type="SCREENSHOT",
                data=b"fake_screenshot_data",
            )
            
            assert preview.preview_id is not None
            assert preview.stored is False


class TestEvidenceRequiresConfirmation:
    """Verify confirmation step required."""

    def test_storage_requires_confirmation(self):
        """Evidence storage requires explicit confirmation."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Initiate capture
            preview = capture.initiate_capture(
                session_id="session-001",
                evidence_type="SCREENSHOT",
                data=b"fake_screenshot_data",
            )
            
            # Confirm storage
            result = capture.confirm_storage(
                preview_id=preview.preview_id,
                human_confirmed=True,
            )
            
            assert result.success is True
            assert result.stored is True

    def test_storage_rejected_without_confirmation(self):
        """Evidence storage rejected without confirmation."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Initiate capture
            preview = capture.initiate_capture(
                session_id="session-001",
                evidence_type="SCREENSHOT",
                data=b"fake_screenshot_data",
            )
            
            # Attempt storage without confirmation
            result = capture.confirm_storage(
                preview_id=preview.preview_id,
                human_confirmed=False,
            )
            
            assert result.success is False


class TestEvidenceCaptureAudited:
    """Verify capture logged to audit trail."""

    def test_capture_logged(self):
        """Evidence capture must be logged."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Initiate and confirm capture
            preview = capture.initiate_capture(
                session_id="session-001",
                evidence_type="SCREENSHOT",
                data=b"fake_screenshot_data",
            )
            capture.confirm_storage(
                preview_id=preview.preview_id,
                human_confirmed=True,
            )
            
            entries = storage.read_all()
            action_types = [e.action_type for e in entries]
            
            assert "EVIDENCE_CAPTURED" in action_types


# =============================================================================
# TASK-5.2: Evidence Size Limits Tests
# =============================================================================

class TestScreenshotSoftLimit:
    """Verify screenshot soft limit 2MB (TH-09)."""

    def test_screenshot_soft_limit_constant(self):
        """Screenshot soft limit must be 2MB."""
        from browser_shell.evidence import EvidenceCapture
        
        assert EvidenceCapture.SCREENSHOT_SOFT_LIMIT == 2 * 1024 * 1024  # 2MB

    def test_screenshot_over_soft_limit_requires_confirmation(self):
        """Screenshot over soft limit requires extra confirmation."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Temporarily lower soft limit for testing
            original_soft = EvidenceCapture.SCREENSHOT_SOFT_LIMIT
            EvidenceCapture.SCREENSHOT_SOFT_LIMIT = 100  # 100 bytes for test
            
            try:
                # Create data over soft limit
                large_data = b"x" * 101  # Just over 100 bytes
                
                preview = capture.initiate_capture(
                    session_id="session-001",
                    evidence_type="SCREENSHOT",
                    data=large_data,
                )
                
                assert preview.exceeds_soft_limit is True
                assert preview.requires_size_confirmation is True
            finally:
                EvidenceCapture.SCREENSHOT_SOFT_LIMIT = original_soft


class TestScreenshotHardLimit:
    """Verify screenshot hard limit 5MB (TH-10)."""

    def test_screenshot_hard_limit_constant(self):
        """Screenshot hard limit must be 5MB."""
        from browser_shell.evidence import EvidenceCapture
        
        assert EvidenceCapture.SCREENSHOT_HARD_LIMIT == 5 * 1024 * 1024  # 5MB

    def test_screenshot_over_hard_limit_blocked(self):
        """Screenshot over hard limit must be blocked."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Temporarily lower hard limit for testing
            original_hard = EvidenceCapture.SCREENSHOT_HARD_LIMIT
            EvidenceCapture.SCREENSHOT_HARD_LIMIT = 200  # 200 bytes for test
            
            try:
                # Create data over hard limit
                huge_data = b"x" * 201  # Just over 200 bytes
                
                preview = capture.initiate_capture(
                    session_id="session-001",
                    evidence_type="SCREENSHOT",
                    data=huge_data,
                )
                
                assert preview.blocked is True
                assert "hard limit" in preview.block_reason.lower()
            finally:
                EvidenceCapture.SCREENSHOT_HARD_LIMIT = original_hard


class TestResponseBodyLimits:
    """Verify response body limits (TH-11, TH-12)."""

    def test_response_body_soft_limit_constant(self):
        """Response body soft limit must be 50KB."""
        from browser_shell.evidence import EvidenceCapture
        
        assert EvidenceCapture.RESPONSE_BODY_SOFT_LIMIT == 50 * 1024  # 50KB

    def test_response_body_hard_limit_constant(self):
        """Response body hard limit must be 200KB."""
        from browser_shell.evidence import EvidenceCapture
        
        assert EvidenceCapture.RESPONSE_BODY_HARD_LIMIT == 200 * 1024  # 200KB


class TestSessionAggregateLimit:
    """Verify session aggregate limit 100MB (TH-21)."""

    def test_session_aggregate_limit_constant(self):
        """Session aggregate limit must be 100MB."""
        from browser_shell.evidence import EvidenceCapture
        
        assert EvidenceCapture.SESSION_AGGREGATE_LIMIT == 100 * 1024 * 1024  # 100MB

    def test_session_aggregate_tracked(self):
        """Session aggregate must be tracked."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Capture some evidence
            preview = capture.initiate_capture(
                session_id="session-001",
                evidence_type="SCREENSHOT",
                data=b"x" * 1000,
            )
            capture.confirm_storage(
                preview_id=preview.preview_id,
                human_confirmed=True,
            )
            
            budget = capture.get_remaining_budget("session-001")
            
            assert budget.used_bytes == 1000
            assert budget.remaining_bytes == 100 * 1024 * 1024 - 1000


class TestBudgetDisplayed:
    """Verify remaining budget shown to human."""

    def test_budget_status_available(self):
        """Budget status must be available."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            budget = capture.get_remaining_budget("session-001")
            
            assert budget.total_bytes == 100 * 1024 * 1024
            assert budget.used_bytes == 0
            assert budget.remaining_bytes == 100 * 1024 * 1024


# =============================================================================
# TASK-5.3: Evidence Content Restrictions Tests
# =============================================================================

class TestCredentialsBlocked:
    """Verify credential-containing evidence blocked."""

    def test_password_pattern_blocked(self):
        """Evidence with password patterns must be blocked."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Data containing credential pattern
            data = b'{"password": "secret123", "data": "test"}'
            
            preview = capture.initiate_capture(
                session_id="session-001",
                evidence_type="RESPONSE_BODY",
                data=data,
            )
            
            assert preview.blocked is True
            assert "credential" in preview.block_reason.lower()

    def test_api_key_pattern_blocked(self):
        """Evidence with API key patterns must be blocked."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Data containing API key pattern
            data = b'api_key=sk_live_abcdef123456'
            
            preview = capture.initiate_capture(
                session_id="session-001",
                evidence_type="RESPONSE_BODY",
                data=data,
            )
            
            assert preview.blocked is True


class TestPIIFlagged:
    """Verify PII-containing evidence flagged for review."""

    def test_email_pattern_flagged(self):
        """Evidence with email patterns must be flagged."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Data containing email pattern
            data = b'Contact: user@example.com for support'
            
            preview = capture.initiate_capture(
                session_id="session-001",
                evidence_type="RESPONSE_BODY",
                data=data,
            )
            
            assert preview.flagged_pii is True
            assert preview.requires_redaction_review is True


class TestBulkDataFlagged:
    """Verify bulk data patterns flagged."""

    def test_large_array_flagged(self):
        """Evidence with large data arrays must be flagged."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Data containing bulk pattern (many records)
            records = ','.join([f'{{"id": {i}}}' for i in range(100)])
            data = f'[{records}]'.encode()
            
            preview = capture.initiate_capture(
                session_id="session-001",
                evidence_type="RESPONSE_BODY",
                data=data,
            )
            
            assert preview.flagged_bulk_data is True


class TestContentDetectionAudited:
    """Verify content detections logged."""

    def test_blocked_evidence_logged(self):
        """Blocked evidence must be logged."""
        from browser_shell.evidence import EvidenceCapture
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            capture = EvidenceCapture(storage=storage, hash_chain=chain)
            
            # Data containing credential pattern
            data = b'{"password": "secret123"}'
            
            capture.initiate_capture(
                session_id="session-001",
                evidence_type="RESPONSE_BODY",
                data=data,
            )
            
            entries = storage.read_all()
            action_types = [e.action_type for e in entries]
            
            assert "EVIDENCE_BLOCKED" in action_types


# =============================================================================
# Forbidden Capability Tests
# =============================================================================

class TestNoAutomationInEvidence:
    """Verify no automation methods in evidence module."""

    def test_no_auto_methods(self):
        """No auto_* methods allowed."""
        from browser_shell.evidence import EvidenceCapture
        
        methods = [m for m in dir(EvidenceCapture) if m.startswith('auto')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_no_background_methods(self):
        """No background_* methods allowed."""
        from browser_shell.evidence import EvidenceCapture
        
        methods = [m for m in dir(EvidenceCapture) if m.startswith('background')]
        assert methods == [], f"Forbidden background methods found: {methods}"

    def test_no_schedule_methods(self):
        """No schedule_* methods allowed."""
        from browser_shell.evidence import EvidenceCapture
        
        methods = [m for m in dir(EvidenceCapture) if m.startswith('schedule')]
        assert methods == [], f"Forbidden schedule methods found: {methods}"

    def test_no_batch_methods(self):
        """No batch_* methods allowed."""
        from browser_shell.evidence import EvidenceCapture
        
        methods = [m for m in dir(EvidenceCapture) if m.startswith('batch')]
        assert methods == [], f"Forbidden batch methods found: {methods}"
