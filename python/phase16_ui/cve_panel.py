"""
Phase-16 CVE Panel Module

GOVERNANCE CONSTRAINT:
- CVE data is reference-only
- Mandatory disclaimer always visible
- Flat text only — no badges, colors, icons
- Alphabetical ordering only — no priority ordering
- Human-initiated fetch only
"""

from typing import Any, Optional

from phase16_ui.strings import UIStrings
from phase16_ui.errors import UIGovernanceViolation


# Exact required disclaimer - cannot be modified
REQUIRED_DISCLAIMER = (
    "CVE data is reference-only and does not verify, confirm, "
    "or validate vulnerabilities."
)


class CVEPanel:
    """
    CVE reference panel with mandatory disclaimer.
    
    GOVERNANCE GUARANTEES:
    - Disclaimer always visible
    - Flat text only (no badges, colors, icons)
    - Alphabetical ordering only
    - Human-initiated fetch only
    - No caching
    """
    
    def __init__(self) -> None:
        """Initialize CVE panel with mandatory disclaimer."""
        # Disclaimer is fixed and cannot be changed
        self._disclaimer = REQUIRED_DISCLAIMER
        self._disclaimer_visible = True  # Always True
        self._disclaimer_position = "top"  # Prominent position
        
        # No caching - governance constraint
        self._cached_data: None = None  # Always None
    
    def has_disclaimer(self) -> bool:
        """Check if panel has disclaimer (always True)."""
        return True
    
    def get_disclaimer_text(self) -> str:
        """Get disclaimer text (exact required text)."""
        return self._disclaimer
    
    def is_disclaimer_visible(self) -> bool:
        """Check if disclaimer is visible (always True)."""
        return True
    
    def hide_disclaimer(self) -> None:
        """
        Attempt to hide disclaimer (ignored - disclaimer always visible).
        
        This method exists but does nothing - disclaimer cannot be hidden.
        """
        # Ignored - disclaimer always visible
        pass
    
    def get_disclaimer_position(self) -> str:
        """Get disclaimer position (always prominent)."""
        return self._disclaimer_position
    
    def fetch_cve(
        self,
        cve_id: str,
        human_initiated: bool = False,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Fetch CVE data (requires human initiation).
        
        Args:
            cve_id: CVE identifier
            human_initiated: MUST be True
            session_id: Optional session ID for audit
            
        Returns:
            CVE reference data
            
        Raises:
            UIGovernanceViolation: If human_initiated is False
        """
        # GOVERNANCE CHECK: Require human initiation
        if not human_initiated:
            raise UIGovernanceViolation(
                "CVE fetch blocked: human_initiated must be True. "
                "Automated CVE fetching is prohibited in UI."
            )
        
        # Import Phase-15 CVE reference (human-gated)
        from phase15_governance.cve_reference import fetch_cve_from_api
        
        # Call Phase-15 with human_initiated=True
        return fetch_cve_from_api(
            cve_id=cve_id,
            human_initiated=True,  # Always True when called from UI
            session_id=session_id,
        )
    
    def render_cve(self, cve_data: dict[str, Any]) -> str:
        """
        Render single CVE as flat text with disclaimer.
        
        Args:
            cve_data: CVE data dict
            
        Returns:
            Flat text rendering with disclaimer
        """
        cve_id = cve_data.get("cve_id", "UNKNOWN")
        description = cve_data.get("description", "No description available")
        
        # Flat text only - no badges, colors, icons
        # Disclaimer always included
        return f"""
{self._disclaimer}

---
CVE ID: {cve_id}
Description: {description}
Status: NOT VERIFIED (reference-only)
---
"""
    
    def render_cve_list(self, cve_list: list[dict[str, Any]]) -> str:
        """
        Render list of CVEs as flat text with disclaimer.
        
        CVEs are sorted alphabetically by ID - no priority ordering.
        
        Args:
            cve_list: List of CVE data dicts
            
        Returns:
            Flat text rendering with disclaimer
        """
        # Sort alphabetically by CVE ID - no priority ordering
        sorted_cves = sorted(cve_list, key=lambda x: x.get("cve_id", ""))
        
        # Build flat text output
        output_parts = [self._disclaimer, "\n---"]
        
        for cve_data in sorted_cves:
            cve_id = cve_data.get("cve_id", "UNKNOWN")
            description = cve_data.get("description", "No description")
            
            # Flat text - no badges, colors, icons
            output_parts.append(f"""
CVE ID: {cve_id}
Description: {description}
Status: NOT VERIFIED (reference-only)
---""")
        
        return "\n".join(output_parts)
