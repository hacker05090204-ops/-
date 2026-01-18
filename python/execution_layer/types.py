"""
Execution Layer Core Data Types

All types enforce architectural boundaries:
- ExecutionToken is one-time and expiring
- SafeAction is validated against allow-list
- EvidenceBundle includes tamper-evident hashes
- ExecutionAuditRecord is immutable and hash-chained
- VideoPoC has idempotency guard (one per finding_id)
- StoreOwnershipAttestation required for Shopify targets

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional, FrozenSet
import hashlib
import secrets


class SafeActionType(str, Enum):
    """Explicitly allowed safe action types."""
    NAVIGATE = "navigate"
    CLICK = "click"
    INPUT_TEXT = "input_text"  # Non-sensitive data only
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    GET_TEXT = "get_text"
    GET_ATTRIBUTE = "get_attribute"
    HOVER = "hover"
    SELECT_OPTION = "select_option"


class ForbiddenActionType(str, Enum):
    """Explicitly forbidden action types — HARD STOP."""
    LOGIN = "login"
    AUTHENTICATE = "authenticate"
    CREATE_ACCOUNT = "create_account"
    DELETE_ACCOUNT = "delete_account"
    MODIFY_DATA = "modify_data"
    DELETE_DATA = "delete_data"
    BYPASS_CAPTCHA = "bypass_captcha"
    BYPASS_AUTH = "bypass_auth"
    SUBMIT_FORM = "submit_form"  # Could modify data
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"
    EXECUTE_SCRIPT = "execute_script"
    IMPERSONATE = "impersonate"
    ACCESS_ADMIN = "access_admin"
    PAYMENT = "payment"
    CHECKOUT = "checkout"


class EvidenceType(str, Enum):
    """Types of evidence captured during execution."""
    HAR = "har"
    SCREENSHOT = "screenshot"
    VIDEO = "video"
    CONSOLE_LOG = "console_log"
    EXECUTION_TRACE = "execution_trace"
    NETWORK_REQUEST = "network_request"


class ExecutionStatus(str, Enum):
    """Status of an execution."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MCPClassification(str, Enum):
    """MCP classification types (from Phase-1, read-only)."""
    BUG = "BUG"
    SIGNAL = "SIGNAL"
    NO_ISSUE = "NO_ISSUE"
    COVERAGE_GAP = "COVERAGE_GAP"


@dataclass(frozen=True)
class StoreOwnershipAttestation:
    """Human-provided attestation of store ownership for Shopify targets.
    
    REQUIRED before any Shopify store can be tested.
    """
    attestation_id: str
    store_domain: str
    attester_id: str  # Human who attests ownership
    attested_at: datetime
    attestation_hash: str
    expires_at: datetime
    
    def __post_init__(self) -> None:
        if not self.attestation_id:
            raise ValueError("StoreOwnershipAttestation must have attestation_id")
        if not self.store_domain:
            raise ValueError("StoreOwnershipAttestation must have store_domain")
        if not self.attester_id:
            raise ValueError("StoreOwnershipAttestation must have attester_id")
        if not self.attestation_hash:
            raise ValueError("StoreOwnershipAttestation must have attestation_hash")
    
    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        return not self.is_expired
    
    @staticmethod
    def create(
        store_domain: str,
        attester_id: str,
        validity_days: int = 30,
    ) -> "StoreOwnershipAttestation":
        now = datetime.now(timezone.utc)
        attestation_id = secrets.token_urlsafe(16)
        content = f"{attestation_id}:{store_domain}:{attester_id}:{now.isoformat()}"
        attestation_hash = hashlib.sha256(content.encode()).hexdigest()
        return StoreOwnershipAttestation(
            attestation_id=attestation_id,
            store_domain=store_domain,
            attester_id=attester_id,
            attested_at=now,
            attestation_hash=attestation_hash,
            expires_at=now + timedelta(days=validity_days),
        )


@dataclass(frozen=True)
class SafeAction:
    """Safe, non-destructive action for execution.
    
    Actions MUST be validated against SAFE_ACTIONS allow-list.
    Actions in FORBIDDEN_ACTIONS cause HARD STOP.
    """
    action_id: str
    action_type: SafeActionType
    target: str  # URL or CSS selector
    parameters: dict[str, Any]
    description: str
    
    def __post_init__(self) -> None:
        if not self.action_id:
            raise ValueError("SafeAction must have action_id")
        if not isinstance(self.action_type, SafeActionType):
            raise ValueError(f"Invalid action_type: {self.action_type}")
    
    def compute_hash(self) -> str:
        """Compute hash of action for token binding."""
        import json
        content = f"{self.action_id}:{self.action_type.value}:{self.target}"
        content += f":{json.dumps(self.parameters, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass(frozen=True)
class ExecutionToken:
    """One-time token proving human approval for execution.
    
    Tokens are:
    - One-time use only (invalidated after use)
    - Tied to specific action(s) via hash
    - Short-lived (expire quickly for security)
    """
    token_id: str
    approver_id: str
    approved_at: datetime
    action_hash: str  # Hash of approved action(s)
    expires_at: datetime
    is_batch: bool = False
    batch_size: int = 1
    
    def __post_init__(self) -> None:
        if not self.token_id:
            raise ValueError("ExecutionToken must have token_id")
        if not self.approver_id:
            raise ValueError("ExecutionToken must have approver_id")
        if not self.action_hash:
            raise ValueError("ExecutionToken must have action_hash")
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
    
    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
    
    def matches_action(self, action: SafeAction) -> bool:
        """Check if token matches single action."""
        return self.action_hash == action.compute_hash() and not self.is_batch
    
    def matches_batch(self, actions: list[SafeAction]) -> bool:
        """Check if token matches batch of actions."""
        if not self.is_batch:
            return False
        batch_hash = ExecutionBatch.compute_batch_hash(actions)
        return self.action_hash == batch_hash and len(actions) == self.batch_size
    
    @staticmethod
    def generate(
        approver_id: str,
        action: SafeAction,
        validity_minutes: int = 15,
    ) -> "ExecutionToken":
        now = datetime.now(timezone.utc)
        return ExecutionToken(
            token_id=secrets.token_urlsafe(32),
            approver_id=approver_id,
            approved_at=now,
            action_hash=action.compute_hash(),
            expires_at=now + timedelta(minutes=validity_minutes),
            is_batch=False,
            batch_size=1,
        )
    
    @staticmethod
    def generate_batch(
        approver_id: str,
        actions: list[SafeAction],
        validity_minutes: int = 30,
    ) -> "ExecutionToken":
        if not actions:
            raise ValueError("Cannot create batch token for empty action list")
        now = datetime.now(timezone.utc)
        batch_hash = ExecutionBatch.compute_batch_hash(actions)
        return ExecutionToken(
            token_id=secrets.token_urlsafe(32),
            approver_id=approver_id,
            approved_at=now,
            action_hash=batch_hash,
            expires_at=now + timedelta(minutes=validity_minutes),
            is_batch=True,
            batch_size=len(actions),
        )


@dataclass(frozen=True)
class ExecutionBatch:
    """Batch of safe actions approved under ONE human approval token.
    
    Allows efficient execution of multiple safe actions without
    requiring separate approval for each action.
    """
    batch_id: str
    actions: tuple[SafeAction, ...]
    token: ExecutionToken
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self) -> None:
        if not self.batch_id:
            raise ValueError("ExecutionBatch must have batch_id")
        if not self.actions:
            raise ValueError("ExecutionBatch must have at least one action")
        if not self.token.is_batch:
            raise ValueError("ExecutionBatch requires a batch token")
        if len(self.actions) != self.token.batch_size:
            raise ValueError("Action count must match token batch_size")
    
    @staticmethod
    def compute_batch_hash(actions: list[SafeAction]) -> str:
        """Compute combined hash for batch of actions."""
        action_hashes = [a.compute_hash() for a in actions]
        combined = ":".join(sorted(action_hashes))
        return hashlib.sha256(combined.encode()).hexdigest()


@dataclass(frozen=True)
class EvidenceArtifact:
    """Single piece of captured evidence with tamper-evident hash."""
    artifact_id: str
    artifact_type: EvidenceType
    content_hash: str
    captured_at: datetime
    file_path: Optional[str] = None
    content: Optional[bytes] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("EvidenceArtifact must have artifact_id")
        if not self.content_hash:
            raise ValueError("EvidenceArtifact must have content_hash")
        
        # SECURITY: Validate file_path for path traversal (RISK-X1)
        if self.file_path is not None:
            from execution_layer.security import validate_file_path_relative
            validate_file_path_relative(self.file_path)
    
    @staticmethod
    def create(
        artifact_type: EvidenceType,
        content: bytes,
        metadata: Optional[dict[str, Any]] = None,
        file_path: Optional[str] = None,
    ) -> "EvidenceArtifact":
        artifact_id = secrets.token_urlsafe(16)
        content_hash = hashlib.sha256(content).hexdigest()
        return EvidenceArtifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            content_hash=content_hash,
            captured_at=datetime.now(timezone.utc),
            file_path=file_path,
            content=content,
            metadata=metadata or {},
        )


@dataclass
class EvidenceBundle:
    """Complete evidence bundle for an execution."""
    bundle_id: str
    execution_id: str
    har_file: Optional[EvidenceArtifact] = None
    screenshots: list[EvidenceArtifact] = field(default_factory=list)
    video: Optional[EvidenceArtifact] = None
    console_logs: list[EvidenceArtifact] = field(default_factory=list)
    execution_trace: list[dict[str, Any]] = field(default_factory=list)
    failure_count: int = 0
    bundle_hash: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self) -> None:
        if not self.bundle_id:
            raise ValueError("EvidenceBundle must have bundle_id")
        if not self.execution_id:
            raise ValueError("EvidenceBundle must have execution_id")
        
        # SECURITY: Validate execution_id format (RISK-X1)
        from execution_layer.security import (
            validate_execution_id,
            validate_har_is_redacted,
            GovernanceViolation,
        )
        try:
            validate_execution_id(self.execution_id)
        except GovernanceViolation:
            raise  # Re-raise GovernanceViolation as-is
        except Exception as e:
            raise ValueError(f"Invalid execution_id: {e}")
        
        # SECURITY: Validate HAR is redacted if present (RISK-X2)
        if self.har_file is not None and self.har_file.content is not None:
            validate_har_is_redacted(self.har_file.content)
    
    def compute_hash(self) -> str:
        """Compute tamper-evident hash for entire bundle."""
        import json
        parts = [self.bundle_id, self.execution_id]
        if self.har_file:
            parts.append(self.har_file.content_hash)
        for ss in self.screenshots:
            parts.append(ss.content_hash)
        if self.video:
            parts.append(self.video.content_hash)
        for log in self.console_logs:
            parts.append(log.content_hash)
        parts.append(json.dumps(self.execution_trace, sort_keys=True))
        parts.append(str(self.failure_count))
        return hashlib.sha256(":".join(parts).encode()).hexdigest()
    
    def finalize(self) -> "EvidenceBundle":
        """Finalize bundle by computing hash."""
        self.bundle_hash = self.compute_hash()
        return self


@dataclass(frozen=True)
class VideoPoC:
    """Video proof-of-concept for confirmed bug.
    
    IDEMPOTENCY GUARD: Only ONE VideoPoC per finding_id.
    Video recording is OFF by default, enabled only for:
    - MCP-confirmed BUG classification
    - Human escalation request
    """
    poc_id: str
    finding_id: str  # Unique - one video per finding
    video_artifact: EvidenceArtifact
    execution_trace: tuple[dict[str, Any], ...]
    timestamps: tuple[tuple[float, str], ...]  # (time, event)
    created_at: datetime
    poc_hash: str
    
    def __post_init__(self) -> None:
        if not self.poc_id:
            raise ValueError("VideoPoC must have poc_id")
        if not self.finding_id:
            raise ValueError("VideoPoC must have finding_id")
        if not self.poc_hash:
            raise ValueError("VideoPoC must have poc_hash")
    
    @staticmethod
    def create(
        finding_id: str,
        video_artifact: EvidenceArtifact,
        execution_trace: list[dict[str, Any]],
        timestamps: list[tuple[float, str]],
    ) -> "VideoPoC":
        poc_id = secrets.token_urlsafe(16)
        now = datetime.now(timezone.utc)
        content = f"{poc_id}:{finding_id}:{video_artifact.content_hash}:{now.isoformat()}"
        poc_hash = hashlib.sha256(content.encode()).hexdigest()
        return VideoPoC(
            poc_id=poc_id,
            finding_id=finding_id,
            video_artifact=video_artifact,
            execution_trace=tuple(execution_trace),
            timestamps=tuple(timestamps),
            created_at=now,
            poc_hash=poc_hash,
        )


@dataclass(frozen=True)
class MCPVerificationResult:
    """Result from MCP verification (read-only from MCP)."""
    verification_id: str
    finding_id: str
    classification: MCPClassification
    invariant_violated: Optional[str]
    proof_hash: Optional[str]
    verified_at: datetime
    
    @property
    def is_bug(self) -> bool:
        return self.classification == MCPClassification.BUG


@dataclass
class ExecutionResult:
    """Result of action execution."""
    execution_id: str
    action: SafeAction
    success: bool
    evidence_bundle: Optional[EvidenceBundle] = None
    mcp_verification: Optional[MCPVerificationResult] = None
    video_poc: Optional[VideoPoC] = None
    draft_id: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    def complete(self, success: bool, error: Optional[str] = None) -> "ExecutionResult":
        self.success = success
        self.error = error
        self.completed_at = datetime.now(timezone.utc)
        return self


@dataclass(frozen=True)
class ExecutionAuditRecord:
    """Immutable audit record with hash chain."""
    record_id: str
    timestamp: datetime
    action_type: str
    actor: str  # Human approver ID
    action: SafeAction
    outcome: str
    evidence_bundle_id: Optional[str]
    approval_token_id: str
    previous_hash: str
    record_hash: str
    
    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("ExecutionAuditRecord must have record_id")
        if not self.record_hash:
            raise ValueError("ExecutionAuditRecord must have record_hash")
    
    @staticmethod
    def compute_hash(
        record_id: str,
        timestamp: datetime,
        action_type: str,
        actor: str,
        action_hash: str,
        outcome: str,
        previous_hash: str,
    ) -> str:
        content = f"{record_id}:{timestamp.isoformat()}:{action_type}:{actor}"
        content += f":{action_hash}:{outcome}:{previous_hash}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass(frozen=True)
class DuplicateExplorationConfig:
    """Configuration for duplicate exploration STOP conditions."""
    max_depth: int = 3  # Maximum exploration depth
    max_hypotheses: int = 5  # Maximum hypotheses to generate
    max_total_actions: int = 20  # Maximum total actions in exploration
    
    def __post_init__(self) -> None:
        if self.max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        if self.max_hypotheses < 1:
            raise ValueError("max_hypotheses must be at least 1")
        if self.max_total_actions < 1:
            raise ValueError("max_total_actions must be at least 1")
