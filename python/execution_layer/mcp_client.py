"""
Execution Layer MCP Client

REAL HTTP client for MCP server communication. NO SIMULATION.
All requests are sent to the actual MCP server endpoint.

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
    MCPClassification,
)
from execution_layer.errors import (
    MCPConnectionError,
    MCPVerificationError,
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
class MCPClientConfig:
    """Configuration for MCP client.
    
    MANDATORY: HTTPS only. Non-HTTPS URLs are rejected.
    """
    base_url: str
    timeout_seconds: float = 30.0
    verify_ssl: bool = True  # MANDATORY: True by default
    api_key: Optional[str] = None
    
    def __post_init__(self) -> None:
        _validate_https_url(self.base_url, "MCPClient")


class MCPClient:
    """Real HTTP client for MCP server.
    
    MANDATORY: All requests are REAL HTTP calls. No simulation allowed.
    - Real HTTP POST to MCP verification endpoint
    - Real response parsing
    - HARD FAIL if MCP unreachable
    """
    
    def __init__(
        self,
        config: MCPClientConfig,
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
    
    async def verify_evidence(
        self,
        evidence_bundle: EvidenceBundle,
    ) -> MCPVerificationResult:
        """Send evidence to MCP for verification.
        
        Args:
            evidence_bundle: Evidence bundle to verify
        
        Returns:
            MCPVerificationResult from MCP server
        
        Raises:
            MCPConnectionError: If MCP server is unreachable
            MCPVerificationError: If verification request fails
            RetryExhaustedError: If all retry attempts fail (when retry_executor provided)
        """
        client = await self._get_client()
        
        # Log request (pre-call, non-blocking) - NO SENSITIVE DATA
        request_id: Optional[str] = None
        start_time = time.monotonic()
        if self._request_logger is not None:
            request_id = self._request_logger.log_request(
                endpoint="/api/v1/verify",
                method="POST",
                execution_id=evidence_bundle.execution_id,
            )
        
        # Prepare request payload
        payload = {
            "bundle_id": evidence_bundle.bundle_id,
            "execution_id": evidence_bundle.execution_id,
            "har_hash": evidence_bundle.har_file.content_hash if evidence_bundle.har_file else None,
            "screenshot_hashes": [s.content_hash for s in evidence_bundle.screenshots],
            "video_hash": evidence_bundle.video.content_hash if evidence_bundle.video else None,
            "execution_trace": evidence_bundle.execution_trace,
            "bundle_hash": evidence_bundle.bundle_hash,
            "captured_at": evidence_bundle.captured_at.isoformat() if evidence_bundle.captured_at else None,
        }
        
        status_code: int = 0
        response_id: Optional[str] = None
        
        async def _do_http_call() -> MCPVerificationResult:
            """Inner HTTP call that can be retried."""
            nonlocal status_code, response_id
            
            response = await client.post(
                "/api/v1/verify",
                json=payload,
            )
            status_code = response.status_code
            
            if response.status_code == 503:
                raise MCPConnectionError(
                    f"MCP server unavailable (503) — HARD FAIL"
                )
            
            if response.status_code != 200:
                raise MCPVerificationError(
                    f"MCP verification failed with status {response.status_code}: "
                    f"{response.text}"
                )
            
            data = response.json()
            
            # Validate response schema (lenient mode: warn on unexpected fields)
            # ResponseValidationError is HARD FAIL for missing required fields
            if self._response_validator is not None:
                self._response_validator.validate_mcp_response(data)
            
            # Parse classification
            classification_str = data.get("classification", "SIGNAL")
            try:
                classification = MCPClassification(classification_str)
            except ValueError:
                classification = MCPClassification.SIGNAL
            
            response_id = data.get("verification_id")
            
            return MCPVerificationResult(
                verification_id=data["verification_id"],
                finding_id=data.get("finding_id", evidence_bundle.execution_id),
                classification=classification,
                invariant_violated=data.get("invariant_violated"),
                proof_hash=data.get("proof_hash"),
                verified_at=datetime.fromisoformat(data["verified_at"]) 
                    if "verified_at" in data 
                    else datetime.now(timezone.utc),
            )
        
        try:
            # Execute with retry if retry_executor is provided
            if self._retry_executor is not None:
                result = await self._retry_executor.execute_with_retry(
                    _do_http_call,
                    operation_name="MCPClient.verify_evidence",
                )
            else:
                result = await _do_http_call()
            
            return result
            
        except httpx.ConnectError as e:
            raise MCPConnectionError(
                f"Failed to connect to MCP server at {self._config.base_url}: {e} — HARD FAIL"
            ) from e
        except httpx.TimeoutException as e:
            raise MCPConnectionError(
                f"MCP server request timed out after {self._config.timeout_seconds}s — HARD FAIL"
            ) from e
        except httpx.HTTPError as e:
            raise MCPVerificationError(
                f"HTTP error during MCP verification: {e}"
            ) from e
        except json.JSONDecodeError as e:
            raise MCPVerificationError(
                f"Invalid JSON response from MCP server: {e}"
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
    
    async def health_check(self) -> bool:
        """Check if MCP server is reachable.
        
        Returns:
            True if MCP server responds, False otherwise
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
