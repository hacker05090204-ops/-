"""
Phase-17 Tests: No Hidden Network Calls

GOVERNANCE CONSTRAINT:
- All network calls MUST be human-triggered
- No background fetch
- No pre-fetch
- No heartbeat/ping
- No telemetry/analytics

Risk Mitigated: RISK-17-001 (Automation), RISK-17-006 (Packaging Abuse)
"""

import pytest
import inspect
import ast


class TestNoHiddenNetworkCalls:
    """Tests verifying no hidden network calls."""

    def test_no_requests_import_in_launcher(self) -> None:
        """Launcher MUST NOT import requests directly."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        tree = ast.parse(source)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # requests should not be imported directly
        assert "requests" not in imports

    def test_no_urllib_import_in_launcher(self) -> None:
        """Launcher MUST NOT import urllib directly."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        tree = ast.parse(source)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        assert "urllib" not in imports
        assert "urllib.request" not in imports

    def test_no_httpx_import(self) -> None:
        """Launcher MUST NOT import httpx."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "httpx" not in source

    def test_no_aiohttp_import(self) -> None:
        """Launcher MUST NOT import aiohttp."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "aiohttp" not in source

    def test_no_background_fetch_method(self) -> None:
        """Launcher MUST NOT have background fetch methods."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "background_fetch")
        assert not hasattr(launcher, "prefetch")
        assert not hasattr(launcher, "pre_fetch")
        assert not hasattr(launcher, "fetch_async")

    def test_no_heartbeat_method(self) -> None:
        """Launcher MUST NOT have heartbeat methods."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "heartbeat")
        assert not hasattr(launcher, "ping")
        assert not hasattr(launcher, "health_check")
        assert not hasattr(launcher, "keep_alive")

    def test_no_telemetry_method(self) -> None:
        """Launcher MUST NOT have telemetry methods."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "send_telemetry")
        assert not hasattr(launcher, "track_usage")
        assert not hasattr(launcher, "report_metrics")

    def test_no_analytics_method(self) -> None:
        """Launcher MUST NOT have analytics methods."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "send_analytics")
        assert not hasattr(launcher, "track_event")
        assert not hasattr(launcher, "log_analytics")

    def test_no_auto_update_check(self) -> None:
        """Launcher MUST NOT check for updates."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "check_update")
        assert not hasattr(launcher, "check_for_updates")
        assert not hasattr(launcher, "auto_update")
        assert not hasattr(launcher, "download_update")

    def test_network_calls_require_human(self) -> None:
        """Any network call MUST require human_initiated=True."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        # Launcher should not make network calls itself
        assert launcher.makes_network_calls is False
