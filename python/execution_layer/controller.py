"""
Execution Layer Controller

Main orchestrator for controlled action execution and evidence capture.
REAL EXECUTION MODE: All browser actions, MCP calls, and Bounty Pipeline
calls are REAL. No simulation.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
import secrets
import uuid

from execution_layer.types import (
    SafeAction,
    ExecutionToken,
    ExecutionBatch,
    EvidenceBundle,
    EvidenceArtifact,
    EvidenceType,
    ExecutionResult,
    MCPVerificationResult,
    VideoPoC,
    StoreOwnershipAttestation,
    DuplicateExplorationConfig,
)
from execution_layer.errors import (
    ExecutionLayerError,
    TokenAlreadyUsedError,
)
from execution_layer.actions import ActionValidator
from execution_layer.scope import ShopifyScopeConfig, ShopifyScopeValidator
from execution_layer.approval import HumanApprovalHook, ApprovalRequest, BatchApprovalRequest
from execution_layer.audit import ExecutionAuditLog
from execution_layer.evidence import EvidenceRecorder
from execution_layer.video import VideoPoCGenerator
from execution_layer.duplicate import DuplicateHandler
from execution_layer.browser import BrowserEngine, BrowserConfig
from execution_layer.mcp_client import MCPClient, MCPClientConfig
from execution_layer.pipeline_client import (
    BountyPipelineClient, BountyPipelineConfig, DraftReport
)
from execution_layer.throttle import ExecutionThrottle, ExecutionThrottleConfig
from execution_layer.retention import EvidenceRetentionManager, EvidenceRetentionPolicy


@dataclass
class ExecutionControllerConfig:
    """Configuration for ExecutionController.
    
    MANDATORY: throttle_config and retention_policy are REQUIRED.
    HARD FAIL if missing.
    """
    scope_config: ShopifyScopeConfig
    mcp_config: MCPClientConfig
    pipeline_config: BountyPipelineConfig
    throttle_config: ExecutionThrottleConfig  # REQUIRED
    retention_policy: EvidenceRetentionPolicy  # REQUIRED
    browser_config: Optional[BrowserConfig] = None
    duplicate_config: Optional[DuplicateExplorationConfig] = None


class ExecutionController:
    """Main orchestrator for controlled action execution.
    
    REAL EXECUTION MODE:
    - Real Playwright browser execution
    - Real HAR/screenshot/video capture to disk
    - Real HTTP calls to MCP server
    - Real HTTP calls to Bounty Pipeline API
    
    NON-RESPONSIBILITIES (HARD STOP if attempted):
    - Classify vulnerabilities (MCP's responsibility)
    - Generate proofs (MCP's responsibility)
    - Compute confidence scores (MCP's responsibility)
    - Submit reports (human's responsibility)
    """
    
    def __init__(self, config: ExecutionControllerConfig) -> None:
        self._scope_validator = ShopifyScopeValidator(config.scope_config)
        self._action_validator = ActionValidator()
        self._approval_hook = HumanApprovalHook()
        self._audit_log = ExecutionAuditLog()
        self._evidence_recorder = EvidenceRecorder()
        self._video_generator = VideoPoCGenerator()
        self._duplicate_handler = DuplicateHandler(config.duplicate_config)
        self._browser_engine = BrowserEngine(config.browser_config)
        self._mcp_client = MCPClient(config.mcp_config)
        self._pipeline_client = BountyPipelineClient(config.pipeline_config)
        self._used_tokens: set[str] = set()

    def register_store_attestation(self, attestation: StoreOwnershipAttestation) -> None:
        """Register store ownership attestation."""
        self._scope_validator.register_attestation(attestation)
    
    def request_approval(self, action: SafeAction) -> ApprovalRequest:
        """Request human approval for single action."""
        self._action_validator.validate(action)
        if action.target.startswith(("http://", "https://")):
            self._scope_validator.validate_target(action.target)
        return self._approval_hook.request_approval(action)
    
    def request_batch_approval(self, actions: list[SafeAction]) -> BatchApprovalRequest:
        """Request human approval for batch of actions."""
        for action in actions:
            self._action_validator.validate(action)
            if action.target.startswith(("http://", "https://")):
                self._scope_validator.validate_target(action.target)
        return self._approval_hook.request_batch_approval(actions)
    
    def approve(self, request_id: str, approver_id: str, 
                validity_minutes: Optional[int] = None) -> ExecutionToken:
        """Approve a pending request."""
        return self._approval_hook.approve(request_id, approver_id, validity_minutes)
    
    def reject(self, request_id: str, reason: str) -> None:
        """Reject a pending request."""
        self._approval_hook.reject(request_id, reason)

    async def execute(self, action: SafeAction, token: ExecutionToken,
                      enable_video: bool = False) -> ExecutionResult:
        """Execute a single safe action with human approval via REAL browser."""
        execution_id = str(uuid.uuid4())
        result = ExecutionResult(execution_id=execution_id, action=action, success=False)
        session_id = str(uuid.uuid4())
        
        try:
            self._validate_token(token, action)
            self._action_validator.validate(action)
            if action.target.startswith(("http://", "https://")):
                self._scope_validator.validate_target(action.target)
            
            await self._browser_engine.start_session(
                session_id=session_id, execution_id=execution_id, enable_video=enable_video)
            
            await self._browser_engine.execute_action(session_id=session_id, action=action)
            await self._browser_engine.capture_screenshot(
                session_id=session_id, label=f"action_{action.action_id}")
            
            evidence_summary = await self._browser_engine.stop_session(session_id)
            evidence_bundle = await self._build_evidence_bundle(execution_id, evidence_summary)
            result.evidence_bundle = evidence_bundle
            
            self._invalidate_token(token)
            self._audit_log.record(
                action=action, actor=token.approver_id, outcome="success",
                token=token, evidence_bundle_id=evidence_bundle.bundle_id,
                execution_id=execution_id)
            result.complete(success=True)
            
        except ExecutionLayerError as e:
            if self._browser_engine.is_session_active(session_id):
                await self._browser_engine.stop_session(session_id)
            self._audit_log.record(
                action=action, actor=token.approver_id if token else "unknown",
                outcome=f"failed: {type(e).__name__}", token=token, execution_id=execution_id)
            result.complete(success=False, error=str(e))
            raise
        return result

    async def execute_batch(self, actions: list[SafeAction], token: ExecutionToken,
                            enable_video: bool = False) -> list[ExecutionResult]:
        """Execute batch of safe actions via REAL browser."""
        self._validate_batch_token(token, actions)
        results: list[ExecutionResult] = []
        batch_execution_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        await self._browser_engine.start_session(
            session_id=session_id, execution_id=batch_execution_id, enable_video=enable_video)
        
        try:
            for i, action in enumerate(actions):
                execution_id = f"{batch_execution_id}_{i}"
                result = ExecutionResult(execution_id=execution_id, action=action, success=False)
                try:
                    self._action_validator.validate(action)
                    if action.target.startswith(("http://", "https://")):
                        self._scope_validator.validate_target(action.target)
                    await self._browser_engine.execute_action(session_id=session_id, action=action)
                    await self._browser_engine.capture_screenshot(
                        session_id=session_id, label=f"batch_{i}_{action.action_id}")
                    result.complete(success=True)
                except ExecutionLayerError as e:
                    result.complete(success=False, error=str(e))
                results.append(result)
            
            evidence_summary = await self._browser_engine.stop_session(session_id)
            evidence_bundle = await self._build_evidence_bundle(batch_execution_id, evidence_summary)
            for result in results:
                result.evidence_bundle = evidence_bundle
            self._invalidate_token(token)
            for result in results:
                self._audit_log.record(
                    action=result.action, actor=token.approver_id,
                    outcome="success" if result.success else f"failed: {result.error}",
                    token=token, evidence_bundle_id=evidence_bundle.bundle_id,
                    execution_id=result.execution_id)
        except Exception:
            if self._browser_engine.is_session_active(session_id):
                await self._browser_engine.stop_session(session_id)
            raise
        return results

    async def send_to_mcp(self, evidence_bundle: EvidenceBundle) -> MCPVerificationResult:
        """Send evidence to MCP for verification via REAL HTTP. HARD FAIL if unreachable."""
        return await self._mcp_client.verify_evidence(evidence_bundle)
    
    def generate_video_poc(self, finding_id: str, mcp_result: MCPVerificationResult,
                           evidence_bundle: EvidenceBundle) -> VideoPoC:
        """Generate Video PoC for MCP-confirmed BUG. IDEMPOTENCY GUARD."""
        return self._video_generator.generate(
            finding_id=finding_id, mcp_result=mcp_result, evidence_bundle=evidence_bundle)
    
    def has_video_poc(self, finding_id: str) -> bool:
        """Check if VideoPoC exists for finding_id."""
        return self._video_generator.has_poc(finding_id)

    async def create_draft(self, finding_id: str, mcp_result: MCPVerificationResult,
                           evidence_bundle: EvidenceBundle, program_id: str) -> DraftReport:
        """Create draft report via REAL Bounty Pipeline API. DRAFT ONLY. HARD FAIL if unreachable."""
        return await self._pipeline_client.create_draft(
            finding_id=finding_id, mcp_result=mcp_result,
            evidence_bundle=evidence_bundle, program_id=program_id)
    
    def start_duplicate_exploration(self, finding_id: str):
        """Start duplicate exploration for a finding."""
        return self._duplicate_handler.start_exploration(finding_id)
    
    def generate_hypothesis(self, exploration_id: str, hypothesis_data: dict[str, Any]):
        """Generate hypothesis for duplicate exploration."""
        return self._duplicate_handler.generate_hypothesis(exploration_id, hypothesis_data)
    
    def record_duplicate_decision(self, finding_id: str, is_duplicate: bool) -> None:
        """Record human decision on duplicate status."""
        self._duplicate_handler.record_human_decision(finding_id, is_duplicate)
    
    def verify_audit_chain(self) -> bool:
        """Verify audit log integrity."""
        return self._audit_log.verify_chain()
    
    def get_audit_records(self, execution_id: str):
        """Get audit records for an execution."""
        return self._audit_log.get_records_for_execution(execution_id)
    
    def export_audit(self, start: Optional[datetime] = None, end: Optional[datetime] = None):
        """Export audit records for compliance."""
        return self._audit_log.export_for_compliance(start, end)
    
    async def cleanup(self) -> None:
        """Cleanup all resources."""
        await self._browser_engine.cleanup()
        await self._mcp_client.close()
        await self._pipeline_client.close()

    def _validate_token(self, token: ExecutionToken, action: SafeAction) -> None:
        """Validate token for single action."""
        if token.token_id in self._used_tokens:
            raise TokenAlreadyUsedError(
                f"Token '{token.token_id}' has already been used — request new approval")
        self._approval_hook.validate_token(token, action)
    
    def _validate_batch_token(self, token: ExecutionToken, actions: list[SafeAction]) -> None:
        """Validate token for batch execution."""
        if token.token_id in self._used_tokens:
            raise TokenAlreadyUsedError(
                f"Token '{token.token_id}' has already been used — request new approval")
        self._approval_hook.validate_batch_token(token, actions)
    
    def _invalidate_token(self, token: ExecutionToken) -> None:
        """Invalidate token after use."""
        self._used_tokens.add(token.token_id)
        self._approval_hook.invalidate_token(token)

    async def _build_evidence_bundle(self, execution_id: str,
                                     evidence_summary: dict[str, Any]) -> EvidenceBundle:
        """Build evidence bundle from REAL file paths on disk."""
        har_artifact: Optional[EvidenceArtifact] = None
        har_path = evidence_summary.get("har_path")
        if har_path and Path(har_path).exists():
            har_content = Path(har_path).read_bytes()
            har_artifact = EvidenceArtifact.create(
                artifact_type=EvidenceType.HAR, content=har_content, file_path=har_path)
        
        screenshots: list[EvidenceArtifact] = []
        for screenshot_path in evidence_summary.get("screenshot_paths", []):
            if Path(screenshot_path).exists():
                screenshot_content = Path(screenshot_path).read_bytes()
                screenshots.append(EvidenceArtifact.create(
                    artifact_type=EvidenceType.SCREENSHOT, content=screenshot_content,
                    file_path=screenshot_path))
        
        video_artifact: Optional[EvidenceArtifact] = None
        video_path = evidence_summary.get("video_path")
        if video_path and Path(video_path).exists():
            video_content = Path(video_path).read_bytes()
            video_artifact = EvidenceArtifact.create(
                artifact_type=EvidenceType.VIDEO, content=video_content, file_path=video_path)
        
        console_logs: list[EvidenceArtifact] = []
        for log_entry in evidence_summary.get("console_logs", []):
            log_content = str(log_entry).encode()
            console_logs.append(EvidenceArtifact.create(
                artifact_type=EvidenceType.CONSOLE_LOG, content=log_content))
        
        execution_trace = [
            {"timestamp": evidence_summary.get("started_at"), "event_type": "session_start",
             "details": {"session_id": evidence_summary.get("session_id")}},
            {"timestamp": evidence_summary.get("stopped_at"), "event_type": "session_stop",
             "details": {"execution_id": execution_id}},
        ]
        
        bundle = EvidenceBundle(
            bundle_id=str(uuid.uuid4()), execution_id=execution_id,
            har_file=har_artifact, screenshots=screenshots, video=video_artifact,
            console_logs=console_logs, execution_trace=execution_trace)
        bundle.finalize()
        return bundle
