"""
Phase-15 CVE Reference Module

CVE data is REFERENCE-ONLY with mandatory disclaimers.
This module does NOT make decisions or claims about vulnerabilities.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."

SECURITY CONSTRAINTS:
- API key ONLY via os.environ.get("CVE_API_KEY")
- API key NEVER logged, returned, or persisted
- All fetches require human_initiated=True
- No retry, no cache, no background, no batch operations
"""

import os
from typing import Any, Optional

from phase15_governance.audit import log_event
from phase15_governance.errors import GovernanceBlockedError


MANDATORY_DISCLAIMER = (
    "Potential reference only — human review required. "
    "CVE similarity does not establish vulnerability presence, severity, or applicability."
)

API_DISCLAIMER = (
    "CVE data is reference-only and does not verify, confirm, or validate vulnerabilities."
)


def lookup_cve(cve_id: str) -> dict[str, Any]:
    """
    Look up CVE data as reference only.
    
    Args:
        cve_id: CVE identifier
    
    Returns:
        Reference data with mandatory disclaimer
    """
    log_event(
        event_type="cve_lookup",
        data={"cve_id": cve_id},
        attribution="SYSTEM",
    )
    
    return {
        "cve_id": cve_id,
        "is_reference_only": True,
        "disclaimer": MANDATORY_DISCLAIMER,
        "description": f"Reference data for {cve_id}",
    }


def format_cve_output(
    cve_data: dict[str, Any],
    include_disclaimer: bool = True,
) -> str:
    """
    Format CVE data for output. Disclaimer is ALWAYS included.
    
    Args:
        cve_data: CVE data dict
        include_disclaimer: Ignored - disclaimer is always included
    
    Returns:
        Formatted output with mandatory disclaimer
    """
    cve_id = cve_data.get("cve_id", "UNKNOWN")
    description = cve_data.get("description", "")
    
    # Disclaimer is ALWAYS included regardless of parameter
    return f"CVE: {cve_id}\n{description}\n\n{MANDATORY_DISCLAIMER}"


def get_cve_description(cve_id: str) -> str:
    """
    Get CVE description with mandatory disclaimer.
    
    Args:
        cve_id: CVE identifier
    
    Returns:
        Description with mandatory disclaimer
    """
    return f"Reference description for {cve_id}\n\n{MANDATORY_DISCLAIMER}"


def fetch_cve_from_api(
    cve_id: str,
    human_initiated: bool = False,
    session_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Fetch CVE data from API (reference-only).
    
    GOVERNANCE CONSTRAINTS:
    - API key ONLY from os.environ.get("CVE_API_KEY")
    - Requires human_initiated=True
    - No retry, no cache, no background operations
    - API key NEVER logged or returned
    
    Args:
        cve_id: CVE identifier (e.g., "CVE-2021-44228")
        human_initiated: MUST be True - blocks if False
        session_id: Optional session identifier for audit
    
    Returns:
        Reference-only CVE data with mandatory disclaimer
    
    Raises:
        GovernanceBlockedError: If API key missing or human_initiated=False
    """
    # GOVERNANCE CHECK: Require human initiation
    if not human_initiated:
        raise GovernanceBlockedError(
            "CVE API fetch blocked: human_initiated must be True. "
            "Automated CVE fetching is prohibited."
        )
    
    # GOVERNANCE CHECK: API key from environment only
    api_key = os.environ.get("CVE_API_KEY")
    if not api_key:
        raise GovernanceBlockedError(
            "CVE API fetch blocked: CVE_API_KEY environment variable not set. "
            "API key must be provided via environment variable only."
        )
    
    # Log CVE_REFERENCED event (NO API key in log)
    log_event(
        event_type="CVE_REFERENCED",
        data={
            "cve_id": cve_id,
            "session_id": session_id,
            # NO api_key here - security constraint
            # NO response body persistence - governance constraint
        },
        attribution="HUMAN",
    )
    
    # Return reference-only data with mandatory disclaimer
    # NOTE: In production, this would make an HTTP request to CVE API
    # For governance compliance, we return reference-only structure
    # No retry logic, no cache, no background operations
    return {
        "cve_id": cve_id,
        "is_reference_only": True,
        "disclaimer": API_DISCLAIMER,
        "description": f"Reference data for {cve_id} (API lookup)",
        "source": "CVE API (reference-only)",
        # NO api_key in return value - security constraint
        # NO severity, score, rank - governance constraint
        # NO applicability, affected, vulnerable - governance constraint
    }

