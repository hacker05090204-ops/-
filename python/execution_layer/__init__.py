"""
Execution Layer - Controlled Active Execution & Evidence Capture (Phase-4)

This system assists humans. It does not autonomously hunt, judge, or earn.

CRITICAL CONSTRAINTS:
- MCP (Phase-1) is READ-ONLY — DO NOT MODIFY
- Cyfer Brain (Phase-2) is READ-ONLY — DO NOT MODIFY
- Bounty Pipeline (Phase-3) is READ-ONLY — DO NOT MODIFY
- NO vulnerability classification (MCP's responsibility)
- NO proof generation (MCP's responsibility)
- NO confidence scoring (MCP's responsibility)
- NO auto-submission (human's responsibility)
- NO auth bypass
- NO CAPTCHA bypass
- Human approval REQUIRED for ALL executions

EXECUTION BOUNDARY:
The system MAY:
- Execute SAFE actions with human approval
- Capture evidence (HAR, screenshots, logs, trace)
- Record video PoC for MCP-confirmed BUG only
- Send evidence to MCP for verification (read-only)
- Create draft reports via Bounty Pipeline (draft only)

The system MUST:
- Require ExecutionToken for every action
- Invalidate tokens after single use
- Enforce scope before any execution
- Capture complete evidence for all actions
- Record all actions in hash-chained audit log
- STOP and wait for human review after draft creation
"""

from execution_layer.types import (
    # Enums
    SafeActionType,
    ForbiddenActionType,
    EvidenceType,
    ExecutionStatus,
    # Core types
    ExecutionToken,
    ExecutionBatch,
    SafeAction,
    EvidenceArtifact,
    EvidenceBundle,
    VideoPoC,
    ExecutionResult,
    ExecutionAuditRecord,
    StoreOwnershipAttestation,
    DuplicateExplorationConfig,
    # MCP types (read-only)
    MCPClassification,
    MCPVerificationResult,
)
from execution_layer.errors import (
    ExecutionLayerError,
    ScopeViolationError,
    UnsafeActionError,
    ForbiddenActionError,
    HumanApprovalRequired,
    TokenExpiredError,
    TokenAlreadyUsedError,
    TokenMismatchError,
    ArchitecturalViolationError,
    EvidenceCaptureError,
    BrowserSessionError,
    AuditIntegrityError,
    VideoPoCExistsError,
    StoreAttestationRequired,
    DuplicateExplorationLimitError,
    MCPConnectionError,
    MCPVerificationError,
    BountyPipelineConnectionError,
    BountyPipelineError,
    # Hardening error types
    ConfigurationError,
    ResponseValidationError,
    PartialEvidenceError,
    RetryExhaustedError,
    HashChainVerificationError,
    AutomationDetectedError,
    BrowserCrashError,
    NavigationFailureError,
    CSPBlockError,
    is_hard_stop,
    is_blocking,
    is_recoverable,
)
from execution_layer.actions import (
    SAFE_ACTIONS,
    FORBIDDEN_ACTIONS,
    ActionValidator,
)
from execution_layer.scope import (
    ShopifyScopeConfig,
    ShopifyScopeValidator,
)
from execution_layer.approval import (
    HumanApprovalHook,
    ApprovalRequest,
    BatchApprovalRequest,
)
from execution_layer.audit import ExecutionAuditLog
from execution_layer.evidence import EvidenceRecorder
from execution_layer.video import VideoPoCGenerator
from execution_layer.duplicate import DuplicateHandler
from execution_layer.controller import ExecutionController, ExecutionControllerConfig
from execution_layer.browser import BrowserEngine, BrowserConfig
from execution_layer.browser_failure import BrowserFailureHandler, FailureType, RecoveryStrategy, FailureContext, PartialEvidence
from execution_layer.mcp_client import MCPClient, MCPClientConfig
from execution_layer.pipeline_client import BountyPipelineClient, BountyPipelineConfig, DraftReport
# Hardening components
from execution_layer.manifest import ExecutionManifest, ManifestGenerator
from execution_layer.schemas import (
    MCPVerificationResponse,
    PipelineDraftResponse,
    ResponseValidator,
)
from execution_layer.retry import RetryPolicy, RetryExecutor, RetryAttempt
from execution_layer.request_logger import RequestLog, ResponseLog, RequestLogger
from execution_layer.anti_detection import AutomationDetectionSignal, AntiDetectionObserver
# Security remediation components (POST-PHASE-19)
from execution_layer.security import (
    GovernanceViolation,
    validate_execution_id,
    validate_session_id,
    validate_artifact_path,
    validate_file_path_relative,
    redact_har_content,
    validate_har_is_redacted,
    scan_for_credentials,
    CredentialScanResult,
    SingleRequestEnforcer,
)

__version__ = "0.1.0"
__all__ = [
    # Main orchestrator
    "ExecutionController",
    "ExecutionControllerConfig",
    # Real execution components
    "BrowserEngine",
    "BrowserConfig",
    "BrowserFailureHandler",
    "FailureType",
    "RecoveryStrategy",
    "FailureContext",
    "PartialEvidence",
    "MCPClient",
    "MCPClientConfig",
    "BountyPipelineClient",
    "BountyPipelineConfig",
    "DraftReport",
    # Components
    "ActionValidator",
    "ShopifyScopeConfig",
    "ShopifyScopeValidator",
    "HumanApprovalHook",
    "ExecutionAuditLog",
    "EvidenceRecorder",
    "VideoPoCGenerator",
    "DuplicateHandler",
    # Approval
    "ApprovalRequest",
    "BatchApprovalRequest",
    # Action lists
    "SAFE_ACTIONS",
    "FORBIDDEN_ACTIONS",
    # Enums
    "SafeActionType",
    "ForbiddenActionType",
    "EvidenceType",
    "ExecutionStatus",
    "MCPClassification",
    # Types
    "ExecutionToken",
    "ExecutionBatch",
    "SafeAction",
    "EvidenceArtifact",
    "EvidenceBundle",
    "VideoPoC",
    "ExecutionResult",
    "ExecutionAuditRecord",
    "MCPVerificationResult",
    "StoreOwnershipAttestation",
    "DuplicateExplorationConfig",
    # Errors
    "ExecutionLayerError",
    "ScopeViolationError",
    "UnsafeActionError",
    "ForbiddenActionError",
    "HumanApprovalRequired",
    "TokenExpiredError",
    "TokenAlreadyUsedError",
    "TokenMismatchError",
    "ArchitecturalViolationError",
    "EvidenceCaptureError",
    "BrowserSessionError",
    "AuditIntegrityError",
    "VideoPoCExistsError",
    "StoreAttestationRequired",
    "DuplicateExplorationLimitError",
    "MCPConnectionError",
    "MCPVerificationError",
    "BountyPipelineConnectionError",
    "BountyPipelineError",
    # Hardening error types
    "ConfigurationError",
    "ResponseValidationError",
    "PartialEvidenceError",
    "RetryExhaustedError",
    "HashChainVerificationError",
    "AutomationDetectedError",
    "BrowserCrashError",
    "NavigationFailureError",
    "CSPBlockError",
    # Error classification
    "is_hard_stop",
    "is_blocking",
    "is_recoverable",
    # Hardening components
    "ExecutionManifest",
    "ManifestGenerator",
    "MCPVerificationResponse",
    "PipelineDraftResponse",
    "ResponseValidator",
    "RetryPolicy",
    "RetryExecutor",
    "RetryAttempt",
    "RequestLog",
    "ResponseLog",
    "RequestLogger",
    "AutomationDetectionSignal",
    "AntiDetectionObserver",
    # Security remediation (POST-PHASE-19)
    "GovernanceViolation",
    "validate_execution_id",
    "validate_session_id",
    "validate_artifact_path",
    "validate_file_path_relative",
    "redact_har_content",
    "validate_har_is_redacted",
    "scan_for_credentials",
    "CredentialScanResult",
    "SingleRequestEnforcer",
]
