"""
Phase-15 No Verification Language Tests

MANDATORY DECLARATION:
Phase-15 may ONLY implement enforcement, validation, logging, and blocking.
NO authority, verification, learning, autonomy, inference, ranking, scoring,
or decision-making is permitted.

FORBIDDEN WORDS (IMMEDIATE HALT IF PRESENT):
- "verify", "verified", "verification"
- "accurate", "accuracy", "confidence"
- "severity", "criticality", "priority"
- "rank", "score", "classify"

Tests MUST FAIL initially (pytest-first methodology).
"""

import pytest
import ast
import os
from pathlib import Path

# Forbidden words that must NOT appear in Phase-15 code
FORBIDDEN_WORDS = [
    "verify", "verified", "verification",
    "accurate", "accuracy", "confidence",
    "severity", "criticality", "priority",
    "rank", "score", "classify",
]

# Phase-15 source directory
PHASE15_DIR = Path(__file__).parent.parent


class TestNoVerificationLanguage:
    """Verify forbidden words do NOT appear in Phase-15 code."""

    def test_phase15_directory_exists(self):
        """Phase-15 directory must exist."""
        assert PHASE15_DIR.exists(), f"Phase-15 directory not found: {PHASE15_DIR}"

    def test_no_forbidden_words_in_source(self):
        """Forbidden words must NOT appear in source code."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            # Skip test files
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text().lower()
                for word in FORBIDDEN_WORDS:
                    if word in content:
                        violations.append(f"{py_file.name}: contains '{word}'")
            except Exception as e:
                pass  # Skip unreadable files
        
        assert len(violations) == 0, f"Forbidden words found: {violations}"

    def test_no_verification_functions(self):
        """No functions with verification-related names may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        name_lower = node.name.lower()
                        for word in FORBIDDEN_WORDS:
                            if word in name_lower:
                                violations.append(f"{py_file.name}: function '{node.name}'")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Forbidden functions found: {violations}"

    def test_no_verification_classes(self):
        """No classes with verification-related names may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        name_lower = node.name.lower()
                        for word in FORBIDDEN_WORDS:
                            if word in name_lower:
                                violations.append(f"{py_file.name}: class '{node.name}'")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Forbidden classes found: {violations}"
