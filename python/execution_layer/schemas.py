"""
Execution Layer Response Schema Validation

Pydantic models for strict validation of MCP and Pipeline API responses.

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from datetime import datetime
from typing import Optional, Any
import logging

from pydantic import BaseModel, Field, field_validator

from execution_layer.errors import ResponseValidationError


logger = logging.getLogger(__name__)


class MCPVerificationResponse(BaseModel):
    """Expected schema for MCP verification response."""
    verification_id: str = Field(..., min_length=1)
    finding_id: Optional[str] = None
    classification: str = Field(..., pattern="^(BUG|SIGNAL|NO_ISSUE|COVERAGE_GAP)$")
    invariant_violated: Optional[str] = None
    proof_hash: Optional[str] = None
    verified_at: str
    
    @field_validator("verified_at")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        """Validate verified_at is valid ISO 8601 datetime."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {v}") from e
        return v


class PipelineDraftResponse(BaseModel):
    """Expected schema for Pipeline draft response."""
    draft_id: str = Field(..., min_length=1)
    status: str = Field(default="draft")
    created_at: str
    
    @field_validator("created_at")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        """Validate created_at is valid ISO 8601 datetime."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {v}") from e
        return v


class ResponseValidator:
    """Validate API responses against expected schemas.
    
    OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
    """
    
    def validate_mcp_response(self, data: dict[str, Any]) -> MCPVerificationResponse:
        """Validate MCP response against schema.
        
        Raises:
            ResponseValidationError: If validation fails (HARD FAIL)
        """
        # Log warning for unexpected fields
        expected_fields = {
            "verification_id", "finding_id", "classification",
            "invariant_violated", "proof_hash", "verified_at"
        }
        unexpected = set(data.keys()) - expected_fields
        if unexpected:
            logger.warning(f"Unexpected fields in MCP response: {unexpected}")
        
        try:
            return MCPVerificationResponse.model_validate(data)
        except Exception as e:
            raise ResponseValidationError(
                f"MCP response validation failed: {e} — HARD FAIL"
            ) from e
    
    def validate_pipeline_response(self, data: dict[str, Any]) -> PipelineDraftResponse:
        """Validate Pipeline response against schema.
        
        Raises:
            ResponseValidationError: If validation fails (HARD FAIL)
        """
        # Log warning for unexpected fields
        expected_fields = {"draft_id", "status", "created_at"}
        unexpected = set(data.keys()) - expected_fields
        if unexpected:
            logger.warning(f"Unexpected fields in Pipeline response: {unexpected}")
        
        try:
            return PipelineDraftResponse.model_validate(data)
        except Exception as e:
            raise ResponseValidationError(
                f"Pipeline response validation failed: {e} — HARD FAIL"
            ) from e
