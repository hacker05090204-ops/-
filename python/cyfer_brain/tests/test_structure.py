"""
Property Tests for Project Structure

**Feature: cyfer-brain, Property: Project Structure Validation**
**Validates: Cyfer Brain is separate from MCP**
"""

import pytest
import os
import sys


class TestProjectStructure:
    """Verify Cyfer Brain project structure is correct and separate from MCP."""
    
    def test_cyfer_brain_directory_exists(self):
        """Verify cyfer_brain directory exists."""
        # Get the path relative to this test file
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cyfer_brain_dir = os.path.dirname(test_dir)
        
        assert os.path.isdir(cyfer_brain_dir), "cyfer_brain directory should exist"
    
    def test_cyfer_brain_is_separate_from_mcp(self):
        """Verify cyfer_brain is in a separate directory from kali_mcp."""
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cyfer_brain_dir = os.path.dirname(test_dir)
        python_dir = os.path.dirname(cyfer_brain_dir)
        
        # Check that kali_mcp exists separately
        kali_mcp_dir = os.path.join(python_dir, "kali_mcp")
        
        # cyfer_brain should not be inside kali_mcp
        assert not cyfer_brain_dir.startswith(kali_mcp_dir), \
            "cyfer_brain should be separate from kali_mcp"
    
    def test_required_modules_exist(self):
        """Verify all required modules exist."""
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cyfer_brain_dir = os.path.dirname(test_dir)
        
        required_files = [
            "__init__.py",
            "types.py",
            "errors.py",
            "client.py",
        ]
        
        for filename in required_files:
            filepath = os.path.join(cyfer_brain_dir, filename)
            assert os.path.isfile(filepath), f"{filename} should exist in cyfer_brain"
    
    def test_can_import_cyfer_brain(self):
        """Verify cyfer_brain can be imported."""
        # Add parent directory to path for import
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cyfer_brain_dir = os.path.dirname(test_dir)
        python_dir = os.path.dirname(cyfer_brain_dir)
        
        if python_dir not in sys.path:
            sys.path.insert(0, python_dir)
        
        # Should be able to import without errors
        import cyfer_brain
        
        # Verify key exports exist
        assert hasattr(cyfer_brain, "Hypothesis")
        assert hasattr(cyfer_brain, "Observation")
        assert hasattr(cyfer_brain, "MCPClient")
        assert hasattr(cyfer_brain, "ArchitecturalViolationError")
    
    def test_cyfer_brain_does_not_import_mcp_internals(self):
        """Verify cyfer_brain does not import MCP internal modules.
        
        Cyfer Brain should only interact with MCP through the MCPClient interface,
        not by importing MCP internals directly.
        """
        test_dir = os.path.dirname(os.path.abspath(__file__))
        cyfer_brain_dir = os.path.dirname(test_dir)
        
        # Check source files for forbidden imports
        forbidden_imports = [
            "from kali_mcp.invariant",
            "from kali_mcp.proof",
            "from kali_mcp.state",
            "import kali_mcp.invariant",
            "import kali_mcp.proof",
            "import kali_mcp.state",
        ]
        
        for filename in os.listdir(cyfer_brain_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                filepath = os.path.join(cyfer_brain_dir, filename)
                with open(filepath, "r") as f:
                    content = f.read()
                    for forbidden in forbidden_imports:
                        assert forbidden not in content, \
                            f"{filename} should not import MCP internals: {forbidden}"
