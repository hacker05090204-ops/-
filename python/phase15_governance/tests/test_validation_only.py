"""
Phase-15 Validation Tests

Tests that Phase-15 code ONLY validates inputs against static constraints.
All tests must FAIL initially until implementation exists.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

import pytest


class TestValidationOnly:
    """Tests that validation functions exist and work correctly."""

    def test_validator_module_exists(self) -> None:
        """Test that validator module exists."""
        try:
            from phase15_governance import validator
            assert hasattr(validator, "validate_input")
        except ImportError:
            pytest.fail("validator module does not exist - implementation required")

    def test_validate_input_requires_constraint(self) -> None:
        """Test that validate_input requires an explicit constraint."""
        try:
            from phase15_governance.validator import validate_input
            # Must raise if no constraint provided
            with pytest.raises(ValueError):
                validate_input(value="test", constraint=None)
        except ImportError:
            pytest.fail("validate_input function does not exist")

    def test_validate_input_rejects_invalid(self) -> None:
        """Test that validate_input rejects invalid input."""
        try:
            from phase15_governance.validator import validate_input
            from phase15_governance.errors import ValidationError
            
            constraint = {"type": "string", "max_length": 10}
            
            with pytest.raises(ValidationError):
                validate_input(value="this is too long", constraint=constraint)
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_validate_input_accepts_valid(self) -> None:
        """Test that validate_input accepts valid input."""
        try:
            from phase15_governance.validator import validate_input
            
            constraint = {"type": "string", "max_length": 10}
            result = validate_input(value="short", constraint=constraint)
            assert result is True
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_validation_is_deterministic(self) -> None:
        """Test that validation produces same result for same input."""
        try:
            from phase15_governance.validator import validate_input
            
            constraint = {"type": "string", "max_length": 10}
            value = "test"
            
            result1 = validate_input(value=value, constraint=constraint)
            result2 = validate_input(value=value, constraint=constraint)
            result3 = validate_input(value=value, constraint=constraint)
            
            assert result1 == result2 == result3
        except ImportError:
            pytest.fail("Implementation does not exist")


class TestValidationConstraints:
    """Tests that validation respects governance constraints."""

    def test_no_inference_in_validator(self) -> None:
        """Test that validator has no inference capability."""
        try:
            from phase15_governance import validator
            import inspect
            source = inspect.getsource(validator)
            
            forbidden = ["infer", "predict", "estimate", "guess", "assume"]
            for word in forbidden:
                assert word not in source.lower(), f"Forbidden: {word}"
        except ImportError:
            pytest.fail("validator module does not exist")

    def test_no_learning_in_validator(self) -> None:
        """Test that validator has no learning capability."""
        try:
            from phase15_governance import validator
            import inspect
            import re
            source = inspect.getsource(validator)
            
            # Use word boundaries to avoid false positives like "constraint"
            forbidden = [r"\blearn\b", r"\btrain\b", r"\boptimize\b", r"\badapt\b", r"\bimprove\b"]
            for pattern in forbidden:
                assert not re.search(pattern, source.lower()), f"Forbidden: {pattern}"
        except ImportError:
            pytest.fail("validator module does not exist")

    def test_validator_does_not_score(self) -> None:
        """Test that validator does not produce scores."""
        try:
            from phase15_governance import validator
            assert not hasattr(validator, "score")
            assert not hasattr(validator, "rank")
            assert not hasattr(validator, "rate")
            assert not hasattr(validator, "classify")
        except ImportError:
            pytest.fail("validator module does not exist")

    def test_validator_does_not_decide(self) -> None:
        """Test that validator does not make decisions."""
        try:
            from phase15_governance import validator
            assert not hasattr(validator, "decide")
            assert not hasattr(validator, "recommend")
            assert not hasattr(validator, "suggest")
        except ImportError:
            pytest.fail("validator module does not exist")

    def test_validation_uses_static_constraints_only(self) -> None:
        """Test that validation only uses static constraints."""
        try:
            from phase15_governance.validator import validate_input
            
            # Dynamic constraint (function) should be rejected
            dynamic_constraint = lambda x: len(x) < 10
            
            with pytest.raises(ValueError, match="static"):
                validate_input(value="test", constraint=dynamic_constraint)
        except ImportError:
            pytest.fail("Implementation does not exist")

