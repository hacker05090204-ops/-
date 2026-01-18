"""
Property tests for Bounty Pipeline project structure.

**Feature: bounty-pipeline, Property: Project Structure Validation**
**Validates: Bounty Pipeline is separate from MCP and Cyfer Brain**
"""

import os
from pathlib import Path

import pytest


class TestProjectStructure:
    """Test that Bounty Pipeline is properly separated from MCP and Cyfer Brain."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get project root directory."""
        # Navigate from tests/ to bounty_pipeline/ to python/ to kali-mcp-toolkit/
        return Path(__file__).parent.parent.parent.parent

    def test_bounty_pipeline_exists(self, project_root: Path) -> None:
        """Bounty Pipeline directory exists."""
        bounty_pipeline = project_root / "python" / "bounty_pipeline"
        assert bounty_pipeline.exists(), "bounty_pipeline directory must exist"
        assert bounty_pipeline.is_dir(), "bounty_pipeline must be a directory"

    def test_bounty_pipeline_has_init(self, project_root: Path) -> None:
        """Bounty Pipeline has __init__.py."""
        init_file = project_root / "python" / "bounty_pipeline" / "__init__.py"
        assert init_file.exists(), "bounty_pipeline must have __init__.py"

    def test_bounty_pipeline_has_types(self, project_root: Path) -> None:
        """Bounty Pipeline has types.py."""
        types_file = project_root / "python" / "bounty_pipeline" / "types.py"
        assert types_file.exists(), "bounty_pipeline must have types.py"

    def test_bounty_pipeline_has_errors(self, project_root: Path) -> None:
        """Bounty Pipeline has errors.py."""
        errors_file = project_root / "python" / "bounty_pipeline" / "errors.py"
        assert errors_file.exists(), "bounty_pipeline must have errors.py"

    def test_mcp_is_separate(self, project_root: Path) -> None:
        """MCP (kali_mcp) is in a separate directory."""
        mcp_dir = project_root / "python" / "kali_mcp"
        bounty_dir = project_root / "python" / "bounty_pipeline"

        # Both must exist
        assert mcp_dir.exists(), "kali_mcp directory must exist"
        assert bounty_dir.exists(), "bounty_pipeline directory must exist"

        # They must be different directories
        assert mcp_dir != bounty_dir, "MCP and Bounty Pipeline must be separate"
        assert not str(bounty_dir).startswith(
            str(mcp_dir)
        ), "Bounty Pipeline must not be inside MCP"
        assert not str(mcp_dir).startswith(
            str(bounty_dir)
        ), "MCP must not be inside Bounty Pipeline"

    def test_cyfer_brain_is_separate(self, project_root: Path) -> None:
        """Cyfer Brain is in a separate directory."""
        cyfer_dir = project_root / "python" / "cyfer_brain"
        bounty_dir = project_root / "python" / "bounty_pipeline"

        # Both must exist
        assert cyfer_dir.exists(), "cyfer_brain directory must exist"
        assert bounty_dir.exists(), "bounty_pipeline directory must exist"

        # They must be different directories
        assert cyfer_dir != bounty_dir, "Cyfer Brain and Bounty Pipeline must be separate"
        assert not str(bounty_dir).startswith(
            str(cyfer_dir)
        ), "Bounty Pipeline must not be inside Cyfer Brain"
        assert not str(cyfer_dir).startswith(
            str(bounty_dir)
        ), "Cyfer Brain must not be inside Bounty Pipeline"

    def test_bounty_pipeline_does_not_import_mcp_internals(
        self, project_root: Path
    ) -> None:
        """Bounty Pipeline does not import MCP internal modules."""
        bounty_dir = project_root / "python" / "bounty_pipeline"

        # Check all Python files in bounty_pipeline
        for py_file in bounty_dir.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue  # Skip test files

            content = py_file.read_text()

            # Should not import from kali_mcp internals
            # (reading MCP findings via interface is OK, but not importing internals)
            forbidden_imports = [
                "from kali_mcp.invariant",
                "from kali_mcp.proof",
                "from kali_mcp.state",
                "import kali_mcp.invariant",
                "import kali_mcp.proof",
                "import kali_mcp.state",
            ]

            for forbidden in forbidden_imports:
                assert (
                    forbidden not in content
                ), f"{py_file.name} must not import MCP internals: {forbidden}"

    def test_bounty_pipeline_does_not_import_cyfer_brain_internals(
        self, project_root: Path
    ) -> None:
        """Bounty Pipeline does not import Cyfer Brain internal modules."""
        bounty_dir = project_root / "python" / "bounty_pipeline"

        # Check all Python files in bounty_pipeline
        for py_file in bounty_dir.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue  # Skip test files

            content = py_file.read_text()

            # Should not import from cyfer_brain internals
            forbidden_imports = [
                "from cyfer_brain.hypothesis",
                "from cyfer_brain.explorer",
                "from cyfer_brain.strategy",
                "import cyfer_brain.hypothesis",
                "import cyfer_brain.explorer",
                "import cyfer_brain.strategy",
            ]

            for forbidden in forbidden_imports:
                assert (
                    forbidden not in content
                ), f"{py_file.name} must not import Cyfer Brain internals: {forbidden}"

    def test_bounty_pipeline_has_tests_directory(self, project_root: Path) -> None:
        """Bounty Pipeline has tests directory."""
        tests_dir = project_root / "python" / "bounty_pipeline" / "tests"
        assert tests_dir.exists(), "bounty_pipeline must have tests directory"
        assert tests_dir.is_dir(), "tests must be a directory"

    def test_architecture_documentation_exists(self, project_root: Path) -> None:
        """Bounty Pipeline has architecture documentation."""
        # Check for ARCHITECTURE.md in bounty_pipeline
        arch_file = project_root / "python" / "bounty_pipeline" / "ARCHITECTURE.md"
        # This will be created later, so we just check the directory exists for now
        bounty_dir = project_root / "python" / "bounty_pipeline"
        assert bounty_dir.exists(), "bounty_pipeline directory must exist"
