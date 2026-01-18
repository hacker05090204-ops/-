"""
Test Execution Layer Controller

Integration tests for the main orchestrator.
Uses asyncio.run() for async execution methods.

CATEGORY B MITIGATION: Uses FakeBrowserLauncher to avoid real browser dependency.
"""

import asyncio
import pytest
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
from execution_layer.browser import BrowserConfig, BrowserEngine
from execution_layer.browser_launcher import FakeBrowserLauncher
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
)


class TestExecutionController:
    """Test ExecutionController class."""
    
    @pytest.fixture
    def scope_config(self):
        return ShopifyScopeConfig(
            researcher_store_domains=frozenset({
                "my-store.myshopify.com",
            }),
            require_store_attestation=False,  # Disable for basic tests
        )
    
    @pytest.fixture
    def throttle_config(self):
        """Throttle config required by ExecutionControllerConfig."""
        return ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=60,
        )
    
    @pytest.fixture
    def retention_policy(self):
        """Retention policy required by ExecutionControllerConfig."""
        return EvidenceRetentionPolicy(
            max_total_disk_mb=100,
            ttl_days=7,
        )
    
    @pytest.fixture
    def fake_launcher(self):
        """Fake browser launcher for testing without real Playwright."""
        return FakeBrowserLauncher()
    
    @pytest.fixture
    def controller_config(self, scope_config, throttle_config, retention_policy):
        return ExecutionControllerConfig(
            scope_config=scope_config,
            mcp_config=MCPClientConfig(base_url="https://localhost:8080"),
            pipeline_config=BountyPipelineConfig(base_url="https://localhost:8081"),
            browser_config=BrowserConfig(headless=True, artifacts_dir="test_artifacts"),
            throttle_config=throttle_config,
            retention_policy=retention_policy,
        )
    
    @pytest.fixture
    def controller(self, controller_config, fake_launcher):
        """Create controller with fake browser launcher."""
        ctrl = ExecutionController(controller_config)
        # Inject fake launcher into browser engine
        ctrl._browser_engine._launcher = fake_launcher
        return ctrl
    
    @pytest.fixture
    def action(self):
        return SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/products",
            parameters={},
            description="Navigate to products",
        )
    
    def test_request_approval(self, controller, action):
        """Should create approval request."""
        request = controller.request_approval(action)
        assert request.request_id
        assert request.action == action
    
    def test_approve_and_execute(self, controller, action):
        """Should execute action with valid token."""
        async def run_test():
            request = controller.request_approval(action)
            token = controller.approve(request.request_id, "human-1")
            
            result = await controller.execute(action, token)
            assert result.success
            assert result.evidence_bundle is not None
            
            await controller.cleanup()
        
        asyncio.run(run_test())
    
    def test_reject_without_approval(self, controller, action):
        """Should reject execution without token."""
        async def run_test():
            # Create a token for different action
            other_action = SafeAction(
                action_id="other",
                action_type=SafeActionType.CLICK,
                target="#button",
                parameters={},
                description="Other",
            )
            request = controller.request_approval(other_action)
            token = controller.approve(request.request_id, "human-1")
            
            with pytest.raises(TokenMismatchError):
                await controller.execute(action, token)
            
            await controller.cleanup()
        
        asyncio.run(run_test())
    
    def test_token_single_use(self, controller, action):
        """Should reject reused token."""
        async def run_test():
            request = controller.request_approval(action)
            token = controller.approve(request.request_id, "human-1")
            
            # First execution should succeed
            result = await controller.execute(action, token)
            assert result.success
            
            # Second execution should fail
            with pytest.raises(TokenAlreadyUsedError):
                await controller.execute(action, token)
            
            await controller.cleanup()
        
        asyncio.run(run_test())


class TestScopeEnforcement:
    """Test scope enforcement in controller."""
    
    @pytest.fixture
    def scope_config(self):
        return ShopifyScopeConfig(
            researcher_store_domains=frozenset({
                "my-store.myshopify.com",
            }),
            require_store_attestation=False,
        )
    
    @pytest.fixture
    def throttle_config(self):
        return ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=60,
        )
    
    @pytest.fixture
    def retention_policy(self):
        return EvidenceRetentionPolicy(
            max_total_disk_mb=100,
            ttl_days=7,
        )
    
    @pytest.fixture
    def fake_launcher(self):
        return FakeBrowserLauncher()
    
    @pytest.fixture
    def controller_config(self, scope_config, throttle_config, retention_policy):
        return ExecutionControllerConfig(
            scope_config=scope_config,
            mcp_config=MCPClientConfig(base_url="https://localhost:8080"),
            pipeline_config=BountyPipelineConfig(base_url="https://localhost:8081"),
            browser_config=BrowserConfig(headless=True, artifacts_dir="test_artifacts"),
            throttle_config=throttle_config,
            retention_policy=retention_policy,
        )
    
    @pytest.fixture
    def controller(self, controller_config, fake_launcher):
        ctrl = ExecutionController(controller_config)
        ctrl._browser_engine._launcher = fake_launcher
        return ctrl
    
    def test_reject_out_of_scope(self, controller):
        """Should reject out-of-scope target."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://other-store.myshopify.com/products",
            parameters={},
            description="Out of scope",
        )
        
        with pytest.raises(ScopeViolationError):
            controller.request_approval(action)
    
    def test_reject_admin_path(self, controller):
        """Should reject admin path (ForbiddenActionError from action validator)."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/admin",
            parameters={},
            description="Admin access",
        )
        
        # Action validator catches forbidden paths before scope validation
        with pytest.raises(ForbiddenActionError):
            controller.request_approval(action)


class TestForbiddenActions:
    """Test forbidden action rejection."""
    
    @pytest.fixture
    def scope_config(self):
        return ShopifyScopeConfig(
            researcher_store_domains=frozenset({
                "my-store.myshopify.com",
            }),
            require_store_attestation=False,
        )
    
    @pytest.fixture
    def throttle_config(self):
        return ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=60,
        )
    
    @pytest.fixture
    def retention_policy(self):
        return EvidenceRetentionPolicy(
            max_total_disk_mb=100,
            ttl_days=7,
        )
    
    @pytest.fixture
    def fake_launcher(self):
        return FakeBrowserLauncher()
    
    @pytest.fixture
    def controller_config(self, scope_config, throttle_config, retention_policy):
        return ExecutionControllerConfig(
            scope_config=scope_config,
            mcp_config=MCPClientConfig(base_url="https://localhost:8080"),
            pipeline_config=BountyPipelineConfig(base_url="https://localhost:8081"),
            browser_config=BrowserConfig(headless=True, artifacts_dir="test_artifacts"),
            throttle_config=throttle_config,
            retention_policy=retention_policy,
        )
    
    @pytest.fixture
    def controller(self, controller_config, fake_launcher):
        ctrl = ExecutionController(controller_config)
        ctrl._browser_engine._launcher = fake_launcher
        return ctrl
    
    def test_reject_login_path(self, controller):
        """Should reject login path (ForbiddenActionError from action validator)."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/account/login",
            parameters={},
            description="Login",
        )
        
        # Action validator catches forbidden paths before scope validation
        with pytest.raises(ForbiddenActionError):
            controller.request_approval(action)
    
    def test_reject_password_in_params(self, controller):
        """Should reject password in parameters."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.INPUT_TEXT,
            target="#input",
            parameters={"text": "password123"},
            description="Enter password",
        )
        
        with pytest.raises(ForbiddenActionError):
            controller.request_approval(action)


class TestBatchExecution:
    """Test batch execution functionality."""
    
    @pytest.fixture
    def scope_config(self):
        return ShopifyScopeConfig(
            researcher_store_domains=frozenset({
                "my-store.myshopify.com",
            }),
            require_store_attestation=False,
        )
    
    @pytest.fixture
    def throttle_config(self):
        return ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=60,
        )
    
    @pytest.fixture
    def retention_policy(self):
        return EvidenceRetentionPolicy(
            max_total_disk_mb=100,
            ttl_days=7,
        )
    
    @pytest.fixture
    def fake_launcher(self):
        return FakeBrowserLauncher()
    
    @pytest.fixture
    def controller_config(self, scope_config, throttle_config, retention_policy):
        return ExecutionControllerConfig(
            scope_config=scope_config,
            mcp_config=MCPClientConfig(base_url="https://localhost:8080"),
            pipeline_config=BountyPipelineConfig(base_url="https://localhost:8081"),
            browser_config=BrowserConfig(headless=True, artifacts_dir="test_artifacts"),
            throttle_config=throttle_config,
            retention_policy=retention_policy,
        )
    
    @pytest.fixture
    def controller(self, controller_config, fake_launcher):
        ctrl = ExecutionController(controller_config)
        ctrl._browser_engine._launcher = fake_launcher
        return ctrl
    
    @pytest.fixture
    def actions(self):
        return [
            SafeAction(
                action_id=f"test-{i}",
                action_type=SafeActionType.NAVIGATE,
                target=f"https://my-store.myshopify.com/products/item{i}",
                parameters={},
                description=f"Navigate to item {i}",
            )
            for i in range(3)
        ]
    
    def test_batch_approval(self, controller, actions):
        """Should approve batch of actions."""
        request = controller.request_batch_approval(actions)
        token = controller.approve(request.request_id, "human-1")
        
        assert token.is_batch
        assert token.batch_size == 3
    
    def test_batch_execution(self, controller, actions):
        """Should execute batch with single token."""
        async def run_test():
            request = controller.request_batch_approval(actions)
            token = controller.approve(request.request_id, "human-1")
            
            results = await controller.execute_batch(actions, token)
            assert len(results) == 3
            assert all(r.success for r in results)
            
            await controller.cleanup()
        
        asyncio.run(run_test())
    
    def test_batch_token_single_use(self, controller, actions):
        """Should reject reused batch token."""
        async def run_test():
            request = controller.request_batch_approval(actions)
            token = controller.approve(request.request_id, "human-1")
            
            # First execution should succeed
            results = await controller.execute_batch(actions, token)
            assert all(r.success for r in results)
            
            # Second execution should fail
            with pytest.raises(TokenAlreadyUsedError):
                await controller.execute_batch(actions, token)
            
            await controller.cleanup()
        
        asyncio.run(run_test())


class TestStoreAttestation:
    """Test store attestation requirement."""
    
    @pytest.fixture
    def scope_config(self):
        return ShopifyScopeConfig(
            researcher_store_domains=frozenset({
                "my-store.myshopify.com",
            }),
            require_store_attestation=True,  # Enable attestation
        )
    
    @pytest.fixture
    def throttle_config(self):
        return ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=60,
        )
    
    @pytest.fixture
    def retention_policy(self):
        return EvidenceRetentionPolicy(
            max_total_disk_mb=100,
            ttl_days=7,
        )
    
    @pytest.fixture
    def fake_launcher(self):
        return FakeBrowserLauncher()
    
    @pytest.fixture
    def controller_config(self, scope_config, throttle_config, retention_policy):
        return ExecutionControllerConfig(
            scope_config=scope_config,
            mcp_config=MCPClientConfig(base_url="https://localhost:8080"),
            pipeline_config=BountyPipelineConfig(base_url="https://localhost:8081"),
            browser_config=BrowserConfig(headless=True, artifacts_dir="test_artifacts"),
            throttle_config=throttle_config,
            retention_policy=retention_policy,
        )
    
    @pytest.fixture
    def controller(self, controller_config, fake_launcher):
        ctrl = ExecutionController(controller_config)
        ctrl._browser_engine._launcher = fake_launcher
        return ctrl
    
    @pytest.fixture
    def action(self):
        return SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/products",
            parameters={},
            description="Navigate",
        )
    
    def test_require_attestation(self, controller, action):
        """Should require attestation for Shopify store."""
        with pytest.raises(StoreAttestationRequired):
            controller.request_approval(action)
    
    def test_accept_with_attestation(self, controller, action):
        """Should accept with valid attestation."""
        attestation = StoreOwnershipAttestation.create(
            store_domain="my-store.myshopify.com",
            attester_id="human-1",
        )
        controller.register_store_attestation(attestation)
        
        request = controller.request_approval(action)
        assert request.request_id


class TestAuditIntegration:
    """Test audit log integration."""
    
    @pytest.fixture
    def scope_config(self):
        return ShopifyScopeConfig(
            researcher_store_domains=frozenset({
                "my-store.myshopify.com",
            }),
            require_store_attestation=False,
        )
    
    @pytest.fixture
    def throttle_config(self):
        return ExecutionThrottleConfig(
            min_delay_per_action_seconds=0.5,
            max_actions_per_host_per_minute=60,
        )
    
    @pytest.fixture
    def retention_policy(self):
        return EvidenceRetentionPolicy(
            max_total_disk_mb=100,
            ttl_days=7,
        )
    
    @pytest.fixture
    def fake_launcher(self):
        return FakeBrowserLauncher()
    
    @pytest.fixture
    def controller_config(self, scope_config, throttle_config, retention_policy):
        return ExecutionControllerConfig(
            scope_config=scope_config,
            mcp_config=MCPClientConfig(base_url="https://localhost:8080"),
            pipeline_config=BountyPipelineConfig(base_url="https://localhost:8081"),
            browser_config=BrowserConfig(headless=True, artifacts_dir="test_artifacts"),
            throttle_config=throttle_config,
            retention_policy=retention_policy,
        )
    
    @pytest.fixture
    def controller(self, controller_config, fake_launcher):
        ctrl = ExecutionController(controller_config)
        ctrl._browser_engine._launcher = fake_launcher
        return ctrl
    
    @pytest.fixture
    def action(self):
        return SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/products",
            parameters={},
            description="Navigate",
        )
    
    def test_audit_records_execution(self, controller, action):
        """Should record execution in audit log."""
        async def run_test():
            request = controller.request_approval(action)
            token = controller.approve(request.request_id, "human-1")
            
            result = await controller.execute(action, token)
            
            records = controller.get_audit_records(result.execution_id)
            assert len(records) == 1
            assert records[0].outcome == "success"
            
            await controller.cleanup()
        
        asyncio.run(run_test())
    
    def test_verify_audit_chain(self, controller, action):
        """Should maintain valid audit chain."""
        async def run_test():
            request = controller.request_approval(action)
            token = controller.approve(request.request_id, "human-1")
            
            await controller.execute(action, token)
            
            assert controller.verify_audit_chain() is True
            
            await controller.cleanup()
        
        asyncio.run(run_test())
