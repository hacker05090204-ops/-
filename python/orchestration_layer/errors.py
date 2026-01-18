# PHASE-12 GOVERNANCE COMPLIANCE
# This module is part of Phase-12 (Runtime Orchestration Implementation)
#
# FORBIDDEN CAPABILITIES:
# - NO execution logic
# - NO decision logic
# - NO submission logic
# - NO network access
# - NO browser automation
# - NO friction wiring or execution
# - NO auto-approval
# - NO frozen phase modification
#
# MANDATORY DECLARATION:
# Phase-12 implements orchestration without altering execution,
# human authority, governance friction, or audit invariants.

"""
Phase-12 Error Classes

Track 1 - TASK-1.1: Define Error Classes

This module defines all error classes for Phase-12 orchestration.
All errors inherit from OrchestrationError base class.

NO EXECUTION LOGIC - NO DECISION LOGIC
"""

from __future__ import annotations


class OrchestrationError(Exception):
    """Base exception for all Phase-12 orchestration errors."""
    pass


class InvalidTransitionError(OrchestrationError):
    """Raised when an invalid workflow state transition is attempted."""
    pass


class FrozenPhaseViolationError(OrchestrationError):
    """Raised when attempting to modify a frozen phase."""
    pass


class AuditIntegrityError(OrchestrationError):
    """Raised when audit hash chain integrity is compromised."""
    pass


class AuthorityDelegationAttemptError(OrchestrationError):
    """Raised when attempting to delegate human authority."""
    pass


class PolicyEnforcementAttemptError(OrchestrationError):
    """Raised when attempting to enforce friction policy (forbidden in Phase-12)."""
    pass


class NetworkAccessDeniedError(OrchestrationError):
    """Raised when network access is attempted (forbidden in Phase-12)."""
    pass


class DesignConformanceError(OrchestrationError):
    """Raised when implementation violates Phase-11 design specification."""
    pass


class ReadOnlyViolationError(OrchestrationError):
    """Raised when attempting to write to read-only data."""
    pass


class NoDecisionCapabilityError(OrchestrationError):
    """Raised when decision logic is attempted (forbidden in Phase-12)."""
    pass


class NoExecutionCapabilityError(OrchestrationError):
    """Raised when execution logic is attempted (forbidden in Phase-12)."""
    pass


class NoSubmissionCapabilityError(OrchestrationError):
    """Raised when submission logic is attempted (forbidden in Phase-12)."""
    pass


class AutomationAttemptError(OrchestrationError):
    """Raised when automation without human confirmation is attempted."""
    pass


class FrictionBypassAttemptError(OrchestrationError):
    """Raised when attempting to bypass governance friction."""
    pass
