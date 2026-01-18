"""
Test: Static Analysis for Governance Compliance

GOVERNANCE: Comprehensive static analysis to detect violations.
"""

import pytest
import ast
from pathlib import Path


class TestNoForbiddenImports:
    """Verify no forbidden imports exist."""

    def test_no_network_imports(self):
        """No network-related imports."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_imports = [
            "requests",
            "urllib",
            "http.client",
            "socket",
            "aiohttp",
            "httpx",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name not in forbidden_imports, \
                            f"Forbidden import '{alias.name}' in {py_file.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for forbidden in forbidden_imports:
                            assert not node.module.startswith(forbidden), \
                                f"Forbidden import from '{node.module}' in {py_file.name}"

    def test_no_database_imports(self):
        """No database-related imports."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_imports = [
            "sqlite3",
            "psycopg2",
            "mysql",
            "pymongo",
            "redis",
            "sqlalchemy",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name not in forbidden_imports, \
                            f"Forbidden import '{alias.name}' in {py_file.name}"


class TestNoForbiddenPatterns:
    """Verify no forbidden code patterns exist."""

    def test_no_eval_or_exec(self):
        """No eval() or exec() calls."""
        phase19_dir = Path(__file__).parent.parent
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        assert node.func.id not in ["eval", "exec", "compile"], \
                            f"Forbidden call '{node.func.id}' in {py_file.name}"

    def test_no_subprocess(self):
        """No subprocess calls."""
        phase19_dir = Path(__file__).parent.parent
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            assert "subprocess" not in content, \
                f"Forbidden subprocess in {py_file.name}"

    def test_no_os_system(self):
        """No os.system calls."""
        phase19_dir = Path(__file__).parent.parent
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            assert "os.system" not in content, \
                f"Forbidden os.system in {py_file.name}"


class TestCodeStructure:
    """Verify code structure compliance."""

    def test_all_modules_have_docstrings(self):
        """All modules MUST have docstrings."""
        phase19_dir = Path(__file__).parent.parent
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            # Check module docstring
            assert ast.get_docstring(tree) is not None, \
                f"Missing docstring in {py_file.name}"

    def test_no_global_mutable_state(self):
        """No global mutable state (excluding local variables in functions)."""
        phase19_dir = Path(__file__).parent.parent
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            # Only check module-level assignments (not inside functions)
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    if isinstance(node.targets[0], ast.Name):
                        name = node.targets[0].id
                        # Allow constants (UPPER_CASE) and private vars
                        if not name.isupper() and not name.startswith("_"):
                            # Check if it's mutable
                            if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                                pytest.fail(
                                    f"Global mutable state '{name}' in {py_file.name}"
                                )


class TestGovernanceCompliance:
    """Verify overall governance compliance."""

    def test_no_decision_making_logic(self):
        """No decision-making logic that could influence human."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "decide",
            "choose",
            "select",
            "pick",
            "determine",
            "analyze",
            "evaluate",
            "assess",
            "judge",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text().lower()
            
            for pattern in forbidden_patterns:
                # Allow in comments and docstrings context
                if f"# {pattern}" in content or f'"{pattern}' in content:
                    continue
                # Check for function/method names
                if f"def {pattern}" in content:
                    pytest.fail(
                        f"Decision-making function '{pattern}' in {py_file.name}"
                    )

    def test_no_intelligence_patterns(self):
        """No intelligence or inference patterns in function/variable names."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "predict",
            "infer",
            "classify",
            "categorize",
            "learn",
            "neural",
            "ml_",
            "ai_",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            # Check function and variable names only
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    name_lower = node.name.lower()
                    for pattern in forbidden_patterns:
                        assert pattern not in name_lower, \
                            f"Forbidden function '{node.name}' in {py_file.name}"
                elif isinstance(node, ast.Name):
                    name_lower = node.id.lower()
                    for pattern in forbidden_patterns:
                        assert pattern not in name_lower, \
                            f"Forbidden variable '{node.id}' in {py_file.name}"
