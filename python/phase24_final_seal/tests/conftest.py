"""
Phase-24 Test Configuration

Fixtures for Final System Seal & Decommission Mode tests.
"""

import pytest
from datetime import datetime, timezone


@pytest.fixture
def sample_sealed_by() -> str:
    """Sample sealer identifier for testing."""
    return "John Doe, Governance Lead"


@pytest.fixture
def sample_seal_reason() -> str:
    """Sample seal reason for testing."""
    return "All governance phases complete. System ready for seal."


@pytest.fixture
def sample_archive_hash() -> str:
    """Sample archive hash for testing."""
    return "a" * 64


@pytest.fixture
def sample_timestamp() -> str:
    """Sample ISO-8601 timestamp for testing."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def sample_decommission_reason() -> str:
    """Sample decommission reason for testing."""
    return "Project complete. System no longer needed."


@pytest.fixture
def sample_decommissioned_by() -> str:
    """Sample decommissioner identifier for testing."""
    return "Jane Smith, Project Manager"

