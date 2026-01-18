"""
Phase-16 Headless Browser Tests (TASK-P16-G03)

Verify headless browser mode is not used.

GOVERNANCE CONSTRAINT:
No headless browser — all browser actions must be visible to human.
"""

import pytest
import ast
from pathlib import Path


class TestNoHeadlessBrowser:
    """Verify headless browser mode is not used."""
    
    HEADLESS_PATTERNS = [
        "headless: true",
        "headless=True",
        "headless=true",
        "--headless",
        "HEADLESS",
        "headless_mode",
        "run_headless",
    ]
    
    def test_no_headless_in_ui_modules(self):
        """UI modules must not enable headless mode."""
        ui_dir = Path(__file__).parent.parent
        
        # Only check for actual headless configuration, not docstring mentions
        headless_code_patterns = [
            "headless: true",
            "headless=True",
            "headless=true",
            "--headless",
            "headless_mode = True",
            "run_headless = True",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in headless_code_patterns:
                if pattern in source:
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line:
                            # Skip comments and docstrings
                            if line.strip().startswith('#'):
                                continue
                            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                                continue
                            # Skip if it's setting to False
                            if "= False" in line or "=False" in line:
                                continue
                            assert False, (
                                f"Forbidden headless pattern in {py_file.name} "
                                f"line {i+1}: {pattern}"
                            )
    
    def test_renderer_not_headless(self):
        """UIRenderer must not be headless."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Check for headless attribute
        assert not getattr(renderer, 'headless', False), (
            "UIRenderer must not be headless"
        )
        assert not getattr(renderer, 'is_headless', False), (
            "UIRenderer must not be headless"
        )
    
    def test_renderer_requires_visible_browser(self):
        """UIRenderer must require visible browser."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Should have visible browser requirement
        assert renderer.requires_visible_browser(), (
            "UIRenderer must require visible browser"
        )


class TestNoHeadlessImports:
    """Verify no headless browser imports."""
    
    HEADLESS_IMPORTS = {
        "puppeteer",
        "pyppeteer",
        "selenium.webdriver.chrome.options",
        "selenium.webdriver.firefox.options",
    }
    
    def test_no_headless_library_imports(self):
        """UI must not import headless browser libraries."""
        ui_dir = Path(__file__).parent.parent
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in self.HEADLESS_IMPORTS:
                            if alias.name.startswith(forbidden.split('.')[0]):
                                # Check if it's used for headless
                                if 'headless' in source.lower():
                                    assert False, (
                                        f"Potential headless import in {py_file.name}: "
                                        f"{alias.name}"
                                    )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for forbidden in self.HEADLESS_IMPORTS:
                            if node.module.startswith(forbidden):
                                assert False, (
                                    f"Forbidden headless import in {py_file.name}: "
                                    f"{node.module}"
                                )


class TestBrowserVisibility:
    """Verify browser actions are visible."""
    
    def test_all_actions_visible_in_viewport(self):
        """All browser actions must be visible in viewport."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Renderer should guarantee visibility
        assert renderer.actions_visible_in_viewport(), (
            "All browser actions must be visible in viewport"
        )
    
    def test_no_offscreen_actions(self):
        """No actions may occur offscreen."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Should not have offscreen action capability
        assert not hasattr(renderer, 'offscreen_action'), (
            "Renderer must not have offscreen_action capability"
        )
        assert not hasattr(renderer, 'hidden_action'), (
            "Renderer must not have hidden_action capability"
        )
    
    def test_no_minimized_browser(self):
        """Browser must not be minimized during actions."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Should not allow minimized state
        assert not getattr(renderer, 'allow_minimized', False), (
            "Renderer must not allow minimized browser"
        )


class TestNoScreenshotOnlyMode:
    """Verify UI is not screenshot-only (which could hide headless)."""
    
    def test_no_screenshot_only_mode(self):
        """UI must not operate in screenshot-only mode."""
        ui_dir = Path(__file__).parent.parent
        
        screenshot_patterns = [
            "screenshot_only",
            "capture_only",
            "render_to_image",
            "headless_screenshot",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in screenshot_patterns:
                if pattern in source:
                    assert False, (
                        f"Forbidden screenshot-only pattern in {py_file.name}: "
                        f"{pattern}"
                    )
