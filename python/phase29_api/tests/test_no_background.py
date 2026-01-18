"""
Phase-29 No Background Execution Tests

PYTEST-FIRST: These tests MUST be written BEFORE implementation.

GOVERNANCE:
- NO background threads
- NO background tasks
- NO polling
- NO scheduled jobs
- NO async background execution
"""

import pytest
import ast
import inspect
from pathlib import Path


class TestNoBackgroundPatterns:
    """Test that no background execution patterns exist in Phase-29 code."""

    def _get_phase29_source_files(self) -> list[Path]:
        """Get all Python source files in phase29_api."""
        phase29_dir = Path(__file__).parent.parent
        return [
            f for f in phase29_dir.glob("*.py")
            if f.name != "__init__.py" and not f.name.startswith("test_")
        ]

    def test_no_threading_import(self) -> None:
        """MUST NOT import threading module."""
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name != "threading", (
                            f"GOVERNANCE VIOLATION: threading import in {source_file.name}"
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "threading" in node.module:
                        pytest.fail(
                            f"GOVERNANCE VIOLATION: threading import in {source_file.name}"
                        )

    def test_no_multiprocessing_import(self) -> None:
        """MUST NOT import multiprocessing module."""
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name != "multiprocessing", (
                            f"GOVERNANCE VIOLATION: multiprocessing import in {source_file.name}"
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "multiprocessing" in node.module:
                        pytest.fail(
                            f"GOVERNANCE VIOLATION: multiprocessing import in {source_file.name}"
                        )

    def test_no_background_tasks_usage(self) -> None:
        """MUST NOT use FastAPI BackgroundTasks."""
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text()
            # Check for BackgroundTasks import or usage
            assert "BackgroundTasks" not in content, (
                f"GOVERNANCE VIOLATION: BackgroundTasks in {source_file.name}"
            )
            assert "background_tasks" not in content.lower() or "# no background" in content.lower(), (
                f"GOVERNANCE VIOLATION: background_tasks pattern in {source_file.name}"
            )

    def test_no_asyncio_create_task_for_background(self) -> None:
        """MUST NOT use asyncio.create_task for background work."""
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text()
            # create_task is allowed for awaited tasks, but not fire-and-forget
            # This is a heuristic check
            if "create_task" in content:
                # Ensure it's awaited or stored for later await
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "create_task" in line and "await" not in line:
                        # Check if the task is stored and awaited later
                        # This is a simplified check
                        if "=" not in line:
                            pytest.fail(
                                f"GOVERNANCE VIOLATION: Unawaited create_task in {source_file.name}:{i+1}"
                            )

    def test_no_scheduler_imports(self) -> None:
        """MUST NOT import scheduling libraries."""
        forbidden_schedulers = ["schedule", "apscheduler", "celery", "rq"]
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text()
            for scheduler in forbidden_schedulers:
                assert scheduler not in content.lower(), (
                    f"GOVERNANCE VIOLATION: {scheduler} in {source_file.name}"
                )


class TestNoPollingPatterns:
    """Test that no polling patterns exist."""

    def test_no_while_true_loops(self) -> None:
        """MUST NOT have while True polling loops."""
        phase29_dir = Path(__file__).parent.parent
        for source_file in phase29_dir.glob("*.py"):
            if source_file.name.startswith("test_"):
                continue
            if not source_file.exists():
                continue
            content = source_file.read_text()
            # Simple heuristic: while True with sleep is likely polling
            if "while True" in content and "sleep" in content:
                pytest.fail(
                    f"GOVERNANCE VIOLATION: Potential polling loop in {source_file.name}"
                )

    def test_no_setinterval_equivalent(self) -> None:
        """MUST NOT have setInterval-like patterns."""
        phase29_dir = Path(__file__).parent.parent
        for source_file in phase29_dir.glob("*.py"):
            if source_file.name.startswith("test_"):
                continue
            if not source_file.exists():
                continue
            content = source_file.read_text()
            # Check for timer-based polling
            forbidden_patterns = [
                "Timer(",
                "call_later",
                "call_at",
                "call_repeatedly",
            ]
            for pattern in forbidden_patterns:
                assert pattern not in content, (
                    f"GOVERNANCE VIOLATION: {pattern} in {source_file.name}"
                )
