"""
Phase-5 Scanner Test Configuration

Configures pytest and hypothesis for property-based testing.
All tests use synthetic artifacts (no real Phase-4 data).
"""

import pytest
from hypothesis import settings, Verbosity

# Hypothesis profiles
settings.register_profile(
    "ci",
    max_examples=100,
    deadline=5000,
    verbosity=Verbosity.normal,
)
settings.register_profile(
    "dev",
    max_examples=20,
    deadline=10000,
    verbosity=Verbosity.verbose,
)

# Load dev profile by default
settings.load_profile("dev")
