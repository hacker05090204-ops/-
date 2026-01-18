"""
Phase-16 Background Operations Tests (TASK-P16-T04)

Verify no background workers, timers, or polling.

GOVERNANCE CONSTRAINT:
No background operations — all actions must be human-initiated and synchronous.
"""

import pytest
import ast
from pathlib import Path


class TestNoBackgroundOperations:
    """Verify no background operations in UI code."""
    
    FORBIDDEN_BACKGROUND_PATTERNS = [
        "Worker",
        "ServiceWorker",
        "WebWorker",
        "threading.Thread",
        "multiprocessing",
        "asyncio.create_task",
        "concurrent.futures",
        "BackgroundScheduler",
        "APScheduler",
    ]
    
    def test_no_workers_in_ui_modules(self):
        """UI modules must not use workers."""
        ui_dir = Path(__file__).parent.parent
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in self.FORBIDDEN_BACKGROUND_PATTERNS:
                # Check imports and usage
                if pattern in source:
                    # Allow in comments
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            assert False, (
                                f"Forbidden background pattern in {py_file.name} "
                                f"line {i+1}: {pattern}"
                            )
    
    def test_no_timers_for_actions(self):
        """UI must not use timers to trigger actions."""
        ui_dir = Path(__file__).parent.parent
        
        timer_patterns = [
            "setTimeout",
            "setInterval",
            "threading.Timer",
            "sched.scheduler",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in timer_patterns:
                if pattern in source:
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            assert False, (
                                f"Forbidden timer in {py_file.name} line {i+1}: {pattern}"
                            )
    
    def test_no_polling(self):
        """UI must not poll for data."""
        ui_dir = Path(__file__).parent.parent
        
        # Only check for actual polling function calls
        polling_patterns = [
            "poll(",
            "while True:",
            "check_for_updates(",
            "refresh_data(",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            if py_file.name == "__init__.py":
                continue  # Skip init files with docstrings
            
            source = py_file.read_text()
            
            for pattern in polling_patterns:
                if pattern in source:
                    # Check if it's in a comment
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            assert False, (
                                f"Potential polling pattern in {py_file.name} "
                                f"line {i+1}: {pattern}"
                            )
    
    def test_no_auto_refresh(self):
        """UI must not auto-refresh."""
        ui_dir = Path(__file__).parent.parent
        
        auto_refresh_patterns = [
            "auto_refresh",
            "autoRefresh",
            "refresh_interval",
            "refreshInterval",
            "periodic_refresh",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in auto_refresh_patterns:
                if pattern in source:
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            assert False, (
                                f"Forbidden auto-refresh in {py_file.name} "
                                f"line {i+1}: {pattern}"
                            )


class TestSynchronousOperations:
    """Verify all operations are synchronous and human-initiated."""
    
    def test_cve_fetch_synchronous(self):
        """CVE fetch must be synchronous."""
        from phase16_ui.cve_panel import CVEPanel
        
        panel = CVEPanel()
        
        # Should not have async fetch methods
        assert not hasattr(panel, 'async_fetch'), (
            "CVEPanel must not have async_fetch"
        )
        assert not hasattr(panel, 'fetch_in_background'), (
            "CVEPanel must not have fetch_in_background"
        )
    
    def test_renderer_synchronous(self):
        """Renderer operations must be synchronous."""
        from phase16_ui.renderer import UIRenderer
        
        renderer = UIRenderer()
        
        # Should not have async methods
        async_methods = [name for name in dir(renderer) 
                        if name.startswith('async_') or name.endswith('_async')]
        
        assert not async_methods, (
            f"Renderer has async methods: {async_methods}"
        )
    
    def test_no_scheduled_actions(self):
        """UI must not have scheduled actions."""
        ui_dir = Path(__file__).parent.parent
        
        schedule_patterns = [
            "schedule(",
            "scheduled_",
            "cron",
            "at_time",
            "run_at",
            "run_later",
            "delay(",
        ]
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            
            for pattern in schedule_patterns:
                if pattern in source:
                    lines = source.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            assert False, (
                                f"Forbidden scheduled action in {py_file.name} "
                                f"line {i+1}: {pattern}"
                            )


class TestNoAsyncImports:
    """Verify no async-related imports that could enable background ops."""
    
    def test_no_asyncio_imports(self):
        """UI modules must not import asyncio for background tasks."""
        ui_dir = Path(__file__).parent.parent
        
        for py_file in ui_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            source = py_file.read_text()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ('asyncio', 'aiohttp', 'aiofiles'):
                            assert False, (
                                f"Forbidden async import in {py_file.name}: {alias.name}"
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith(('asyncio', 'aio')):
                        assert False, (
                            f"Forbidden async import in {py_file.name}: {node.module}"
                        )
