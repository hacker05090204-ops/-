"""
Phase-21 Test Configuration

Fixtures for Patch Covenant & Update Validation tests.
"""

import pytest
from datetime import datetime, timezone


@pytest.fixture
def sample_patch_content() -> str:
    """Sample patch content for testing."""
    return """
--- a/module.py
+++ b/module.py
@@ -10,7 +10,7 @@
 def allowed_function():
-    return "old"
+    return "new"
"""


@pytest.fixture
def sample_patch_id() -> str:
    """Sample patch ID for testing."""
    return "patch-12345678-1234-1234-1234-123456789abc"


@pytest.fixture
def sample_session_id() -> str:
    """Sample session ID for testing."""
    return "session-12345678-1234-1234-1234-123456789abc"


@pytest.fixture
def sample_timestamp() -> str:
    """Sample ISO-8601 timestamp for testing."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def sample_allowlist() -> frozenset:
    """Sample symbol allowlist for testing."""
    return frozenset({
        "allowed_function",
        "safe_method",
        "permitted_class",
    })


@pytest.fixture
def sample_denylist() -> frozenset:
    """Sample symbol denylist for testing."""
    return frozenset({
        "forbidden_function",
        "dangerous_method",
        "blocked_class",
        "eval",
        "exec",
    })


@pytest.fixture
def sample_human_reason() -> str:
    """Sample human-provided reason for testing."""
    return "Reviewed patch and confirmed it only modifies allowed symbols."

