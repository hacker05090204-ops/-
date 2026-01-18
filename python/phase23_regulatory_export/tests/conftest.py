"""
Phase-23 Test Configuration

Fixtures for Regulatory Export & Jurisdiction Mode tests.
"""

import pytest
from datetime import datetime, timezone


@pytest.fixture
def sample_jurisdiction_code() -> str:
    """Sample jurisdiction code for testing."""
    return "US"


@pytest.fixture
def sample_jurisdiction_name() -> str:
    """Sample jurisdiction name for testing."""
    return "United States"


@pytest.fixture
def sample_timestamp() -> str:
    """Sample ISO-8601 timestamp for testing."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def sample_content() -> str:
    """Sample content for testing."""
    return "Vulnerability finding: XSS in login form."


@pytest.fixture
def sample_content_hash() -> str:
    """Sample content hash for testing."""
    return "a" * 64


@pytest.fixture
def sample_selected_by() -> str:
    """Sample selector identifier for testing."""
    return "John Doe, Security Researcher"

