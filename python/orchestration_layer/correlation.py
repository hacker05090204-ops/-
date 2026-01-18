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
Phase-12 Cross-Phase Correlation Module

Track 4 - TASK-4.1 and TASK-4.2: Cross-Phase Correlation (READ-ONLY)

This module provides READ-ONLY correlation between phases.
Correlation = ID references ONLY.
NO writes to frozen phases.
NO decision logic.
NO execution logic.
NO friction wiring or enforcement.

Requirements: REQ-3.2, INV-5.3, INV-5.4
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from .errors import (
    FrozenPhaseViolationError,
    ReadOnlyViolationError,
)
from .types import CrossPhaseCorrelation


# =============================================================================
# TASK-4.1: Cross-Phase Correlation (READ-ONLY)
# =============================================================================

def create_correlation(phase_entries: Dict[str, str]) -> CrossPhaseCorrelation:
    """
    Create a cross-phase correlation with ID references only.
    
    This function creates an immutable correlation record that references
    audit entry IDs from different phases. It does NOT read, modify, or
    access the actual audit entries - only stores their IDs.
    
    Args:
        phase_entries: Dictionary mapping phase names to audit entry IDs.
                      Example: {"phase_4": "entry_123", "phase_10": "entry_456"}
    
    Returns:
        CrossPhaseCorrelation: Immutable correlation record with ID references.
    
    Raises:
        ReadOnlyViolationError: If phase_entries is not a valid dict.
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    # Validate input is a dictionary (READ-ONLY check)
    if not isinstance(phase_entries, dict):
        raise ReadOnlyViolationError(
            "phase_entries must be a dictionary of phase_name -> audit_entry_id"
        )
    
    # Validate all values are strings (ID references only)
    for phase_name, entry_id in phase_entries.items():
        if not isinstance(phase_name, str) or not isinstance(entry_id, str):
            raise ReadOnlyViolationError(
                "Correlation only accepts string ID references"
            )
    
    # Create immutable correlation with ID references only
    # NO reads from other phases
    # NO writes to other phases
    # NO decision logic based on entry contents
    correlation_id = f"corr_{uuid.uuid4().hex[:16]}"
    
    return CrossPhaseCorrelation(
        correlation_id=correlation_id,
        phase_entries=dict(phase_entries),  # Shallow copy of ID references
        created_at=datetime.now(timezone.utc),
        human_confirmation_required=True,  # ALWAYS True - INV-5.1
        no_auto_action=True,  # ALWAYS True - INV-5.1
    )


def get_correlated_entries(correlation: CrossPhaseCorrelation) -> Dict[str, str]:
    """
    Get the phase entries from a correlation (READ-ONLY).
    
    This function returns the ID references stored in the correlation.
    It does NOT fetch, read, or access the actual audit entries.
    
    Args:
        correlation: The CrossPhaseCorrelation to read from.
    
    Returns:
        Dict[str, str]: Dictionary of phase_name -> audit_entry_id references.
    
    Raises:
        ReadOnlyViolationError: If correlation is not a valid CrossPhaseCorrelation.
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    if not isinstance(correlation, CrossPhaseCorrelation):
        raise ReadOnlyViolationError(
            "Expected CrossPhaseCorrelation instance"
        )
    
    # Return a copy of the ID references (READ-ONLY)
    # NO fetching of actual entries
    # NO decision logic based on entry contents
    return dict(correlation.phase_entries)


# =============================================================================
# TASK-4.2: Phase-10 Friction Result Consumption (READ-ONLY)
# =============================================================================

def consume_friction_result(friction_record_id: str) -> Dict[str, Any]:
    """
    Consume a Phase-10 friction result (READ-ONLY reference).
    
    This function creates a READ-ONLY reference to a Phase-10 friction record.
    It does NOT:
    - Read the actual friction record contents
    - Execute any friction mechanisms
    - Wire friction into any flows
    - Enforce any friction policy
    - Bypass or reduce friction
    - Make any decisions based on friction state
    
    The returned dictionary contains ONLY the reference ID and metadata
    indicating that this is a READ-ONLY reference.
    
    Args:
        friction_record_id: The ID of the Phase-10 friction record to reference.
    
    Returns:
        Dict[str, Any]: READ-ONLY reference metadata containing:
            - friction_record_id: The referenced record ID
            - reference_type: Always "read_only"
            - phase: Always "phase_10"
            - human_confirmation_required: Always True
            - no_auto_action: Always True
            - friction_executed: Always False (we do NOT execute friction)
            - friction_wired: Always False (we do NOT wire friction)
            - friction_enforced: Always False (we do NOT enforce friction)
    
    Raises:
        ReadOnlyViolationError: If friction_record_id is not a valid string.
        FrozenPhaseViolationError: If any write to Phase-10 is attempted.
    
    NO EXECUTION LOGIC - NO DECISION LOGIC - NO FRICTION WIRING
    """
    # Validate input
    if not isinstance(friction_record_id, str):
        raise ReadOnlyViolationError(
            "friction_record_id must be a string"
        )
    
    if not friction_record_id.strip():
        raise ReadOnlyViolationError(
            "friction_record_id cannot be empty"
        )
    
    # Return READ-ONLY reference metadata
    # NO actual read of Phase-10 data
    # NO execution of friction
    # NO wiring of friction
    # NO enforcement of friction
    # NO decision based on friction state
    return {
        "friction_record_id": friction_record_id,
        "reference_type": "read_only",
        "phase": "phase_10",
        "human_confirmation_required": True,  # ALWAYS True - INV-5.1
        "no_auto_action": True,  # ALWAYS True - INV-5.1
        "friction_executed": False,  # We do NOT execute friction
        "friction_wired": False,  # We do NOT wire friction
        "friction_enforced": False,  # We do NOT enforce friction
    }
