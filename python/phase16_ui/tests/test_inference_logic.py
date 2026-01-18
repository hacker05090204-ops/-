"""
Phase-16 Inference Logic Tests (TASK-P16-G01)

Static analysis to verify no inference logic in UI.

GOVERNANCE CONSTRAINT:
UI must not compute, infer, or derive values from data content.
"""

import pytest
import ast
from pathlib import Path


class TestNoInferenceLogic:
    """Verify no inference logic exists in UI code."""
    
    FORBIDDEN_FUNCTION_NAMES = {
        "compute_importance",
        "derive_priority",
        "infer_relevance",
        "calculate_score",
        "determine_severity",
        "analyze_content",
        "classify_finding",
        "rank_findings",
        "prioritize",
        "score_vulnerability",
        "assess_risk",
        "evaluate_severity",
    }
    
    FORBIDDEN_VARIABLE_NAMES = {
        "importance",
        "priority",
        "relevance",
        "score",
        "severity",
        "confidence",
        "risk_level",
        "threat_level",
        "criticality",
    }
    
    def test_no_inference_functions_in_ui(self):
        """UI modules must not have inference functions."""
        ui_dir = Path(__file__).parent.parent
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name in self.FORBIDDEN_FUNCTION_NAMES:
                        assert False, (
                            f"Forbidden inference function in {py_file.name}: "
                            f"{node.name}"
                        )
    
    def test_no_inference_variables_in_ui(self):
        """UI modules must not have inference-related variables."""
        ui_dir = Path(__file__).parent.parent
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id in self.FORBIDDEN_VARIABLE_NAMES:
                                assert False, (
                                    f"Forbidden inference variable in {py_file.name}: "
                                    f"{target.id}"
                                )
    
    def test_no_conditional_rendering_on_content(self):
        """UI must not conditionally render based on content analysis."""
        ui_dir = Path(__file__).parent.parent
        
        # Check for actual conditional rendering patterns in code
        forbidden_conditions = [
            "if severity",
            "if priority",
            "if important",
            "if critical",
            "if score",
            "if risk",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            if py_file.name == "strings.py":
                continue  # Skip strings file with docstrings
            
            source = py_file.read_text()
            lines = source.split('\n')
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # Skip comments and docstrings
                if line_stripped.startswith('#'):
                    continue
                if line_stripped.startswith('"""') or line_stripped.startswith("'''"):
                    continue
                if '"""' in line_stripped or "'''" in line_stripped:
                    continue
                
                for pattern in forbidden_conditions:
                    if pattern in line.lower():
                        assert False, (
                            f"Forbidden conditional rendering in {py_file.name} "
                            f"line {i+1}: {line_stripped}"
                        )
    
    def test_no_emphasis_based_on_data(self):
        """UI must not emphasize elements based on data content."""
        ui_dir = Path(__file__).parent.parent
        
        emphasis_patterns = [
            "highlight_if",
            "emphasize_when",
            "bold_if",
            "color_by",
            "style_by_severity",
            "format_by_priority",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in emphasis_patterns:
                if pattern in source:
                    assert False, (
                        f"Forbidden emphasis pattern in {py_file.name}: {pattern}"
                    )


class TestNoContentAnalysis:
    """Verify UI does not analyze content."""
    
    ANALYSIS_IMPORTS = {
        "sklearn",
        "tensorflow",
        "torch",
        "nltk",
        "spacy",
        "transformers",
        "openai",
        "anthropic",
    }
    
    def test_no_ml_imports(self):
        """UI must not import ML/AI libraries."""
        ui_dir = Path(__file__).parent.parent
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.ANALYSIS_IMPORTS:
                            assert False, (
                                f"Forbidden ML import in {py_file.name}: {alias.name}"
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for forbidden in self.ANALYSIS_IMPORTS:
                            if node.module.startswith(forbidden):
                                assert False, (
                                    f"Forbidden ML import in {py_file.name}: "
                                    f"{node.module}"
                                )
    
    def test_no_text_analysis_functions(self):
        """UI must not have text analysis functions."""
        ui_dir = Path(__file__).parent.parent
        
        analysis_functions = {
            "analyze_text",
            "parse_content",
            "extract_keywords",
            "classify_text",
            "sentiment_analysis",
            "entity_extraction",
            "summarize",
        }
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name in analysis_functions:
                        assert False, (
                            f"Forbidden analysis function in {py_file.name}: "
                            f"{node.name}"
                        )


class TestNoDerivedState:
    """Verify UI state is not derived from content."""
    
    def test_state_not_computed_from_data(self):
        """UI state must not be computed from data content."""
        from phase16_ui.state import UIState
        
        state = UIState()
        
        # Set some data
        if hasattr(state, 'set_data'):
            state.set_data("finding", {"title": "Test", "description": "Test desc"})
        
        # Check that no derived fields were created
        forbidden_derived = {
            "computed_priority",
            "derived_severity",
            "inferred_importance",
            "calculated_score",
        }
        
        instance_attrs = set(vars(state).keys()) if hasattr(state, '__dict__') else set()
        forbidden_found = instance_attrs & forbidden_derived
        
        assert not forbidden_found, (
            f"UIState has forbidden derived fields: {forbidden_found}"
        )
