"""
Integration Tests for Execution Layer

End-to-end tests verifying complete execution flows.
Uses asyncio.run() for async execution methods.

NOTE: These tests require real browser execution. They are SKIPPED by default
unless ALLOW_REAL_BROWSER=1 is set in the environment.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import asyncio
import os
import pytest
import uuid
from datetime import datetime, timezone

from execution_layer.types import (
    SafeActionType,
    SafeAction,
    ExecutionToken,
    StoreOwnershipAttestation,
    DuplicateExplorationConfig,
    MCPClassification,
    MCPVerificationResult,
    EvidenceType,
    EvidenceArtifact,
    EvidenceBundle,
)
from execution_layer.scope import ShopifyScopeConfig
from execution_layer.controller import ExecutionController, ExecutionControllerConfig
from execution_layer.mcp_client import MCPClientConfig
from execution_layer.pipeline_client import BountyPipelineConfig
from execution_layer.browser import BrowserConfig
from execution_layer.throttle import ExecutionThrottleConfig
from execution_layer.retention import EvidenceRetentionPolicy
from execution_layer.errors import (
    ScopeViolationError,
    UnsafeActionError,
    ForbiddenActionError,
    HumanApprovalRequired,
    TokenExpiredError,
    TokenAlreadyUsedError,
    TokenMismatchError,
    StoreAttestationRequired,
    ArchitecturalViolationError,
    VideoPoCExistsError,
    DuplicateExplorationLimitError,
)


# === Test UUID Helpers ===
def make_test_uuid(seed: int = 0) -> str:
    """Generate a valid UUIDv4 for tests.
    
    Uses uuid4() to generate valid UUIDv4 format that passes security validation.
    """
    return str(uuid.uuid4())


def make_exec_id(n: int = 1) -> str:
    """Generate a test execution ID (valid UUIDv4)."""
    return str(uuid.uuid4())


def make_bundle_id(n: int = 1) -> str:
    """Generate a test bundle ID (valid UUIDv4)."""
    return str(uuid.uuid4())


# Skip all tests in this module unless ALLOW_REAL_BROWSER=1
pytestmark = pytest.mark.skipif(
    os.getenv("ALLOW_REAL_BROWSER") != "1",
    reason="Integration tests require ALLOW_REAL_BROWSER=1 (real Playwright)"
)


class TestEndToEndExecution:
    """End-to-end execution flow tests."""
    
    # Uses fixtures from conftest.py (scope_config, controller_config, controller)
    
    def test_complete_execution_flow(self, controller):
        """Test complete execution flow: request -> approve -> execute -> audit."""
        async def run_test():
            # 1. Create action
            action = SafeAction(
                action_id="e2e-test-1",
                action_type=SafeActionType.NAVIGATE,
                target="https://my-store.myshopify.com/products",
                parameters={},
                description="Navigate to products page",
            )
            
            # 2. Request approval
            request = controller.request_approval(action)
            assert request.request_id
            assert not request.approved
            
            # 3. Approve request
            token = controller.approve(request.request_id, "human-tester")
            assert token.token_id
            assert token.approver_id == "human-tester"
            
            # 4. Execute action (async)
            result = await controller.execute(action, token)
            assert result.success
            assert result.evidence_bundle is not None
            assert result.evidence_bundle.bundle_hash
            
            # 5. Verify audit trail
            records = controller.get_audit_records(result.execution_id)
            assert len(records) == 1
            assert records[0].outcome == "success"
            assert records[0].actor == "human-tester"
            
            # 6. Verify audit chain integrity
            assert controller.verify_audit_chain() is True
            
            # Cleanup
            await controller.cleanup()
        
        asyncio.run(run_test())
    
    def test_batch_execution_flow(self, controller):
        """Test batch execution flow."""
        async def run_test():
            # 1. Create multiple actions
            actions = [
                SafeAction(
                    action_id=f"batch-{i}",
                    action_type=SafeActionType.NAVIGATE,
                    target=f"https://my-store.myshopify.com/products/item{i}",
                    parameters={},
                    description=f"Navigate to item {i}",
                )
                for i in range(5)
            ]
            
            # 2. Request batch approval
            request = controller.request_batch_approval(actions)
            assert request.request_id
            
            # 3. Approve batch
            token = controller.approve(request.request_id, "batch-approver")
            assert token.is_batch
            assert token.batch_size == 5
            
            # 4. Execute batch (async)
            results = await controller.execute_batch(actions, token)
            assert len(results) == 5
            assert all(r.success for r in results)
            
            # 5. All results share evidence bundle
            bundle_ids = {r.evidence_bundle.bundle_id for r in results}
            assert len(bundle_ids) == 1  # Same bundle for all
            
            # 6. Verify audit trail
            assert controller.verify_audit_chain() is True
            
            # Cleanup
            await controller.cleanup()
        
        asyncio.run(run_test())


class TestRefusalPaths:
    """Test all refusal paths."""
    
    # Uses fixtures from conftest.py (scope_config, controller_config, controller)
    
    def test_refuse_out_of_scope_domain(self, controller):
        """Should refuse out-of-scope domain."""
        action = SafeAction(
            action_id="test",
            action_type=SafeActionType.NAVIGATE,
            target="https://malicious-site.com/exploit",
            parameters={},
            description="Out of scope",
        )
        
        with pytest.raises(ScopeViolationError):
            controller.request_approval(action)
    
    def test_refuse_admin_path(self, controller):
        """Should refuse admin path."""
        action = SafeAction(
            action_id="test",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/admin/settings",
            parameters={},
            description="Admin access",
        )
        
        with pytest.raises(ForbiddenActionError):
            controller.request_approval(action)
    
    def test_refuse_login_path(self, controller):
        """Should refuse login path."""
        action = SafeAction(
            action_id="test",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/account/login",
            parameters={},
            description="Login",
        )
        
        with pytest.raises(ForbiddenActionError):
            controller.request_approval(action)
    
    def test_refuse_checkout_path(self, controller):
        """Should refuse checkout path."""
        action = SafeAction(
            action_id="test",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/checkout",
            parameters={},
            description="Checkout",
        )
        
        with pytest.raises(ForbiddenActionError):
            controller.request_approval(action)
    
    def test_refuse_password_in_params(self, controller):
        """Should refuse password in parameters."""
        action = SafeAction(
            action_id="test",
            action_type=SafeActionType.INPUT_TEXT,
            target="#password-field",
            parameters={"text": "my_password_123"},
            description="Enter password",
        )
        
        with pytest.raises(ForbiddenActionError):
            controller.request_approval(action)
    
    def test_refuse_token_reuse(self, controller):
        """Should refuse token reuse."""
        async def run_test():
            action = SafeAction(
                action_id="test",
                action_type=SafeActionType.NAVIGATE,
                target="https://my-store.myshopify.com/products",
                parameters={},
                description="Navigate",
            )
            
            request = controller.request_approval(action)
            token = controller.approve(request.request_id, "human")
            
            # First use succeeds
            result = await controller.execute(action, token)
            assert result.success
            
            # Second use fails
            with pytest.raises(TokenAlreadyUsedError):
                await controller.execute(action, token)
            
            # Cleanup
            await controller.cleanup()
        
        asyncio.run(run_test())
    
    def test_refuse_mismatched_token(self, controller):
        """Should refuse token for different action."""
        async def run_test():
            action1 = SafeAction(
                action_id="action-1",
                action_type=SafeActionType.NAVIGATE,
                target="https://my-store.myshopify.com/products",
                parameters={},
                description="Action 1",
            )
            action2 = SafeAction(
                action_id="action-2",
                action_type=SafeActionType.CLICK,
                target="#button",
                parameters={},
                description="Action 2",
            )
            
            request = controller.request_approval(action1)
            token = controller.approve(request.request_id, "human")
            
            # Token for action1 should not work for action2
            with pytest.raises(TokenMismatchError):
                await controller.execute(action2, token)
            
            # Cleanup
            await controller.cleanup()
        
        asyncio.run(run_test())


class TestStoreAttestationFlow:
    """Test store attestation requirement flow."""
    
    # Uses fixtures from conftest.py (scope_config_with_attestation, controller_config_with_attestation)
    
    @pytest.fixture
    def controller(self, controller_config_with_attestation):
        return ExecutionController(controller_config_with_attestation)
    
    def test_require_attestation_before_approval(self, controller):
        """Should require attestation before approval."""
        action = SafeAction(
            action_id="test",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/products",
            parameters={},
            description="Navigate",
        )
        
        with pytest.raises(StoreAttestationRequired):
            controller.request_approval(action)
    
    def test_accept_with_valid_attestation(self, controller):
        """Should accept with valid attestation."""
        # Register attestation
        attestation = StoreOwnershipAttestation.create(
            store_domain="my-store.myshopify.com",
            attester_id="store-owner",
            validity_days=30,
        )
        controller.register_store_attestation(attestation)
        
        # Now approval should work
        action = SafeAction(
            action_id="test",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/products",
            parameters={},
            description="Navigate",
        )
        
        request = controller.request_approval(action)
        assert request.request_id


class TestVideoPoCFlow:
    """Test Video PoC generation flow."""
    
    # Uses fixtures from conftest.py (scope_config, controller_config, controller)
    
    def test_generate_video_poc_for_bug(self, controller):
        """Should generate Video PoC for MCP BUG."""
        # Create MCP BUG result
        mcp_result = MCPVerificationResult(
            verification_id="mcp-1",
            finding_id="finding-1",
            classification=MCPClassification.BUG,
            invariant_violated="auth-bypass",
            proof_hash="proof-hash-123",
            verified_at=datetime.now(timezone.utc),
        )
        
        # Create evidence bundle with video
        video_artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.VIDEO,
            content=b"video_content_here",
        )
        bundle = EvidenceBundle(
            bundle_id=make_bundle_id(1),
            execution_id=make_exec_id(1),
            video=video_artifact,
            execution_trace=[
                {"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "start"},
                {"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "action"},
                {"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "end"},
            ],
        )
        
        # Generate PoC
        poc = controller.generate_video_poc("finding-1", mcp_result, bundle)
        assert poc.finding_id == "finding-1"
        assert poc.poc_hash
        
        # Verify idempotency
        assert controller.has_video_poc("finding-1") is True
        
        # Second generation should fail
        with pytest.raises(VideoPoCExistsError):
            controller.generate_video_poc("finding-1", mcp_result, bundle)
    
    def test_reject_video_poc_for_non_bug(self, controller):
        """Should reject Video PoC for non-BUG."""
        mcp_result = MCPVerificationResult(
            verification_id="mcp-1",
            finding_id="finding-1",
            classification=MCPClassification.SIGNAL,  # Not BUG
            invariant_violated=None,
            proof_hash=None,
            verified_at=datetime.now(timezone.utc),
        )
        
        video_artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.VIDEO,
            content=b"video",
        )
        bundle = EvidenceBundle(
            bundle_id=make_bundle_id(2),
            execution_id=make_exec_id(2),
            video=video_artifact,
            execution_trace=[{"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "test"}],
        )
        
        with pytest.raises(ArchitecturalViolationError):
            controller.generate_video_poc("finding-1", mcp_result, bundle)


class TestDuplicateExplorationFlow:
    """Test duplicate exploration flow."""
    
    # Uses fixtures from conftest.py (duplicate_config, controller_config_with_duplicate)
    
    @pytest.fixture
    def controller(self, controller_config_with_duplicate):
        return ExecutionController(controller_config_with_duplicate)
    
    def test_exploration_with_limits(self, controller):
        """Should enforce exploration limits."""
        # Start exploration
        state = controller.start_duplicate_exploration("finding-1")
        assert state.exploration_id
        
        # Generate hypotheses up to limit
        for i in range(5):
            hypothesis = controller.generate_hypothesis(
                state.exploration_id,
                {"variant": i},
            )
            assert hypothesis["hypothesis_id"]
        
        # Next hypothesis should fail
        with pytest.raises(DuplicateExplorationLimitError):
            controller.generate_hypothesis(state.exploration_id, {"variant": 5})
    
    def test_human_decision_recording(self, controller):
        """Should record human decision on duplicate."""
        controller.record_duplicate_decision("finding-1", is_duplicate=True)
        controller.record_duplicate_decision("finding-2", is_duplicate=False)
        
        # Decisions are advisory, not automatic


class TestAuditCompliance:
    """Test audit compliance features."""
    
    # Uses fixtures from conftest.py (scope_config, controller_config, controller)
    
    def test_audit_export(self, controller):
        """Should export audit records for compliance."""
        async def run_test():
            # Execute some actions
            for i in range(3):
                action = SafeAction(
                    action_id=f"audit-test-{i}",
                    action_type=SafeActionType.NAVIGATE,
                    target="https://my-store.myshopify.com/products",
                    parameters={},
                    description=f"Action {i}",
                )
                request = controller.request_approval(action)
                token = controller.approve(request.request_id, f"auditor-{i}")
                await controller.execute(action, token)
            
            # Export audit
            export = controller.export_audit()
            assert len(export) == 3
            
            # Verify export format
            for record in export:
                assert "record_id" in record
                assert "timestamp" in record
                assert "action_type" in record
                assert "actor" in record
                assert "outcome" in record
                assert "record_hash" in record
            
            # Cleanup
            await controller.cleanup()
        
        asyncio.run(run_test())
