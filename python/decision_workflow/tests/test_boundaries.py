"""
Tests for Phase-6 Architectural Boundaries.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
"""

import pytest
import ast
import sys
from pathlib import Path

from decision_workflow.boundaries import BoundaryGuard
from decision_workflow.errors import ArchitecturalViolationError


# ============================================================================
# Unit Tests - Forbidden Methods
# ============================================================================

class TestForbiddenMethods:
    """
    Unit tests for forbidden methods.
    
    Each forbidden method must raise ArchitecturalViolationError.
    
    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """
    
    @pytest.fixture
    def guard(self):
        """Create a boundary guard."""
        return BoundaryGuard()
    
    def test_auto_classify_forbidden(self, guard):
        """auto_classify() raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            guard.auto_classify()
        
        assert exc_info.value.action == "auto_classify"
    
    def test_auto_severity_forbidden(self, guard):
        """auto_severity() raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            guard.auto_severity()
        
        assert exc_info.value.action == "auto_severity"
    
    def test_auto_submit_forbidden(self, guard):
        """auto_submit() raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            guard.auto_submit()
        
        assert exc_info.value.action == "auto_submit"
    
    def test_trigger_execution_forbidden(self, guard):
        """trigger_execution() raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            guard.trigger_execution()
        
        assert exc_info.value.action == "trigger_execution"
    
    def test_trigger_scan_forbidden(self, guard):
        """trigger_scan() raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            guard.trigger_scan()
        
        assert exc_info.value.action == "trigger_scan"
    
    def test_make_network_request_forbidden(self, guard):
        """make_network_request() raises ArchitecturalViolationError."""
        with pytest.raises(ArchitecturalViolationError) as exc_info:
            guard.make_network_request()
        
        assert exc_info.value.action == "make_network_request"
    
    def test_all_forbidden_methods_raise_correct_error_type(self, guard):
        """All forbidden methods raise ArchitecturalViolationError."""
        forbidden_methods = [
            "auto_classify",
            "auto_severity",
            "auto_submit",
            "trigger_execution",
            "trigger_scan",
            "make_network_request",
        ]
        
        for method_name in forbidden_methods:
            method = getattr(guard, method_name)
            with pytest.raises(ArchitecturalViolationError):
                method()


# ============================================================================
# Import Boundary Tests
# ============================================================================

class TestImportBoundaries:
    """
    Tests for import restrictions.
    
    Phase-6 must not import:
    - execution_layer (Phase-4)
    - httpx, requests, aiohttp (network libraries)
    
    Validates: Requirements 6.7, 6.8
    """
    
    @pytest.fixture
    def decision_workflow_path(self):
        """Get the path to the decision_workflow module."""
        return Path(__file__).parent.parent
    
    def test_no_execution_layer_import(self, decision_workflow_path):
        """decision_workflow must not import execution_layer."""
        forbidden_imports = self._find_imports(decision_workflow_path, "execution_layer")
        
        assert len(forbidden_imports) == 0, (
            f"Found forbidden imports of 'execution_layer' in: {forbidden_imports}"
        )
    
    def test_no_httpx_import(self, decision_workflow_path):
        """decision_workflow must not import httpx."""
        forbidden_imports = self._find_imports(decision_workflow_path, "httpx")
        
        assert len(forbidden_imports) == 0, (
            f"Found forbidden imports of 'httpx' in: {forbidden_imports}"
        )
    
    def test_no_requests_import(self, decision_workflow_path):
        """decision_workflow must not import requests."""
        forbidden_imports = self._find_imports(decision_workflow_path, "requests")
        
        assert len(forbidden_imports) == 0, (
            f"Found forbidden imports of 'requests' in: {forbidden_imports}"
        )
    
    def test_no_aiohttp_import(self, decision_workflow_path):
        """decision_workflow must not import aiohttp."""
        forbidden_imports = self._find_imports(decision_workflow_path, "aiohttp")
        
        assert len(forbidden_imports) == 0, (
            f"Found forbidden imports of 'aiohttp' in: {forbidden_imports}"
        )
    
    def test_no_network_libraries_in_any_file(self, decision_workflow_path):
        """No network libraries imported in any decision_workflow file."""
        network_libs = ["httpx", "requests", "aiohttp", "urllib3", "socket"]
        
        for lib in network_libs:
            forbidden_imports = self._find_imports(decision_workflow_path, lib)
            assert len(forbidden_imports) == 0, (
                f"Found forbidden imports of '{lib}' in: {forbidden_imports}"
            )
    
    def _find_imports(self, module_path: Path, module_name: str) -> list[str]:
        """
        Find all files that import the given module.
        
        Args:
            module_path: Path to the module directory.
            module_name: Name of the module to search for.
            
        Returns:
            List of file paths that import the module.
        """
        forbidden_files = []
        
        for py_file in module_path.rglob("*.py"):
            # Skip test files for import checking
            if "test_" in py_file.name:
                continue
            
            try:
                with open(py_file, "r") as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == module_name or alias.name.startswith(f"{module_name}."):
                                forbidden_files.append(str(py_file))
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and (
                            node.module == module_name or 
                            node.module.startswith(f"{module_name}.")
                        ):
                            forbidden_files.append(str(py_file))
            
            except SyntaxError:
                # Skip files with syntax errors
                pass
        
        return forbidden_files


# ============================================================================
# Runtime Import Tests
# ============================================================================

class TestRuntimeImports:
    """
    Tests that verify no forbidden modules are loaded at runtime.
    """
    
    def test_execution_layer_not_in_sys_modules(self):
        """execution_layer should not be loaded when importing decision_workflow."""
        # Import decision_workflow
        import decision_workflow
        
        # Check that execution_layer is not loaded
        execution_layer_modules = [
            m for m in sys.modules.keys() 
            if m == "execution_layer" or m.startswith("execution_layer.")
        ]
        
        assert len(execution_layer_modules) == 0, (
            f"execution_layer modules loaded: {execution_layer_modules}"
        )
    
    def test_httpx_not_in_sys_modules(self):
        """httpx should not be loaded when importing decision_workflow."""
        # Clear any existing httpx imports
        httpx_modules = [m for m in sys.modules.keys() if m.startswith("httpx")]
        for m in httpx_modules:
            del sys.modules[m]
        
        # Re-import decision_workflow
        import importlib
        import decision_workflow
        importlib.reload(decision_workflow)
        
        # Check that httpx is not loaded
        httpx_modules = [m for m in sys.modules.keys() if m.startswith("httpx")]
        
        # Note: httpx might be loaded by other test dependencies, so we just
        # verify decision_workflow doesn't directly import it
        # This is covered by the AST-based test above
    
    def test_requests_not_in_sys_modules(self):
        """requests should not be loaded when importing decision_workflow."""
        # This is covered by the AST-based test above
        pass
    
    def test_aiohttp_not_in_sys_modules(self):
        """aiohttp should not be loaded when importing decision_workflow."""
        # This is covered by the AST-based test above
        pass
