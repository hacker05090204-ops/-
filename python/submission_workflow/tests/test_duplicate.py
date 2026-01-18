"""
Phase-7 Duplicate Submission Guard Tests

Tests for the DuplicateSubmissionGuard that ensures:
- decision_id + platform uniqueness is enforced atomically
- Concurrent submissions: one succeeds, one fails
- All duplicate attempts are logged to audit trail
- Lock is properly acquired and released

Feature: human-authorized-submission, Property 14: Duplicate Prevention
Validates: Requirements 4.11, 4.12
"""

from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from threading import Barrier, Event
from typing import Optional
import time
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
from submission_workflow.errors import DuplicateSubmissionError
from submission_workflow.audit import SubmissionAuditLogger, create_audit_entry
from submission_workflow.duplicate import DuplicateSubmissionGuard, SubmissionKey
from submission_workflow.tests.conftest import make_draft


class TestSubmissionKey:
    """Tests for SubmissionKey dataclass."""
    
    def test_key_equality(self) -> None:
        """Keys with same decision_id and platform should be equal."""
        key1 = SubmissionKey(decision_id="dec-123", platform=Platform.HACKERONE)
        key2 = SubmissionKey(decision_id="dec-123", platform=Platform.HACKERONE)
        
        assert key1 == key2
        assert hash(key1) == hash(key2)
    
    def test_key_inequality_different_decision(self) -> None:
        """Keys with different decision_id should not be equal."""
        key1 = SubmissionKey(decision_id="dec-123", platform=Platform.HACKERONE)
        key2 = SubmissionKey(decision_id="dec-456", platform=Platform.HACKERONE)
        
        assert key1 != key2
    
    def test_key_inequality_different_platform(self) -> None:
        """Keys with different platform should not be equal."""
        key1 = SubmissionKey(decision_id="dec-123", platform=Platform.HACKERONE)
        key2 = SubmissionKey(decision_id="dec-123", platform=Platform.BUGCROWD)
        
        assert key1 != key2
    
    def test_key_hashable_for_set(self) -> None:
        """Keys should be usable in sets."""
        key1 = SubmissionKey(decision_id="dec-123", platform=Platform.HACKERONE)
        key2 = SubmissionKey(decision_id="dec-123", platform=Platform.HACKERONE)
        key3 = SubmissionKey(decision_id="dec-456", platform=Platform.HACKERONE)
        
        key_set = {key1, key2, key3}
        assert len(key_set) == 2  # key1 and key2 are duplicates


class TestDuplicateSubmissionGuardBasic:
    """Basic functionality tests for DuplicateSubmissionGuard."""
    
    def test_first_submission_succeeds(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """First submission for a decision/platform should succeed."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        key = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="test-submitter",
        )
        
        assert key.decision_id == "dec-123"
        assert key.platform == Platform.HACKERONE
        assert guard.get_active_count() == 1
        
        # Clean up
        guard.release_on_error(key)
    
    def test_duplicate_blocked_when_active(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """Duplicate submission blocked when another is active."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        # First submission acquires lock
        key1 = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="submitter-1",
        )
        
        # Second submission for same decision/platform should fail
        with pytest.raises(DuplicateSubmissionError) as exc_info:
            guard.check_and_acquire(
                decision_id="dec-123",
                platform=Platform.HACKERONE,
                submitter_id="submitter-2",
            )
        
        assert exc_info.value.decision_id == "dec-123"
        assert exc_info.value.platform == Platform.HACKERONE
        
        # Clean up
        guard.release_on_error(key1)
    
    def test_different_platform_allowed(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """Same decision can be submitted to different platforms."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        key1 = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="test-submitter",
        )
        
        key2 = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.BUGCROWD,
            submitter_id="test-submitter",
        )
        
        assert guard.get_active_count() == 2
        
        # Clean up
        guard.release_on_error(key1)
        guard.release_on_error(key2)
    
    def test_different_decision_allowed(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """Different decisions can be submitted to same platform."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        key1 = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="test-submitter",
        )
        
        key2 = guard.check_and_acquire(
            decision_id="dec-456",
            platform=Platform.HACKERONE,
            submitter_id="test-submitter",
        )
        
        assert guard.get_active_count() == 2
        
        # Clean up
        guard.release_on_error(key1)
        guard.release_on_error(key2)
    
    def test_release_allows_new_submission(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """After release, new submission for same key is allowed."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        # First submission
        key1 = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="test-submitter",
        )
        guard.release_on_error(key1)
        
        # Second submission should succeed (no TRANSMITTED entry in audit)
        key2 = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="test-submitter",
        )
        
        assert key2.decision_id == "dec-123"
        guard.release_on_error(key2)


class TestDuplicateSubmissionGuardAuditLog:
    """Tests for audit log integration."""
    
    def test_duplicate_blocked_logged(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """Blocked duplicate attempts should be logged."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        key1 = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="submitter-1",
        )
        
        with pytest.raises(DuplicateSubmissionError):
            guard.check_and_acquire(
                decision_id="dec-123",
                platform=Platform.HACKERONE,
                submitter_id="submitter-2",
            )
        
        # Check audit log
        blocked_entries = [
            e for e in audit_logger.get_chain()
            if e.action == SubmissionAction.DUPLICATE_BLOCKED
        ]
        assert len(blocked_entries) == 1
        assert blocked_entries[0].decision_id == "dec-123"
        assert blocked_entries[0].platform == Platform.HACKERONE
        
        guard.release_on_error(key1)
    
    def test_already_submitted_blocked(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """Submission blocked if already in audit log as TRANSMITTED."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        # Simulate a previous successful submission in audit log
        audit_logger.log(create_audit_entry(
            submitter_id="previous-submitter",
            action=SubmissionAction.TRANSMITTED,
            decision_id="dec-123",
            platform=Platform.HACKERONE,
        ))
        
        # New submission should be blocked
        with pytest.raises(DuplicateSubmissionError) as exc_info:
            guard.check_and_acquire(
                decision_id="dec-123",
                platform=Platform.HACKERONE,
                submitter_id="new-submitter",
            )
        
        assert exc_info.value.decision_id == "dec-123"
    
    def test_is_submitted_returns_true_after_transmission(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """is_submitted() returns True if TRANSMITTED entry exists."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        # Initially not submitted
        assert not guard.is_submitted("dec-123", Platform.HACKERONE)
        
        # Add TRANSMITTED entry
        audit_logger.log(create_audit_entry(
            submitter_id="test-submitter",
            action=SubmissionAction.TRANSMITTED,
            decision_id="dec-123",
            platform=Platform.HACKERONE,
        ))
        
        # Now should be submitted
        assert guard.is_submitted("dec-123", Platform.HACKERONE)
        # Different platform should not be submitted
        assert not guard.is_submitted("dec-123", Platform.BUGCROWD)


class TestDuplicateSubmissionGuardVerifyAndRelease:
    """Tests for verify_and_release() method."""
    
    def test_verify_and_release_success(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """verify_and_release() should release lock on success."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        key = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="test-submitter",
        )
        
        assert guard.get_active_count() == 1
        
        guard.verify_and_release(
            key=key,
            submitter_id="test-submitter",
            transmission_success=True,
        )
        
        assert guard.get_active_count() == 0
    
    def test_verify_and_release_failure(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """verify_and_release() should release lock on failure."""
        guard = DuplicateSubmissionGuard(audit_logger)
        
        key = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="test-submitter",
        )
        
        guard.verify_and_release(
            key=key,
            submitter_id="test-submitter",
            transmission_success=False,
        )
        
        assert guard.get_active_count() == 0


class TestConcurrentSubmissions:
    """Tests for concurrent submission handling."""
    
    def test_concurrent_submissions_one_succeeds_one_fails(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """
        Two simultaneous submissions → one succeeds, one fails.
        
        Feature: human-authorized-submission, Property 14: Duplicate Prevention
        Validates: Requirements 4.11, 4.12
        """
        guard = DuplicateSubmissionGuard(audit_logger)
        barrier = Barrier(2)  # Synchronize two threads
        results: list[tuple[str, bool, Optional[Exception]]] = []
        
        def attempt_submission(submitter_id: str) -> None:
            """Attempt to acquire lock for submission."""
            barrier.wait()  # Wait for both threads to be ready
            try:
                key = guard.check_and_acquire(
                    decision_id="dec-123",
                    platform=Platform.HACKERONE,
                    submitter_id=submitter_id,
                )
                # Simulate transmission time
                time.sleep(0.05)
                # Log TRANSMITTED entry (simulating successful transmission)
                audit_logger.log(create_audit_entry(
                    submitter_id=submitter_id,
                    action=SubmissionAction.TRANSMITTED,
                    decision_id="dec-123",
                    platform=Platform.HACKERONE,
                ))
                guard.verify_and_release(key, submitter_id, True)
                results.append((submitter_id, True, None))
            except DuplicateSubmissionError as e:
                results.append((submitter_id, False, e))
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(attempt_submission, "submitter-1"),
                executor.submit(attempt_submission, "submitter-2"),
            ]
            for future in as_completed(futures):
                future.result()  # Raise any exceptions
        
        # Exactly one should succeed, one should fail
        successes = [r for r in results if r[1]]
        failures = [r for r in results if not r[1]]
        
        assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"
        assert len(failures) == 1, f"Expected 1 failure, got {len(failures)}"
        assert isinstance(failures[0][2], DuplicateSubmissionError)
    
    def test_concurrent_different_decisions_both_succeed(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """Concurrent submissions for different decisions should both succeed."""
        guard = DuplicateSubmissionGuard(audit_logger)
        barrier = Barrier(2)
        results: list[tuple[str, bool]] = []
        
        def attempt_submission(decision_id: str) -> None:
            barrier.wait()
            try:
                key = guard.check_and_acquire(
                    decision_id=decision_id,
                    platform=Platform.HACKERONE,
                    submitter_id="test-submitter",
                )
                time.sleep(0.01)
                audit_logger.log(create_audit_entry(
                    submitter_id="test-submitter",
                    action=SubmissionAction.TRANSMITTED,
                    decision_id=decision_id,
                    platform=Platform.HACKERONE,
                ))
                guard.verify_and_release(key, "test-submitter", True)
                results.append((decision_id, True))
            except DuplicateSubmissionError:
                results.append((decision_id, False))
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(attempt_submission, "dec-123"),
                executor.submit(attempt_submission, "dec-456"),
            ]
            for future in as_completed(futures):
                future.result()
        
        # Both should succeed
        assert all(r[1] for r in results)
    
    def test_many_concurrent_submissions_only_one_succeeds(
        self,
        audit_logger: SubmissionAuditLogger,
    ) -> None:
        """Many concurrent submissions for same key → exactly one succeeds."""
        guard = DuplicateSubmissionGuard(audit_logger)
        num_threads = 10
        barrier = Barrier(num_threads)
        results: list[bool] = []
        
        def attempt_submission(thread_id: int) -> None:
            barrier.wait()
            try:
                key = guard.check_and_acquire(
                    decision_id="dec-123",
                    platform=Platform.HACKERONE,
                    submitter_id=f"submitter-{thread_id}",
                )
                time.sleep(0.05)
                # Log TRANSMITTED entry
                audit_logger.log(create_audit_entry(
                    submitter_id=f"submitter-{thread_id}",
                    action=SubmissionAction.TRANSMITTED,
                    decision_id="dec-123",
                    platform=Platform.HACKERONE,
                ))
                guard.verify_and_release(key, f"submitter-{thread_id}", True)
                results.append(True)
            except DuplicateSubmissionError:
                results.append(False)
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(attempt_submission, i)
                for i in range(num_threads)
            ]
            for future in as_completed(futures):
                future.result()
        
        # Exactly one should succeed
        assert sum(results) == 1


class TestPropertyBased:
    """Property-based tests for DuplicateSubmissionGuard."""
    
    @given(
        decision_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        platform=st.sampled_from(list(Platform)),
    )
    @settings(max_examples=100)
    def test_property_uniqueness_invariant(
        self,
        decision_id: str,
        platform: Platform,
    ) -> None:
        """
        Property: decision_id + platform combination is unique.
        
        For any decision_id and platform, only ONE submission can succeed.
        All subsequent attempts MUST fail with DuplicateSubmissionError.
        
        Feature: human-authorized-submission, Property 14: Duplicate Prevention
        """
        assume(decision_id.strip())
        
        audit_logger = SubmissionAuditLogger()
        guard = DuplicateSubmissionGuard(audit_logger)
        
        # First submission succeeds
        key = guard.check_and_acquire(
            decision_id=decision_id,
            platform=platform,
            submitter_id="first-submitter",
        )
        
        # Simulate successful transmission
        audit_logger.log(create_audit_entry(
            submitter_id="first-submitter",
            action=SubmissionAction.TRANSMITTED,
            decision_id=decision_id,
            platform=platform,
        ))
        guard.verify_and_release(key, "first-submitter", True)
        
        # Second submission MUST fail
        with pytest.raises(DuplicateSubmissionError):
            guard.check_and_acquire(
                decision_id=decision_id,
                platform=platform,
                submitter_id="second-submitter",
            )
    
    @given(
        num_attempts=st.integers(min_value=2, max_value=10),
    )
    @settings(max_examples=100)
    def test_property_all_duplicates_logged(
        self,
        num_attempts: int,
    ) -> None:
        """
        Property: All duplicate attempts are logged to audit trail.
        
        Feature: human-authorized-submission, Property 14: Duplicate Prevention
        """
        audit_logger = SubmissionAuditLogger()
        guard = DuplicateSubmissionGuard(audit_logger)
        
        # First submission succeeds
        key = guard.check_and_acquire(
            decision_id="dec-123",
            platform=Platform.HACKERONE,
            submitter_id="first-submitter",
        )
        
        # Simulate successful transmission
        audit_logger.log(create_audit_entry(
            submitter_id="first-submitter",
            action=SubmissionAction.TRANSMITTED,
            decision_id="dec-123",
            platform=Platform.HACKERONE,
        ))
        guard.verify_and_release(key, "first-submitter", True)
        
        # All subsequent attempts fail and are logged
        for i in range(num_attempts - 1):
            with pytest.raises(DuplicateSubmissionError):
                guard.check_and_acquire(
                    decision_id="dec-123",
                    platform=Platform.HACKERONE,
                    submitter_id=f"submitter-{i}",
                )
        
        # Check all duplicates were logged
        blocked_entries = [
            e for e in audit_logger.get_chain()
            if e.action == SubmissionAction.DUPLICATE_BLOCKED
        ]
        assert len(blocked_entries) == num_attempts - 1
    
    @given(
        platforms=st.lists(
            st.sampled_from(list(Platform)),
            min_size=1,
            max_size=len(Platform),
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_property_same_decision_different_platforms(
        self,
        platforms: list[Platform],
    ) -> None:
        """
        Property: Same decision can be submitted to different platforms.
        
        The uniqueness constraint is decision_id + platform, not just decision_id.
        """
        audit_logger = SubmissionAuditLogger()
        guard = DuplicateSubmissionGuard(audit_logger)
        decision_id = "dec-123"
        
        # Submit to each platform
        for platform in platforms:
            key = guard.check_and_acquire(
                decision_id=decision_id,
                platform=platform,
                submitter_id="test-submitter",
            )
            audit_logger.log(create_audit_entry(
                submitter_id="test-submitter",
                action=SubmissionAction.TRANSMITTED,
                decision_id=decision_id,
                platform=platform,
            ))
            guard.verify_and_release(key, "test-submitter", True)
        
        # All platforms should show as submitted
        for platform in platforms:
            assert guard.is_submitted(decision_id, platform)
        
        # Count TRANSMITTED entries
        transmitted = [
            e for e in audit_logger.get_chain()
            if e.action == SubmissionAction.TRANSMITTED
        ]
        assert len(transmitted) == len(platforms)


# Fixtures
@pytest.fixture
def audit_logger() -> SubmissionAuditLogger:
    """Create a fresh audit logger for testing."""
    return SubmissionAuditLogger()


class TestDuplicateGuardNetworkIntegration:
    """Tests for DuplicateSubmissionGuard integration with NetworkTransmitManager."""
    
    def test_duplicate_blocked_in_network_manager(self) -> None:
        """
        Duplicate submission blocked when using NetworkTransmitManager.
        
        Feature: human-authorized-submission, Property 14: Duplicate Prevention
        """
        from submission_workflow.network import NetworkTransmitManager
        from submission_workflow.registry import ConfirmationRegistry
        from submission_workflow.tests.conftest import make_draft
        
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        guard = DuplicateSubmissionGuard(audit_logger)
        network_manager = NetworkTransmitManager(audit_logger, registry, guard)
        
        # Create draft and confirmation
        draft = make_draft()
        now = datetime.now()
        confirmation1 = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft.request_id,
            submitter_id="test-submitter",
            report_hash=draft.compute_hash(),
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        # Mock adapter
        class MockAdapter:
            def submit(self, report: DraftReport) -> tuple[str, str]:
                return ("platform-123", "Accepted")
        
        # First submission succeeds
        record1 = network_manager.transmit(
            confirmation=confirmation1,
            draft=draft,
            platform_adapter=MockAdapter(),
            submitter_id="test-submitter",
            decision_id="dec-123",
        )
        assert record1.status == SubmissionStatus.SUBMITTED
        
        # Second submission with new confirmation should fail (duplicate)
        confirmation2 = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft.request_id,
            submitter_id="test-submitter",
            report_hash=draft.compute_hash(),
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        with pytest.raises(DuplicateSubmissionError) as exc_info:
            network_manager.transmit(
                confirmation=confirmation2,
                draft=draft,
                platform_adapter=MockAdapter(),
                submitter_id="test-submitter",
                decision_id="dec-123",  # Same decision_id
            )
        
        assert exc_info.value.decision_id == "dec-123"
    
    def test_different_decision_allowed_in_network_manager(self) -> None:
        """Different decisions can be submitted through NetworkTransmitManager."""
        from submission_workflow.network import NetworkTransmitManager
        from submission_workflow.registry import ConfirmationRegistry
        from submission_workflow.tests.conftest import make_draft
        
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        guard = DuplicateSubmissionGuard(audit_logger)
        network_manager = NetworkTransmitManager(audit_logger, registry, guard)
        
        class MockAdapter:
            def submit(self, report: DraftReport) -> tuple[str, str]:
                return ("platform-123", "Accepted")
        
        # Submit first decision
        draft1 = make_draft()
        now = datetime.now()
        confirmation1 = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft1.request_id,
            submitter_id="test-submitter",
            report_hash=draft1.compute_hash(),
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        record1 = network_manager.transmit(
            confirmation=confirmation1,
            draft=draft1,
            platform_adapter=MockAdapter(),
            submitter_id="test-submitter",
            decision_id="dec-123",
        )
        assert record1.status == SubmissionStatus.SUBMITTED
        
        # Submit different decision
        draft2 = make_draft()
        confirmation2 = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft2.request_id,
            submitter_id="test-submitter",
            report_hash=draft2.compute_hash(),
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        record2 = network_manager.transmit(
            confirmation=confirmation2,
            draft=draft2,
            platform_adapter=MockAdapter(),
            submitter_id="test-submitter",
            decision_id="dec-456",  # Different decision_id
        )
        assert record2.status == SubmissionStatus.SUBMITTED
    
    def test_no_decision_id_skips_duplicate_check(self) -> None:
        """When decision_id is not provided, duplicate check is skipped."""
        from submission_workflow.network import NetworkTransmitManager
        from submission_workflow.registry import ConfirmationRegistry
        from submission_workflow.tests.conftest import make_draft
        
        audit_logger = SubmissionAuditLogger()
        registry = ConfirmationRegistry(audit_logger)
        guard = DuplicateSubmissionGuard(audit_logger)
        network_manager = NetworkTransmitManager(audit_logger, registry, guard)
        
        class MockAdapter:
            def submit(self, report: DraftReport) -> tuple[str, str]:
                return ("platform-123", "Accepted")
        
        # Submit without decision_id
        draft1 = make_draft()
        now = datetime.now()
        confirmation1 = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft1.request_id,
            submitter_id="test-submitter",
            report_hash=draft1.compute_hash(),
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        record1 = network_manager.transmit(
            confirmation=confirmation1,
            draft=draft1,
            platform_adapter=MockAdapter(),
            submitter_id="test-submitter",
            # No decision_id
        )
        assert record1.status == SubmissionStatus.SUBMITTED
        
        # Submit again without decision_id (different confirmation)
        draft2 = make_draft()
        confirmation2 = SubmissionConfirmation(
            confirmation_id=str(uuid.uuid4()),
            request_id=draft2.request_id,
            submitter_id="test-submitter",
            report_hash=draft2.compute_hash(),
            confirmed_at=now,
            expires_at=now + timedelta(minutes=15),
            submitter_signature="test-signature",
        )
        
        # Should succeed (no duplicate check without decision_id)
        record2 = network_manager.transmit(
            confirmation=confirmation2,
            draft=draft2,
            platform_adapter=MockAdapter(),
            submitter_id="test-submitter",
            # No decision_id
        )
        assert record2.status == SubmissionStatus.SUBMITTED


# Additional imports needed for integration tests
from datetime import datetime, timedelta
from submission_workflow.types import SubmissionConfirmation, SubmissionStatus
import uuid
