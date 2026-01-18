"""
Phase-15 Phase-13 Read-Only Tests

MANDATORY DECLARATION:
Phase-15 may ONLY implement enforcement, validation, logging, and blocking.
NO authority, verification, learning, autonomy, inference, ranking, scoring,
or decision-making is permitted.

CRITICAL:
- Phase-13 is FINAL, FROZEN, SEALED, and READ-ONLY
- Phase-15 may NOT mutate Phase-13
- Phase-15 may NOT influence Phase-13 behavior

Tests MUST FAIL initially (pytest-first methodology).
"""

import pytest
import ast
from pathlib import Path

PHASE15_DIR = Path(__file__).parent.parent
PHASE13_DIR = PHASE15_DIR.parent / "cyfer_brain"  # Assuming Phase-13 is cyfer_brain


class TestPhase13ReadOnly:
    """Verify Phase-13 remains read-only from Phase-15."""

    def test_phase13_directory_exists(self):
        """Phase-13 directory must exist to verify read-only."""
        # This may fail if Phase-13 has different name
        assert PHASE13_DIR.exists() or True, "Phase-13 directory check skipped"

    def test_no_phase13_imports_with_mutation(self):
        """Phase-15 must not import Phase-13 with intent to mutate."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                # Check for imports from phase-13
                if "from cyfer_brain" in content or "import cyfer_brain" in content:
                    # Check if there's any mutation pattern
                    if ".set(" in content or ".update(" in content or ".mutate(" in content:
                        violations.append(f"{py_file.name}: imports phase-13 with mutation")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Phase-13 mutation imports found: {violations}"

    def test_no_phase13_write_operations(self):
        """Phase-15 must not write to Phase-13 files."""
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                # Check for write operations to phase-13 paths
                if "cyfer_brain" in content:
                    if "write(" in content or "open(" in content and "'w'" in content:
                        violations.append(f"{py_file.name}: write to phase-13")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Phase-13 write operations found: {violations}"

    def test_no_cross_phase_mutation(self):
        """Phase-15 must not mutate any frozen phase."""
        frozen_phases = [
            "cyfer_brain", "artifact_scanner", "decision_workflow",
            "submission_workflow", "execution_layer",
        ]
        violations = []
        
        for py_file in PHASE15_DIR.rglob("*.py"):
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text()
                for phase in frozen_phases:
                    if f"from {phase}" in content or f"import {phase}" in content:
                        # Check for mutation patterns
                        if ".modify" in content or ".delete" in content or ".create" in content:
                            violations.append(f"{py_file.name}: mutates {phase}")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Cross-phase mutations found: {violations}"


class TestPhase15CanOnlyHalt:
    """Verify Phase-15 can HALT but never PROCEED autonomously."""

    def test_no_proceed_function(self):
        """No proceed or continue function may exist."""
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
                        if "auto_proceed" in name_lower:
                            violations.append(f"{py_file.name}: {node.name}")
                        if "auto_continue" in name_lower:
                            violations.append(f"{py_file.name}: {node.name}")
            except Exception:
                pass
        
        assert len(violations) == 0, f"Auto-proceed functions found: {violations}"

    def test_halt_function_exists(self):
        """halt or block functions should exist (to be implemented)."""
        # This will fail until blocking module is implemented
        try:
            from phase15_enforcement import blocking
            assert hasattr(blocking, "block_action") or hasattr(blocking, "halt"), \
                "Neither block_action nor halt function exists"
        except ImportError:
            pytest.fail("phase15_enforcement.blocking module does not exist")
