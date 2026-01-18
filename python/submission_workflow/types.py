"""
Phase-7 Data Types

Immutable data models for the Human-Authorized Submission Workflow.
All core types use frozen dataclasses to ensure immutability.

ARCHITECTURAL CONSTRAINTS:
- All data models are frozen (immutable)
- SubmissionRequest references HumanDecision.decision_id
- SubmissionConfirmation authorizes exactly ONE network request
- Audit entries include hash chain for integrity
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import hashlib


class Platform(Enum):
    """Supported bug bounty platforms."""
    HACKERONE = "hackerone"
    BUGCROWD = "bugcrowd"
    GENERIC = "generic"


class SubmissionStatus(Enum):
    """Status of a submission through its lifecycle."""
    PENDING = "pending"           # Request created, not confirmed
    CONFIRMED = "confirmed"       # Human confirmed, ready to transmit
    SUBMITTED = "submitted"       # Transmitted to platform
    ACKNOWLEDGED = "acknowledged" # Platform acknowledged receipt
    REJECTED = "rejected"         # Platform rejected submission
    FAILED = "failed"             # Transmission failed


# Valid status transitions (state diagram)
# PENDING → CONFIRMED → SUBMITTED → ACKNOWLEDGED
#                 ↓           ↓
#              FAILED      REJECTED
VALID_STATUS_TRANSITIONS: dict[SubmissionStatus, set[SubmissionStatus]] = {
    SubmissionStatus.PENDING: {SubmissionStatus.CONFIRMED},
    SubmissionStatus.CONFIRMED: {SubmissionStatus.SUBMITTED, SubmissionStatus.FAILED},
    SubmissionStatus.SUBMITTED: {SubmissionStatus.ACKNOWLEDGED, SubmissionStatus.REJECTED},
    SubmissionStatus.ACKNOWLEDGED: set(),  # Terminal state
    SubmissionStatus.REJECTED: set(),      # Terminal state
    SubmissionStatus.FAILED: set(),        # Terminal state
}


class SubmissionStatusMachine:
    """
    State machine for SubmissionStatus transitions.
    
    Enforces the valid state diagram:
    
    PENDING → CONFIRMED → SUBMITTED → ACKNOWLEDGED
                    ↓           ↓
                 FAILED      REJECTED
    
    SECURITY: This prevents bypassing the human confirmation step.
    A submission MUST go through CONFIRMED before reaching SUBMITTED.
    
    Usage:
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        machine.transition(SubmissionStatus.CONFIRMED)  # OK
        machine.transition(SubmissionStatus.SUBMITTED)  # OK
        
        # Invalid:
        machine = SubmissionStatusMachine(SubmissionStatus.PENDING)
        machine.transition(SubmissionStatus.SUBMITTED)  # Raises InvalidStatusTransitionError
    """
    
    def __init__(self, initial_status: SubmissionStatus = SubmissionStatus.PENDING):
        """
        Initialize the state machine.
        
        Args:
            initial_status: The starting status (default: PENDING).
        """
        self._current_status = initial_status
    
    @property
    def current_status(self) -> SubmissionStatus:
        """Return the current status."""
        return self._current_status
    
    def can_transition(self, to_status: SubmissionStatus) -> bool:
        """
        Check if a transition is valid without performing it.
        
        Args:
            to_status: The target status.
            
        Returns:
            True if the transition is valid, False otherwise.
        """
        valid_targets = VALID_STATUS_TRANSITIONS.get(self._current_status, set())
        return to_status in valid_targets
    
    def transition(self, to_status: SubmissionStatus) -> SubmissionStatus:
        """
        Transition to a new status.
        
        Args:
            to_status: The target status.
            
        Returns:
            The new status.
            
        Raises:
            InvalidStatusTransitionError: If the transition is invalid.
        """
        from submission_workflow.errors import InvalidStatusTransitionError
        
        if not self.can_transition(to_status):
            raise InvalidStatusTransitionError(self._current_status, to_status)
        
        self._current_status = to_status
        return self._current_status
    
    def is_terminal(self) -> bool:
        """
        Check if the current status is a terminal state.
        
        Terminal states: ACKNOWLEDGED, REJECTED, FAILED
        
        Returns:
            True if in a terminal state.
        """
        return len(VALID_STATUS_TRANSITIONS.get(self._current_status, set())) == 0
    
    @staticmethod
    def get_valid_transitions(from_status: SubmissionStatus) -> set[SubmissionStatus]:
        """
        Get valid target statuses from a given status.
        
        Args:
            from_status: The source status.
            
        Returns:
            Set of valid target statuses.
        """
        return VALID_STATUS_TRANSITIONS.get(from_status, set()).copy()
    
    @staticmethod
    def validate_transition(
        from_status: SubmissionStatus,
        to_status: SubmissionStatus,
    ) -> bool:
        """
        Validate a transition without a state machine instance.
        
        Args:
            from_status: The source status.
            to_status: The target status.
            
        Returns:
            True if the transition is valid.
        """
        valid_targets = VALID_STATUS_TRANSITIONS.get(from_status, set())
        return to_status in valid_targets


class SubmissionAction(Enum):
    """Actions logged to the submission audit trail."""
    REQUEST_CREATED = "request_created"
    CONFIRMATION_REQUESTED = "confirmation_requested"
    CONFIRMED = "confirmed"
    CONFIRMATION_CONSUMED = "confirmation_consumed"
    CONFIRMATION_REPLAY_BLOCKED = "confirmation_replay_blocked"
    REPORT_TAMPERING_DETECTED = "report_tampering_detected"
    NETWORK_ACCESS_GRANTED = "network_access_granted"
    NETWORK_ACCESS_DENIED = "network_access_denied"
    TRANSMITTED = "transmitted"
    TRANSMISSION_FAILED = "transmission_failed"
    PLATFORM_ACKNOWLEDGED = "platform_acknowledged"
    PLATFORM_REJECTED = "platform_rejected"
    DUPLICATE_BLOCKED = "duplicate_blocked"
    PERMISSION_DENIED = "permission_denied"


@dataclass(frozen=True)
class SubmissionRequest:
    """
    Immutable record linking a HumanDecision to a submission intent.
    
    TRACEABILITY: Every SubmissionRequest MUST reference a decision_id
    from Phase-6. This creates an unbreakable audit chain from
    human decision to platform submission.
    """
    request_id: str
    decision_id: str          # Reference to Phase-6 HumanDecision
    finding_id: str           # From HumanDecision
    severity: str             # From HumanDecision (NOT recalculated)
    platform: Platform
    submitter_id: str
    created_at: datetime
    status: SubmissionStatus = SubmissionStatus.PENDING


@dataclass(frozen=True)
class SubmissionConfirmation:
    """
    Explicit human confirmation authorizing network transmission.
    
    NETWORK GATE: Network access is DISABLED until a valid
    SubmissionConfirmation is presented. Each confirmation
    authorizes exactly ONE network request.
    
    SECURITY: Once used, the confirmation_id is recorded in the
    ConfirmationRegistry and cannot be reused. This prevents
    replay attacks.
    """
    confirmation_id: str
    request_id: str
    submitter_id: str
    report_hash: str          # SHA-256 of draft report content
    confirmed_at: datetime
    expires_at: datetime      # 15 minutes from confirmed_at
    submitter_signature: str  # Cryptographic signature
    
    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Check if confirmation has expired."""
        check_time = now or datetime.now()
        return check_time > self.expires_at


@dataclass(frozen=True)
class SubmissionRecord:
    """
    Immutable record of a completed submission with platform response.
    """
    submission_id: str
    request_id: str
    confirmation_id: str
    platform: Platform
    platform_submission_id: Optional[str]  # ID from platform
    platform_response: str                  # Raw response
    submitted_at: datetime
    status: SubmissionStatus


@dataclass(frozen=True)
class UsedConfirmation:
    """
    Record of a consumed confirmation in the registry.
    
    This record is created immediately after a transmission attempt
    (success or failure) to prevent replay attacks.
    """
    confirmation_id: str
    request_id: str
    used_at: datetime
    transmission_success: bool
    error_message: Optional[str] = None


@dataclass(frozen=True)
class SubmissionAuditEntry:
    """
    Immutable audit log entry with hash chain integrity.
    
    SEPARATION: This audit log is SEPARATE from Phase-6 audit log.
    Phase-7 MUST NOT write to Phase-6 audit log.
    """
    entry_id: str
    timestamp: datetime
    action: SubmissionAction
    submitter_id: str
    request_id: Optional[str] = None
    confirmation_id: Optional[str] = None
    submission_id: Optional[str] = None
    platform: Optional[Platform] = None
    decision_id: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    previous_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of entry content."""
        platform_str = self.platform.value if self.platform else "None"
        content = (
            f"{self.entry_id}|{self.timestamp.isoformat()}|"
            f"{self.action.value}|{self.submitter_id}|"
            f"{self.request_id}|{self.confirmation_id}|"
            f"{self.submission_id}|{platform_str}|"
            f"{self.decision_id}|{self.previous_hash}"
        )
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class DraftReport:
    """
    Editable draft report for human review before submission.
    
    NOTE: This is the ONLY mutable data model in Phase-7.
    It becomes immutable once confirmed (via report_hash in confirmation).
    
    SECURITY: At transmission time, the hash is recomputed and compared
    with the hash stored in SubmissionConfirmation. If they differ,
    ReportTamperingDetectedError is raised and transmission is blocked.
    """
    draft_id: str
    request_id: str
    title: str
    description: str
    severity: str                  # From HumanDecision, NOT editable
    classification: Optional[str]  # From MCP, NOT editable
    evidence_references: list[str] # Links only, no generation
    custom_fields: dict[str, str]  # Platform-specific fields
    
    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of report content.
        
        This hash is stored in SubmissionConfirmation at confirmation time
        and verified at transmission time to detect tampering.
        """
        # Sort evidence_references for deterministic hashing
        sorted_refs = sorted(self.evidence_references)
        # Sort custom_fields for deterministic hashing
        sorted_fields = sorted(self.custom_fields.items())
        
        content = (
            f"{self.draft_id}|{self.request_id}|{self.title}|"
            f"{self.description}|{self.severity}|{self.classification}|"
            f"{sorted_refs}|{sorted_fields}"
        )
        return hashlib.sha256(content.encode()).hexdigest()
