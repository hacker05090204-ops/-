"""
Phase-17 Tests: Static Analysis

GOVERNANCE CONSTRAINT:
- No forbidden imports
- No forbidden patterns
- No automation code
- No intelligence code

Risk Mitigated: All RISK-17-* risks
"""

import pytest
import ast
import inspect


class TestStaticAnalysis:
    """Static analysis tests for governance compliance."""

    def test_no_scheduler_imports(self) -> None:
        """No scheduler imports allowed."""
        from phase17_runtime import launcher, lifecycle
        
        for module in [launcher, lifecycle]:
            source = inspect.getsource(module)
            tree = ast.parse(source)
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            assert "schedule" not in imports
            assert "apscheduler" not in imports
            assert "celery" not in imports

    def test_no_async_background_patterns(self) -> None:
        """No async background patterns allowed."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        # No asyncio background patterns
        assert "asyncio.create_task" not in source
        assert "asyncio.ensure_future" not in source
        assert "loop.run_in_executor" not in source

    def test_no_telemetry_patterns(self) -> None:
        """No telemetry patterns allowed."""
        from phase17_runtime import launcher, lifecycle
        
        for module in [launcher, lifecycle]:
            source = inspect.getsource(module)
            
            assert "telemetry" not in source.lower()
            assert "analytics" not in source.lower()
            assert "track_event" not in source
            assert "send_metrics" not in source

    def test_no_auto_patterns(self) -> None:
        """No auto-* patterns allowed (except in governance constraints/comments)."""
        from phase17_runtime import launcher, lifecycle
        
        for module in [launcher, lifecycle]:
            source = inspect.getsource(module)
            lines = source.split('\n')
            
            for line in lines:
                stripped = line.strip().lower()
                # Skip comments, docstrings, and governance constraint declarations
                if (stripped.startswith('#') or 
                    stripped.startswith('"') or 
                    stripped.startswith("'") or
                    'governance' in stripped or
                    'prohibited' in stripped or
                    'constraint' in stripped or
                    '= false' in stripped):
                    continue
                # Check actual code for forbidden patterns
                if 'auto_start' in stripped and '= true' in stripped:
                    assert False, f"Found auto_start=True: {line}"
                if 'auto_restart' in stripped and '= true' in stripped:
                    assert False, f"Found auto_restart=True: {line}"

    def test_no_daemon_patterns(self) -> None:
        """No daemon patterns allowed."""
        from phase17_runtime import launcher, lifecycle
        
        for module in [launcher, lifecycle]:
            source = inspect.getsource(module)
            
            assert "daemon=True" not in source
            assert "daemonize" not in source
            assert "run_as_daemon" not in source

    def test_no_inference_patterns(self) -> None:
        """No inference/intelligence patterns allowed."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "infer" not in source.lower() or "interface" in source.lower()
        assert "predict" not in source
        assert "classify" not in source
        assert "score" not in source
        assert "rank" not in source

    def test_no_verification_patterns(self) -> None:
        """No verification patterns allowed."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        # Runtime should not verify
        assert "verify_vulnerability" not in source
        assert "confirm_finding" not in source
        assert "validate_cve" not in source

    def test_no_hidden_functionality(self) -> None:
        """No hidden functionality patterns."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        # No hidden/secret patterns
        assert "hidden_" not in source
        assert "secret_" not in source
        assert "_backdoor" not in source
        assert "_bypass" not in source

    def test_module_docstrings_present(self) -> None:
        """All modules MUST have governance docstrings."""
        from phase17_runtime import launcher, lifecycle, signals
        
        for module in [launcher, lifecycle, signals]:
            assert module.__doc__ is not None
            assert "GOVERNANCE" in module.__doc__.upper()

    def test_no_eval_or_exec(self) -> None:
        """No eval() or exec() allowed."""
        from phase17_runtime import launcher, lifecycle
        
        for module in [launcher, lifecycle]:
            source = inspect.getsource(module)
            
            # No dynamic code execution
            assert "eval(" not in source
            assert "exec(" not in source
            assert "compile(" not in source
