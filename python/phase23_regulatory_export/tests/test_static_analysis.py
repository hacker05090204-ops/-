"""
Phase-23 Static Analysis Tests

Tests verifying NO forbidden imports or patterns exist in Phase-23 code.
"""

import pytest
import ast
from pathlib import Path


FORBIDDEN_FUNCTION_PREFIXES = {
    "auto_select",
    "detect_jurisdiction",
    "recommend_",
    "interpret_",
    "analyze_legal",
    "check_compliance",
}


def get_phase23_python_files() -> list[Path]:
    """Get all Python files in phase23_regulatory_export module."""
    phase23_dir = Path(__file__).parent.parent
    return list(phase23_dir.glob("*.py"))


class TestNoForbiddenFunctions:
    """Tests verifying no auto-selection or legal interpretation functions."""

    def test_no_auto_selection_functions(self) -> None:
        """Phase-23 must not define auto-selection functions."""
        for filepath in get_phase23_python_files():
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

    def test_no_phase13_to_phase22_imports(self) -> None:
        """Phase-23 must not import from Phase-13 through Phase-22."""
        forbidden_modules = {
            "phase13", "phase14", "phase15", "phase16", "phase17",
            "phase18", "phase19", "phase20", "phase21", "phase22",
            "browser_shell", "phase15_governance", "phase16_ui",
            "phase17_runtime", "phase18_distribution", "phase19_submission",
            "phase20_reflection", "phase21_patch_covenant", "phase22_chain_of_custody",
        }
        
        for filepath in get_phase23_python_files():
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


class TestNoContentModification:
    """Tests verifying no content modification functions."""

    def test_no_modify_content_function(self) -> None:
        """Phase-23 must not have content modification functions."""
        for filepath in get_phase23_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name_lower = node.name.lower()
                    
                    forbidden_patterns = [
                        "modify_findings",
                        "alter_content",
                        "transform_findings",
                    ]
                    
                    for pattern in forbidden_patterns:
                        assert pattern not in func_name_lower, (
                            f"Content modification function '{node.name}' "
                            f"found in {filepath.name}"
                        )

