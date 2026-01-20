"""
PHASE 05 — SCANNER ABSTRACTIONS
2026 RE-IMPLEMENTATION

This module defines scanner abstractions for security testing tools.
Scanners are READ-ONLY and do NOT perform exploitation.

⚠️ CRITICAL: This is a 2026 RE-IMPLEMENTATION.

Document ID: GOV-PHASE05-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Final
import uuid


# =============================================================================
# SCANNER TYPE ENUM
# =============================================================================

class ScannerType(Enum):
    """Types of security scanners."""
    PORT_SCANNER = "port_scanner"
    VULNERABILITY_SCANNER = "vulnerability_scanner"
    WEB_SCANNER = "web_scanner"
    NETWORK_SCANNER = "network_scanner"
    CUSTOM = "custom"


class ScanStatus(Enum):
    """Status of a scan operation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# SCANNER DEFINITION
# =============================================================================

@dataclass(frozen=True)
class ScannerDefinition:
    """
    Immutable definition of a scanner.
    
    Scanners are READ-ONLY tools that gather information.
    They do NOT perform exploitation or modification.
    """
    scanner_id: str
    name: str
    scanner_type: ScannerType
    description: str
    is_read_only: bool = True  # Always True - scanners don't modify


# =============================================================================
# SCAN REQUEST
# =============================================================================

@dataclass(frozen=True)
class ScanRequest:
    """
    Request to perform a scan operation.
    
    All scans require human initiation.
    """
    request_id: str
    scanner_id: str
    target: str
    parameters: dict[str, Any]
    requires_confirmation: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# SCAN RESULT
# =============================================================================

@dataclass(frozen=True)
class ScanResult:
    """Result of a scan operation."""
    request_id: str
    status: ScanStatus
    findings: list[str] = field(default_factory=list)
    raw_output: Optional[str] = None
    error_message: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_scanner_definition(
    name: str,
    scanner_type: ScannerType,
    description: str
) -> ScannerDefinition:
    """Create a new scanner definition."""
    if not name or not name.strip():
        raise ValueError("name cannot be empty")
    
    return ScannerDefinition(
        scanner_id=str(uuid.uuid4()),
        name=name.strip(),
        scanner_type=scanner_type,
        description=description,
        is_read_only=True  # Always read-only
    )


def create_scan_request(
    scanner_id: str,
    target: str,
    parameters: Optional[dict[str, Any]] = None
) -> ScanRequest:
    """Create a new scan request."""
    if not target or not target.strip():
        raise ValueError("target cannot be empty")
    
    return ScanRequest(
        request_id=str(uuid.uuid4()),
        scanner_id=scanner_id,
        target=target.strip(),
        parameters=parameters or {},
        requires_confirmation=True
    )


# =============================================================================
# END OF PHASE-05 SCANNER
# =============================================================================
