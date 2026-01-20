"""
PHASE 04 — EXECUTION PRIMITIVES
2026 RE-IMPLEMENTATION

This module defines the foundational structures for executing operations.

⚠️ CRITICAL: This is a 2026 RE-IMPLEMENTATION.

Document ID: GOV-PHASE04-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Final
import uuid

from phase02_actors import Actor
from phase03_trust import TrustZone


# =============================================================================
# OPERATION STATUS ENUM
# =============================================================================

class OperationStatus(Enum):
    """Status of an operation request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# OPERATION REQUEST
# =============================================================================

@dataclass(frozen=True)
class OperationRequest:
    """
    Immutable request to perform an operation.
    
    All operations require explicit human approval when requires_confirmation=True.
    """
    request_id: str
    actor: Actor
    operation_name: str
    parameters: dict[str, Any]
    requires_confirmation: bool = True  # Default: require human confirmation
    created_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# OPERATION RESULT
# =============================================================================

@dataclass(frozen=True)
class OperationResult:
    """Immutable result of an operation."""
    request_id: str
    status: OperationStatus
    output: Optional[Any] = None
    error_message: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# EXECUTION CONTEXT
# =============================================================================

@dataclass(frozen=True)
class ExecutionContext:
    """
    Context in which operations execute.
    
    Every operation runs within a context that tracks the actor and trust zone.
    """
    context_id: str
    actor: Actor
    trust_zone: TrustZone
    created_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_operation_request(
    actor: Actor,
    operation_name: str,
    parameters: Optional[dict[str, Any]] = None,
    requires_confirmation: bool = True
) -> OperationRequest:
    """Create a new operation request with generated ID."""
    if not operation_name or not operation_name.strip():
        raise ValueError("operation_name cannot be empty")
    
    return OperationRequest(
        request_id=str(uuid.uuid4()),
        actor=actor,
        operation_name=operation_name.strip(),
        parameters=parameters or {},
        requires_confirmation=requires_confirmation
    )


def create_execution_context(
    actor: Actor,
    trust_zone: TrustZone
) -> ExecutionContext:
    """Create a new execution context with generated ID."""
    return ExecutionContext(
        context_id=str(uuid.uuid4()),
        actor=actor,
        trust_zone=trust_zone
    )


def create_result_success(
    request_id: str,
    output: Any = None
) -> OperationResult:
    """Create a successful operation result."""
    return OperationResult(
        request_id=request_id,
        status=OperationStatus.COMPLETED,
        output=output
    )


def create_result_failure(
    request_id: str,
    error_message: str
) -> OperationResult:
    """Create a failed operation result."""
    return OperationResult(
        request_id=request_id,
        status=OperationStatus.FAILED,
        error_message=error_message
    )


# =============================================================================
# END OF PHASE-04 EXECUTION
# =============================================================================
