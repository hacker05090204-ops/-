# PHASE-13 GOVERNANCE COMPLIANCE
# This module is part of Phase-13 (Controlled Bug Bounty Browser Shell)
#
# FORBIDDEN CAPABILITIES:
# - NO automation logic
# - NO execution authority
# - NO decision authority
# - NO learning or personalization
# - NO audit modification
# - NO scope expansion
# - NO session extension
# - NO batch approvals
# - NO scheduled actions
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""
Audit Entry Types for Phase-13 Browser Shell.

Requirement: 6.2 (Audit Trail Content)

This module defines ONLY immutable data types for audit entries.
NO execution methods. NO automation methods. NO modification methods.
"""

from dataclasses import dataclass
from enum import Enum


class Initiator(Enum):
    """
    Initiator of an action - HUMAN or SYSTEM only.
    
    Per Requirement 3.3 (Attribution):
    - HUMAN: Action initiated by human operator
    - SYSTEM: Action initiated by system (validation, logging, blocking)
    
    NO other values permitted.
    """
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"


class ActionType(Enum):
    """
    Types of actions that can be logged to the audit trail.
    
    Per Requirement 6.2 (Audit Trail Content):
    All significant actions must be categorized and logged.
    
    NO execution methods. NO automation methods.
    """
    # Session actions (Requirement 1.1, 1.2, 1.3)
    SESSION_START = "SESSION_START"
    SESSION_END = "SESSION_END"
    SESSION_TIMEOUT = "SESSION_TIMEOUT"
    SESSION_IDLE_TIMEOUT = "SESSION_IDLE_TIMEOUT"
    
    # Scope actions (Requirement 2.1, 2.2, 2.3)
    SCOPE_DEFINED = "SCOPE_DEFINED"
    SCOPE_VALIDATED = "SCOPE_VALIDATED"
    SCOPE_VIOLATION = "SCOPE_VIOLATION"
    SCOPE_BLOCKED = "SCOPE_BLOCKED"
    
    # Evidence actions (Requirement 4.1, 4.2, 4.3)
    EVIDENCE_CAPTURED = "EVIDENCE_CAPTURED"
    EVIDENCE_BLOCKED = "EVIDENCE_BLOCKED"
    EVIDENCE_FLAGGED = "EVIDENCE_FLAGGED"
    EVIDENCE_SIZE_EXCEEDED = "EVIDENCE_SIZE_EXCEEDED"
    
    # Decision actions (Requirement 3.1, 3.2, 3.3)
    DECISION_POINT = "DECISION_POINT"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    CONFIRMATION_RECEIVED = "CONFIRMATION_RECEIVED"
    CONFIRMATION_TIMEOUT = "CONFIRMATION_TIMEOUT"
    
    # Submission actions (Requirement 5.1, 5.2)
    SUBMISSION_STEP_1 = "SUBMISSION_STEP_1"
    SUBMISSION_STEP_2 = "SUBMISSION_STEP_2"
    SUBMISSION_STEP_3 = "SUBMISSION_STEP_3"
    SUBMISSION_BLOCKED = "SUBMISSION_BLOCKED"
    
    # Halt and recovery actions (Requirement 10.1, 10.2)
    HALT_TRIGGERED = "HALT_TRIGGERED"
    RECOVERY_STARTED = "RECOVERY_STARTED"
    RECOVERY_COMPLETED = "RECOVERY_COMPLETED"
    
    # Audit integrity actions (Requirement 6.1, 6.3)
    HASH_CHAIN_VALIDATED = "HASH_CHAIN_VALIDATED"
    HASH_CHAIN_FAILED = "HASH_CHAIN_FAILED"
    AUDIT_WRITE_FAILED = "AUDIT_WRITE_FAILED"


@dataclass(frozen=True)
class AuditEntry:
    """
    Immutable audit entry for Phase-13 audit trail.
    
    Per Requirement 6.2 (Audit Trail Content):
    Each entry must contain all required fields for complete accountability.
    
    frozen=True ensures immutability after creation.
    
    NO methods that modify state.
    NO methods that execute actions.
    NO methods that automate behavior.
    """
    # Unique identifier for this entry
    entry_id: str
    
    # ISO 8601 timestamp from external time source
    timestamp: str
    
    # Hash of the previous entry (chain integrity)
    previous_hash: str
    
    # Type of action being logged
    action_type: str
    
    # Who initiated: HUMAN or SYSTEM
    initiator: str
    
    # Session this entry belongs to
    session_id: str
    
    # Hash of the active scope at time of action
    scope_hash: str
    
    # Human-readable description of the action
    action_details: str
    
    # Outcome: SUCCESS, BLOCKED, FAILED, FLAGGED
    outcome: str
    
    # Cryptographic hash of this entry (for chain)
    entry_hash: str
