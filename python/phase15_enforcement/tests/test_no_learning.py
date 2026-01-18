"""
Phase-15 No Learning Tests

MANDATORY DECLARATION:
Phase-15 may ONLY implement enforcement, validation, logging, and blocking.
NO authority, verification, learning, autonomy, inference, ranking, scoring,
or decision-making is permitted.

FORBIDDEN:
- ML, heuristics, pattern learning
- feedback loops
- behavioral memory
- history analysis

Tests MUST FAIL initially (pytest-first methodology).
"""

import pytest
import ast
from pathlib import Path

# Forbidden learning patterns
FORBIDDEN_LEARNING_PATTERNS = [
    "learn", "train", "model", "predict",
    "heuristic", "pattern", "history",
    "feedback", "memory", "remember",
    "ml", "machine_learning", "neural",
]

PHASE15_DIR = Path(__file__).parent.parent


class TestNoLearning:
    """Verify NO learning behavior exists in Phase-15."""

    def test_no_learn_functions(self):
        """No learn_* functions may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.name.startswith("learn"):
                            violations.append(f"{py_file.name}: {node.name}")
                        if node.name.startswith("train"):
                            violations.append(f"{py_file.name}: {node.name}")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Learning functions found: {violations}"

    def test_no_ml_imports(self):
        """No ML library imports may exist."""
        forbidden_imports = [
            "sklearn", "tensorflow", "torch", "keras",
            "numpy.random", "scipy.optimize",
        ]
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                for imp in forbidden_imports:
                    if f"import {imp}" in content or f"from {imp}" in content:
                        violations.append(f"{py_file.name}: imports '{imp}'")
            except Exception:
                pass
        
        assert len(violations) == 0, f"ML imports found: {violations}"

    def test_no_memory_storage(self):
        """No behavioral memory storage may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if hasattr(target, 'id'):
                                        if 'memory' in target.id.lower():
                                            violations.append(f"{py_file.name}: {target.id}")
                                        if 'history' in target.id.lower():
                                            violations.append(f"{py_file.name}: {target.id}")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Memory storage found: {violations}"

    def test_no_feedback_loops(self):
        """No feedback loop patterns may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text().lower()
                if "feedback" in content and "loop" in content:
                    violations.append(f"{py_file.name}: feedback loop pattern")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Feedback loops found: {violations}"
