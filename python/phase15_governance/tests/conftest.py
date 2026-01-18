"""
Phase-15 Test Configuration

Pytest configuration for Phase-15 governance tests.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

import pytest
import sys
from pathlib import Path


# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


@pytest.fixture(autouse=True)
def reset_audit_state():
    """Reset audit state before each test."""
    try:
        from phase15_governance import audit
        if hasattr(audit, "_reset_for_testing"):
            audit._reset_for_testing()
    except ImportError:
        pass  # Module not yet implemented
    yield
