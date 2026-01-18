"""
Pre-Integration Tests for Schema Validation (Integration Track #2)

PHASE-4.1 TEST-ONLY AUTHORIZATION
Status: AUTHORIZED
Date: 2026-01-02

These tests validate the ResponseValidator standalone component BEFORE integration.
NO WIRING. NO PRODUCTION CODE CHANGES.

Tests Required (per tasks.md):
- 8.1: Property test - Valid responses pass validation
- 8.2: Property test - Invalid responses raise ResponseValidationError
- 8.3: Property test - Unexpected fields logged not rejected (lenient mode)
- 8.4: Integration test - Existing API contracts preserved
- 8.5: Integration test - Validation errors include actionable diagnostics

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import pytest
import logging
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings, assume
from typing import Optional, Any

from execution_layer.schemas import (
    ResponseValidator,
    MCPVerificationResponse,
    PipelineDraftResponse,
)
from execution_layer.errors import ResponseValidationError


# === Hypothesis Strategies ===

# Valid verification IDs
verification_ids = st.text(min_size=1, max_size=64, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_")

# Valid finding IDs (optional)
finding_ids = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=64, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_")
)

# Valid classifications
classifications = st.sampled_from(["BUG", "SIGNAL", "NO_ISSUE", "COVERAGE_GAP"])


# Invalid classifications
invalid_classifications = st.sampled_from([
    "bug", "Bug", "BUGS", "signal", "Signal", "INVALID", 
    "UNKNOWN", "ERROR", "", "null", "undefined"
])

# Valid invariant violated (optional)
invariant_violated = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=256, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_. ")
)

# Valid proof hash (optional)
proof_hashes = st.one_of(
    st.none(),
    st.text(min_size=32, max_size=64, alphabet="abcdef0123456789")
)

# Valid draft IDs
draft_ids = st.text(min_size=1, max_size=64, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_")

# Valid statuses
draft_statuses = st.sampled_from(["draft", "pending", "submitted", "approved", "rejected"])


@st.composite
def valid_iso_datetimes(draw):
    """Generate valid ISO 8601 datetime strings."""
    # Generate datetime within reasonable range
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    
    dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    return dt.isoformat()


@st.composite
def invalid_iso_datetimes(draw):
    """Generate invalid datetime strings."""
    return draw(st.sampled_from([
        "not-a-date",
        "2024-13-01T00:00:00Z",  # Invalid month
        "2024-01-32T00:00:00Z",  # Invalid day
        "2024-01-01T25:00:00Z",  # Invalid hour
        "01-01-2024T00:00:00Z",  # Wrong format
        "",
        "null",
        "undefined",
        "abc123",
        "2024/01/01T00:00:00Z",  # Wrong separator
    ]))


@st.composite
def valid_mcp_responses(draw):
    """Generate valid MCP verification responses."""
    return {
        "verification_id": draw(verification_ids),
        "finding_id": draw(finding_ids),
        "classification": draw(classifications),
        "invariant_violated": draw(invariant_violated),
        "proof_hash": draw(proof_hashes),
        "verified_at": draw(valid_iso_datetimes()),
    }


@st.composite
def valid_pipeline_responses(draw):
    """Generate valid Pipeline draft responses."""
    return {
        "draft_id": draw(draft_ids),
        "status": draw(draft_statuses),
        "created_at": draw(valid_iso_datetimes()),
    }


# Extra fields that might appear in API evolution
extra_fields = st.dictionaries(
    keys=st.sampled_from([
        "extra_field", "new_field", "metadata", "version", 
        "api_version", "debug_info", "trace_id", "request_id"
    ]),
    values=st.one_of(
        st.text(min_size=1, max_size=32),
        st.integers(),
        st.booleans(),
    ),
    min_size=1,
    max_size=3,
)


# === Property Tests ===

class TestValidResponsesPassValidation:
    """
    Property Test 8.1: Valid responses pass validation
    
    Requirement 2.2: Well-formed responses pass in all modes.
    """
    
    @given(response=valid_mcp_responses())
    @settings(max_examples=100, deadline=5000)
    def test_valid_mcp_response_passes(self, response):
        """**Feature: schema-validation, Property: Valid Responses Pass**
        
        Valid MCP responses must pass validation.
        """
        assume(response["verification_id"])  # Must be non-empty
        
        validator = ResponseValidator()
        result = validator.validate_mcp_response(response)
        
        assert isinstance(result, MCPVerificationResponse)
        assert result.verification_id == response["verification_id"]
        assert result.classification == response["classification"]
    
    @given(response=valid_pipeline_responses())
    @settings(max_examples=100, deadline=5000)
    def test_valid_pipeline_response_passes(self, response):
        """**Feature: schema-validation, Property: Valid Responses Pass**
        
        Valid Pipeline responses must pass validation.
        """
        assume(response["draft_id"])  # Must be non-empty
        
        validator = ResponseValidator()
        result = validator.validate_pipeline_response(response)
        
        assert isinstance(result, PipelineDraftResponse)
        assert result.draft_id == response["draft_id"]
        assert result.status == response["status"]
    
    @given(classification=classifications)
    @settings(max_examples=100, deadline=5000)
    def test_all_valid_classifications_accepted(self, classification):
        """**Feature: schema-validation, Property: Valid Responses Pass**
        
        All valid classification values must be accepted.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "classification": classification,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = validator.validate_mcp_response(response)
        assert result.classification == classification


class TestInvalidResponsesRaiseError:
    """
    Property Test 8.2: Invalid responses raise ResponseValidationError
    
    Requirement 2.5: Missing required fields cause rejection.
    """
    
    def test_missing_verification_id_raises(self):
        """**Feature: schema-validation, Property: Invalid Responses Rejected**
        
        Missing verification_id must raise ResponseValidationError.
        """
        validator = ResponseValidator()
        response = {
            # "verification_id" missing
            "classification": "BUG",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(ResponseValidationError) as exc_info:
            validator.validate_mcp_response(response)
        
        assert "verification_id" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()
    
    def test_missing_classification_raises(self):
        """**Feature: schema-validation, Property: Invalid Responses Rejected**
        
        Missing classification must raise ResponseValidationError.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            # "classification" missing
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(ResponseValidationError) as exc_info:
            validator.validate_mcp_response(response)
        
        assert "classification" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()
    
    def test_missing_verified_at_raises(self):
        """**Feature: schema-validation, Property: Invalid Responses Rejected**
        
        Missing verified_at must raise ResponseValidationError.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "classification": "BUG",
            # "verified_at" missing
        }
        
        with pytest.raises(ResponseValidationError) as exc_info:
            validator.validate_mcp_response(response)
        
        assert "verified_at" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()
    
    @given(classification=invalid_classifications)
    @settings(max_examples=100, deadline=5000)
    def test_invalid_classification_raises(self, classification):
        """**Feature: schema-validation, Property: Invalid Responses Rejected**
        
        Invalid classification values must raise ResponseValidationError.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "classification": classification,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(ResponseValidationError):
            validator.validate_mcp_response(response)
    
    @given(invalid_dt=invalid_iso_datetimes())
    @settings(max_examples=100, deadline=5000)
    def test_invalid_datetime_raises(self, invalid_dt):
        """**Feature: schema-validation, Property: Invalid Responses Rejected**
        
        Invalid datetime formats must raise ResponseValidationError.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "classification": "BUG",
            "verified_at": invalid_dt,
        }
        
        with pytest.raises(ResponseValidationError):
            validator.validate_mcp_response(response)
    
    def test_empty_verification_id_raises(self):
        """**Feature: schema-validation, Property: Invalid Responses Rejected**
        
        Empty verification_id must raise ResponseValidationError.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "",  # Empty string
            "classification": "BUG",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(ResponseValidationError):
            validator.validate_mcp_response(response)
    
    def test_missing_draft_id_raises(self):
        """**Feature: schema-validation, Property: Invalid Responses Rejected**
        
        Missing draft_id must raise ResponseValidationError.
        """
        validator = ResponseValidator()
        response = {
            # "draft_id" missing
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(ResponseValidationError) as exc_info:
            validator.validate_pipeline_response(response)
        
        assert "draft_id" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()
    
    def test_missing_created_at_raises(self):
        """**Feature: schema-validation, Property: Invalid Responses Rejected**
        
        Missing created_at must raise ResponseValidationError.
        """
        validator = ResponseValidator()
        response = {
            "draft_id": "draft-123",
            "status": "draft",
            # "created_at" missing
        }
        
        with pytest.raises(ResponseValidationError) as exc_info:
            validator.validate_pipeline_response(response)
        
        assert "created_at" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()


class TestUnexpectedFieldsLoggedNotRejected:
    """
    Property Test 8.3: Unexpected fields logged not rejected (lenient mode)
    
    Requirement 2.2, 2.3: Extra fields trigger warnings, not errors.
    """
    
    def test_mcp_response_with_extra_fields_passes(self, caplog):
        """**Feature: schema-validation, Property: Unexpected Fields Logged**
        
        MCP responses with extra fields must pass validation with warnings.
        """
        response = {
            "verification_id": "test-123",
            "classification": "BUG",
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "extra_field": "extra_value",
            "another_extra": 42,
        }
        
        validator = ResponseValidator()
        
        with caplog.at_level(logging.WARNING):
            result = validator.validate_mcp_response(response)
        
        # Validation should succeed
        assert isinstance(result, MCPVerificationResponse)
        assert result.verification_id == "test-123"
        
        # Warning should be logged for unexpected fields
        assert any("unexpected" in record.message.lower() for record in caplog.records)
    
    def test_pipeline_response_with_extra_fields_passes(self, caplog):
        """**Feature: schema-validation, Property: Unexpected Fields Logged**
        
        Pipeline responses with extra fields must pass validation with warnings.
        """
        response = {
            "draft_id": "draft-123",
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"key": "value"},
            "version": "1.0",
        }
        
        validator = ResponseValidator()
        
        with caplog.at_level(logging.WARNING):
            result = validator.validate_pipeline_response(response)
        
        # Validation should succeed
        assert isinstance(result, PipelineDraftResponse)
        assert result.draft_id == "draft-123"
        
        # Warning should be logged for unexpected fields
        assert any("unexpected" in record.message.lower() for record in caplog.records)
    
    def test_warning_contains_field_names(self, caplog):
        """**Feature: schema-validation, Property: Unexpected Fields Logged**
        
        Warning message must contain the unexpected field names.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "classification": "BUG",
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "unknown_field_xyz": "some_value",
            "another_extra": 42,
        }
        
        with caplog.at_level(logging.WARNING):
            result = validator.validate_mcp_response(response)
        
        assert isinstance(result, MCPVerificationResponse)
        
        # Check warning contains field names
        warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_messages) > 0
        combined_warnings = " ".join(warning_messages).lower()
        assert "unknown_field_xyz" in combined_warnings or "another_extra" in combined_warnings


# === Integration-Style Tests (No Wiring) ===

class TestExistingAPIContractsPreserved:
    """
    Integration Test 8.4: Existing API contracts preserved
    
    Requirement 2.6: Test against real MCP and Pipeline API response formats.
    """
    
    def test_real_mcp_bug_response_format(self):
        """**Feature: schema-validation, Integration: API Contracts**
        
        Real MCP BUG response format must be accepted.
        """
        validator = ResponseValidator()
        
        # Simulated real MCP response for BUG classification
        response = {
            "verification_id": "mcp-verify-abc123def456",
            "finding_id": "finding-2026-001",
            "classification": "BUG",
            "invariant_violated": "AUTH_BYPASS_DETECTED",
            "proof_hash": "sha256:a1b2c3d4e5f6789012345678901234567890abcdef",
            "verified_at": "2026-01-02T10:30:00+00:00",
        }
        
        result = validator.validate_mcp_response(response)
        
        assert result.verification_id == "mcp-verify-abc123def456"
        assert result.classification == "BUG"
        assert result.invariant_violated == "AUTH_BYPASS_DETECTED"
    
    def test_real_mcp_signal_response_format(self):
        """**Feature: schema-validation, Integration: API Contracts**
        
        Real MCP SIGNAL response format must be accepted.
        """
        validator = ResponseValidator()
        
        # Simulated real MCP response for SIGNAL classification
        response = {
            "verification_id": "mcp-verify-xyz789",
            "finding_id": "finding-2026-002",
            "classification": "SIGNAL",
            "invariant_violated": None,
            "proof_hash": None,
            "verified_at": "2026-01-02T11:00:00Z",
        }
        
        result = validator.validate_mcp_response(response)
        
        assert result.verification_id == "mcp-verify-xyz789"
        assert result.classification == "SIGNAL"
        assert result.invariant_violated is None
    
    def test_real_mcp_no_issue_response_format(self):
        """**Feature: schema-validation, Integration: API Contracts**
        
        Real MCP NO_ISSUE response format must be accepted.
        """
        validator = ResponseValidator()
        
        response = {
            "verification_id": "mcp-verify-noissue-001",
            "classification": "NO_ISSUE",
            "verified_at": "2026-01-02T12:00:00+00:00",
        }
        
        result = validator.validate_mcp_response(response)
        
        assert result.classification == "NO_ISSUE"
        assert result.finding_id is None  # Optional field
    
    def test_real_pipeline_draft_response_format(self):
        """**Feature: schema-validation, Integration: API Contracts**
        
        Real Pipeline draft response format must be accepted.
        """
        validator = ResponseValidator()
        
        # Simulated real Pipeline response
        response = {
            "draft_id": "draft-2026-001-abc123",
            "status": "draft",
            "created_at": "2026-01-02T10:35:00+00:00",
        }
        
        result = validator.validate_pipeline_response(response)
        
        assert result.draft_id == "draft-2026-001-abc123"
        assert result.status == "draft"
    
    def test_mcp_response_with_z_timezone(self):
        """**Feature: schema-validation, Integration: API Contracts**
        
        MCP responses with 'Z' timezone suffix must be accepted.
        """
        validator = ResponseValidator()
        
        response = {
            "verification_id": "test-z-timezone",
            "classification": "BUG",
            "verified_at": "2026-01-02T10:30:00Z",  # Z suffix
        }
        
        result = validator.validate_mcp_response(response)
        assert result.verification_id == "test-z-timezone"
    
    def test_mcp_response_with_offset_timezone(self):
        """**Feature: schema-validation, Integration: API Contracts**
        
        MCP responses with offset timezone must be accepted.
        """
        validator = ResponseValidator()
        
        response = {
            "verification_id": "test-offset-timezone",
            "classification": "SIGNAL",
            "verified_at": "2026-01-02T10:30:00+05:30",  # Offset timezone
        }
        
        result = validator.validate_mcp_response(response)
        assert result.verification_id == "test-offset-timezone"


class TestValidationErrorsActionable:
    """
    Integration Test 8.5: Validation errors include actionable diagnostics
    
    Requirement 2.5: Error messages help debugging.
    """
    
    def test_error_message_contains_field_name(self):
        """**Feature: schema-validation, Integration: Actionable Errors**
        
        Error messages must contain the problematic field name.
        """
        validator = ResponseValidator()
        response = {
            # Missing verification_id
            "classification": "BUG",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(ResponseValidationError) as exc_info:
            validator.validate_mcp_response(response)
        
        error_msg = str(exc_info.value).lower()
        # Should mention the missing field or validation failure
        assert "verification_id" in error_msg or "required" in error_msg or "validation" in error_msg
    
    def test_error_message_contains_invalid_value_context(self):
        """**Feature: schema-validation, Integration: Actionable Errors**
        
        Error messages must provide context about invalid values.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "classification": "INVALID_CLASSIFICATION",  # Invalid value
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(ResponseValidationError) as exc_info:
            validator.validate_mcp_response(response)
        
        error_msg = str(exc_info.value).lower()
        # Should mention classification or pattern mismatch
        assert "classification" in error_msg or "pattern" in error_msg or "validation" in error_msg
    
    def test_error_message_contains_datetime_context(self):
        """**Feature: schema-validation, Integration: Actionable Errors**
        
        Error messages for datetime issues must be helpful.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "classification": "BUG",
            "verified_at": "not-a-valid-datetime",
        }
        
        with pytest.raises(ResponseValidationError) as exc_info:
            validator.validate_mcp_response(response)
        
        error_msg = str(exc_info.value).lower()
        # Should mention datetime or format issue
        assert "datetime" in error_msg or "format" in error_msg or "verified_at" in error_msg or "validation" in error_msg
    
    def test_error_is_subclass_of_execution_layer_error(self):
        """**Feature: schema-validation, Integration: Actionable Errors**
        
        ResponseValidationError must be subclass of ExecutionLayerError.
        """
        from execution_layer.errors import ExecutionLayerError
        
        validator = ResponseValidator()
        response = {
            "classification": "BUG",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(ExecutionLayerError):
            validator.validate_mcp_response(response)
    
    def test_error_is_hard_stop(self):
        """**Feature: schema-validation, Integration: Actionable Errors**
        
        ResponseValidationError must be classified as HARD_STOP.
        """
        from execution_layer.errors import is_hard_stop, ResponseValidationError
        
        error = ResponseValidationError("Test validation error")
        assert is_hard_stop(error) is True


# === Backward Compatibility Tests ===

class TestBackwardCompatibility:
    """
    Backward Compatibility Tests
    
    These tests verify that the ResponseValidator interface is compatible
    with the planned integration into MCPClient and BountyPipelineClient.
    
    NO WIRING - just interface validation.
    """
    
    def test_validator_instantiation_no_args(self):
        """**Feature: schema-validation, Backward Compat: No Args**
        
        ResponseValidator must be instantiable without arguments.
        """
        validator = ResponseValidator()
        assert validator is not None
    
    def test_validate_mcp_response_returns_model(self):
        """**Feature: schema-validation, Backward Compat: Return Type**
        
        validate_mcp_response must return MCPVerificationResponse.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "classification": "BUG",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = validator.validate_mcp_response(response)
        
        assert isinstance(result, MCPVerificationResponse)
    
    def test_validate_pipeline_response_returns_model(self):
        """**Feature: schema-validation, Backward Compat: Return Type**
        
        validate_pipeline_response must return PipelineDraftResponse.
        """
        validator = ResponseValidator()
        response = {
            "draft_id": "draft-123",
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = validator.validate_pipeline_response(response)
        
        assert isinstance(result, PipelineDraftResponse)
    
    def test_model_fields_accessible(self):
        """**Feature: schema-validation, Backward Compat: Field Access**
        
        Validated model fields must be accessible.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "finding_id": "finding-456",
            "classification": "BUG",
            "invariant_violated": "AUTH_BYPASS",
            "proof_hash": "abc123",
            "verified_at": "2026-01-02T10:00:00Z",
        }
        
        result = validator.validate_mcp_response(response)
        
        # All fields must be accessible
        assert result.verification_id == "test-123"
        assert result.finding_id == "finding-456"
        assert result.classification == "BUG"
        assert result.invariant_violated == "AUTH_BYPASS"
        assert result.proof_hash == "abc123"
        assert result.verified_at == "2026-01-02T10:00:00Z"
    
    def test_optional_fields_default_to_none(self):
        """**Feature: schema-validation, Backward Compat: Optional Fields**
        
        Optional fields must default to None when not provided.
        """
        validator = ResponseValidator()
        response = {
            "verification_id": "test-123",
            "classification": "SIGNAL",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = validator.validate_mcp_response(response)
        
        assert result.finding_id is None
        assert result.invariant_violated is None
        assert result.proof_hash is None
    
    def test_pipeline_status_defaults(self):
        """**Feature: schema-validation, Backward Compat: Status Default**
        
        Pipeline status must default to 'draft' when not provided.
        """
        validator = ResponseValidator()
        response = {
            "draft_id": "draft-123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            # status not provided
        }
        
        result = validator.validate_pipeline_response(response)
        
        assert result.status == "draft"


# === Performance Tests ===

class TestValidationPerformance:
    """
    Performance Tests
    
    Validate that schema validation meets performance requirements.
    """
    
    def test_mcp_validation_under_5ms(self):
        """**Feature: schema-validation, Performance: Latency**
        
        MCP validation must complete in under 5ms.
        """
        import time
        
        validator = ResponseValidator()
        response = {
            "verification_id": "perf-test-123",
            "classification": "BUG",
            "invariant_violated": "TEST_INVARIANT",
            "proof_hash": "abc123def456",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Warm up
        validator.validate_mcp_response(response)
        
        # Measure
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            validator.validate_mcp_response(response)
        elapsed = time.perf_counter() - start
        
        avg_ms = (elapsed / iterations) * 1000
        assert avg_ms < 5.0, f"Average validation time {avg_ms:.2f}ms exceeds 5ms limit"
    
    def test_pipeline_validation_under_5ms(self):
        """**Feature: schema-validation, Performance: Latency**
        
        Pipeline validation must complete in under 5ms.
        """
        import time
        
        validator = ResponseValidator()
        response = {
            "draft_id": "perf-draft-123",
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Warm up
        validator.validate_pipeline_response(response)
        
        # Measure
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            validator.validate_pipeline_response(response)
        elapsed = time.perf_counter() - start
        
        avg_ms = (elapsed / iterations) * 1000
        assert avg_ms < 5.0, f"Average validation time {avg_ms:.2f}ms exceeds 5ms limit"
