"""
Bounty Pipeline Core Data Types

All types are designed to enforce architectural boundaries:
- MCPFinding is READ-ONLY from MCP
- ValidatedFinding requires MCP BUG classification + proof
- SubmissionDraft requires human approval before submission
- ApprovalToken is one-time and expiring
- AuditRecord is immutable and hash-chained
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import hashlib
import secrets


class MCPClassification(str, Enum):
    """MCP classification types (from Phase-1, read-only)."""

    BUG = "BUG"
    SIGNAL = "SIGNAL"
    NO_ISSUE = "NO_ISSUE"
    COVERAGE_GAP = "COVERAGE_GAP"


class DraftStatus(str, Enum):
    """Status of a submission draft."""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    ARCHIVED = "archived"


class SubmissionStatus(str, Enum):
    """Status of a submission on the platform."""

    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    NEEDS_MORE_INFO = "needs_more_info"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PAID = "paid"
    UNKNOWN = "unknown"
    UNKNOWN_UNCONFIRMED = "unknown_unconfirmed"  # API unavailable, status cannot be confirmed


@dataclass(frozen=True)
class ProofChain:
    """Complete proof chain from MCP (immutable).

    This is READ-ONLY data from MCP. Bounty Pipeline
    MUST NOT modify or generate proof chains.
    """

    before_state: dict[str, Any]
    action_sequence: list[dict[str, Any]]
    after_state: dict[str, Any]
    causality_chain: list[dict[str, Any]]
    replay_instructions: list[dict[str, Any]]
    invariant_violated: str
    proof_hash: str

    def __post_init__(self) -> None:
        """Validate proof chain integrity."""
        if not self.proof_hash:
            raise ValueError("ProofChain must have proof_hash")
        if not self.invariant_violated:
            raise ValueError("ProofChain must specify invariant_violated")


@dataclass(frozen=True)
class MCPFinding:
    """Finding from MCP (read-only for Bounty Pipeline).

    This is READ-ONLY data from MCP. Bounty Pipeline
    MUST NOT modify MCP findings or generate new ones.
    """

    finding_id: str
    classification: MCPClassification
    invariant_violated: Optional[str]
    proof: Optional[ProofChain]
    severity: str
    cyfer_brain_observation_id: str
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate MCP finding."""
        if not self.finding_id:
            raise ValueError("MCPFinding must have finding_id")

    @property
    def has_valid_proof(self) -> bool:
        """Check if finding has valid proof for submission."""
        return (
            self.classification == MCPClassification.BUG
            and self.proof is not None
            and self.invariant_violated is not None
        )


@dataclass(frozen=True)
class SourceLinks:
    """Links to original MCP proof and Cyfer Brain observation."""

    mcp_proof_id: str
    mcp_proof_hash: str
    cyfer_brain_observation_id: str
    linked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ValidatedFinding:
    """Finding that passed validation (has MCP BUG + proof).

    A ValidatedFinding can ONLY be created from an MCPFinding
    that has BUG classification and valid proof chain.
    """

    finding_id: str
    mcp_finding: MCPFinding
    proof_chain: ProofChain
    source_links: SourceLinks
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate that finding meets requirements."""
        if self.mcp_finding.classification != MCPClassification.BUG:
            raise ValueError("ValidatedFinding requires MCP BUG classification")
        if self.mcp_finding.proof is None:
            raise ValueError("ValidatedFinding requires MCP proof")


@dataclass(frozen=True)
class ReproductionStep:
    """Single step in reproduction instructions."""

    step_number: int
    action: str
    expected_result: str
    actual_result: Optional[str] = None


@dataclass
class SubmissionDraft:
    """Draft report awaiting human approval.

    A draft MUST be reviewed and approved by a human
    before it can be submitted to any platform.
    """

    draft_id: str
    finding: ValidatedFinding
    platform: str
    report_title: str
    report_body: str
    severity: str  # Mapped from MCP severity (deterministic)
    reproduction_steps: list[ReproductionStep]
    proof_summary: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: DraftStatus = DraftStatus.PENDING_REVIEW
    rejection_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_token_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate draft."""
        if not self.draft_id:
            raise ValueError("SubmissionDraft must have draft_id")
        if not self.report_title:
            raise ValueError("SubmissionDraft must have report_title")

    @property
    def is_approved(self) -> bool:
        """Check if draft has been approved."""
        return self.status == DraftStatus.APPROVED and self.approval_token_id is not None

    @property
    def can_submit(self) -> bool:
        """Check if draft can be submitted."""
        return self.is_approved and self.status != DraftStatus.SUBMITTED

    def compute_hash(self) -> str:
        """Compute hash of draft content for approval verification."""
        content = f"{self.draft_id}:{self.report_title}:{self.report_body}:{self.severity}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass(frozen=True)
class ApprovalToken:
    """One-time token proving human approval.

    Tokens are:
    - One-time use only
    - Tied to specific draft content (via hash)
    - Short-lived (expire quickly for security)
    """

    token_id: str
    approver_id: str
    approved_at: datetime
    draft_hash: str  # Hash of approved content
    expires_at: datetime

    def __post_init__(self) -> None:
        """Validate token."""
        if not self.token_id:
            raise ValueError("ApprovalToken must have token_id")
        if not self.approver_id:
            raise ValueError("ApprovalToken must have approver_id")
        if not self.draft_hash:
            raise ValueError("ApprovalToken must have draft_hash")

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def matches_draft(self, draft: SubmissionDraft) -> bool:
        """Check if token matches draft content."""
        return self.draft_hash == draft.compute_hash()

    @staticmethod
    def generate(
        approver_id: str,
        draft: SubmissionDraft,
        validity_minutes: int = 30,
    ) -> "ApprovalToken":
        """Generate a new approval token for a draft."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta

        return ApprovalToken(
            token_id=secrets.token_urlsafe(32),
            approver_id=approver_id,
            approved_at=now,
            draft_hash=draft.compute_hash(),
            expires_at=now + timedelta(minutes=validity_minutes),
        )


@dataclass(frozen=True)
class SubmissionReceipt:
    """Confirmation from platform that report was received."""

    platform: str
    submission_id: str
    submitted_at: datetime
    receipt_data: dict[str, Any]
    receipt_hash: str  # For audit trail

    def __post_init__(self) -> None:
        """Validate receipt."""
        if not self.submission_id:
            raise ValueError("SubmissionReceipt must have submission_id")


@dataclass(frozen=True)
class AuthorizationDocument:
    """Legal document authorizing testing."""

    program_name: str
    authorized_domains: tuple[str, ...]
    authorized_ip_ranges: tuple[str, ...]
    excluded_paths: tuple[str, ...]
    valid_from: datetime
    valid_until: datetime
    document_hash: str  # For audit trail

    def __post_init__(self) -> None:
        """Validate authorization document."""
        if not self.program_name:
            raise ValueError("AuthorizationDocument must have program_name")
        if not self.document_hash:
            raise ValueError("AuthorizationDocument must have document_hash")

    @property
    def is_expired(self) -> bool:
        """Check if authorization has expired."""
        return datetime.now(timezone.utc) > self.valid_until

    @property
    def is_active(self) -> bool:
        """Check if authorization is currently active."""
        now = datetime.now(timezone.utc)
        return self.valid_from <= now <= self.valid_until


@dataclass(frozen=True)
class AuditRecord:
    """Immutable audit record with hash chain.

    Audit records are:
    - Append-only (cannot be modified or deleted)
    - Hash-chained (tamper-evident)
    - Complete (record all actions)
    """

    record_id: str
    timestamp: datetime
    action_type: str
    actor: str  # "system" or human identifier
    outcome: str
    details: dict[str, Any]
    mcp_proof_link: Optional[str]
    cyfer_brain_observation_link: Optional[str]
    previous_hash: str  # Hash chain
    record_hash: str

    def __post_init__(self) -> None:
        """Validate audit record."""
        if not self.record_id:
            raise ValueError("AuditRecord must have record_id")
        if not self.record_hash:
            raise ValueError("AuditRecord must have record_hash")

    @staticmethod
    def compute_hash(
        record_id: str,
        timestamp: datetime,
        action_type: str,
        actor: str,
        outcome: str,
        details: dict[str, Any],
        previous_hash: str,
    ) -> str:
        """Compute hash for audit record."""
        import json

        content = f"{record_id}:{timestamp.isoformat()}:{action_type}:{actor}:{outcome}"
        content += f":{json.dumps(details, sort_keys=True)}:{previous_hash}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass(frozen=True)
class DuplicateCandidate:
    """Potential duplicate of a previous submission."""

    original_finding_id: str
    original_submission_id: str
    similarity_score: float  # NOT confidence — just similarity metric
    comparison_details: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate duplicate candidate."""
        if not 0.0 <= self.similarity_score <= 1.0:
            raise ValueError("similarity_score must be between 0.0 and 1.0")


@dataclass
class StatusUpdate:
    """Update to submission status."""

    submission_id: str
    old_status: SubmissionStatus
    new_status: SubmissionStatus
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    platform_data: dict[str, Any] = field(default_factory=dict)
    bounty_amount: Optional[float] = None  # Only if PAID
    rejection_reason: Optional[str] = None  # Only if REJECTED

    def __post_init__(self) -> None:
        """Validate status update."""
        if self.new_status == SubmissionStatus.PAID and self.bounty_amount is None:
            # Don't require bounty_amount — some programs don't disclose
            pass
        if self.new_status == SubmissionStatus.REJECTED and self.rejection_reason is None:
            # Don't require rejection_reason — some platforms don't provide
            pass
