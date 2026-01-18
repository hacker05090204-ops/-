"""
Phase-21 Static Analysis Tests

Tests verifying NO forbidden imports or patterns exist in Phase-21 code.
"""

import pytest
import ast
from pathlib import Path


# Forbidden imports that would enable patch analysis
FORBIDDEN_IMPORTS = {
    "nltk",
    "spacy",
    "transformers",
    "openai",
    "anthropic",
    "langchain",
    "sklearn",
    "tensorflow",
    "torch",
    "keras",
}

# Forbidden function names that suggest analysis
# These must be exact matches or prefixes, not substrings
FORBIDDEN_FUNCTION_PREFIXES = {
    "analyze_",
    "analyse_",
    "score_",
    "rank_",
    "rate_",
    "suggest_",
    "recommend_",
    "evaluate_",
    "assess_",
    "auto_apply",
    "auto_confirm",
    "auto_approve",
    "schedule_patch",
}

FORBIDDEN_FUNCTION_EXACT = {
    "analyze",
    "analyse",
    "score",
    "rank",
    "rate",
    "suggest",
    "recommend",
    "evaluate",
    "assess",
}

# Forbidden field names that suggest scoring
FORBIDDEN_FIELD_NAMES = {
    "score",
    "quality",
    "rating",
    "rank",
    "safety_score",
    "confidence",
    "probability",
}


def get_phase21_python_files() -> list[Path]:
    """Get all Python files in phase21_patch_covenant module."""
    phase21_dir = Path(__file__).parent.parent
    return list(phase21_dir.glob("*.py"))


class TestNoForbiddenImports:
    """Tests verifying no ML/AI imports."""

    def test_no_ml_imports(self) -> None:
        """Phase-21 must not import ML/AI libraries."""
        for filepath in get_phase21_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        assert module_name not in FORBIDDEN_IMPORTS, (
                            f"Forbidden import '{alias.name}' found in {filepath.name}"
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split(".")[0]
                        assert module_name not in FORBIDDEN_IMPORTS, (
                            f"Forbidden import from '{node.module}' found in {filepath.name}"
                        )


class TestNoForbiddenFunctions:
    """Tests verifying no analysis or auto-apply functions exist."""

    def test_no_analysis_functions(self) -> None:
        """Phase-21 must not define analysis functions."""
        for filepath in get_phase21_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name_lower = node.name.lower()
                    
                    # Check exact matches
                    assert func_name_lower not in FORBIDDEN_FUNCTION_EXACT, (
                        f"Forbidden function name '{node.name}' found in {filepath.name}"
                    )
                    
                    # Check prefixes
                    for forbidden in FORBIDDEN_FUNCTION_PREFIXES:
                        assert not func_name_lower.startswith(forbidden), (
                            f"Forbidden function name '{node.name}' "
                            f"(starts with '{forbidden}') found in {filepath.name}"
                        )


class TestNoForbiddenFields:
    """Tests verifying no scoring fields exist."""

    def test_no_scoring_fields_in_dataclasses(self) -> None:
        """Phase-21 dataclasses must not have scoring fields."""
        for filepath in get_phase21_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            field_name_lower = item.target.id.lower()
                            for forbidden in FORBIDDEN_FIELD_NAMES:
                                assert forbidden not in field_name_lower, (
                                    f"Forbidden field '{item.target.id}' "
                                    f"(contains '{forbidden}') in class {node.name} "
                                    f"in {filepath.name}"
                                )


class TestNoPriorPhaseImports:
    """Tests verifying no imports from prior phases."""

    def test_no_phase13_to_phase20_imports(self) -> None:
        """Phase-21 must not import from Phase-13 through Phase-20."""
        forbidden_modules = {
            "phase13",
            "phase14",
            "phase15",
            "phase16",
            "phase17",
            "phase18",
            "phase19",
            "phase20",
            "browser_shell",
            "phase15_governance",
            "phase16_ui",
            "phase17_runtime",
            "phase18_distribution",
            "phase19_submission",
            "phase20_reflection",
        }
        
        for filepath in get_phase21_python_files():
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


class TestNoBackgroundProcessing:
    """Tests verifying no background patch processing."""

    def test_no_thread_for_patches(self) -> None:
        """Phase-21 must not use threading for patch processing."""
        for filepath in get_phase21_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module == "threading":
                        for alias in node.names:
                            assert alias.name != "Thread", (
                                f"Thread import found in {filepath.name} - "
                                "background processing forbidden"
                            )

    def test_no_async_patch_processing(self) -> None:
        """Patch processing must be synchronous."""
        for filepath in get_phase21_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef):
                    func_name_lower = node.name.lower()
                    assert "patch" not in func_name_lower, (
                        f"Async patch function '{node.name}' found in {filepath.name} - "
                        "patch processing must be synchronous"
                    )
                    assert "apply" not in func_name_lower, (
                        f"Async apply function '{node.name}' found in {filepath.name} - "
                        "patch application must be synchronous"
                    )

