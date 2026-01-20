"""
PHASE 11 — EVIDENCE SCHEMA
2026 RE-IMPLEMENTATION

Schema for security testing evidence and artifacts.

Document ID: GOV-PHASE11-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import uuid


class EvidenceType(Enum):
    """Types of security evidence."""
    SCREENSHOT = "screenshot"
    LOG = "log"
    REQUEST = "request"
    RESPONSE = "response"
    FILE = "file"
    NETWORK_CAPTURE = "network_capture"
    OTHER = "other"


@dataclass(frozen=True)
class Evidence:
    """Immutable evidence artifact."""
    evidence_id: str
    evidence_type: EvidenceType
    description: str
    source: str
    content_hash: Optional[str] = None
    collected_at: datetime = field(default_factory=datetime.utcnow)
    collected_by_actor_id: Optional[str] = None


def create_evidence(
    evidence_type: EvidenceType,
    description: str,
    source: str,
    actor_id: Optional[str] = None
) -> Evidence:
    """Create new evidence record."""
    if not description or not description.strip():
        raise ValueError("description cannot be empty")
    
    return Evidence(
        evidence_id=str(uuid.uuid4()),
        evidence_type=evidence_type,
        description=description.strip(),
        source=source,
        collected_by_actor_id=actor_id
    )


def is_valid_evidence(evidence: Evidence) -> bool:
    """Validate evidence has required fields."""
    return bool(evidence.evidence_id and evidence.description and evidence.source)
