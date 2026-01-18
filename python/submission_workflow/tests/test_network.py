"""
Phase-7 Network Transmit Manager Tests

Tests for the NetworkTransmitManager that ensures:
- Report hash verification detects tampering
- Tampering triggers HARD STOP (no network access)
- Tampering is logged to audit trail
- Network access is confirmation-gated

Feature: human-authorized-submission, Property 12: Report Integrity Verification
Validates: Requirements 4.3, 4.8, 4.9
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
import uuid

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from submission_workflow.types import (
    Platform,
    SubmissionStatus,
    SubmissionAction,
    SubmissionConfirmation,
    DraftReport,
)
from submission_workflow.errors import (
    ReportTamperingDetectedError,
    TokenAlreadyUsedError,
    TokenExpiredError,
    ArchitecturalViolationError,
)
from submission_workflow.audit import SubmissionAuditLogger
from submission_workflow.registry import ConfirmationRegistry
from submission_workflow.network import (
    NetworkTransmitManager,
    verify_report_integrity,
    RequestCountingAdapter,
)
from submission_workflow.tests.conftest import make_confirmation, make_draft


class MockPlatformAdapter:
    """Mock platform adapter for testing (simple protocol implementation)."""
    
    def __init__(
        self,
        should_fail: bool = False,
        error_message: str = "Platform error",
    ):
        self.should_fail = should_fail
        self.error_message = error_message
        self.submit_called = False
        self.submitted_report: Optional[DraftReport] = None
    
    def submit(self, report: DraftReport) -> tuple[str, str]:
        """Mock submit that tracks calls."""
        self.submit_called = True
        self.submitted_report = report
        
        if self.should_fail:
            raise RuntimeError(self.error_message)
        
        return (f"platform-{uuid.uuid4()}", "Submission accepted")


class MockCountingAdapter(RequestCountingAdapter):
    """Mock adapter using RequestCountingAdapter base class."""
    
    def __init__(
        self,
        should_fail: bool = False,
        error_message: str = "Platform error",
        num_requests: int = 1,
    ):
        super().__init__()
        self.should_fail = should_fail
        self.error_message = error_message
        self.num_requests = num_requests  # How many requests to attempt
        self.submit_called = False
        self.submitted_report: Optional[DraftReport] = None
    
    def _do_submit(self, report: DraftReport) -> tuple[str, str]:
        """Mock submit that tracks calls and enforces request counting."""
        self.submit_called = True
        self.submitted_report = report
        
        # Simulate making HTTP requests
        for _ in range(self.num_requests):
            self._increment_request_count()  # MUST call before each request
        
        if self.should_fail:
            raise RuntimeError(self.error_message)
        
        return (f"platform-{uuid.uuid4()}", "Submission accepted")


class TestNetworkTransmitManagerBasic:
    """Basic functionality tests for NetworkTransmitManager."""
    
    def test_network_disabled_by_default(
        self,
        network_manager: NetworkTransmitManager,
    ) -> None:
        """Network access should be disabled by default."""
        assert not network_manager.is_network_enabled()
    
    def test_successful_transmission(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Successful transmission should return SubmissionRecord."""
        adapter = MockPlatformAdapter()
        
        record = network_manager.transmit(
            confirmation=sample_confirmation,
            draft=sample_draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        assert record.status == SubmissionStatus.SUBMITTED
        assert record.confirmation_id == sample_confirmation.confirmation_id
        assert record.request_id == sample_confirmation.request_id
        assert record.platform_submission_id is not None
        assert adapter.submit_called
    
    def test_network_disabled_after_transmission(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Network should be disabled after transmission completes."""
        adapter = MockPlatformAdapter()
        
        network_manager.transmit(
            confirmation=sample_confirmation,
            draft=sample_draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        assert not network_manager.is_network_enabled()
    
    def test_failed_transmission_still_consumes_confirmation(
        self,
        network_manager: NetworkTransmitManager,
        registry: ConfirmationRegistry,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Failed transmission should still consume the confirmation."""
        adapter = MockPlatformAdapter(should_fail=True)
        
        record = network_manager.transmit(
            confirmation=sample_confirmation,
            draft=sample_draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        assert record.status == SubmissionStatus.FAILED
        assert registry.is_used(sample_confirmation.confirmation_id)


class TestTamperingDetection:
    """Tests for report tampering detection."""
    
    def test_hash_mismatch_raises_tampering_error(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
    ) -> None:
        """
        Hash mismatch raises ReportTamperingDetectedError.
        
        Feature: human-authorized-submission, Property 12: Report Integrity Verification
        Validates: Requirements 4.3, 4.8
        """
        # Create confirmation with different hash (simulating tampering)
        now = datetime.now()
        tampered_confirmation = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=sample_draft.request_id,
            submitter_id="test-submitter",
            report_hash="wrong-hash-value",  # Hash doesn't match draft
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        adapter = MockPlatformAdapter()
        
        with pytest.raises(ReportTamperingDetectedError) as exc_info:
            network_manager.transmit(
                confirmation=tampered_confirmation,
                draft=sample_draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )
        
        assert exc_info.value.confirmation_id == tampered_confirmation.confirmation_id
        assert exc_info.value.expected_hash == "wrong-hash-value"
        assert exc_info.value.actual_hash == sample_draft.compute_hash()
    
    def test_tampering_blocks_network_access(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
    ) -> None:
        """
        Tampering detection blocks network access (HARD STOP).
        
        Feature: human-authorized-submission, Property 12: Report Integrity Verification
        Validates: Requirements 4.8, 4.9
        """
        now = datetime.now()
        tampered_confirmation = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=sample_draft.request_id,
            submitter_id="test-submitter",
            report_hash="wrong-hash-value",
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        adapter = MockPlatformAdapter()
        
        with pytest.raises(ReportTamperingDetectedError):
            network_manager.transmit(
                confirmation=tampered_confirmation,
                draft=sample_draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )
        
        # Network should NOT have been accessed
        assert not adapter.submit_called
        # Network should remain disabled
        assert not network_manager.is_network_enabled()
    
    def test_tampering_logged_to_audit_trail(
        self,
        audit_logger: SubmissionAuditLogger,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
    ) -> None:
        """
        Tampering is logged to audit trail.
        
        Feature: human-authorized-submission, Property 12: Report Integrity Verification
        Validates: Requirements 4.3, 4.8
        """
        now = datetime.now()
        tampered_confirmation = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=sample_draft.request_id,
            submitter_id="test-submitter",
            report_hash="wrong-hash-value",
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        adapter = MockPlatformAdapter()
        
        with pytest.raises(ReportTamperingDetectedError):
            network_manager.transmit(
                confirmation=tampered_confirmation,
                draft=sample_draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )
        
        # Check audit log for tampering entry
        tampering_entries = [
            e for e in audit_logger.get_chain()
            if e.action == SubmissionAction.REPORT_TAMPERING_DETECTED
        ]
        assert len(tampering_entries) == 1
        entry = tampering_entries[0]
        assert entry.confirmation_id == tampered_confirmation.confirmation_id
        assert entry.error_type == "ReportTamperingDetectedError"
        assert "wrong-hash-value" in entry.error_message
    
    def test_modified_title_detected_as_tampering(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Modifying the title after confirmation should be detected."""
        # Modify the draft after confirmation was created
        sample_draft.title = "MODIFIED TITLE"
        
        adapter = MockPlatformAdapter()
        
        with pytest.raises(ReportTamperingDetectedError):
            network_manager.transmit(
                confirmation=sample_confirmation,
                draft=sample_draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )
    
    def test_modified_description_detected_as_tampering(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Modifying the description after confirmation should be detected."""
        sample_draft.description = "MODIFIED DESCRIPTION"
        
        adapter = MockPlatformAdapter()
        
        with pytest.raises(ReportTamperingDetectedError):
            network_manager.transmit(
                confirmation=sample_confirmation,
                draft=sample_draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )
    
    def test_modified_evidence_detected_as_tampering(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Modifying evidence references after confirmation should be detected."""
        sample_draft.evidence_references.append("https://malicious.com/fake")
        
        adapter = MockPlatformAdapter()
        
        with pytest.raises(ReportTamperingDetectedError):
            network_manager.transmit(
                confirmation=sample_confirmation,
                draft=sample_draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )


class TestReplayPrevention:
    """Tests for replay attack prevention in network transmission."""
    
    def test_replay_attempt_blocked(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Replay attempt should be blocked."""
        adapter = MockPlatformAdapter()
        
        # First transmission succeeds
        network_manager.transmit(
            confirmation=sample_confirmation,
            draft=sample_draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        # Replay attempt fails
        with pytest.raises(TokenAlreadyUsedError):
            network_manager.transmit(
                confirmation=sample_confirmation,
                draft=sample_draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )
    
    def test_expired_confirmation_rejected(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        expired_confirmation: SubmissionConfirmation,
    ) -> None:
        """Expired confirmation should be rejected."""
        adapter = MockPlatformAdapter()
        
        with pytest.raises(TokenExpiredError):
            network_manager.transmit(
                confirmation=expired_confirmation,
                draft=sample_draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )


class TestAuditIntegration:
    """Tests for audit log integration."""
    
    def test_successful_transmission_logged(
        self,
        audit_logger: SubmissionAuditLogger,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Successful transmission should be logged."""
        adapter = MockPlatformAdapter()
        
        network_manager.transmit(
            confirmation=sample_confirmation,
            draft=sample_draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        # Check for TRANSMITTED action
        transmitted_entries = [
            e for e in audit_logger.get_chain()
            if e.action == SubmissionAction.TRANSMITTED
        ]
        assert len(transmitted_entries) == 1
    
    def test_network_access_granted_logged(
        self,
        audit_logger: SubmissionAuditLogger,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Network access grant should be logged."""
        adapter = MockPlatformAdapter()
        
        network_manager.transmit(
            confirmation=sample_confirmation,
            draft=sample_draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        # Check for NETWORK_ACCESS_GRANTED action
        granted_entries = [
            e for e in audit_logger.get_chain()
            if e.action == SubmissionAction.NETWORK_ACCESS_GRANTED
        ]
        assert len(granted_entries) == 1
    
    def test_failed_transmission_logged(
        self,
        audit_logger: SubmissionAuditLogger,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Failed transmission should be logged."""
        adapter = MockPlatformAdapter(should_fail=True, error_message="Platform down")
        
        network_manager.transmit(
            confirmation=sample_confirmation,
            draft=sample_draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        # Check for TRANSMISSION_FAILED action
        failed_entries = [
            e for e in audit_logger.get_chain()
            if e.action == SubmissionAction.TRANSMISSION_FAILED
        ]
        assert len(failed_entries) == 1
        assert "Platform down" in failed_entries[0].error_message


class TestVerifyReportIntegrity:
    """Tests for the verify_report_integrity utility function."""
    
    def test_matching_hash_returns_true(
        self,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Matching hash should return True."""
        assert verify_report_integrity(sample_confirmation, sample_draft)
    
    def test_mismatched_hash_returns_false(
        self,
        sample_draft: DraftReport,
    ) -> None:
        """Mismatched hash should return False."""
        now = datetime.now()
        bad_confirmation = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=sample_draft.request_id,
            submitter_id="test-submitter",
            report_hash="wrong-hash",
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        assert not verify_report_integrity(bad_confirmation, sample_draft)


class TestPropertyBased:
    """Property-based tests for NetworkTransmitManager."""
    
    @given(
        title=st.text(min_size=1, max_size=100),
        description=st.text(min_size=1, max_size=500),
    )
    @settings(max_examples=100)
    def test_property_confirmed_report_cannot_change(
        self,
        title: str,
        description: str,
    ) -> None:
        """
        Property: Confirmed report content cannot change post-confirmation.
        
        Any modification to the report after confirmation MUST be detected
        and result in ReportTamperingDetectedError.
        
        Feature: human-authorized-submission, Property 12: Report Integrity Verification
        Validates: Requirements 4.3, 4.8, 4.9
        """
        # Skip empty strings that would cause issues
        assume(title.strip() and description.strip())
        
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        network_manager = NetworkTransmitManager(audit_logger, registry)
        
        # Create original draft
        draft = make_draft(title=title, description=description)
        original_hash = draft.compute_hash()
        
        # Create confirmation with original hash
        now = datetime.now()
        confirmation = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft.request_id,
            submitter_id="test-submitter",
            report_hash=original_hash,
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        # Modify the draft (tampering)
        draft.title = draft.title + " TAMPERED"
        
        adapter = MockPlatformAdapter()
        
        # Tampering MUST be detected
        with pytest.raises(ReportTamperingDetectedError):
            network_manager.transmit(
                confirmation=confirmation,
                draft=draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )
        
        # Network MUST NOT have been accessed
        assert not adapter.submit_called
    
    @given(
        num_evidence=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100)
    def test_property_evidence_modification_detected(
        self,
        num_evidence: int,
    ) -> None:
        """
        Property: Any evidence modification is detected as tampering.
        
        Feature: human-authorized-submission, Property 12: Report Integrity Verification
        """
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        network_manager = NetworkTransmitManager(audit_logger, registry)
        
        # Create draft with evidence
        draft = DraftReport(
            draft_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            title="Test Report",
            description="Test description",
            severity="HIGH",
            classification="XSS",
            evidence_references=[f"https://example.com/evidence{i}" for i in range(num_evidence)],
            custom_fields={"platform": "hackerone"},
        )
        original_hash = draft.compute_hash()
        
        # Create confirmation
        now = datetime.now()
        confirmation = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft.request_id,
            submitter_id="test-submitter",
            report_hash=original_hash,
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        # Add new evidence (tampering)
        draft.evidence_references.append("https://malicious.com/injected")
        
        adapter = MockPlatformAdapter()
        
        # Tampering MUST be detected
        with pytest.raises(ReportTamperingDetectedError):
            network_manager.transmit(
                confirmation=confirmation,
                draft=draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )
    
    @given(
        custom_field_key=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        custom_field_value=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=100)
    def test_property_custom_field_modification_detected(
        self,
        custom_field_key: str,
        custom_field_value: str,
    ) -> None:
        """
        Property: Any custom field modification is detected as tampering.
        
        Feature: human-authorized-submission, Property 12: Report Integrity Verification
        """
        assume(custom_field_key.strip() and custom_field_value.strip())
        assume(custom_field_key != "platform")  # Don't overwrite platform
        
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        network_manager = NetworkTransmitManager(audit_logger, registry)
        
        # Create draft
        draft = make_draft()
        original_hash = draft.compute_hash()
        
        # Create confirmation
        now = datetime.now()
        confirmation = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft.request_id,
            submitter_id="test-submitter",
            report_hash=original_hash,
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        # Add new custom field (tampering)
        draft.custom_fields[custom_field_key] = custom_field_value
        
        adapter = MockPlatformAdapter()
        
        # Tampering MUST be detected
        with pytest.raises(ReportTamperingDetectedError):
            network_manager.transmit(
                confirmation=confirmation,
                draft=draft,
                platform_adapter=adapter,
                submitter_id="test-submitter",
            )
    
    @given(
        num_transmissions=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=100)
    def test_property_one_transmission_per_confirmation(
        self,
        num_transmissions: int,
    ) -> None:
        """
        Property: Each confirmation authorizes exactly ONE transmission.
        
        Feature: human-authorized-submission, Property 11: One Confirmation Per Request
        """
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        network_manager = NetworkTransmitManager(audit_logger, registry)
        
        # Create draft and matching confirmation
        draft = make_draft()
        now = datetime.now()
        confirmation = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft.request_id,
            submitter_id="test-submitter",
            report_hash=draft.compute_hash(),
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        adapter = MockPlatformAdapter()
        
        # First transmission succeeds
        network_manager.transmit(
            confirmation=confirmation,
            draft=draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        # All subsequent attempts MUST fail
        for _ in range(num_transmissions - 1):
            with pytest.raises(TokenAlreadyUsedError):
                network_manager.transmit(
                    confirmation=confirmation,
                    draft=draft,
                    platform_adapter=adapter,
                    submitter_id="test-submitter",
                )


class TestRequestCountingAdapter:
    """Tests for RequestCountingAdapter base class invariants."""
    
    def test_single_request_succeeds(self) -> None:
        """Adapter with exactly one request should succeed."""
        adapter = MockCountingAdapter(num_requests=1)
        draft = make_draft()
        
        platform_id, response = adapter.submit(draft)
        
        assert adapter.submit_called
        assert adapter.request_count == 1
        assert platform_id.startswith("platform-")
    
    def test_multiple_requests_raises_architectural_violation(self) -> None:
        """
        Adapter cannot send more than one request per confirmation.
        
        Feature: human-authorized-submission, Property 13: Single Request Per Transmit
        Validates: Requirements 4.10
        """
        adapter = MockCountingAdapter(num_requests=2)
        draft = make_draft()
        
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            adapter.submit(draft)
        
        assert "adapter_multiple_requests" in str(exc_info.value)
        assert "2 requests" in str(exc_info.value)
        assert "maximum allowed is 1" in str(exc_info.value)
    
    def test_three_requests_raises_architectural_violation(self) -> None:
        """Adapter attempting 3 requests should fail on second."""
        adapter = MockCountingAdapter(num_requests=3)
        draft = make_draft()
        
        with pytest.raises(ArchitecturalViolationError):
            adapter.submit(draft)
        
        # Should have stopped at 2 (when violation detected)
        assert adapter.request_count == 2
    
    def test_request_count_resets_between_calls(self) -> None:
        """Request count should reset between submit() calls."""
        adapter = MockCountingAdapter(num_requests=1)
        draft = make_draft()
        
        # First call
        adapter.submit(draft)
        assert adapter.request_count == 1
        
        # Second call - count should reset
        adapter.submit(draft)
        assert adapter.request_count == 1
    
    def test_counting_adapter_with_network_manager(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """Counting adapter should work with NetworkTransmitManager."""
        adapter = MockCountingAdapter(num_requests=1)
        
        record = network_manager.transmit(
            confirmation=sample_confirmation,
            draft=sample_draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        assert record.status == SubmissionStatus.SUBMITTED
        assert adapter.request_count == 1
    
    def test_multiple_requests_blocked_in_network_manager(
        self,
        network_manager: NetworkTransmitManager,
        sample_draft: DraftReport,
        sample_confirmation: SubmissionConfirmation,
    ) -> None:
        """
        Multiple requests should be blocked even through NetworkTransmitManager.
        
        Feature: human-authorized-submission, Property 13: Single Request Per Transmit
        """
        adapter = MockCountingAdapter(num_requests=2)
        
        # The adapter will raise ArchitecturalViolationError
        # NetworkTransmitManager will catch it as a transmission failure
        record = network_manager.transmit(
            confirmation=sample_confirmation,
            draft=sample_draft,
            platform_adapter=adapter,
            submitter_id="test-submitter",
        )
        
        # Transmission should fail due to architectural violation
        assert record.status == SubmissionStatus.FAILED
        assert "adapter_multiple_requests" in record.platform_response


class TestAdapterInvariantsPropertyBased:
    """Property-based tests for adapter invariants."""
    
    @given(
        num_requests=st.integers(min_value=2, max_value=10),
    )
    @settings(max_examples=100)
    def test_property_adapter_single_request_invariant(
        self,
        num_requests: int,
    ) -> None:
        """
        Property: Adapter MUST NOT send more than one HTTP request per transmit().
        
        For any number of requests > 1, ArchitecturalViolationError MUST be raised.
        
        Feature: human-authorized-submission, Property 13: Single Request Per Transmit
        Validates: Requirements 4.10
        """
        adapter = MockCountingAdapter(num_requests=num_requests)
        draft = make_draft()
        
        # Any attempt to send >1 request MUST fail
        with pytest.raises(ArchitecturalViolationError):
            adapter.submit(draft)
    
    @given(
        num_calls=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_property_request_count_resets(
        self,
        num_calls: int,
    ) -> None:
        """
        Property: Request count resets between submit() calls.
        
        Each submit() call starts with a fresh request count of 0.
        """
        adapter = MockCountingAdapter(num_requests=1)
        draft = make_draft()
        
        for _ in range(num_calls):
            adapter.submit(draft)
            # After each call, count should be exactly 1
            assert adapter.request_count == 1
