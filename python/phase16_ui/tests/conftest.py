"""
Phase-16 UI Test Configuration

Provides fixtures for testing UI components under governance constraints.
"""

import pytest
from typing import Any


@pytest.fixture
def sample_cve_data() -> dict[str, Any]:
    """Sample CVE data for testing (reference-only)."""
    return {
        "cve_id": "CVE-2021-44228",
        "is_reference_only": True,
        "disclaimer": "CVE data is reference-only and does not verify, confirm, or validate vulnerabilities.",
        "description": "Reference data for CVE-2021-44228 (API lookup)",
        "source": "CVE API (reference-only)",
    }


@pytest.fixture
def sample_finding() -> dict[str, Any]:
    """Sample finding data for testing (not verified)."""
    return {
        "id": "finding-001",
        "title": "Sample Finding",
        "description": "This is a sample finding for testing.",
        "evidence": "Sample evidence content",
        "is_verified": False,  # Always False - UI cannot verify
    }


@pytest.fixture
def sample_evidence() -> str:
    """Sample evidence content for testing."""
    return "This is sample evidence content that should be displayed as-is."


@pytest.fixture
def mock_session_id() -> str:
    """Mock session ID for testing."""
    return "test-session-001"
