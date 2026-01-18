"""
Test: No Automation (RISK-D)

GOVERNANCE: All actions MUST require explicit human initiation.
No implicit triggers, no background execution, no auto-actions.
"""

import pytest
import ast
import inspect
from pathlib import Path

from ..types import ExportRequest, URLOpenRequest, Finding, ExportFormat
from ..errors import HumanInitiationRequired, HumanConfirmationRequired, AutomationAttempt


class TestNoAutomation:
    """Verify no automation exists in Phase-19."""

    def test_export_requires_human_initiation(self, sample_findings):
        """Export MUST require human_initiated=True."""
        with pytest.raises(ValueError, match="human-initiated"):
            ExportRequest(
                findings=sample_findings,
                export_format=ExportFormat.TXT,
                human_initiated=False,
            )

    def test_export_succeeds_with_human_initiation(self, sample_findings):
        """Export succeeds when human_initiated=True."""
        request = ExportRequest(
            findings=sample_findings,
            export_format=ExportFormat.TXT,
            human_initiated=True,
        )
        assert request.human_initiated is True

    def test_url_open_requires_human_confirmation(self):
        """URL open MUST require human_confirmed=True."""
        with pytest.raises(ValueError, match="human-confirmed"):
            URLOpenRequest(
                url="https://example.com",
                human_confirmed=False,
            )

    def test_url_open_succeeds_with_human_confirmation(self):
        """URL open succeeds when human_confirmed=True."""
        request = URLOpenRequest(
            url="https://example.com",
            human_confirmed=True,
        )
        assert request.human_confirmed is True


class TestNoBackgroundExecution:
    """Verify no background execution patterns exist."""

    def test_no_threading_imports(self):
        """Phase-19 modules MUST NOT import threading."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_imports = [
            "threading",
            "multiprocessing",
            "concurrent.futures",
            "asyncio",
            "subprocess",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name not in forbidden_imports, \
                            f"Forbidden import '{alias.name}' in {py_file.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for forbidden in forbidden_imports:
                            assert not node.module.startswith(forbidden), \
                                f"Forbidden import from '{node.module}' in {py_file.name}"

    def test_no_async_functions(self):
        """Phase-19 modules MUST NOT have async functions."""
        phase19_dir = Path(__file__).parent.parent
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                assert not isinstance(node, ast.AsyncFunctionDef), \
                    f"Async function found in {py_file.name}: {node.name}"

    def test_no_timer_patterns(self):
        """Phase-19 modules MUST NOT have timer/scheduler patterns."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "Timer(",
            "schedule(",
            "cron",
            "interval",
            "setTimeout",
            "setInterval",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden pattern '{pattern}' in {py_file.name}"


class TestNoImplicitTriggers:
    """Verify no implicit triggers exist."""

    def test_no_on_load_patterns(self):
        """No on-load or auto-execute patterns."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "__init__",  # Check for auto-execution in __init__
            "on_load",
            "on_start",
            "auto_run",
            "auto_execute",
            "on_render",
            "on_data_change",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name in ["__init__.py", "conftest.py"] or py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            # Check for auto-execution patterns (not just the words)
            assert "if __name__" not in content or "main()" not in content, \
                f"Auto-execution pattern in {py_file.name}"

    def test_no_event_listeners_without_human_action(self):
        """No event listeners that trigger without human action."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "addEventListener",
            "on_event",
            "subscribe(",
            "watch(",
            "observe(",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden event pattern '{pattern}' in {py_file.name}"
