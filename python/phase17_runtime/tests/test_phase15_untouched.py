"""
Phase-17 Tests: Phase-15 Untouched

GOVERNANCE CONSTRAINT:
- Phase-15 logic MUST NOT be modified
- Phase-15 behavior MUST NOT change
- Runtime uses Phase-15 public interface only

Risk Mitigated: RISK-17-005 (Phase-15/16 Coupling)
"""

import pytest
import inspect


class TestPhase15Untouched:
    """Tests verifying Phase-15 is not modified."""

    def test_no_phase15_modification_methods(self) -> None:
        """Runtime MUST NOT have Phase-15 modification methods."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "modify_enforcer")
        assert not hasattr(launcher, "modify_validator")
        assert not hasattr(launcher, "modify_blocker")
        assert not hasattr(launcher, "patch_phase15")

    def test_no_phase15_internal_access(self) -> None:
        """Runtime MUST NOT access Phase-15 internals."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        # No internal access patterns
        assert "_enforcer" not in source
        assert "_validator" not in source
        assert "_blocker" not in source
        assert "phase15_governance._" not in source

    def test_phase15_enforcer_unchanged(self) -> None:
        """Phase-15 enforcer MUST be unchanged."""
        from phase15_governance.enforcer import enforce_rule
        
        # Verify enforcer still works (rule must be dict, context must have human_initiated)
        result = enforce_rule(
            rule={"type": "allow", "target": "test"},
            context={"human_initiated": True}
        )
        assert result is True

    def test_phase15_validator_unchanged(self) -> None:
        """Phase-15 validator MUST be unchanged."""
        from phase15_governance.validator import validate_input
        
        # Verify validator still works (with required constraint as dict)
        result = validate_input({"test": "data"}, constraint={"type": "test"})
        assert result is not None

    def test_phase15_blocker_unchanged(self) -> None:
        """Phase-15 blocker MUST be unchanged."""
        from phase15_governance.blocker import block_if_prohibited
        
        # Verify blocker still works
        result = block_if_prohibited("test_action")
        # Result may be None if action is not prohibited
        assert result is None or "blocked" in str(result)

    def test_phase15_cve_reference_unchanged(self) -> None:
        """Phase-15 CVE reference MUST be unchanged."""
        from phase15_governance.cve_reference import lookup_cve, MANDATORY_DISCLAIMER
        
        # Verify CVE reference still has disclaimer
        assert "reference" in MANDATORY_DISCLAIMER.lower()
        
        result = lookup_cve("CVE-2021-44228")
        assert result["is_reference_only"] is True

    def test_runtime_uses_phase15_public_interface(self) -> None:
        """Runtime MUST use Phase-15 public interface only."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert launcher.uses_phase15_public_interface is True

    def test_no_phase15_monkey_patching(self) -> None:
        """Runtime MUST NOT monkey-patch Phase-15."""
        from phase17_runtime import launcher
        
        source = inspect.getsource(launcher)
        
        assert "setattr(phase15" not in source
        assert "phase15_governance.__dict__" not in source

    def test_phase15_audit_unchanged(self) -> None:
        """Phase-15 audit MUST be unchanged."""
        from phase15_governance.audit import log_event
        
        # Verify audit still works
        log_event(
            event_type="test_event",
            data={"test": "data"},
            attribution="HUMAN",
        )

    def test_no_phase15_bypass(self) -> None:
        """Runtime MUST NOT bypass Phase-15 checks."""
        from phase17_runtime.launcher import WindowLauncher
        
        launcher = WindowLauncher()
        
        assert not hasattr(launcher, "bypass_enforcer")
        assert not hasattr(launcher, "skip_validation")
        assert not hasattr(launcher, "disable_blocking")
