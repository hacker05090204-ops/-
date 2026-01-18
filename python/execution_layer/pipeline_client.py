"""
Execution Layer Bounty Pipeline Client

REAL HTTP client for Phase-3 Bounty Pipeline. NO SIMULATION.
All requests call the actual Bounty Pipeline API.

CONSTRAINT: DRAFT-ONLY. No submission allowed.

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any, TYPE_CHECKING
from urllib.parse import urlparse
import json
import time

import httpx

from execution_layer.types import (
    EvidenceBundle,
    MCPVerificationResult,
)
from execution_layer.errors import (
    BountyPipelineConnectionError,
    BountyPipelineError,
    ArchitecturalViolationError,
    ConfigurationError,
)

if TYPE_CHECKING:
    from execution_layer.request_logger import RequestLogger
    from execution_layer.schemas import ResponseValidator
    from execution_layer.retry import RetryExecutor


def _validate_https_url(url: str, client_name: str) -> None:
    """Validate URL is HTTPS.
    
    OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
    
    Raises:
        ConfigurationError: If URL is not HTTPS
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ConfigurationError(
            f"{client_name} requires HTTPS URL, got: {url} — "
            f"Non-HTTPS URLs are rejected for security."
        )


@dataclass
class BountyPipelineConfig:
    """Configuration for Bounty Pipeline client.
    
    MANDATORY: HTTPS only. Non-HTTPS URLs are rejected.
    """
    base_url: str
    timeout_seconds: float = 30.0
    verify_ssl: bool = True  # MANDATORY: True by default
    api_key: Optional[str] = None
    
    def __post_init__(self) -> None:
        _validate_https_url(self.base_url, "BountyPipelineClient")


@dataclass
class DraftReport:
    """Draft report created via Bounty Pipeline."""
    draft_id: str
    finding_id: str
    program_id: str
    status: str
    created_at: datetime
    evidence_bundle_id: str
    mcp_verification_id: str


class BountyPipelineClient:
    """Real HTTP client for Bounty Pipeline.
    
    MANDATORY: All requests are REAL HTTP calls. No simulation allowed.
    - Real HTTP POST to create draft
    - DRAFT-ONLY constraint enforced
    - HARD FAIL if Bounty Pipeline unreachable
    
    FORBIDDEN: Submission is NOT allowed. Only draft creation.
    """
    
    def __init__(
        self,
        config: BountyPipelineConfig,
        request_logger: Optional["RequestLogger"] = None,
        response_validator: Optional["ResponseValidator"] = None,
        retry_executor: Optional["RetryExecutor"] = None,
    ) -> None:
        self._config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._request_logger = request_logger
        self._response_validator = response_validator
        self._retry_executor = retry_executor
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self._config.api_key:
                headers["Authorization"] = f"Bearer {self._config.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self._config.base_url,
                timeout=self._config.timeout_seconds,
                verify=self._config.verify_ssl,
                headers=headers,
            )
        return self._client
    
    async def create_draft(
        self,
        finding_id: str,
        mcp_result: MCPVerificationResult,
        evidence_bundle: EvidenceBundle,
        program_id: str,
    ) -> DraftReport:
        """Create draft report via Bounty Pipeline (DRAFT ONLY).
        
        Args:
            finding_id: Unique finding identifier
            mcp_result: MCP verification result (must be BUG)
            evidence_bundle: Evidence bundle for the finding
            program_id: Bug bounty program identifier
        
        Returns:
            DraftReport with draft_id from Bounty Pipeline
        
        Raises:
            ArchitecturalViolationError: If MCP classification is not BUG
            BountyPipelineConnectionError: If Bounty Pipeline unreachable
            BountyPipelineError: If draft creation fails
            RetryExhaustedError: If all retry attempts fail (when retry_executor provided)
        """
        # Enforce BUG-only constraint
        if not mcp_result.is_bug:
            raise ArchitecturalViolationError(
                f"Cannot create draft for non-BUG classification "
                f"'{mcp_result.classification.value}' — "
                f"only MCP-confirmed BUG can be drafted"
            )
        
        client = await self._get_client()
        
        # Log request (pre-call, non-blocking) - NO SENSITIVE DATA
        request_id: Optional[str] = None
        start_time = time.monotonic()
        if self._request_logger is not None:
            request_id = self._request_logger.log_request(
                endpoint="/api/v1/drafts",
                method="POST",
                execution_id=evidence_bundle.execution_id,
            )
        
        # Prepare request payload
        payload = {
            "finding_id": finding_id,
            "program_id": program_id,
            "mcp_verification_id": mcp_result.verification_id,
            "classification": mcp_result.classification.value,
            "invariant_violated": mcp_result.invariant_violated,
            "proof_hash": mcp_result.proof_hash,
            "evidence_bundle_id": evidence_bundle.bundle_id,
            "evidence_bundle_hash": evidence_bundle.bundle_hash,
            "har_hash": evidence_bundle.har_file.content_hash if evidence_bundle.har_file else None,
            "screenshot_count": len(evidence_bundle.screenshots),
            "has_video": evidence_bundle.video is not None,
        }
        
        status_code: int = 0
        response_id: Optional[str] = None
        
        async def _do_http_call() -> DraftReport:
            """Inner HTTP call that can be retried."""
            nonlocal status_code, response_id
            
            response = await client.post(
                "/api/v1/drafts",
                json=payload,
            )
            status_code = response.status_code
            
            if response.status_code == 503:
                raise BountyPipelineConnectionError(
                    f"Bounty Pipeline unavailable (503) — HARD FAIL"
                )
            
            if response.status_code not in (200, 201):
                raise BountyPipelineError(
                    f"Draft creation failed with status {response.status_code}: "
                    f"{response.text}"
                )
            
            data = response.json()
            response_id = data.get("draft_id")
            
            # Validate response schema (lenient mode: warn on unexpected fields)
            # ResponseValidationError is HARD FAIL for missing required fields
            if self._response_validator is not None:
                self._response_validator.validate_pipeline_response(data)
            
            return DraftReport(
                draft_id=data["draft_id"],
                finding_id=finding_id,
                program_id=program_id,
                status=data.get("status", "draft"),
                created_at=datetime.fromisoformat(data["created_at"])
                    if "created_at" in data
                    else datetime.now(timezone.utc),
                evidence_bundle_id=evidence_bundle.bundle_id,
                mcp_verification_id=mcp_result.verification_id,
            )
        
        try:
            # Execute with retry if retry_executor is provided
            if self._retry_executor is not None:
                result = await self._retry_executor.execute_with_retry(
                    _do_http_call,
                    operation_name="BountyPipelineClient.create_draft",
                )
            else:
                result = await _do_http_call()
            
            return result
            
        except httpx.ConnectError as e:
            raise BountyPipelineConnectionError(
                f"Failed to connect to Bounty Pipeline at {self._config.base_url}: {e} — HARD FAIL"
            ) from e
        except httpx.TimeoutException as e:
            raise BountyPipelineConnectionError(
                f"Bounty Pipeline request timed out after {self._config.timeout_seconds}s — HARD FAIL"
            ) from e
        except httpx.HTTPError as e:
            raise BountyPipelineError(
                f"HTTP error during draft creation: {e}"
            ) from e
        except json.JSONDecodeError as e:
            raise BountyPipelineError(
                f"Invalid JSON response from Bounty Pipeline: {e}"
            ) from e
        finally:
            # Log response (post-call, non-blocking) - NO SENSITIVE DATA
            if self._request_logger is not None and request_id is not None:
                elapsed_ms = (time.monotonic() - start_time) * 1000
                self._request_logger.log_response(
                    request_id=request_id,
                    status_code=status_code,
                    response_time_ms=elapsed_ms,
                    response_id=response_id,
                )
    
    async def get_draft(self, draft_id: str) -> Optional[DraftReport]:
        """Get draft report by ID.
        
        Args:
            draft_id: Draft identifier
        
        Returns:
            DraftReport if found, None otherwise
        
        Raises:
            BountyPipelineError: If request fails
            RetryExhaustedError: If all retry attempts fail (when retry_executor provided)
        """
        client = await self._get_client()
        
        # Log request (pre-call, non-blocking) - NO SENSITIVE DATA
        request_id: Optional[str] = None
        start_time = time.monotonic()
        if self._request_logger is not None:
            request_id = self._request_logger.log_request(
                endpoint=f"/api/v1/drafts/{draft_id}",
                method="GET",
                execution_id=None,
            )
        
        status_code: int = 0
        response_id: Optional[str] = None
        
        async def _do_http_call() -> Optional[DraftReport]:
            """Inner HTTP call that can be retried."""
            nonlocal status_code, response_id
            
            response = await client.get(f"/api/v1/drafts/{draft_id}")
            status_code = response.status_code
            
            if response.status_code == 404:
                return None
            
            if response.status_code != 200:
                raise BountyPipelineError(
                    f"Failed to get draft with status {response.status_code}"
                )
            
            data = response.json()
            response_id = data.get("draft_id")
            
            # Validate response schema (lenient mode: warn on unexpected fields)
            # ResponseValidationError is HARD FAIL for missing required fields
            if self._response_validator is not None:
                self._response_validator.validate_pipeline_response(data)
            
            return DraftReport(
                draft_id=data["draft_id"],
                finding_id=data["finding_id"],
                program_id=data["program_id"],
                status=data.get("status", "draft"),
                created_at=datetime.fromisoformat(data["created_at"])
                    if "created_at" in data
                    else datetime.now(timezone.utc),
                evidence_bundle_id=data.get("evidence_bundle_id", ""),
                mcp_verification_id=data.get("mcp_verification_id", ""),
            )
        
        try:
            # Execute with retry if retry_executor is provided
            if self._retry_executor is not None:
                result = await self._retry_executor.execute_with_retry(
                    _do_http_call,
                    operation_name="BountyPipelineClient.get_draft",
                )
            else:
                result = await _do_http_call()
            
            return result
            
        except httpx.HTTPError as e:
            raise BountyPipelineError(f"HTTP error getting draft: {e}") from e
        finally:
            # Log response (post-call, non-blocking) - NO SENSITIVE DATA
            if self._request_logger is not None and request_id is not None:
                elapsed_ms = (time.monotonic() - start_time) * 1000
                self._request_logger.log_response(
                    request_id=request_id,
                    status_code=status_code,
                    response_time_ms=elapsed_ms,
                    response_id=response_id,
                )
    
    async def health_check(self) -> bool:
        """Check if Bounty Pipeline is reachable.
        
        Returns:
            True if Bounty Pipeline responds, False otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
