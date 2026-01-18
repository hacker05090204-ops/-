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
Phase-12 Integration Report Module

Track 5 - TASK-5.1 and TASK-5.2: Integration Report (No Auto-Submit)

This module provides report generation and export functionality.
Reports are NEVER auto-submitted.
Export requires explicit human confirmation.
NO network access.
NO execution logic.
NO decision logic.

Requirements: REQ-3.5, INV-5.1
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from .errors import (
    AutomationAttemptError,
    NoSubmissionCapabilityError,
)
from .types import IntegrationReport


# =============================================================================
# TASK-5.1: Report Generation (No Auto-Submit)
# =============================================================================

def generate_report(
    workflow_id: str,
    phase_summaries: Dict[str, str],
    correlation_ids: List[str],
) -> IntegrationReport:
    """
    Generate an integration report (NO AUTO-SUBMIT).
    
    This function creates an immutable integration report that summarizes
    workflow execution across phases. The report is NEVER auto-submitted.
    
    Args:
        workflow_id: The workflow ID this report is for.
        phase_summaries: Dictionary mapping phase names to summary strings.
        correlation_ids: List of correlation IDs referenced by this report.
    
    Returns:
        IntegrationReport: Immutable report with auto_submit_allowed=False.
    
    Raises:
        AutomationAttemptError: If any auto-submit attempt is detected.
    
    NO EXECUTION LOGIC - NO DECISION LOGIC - NO AUTO-SUBMIT
    """
    # Validate inputs
    if not isinstance(workflow_id, str) or not workflow_id.strip():
        raise AutomationAttemptError(
            "workflow_id must be a non-empty string"
        )
    
    if not isinstance(phase_summaries, dict):
        raise AutomationAttemptError(
            "phase_summaries must be a dictionary"
        )
    
    if not isinstance(correlation_ids, list):
        raise AutomationAttemptError(
            "correlation_ids must be a list"
        )
    
    # Generate report ID
    report_id = f"report_{uuid.uuid4().hex[:16]}"
    
    # Create summary from phase summaries
    summary = _create_summary(phase_summaries)
    
    # Create immutable report
    # auto_submit_allowed is ALWAYS False
    # human_confirmation_required is ALWAYS True
    # no_auto_action is ALWAYS True
    return IntegrationReport(
        report_id=report_id,
        workflow_id=workflow_id,
        generated_at=datetime.now(timezone.utc),
        summary=summary,
        phase_summaries=dict(phase_summaries),  # Shallow copy
        correlation_ids=list(correlation_ids),  # Shallow copy
        human_confirmation_required=True,  # ALWAYS True - INV-5.1
        no_auto_action=True,  # ALWAYS True - INV-5.1
        auto_submit_allowed=False,  # ALWAYS False - REQ-3.5.3
    )


def _create_summary(phase_summaries: Dict[str, str]) -> str:
    """
    Create a summary string from phase summaries.
    
    This is a simple concatenation - NO decision logic, NO inference.
    
    Args:
        phase_summaries: Dictionary mapping phase names to summary strings.
    
    Returns:
        str: Combined summary string.
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    if not phase_summaries:
        return "No phase summaries available."
    
    # Simple concatenation - NO inference, NO recommendations
    parts = []
    for phase_name in sorted(phase_summaries.keys()):
        parts.append(f"{phase_name}: {phase_summaries[phase_name]}")
    
    return " | ".join(parts)


# =============================================================================
# TASK-5.2: Report Export (Human Confirmation Required)
# =============================================================================

def export_report(
    report: IntegrationReport,
    human_confirmation_token: str,
) -> Dict[str, Any]:
    """
    Export a report (REQUIRES HUMAN CONFIRMATION).
    
    This function exports a report to a dictionary format suitable for
    human review. It does NOT auto-submit, does NOT send data externally,
    and does NOT trigger any actions.
    
    Args:
        report: The IntegrationReport to export.
        human_confirmation_token: Explicit human confirmation token (required).
    
    Returns:
        Dict[str, Any]: Exported report data for human review.
    
    Raises:
        AutomationAttemptError: If human_confirmation_token is invalid.
        NoSubmissionCapabilityError: If any submission is attempted.
    
    NO EXECUTION LOGIC - NO DECISION LOGIC - NO AUTO-SUBMIT - NO NETWORK
    """
    # Validate report type
    if not isinstance(report, IntegrationReport):
        raise AutomationAttemptError(
            "Expected IntegrationReport instance"
        )
    
    # Validate human confirmation token
    if not isinstance(human_confirmation_token, str):
        raise AutomationAttemptError(
            "human_confirmation_token must be a string"
        )
    
    if not human_confirmation_token.strip():
        raise AutomationAttemptError(
            "human_confirmation_token cannot be empty"
        )
    
    # Verify auto_submit_allowed is False (defensive check)
    if report.auto_submit_allowed:
        raise NoSubmissionCapabilityError(
            "Report has auto_submit_allowed=True which is forbidden"
        )
    
    # Export report data for human review
    # NO network transmission
    # NO external submission
    # NO action triggering
    return {
        "report_id": report.report_id,
        "workflow_id": report.workflow_id,
        "generated_at": report.generated_at.isoformat(),
        "summary": report.summary,
        "phase_summaries": dict(report.phase_summaries),
        "correlation_ids": list(report.correlation_ids),
        "human_confirmation_required": report.human_confirmation_required,
        "no_auto_action": report.no_auto_action,
        "auto_submit_allowed": report.auto_submit_allowed,
        "export_metadata": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "human_confirmed": True,
            "auto_submitted": False,  # NEVER auto-submitted
            "network_transmitted": False,  # NEVER transmitted
        },
    }


def get_report_status(report: IntegrationReport) -> Dict[str, Any]:
    """
    Get the status of a report (READ-ONLY).
    
    This function returns status information about a report.
    It does NOT modify the report, does NOT trigger actions,
    and does NOT make decisions.
    
    Args:
        report: The IntegrationReport to check.
    
    Returns:
        Dict[str, Any]: Report status information.
    
    NO EXECUTION LOGIC - NO DECISION LOGIC
    """
    if not isinstance(report, IntegrationReport):
        raise AutomationAttemptError(
            "Expected IntegrationReport instance"
        )
    
    return {
        "report_id": report.report_id,
        "workflow_id": report.workflow_id,
        "generated_at": report.generated_at.isoformat(),
        "human_confirmation_required": report.human_confirmation_required,
        "no_auto_action": report.no_auto_action,
        "auto_submit_allowed": report.auto_submit_allowed,
        "phase_count": len(report.phase_summaries),
        "correlation_count": len(report.correlation_ids),
    }
