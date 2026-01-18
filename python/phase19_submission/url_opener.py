"""
Phase-19 URL Opener

GOVERNANCE CONSTRAINTS:
- Human click required to open URL
- Human confirmation required before opening
- URL passed through verbatim (no validation, parsing, or analysis)
- No platform detection or selection
- No URL safety checks
- Visible action only (no background)

This module handles opening external URLs for submission.
Human confirmation is REQUIRED for all URL opens.
"""

import webbrowser
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .types import URLOpenRequest, SubmissionLog, SubmissionAction
from .errors import HumanConfirmationRequired


@dataclass
class URLOpenResult:
    """Result of URL open operation."""
    url: str
    opened: bool
    timestamp: datetime
    attribution: str = "HUMAN"


class URLOpener:
    """
    Opens URLs in browser.
    
    GOVERNANCE:
    - Human confirmation required
    - URL passed verbatim (no analysis)
    - No platform detection
    - Visible action only
    """
    
    def __init__(self):
        """Initialize URL opener."""
        self._logs: list = []
    
    def open_url(
        self,
        url: str,
        human_confirmed: bool,
    ) -> URLOpenResult:
        """
        Open URL in browser.
        
        Args:
            url: URL to open (passed verbatim, no validation)
            human_confirmed: MUST be True
            
        Returns:
            URLOpenResult with operation details
            
        Raises:
            HumanConfirmationRequired: If human_confirmed is False
        """
        # GOVERNANCE: Require human confirmation
        if not human_confirmed:
            raise HumanConfirmationRequired(
                "URL open MUST be confirmed by human action"
            )
        
        # GOVERNANCE: Pass URL verbatim (no validation, no parsing)
        # We do NOT:
        # - Validate URL format
        # - Parse URL components
        # - Check URL safety
        # - Detect platform
        # - Classify URL type
        
        timestamp = datetime.now()
        
        # Open URL in default browser
        # This is a visible action (not background)
        try:
            webbrowser.open(url)
            opened = True
        except Exception:
            opened = False
        
        # Log the action with HUMAN attribution
        log = SubmissionLog(
            timestamp=timestamp,
            action=SubmissionAction.OPEN_URL,
            attribution="HUMAN",
            details=f"Opened URL: {url}",
        )
        self._logs.append(log)
        
        return URLOpenResult(
            url=url,
            opened=opened,
            timestamp=timestamp,
            attribution="HUMAN",
        )
    
    def get_logs(self) -> list:
        """Get all URL open logs."""
        return list(self._logs)
