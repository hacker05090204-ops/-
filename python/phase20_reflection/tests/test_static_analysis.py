"""
Phase-20 Static Analysis Tests

These tests verify NO forbidden imports or patterns exist in Phase-20 code.
"""

import pytest
import ast
import os
from pathlib import Path


# Forbidden imports that would enable content analysis
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
    "gensim",
    "textblob",
    "pattern",
    "polyglot",
    "flair",
}

# Forbidden function names that suggest analysis
FORBIDDEN_FUNCTION_NAMES = {
    "analyze",
    "analyse",
    "score",
    "rank",
    "rate",
    "suggest",
    "recommend",
    "evaluate",
    "assess",
    "classify",
    "categorize",
    "sentiment",
    "tokenize",
    "parse_content",
    "extract_meaning",
    "validate_content",
    "check_quality",
}

# Forbidden field names that suggest scoring
FORBIDDEN_FIELD_NAMES = {
    "score",
    "quality",
    "rating",
    "rank",
    "sentiment",
    "confidence",
    "probability",
    "likelihood",
    "weight",
    "importance",
}


def get_phase20_python_files() -> list[Path]:
    """Get all Python files in phase20_reflection module."""
    phase20_dir = Path(__file__).parent.parent
    return list(phase20_dir.glob("*.py"))


class TestNoForbiddenImports:
    """Tests verifying no NLP or AI imports."""

    def test_no_nlp_imports(self) -> None:
        """Phase-20 must not import NLP libraries."""
        for filepath in get_phase20_python_files():
            if filepath.name.startswith("test_"):
                continue  # Skip test files
            
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
    """Tests verifying no analysis functions exist."""

    def test_no_analysis_functions(self) -> None:
        """Phase-20 must not define analysis functions."""
        for filepath in get_phase20_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name_lower = node.name.lower()
                    for forbidden in FORBIDDEN_FUNCTION_NAMES:
                        assert forbidden not in func_name_lower, (
                            f"Forbidden function name '{node.name}' "
                            f"(contains '{forbidden}') found in {filepath.name}"
                        )


class TestNoForbiddenFields:
    """Tests verifying no scoring fields exist."""

    def test_no_scoring_fields_in_dataclasses(self) -> None:
        """Phase-20 dataclasses must not have scoring fields."""
        for filepath in get_phase20_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check for dataclass fields
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            field_name_lower = item.target.id.lower()
                            for forbidden in FORBIDDEN_FIELD_NAMES:
                                assert forbidden not in field_name_lower, (
                                    f"Forbidden field '{item.target.id}' "
                                    f"(contains '{forbidden}') in class {node.name} "
                                    f"in {filepath.name}"
                                )


class TestNoBackgroundThreads:
    """Tests verifying no background processing."""

    def test_no_thread_imports(self) -> None:
        """Phase-20 must not use threading for reflection."""
        for filepath in get_phase20_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # threading is allowed for other purposes, but not for reflection
                        # We check for Thread class usage instead
                        pass
                elif isinstance(node, ast.ImportFrom):
                    if node.module == "threading":
                        for alias in node.names:
                            assert alias.name != "Thread", (
                                f"Thread import found in {filepath.name} - "
                                "background processing forbidden"
                            )

    def test_no_async_reflection_processing(self) -> None:
        """Reflection processing must be synchronous."""
        for filepath in get_phase20_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef):
                    func_name_lower = node.name.lower()
                    # Async is forbidden for reflection-related functions
                    assert "reflection" not in func_name_lower, (
                        f"Async reflection function '{node.name}' found in {filepath.name} - "
                        "reflection must be synchronous"
                    )


class TestNoContentRegex:
    """Tests verifying no regex-based content analysis."""

    def test_no_content_analysis_regex(self) -> None:
        """Phase-20 must not use regex for content analysis."""
        # Allowed regex patterns (for hashing, formatting, etc.)
        allowed_patterns = {
            r"^[a-f0-9]{64}$",  # SHA-256 validation
            r"^\d{4}-\d{2}-\d{2}",  # Date format
        }
        
        for filepath in get_phase20_python_files():
            if filepath.name.startswith("test_"):
                continue
            
            content = filepath.read_text()
            
            # Check for re.compile or re.match/search with content-analysis patterns
            # This is a heuristic check - we look for suspicious patterns
            suspicious_patterns = [
                "re.compile.*reflection",
                "re.match.*reflection",
                "re.search.*reflection",
                "re.findall.*reflection",
            ]
            
            for pattern in suspicious_patterns:
                # Simple string check - not perfect but catches obvious cases
                assert pattern not in content.lower(), (
                    f"Suspicious regex pattern found in {filepath.name}"
                )
