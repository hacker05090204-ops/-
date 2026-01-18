"""
Phase-9 Browser Observer Tests

Tests for passive browser observation.
"""

import pytest
from datetime import datetime

from browser_assistant.observer import BrowserObserver
from browser_assistant.types import ObservationType, BrowserObservation
from browser_assistant.errors import InvalidObservationError


class TestBrowserObserver:
    """Test browser observer functionality."""
    
    def test_receive_observation(self, browser_observer):
        """Verify observations can be received."""
        obs = browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com/page",
            content="Page content",
        )
        
        assert obs.observation_id is not None
        assert obs.observation_type == ObservationType.URL_NAVIGATION
        assert obs.url == "https://example.com/page"
        assert obs.content == "Page content"
    
    def test_observation_is_passive(self, browser_observer):
        """Verify observations are marked as passive."""
        obs = browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com",
            content="Test",
        )
        
        assert obs.is_passive_observation is True
        assert obs.no_modification_performed is True
    
    def test_observation_with_metadata(self, browser_observer):
        """Verify observations can include metadata."""
        obs = browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com",
            content="Test",
            metadata={"referrer": "https://google.com", "method": "GET"},
        )
        
        assert len(obs.metadata) == 2
        # Metadata is sorted tuples
        assert ("method", "GET") in obs.metadata
        assert ("referrer", "https://google.com") in obs.metadata
    
    def test_observation_with_custom_timestamp(self, browser_observer):
        """Verify observations can have custom timestamps."""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        obs = browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com",
            content="Test",
            timestamp=custom_time,
        )
        
        assert obs.timestamp == custom_time
    
    def test_invalid_observation_empty_url(self, browser_observer):
        """Verify empty URL raises error."""
        with pytest.raises(InvalidObservationError):
            browser_observer.receive_observation(
                observation_type=ObservationType.URL_NAVIGATION,
                url="",
                content="Test",
            )
    
    def test_invalid_observation_empty_content(self, browser_observer):
        """Verify empty content raises error."""
        with pytest.raises(InvalidObservationError):
            browser_observer.receive_observation(
                observation_type=ObservationType.URL_NAVIGATION,
                url="https://example.com",
                content="",
            )
    
    def test_url_credential_sanitization(self, browser_observer):
        """Verify credentials are removed from URLs."""
        obs = browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://user:password@example.com/page",
            content="Test",
        )
        
        assert "password" not in obs.url
        assert "[REDACTED]" in obs.url
    
    def test_get_observations(self, browser_observer):
        """Verify observations can be retrieved."""
        # Add multiple observations
        for i in range(5):
            browser_observer.receive_observation(
                observation_type=ObservationType.URL_NAVIGATION,
                url=f"https://example.com/page{i}",
                content=f"Content {i}",
            )
        
        observations = browser_observer.get_observations()
        assert len(observations) == 5
    
    def test_get_observations_with_limit(self, browser_observer):
        """Verify observation retrieval respects limit."""
        for i in range(10):
            browser_observer.receive_observation(
                observation_type=ObservationType.URL_NAVIGATION,
                url=f"https://example.com/page{i}",
                content=f"Content {i}",
            )
        
        observations = browser_observer.get_observations(limit=3)
        assert len(observations) == 3
    
    def test_get_observations_by_type(self, browser_observer):
        """Verify observations can be filtered by type."""
        browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com/nav",
            content="Navigation",
        )
        browser_observer.receive_observation(
            observation_type=ObservationType.FORM_DETECTED,
            url="https://example.com/form",
            content="Form",
        )
        
        nav_obs = browser_observer.get_observations(
            observation_type=ObservationType.URL_NAVIGATION,
        )
        assert len(nav_obs) == 1
        assert nav_obs[0].observation_type == ObservationType.URL_NAVIGATION
    
    def test_get_observations_by_url_pattern(self, browser_observer):
        """Verify observations can be filtered by URL pattern."""
        browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com/api/users",
            content="Users API",
        )
        browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com/page",
            content="Page",
        )
        
        api_obs = browser_observer.get_observations(url_pattern="/api/")
        assert len(api_obs) == 1
        assert "/api/" in api_obs[0].url
    
    def test_get_observation_by_id(self, browser_observer):
        """Verify observation can be retrieved by ID."""
        obs = browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com",
            content="Test",
        )
        
        retrieved = browser_observer.get_observation_by_id(obs.observation_id)
        assert retrieved is not None
        assert retrieved.observation_id == obs.observation_id
    
    def test_get_observation_by_id_not_found(self, browser_observer):
        """Verify None returned for unknown ID."""
        retrieved = browser_observer.get_observation_by_id("nonexistent")
        assert retrieved is None
    
    def test_get_recent_urls(self, browser_observer):
        """Verify recent URLs can be retrieved."""
        browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com/page1",
            content="Page 1",
        )
        browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com/page2",
            content="Page 2",
        )
        browser_observer.receive_observation(
            observation_type=ObservationType.URL_NAVIGATION,
            url="https://example.com/page1",  # Duplicate
            content="Page 1 again",
        )
        
        urls = browser_observer.get_recent_urls()
        # Should be unique
        assert len(urls) == 2
    
    def test_clear_observations(self, browser_observer):
        """Verify observations can be cleared."""
        for i in range(5):
            browser_observer.receive_observation(
                observation_type=ObservationType.URL_NAVIGATION,
                url=f"https://example.com/page{i}",
                content=f"Content {i}",
            )
        
        count = browser_observer.clear_observations()
        assert count == 5
        
        observations = browser_observer.get_observations()
        assert len(observations) == 0
    
    def test_observation_limit_enforced(self, browser_observer):
        """Verify observation storage limit is enforced."""
        # Set a lower limit for testing
        browser_observer._max_observations = 10
        
        for i in range(15):
            browser_observer.receive_observation(
                observation_type=ObservationType.URL_NAVIGATION,
                url=f"https://example.com/page{i}",
                content=f"Content {i}",
            )
        
        observations = browser_observer.get_observations(limit=100)
        assert len(observations) == 10


class TestObserverNoForbiddenMethods:
    """Verify observer has no forbidden methods."""
    
    def test_no_execute_script(self, browser_observer):
        """Verify execute_script method does not exist."""
        assert not hasattr(browser_observer, "execute_script")
    
    def test_no_inject_payload(self, browser_observer):
        """Verify inject_payload method does not exist."""
        assert not hasattr(browser_observer, "inject_payload")
    
    def test_no_modify_request(self, browser_observer):
        """Verify modify_request method does not exist."""
        assert not hasattr(browser_observer, "modify_request")
    
    def test_no_intercept_traffic(self, browser_observer):
        """Verify intercept_traffic method does not exist."""
        assert not hasattr(browser_observer, "intercept_traffic")
    
    def test_no_navigate_to(self, browser_observer):
        """Verify navigate_to method does not exist."""
        assert not hasattr(browser_observer, "navigate_to")
    
    def test_no_click_element(self, browser_observer):
        """Verify click_element method does not exist."""
        assert not hasattr(browser_observer, "click_element")
    
    def test_no_fill_form(self, browser_observer):
        """Verify fill_form method does not exist."""
        assert not hasattr(browser_observer, "fill_form")
    
    def test_no_submit_form(self, browser_observer):
        """Verify submit_form method does not exist."""
        assert not hasattr(browser_observer, "submit_form")
    
    def test_no_take_screenshot(self, browser_observer):
        """Verify take_screenshot method does not exist."""
        assert not hasattr(browser_observer, "take_screenshot")
    
    def test_no_record_video(self, browser_observer):
        """Verify record_video method does not exist."""
        assert not hasattr(browser_observer, "record_video")
