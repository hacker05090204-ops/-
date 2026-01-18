"""
Phase-15 No Autonomy Tests

Tests that no autonomous/agent behavior exists in code.
All tests must FAIL initially until implementation exists.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

import pytest


FORBIDDEN_AUTONOMY_WORDS = [
    "autonomous", "autonomy", "auto_",
    "agent", "self_directed",
    "background", "daemon",
    "scheduler", "cron",
    "periodic", "interval",
    "batch", "bulk",
]


class TestNoAutonomy:
    """Tests that no autonomous behavior exists."""

    def test_no_autonomous_functions(self) -> None:
        """Test that no autonomous functions exist."""
        try:
            from phase15_governance import enforcer, validator, blocker, audit
            
            modules = [enforcer, validator, blocker, audit]
            for module in modules:
                for attr in dir(module):
                    attr_lower = attr.lower()
                    assert "auto" not in attr_lower, f"Auto function: {attr}"
                    assert "agent" not in attr_lower, f"Agent function: {attr}"
                    assert "daemon" not in attr_lower, f"Daemon function: {attr}"
        except ImportError:
            pytest.fail("Modules do not exist")

    def test_no_background_jobs(self) -> None:
        """Test that no background job capability exists."""
        try:
            from phase15_governance import enforcer
            import inspect
            source = inspect.getsource(enforcer)
            
            forbidden = ["threading", "multiprocessing", "asyncio.create_task"]
            for word in forbidden:
                assert word not in source, f"Forbidden: {word}"
        except ImportError:
            pytest.fail("enforcer module does not exist")


    def test_no_scheduler_capability(self) -> None:
        """Test that no scheduler capability exists."""
        try:
            from phase15_governance import enforcer, validator, blocker, audit
            import inspect
            import re
            
            modules = [enforcer, validator, blocker, audit]
            for module in modules:
                source = inspect.getsource(module)
                # Check for scheduler implementations, not blocking of schedules
                forbidden_patterns = [
                    r"\bcron\b", r"\bperiodic\b", r"\binterval\b",
                    r"sched\.", r"apscheduler", r"celery",
                ]
                for pattern in forbidden_patterns:
                    assert not re.search(pattern, source.lower()), f"Forbidden: {pattern}"
        except ImportError:
            pytest.fail("Modules do not exist")

    def test_all_actions_require_human_initiation(self) -> None:
        """Test that all actions require human initiation."""
        try:
            from phase15_governance.enforcer import enforce_rule
            
            rule = {"type": "allow", "target": "test"}
            context = {"action": "read"}  # Missing human_initiated
            
            with pytest.raises(ValueError, match="human_initiated"):
                enforce_rule(rule=rule, context=context)
        except ImportError:
            pytest.fail("Implementation does not exist")


class TestNoAgentBehavior:
    """Tests that no agent-style behavior exists."""

    def test_no_goal_directed_code(self) -> None:
        """Test that no goal-directed code exists."""
        try:
            from phase15_governance import enforcer
            import inspect
            source = inspect.getsource(enforcer)
            
            forbidden = ["goal", "objective", "target_state", "achieve"]
            for word in forbidden:
                assert word not in source.lower(), f"Forbidden: {word}"
        except ImportError:
            pytest.fail("enforcer module does not exist")

    def test_no_multi_step_automation(self) -> None:
        """Test that no multi-step automation exists."""
        try:
            from phase15_governance import enforcer
            import inspect
            source = inspect.getsource(enforcer)
            
            forbidden = ["step_sequence", "workflow_auto", "chain_execute"]
            for word in forbidden:
                assert word not in source.lower(), f"Forbidden: {word}"
        except ImportError:
            pytest.fail("enforcer module does not exist")

    def test_no_self_directed_exploration(self) -> None:
        """Test that no self-directed exploration exists."""
        try:
            from phase15_governance import enforcer, validator, blocker
            
            modules = [enforcer, validator, blocker]
            for module in modules:
                assert not hasattr(module, "explore")
                assert not hasattr(module, "discover")
                assert not hasattr(module, "search")
                assert not hasattr(module, "navigate")
        except ImportError:
            pytest.fail("Modules do not exist")
