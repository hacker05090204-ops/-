"""
Phase-15 Phase-13 Read-Only Tests

Tests that Phase-13 cannot be mutated by Phase-15.
All tests must FAIL initially until implementation exists.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

import pytest


class TestPhase13ReadOnly:
    """Tests that Phase-13 is read-only."""

    def test_phase13_guard_exists(self) -> None:
        """Test that Phase-13 guard module exists."""
        try:
            from phase15_governance import phase13_guard
            assert hasattr(phase13_guard, "check_phase13_access")
        except ImportError:
            pytest.fail("phase13_guard module does not exist - implementation required")

    def test_phase13_write_blocked(self) -> None:
        """Test that Phase-13 write is blocked."""
        try:
            from phase15_governance.phase13_guard import check_phase13_access
            from phase15_governance.errors import GovernanceBlockedError
            
            with pytest.raises(GovernanceBlockedError):
                check_phase13_access(action="write", target="phase13")
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_phase13_delete_blocked(self) -> None:
        """Test that Phase-13 delete is blocked."""
        try:
            from phase15_governance.phase13_guard import check_phase13_access
            from phase15_governance.errors import GovernanceBlockedError
            
            with pytest.raises(GovernanceBlockedError):
                check_phase13_access(action="delete", target="phase13")
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_phase13_update_blocked(self) -> None:
        """Test that Phase-13 update is blocked."""
        try:
            from phase15_governance.phase13_guard import check_phase13_access
            from phase15_governance.errors import GovernanceBlockedError
            
            with pytest.raises(GovernanceBlockedError):
                check_phase13_access(action="update", target="phase13")
        except ImportError:
            pytest.fail("Implementation does not exist")


    def test_phase13_read_allowed(self) -> None:
        """Test that Phase-13 read is allowed."""
        try:
            from phase15_governance.phase13_guard import check_phase13_access
            
            # Read should not raise
            result = check_phase13_access(action="read", target="phase13")
            assert result is True
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_phase13_observe_allowed(self) -> None:
        """Test that Phase-13 observe is allowed."""
        try:
            from phase15_governance.phase13_guard import check_phase13_access
            
            # Observe should not raise
            result = check_phase13_access(action="observe", target="phase13")
            assert result is True
        except ImportError:
            pytest.fail("Implementation does not exist")


class TestPhase13InteractionLogging:
    """Tests that Phase-13 interactions are logged."""

    def test_phase13_read_logged(self) -> None:
        """Test that Phase-13 read is logged."""
        try:
            from phase15_governance.phase13_guard import check_phase13_access
            from phase15_governance.audit import get_last_entry
            
            check_phase13_access(action="read", target="phase13")
            
            last_entry = get_last_entry()
            assert last_entry is not None
            assert last_entry["event_type"] == "phase13_interaction"
            assert last_entry["data"]["action"] == "read"
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_phase13_blocked_write_logged(self) -> None:
        """Test that blocked Phase-13 write is logged."""
        try:
            from phase15_governance.phase13_guard import check_phase13_access
            from phase15_governance.audit import get_last_entry
            from phase15_governance.errors import GovernanceBlockedError
            
            try:
                check_phase13_access(action="write", target="phase13")
            except GovernanceBlockedError:
                pass
            
            last_entry = get_last_entry()
            assert last_entry is not None
            assert last_entry["event_type"] == "phase13_write_blocked"
        except ImportError:
            pytest.fail("Implementation does not exist")


class TestPhase13Immutability:
    """Tests that Phase-13 immutability is enforced."""

    def test_no_phase13_mutation_functions(self) -> None:
        """Test that no Phase-13 mutation functions exist."""
        try:
            from phase15_governance import phase13_guard
            
            assert not hasattr(phase13_guard, "write_to_phase13")
            assert not hasattr(phase13_guard, "update_phase13")
            assert not hasattr(phase13_guard, "delete_from_phase13")
            assert not hasattr(phase13_guard, "modify_phase13")
        except ImportError:
            pytest.fail("phase13_guard module does not exist")

    def test_phase13_guard_is_enforcement_only(self) -> None:
        """Test that Phase-13 guard only enforces, does not modify."""
        try:
            from phase15_governance import phase13_guard
            import inspect
            source = inspect.getsource(phase13_guard)
            
            # Should not have write/modify operations
            forbidden = ["open(", "write(", "truncate(", "unlink("]
            for word in forbidden:
                assert word not in source, f"Forbidden operation: {word}"
        except ImportError:
            pytest.fail("phase13_guard module does not exist")

    def test_indirect_phase13_mutation_blocked(self) -> None:
        """Test that indirect Phase-13 mutation is blocked."""
        try:
            from phase15_governance.phase13_guard import check_phase13_access
            from phase15_governance.errors import GovernanceBlockedError
            
            # Indirect mutation attempts should be blocked
            with pytest.raises(GovernanceBlockedError):
                check_phase13_access(action="append", target="phase13")
            
            with pytest.raises(GovernanceBlockedError):
                check_phase13_access(action="truncate", target="phase13")
            
            with pytest.raises(GovernanceBlockedError):
                check_phase13_access(action="overwrite", target="phase13")
        except ImportError:
            pytest.fail("Implementation does not exist")
