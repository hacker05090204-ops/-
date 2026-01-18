"""
Phase-16 Navigation Tests (TASK-P16-T03)

Verify no automatic navigation exists.

GOVERNANCE CONSTRAINT:
All navigation requires explicit human click — no auto-navigation.
"""

import pytest
import ast
import inspect
from pathlib import Path


class TestNoAutoNavigation:
    """Verify no automatic navigation in UI."""
    
    FORBIDDEN_NAVIGATION_PATTERNS = [
        "auto_navigate",
        "autoNavigate",
        "programmatic_navigate",
        "navigate_to_next",
        "navigateToNext",
        "auto_redirect",
        "autoRedirect",
        "scheduled_navigation",
        "timer_navigate",
    ]
    
    def test_renderer_no_auto_navigation_methods(self):
        """UIRenderer must not have auto-navigation methods."""
        from phase16_ui.renderer import UIRenderer
        
        renderer_methods = {name for name in dir(UIRenderer) if not name.startswith('_')}
        
        for pattern in self.FORBIDDEN_NAVIGATION_PATTERNS:
            assert pattern not in renderer_methods, (
                f"UIRenderer has forbidden navigation method: {pattern}"
            )
    
    def test_navigation_requires_human_click(self):
        """All navigation must require human_initiated=True."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Navigation without human_initiated should raise
        with pytest.raises(Exception):
            renderer.navigate("https://example.com", human_initiated=False)
    
    def test_navigation_with_human_click_succeeds(self):
        """Navigation with human_initiated=True should succeed."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Should not raise
        result = renderer.navigate("https://example.com", human_initiated=True)
        assert result is not None
    
    def test_no_navigation_on_page_load(self):
        """No navigation should occur on page load."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Check that renderer doesn't auto-navigate on init
        assert not renderer.has_pending_navigation(), (
            "Renderer must not have pending navigation on init"
        )
    
    def test_no_navigation_suggestions(self):
        """Renderer must not provide navigation suggestions."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Check for suggestion methods
        forbidden_suggestion_methods = {
            "suggest_url",
            "recommend_page",
            "next_page",
            "suggested_navigation",
        }
        
        renderer_methods = {name for name in dir(renderer) if not name.startswith('_')}
        forbidden_found = renderer_methods & forbidden_suggestion_methods
        
        assert not forbidden_found, (
            f"Renderer has forbidden suggestion methods: {forbidden_found}"
        )


class TestNavigationStaticAnalysis:
    """Static analysis of navigation code."""
    
    def test_renderer_no_timer_navigation(self):
        """Renderer must not use timers for navigation."""
        renderer_file = Path(__file__).parent.parent / "renderer.py"
        
        if not renderer_file.exists():
            pytest.skip("renderer.py not yet implemented")
        
        source = renderer_file.read_text()
        
        forbidden_patterns = [
            "setTimeout",
            "setInterval",
            "threading.Timer",
            "asyncio.sleep",
            "time.sleep",
            "schedule",
        ]
        
        for pattern in forbidden_patterns:
            # Allow in comments but not in code
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if pattern in line and not line.strip().startswith('#'):
                    assert False, (
                        f"Forbidden timer pattern in renderer.py line {i+1}: {pattern}"
                    )
    
    def test_renderer_no_event_triggered_navigation(self):
        """Renderer must not navigate on non-click events."""
        renderer_file = Path(__file__).parent.parent / "renderer.py"
        
        if not renderer_file.exists():
            pytest.skip("renderer.py not yet implemented")
        
        source = renderer_file.read_text()
        
        # Navigation should only happen in click handlers
        forbidden_event_navigation = [
            "on_load.*navigate",
            "on_data.*navigate",
            "on_change.*navigate",
            "on_update.*navigate",
        ]
        
        import re
        for pattern in forbidden_event_navigation:
            matches = re.findall(pattern, source, re.IGNORECASE)
            assert not matches, (
                f"Forbidden event-triggered navigation: {pattern}"
            )


class TestNavigationControls:
    """Test navigation control buttons."""
    
    def test_back_button_requires_click(self):
        """Back button must require human click."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Back without human_initiated should raise
        with pytest.raises(Exception):
            renderer.go_back(human_initiated=False)
    
    def test_forward_button_requires_click(self):
        """Forward button must require human click."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Forward without human_initiated should raise
        with pytest.raises(Exception):
            renderer.go_forward(human_initiated=False)
    
    def test_refresh_button_requires_click(self):
        """Refresh button must require human click."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Refresh without human_initiated should raise
        with pytest.raises(Exception):
            renderer.refresh(human_initiated=False)
    
    def test_no_auto_refresh(self):
        """Renderer must not auto-refresh."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        assert not hasattr(renderer, 'auto_refresh'), (
            "Renderer must not have auto_refresh capability"
        )
        assert not hasattr(renderer, 'refresh_interval'), (
            "Renderer must not have refresh_interval"
        )
