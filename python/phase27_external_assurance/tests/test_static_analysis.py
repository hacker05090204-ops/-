"""
Phase-27 Static Analysis Tests

NO AUTHORITY / PROOF ONLY

Tests for forbidden patterns via static analysis.
"""

import ast
import pytest
from pathlib import Path


# Module directory
MODULE_DIR = Path(__file__).parent.parent


def get_module_files():
    """Get all Python files in the module (excluding tests)."""
    files = []
    for f in MODULE_DIR.glob("*.py"):
        if f.name != "__init__.py" and not f.name.startswith("test_"):
            files.append(f)
    return files


def get_all_imports(filepath: Path) -> set[str]:
    """Extract all imports from a Python file."""
    try:
        source = filepath.read_text()
        tree = ast.parse(source)
    except Exception:
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def get_all_names(filepath: Path) -> set[str]:
    """Extract all names (identifiers) from a Python file."""
    try:
        source = filepath.read_text()
        tree = ast.parse(source)
    except Exception:
        return set()

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
    return names


class TestNoNetworkImports:
    """Tests that no network-related imports exist."""

    FORBIDDEN_NETWORK_IMPORTS = {
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "http",
    }

    def test_no_network_imports(self):
        """Module MUST NOT import network libraries."""
        for filepath in get_module_files():
            imports = get_all_imports(filepath)
            forbidden = imports & self.FORBIDDEN_NETWORK_IMPORTS
            assert not forbidden, f"{filepath.name} imports forbidden network modules: {forbidden}"


class TestNoExecutionImports:
    """Tests that no execution-related imports exist."""

    FORBIDDEN_EXECUTION_IMPORTS = {
        "subprocess",
        "multiprocessing",
        "concurrent",
        "asyncio",  # Only if used for background tasks
    }

    def test_no_subprocess_import(self):
        """Module MUST NOT import subprocess."""
        for filepath in get_module_files():
            imports = get_all_imports(filepath)
            assert "subprocess" not in imports, f"{filepath.name} imports subprocess"

    def test_no_multiprocessing_import(self):
        """Module MUST NOT import multiprocessing."""
        for filepath in get_module_files():
            imports = get_all_imports(filepath)
            assert "multiprocessing" not in imports, f"{filepath.name} imports multiprocessing"


class TestNoScoringSymbols:
    """Tests that no scoring-related symbols exist."""

    FORBIDDEN_SCORING_SYMBOLS = {
        "score",
        "rank",
        "classify",
        "prioritize",
        "weight",
        "rating",
        "severity",
    }

    def test_no_scoring_function_names(self):
        """Module MUST NOT have scoring function names."""
        for filepath in get_module_files():
            names = get_all_names(filepath)
            # Check for function names starting with forbidden prefixes
            for name in names:
                name_lower = name.lower()
                for forbidden in self.FORBIDDEN_SCORING_SYMBOLS:
                    if name_lower.startswith(forbidden) or name_lower.startswith(f"auto_{forbidden}"):
                        pytest.fail(f"{filepath.name} has forbidden scoring symbol: {name}")


class TestNoAutomationSymbols:
    """Tests that no automation-related symbols exist."""

    FORBIDDEN_AUTOMATION_PREFIXES = {
        "auto_",
        "schedule_",
        "trigger_",
        "background_",
        "daemon_",
    }

    def test_no_automation_function_names(self):
        """Module MUST NOT have automation function names."""
        for filepath in get_module_files():
            names = get_all_names(filepath)
            for name in names:
                name_lower = name.lower()
                for prefix in self.FORBIDDEN_AUTOMATION_PREFIXES:
                    if name_lower.startswith(prefix):
                        pytest.fail(f"{filepath.name} has forbidden automation symbol: {name}")


class TestNoEnforcementSymbols:
    """Tests that no enforcement-related symbols exist."""

    FORBIDDEN_ENFORCEMENT_SYMBOLS = {
        "enforce",
        "block",
        "reject",
        "deny",
        "prevent",
    }

    def test_no_enforcement_function_names(self):
        """Module MUST NOT have enforcement function names."""
        for filepath in get_module_files():
            names = get_all_names(filepath)
            for name in names:
                name_lower = name.lower()
                for forbidden in self.FORBIDDEN_ENFORCEMENT_SYMBOLS:
                    # Allow "disclaimer" but not "enforce_*"
                    if name_lower.startswith(f"{forbidden}_") or name_lower == forbidden:
                        pytest.fail(f"{filepath.name} has forbidden enforcement symbol: {name}")


class TestNoPriorPhaseImports:
    """Tests that no prior phase imports exist."""

    FORBIDDEN_PHASE_IMPORTS = {
        f"phase{i}" for i in range(13, 27)
    }

    def test_no_prior_phase_imports(self):
        """Module MUST NOT import from prior phases."""
        for filepath in get_module_files():
            imports = get_all_imports(filepath)
            for imp in imports:
                for forbidden in self.FORBIDDEN_PHASE_IMPORTS:
                    if forbidden in imp.lower():
                        pytest.fail(f"{filepath.name} imports from prior phase: {imp}")
