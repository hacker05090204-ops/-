"""
Phase-15 Enforcement Tests

Tests that Phase-15 code ONLY enforces pre-defined rules.
All tests must FAIL initially until implementation exists.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

import pytest


class TestEnforcementOnly:
    """Tests that enforcement functions exist and work correctly."""

    def test_rule_enforcer_exists(self) -> None:
        """Test that rule enforcer module exists."""
        try:
            from phase15_governance import enforcer
            assert hasattr(enforcer, "enforce_rule")
        except ImportError:
            pytest.fail("enforcer module does not exist - implementation required")

    def test_enforce_rule_requires_explicit_rule(self) -> None:
        """Test that enforce_rule requires an explicit rule definition."""
        try:
            from phase15_governance.enforcer import enforce_rule
            # Must raise if no rule provided
            with pytest.raises(ValueError):
                enforce_rule(rule=None, context={})
        except ImportError:
            pytest.fail("enforce_rule function does not exist")

    def test_enforce_rule_blocks_on_violation(self) -> None:
        """Test that enforce_rule blocks when rule is violated."""
        try:
            from phase15_governance.enforcer import enforce_rule
            from phase15_governance.errors import GovernanceBlockedError
            
            rule = {"type": "block_write", "target": "phase13"}
            context = {"action": "write", "target": "phase13", "human_initiated": True}
            
            with pytest.raises(GovernanceBlockedError):
                enforce_rule(rule=rule, context=context)
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_enforce_rule_logs_before_blocking(self) -> None:
        """Test that enforcement logs before blocking."""
        try:
            from phase15_governance.enforcer import enforce_rule
            from phase15_governance.audit import get_last_entry
            from phase15_governance.errors import GovernanceBlockedError
            
            rule = {"type": "block_write", "target": "phase13"}
            context = {"action": "write", "target": "phase13", "human_initiated": True}
            
            try:
                enforce_rule(rule=rule, context=context)
            except GovernanceBlockedError:
                pass
            
            last_entry = get_last_entry()
            assert last_entry is not None
            assert last_entry["event_type"] == "enforcement_block"
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_enforcement_does_not_decide(self) -> None:
        """Test that enforcement does not make decisions."""
        try:
            from phase15_governance import enforcer
            # Enforcement module must NOT have decision functions
            assert not hasattr(enforcer, "decide")
            assert not hasattr(enforcer, "recommend")
            assert not hasattr(enforcer, "suggest")
            assert not hasattr(enforcer, "choose")
            assert not hasattr(enforcer, "select")
        except ImportError:
            pytest.fail("enforcer module does not exist")

    def test_enforcement_requires_human_initiation(self) -> None:
        """Test that enforcement requires human initiation flag."""
        try:
            from phase15_governance.enforcer import enforce_rule
            
            rule = {"type": "allow", "target": "test"}
            context = {"action": "read", "human_initiated": False}
            
            # Must raise if not human initiated
            with pytest.raises(ValueError, match="human_initiated"):
                enforce_rule(rule=rule, context=context)
        except ImportError:
            pytest.fail("Implementation does not exist")


class TestEnforcementConstraints:
    """Tests that enforcement respects governance constraints."""

    def test_no_auto_execute_in_enforcer(self) -> None:
        """Test that enforcer has no auto-execute capability."""
        try:
            from phase15_governance import enforcer
            import inspect
            source = inspect.getsource(enforcer)
            
            forbidden = ["auto_execute", "autoexecute", "auto_run", "autorun"]
            for word in forbidden:
                assert word not in source.lower(), f"Forbidden: {word}"
        except ImportError:
            pytest.fail("enforcer module does not exist")

    def test_no_background_jobs_in_enforcer(self) -> None:
        """Test that enforcer has no background job capability."""
        try:
            from phase15_governance import enforcer
            import inspect
            source = inspect.getsource(enforcer)
            
            forbidden = ["background", "scheduler", "cron", "periodic", "daemon"]
            for word in forbidden:
                assert word not in source.lower(), f"Forbidden: {word}"
        except ImportError:
            pytest.fail("enforcer module does not exist")
