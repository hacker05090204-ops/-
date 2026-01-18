"""
Phase-6 Data Models

All data models are immutable (frozen dataclasses) to ensure:
- Input data cannot be modified
- Decisions cannot be altered after creation
- Audit entries are tamper-evident

ARCHITECTURAL NOTES:
- ReviewSession lifecycle is derived from audit events, not stored
- QueueItem status is derived from decisions, not stored
- All Optional fields that are None indicate "not provided by human"
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import hashlib
import json


# ============================================================================
# Core Enums
# ============================================================================

class Role(Enum):
    """
    Human roles in the decision workflow.
    
    OPERATOR: Initial triage - can view, mark reviewed, add notes, defer, escalate
    REVIEWER: Final authority - can do everything Operator can plus approve, reject, assign severity
    """
    OPERATOR = "operator"
    REVIEWER = "reviewer"


class DecisionType(Enum):
    """Types of decisions a human can make on a finding."""
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"
    ESCALATE = "escalate"
    MARK_REVIEWED = "mark_reviewed"
    ADD_NOTE = "add_note"


class Severity(Enum):
    """
    Severity levels for approved findings.
    
    These are assigned by humans only - never auto-calculated.
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class Action(Enum):
    """Actions that can be performed in the workflow, used for permission checking."""
    VIEW_FINDINGS = "view_findings"
    MARK_REVIEWED = "mark_reviewed"
    ADD_NOTE = "add_note"
    DEFER = "defer"
    ESCALATE = "escalate"
    ASSIGN_SEVERITY = "assign_severity"
    APPROVE = "approve"
    REJECT = "reject"


# ============================================================================
# Role Permissions
# ============================================================================

ROLE_PERMISSIONS: dict[Role, set[Action]] = {
    Role.OPERATOR: {
        Action.VIEW_FINDINGS,
        Action.MARK_REVIEWED,
        Action.ADD_NOTE,
        Action.DEFER,
        Action.ESCALATE,
    },
    Role.REVIEWER: {
        Action.VIEW_FINDINGS,
        Action.MARK_REVIEWED,
        Action.ADD_NOTE,
        Action.DEFER,
        Action.ESCALATE,
        Action.ASSIGN_SEVERITY,
        Action.APPROVE,
        Action.REJECT,
    },
}


# ============================================================================
# Session and Credentials
# ============================================================================

@dataclass(frozen=True)
class Credentials:
    """
    Authentication credentials for a human reviewer.
    
    In production, would include auth token/signature.
    """
    user_id: str
    role: Role


@dataclass(frozen=True)
class ReviewSession:
    """
    An authenticated review session.
    
    IMMUTABILITY NOTE: ReviewSession is a frozen dataclass.
    Session lifecycle (active/ended) is DERIVED from audit events:
    - Session is "active" if no SESSION_END audit entry exists
    - Session is "ended" if SESSION_END audit entry exists
    - decisions_made_count is computed from audit entries, not stored
    
    This ensures session state cannot be corrupted independently of audit log.
    """
    session_id: str
    reviewer_id: str
    role: Role
    start_time: datetime


# ============================================================================
# Decision Records
# ============================================================================

@dataclass(frozen=True)
class DecisionInput:
    """
    Input for making a decision on a finding.
    
    Different decision types require different fields:
    - APPROVE: requires severity (and optionally cvss_score)
    - REJECT: requires rationale
    - DEFER: requires defer_reason
    - ESCALATE: requires escalation_target
    - MARK_REVIEWED: no additional fields required
    - ADD_NOTE: requires note
    """
    decision_type: DecisionType
    severity: Optional[Severity] = None
    cvss_score: Optional[float] = None
    rationale: Optional[str] = None
    defer_reason: Optional[str] = None
    escalation_target: Optional[str] = None
    note: Optional[str] = None


@dataclass(frozen=True)
class HumanDecision:
    """
    Immutable record of a human's judgment on a finding.
    
    Once created, this record cannot be modified. Any changes
    require creating a new decision record.
    """
    decision_id: str
    finding_id: str
    session_id: str
    reviewer_id: str
    role: Role
    decision_type: DecisionType
    timestamp: datetime
    severity: Optional[Severity] = None
    cvss_score: Optional[float] = None
    rationale: Optional[str] = None
    defer_reason: Optional[str] = None
    escalation_target: Optional[str] = None
    note: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "decision_id": self.decision_id,
            "finding_id": self.finding_id,
            "session_id": self.session_id,
            "reviewer_id": self.reviewer_id,
            "role": self.role.value,
            "decision_type": self.decision_type.value,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.severity is not None:
            result["severity"] = self.severity.value
        if self.cvss_score is not None:
            result["cvss_score"] = self.cvss_score
        if self.rationale is not None:
            result["rationale"] = self.rationale
        if self.defer_reason is not None:
            result["defer_reason"] = self.defer_reason
        if self.escalation_target is not None:
            result["escalation_target"] = self.escalation_target
        if self.note is not None:
            result["note"] = self.note
        return result


# ============================================================================
# Audit Entry
# ============================================================================

@dataclass(frozen=True)
class AuditEntry:
    """
    Immutable audit log entry with hash chain integrity.
    
    Each entry contains a hash of the previous entry, creating
    a tamper-evident chain. If any entry is modified, the chain
    breaks and integrity verification fails.
    """
    entry_id: str
    timestamp: datetime
    session_id: str
    reviewer_id: str
    role: Role
    action: str
    finding_id: Optional[str] = None
    decision_id: Optional[str] = None
    decision_type: Optional[DecisionType] = None
    severity: Optional[Severity] = None
    rationale: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    previous_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    
    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of entry content.
        
        The hash includes all fields except entry_hash itself,
        ensuring the hash covers the complete entry content.
        """
        content = (
            f"{self.entry_id}|"
            f"{self.timestamp.isoformat()}|"
            f"{self.session_id}|"
            f"{self.reviewer_id}|"
            f"{self.role.value}|"
            f"{self.action}|"
            f"{self.finding_id}|"
            f"{self.decision_id}|"
            f"{self.decision_type.value if self.decision_type else None}|"
            f"{self.severity.value if self.severity else None}|"
            f"{self.rationale}|"
            f"{self.error_type}|"
            f"{self.error_message}|"
            f"{self.previous_hash}"
        )
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "reviewer_id": self.reviewer_id,
            "role": self.role.value,
            "action": self.action,
        }
        if self.finding_id is not None:
            result["finding_id"] = self.finding_id
        if self.decision_id is not None:
            result["decision_id"] = self.decision_id
        if self.decision_type is not None:
            result["decision_type"] = self.decision_type.value
        if self.severity is not None:
            result["severity"] = self.severity.value
        if self.rationale is not None:
            result["rationale"] = self.rationale
        if self.error_type is not None:
            result["error_type"] = self.error_type
        if self.error_message is not None:
            result["error_message"] = self.error_message
        if self.previous_hash is not None:
            result["previous_hash"] = self.previous_hash
        if self.entry_hash is not None:
            result["entry_hash"] = self.entry_hash
        return result


# ============================================================================
# Queue Item
# ============================================================================

@dataclass(frozen=True)
class QueueItem:
    """
    A finding candidate in the review queue.
    
    MCP INPUT HANDLING:
    - mcp_classification and mcp_confidence are OPTIONAL
    - MCP data is treated as READ-ONLY (never modified by Phase-6)
    - Missing MCP data: fields are None, UI displays "Not classified"
    - Malformed MCP data: logged as warning, treated as missing
    - Phase-6 NEVER generates or modifies MCP classifications
    
    STATUS NOTE:
    - status is derived from decisions in the audit log, not stored
    - This field is for display purposes only
    """
    finding_id: str
    endpoint: str
    signals: tuple[dict[str, Any], ...]  # Signal data from Phase-5
    mcp_classification: Optional[str] = None
    mcp_confidence: Optional[float] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "finding_id": self.finding_id,
            "endpoint": self.endpoint,
            "signals": list(self.signals),
        }
        if self.mcp_classification is not None:
            result["mcp_classification"] = self.mcp_classification
        if self.mcp_confidence is not None:
            result["mcp_confidence"] = self.mcp_confidence
        return result


# ============================================================================
# Decision Report
# ============================================================================

@dataclass(frozen=True)
class DecisionReport:
    """
    Export report of all decisions in a session.
    
    This report is JSON-serializable and can be exported for
    sharing with stakeholders. It is NOT auto-submitted to
    any external system.
    """
    report_id: str
    session_id: str
    reviewer_id: str
    role: Role
    generated_at: datetime
    decisions: tuple[HumanDecision, ...]
    
    @property
    def total_decisions(self) -> int:
        """Total number of decisions in the report."""
        return len(self.decisions)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "report_id": self.report_id,
            "session_id": self.session_id,
            "reviewer_id": self.reviewer_id,
            "role": self.role.value,
            "generated_at": self.generated_at.isoformat(),
            "total_decisions": self.total_decisions,
            "decisions": [d.to_dict() for d in self.decisions],
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
