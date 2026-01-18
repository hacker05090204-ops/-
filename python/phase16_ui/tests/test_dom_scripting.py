"""
Phase-16 DOM Scripting Tests (TASK-P16-G02)

Verify no DOM manipulation or scripting.

GOVERNANCE CONSTRAINT:
UI must not manipulate DOM programmatically — all actions must be human-initiated.
"""

import pytest
import ast
from pathlib import Path


class TestNoDOMScripting:
    """Verify no DOM scripting in UI code."""
    
    FORBIDDEN_DOM_PATTERNS = [
        "document.querySelector",
        "document.getElementById",
        "document.getElementsBy",
        "document.createElement",
        "element.click()",
        "element.submit()",
        "element.focus()",
        ".innerHTML",
        ".outerHTML",
        "dispatchEvent",
        "createEvent",
        "fireEvent",
        "simulateClick",
        "programmatic_click",
    ]
    
    def test_no_dom_manipulation_in_ui(self):
        """UI modules must not have DOM manipulation."""
        ui_dir = Path(__file__).parent.parent
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in self.FORBIDDEN_DOM_PATTERNS:
                if pattern in source:
                    # Check if it's in a comment
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            assert False, (
                                f"Forbidden DOM pattern in {py_file.name} "
                                f"line {i+1}: {pattern}"
                            )
    
    def test_no_eval_in_ui(self):
        """UI must not use eval or exec."""
        ui_dir = Path(__file__).parent.parent
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ('eval', 'exec'):
                            assert False, (
                                f"Forbidden eval/exec in {py_file.name}"
                            )
    
    def test_no_dynamic_script_injection(self):
        """UI must not inject scripts dynamically."""
        ui_dir = Path(__file__).parent.parent
        
        # Simple string patterns (no regex)
        injection_patterns = [
            "<script",
            "javascript:",
            "eval(",
            "Function(",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in injection_patterns:
                if pattern in source:
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            assert False, (
                                f"Forbidden script injection in {py_file.name} "
                                f"line {i+1}: {pattern}"
                            )


class TestNoEventSimulation:
    """Verify UI does not simulate events."""
    
    def test_no_click_simulation(self):
        """UI must not simulate clicks."""
        ui_dir = Path(__file__).parent.parent
        
        simulation_patterns = [
            "simulate_click",
            "trigger_click",
            "fake_click",
            "programmatic_click",
            "auto_click",
            ".click()",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in simulation_patterns:
                if pattern in source:
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            assert False, (
                                f"Forbidden click simulation in {py_file.name} "
                                f"line {i+1}: {pattern}"
                            )
    
    def test_no_keyboard_simulation(self):
        """UI must not simulate keyboard events."""
        ui_dir = Path(__file__).parent.parent
        
        keyboard_patterns = [
            "simulate_key",
            "trigger_key",
            "fake_input",
            "programmatic_input",
            "auto_type",
            "sendKeys",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in keyboard_patterns:
                if pattern in source:
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            assert False, (
                                f"Forbidden keyboard simulation in {py_file.name} "
                                f"line {i+1}: {pattern}"
                            )


class TestNoHiddenActions:
    """Verify UI has no hidden actions."""
    
    def test_no_hidden_form_submission(self):
        """UI must not have hidden form submissions."""
        ui_dir = Path(__file__).parent.parent
        
        hidden_patterns = [
            "hidden_submit",
            "auto_submit",
            "silent_submit",
            "background_submit",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in hidden_patterns:
                if pattern in source:
                    assert False, (
                        f"Forbidden hidden submission in {py_file.name}: {pattern}"
                    )
    
    def test_no_invisible_elements(self):
        """UI must not use invisible elements for actions."""
        ui_dir = Path(__file__).parent.parent
        
        invisible_patterns = [
            "visibility: hidden",
            "display: none",
            "opacity: 0",
            "hidden=True",
            "invisible_button",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in invisible_patterns:
                if pattern in source:
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            # Allow in test context
                            if "test" not in line.lower():
                                assert False, (
                                    f"Forbidden invisible element in {py_file.name} "
                                    f"line {i+1}: {pattern}"
                                )
