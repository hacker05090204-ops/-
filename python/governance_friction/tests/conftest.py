"""
Pytest configuration for Phase-10 tests.
"""

import pytest
from hypothesis import settings, Verbosity

# Configure hypothesis for property tests
settings.register_profile(
    "phase10",
    max_examples=100,  # MANDATORY: minimum 100 iterations per property
    verbosity=Verbosity.normal,
    deadline=None,  # No deadline for timing-sensitive tests
)
settings.load_profile("phase10")


@pytest.fixture
def decision_id():
    """Provide a test decision ID."""
    return "test-decision-001"


@pytest.fixture
def reviewer_id():
    """Provide a test reviewer ID."""
    return "test-reviewer-001"


@pytest.fixture
def original_content():
    """Provide test original content."""
    return "This is the original vulnerability report content."


@pytest.fixture
def edited_content():
    """Provide test edited content (meaningful edit)."""
    return "This is the MODIFIED vulnerability report content with changes."


@pytest.fixture
def whitespace_only_edit():
    """Provide test content with only whitespace changes."""
    return "This is the original vulnerability report content. "


@pytest.fixture
def context():
    """Provide test context for challenge generation."""
    return {
        "type": "vulnerability",
        "title": "SQL Injection in Login Form",
        "summary": "Critical SQL injection vulnerability found in login endpoint",
    }
