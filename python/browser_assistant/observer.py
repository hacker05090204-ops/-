"""
Phase-9 Browser Observer

PASSIVE observation of browser activity.

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- NO request modification
- NO JavaScript injection
- NO traffic interception
- NO payload execution
- NO browser automation
- NO DOM manipulation

This observer ONLY receives data that the browser extension
sends to it. It does NOT control the browser in any way.

Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
import uuid

from browser_assistant.types import (
    BrowserObservation,
    ObservationType,
)
from browser_assistant.errors import (
    InvalidObservationError,
    AutomationAttemptError,
    NetworkExecutionAttemptError,
)
from browser_assistant.boundaries import Phase9BoundaryGuard


class BrowserObserver:
    """
    Passive observer of browser activity.
    
    SECURITY: This observer ONLY receives data. It NEVER:
    - Sends commands to the browser
    - Modifies requests or responses
    - Injects JavaScript
    - Intercepts traffic
    - Automates browser actions
    
    The browser extension sends observations TO this observer.
    This observer does NOT send commands TO the browser.
    
    FORBIDDEN METHODS (do not add):
    - execute_script()
    - inject_payload()
    - modify_request()
    - intercept_traffic()
    - navigate_to()
    - click_element()
    - fill_form()
    - submit_form()
    """
    
    def __init__(self):
        """Initialize the browser observer."""
        Phase9BoundaryGuard.assert_passive_observation()
        Phase9BoundaryGuard.assert_no_network_execution()
        Phase9BoundaryGuard.assert_no_automation()
        
        self._observations: List[BrowserObservation] = []
        self._max_observations = 10000  # Prevent unbounded growth
    
    def receive_observation(
        self,
        observation_type: ObservationType,
        url: str,
        content: str,
        metadata: Optional[dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> BrowserObservation:
        """
        Receive an observation from the browser extension.
        
        This method is called BY the browser extension to report
        what the user is doing. It does NOT control the browser.
        
        Args:
            observation_type: Type of observation.
            url: URL where observation occurred.
            content: Content of the observation.
            metadata: Additional context (optional).
            timestamp: When observation occurred (optional, defaults to now).
            
        Returns:
            BrowserObservation record.
            
        Raises:
            InvalidObservationError: If observation data is invalid.
        """
        # Validate inputs
        if not url:
            raise InvalidObservationError("URL is required")
        if not content:
            raise InvalidObservationError("Content is required")
        
        # Sanitize URL - remove credentials if present
        sanitized_url = self._sanitize_url(url)
        
        # Convert metadata to frozen tuples
        frozen_metadata: tuple[tuple[str, str], ...] = ()
        if metadata:
            frozen_metadata = tuple(sorted(metadata.items()))
        
        # Create observation
        observation = BrowserObservation(
            observation_id=str(uuid.uuid4()),
            observation_type=observation_type,
            timestamp=timestamp or datetime.now(),
            url=sanitized_url,
            content=content,
            metadata=frozen_metadata,
            is_passive_observation=True,  # Always True
            no_modification_performed=True,  # Always True
        )
        
        # Store observation (with size limit)
        if len(self._observations) >= self._max_observations:
            self._observations.pop(0)  # Remove oldest
        self._observations.append(observation)
        
        return observation
    
    def get_observations(
        self,
        observation_type: Optional[ObservationType] = None,
        url_pattern: Optional[str] = None,
        limit: int = 100,
    ) -> List[BrowserObservation]:
        """
        Get stored observations with optional filtering.
        
        Args:
            observation_type: Filter by type (optional).
            url_pattern: Filter by URL substring (optional).
            limit: Maximum observations to return.
            
        Returns:
            List of matching observations (newest first).
        """
        results = []
        
        for obs in reversed(self._observations):
            if len(results) >= limit:
                break
            
            # Apply filters
            if observation_type and obs.observation_type != observation_type:
                continue
            if url_pattern and url_pattern not in obs.url:
                continue
            
            results.append(obs)
        
        return results
    
    def get_observation_by_id(
        self,
        observation_id: str,
    ) -> Optional[BrowserObservation]:
        """
        Get a specific observation by ID.
        
        Args:
            observation_id: ID of the observation.
            
        Returns:
            BrowserObservation if found, None otherwise.
        """
        for obs in self._observations:
            if obs.observation_id == observation_id:
                return obs
        return None
    
    def get_recent_urls(self, limit: int = 10) -> List[str]:
        """
        Get recently observed URLs.
        
        Args:
            limit: Maximum URLs to return.
            
        Returns:
            List of unique URLs (newest first).
        """
        seen = set()
        urls = []
        
        for obs in reversed(self._observations):
            if len(urls) >= limit:
                break
            if obs.url not in seen:
                seen.add(obs.url)
                urls.append(obs.url)
        
        return urls
    
    def clear_observations(self) -> int:
        """
        Clear all stored observations.
        
        Returns:
            Number of observations cleared.
        """
        count = len(self._observations)
        self._observations.clear()
        return count
    
    def _sanitize_url(self, url: str) -> str:
        """
        Sanitize URL by removing credentials.
        
        Args:
            url: URL to sanitize.
            
        Returns:
            Sanitized URL.
        """
        # Remove credentials from URL (user:pass@host)
        if "@" in url and "://" in url:
            protocol_end = url.index("://") + 3
            at_pos = url.index("@")
            # Only sanitize if @ is before the first /
            slash_pos = url.find("/", protocol_end)
            if slash_pos == -1 or at_pos < slash_pos:
                url = url[:protocol_end] + "[REDACTED]@" + url[at_pos + 1:]
        return url
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    #
    # - execute_script() - Phase-9 does NOT execute JavaScript
    # - inject_payload() - Phase-9 does NOT inject payloads
    # - modify_request() - Phase-9 does NOT modify requests
    # - intercept_traffic() - Phase-9 does NOT intercept traffic
    # - navigate_to() - Phase-9 does NOT control navigation
    # - click_element() - Phase-9 does NOT click elements
    # - fill_form() - Phase-9 does NOT fill forms
    # - submit_form() - Phase-9 does NOT submit forms
    # - send_keys() - Phase-9 does NOT send keystrokes
    # - take_screenshot() - Phase-9 does NOT capture screenshots
    # - record_video() - Phase-9 does NOT record video
    # - start_recording() - Phase-9 does NOT start recording
    # - stop_recording() - Phase-9 does NOT stop recording
    # ========================================================================
