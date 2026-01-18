"""
Phase-29 API Test Fixtures

GOVERNANCE:
- All fixtures enforce human_initiated=True
- No background execution in fixtures
- No automation patterns
"""

import pytest
from datetime import datetime, timezone


@pytest.fixture
def valid_human_initiation() -> dict:
    """Valid human initiation metadata."""
    return {
        "human_initiated": True,
        "initiation_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "element_id": "test-button",
            "user_action": "click",
        },
    }


@pytest.fixture
def invalid_human_initiation_false() -> dict:
    """Invalid: human_initiated=False."""
    return {
        "human_initiated": False,
        "initiation_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "element_id": "test-button",
            "user_action": "click",
        },
    }


@pytest.fixture
def invalid_human_initiation_missing() -> dict:
    """Invalid: human_initiated missing."""
    return {
        "initiation_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "element_id": "test-button",
            "user_action": "click",
        },
    }


@pytest.fixture
def valid_session_config() -> dict:
    """Valid session configuration."""
    return {
        "enable_video": False,
        "viewport_width": 1280,
        "viewport_height": 720,
    }


@pytest.fixture
def valid_navigate_action() -> dict:
    """Valid navigate action."""
    return {
        "action_type": "navigate",
        "target": "https://example.com",
        "parameters": {},
    }


@pytest.fixture
def valid_click_action() -> dict:
    """Valid click action."""
    return {
        "action_type": "click",
        "target": "#submit-button",
        "parameters": {},
    }


@pytest.fixture
def valid_scroll_action() -> dict:
    """Valid scroll action."""
    return {
        "action_type": "scroll",
        "target": "body",
        "parameters": {"direction": "down", "amount": 300},
    }
