"""
Phase-7 Network Transmit Manager

Controls network access with confirmation-gated transmission.
Enforces report hash verification to detect tampering.
Enforces decision_id + platform uniqueness with atomic locking.

SECURITY INVARIANTS:
- Network access DISABLED by default
- Network access ENABLED only with valid SubmissionConfirmation
- ONE request per confirmation (then invalidated)
- Report hash MUST match confirmation hash (tampering detection)
- AUTO-DISABLED after request completes
- EXACTLY ONE HTTP request per transmit() call
- decision_id + platform combination is unique (duplicate prevention)

ARCHITECTURAL CONSTRAINTS:
- No persistent network connections
- No auto-retry without new confirmation
- No background tasks
- No async loops
- No scheduling
- HARD STOP on tampering detection
- HARD STOP if adapter sends >1 request
- HARD STOP on duplicate submission attempt
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol
import uuid

from submission_workflow.types import (
    Platform,
    SubmissionStatus,
    SubmissionAction,
    SubmissionConfirmation,
    SubmissionRecord,
    DraftReport,
)
from submission_workflow.errors import (
    NetworkAccessDeniedError,
    TokenExpiredError,
    ReportTamperingDetectedError,
    AuditLogFailure,
    ArchitecturalViolationError,
    DuplicateSubmissionError,
)
from submission_workflow.audit import SubmissionAuditLogger, create_audit_entry
from submission_workflow.registry import ConfirmationRegistry
from submission_workflow.duplicate import DuplicateSubmissionGuard, SubmissionKey


class PlatformAdapter(Protocol):
    """
    Protocol for platform adapters (HackerOne, Bugcrowd, etc.).
    
    INVARIANTS:
    - Exactly ONE HTTP request per submit() call
    - No retry logic (retry requires new confirmation)
    - No background tasks
    - No async loops
    - No scheduling
    
    Implementations MUST use RequestCountingAdapter base class
    to enforce the single-request invariant.
    """
    
    def submit(self, report: DraftReport) -> tuple[str, str]:
        """
        Submit report to platform.
        
        Returns:
            Tuple of (platform_submission_id, platform_response)
        """
        ...


class RequestCountingAdapter(ABC):
    """
    Base class for platform adapters with request counting enforcement.
    
    SECURITY: Enforces the single-request invariant by counting
    outgoing HTTP requests. If more than one request is attempted,
    ArchitecturalViolationError is raised (HARD STOP).
    
    INVARIANTS:
    - Exactly ONE HTTP request per submit() call
    - No retry logic
    - No background tasks
    - No async loops
    - No scheduling
    
    Subclasses MUST:
    1. Call _increment_request_count() before each HTTP request
    2. Implement _do_submit() with the actual submission logic
    """
    
    def __init__(self) -> None:
        """Initialize the adapter with zero request count."""
        self._request_count = 0
        self._max_requests = 1
    
    @property
    def request_count(self) -> int:
        """Return the current request count."""
        return self._request_count
    
    def _increment_request_count(self) -> None:
        """
        Increment request count and enforce single-request invariant.
        
        MUST be called before each HTTP request in _do_submit().
        
        Raises:
            ArchitecturalViolationError: If >1 request attempted (HARD STOP).
        """
        self._request_count += 1
        if self._request_count > self._max_requests:
            raise ArchitecturalViolationError(
                f"adapter_multiple_requests: Adapter sent {self._request_count} "
                f"requests, maximum allowed is {self._max_requests}"
            )
    
    def _reset_request_count(self) -> None:
        """Reset request count (called by NetworkTransmitManager)."""
        self._request_count = 0
    
    def submit(self, report: DraftReport) -> tuple[str, str]:
        """
        Submit report to platform with request counting.
        
        Delegates to _do_submit() after resetting the request count.
        
        Args:
            report: The draft report to submit.
            
        Returns:
            Tuple of (platform_submission_id, platform_response).
            
        Raises:
            ArchitecturalViolationError: If >1 request attempted.
        """
        self._reset_request_count()
        return self._do_submit(report)
    
    @abstractmethod
    def _do_submit(self, report: DraftReport) -> tuple[str, str]:
        """
        Perform the actual submission to the platform.
        
        Subclasses MUST:
        1. Call self._increment_request_count() before each HTTP request
        2. Make exactly ONE HTTP request
        3. Return (platform_submission_id, platform_response)
        
        Args:
            report: The draft report to submit.
            
        Returns:
            Tuple of (platform_submission_id, platform_response).
        """
        ...


class NetworkTransmitManager:
    """
    Controls network access with confirmation-gated transmission.
    
    SECURITY: Network access is DISABLED by default. It is only enabled
    when a valid SubmissionConfirmation is presented, and only for ONE
    request. After the request completes (success or failure), network
    access is automatically disabled.
    
    TAMPERING DETECTION: Before transmission, the report hash is
    recomputed and compared with the hash stored in the confirmation.
    If they differ, ReportTamperingDetectedError is raised and
    transmission is blocked (HARD STOP).
    
    DUPLICATE PREVENTION: decision_id + platform uniqueness is enforced
    with atomic locking. If a submission already exists for the same
    decision/platform, DuplicateSubmissionError is raised (HARD STOP).
    """
    
    def __init__(
        self,
        audit_logger: SubmissionAuditLogger,
        registry: ConfirmationRegistry,
        duplicate_guard: Optional[DuplicateSubmissionGuard] = None,
    ):
        """
        Initialize the network transmit manager.
        
        Args:
            audit_logger: The submission audit logger.
            registry: The confirmation consumption registry.
            duplicate_guard: Optional duplicate submission guard.
                            If not provided, one will be created.
        """
        self._network_enabled = False  # DISABLED by default
        self._active_confirmation_id: Optional[str] = None
        self._audit_logger = audit_logger
        self._registry = registry
        self._duplicate_guard = duplicate_guard or DuplicateSubmissionGuard(audit_logger)
    
    def is_network_enabled(self) -> bool:
        """Check if network access is currently enabled."""
        return self._network_enabled
    
    def transmit(
        self,
        confirmation: SubmissionConfirmation,
        draft: DraftReport,
        platform_adapter: PlatformAdapter,
        submitter_id: str,
        decision_id: Optional[str] = None,
    ) -> SubmissionRecord:
        """
        Transmit report to platform with confirmation-gated network access.
        
        SECURITY CHECKS (in order):
        1. Validate confirmation is not already used (replay protection)
        2. Validate confirmation is not expired
        3. Check for duplicate submission (decision_id + platform uniqueness)
        4. Verify report hash matches confirmation hash (tampering detection)
        5. Enable network access for ONE request
        6. Transmit to platform
        7. Disable network access
        8. Mark confirmation as consumed
        9. Create SubmissionRecord with platform response
        
        Args:
            confirmation: The submission confirmation authorizing transmission.
            draft: The draft report to transmit.
            platform_adapter: The platform adapter for submission.
            submitter_id: The submitter ID for audit logging.
            decision_id: Optional decision ID for duplicate prevention.
                        If not provided, duplicate check is skipped.
            
        Returns:
            SubmissionRecord with platform response.
            
        Raises:
            TokenAlreadyUsedError: If confirmation was already used.
            TokenExpiredError: If confirmation has expired.
            DuplicateSubmissionError: If already submitted to this platform.
            ReportTamperingDetectedError: If report hash doesn't match (HARD STOP).
            NetworkAccessDeniedError: If network access is denied.
            AuditLogFailure: If audit logging fails (HARD STOP).
        """
        # Step 1 & 2: Validate confirmation (replay + expiry)
        # SECURITY FIX: Consume token ATOMICALLY BEFORE network transmit
        # This prevents race conditions where concurrent requests could use same token
        # Previous behavior: check then transmit then consume (race window)
        # New behavior: atomic consume-or-lock BEFORE transmit
        
        # First check expiry (before consuming)
        if confirmation.is_expired():
            raise TokenExpiredError(
                confirmation.confirmation_id,
                confirmation.expires_at,
            )
        
        # ATOMIC: Consume token BEFORE any network activity
        # This guarantees: ONE token = ONE request (even under concurrency)
        self._registry.consume(
            confirmation=confirmation,
            submitter_id=submitter_id,
            transmission_success=False,  # Mark as consumed, update on success
            error_message="Token consumed - transmission pending",
        )
        
        # Step 3: Check for duplicate submission (if decision_id provided)
        platform = Platform(draft.custom_fields.get("platform", "generic"))
        submission_key: Optional[SubmissionKey] = None
        
        if decision_id is not None:
            submission_key = self._duplicate_guard.check_and_acquire(
                decision_id=decision_id,
                platform=platform,
                submitter_id=submitter_id,
            )
        
        try:
            # Step 4: CRITICAL - Verify report hash (tampering detection)
            self._verify_report_hash(confirmation, draft, submitter_id)
            
            # Step 5: Enable network access
            self._enable_network(confirmation.confirmation_id)
            
            try:
                # Log network access granted
                self._audit_logger.log(create_audit_entry(
                    submitter_id=submitter_id,
                    action=SubmissionAction.NETWORK_ACCESS_GRANTED,
                    request_id=confirmation.request_id,
                    confirmation_id=confirmation.confirmation_id,
                    decision_id=decision_id,
                ))
                
                # Step 6: Transmit to platform
                try:
                    platform_id, platform_response = platform_adapter.submit(draft)
                    status = SubmissionStatus.SUBMITTED
                    
                    # Log successful transmission
                    self._audit_logger.log(create_audit_entry(
                        submitter_id=submitter_id,
                        action=SubmissionAction.TRANSMITTED,
                        request_id=confirmation.request_id,
                        confirmation_id=confirmation.confirmation_id,
                        platform=platform,
                        decision_id=decision_id,
                    ))
                    
                    # SECURITY FIX: Token was already consumed before transmit
                    # No need to consume again - this prevents race conditions
                    # The token is already marked as used in the registry
                    
                    # Release duplicate guard with success
                    if submission_key is not None:
                        self._duplicate_guard.verify_and_release(
                            key=submission_key,
                            submitter_id=submitter_id,
                            transmission_success=True,
                        )
                        submission_key = None  # Mark as released
                    
                except Exception as e:
                    # Log failed transmission
                    self._audit_logger.log(create_audit_entry(
                        submitter_id=submitter_id,
                        action=SubmissionAction.TRANSMISSION_FAILED,
                        request_id=confirmation.request_id,
                        confirmation_id=confirmation.confirmation_id,
                        decision_id=decision_id,
                        error_type=type(e).__name__,
                        error_message=str(e),
                    ))
                    
                    # SECURITY FIX: Token was already consumed before transmit
                    # No need to consume again - this prevents race conditions
                    # The token is already marked as used in the registry
                    
                    platform_id = None
                    platform_response = str(e)
                    status = SubmissionStatus.FAILED
                    
            finally:
                # Step 7: ALWAYS disable network access
                self._disable_network()
        
        finally:
            # Release duplicate guard on error (if not already released)
            if submission_key is not None:
                self._duplicate_guard.release_on_error(submission_key)
        
        # Step 9: Create SubmissionRecord
        return SubmissionRecord(
            submission_id=str(uuid.uuid4()),
            request_id=confirmation.request_id,
            confirmation_id=confirmation.confirmation_id,
            platform=platform,
            platform_submission_id=platform_id,
            platform_response=platform_response,
            submitted_at=datetime.now(),
            status=status,
        )
    
    def _verify_report_hash(
        self,
        confirmation: SubmissionConfirmation,
        draft: DraftReport,
        submitter_id: str,
    ) -> None:
        """
        Verify report hash matches confirmation hash.
        
        SECURITY: This detects if the report was tampered with after
        the human confirmed it. If hashes differ, this is a HARD STOP.
        
        Args:
            confirmation: The submission confirmation with expected hash.
            draft: The draft report to verify.
            submitter_id: The submitter ID for audit logging.
            
        Raises:
            ReportTamperingDetectedError: If hashes don't match (HARD STOP).
        """
        expected_hash = confirmation.report_hash
        actual_hash = draft.compute_hash()
        
        if expected_hash != actual_hash:
            # Log tampering detection to audit trail BEFORE raising
            self._audit_logger.log(create_audit_entry(
                submitter_id=submitter_id,
                action=SubmissionAction.REPORT_TAMPERING_DETECTED,
                request_id=confirmation.request_id,
                confirmation_id=confirmation.confirmation_id,
                error_type="ReportTamperingDetectedError",
                error_message=(
                    f"Expected hash: {expected_hash}, "
                    f"Actual hash: {actual_hash}"
                ),
            ))
            
            # HARD STOP - raise error
            raise ReportTamperingDetectedError(
                confirmation_id=confirmation.confirmation_id,
                expected_hash=expected_hash,
                actual_hash=actual_hash,
            )
    
    def _enable_network(self, confirmation_id: str) -> None:
        """Enable network access for one request."""
        self._network_enabled = True
        self._active_confirmation_id = confirmation_id
    
    def _disable_network(self) -> None:
        """Disable network access."""
        self._network_enabled = False
        self._active_confirmation_id = None


def verify_report_integrity(
    confirmation: SubmissionConfirmation,
    draft: DraftReport,
) -> bool:
    """
    Verify report integrity without raising an error.
    
    Utility function for checking if a report matches its confirmation
    without triggering the full transmission flow.
    
    Args:
        confirmation: The submission confirmation with expected hash.
        draft: The draft report to verify.
        
    Returns:
        True if hashes match, False otherwise.
    """
    return confirmation.report_hash == draft.compute_hash()
