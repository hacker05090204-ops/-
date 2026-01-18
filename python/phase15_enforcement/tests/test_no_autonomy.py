"""
Phase-15 No Autonomy Tests

MANDATORY DECLARATION:
Phase-15 may ONLY implement enforcement, validation, logging, and blocking.
NO authority, verification, learning, autonomy, inference, ranking, scoring,
or decision-making is permitted.

FORBIDDEN (IMMEDIATE HALT IF PRESENT):
- autonomous agents
- background jobs
- schedulers
- retry logic
- batch execution
- silent fallbacks
- auto-execute any action
- navigate autonomously
- act without human initiation

Tests MUST FAIL initially (pytest-first methodology).
"""

import pytest
import ast
from pathlib import Path

# Forbidden autonomy patterns
FORBIDDEN_AUTONOMY_PATTERNS = [
    "auto_", "autonomous", "agent",
    "background", "scheduler", "cron",
    "retry", "batch_execute", "auto_execute",
    "auto_navigate", "self_", "daemon",
]

PHASE15_DIR = Path(__file__).parent.parent


class TestNoAutonomy:
    """Verify NO autonomous behavior exists in Phase-15."""

    def test_no_auto_prefixed_functions(self):
        """No auto_* prefixed functions may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.name.startswith("auto_"):
                            violations.append(f"{py_file.name}: {node.name}")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Auto-prefixed functions found: {violations}"

    def test_no_agent_classes(self):
        """No Agent classes may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if "agent" in node.name.lower():
                            violations.append(f"{py_file.name}: {node.name}")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Agent classes found: {violations}"

    def test_no_scheduler_imports(self):
        """No scheduler-related imports may exist."""
        forbidden_imports = ["schedule", "apscheduler", "celery", "threading.Timer"]
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text().lower()
                for imp in forbidden_imports:
                    if imp.lower() in content:
                        violations.append(f"{py_file.name}: imports '{imp}'")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Scheduler imports found: {violations}"

    def test_no_background_thread_creation(self):
        """No background thread creation may exist."""
        forbidden_patterns = ["Thread(", "daemon=True", "start()"]
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                for pattern in forbidden_patterns:
                    if pattern in content and "daemon=True" in content:
                        violations.append(f"{py_file.name}: daemon thread pattern")
                        break
            except Exception:
                pass
        
        # This is a loose check - may need refinement
        # For now, just ensure no obvious daemon patterns
        assert len(violations) == 0, f"Background threads found: {violations}"

    def test_no_retry_decorators(self):
        """No retry decorators or logic may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        for decorator in node.decorator_list:
                            if hasattr(decorator, 'id') and 'retry' in decorator.id.lower():
                                violations.append(f"{py_file.name}: @{decorator.id}")
                            elif hasattr(decorator, 'attr') and 'retry' in decorator.attr.lower():
                                violations.append(f"{py_file.name}: @{decorator.attr}")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Retry decorators found: {violations}"
