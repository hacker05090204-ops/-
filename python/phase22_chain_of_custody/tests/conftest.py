"""
Phase-22 Test Configuration

Fixtures for Chain-of-Custody & Legal Attestation tests.
"""

import pytest
from datetime import datetime, timezone


@pytest.fixture
def sample_evidence_hash() -> str:
    """Sample evidence hash for testing."""
    return "a" * 64


@pytest.fixture
def sample_attestor_id() -> str:
    """Sample attestor identifier for testing."""
    return "John Doe, Security Researcher"


@pytest.fixture
def sample_attestation_text() -> str:
    """Sample attestation text for testing."""
    return "I attest that I have reviewed this evidence and it is accurate to the best of my knowledge."


@pytest.fixture
def sample_timestamp() -> str:
    """Sample ISO-8601 timestamp for testing."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def sample_from_party() -> str:
    """Sample from party for testing."""
    return "Security Team"


@pytest.fixture
def sample_to_party() -> str:
    """Sample to party for testing."""
    return "Legal Department"


@pytest.fixture
def sample_refusal_reason() -> str:
    """Sample refusal reason for testing."""
    return "I cannot attest to evidence I have not personally verified."

