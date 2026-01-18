"""
Phase-20 Test Configuration

All tests verify HUMAN REFLECTION ONLY behavior.
No tests may require content analysis to pass.
"""

import pytest
import uuid
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def clear_reflection_store() -> None:
    """Clear the reflection store before each test."""
    from phase20_reflection.reflection_logger import clear_store_for_testing
    clear_store_for_testing()


@pytest.fixture
def session_id() -> str:
    """Generate a unique session ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_reflection_text() -> str:
    """Sample reflection text - content is NOT analyzed."""
    return "I reviewed the findings and believe they are valid based on my manual testing."


@pytest.fixture
def empty_reflection_text() -> str:
    """Empty reflection - must be accepted without validation."""
    return ""


@pytest.fixture
def decline_reason() -> str:
    """Sample decline reason - content is NOT analyzed."""
    return "I prefer not to provide a reflection at this time."


@pytest.fixture
def timestamp() -> str:
    """ISO-8601 timestamp for testing."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def mock_phase15_digest() -> str:
    """Mock Phase-15 log digest (SHA-256 hex)."""
    return "a" * 64  # 64 hex chars = 256 bits


@pytest.fixture
def mock_phase19_digest() -> str:
    """Mock Phase-19 export digest (SHA-256 hex)."""
    return "b" * 64  # 64 hex chars = 256 bits
