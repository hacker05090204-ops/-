"""
Phase-15 Validation Tests

MANDATORY DECLARATION:
Phase-15 may ONLY implement enforcement, validation, logging, and blocking.
NO authority, verification, learning, autonomy, inference, ranking, scoring,
or decision-making is permitted.

These tests verify that validation functions EXIST and operate correctly.
Tests MUST FAIL initially (pytest-first methodology).
"""

import pytest

# Import the module that DOES NOT EXIST YET - tests will fail
try:
    from phase15_enforcement import validation
    HAS_VALIDATION = True
except ImportError:
    HAS_VALIDATION = False


class TestValidationExists:
    """Verify validation functions exist."""

    def test_validation_module_exists(self):
        """Validation module must exist."""
        assert HAS_VALIDATION, "phase15_enforcement.validation module does not exist"

    def test_validate_input_function_exists(self):
        """validate_input function must exist."""
        assert HAS_VALIDATION, "Module not imported"
        assert hasattr(validation, "validate_input"), "validate_input function missing"

    def test_validate_constraint_function_exists(self):
        """validate_constraint function must exist."""
        assert HAS_VALIDATION, "Module not imported"
        assert hasattr(validation, "validate_constraint"), "validate_constraint function missing"


class TestValidationBehavior:
    """Verify validation functions behave correctly."""

    @pytest.mark.skipif(not HAS_VALIDATION, reason="Module not available")
    def test_validate_input_requires_schema(self):
        """validate_input must require explicit schema parameter."""
        with pytest.raises(TypeError):
            validation.validate_input(data={"key": "value"})  # Missing schema

    @pytest.mark.skipif(not HAS_VALIDATION, reason="Module not available")
    def test_validate_input_rejects_none_data(self):
        """validate_input must reject None data."""
        with pytest.raises(ValueError):
            validation.validate_input(data=None, schema={})

    @pytest.mark.skipif(not HAS_VALIDATION, reason="Module not available")
    def test_validate_constraint_requires_constraint_def(self):
        """validate_constraint must require constraint definition."""
        with pytest.raises(TypeError):
            validation.validate_constraint()


class TestValidationDoesNotInfer:
    """Verify validation does NOT infer correctness."""

    @pytest.mark.skipif(not HAS_VALIDATION, reason="Module not available")
    def test_validate_input_no_inference(self):
        """validate_input must NOT infer missing fields."""
        result = validation.validate_input(data={"a": 1}, schema={"a": int, "b": int})
        assert result["valid"] is False, "Must not infer missing 'b'"

    @pytest.mark.skipif(not HAS_VALIDATION, reason="Module not available")
    def test_no_auto_validate_method(self):
        """No auto_validate method may exist."""
        assert not hasattr(validation, "auto_validate"), "auto_validate is FORBIDDEN"
        assert not hasattr(validation, "smart_validate"), "smart_validate is FORBIDDEN"
