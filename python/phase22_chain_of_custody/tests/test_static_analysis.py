"""
Phase-22 Static Analysis Tests

Tests verifying NO forbidden imports or patterns exist in Phase-22 code.
"""

import pytest
import ast
from pathlib import Path


# Forbidden imports
FORBIDDEN_IMPORTS = {
    "nltk",
    "spacy",
    "transformers",
    "openai",
    "anthropic",
}

# Forbidden function prefixes
FORBIDDEN_FUNCTION_PREFIXES = {
    "analyze_",
    "score_",
    "validate_content",
    "judge_",
    "auto_generate",
    "auto_attest",
    "generate_attestation",
}

# Forbidden function exact names
FORBIDDEN_FUNCTION_EXACT = {
    "analyze",
    "score",
    "judge",
}


def get_phase22_python_files() -> list[Path]:
    """Get all Python files in phase22_chain_of_custody module."""
    phase22_dir = Path(__file__).parent.parent
    return list(phase22_dir.glob("*.py"))


class TestNoForbiddenImports:
    """Tests verifying no forbidden imports."""

    def test_no_nlp_imports(self) -> None:
        """Phase-22 must not import NLP libraries."""
        for filepath in get_phase22_python_files():
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
    """Tests verifying no analysis or auto-generation functions exist."""

    def test_no_analysis_functions(self) -> None:
        """Phase-22 must not define analysis functions."""
        for filepath in get_phase22_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name_lower = node.name.lower()
                    
                    assert func_name_lower not in FORBIDDEN_FUNCTION_EXACT, (
                        f"Forbidden function name '{node.name}' found in {filepath.name}"
                    )
                    
                    for forbidden in FORBIDDEN_FUNCTION_PREFIXES:
                        assert not func_name_lower.startswith(forbidden), (
                            f"Forbidden function name '{node.name}' "
                            f"(starts with '{forbidden}') found in {filepath.name}"
                        )


class TestNoPriorPhaseImports:
    """Tests verifying no imports from prior phases."""

    def test_no_phase13_to_phase21_imports(self) -> None:
        """Phase-22 must not import from Phase-13 through Phase-21."""
        forbidden_modules = {
            "phase13", "phase14", "phase15", "phase16", "phase17",
            "phase18", "phase19", "phase20", "phase21",
            "browser_shell", "phase15_governance", "phase16_ui",
            "phase17_runtime", "phase18_distribution", "phase19_submission",
            "phase20_reflection", "phase21_patch_covenant",
        }
        
        for filepath in get_phase22_python_files():
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


class TestNoEvidenceModification:
    """Tests verifying no evidence modification functions."""

    def test_no_modify_evidence_function(self) -> None:
        """Phase-22 must not have evidence modification functions."""
        for filepath in get_phase22_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name_lower = node.name.lower()
                    
                    forbidden_patterns = [
                        "modify_evidence",
                        "alter_evidence",
                        "transform_evidence",
                        "change_evidence",
                    ]
                    
                    for pattern in forbidden_patterns:
                        assert pattern not in func_name_lower, (
                            f"Evidence modification function '{node.name}' "
                            f"found in {filepath.name}"
                        )

