"""
Phase-5 Scanner Data Types

All types enforce architectural boundaries:
- Signal has forbidden fields (severity, classification, confidence) as None
- FindingCandidate has forbidden fields as None
- ScanResult is immutable and JSON-serializable

CRITICAL: This system assists humans. It does not autonomously hunt, judge, or earn.

NON-GOALS (FORBIDDEN):
- NO severity assignment (human's responsibility)
- NO classification (MCP's responsibility)
- NO confidence scoring (MCP's responsibility)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import json
import secrets


class SignalType(str, Enum):
    """Types of security signals extracted from artifacts.
    
    These are OBSERVATIONS, not classifications.
    """
    SENSITIVE_DATA = "sensitive_data"
    HEADER_MISCONFIG = "header_misconfig"
    REFLECTION = "reflection"
    PATH_DISCLOSURE = "path_disclosure"
    DOM_ERROR = "dom_error"
    CSP_VIOLATION = "csp_violation"
    STATE_ANOMALY = "state_anomaly"


@dataclass(frozen=True)
class Signal:
    """Security signal - an observation, NOT a classification.
    
    INVARIANT: severity, classification, confidence MUST be None.
    These fields exist only to enforce the architectural boundary.
    """
    signal_id: str
    signal_type: SignalType
    source_artifact: str  # Path to source artifact
    description: str
    evidence: dict[str, Any]
    detected_at: datetime
    endpoint: Optional[str] = None  # Related endpoint if applicable
    
    # FORBIDDEN FIELDS - MUST be None (architectural boundary)
    severity: None = None
    classification: None = None
    confidence: None = None
    
    def __post_init__(self) -> None:
        if not self.signal_id:
            raise ValueError("Signal must have signal_id")
        if not isinstance(self.signal_type, SignalType):
            raise ValueError(f"Invalid signal_type: {self.signal_type}")
        if not self.source_artifact:
            raise ValueError("Signal must have source_artifact")
        if not self.description:
            raise ValueError("Signal must have description")
        
        # Enforce forbidden fields are None
        if self.severity is not None:
            raise ValueError("Signal.severity MUST be None (human's responsibility)")
        if self.classification is not None:
            raise ValueError("Signal.classification MUST be None (MCP's responsibility)")
        if self.confidence is not None:
            raise ValueError("Signal.confidence MUST be None (MCP's responsibility)")
    
    @staticmethod
    def create(
        signal_type: SignalType,
        source_artifact: str,
        description: str,
        evidence: dict[str, Any],
        endpoint: Optional[str] = None,
    ) -> "Signal":
        """Create a new Signal with auto-generated ID and timestamp."""
        return Signal(
            signal_id=secrets.token_urlsafe(16),
            signal_type=signal_type,
            source_artifact=source_artifact,
            description=description,
            evidence=evidence,
            detected_at=datetime.now(timezone.utc),
            endpoint=endpoint,
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "source_artifact": self.source_artifact,
            "endpoint": self.endpoint,
            "description": self.description,
            "evidence": self.evidence,
            "detected_at": self.detected_at.isoformat(),
            # Forbidden fields explicitly included as None
            "severity": None,
            "classification": None,
            "confidence": None,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Signal":
        """Deserialize from dictionary."""
        return cls(
            signal_id=data["signal_id"],
            signal_type=SignalType(data["signal_type"]),
            source_artifact=data["source_artifact"],
            endpoint=data.get("endpoint"),
            description=data["description"],
            evidence=data["evidence"],
            detected_at=datetime.fromisoformat(data["detected_at"]),
        )


@dataclass(frozen=True)
class FindingCandidate:
    """Potential finding for human review.
    
    NOT a vulnerability classification - just grouped signals.
    
    INVARIANT: severity, classification, confidence MUST be None.
    """
    candidate_id: str
    endpoint: str
    signals: tuple[Signal, ...]
    artifact_references: tuple[str, ...]
    created_at: datetime
    
    # FORBIDDEN FIELDS - MUST be None (architectural boundary)
    severity: None = None
    classification: None = None
    confidence: None = None
    
    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("FindingCandidate must have candidate_id")
        if not self.endpoint:
            raise ValueError("FindingCandidate must have endpoint")
        if not self.signals:
            raise ValueError("FindingCandidate must have at least one signal")
        
        # Enforce forbidden fields are None
        if self.severity is not None:
            raise ValueError("FindingCandidate.severity MUST be None (human's responsibility)")
        if self.classification is not None:
            raise ValueError("FindingCandidate.classification MUST be None (MCP's responsibility)")
        if self.confidence is not None:
            raise ValueError("FindingCandidate.confidence MUST be None (MCP's responsibility)")
    
    @staticmethod
    def create(
        endpoint: str,
        signals: list[Signal],
    ) -> "FindingCandidate":
        """Create a new FindingCandidate with auto-generated ID."""
        artifact_refs = tuple(sorted(set(s.source_artifact for s in signals)))
        return FindingCandidate(
            candidate_id=secrets.token_urlsafe(16),
            endpoint=endpoint,
            signals=tuple(signals),
            artifact_references=artifact_refs,
            created_at=datetime.now(timezone.utc),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        return {
            "candidate_id": self.candidate_id,
            "endpoint": self.endpoint,
            "signals": [s.to_dict() for s in self.signals],
            "artifact_references": list(self.artifact_references),
            "created_at": self.created_at.isoformat(),
            # Forbidden fields explicitly included as None
            "severity": None,
            "classification": None,
            "confidence": None,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FindingCandidate":
        """Deserialize from dictionary."""
        return cls(
            candidate_id=data["candidate_id"],
            endpoint=data["endpoint"],
            signals=tuple(Signal.from_dict(s) for s in data["signals"]),
            artifact_references=tuple(data["artifact_references"]),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass(frozen=True)
class ScanResult:
    """Complete scan result for human review.
    
    Contains all signals and finding candidates from a scan.
    Supports JSON serialization for integration with review workflows.
    """
    result_id: str
    execution_id: str
    signals: tuple[Signal, ...]
    finding_candidates: tuple[FindingCandidate, ...]
    artifacts_scanned: tuple[str, ...]
    artifacts_failed: tuple[str, ...]  # Partial results support
    scan_started_at: datetime
    scan_completed_at: datetime
    immutability_verified: bool
    
    def __post_init__(self) -> None:
        if not self.result_id:
            raise ValueError("ScanResult must have result_id")
        if not self.execution_id:
            raise ValueError("ScanResult must have execution_id")
    
    @staticmethod
    def create(
        execution_id: str,
        signals: list[Signal],
        finding_candidates: list[FindingCandidate],
        artifacts_scanned: list[str],
        artifacts_failed: list[str],
        scan_started_at: datetime,
        immutability_verified: bool,
    ) -> "ScanResult":
        """Create a new ScanResult with auto-generated ID."""
        return ScanResult(
            result_id=secrets.token_urlsafe(16),
            execution_id=execution_id,
            signals=tuple(signals),
            finding_candidates=tuple(finding_candidates),
            artifacts_scanned=tuple(artifacts_scanned),
            artifacts_failed=tuple(artifacts_failed),
            scan_started_at=scan_started_at,
            scan_completed_at=datetime.now(timezone.utc),
            immutability_verified=immutability_verified,
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        return {
            "result_id": self.result_id,
            "execution_id": self.execution_id,
            "signals": [s.to_dict() for s in self.signals],
            "finding_candidates": [fc.to_dict() for fc in self.finding_candidates],
            "artifacts_scanned": list(self.artifacts_scanned),
            "artifacts_failed": list(self.artifacts_failed),
            "scan_started_at": self.scan_started_at.isoformat(),
            "scan_completed_at": self.scan_completed_at.isoformat(),
            "immutability_verified": self.immutability_verified,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string for human review."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanResult":
        """Deserialize from dictionary."""
        return cls(
            result_id=data["result_id"],
            execution_id=data["execution_id"],
            signals=tuple(Signal.from_dict(s) for s in data["signals"]),
            finding_candidates=tuple(
                FindingCandidate.from_dict(fc) for fc in data["finding_candidates"]
            ),
            artifacts_scanned=tuple(data["artifacts_scanned"]),
            artifacts_failed=tuple(data["artifacts_failed"]),
            scan_started_at=datetime.fromisoformat(data["scan_started_at"]),
            scan_completed_at=datetime.fromisoformat(data["scan_completed_at"]),
            immutability_verified=data["immutability_verified"],
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "ScanResult":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
