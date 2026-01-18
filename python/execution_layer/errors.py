"""
Execution Layer Error Hierarchy

All errors that cause HARD STOP are marked as such.
HARD STOP means: refuse to proceed, log the violation, alert human.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""


class ExecutionLayerError(Exception):
    """Base error for Execution Layer."""
    pass


class ScopeViolationError(ExecutionLayerError):
    """Target is outside authorized scope — HARD STOP.
    
    This error is raised when:
    - Target domain is not in authorized scope
    - Target is a live merchant store (Shopify)
    - Target path is explicitly excluded
    """
    pass


class UnsafeActionError(ExecutionLayerError):
    """Action is not in SAFE_ACTIONS allow-list — HARD STOP.
    
    This error is raised when:
    - Action type is not in SAFE_ACTIONS
    - Action parameters indicate unsafe behavior
    """
    pass


class ForbiddenActionError(ExecutionLayerError):
    """Action is in FORBIDDEN_ACTIONS list — HARD STOP.
    
    This error is raised when:
    - Action type is in FORBIDDEN_ACTIONS
    - Action attempts auth bypass, CAPTCHA bypass, etc.
    """
    pass


class HumanApprovalRequired(ExecutionLayerError):
    """Execution blocked — human approval required.
    
    This is NOT a HARD STOP — it blocks until human approves.
    """
    pass


class TokenExpiredError(ExecutionLayerError):
    """Execution token has expired — request new approval."""
    pass


class TokenAlreadyUsedError(ExecutionLayerError):
    """Execution token already used — request new approval.
    
    Tokens are ONE-TIME USE only.
    """
    pass


class TokenMismatchError(ExecutionLayerError):
    """Token does not match action — request new approval.
    
    Tokens are bound to specific action(s) via hash.
    """
    pass


class ArchitecturalViolationError(ExecutionLayerError):
    """Attempted to perform frozen phase responsibility — HARD STOP.
    
    This error is raised when Execution Layer is asked to:
    - Classify vulnerabilities (MCP's responsibility)
    - Generate proofs (MCP's responsibility)
    - Compute confidence scores (MCP's responsibility)
    - Submit reports (human's responsibility)
    - Bypass human approval
    """
    pass


class EvidenceCaptureError(ExecutionLayerError):
    """Error capturing evidence — retry or abort."""
    pass


class BrowserSessionError(ExecutionLayerError):
    """Error with browser session — cleanup and retry."""
    pass


class AuditIntegrityError(ExecutionLayerError):
    """Audit trail integrity compromised — HARD STOP."""
    pass


class VideoPoCExistsError(ExecutionLayerError):
    """VideoPoC already exists for this finding_id — IDEMPOTENCY GUARD.
    
    Only ONE VideoPoC per finding_id is allowed.
    """
    pass


class StoreAttestationRequired(ExecutionLayerError):
    """Store ownership attestation required for Shopify target — HARD STOP.
    
    Human must provide attestation that they own/control the store.
    """
    pass


class DuplicateExplorationLimitError(ExecutionLayerError):
    """Duplicate exploration limit reached — STOP condition.
    
    This error is raised when:
    - max_depth exceeded
    - max_hypotheses exceeded
    - max_total_actions exceeded
    """
    pass


class MCPConnectionError(ExecutionLayerError):
    """MCP server unreachable — HARD FAIL.
    
    This error is raised when:
    - MCP server is not responding
    - Connection timeout
    - Network error
    """
    pass


class MCPVerificationError(ExecutionLayerError):
    """MCP verification request failed.
    
    This error is raised when:
    - MCP returns non-200 status
    - Invalid response format
    """
    pass


class BountyPipelineConnectionError(ExecutionLayerError):
    """Bounty Pipeline unreachable — HARD FAIL.
    
    This error is raised when:
    - Bounty Pipeline is not responding
    - Connection timeout
    - Network error
    """
    pass


class BountyPipelineError(ExecutionLayerError):
    """Bounty Pipeline request failed.
    
    This error is raised when:
    - Draft creation fails
    - Invalid response format
    """
    pass


class ThrottleConfigError(ExecutionLayerError):
    """Throttle configuration missing or invalid — HARD FAIL.
    
    This error is raised when:
    - ExecutionThrottleConfig is missing
    - min_delay_per_action is invalid
    - max_actions_per_host_per_minute is invalid
    """
    pass


class ThrottleLimitExceededError(ExecutionLayerError):
    """Per-host action limit exceeded — HARD FAIL.
    
    This error is raised when:
    - max_actions_per_host_per_minute exceeded
    - Rate limit triggered for target host
    """
    pass


class DiskRetentionError(ExecutionLayerError):
    """Disk retention limit exceeded — HARD FAIL.
    
    This error is raised when:
    - max_total_disk_mb exceeded
    - max_artifacts_per_execution exceeded
    - Disk space critically low
    """
    pass


class HeadlessOverrideError(ExecutionLayerError):
    """Headless override without explicit approval — HARD FAIL.
    
    This error is raised when:
    - headless=False without explicit HumanApproval flag
    - Non-headless mode attempted without HIGH-RISK acknowledgment
    """
    pass


# ============================================================================
# HARDENING ERROR TYPES (Phase-4 Hardening)
# OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS
# ============================================================================


class ConfigurationError(ExecutionLayerError):
    """Configuration error (e.g., non-HTTPS URL) — startup failure.
    
    This error is raised when:
    - Non-HTTPS URL configured for MCP or Pipeline client
    - Invalid SSL configuration
    """
    pass


class ResponseValidationError(ExecutionLayerError):
    """API response failed schema validation — HARD FAIL.
    
    This error is raised when:
    - MCP response missing required fields
    - Pipeline response missing required fields
    - Response schema mismatch
    """
    pass


class PartialEvidenceError(ExecutionLayerError):
    """Evidence capture incomplete — HARD FAIL.
    
    This error is raised when:
    - HAR file missing after execution
    - No screenshots captured
    - Evidence bundle incomplete
    """
    pass


class RetryExhaustedError(ExecutionLayerError):
    """All retries exhausted — HARD FAIL.
    
    This error is raised when:
    - Maximum retry attempts reached
    - All retry attempts failed
    """
    pass


class HashChainVerificationError(ExecutionLayerError):
    """Hash chain verification failed — HARD FAIL.
    
    This error is raised when:
    - Manifest hash chain broken
    - Evidence bundle hash mismatch
    - Audit log hash chain broken
    """
    pass


class AutomationDetectedError(ExecutionLayerError):
    """Automation detection triggered — STOP and alert human.
    
    OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
    
    This error is raised when:
    - navigator.webdriver detected
    - CAPTCHA presence detected (NO bypass)
    - Rate limiting detected
    - Fingerprint detection triggered
    """
    pass


class BrowserFailure(ExecutionLayerError):
    """Base error for recoverable browser failures.
    
    These errors trigger the resilience/recovery workflow:
    1. Log failure
    2. Increment failure count
    3. Safe restart (if limit not reached)
    4. Resume/Retry
    """
    pass


class BrowserCrashError(BrowserFailure):
    """Browser crashed mid-execution — Recoverable.
    
    This error is raised when:
    - Browser process terminated unexpectedly
    - Page crash detected
    - Context destroyed unexpectedly
    """
    pass


class BrowserTimeoutError(BrowserFailure):
    """Browser operation timed out — Recoverable.
    
    This error is raised when:
    - Page load exceeds timeout
    - Selector wait exceeds timeout
    """
    pass


class BrowserDisconnectError(BrowserFailure):
    """Browser disconnected — Recoverable.
    
    This error is raised when:
    - CDP connection lost
    - Browser closed by external process
    """
    pass


class NavigationFailureError(ExecutionLayerError):
    """Navigation failed — capture error and fail.
    
    This error is raised when:
    - Page navigation timeout
    - DNS resolution failure
    - Connection refused
    """
    pass


class CSPBlockError(ExecutionLayerError):
    """CSP blocked request — record and fail.
    
    This error is raised when:
    - Content Security Policy violation
    - Script blocked by CSP
    - Resource blocked by CSP
    """
    pass


# Error classification for handling
HARD_STOP_ERRORS = (
    ScopeViolationError,
    UnsafeActionError,
    ForbiddenActionError,
    ArchitecturalViolationError,
    AuditIntegrityError,
    StoreAttestationRequired,
    MCPConnectionError,
    BountyPipelineConnectionError,
    ThrottleConfigError,
    ThrottleLimitExceededError,
    DiskRetentionError,
    HeadlessOverrideError,
    # Hardening error types (Phase-4 Hardening)
    ConfigurationError,
    ResponseValidationError,
    PartialEvidenceError,
    RetryExhaustedError,
    HashChainVerificationError,
    # BrowserCrashError moved to RECOVERABLE
    NavigationFailureError,
    CSPBlockError,
)

BLOCKING_ERRORS = (
    HumanApprovalRequired,
    AutomationDetectedError,  # Blocks until human decides
)

RECOVERABLE_ERRORS = (
    TokenExpiredError,
    TokenAlreadyUsedError,
    TokenMismatchError,
    EvidenceCaptureError,
    BrowserSessionError,
    VideoPoCExistsError,
    DuplicateExplorationLimitError,
    MCPVerificationError,
    BountyPipelineError,
    # Resilience Layer Errors
    BrowserFailure,  # Catches all subclasses: Crash, Timeout, Disconnect
)


def is_hard_stop(error: Exception) -> bool:
    """Check if error requires HARD STOP."""
    return isinstance(error, HARD_STOP_ERRORS)


def is_blocking(error: Exception) -> bool:
    """Check if error blocks until human action."""
    return isinstance(error, BLOCKING_ERRORS)


def is_recoverable(error: Exception) -> bool:
    """Check if error can be recovered from."""
    return isinstance(error, RECOVERABLE_ERRORS)
