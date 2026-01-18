"""
Phase-17 Runtime Test Configuration

GOVERNANCE CONSTRAINT:
- All tests verify runtime-only behavior
- No automation, background execution, or intelligence
"""

import pytest
from typing import Generator


@pytest.fixture
def runtime_context() -> Generator[dict, None, None]:
    """Provide runtime test context."""
    yield {
        "human_initiated": True,
        "visible_window": True,
        "headless": False,
    }


@pytest.fixture
def forbidden_imports() -> list[str]:
    """List of forbidden imports for Phase-17."""
    return [
        "threading",
        "multiprocessing", 
        "subprocess",
        "schedule",
        "apscheduler",
        "celery",
        "asyncio",  # No async background tasks
    ]


@pytest.fixture
def forbidden_patterns() -> list[str]:
    """List of forbidden code patterns for Phase-17."""
    return [
        "Thread(",
        "Process(",
        "subprocess.Popen",
        "subprocess.run",
        "daemon=True",
        "headless=True",
        "auto_start",
        "auto_restart",
        "auto_update",
        "telemetry",
        "analytics",
        "Timer(",
        "schedule.",
    ]
