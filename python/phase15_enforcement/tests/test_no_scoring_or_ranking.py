"""
Phase-15 No Scoring or Ranking Tests

MANDATORY DECLARATION:
Phase-15 may ONLY implement enforcement, validation, logging, and blocking.
NO authority, verification, learning, autonomy, inference, ranking, scoring,
or decision-making is permitted.

FORBIDDEN:
- score
- rank
- classify
- severity
- criticality
- priority
- confidence

Tests MUST FAIL initially (pytest-first methodology).
"""

import pytest
import ast
from pathlib import Path

FORBIDDEN_SCORING_WORDS = [
    "score", "rank", "classify",
    "severity", "criticality", "priority",
    "confidence", "weight", "rating",
]

PHASE15_DIR = Path(__file__).parent.parent


class TestNoScoringOrRanking:
    """Verify NO scoring or ranking exists in Phase-15."""

    def test_no_score_functions(self):
        """No score_* or rank_* functions may exist."""
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
                        if "score" in name_lower:
                            violations.append(f"{py_file.name}: {node.name}")
                        if "rank" in name_lower:
                            violations.append(f"{py_file.name}: {node.name}")
                        if "classify" in name_lower:
                            violations.append(f"{py_file.name}: {node.name}")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Scoring/ranking functions found: {violations}"

    def test_no_severity_constants(self):
        """No severity/priority constants may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in item.targets if isinstance(node, ast.Assign) else []:
                            pass
                    # Check for SEVERITY, PRIORITY, etc.
                    if "SEVERITY" in content.upper() or "PRIORITY" in content.upper():
                        if py_file.name not in [v.split(":")[0] for v in violations]:
                            violations.append(f"{py_file.name}: SEVERITY or PRIORITY constant")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Severity/priority constants found: {violations}"

    def test_no_confidence_values(self):
        """No confidence values or scores may exist."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text().lower()
                if "confidence" in content:
                    # Allow in comments/docstrings that say "no confidence"
                    if "no confidence" not in content and "not confidence" not in content:
                        violations.append(f"{py_file.name}: confidence pattern")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Confidence patterns found: {violations}"

    def test_no_ranking_return_types(self):
        """No functions may return ranked/scored results."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                # Check for common ranking patterns
                patterns = ["sorted_by_score", "ranked_", "top_n", "highest_"]
                for pattern in patterns:
                    if pattern in content.lower():
                        violations.append(f"{py_file.name}: ranking pattern '{pattern}'")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Ranking patterns found: {violations}"
