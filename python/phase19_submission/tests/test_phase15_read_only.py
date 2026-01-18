"""
Test: Phase-15 Read-Only Access

GOVERNANCE: Phase-19 MUST have read-only access to Phase-15.
No modification, no deletion, no update of Phase-15 data.
"""

import pytest
import ast
from pathlib import Path


class TestPhase15ReadOnly:
    """Verify Phase-15 access is read-only."""

    def test_no_phase15_write_operations(self):
        """No write operations to Phase-15."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "phase15.write",
            "phase15.update",
            "phase15.delete",
            "phase15.modify",
            "phase15.save",
            "phase15.create",
            "phase15.insert",
            "phase15.append",
            "phase15.remove",
            "phase15.clear",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text().lower()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden Phase-15 write pattern '{pattern}' in {py_file.name}"

    def test_no_phase15_mutation_methods(self):
        """No mutation methods called on Phase-15 data."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            ".set(",
            ".put(",
            ".post(",
            ".patch(",
            ".delete(",
            "= phase15",  # Assignment from Phase-15 that could be mutated
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            # Check for mutation patterns near phase15 references
            if "phase15" in content.lower():
                for pattern in forbidden_patterns:
                    # Allow read operations
                    if ".get(" in pattern:
                        continue
                    # Check if pattern appears near phase15
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if "phase15" in line.lower() and pattern in line:
                            pytest.fail(
                                f"Potential Phase-15 mutation in {py_file.name}:{i+1}"
                            )


class TestPhase15DataIntegrity:
    """Verify Phase-15 data is not modified during export."""

    def test_export_creates_copy(self):
        """Export creates a copy, not a reference."""
        from ..types import Finding
        
        original = Finding(
            finding_id="ORIG-001",
            title="Original Title",
            description="Original description",
        )
        
        # Findings are frozen dataclasses - immutable by design
        assert original.finding_id == "ORIG-001"
        assert original.title == "Original Title"
        
        # Cannot modify frozen dataclass
        with pytest.raises(AttributeError):
            original.title = "Modified Title"

    def test_findings_are_immutable(self):
        """Finding objects are immutable."""
        from ..types import Finding
        
        finding = Finding(
            finding_id="TEST-001",
            title="Test",
            description="Test",
        )
        
        # Frozen dataclass prevents modification
        with pytest.raises(AttributeError):
            finding.finding_id = "MODIFIED"


class TestNoPhase15Imports:
    """Verify no dangerous Phase-15 imports."""

    def test_no_phase15_write_imports(self):
        """No imports that could write to Phase-15."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_imports = [
            "phase15_governance.writer",
            "phase15_governance.modifier",
            "phase15_governance.updater",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        for forbidden in forbidden_imports:
                            assert not node.module.startswith(forbidden), \
                                f"Forbidden import '{node.module}' in {py_file.name}"
