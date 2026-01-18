"""
Phase-24 Static Analysis Tests

Tests verifying NO forbidden imports or patterns exist in Phase-24 code.
"""

import pytest
import ast
from pathlib import Path


FORBIDDEN_FUNCTION_PREFIXES = {
    "auto_seal",
    "auto_decommission",
    "schedule_",
    "modify_history",
    "delete_",
    "reopen_phase",
}


def get_phase24_python_files() -> list[Path]:
    """Get all Python files in phase24_final_seal module."""
    phase24_dir = Path(__file__).parent.parent
    return list(phase24_dir.glob("*.py"))


class TestNoForbiddenFunctions:
    """Tests verifying no auto-seal or auto-decommission functions."""

    def test_no_auto_functions(self) -> None:
        """Phase-24 must not define auto functions."""
        for filepath in get_phase24_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name_lower = node.name.lower()
                    
                    for forbidden in FORBIDDEN_FUNCTION_PREFIXES:
                        assert not func_name_lower.startswith(forbidden), (
                            f"Forbidden function name '{node.name}' "
                            f"(starts with '{forbidden}') found in {filepath.name}"
                        )


class TestNoPriorPhaseImports:
    """Tests verifying no imports from prior phases."""

    def test_no_phase13_to_phase23_imports(self) -> None:
        """Phase-24 must not import from Phase-13 through Phase-23."""
        forbidden_modules = {
            "phase13", "phase14", "phase15", "phase16", "phase17",
            "phase18", "phase19", "phase20", "phase21", "phase22", "phase23",
            "browser_shell", "phase15_governance", "phase16_ui",
            "phase17_runtime", "phase18_distribution", "phase19_submission",
            "phase20_reflection", "phase21_patch_covenant", "phase22_chain_of_custody",
            "phase23_regulatory_export",
        }
        
        for filepath in get_phase24_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        assert module_name not in forbidden_modules, (
                            f"Forbidden import from prior phase '{alias.name}' "
                            f"found in {filepath.name}"
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split(".")[0]
                        assert module_name not in forbidden_modules, (
                            f"Forbidden import from prior phase '{node.module}' "
                            f"found in {filepath.name}"
                        )


class TestNoHistoryModification:
    """Tests verifying no history modification functions."""

    def test_no_modify_history_function(self) -> None:
        """Phase-24 must not have history modification functions."""
        for filepath in get_phase24_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name_lower = node.name.lower()
                    
                    forbidden_patterns = [
                        "modify_audit",
                        "delete_phase",
                        "rewrite_history",
                        "alter_archive",
                    ]
                    
                    for pattern in forbidden_patterns:
                        assert pattern not in func_name_lower, (
                            f"History modification function '{node.name}' "
                            f"found in {filepath.name}"
                        )

