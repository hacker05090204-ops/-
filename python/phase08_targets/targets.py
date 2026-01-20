"""
PHASE 08 — TARGET METADATA MODEL
2026 RE-IMPLEMENTATION

Defines target metadata for security testing targets.

Document ID: GOV-PHASE08-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class TargetType(Enum):
    """Types of security testing targets."""
    HOST = "host"
    NETWORK = "network"
    WEB_APPLICATION = "web_application"
    API = "api"
    SERVICE = "service"


class TargetStatus(Enum):
    """Status of a target."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TargetMetadata:
    """Immutable metadata about a security testing target."""
    target_id: str
    name: str
    target_type: TargetType
    address: str  # IP, URL, hostname, etc.
    description: str = ""
    status: TargetStatus = TargetStatus.UNKNOWN
    created_at: datetime = field(default_factory=datetime.utcnow)


def create_target(
    name: str,
    target_type: TargetType,
    address: str,
    description: str = ""
) -> TargetMetadata:
    """Create a new target with validation."""
    if not name or not name.strip():
        raise ValueError("name cannot be empty")
    if not address or not address.strip():
        raise ValueError("address cannot be empty")
    
    return TargetMetadata(
        target_id=str(uuid.uuid4()),
        name=name.strip(),
        target_type=target_type,
        address=address.strip(),
        description=description
    )


def is_valid_target(target: TargetMetadata) -> bool:
    """Check if target metadata is valid."""
    return bool(target.target_id and target.name and target.address)
