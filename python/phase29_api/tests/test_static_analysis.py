"""
Phase-29 Static Analysis Tests

PYTEST-FIRST: These tests MUST be written BEFORE implementation.

GOVERNANCE:
- No automation patterns (auto_*)
- No scoring/ranking functions
- No AI/inference logic
- No modification of frozen phases
"""

import pytest
import ast
from pathlib import Path


class TestNoAutomationPatterns:
    """Test that no automation patterns exist."""

    def _get_phase29_source_files(self) -> list[Path]:
        """Get all Python source files in phase29_api."""
        phase29_dir = Path(__file__).parent.parent
        return [
            f for f in phase29_dir.glob("*.py")
            if not f.name.startswith("test_")
        ]

    def test_no_auto_prefix_functions(self) -> None:
        """MUST NOT have functions starting with 'auto_'."""
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    assert not node.name.startswith("auto_"), (
                        f"GOVERNANCE VIOLATION: auto_ function '{node.name}' in {source_file.name}"
                    )

    def test_no_autorun_patterns(self) -> None:
        """MUST NOT have autorun patterns."""
        forbidden_patterns = [
            "autorun",
            "auto_run",
            "auto_start",
            "autostart",
            "auto_execute",
            "autoexecute",
            "auto_navigate",
            "autonavigate",
        ]
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text().lower()
            for pattern in forbidden_patterns:
                assert pattern not in content, (
                    f"GOVERNANCE VIOLATION: '{pattern}' in {source_file.name}"
                )


class TestNoScoringPatterns:
    """Test that no scoring/ranking patterns exist."""

    def _get_phase29_source_files(self) -> list[Path]:
        """Get all Python source files in phase29_api."""
        phase29_dir = Path(__file__).parent.parent
        return [
            f for f in phase29_dir.glob("*.py")
            if not f.name.startswith("test_")
        ]

    def test_no_scoring_functions(self) -> None:
        """MUST NOT have scoring functions."""
        scoring_patterns = [
            "calculate_score",
            "compute_score",
            "get_score",
            "score_",
            "_score",
            "rank_",
            "_rank",
            "classify_",
            "_classify",
            "prioritize",
            "severity_",
        ]
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name_lower = node.name.lower()
                    for pattern in scoring_patterns:
                        assert pattern not in name_lower, (
                            f"GOVERNANCE VIOLATION: scoring function '{node.name}' in {source_file.name}"
                        )


class TestNoInferencePatterns:
    """Test that no AI/inference patterns exist."""

    def _get_phase29_source_files(self) -> list[Path]:
        """Get all Python source files in phase29_api."""
        phase29_dir = Path(__file__).parent.parent
        return [
            f for f in phase29_dir.glob("*.py")
            if not f.name.startswith("test_")
        ]

    def test_no_inference_functions(self) -> None:
        """MUST NOT have inference functions."""
        inference_patterns = [
            "infer",
            "predict",
            "suggest",
            "recommend",
            "analyze",
            "interpret",
            "evaluate",
            "assess",
        ]
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name_lower = node.name.lower()
                    for pattern in inference_patterns:
                        # Allow "validate" but not "evaluate"
                        if pattern in name_lower and pattern != "validate":
                            pytest.fail(
                                f"GOVERNANCE VIOLATION: inference function '{node.name}' in {source_file.name}"
                            )

    def test_no_ai_library_imports(self) -> None:
        """MUST NOT import AI/ML libraries."""
        forbidden_imports = [
            "openai",
            "anthropic",
            "transformers",
            "torch",
            "tensorflow",
            "keras",
            "sklearn",
            "langchain",
            "llama",
        ]
        for source_file in self._get_phase29_source_files():
            if not source_file.exists():
                continue
            content = source_file.read_text()
            for imp in forbidden_imports:
                assert imp not in content, (
                    f"GOVERNANCE VIOLATION: {imp} import in {source_file.name}"
                )


class TestNoFrozenPhaseModification:
    """Test that frozen phases are not modified."""

    def test_no_imports_from_phase15_plus(self) -> None:
        """Phase-29 MUST NOT modify Phase-15+ modules."""
        # Phase-29 can READ from execution_layer but not MODIFY
        # This test ensures we don't import and modify frozen phase internals
        phase29_dir = Path(__file__).parent.parent
        for source_file in phase29_dir.glob("*.py"):
            if source_file.name.startswith("test_"):
                continue
            if not source_file.exists():
                continue
            content = source_file.read_text()
            # Check for dangerous modification patterns
            dangerous_patterns = [
                "phase15_governance.",
                "phase16_ui.",
                "phase17_runtime.",
                "phase18_distribution.",
                "phase19_submission.",
                "phase20_reflection.",
                "phase21_patch_covenant.",
                "phase22_chain_of_custody.",
                "phase23_regulatory_export.",
                "phase24_final_seal.",
                "phase25_governance_clarification.",
                "phase26_governed_reachability.",
                "phase27_external_assurance.",
                "phase28_external_disclosure.",
            ]
            for pattern in dangerous_patterns:
                # Allow reading types, but not modifying
                if pattern in content:
                    # Check if it's just a type import
                    lines = [l for l in content.split("\n") if pattern in l]
                    for line in lines:
                        if "import" not in line.lower():
                            pytest.fail(
                                f"GOVERNANCE VIOLATION: Potential modification of frozen phase in {source_file.name}"
                            )


class TestDisclaimerPresence:
    """Test that disclaimers are present in all modules."""

    def test_all_modules_have_governance_docstring(self) -> None:
        """All modules MUST have governance docstring."""
        phase29_dir = Path(__file__).parent.parent
        for source_file in phase29_dir.glob("*.py"):
            if source_file.name.startswith("test_"):
                continue
            if source_file.name == "__init__.py":
                continue
            if not source_file.exists():
                continue
            content = source_file.read_text()
            # Check for governance-related docstring
            assert '"""' in content, (
                f"Missing docstring in {source_file.name}"
            )
            # Should mention governance or human_initiated
            content_lower = content.lower()
            has_governance = "governance" in content_lower or "human_initiated" in content_lower
            assert has_governance, (
                f"Missing governance documentation in {source_file.name}"
            )
