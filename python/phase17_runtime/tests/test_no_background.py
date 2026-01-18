"""
Phase-17 Tests: No Background Threads/Processes

GOVERNANCE CONSTRAINT:
- No threading
- No multiprocessing
- No subprocess spawn
- No background workers

Risk Mitigated: RISK-17-002 (Background Execution)
"""

import pytest
import ast
import inspect


class TestNoBackgroundExecution:
    """Tests verifying no background execution."""

    def test_no_threading_import(self) -> None:
        """Module MUST NOT import threading."""
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
        
        assert "threading" not in imports

    def test_no_multiprocessing_import(self) -> None:
        """Module MUST NOT import multiprocessing."""
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
        
        assert "multiprocessing" not in imports

    def test_no_subprocess_import(self) -> None:
        """Module MUST NOT import subprocess."""
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
        
        assert "subprocess" not in imports

    def test_no_thread_creation(self) -> None:
        """Source MUST NOT contain Thread creation."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "Thread(" not in source
        assert "threading.Thread" not in source

    def test_no_process_creation(self) -> None:
        """Source MUST NOT contain Process creation."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "Process(" not in source
        assert "multiprocessing.Process" not in source

    def test_no_daemon_flag(self) -> None:
        """Source MUST NOT contain daemon=True."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "daemon=True" not in source
        assert "daemon = True" not in source

    def test_lifecycle_no_background(self) -> None:
        """Lifecycle manager MUST NOT use background threads."""
        from phase17_runtime import lifecycle
        
        source = inspect.getsource(lifecycle)
        
        assert "Thread(" not in source
        assert "Process(" not in source
        assert "daemon" not in source.lower()

    def test_no_timer_usage(self) -> None:
        """Source MUST NOT use Timer."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "Timer(" not in source
        assert "threading.Timer" not in source

    def test_no_executor_usage(self) -> None:
        """Source MUST NOT use ThreadPoolExecutor or ProcessPoolExecutor."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "ThreadPoolExecutor" not in source
        assert "ProcessPoolExecutor" not in source
        assert "concurrent.futures" not in source

    def test_launcher_has_no_background_methods(self) -> None:
        """Launcher MUST NOT have background-related methods."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "start_background")
        assert not hasattr(launcher, "run_async")
        assert not hasattr(launcher, "spawn_worker")
        assert not hasattr(launcher, "create_thread")
