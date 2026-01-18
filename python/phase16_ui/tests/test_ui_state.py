"""
Phase-16 UI State Tests (TASK-P16-T01)

Verify UI state contains no inference or derived values.

GOVERNANCE CONSTRAINT:
UI state MUST be declarative only — no inference or derivation.
"""

import pytest
import ast
import inspect
from pathlib import Path


class TestNoInferenceInUIState:
    """Verify UI state has no inference-based fields."""
    
    # Forbidden state field names that imply inference
    FORBIDDEN_STATE_FIELDS = {
        "is_important",
        "isImportant",
        "is_recommended",
        "isRecommended",
        "priority",
        "relevance",
        "confidence",
        "score",
        "rank",
        "severity",
        "next_action",
        "nextAction",
        "suggested_step",
        "suggestedStep",
        "computed_emphasis",
        "derived_priority",
        "inferred_relevance",
    }
    
    def test_ui_state_no_forbidden_fields(self):
        """UIState class must not have forbidden inference fields."""
        from phase16_ui.state import UIState
        
        # Get all attributes of UIState
        state_attrs = set(dir(UIState))
        
        # Check for forbidden fields
        forbidden_found = state_attrs & self.FORBIDDEN_STATE_FIELDS
        assert not forbidden_found, (
            f"UIState contains forbidden inference fields: {forbidden_found}"
        )
    
    def test_ui_state_instance_no_forbidden_fields(self):
        """UIState instances must not have forbidden inference fields."""
        from phase16_ui.state import UIState
        
        # Create instance
        state = UIState()
        
        # Get instance attributes
        instance_attrs = set(vars(state).keys()) if hasattr(state, '__dict__') else set()
        
        # Check for forbidden fields
        forbidden_found = instance_attrs & self.FORBIDDEN_STATE_FIELDS
        assert not forbidden_found, (
            f"UIState instance contains forbidden inference fields: {forbidden_found}"
        )
    
    def test_ui_state_no_derived_computation(self):
        """UIState must not compute derived values from data content."""
        from phase16_ui.state import UIState
        
        # Check that UIState has no methods that compute derived values
        forbidden_methods = {
            "compute_importance",
            "derive_priority",
            "infer_relevance",
            "calculate_score",
            "determine_severity",
            "suggest_action",
            "recommend_next",
        }
        
        state_methods = {name for name in dir(UIState) if callable(getattr(UIState, name, None))}
        forbidden_found = state_methods & forbidden_methods
        
        assert not forbidden_found, (
            f"UIState contains forbidden computation methods: {forbidden_found}"
        )
    
    def test_ui_state_declarative_only(self):
        """UIState must be declarative (data storage only)."""
        from phase16_ui.state import UIState
        
        state = UIState()
        
        # UIState should only store data, not compute
        # Check that setting data doesn't trigger computation
        if hasattr(state, 'set_data'):
            state.set_data("test_key", "test_value")
            # Should not have any derived fields after setting data
            instance_attrs = set(vars(state).keys()) if hasattr(state, '__dict__') else set()
            forbidden_found = instance_attrs & self.FORBIDDEN_STATE_FIELDS
            assert not forbidden_found
    
    def test_ui_state_no_content_analysis(self):
        """UIState must not analyze content to derive state."""
        from phase16_ui.state import UIState
        
        # Check source code for content analysis patterns
        source = inspect.getsource(UIState)
        
        forbidden_patterns = [
            "if content",
            "if data",
            "analyze(",
            "infer(",
            "compute(",
            "derive(",
            "calculate(",
            ".severity",
            ".priority",
            ".importance",
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source, (
                f"UIState source contains forbidden pattern: {pattern}"
            )


class TestUIStateStaticAnalysis:
    """Static analysis of UI state module."""
    
    def test_state_module_no_inference_imports(self):
        """State module must not import inference-related modules."""
        state_file = Path(__file__).parent.parent / "state.py"
        
        if not state_file.exists():
            pytest.skip("state.py not yet implemented")
        
        source = state_file.read_text()
        tree = ast.parse(source)
        
        forbidden_imports = {
            "sklearn",
            "tensorflow",
            "torch",
            "numpy",  # Could be used for scoring
            "scipy",
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_imports, (
                        f"Forbidden import in state.py: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for forbidden in forbidden_imports:
                        assert not node.module.startswith(forbidden), (
                            f"Forbidden import in state.py: {node.module}"
                        )
    
    def test_state_module_no_scoring_functions(self):
        """State module must not define scoring functions."""
        state_file = Path(__file__).parent.parent / "state.py"
        
        if not state_file.exists():
            pytest.skip("state.py not yet implemented")
        
        source = state_file.read_text()
        tree = ast.parse(source)
        
        forbidden_function_names = {
            "score",
            "rank",
            "classify",
            "prioritize",
            "compute_severity",
            "calculate_risk",
            "infer_importance",
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                assert node.name not in forbidden_function_names, (
                    f"Forbidden function in state.py: {node.name}"
                )
