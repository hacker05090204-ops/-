"""
Test Execution Layer Project Structure

Validates that Execution Layer is separate from frozen phases.
"""

import os
import pytest


class TestProjectStructure:
    """Test project structure and separation from frozen phases."""
    
    def test_execution_layer_directory_exists(self):
        """Execution Layer directory should exist."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assert os.path.isdir(base_path)
    
    def test_execution_layer_has_init(self):
        """Execution Layer should have __init__.py."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        init_path = os.path.join(base_path, "__init__.py")
        assert os.path.isfile(init_path)
    
    def test_execution_layer_has_types(self):
        """Execution Layer should have types.py."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        types_path = os.path.join(base_path, "types.py")
        assert os.path.isfile(types_path)
    
    def test_execution_layer_has_errors(self):
        """Execution Layer should have errors.py."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        errors_path = os.path.join(base_path, "errors.py")
        assert os.path.isfile(errors_path)
    
    def test_execution_layer_separate_from_mcp(self):
        """Execution Layer should be separate from MCP."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Execution Layer should not be inside kali_mcp
        assert "kali_mcp" not in base_path
    
    def test_execution_layer_separate_from_cyfer_brain(self):
        """Execution Layer should be separate from Cyfer Brain."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Execution Layer should not be inside cyfer_brain
        assert "cyfer_brain" not in base_path
    
    def test_execution_layer_separate_from_bounty_pipeline(self):
        """Execution Layer should be separate from Bounty Pipeline."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Execution Layer should not be inside bounty_pipeline
        assert "bounty_pipeline" not in base_path
    
    def test_can_import_execution_layer(self):
        """Should be able to import execution_layer module."""
        import execution_layer
        assert hasattr(execution_layer, "__version__")
    
    def test_can_import_types(self):
        """Should be able to import types."""
        from execution_layer.types import (
            SafeActionType,
            ForbiddenActionType,
            ExecutionToken,
            SafeAction,
        )
        assert SafeActionType.NAVIGATE.value == "navigate"
        assert ForbiddenActionType.LOGIN.value == "login"
    
    def test_can_import_errors(self):
        """Should be able to import errors."""
        from execution_layer.errors import (
            ExecutionLayerError,
            ScopeViolationError,
            UnsafeActionError,
            ForbiddenActionError,
        )
        assert issubclass(ScopeViolationError, ExecutionLayerError)
