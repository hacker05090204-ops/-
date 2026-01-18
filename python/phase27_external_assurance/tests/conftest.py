"""
Phase-27 Test Configuration

NO AUTHORITY / PROOF ONLY

This test configuration is for external assurance testing only.
"""

import pytest


@pytest.fixture
def sample_artifact_path(tmp_path):
    """Create a sample artifact file for testing."""
    artifact = tmp_path / "sample_artifact.txt"
    artifact.write_text("Sample artifact content for hash testing.")
    return str(artifact)


@pytest.fixture
def sample_governance_doc(tmp_path):
    """Create a sample governance document for testing."""
    doc = tmp_path / "SAMPLE_GOVERNANCE.md"
    doc.write_text("# Sample Governance Document\n\nThis is a test document.")
    return str(doc)


@pytest.fixture
def nonexistent_path():
    """Return a path that does not exist."""
    return "/nonexistent/path/to/artifact.txt"
