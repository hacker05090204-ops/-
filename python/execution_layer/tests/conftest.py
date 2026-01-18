"""
Shared test fixtures for Execution Layer tests.
"""

import pytest
from datetime import datetime, timezone

from execution_layer.types import (
    SafeActionType,
    SafeAction,
    StoreOwnershipAttestation,
    DuplicateExplorationConfig,
)
from execution_layer.scope import ShopifyScopeConfig
from execution_layer.controller import ExecutionController, ExecutionControllerConfig
from execution_layer.mcp_client import MCPClientConfig
from execution_layer.pipeline_client import BountyPipelineConfig
from execution_layer.browser import BrowserConfig
from execution_layer.throttle import ExecutionThrottleConfig
from execution_layer.retention import EvidenceRetentionPolicy
from execution_layer.browser_launcher import FakeBrowserLauncher


@pytest.fixture
def scope_config():
    """Default scope config for tests."""
    return ShopifyScopeConfig(
        researcher_store_domains=frozenset({
            "my-store.myshopify.com",
        }),
        require_store_attestation=False,
    )


@pytest.fixture
def scope_config_with_attestation():
    """Scope config requiring attestation."""
    return ShopifyScopeConfig(
        researcher_store_domains=frozenset({
            "my-store.myshopify.com",
        }),
        require_store_attestation=True,
    )


@pytest.fixture
def mcp_config():
    """Default MCP client config for tests."""
    return MCPClientConfig(base_url="https://localhost:8080")


@pytest.fixture
def pipeline_config():
    """Default Bounty Pipeline config for tests."""
    return BountyPipelineConfig(base_url="https://localhost:8081")


@pytest.fixture
def browser_config():
    """Default browser config for tests."""
    return BrowserConfig(headless=True, artifacts_dir="test_artifacts")


@pytest.fixture
def throttle_config():
    """Default throttle config for tests."""
    return ExecutionThrottleConfig(
        max_requests_per_minute=60,
        max_requests_per_hour=600,
        cooldown_seconds=1,
    )


@pytest.fixture
def retention_policy():
    """Default retention policy for tests."""
    return EvidenceRetentionPolicy(
        max_age_days=30,
        max_total_size_mb=1000,
        cleanup_interval_hours=24,
    )


@pytest.fixture
def fake_browser_launcher():
    """Fake browser launcher for tests without real Playwright."""
    return FakeBrowserLauncher()


@pytest.fixture
def duplicate_config():
    """Default duplicate exploration config."""
    return DuplicateExplorationConfig(
        max_depth=3,
        max_hypotheses=5,
        max_total_actions=20,
    )


@pytest.fixture
def controller_config(scope_config, mcp_config, pipeline_config, browser_config, 
                      throttle_config, retention_policy):
    """Default controller config for tests."""
    return ExecutionControllerConfig(
        scope_config=scope_config,
        mcp_config=mcp_config,
        pipeline_config=pipeline_config,
        browser_config=browser_config,
        throttle_config=throttle_config,
        retention_policy=retention_policy,
    )


@pytest.fixture
def controller_config_with_attestation(scope_config_with_attestation, mcp_config, 
                                       pipeline_config, browser_config,
                                       throttle_config, retention_policy):
    """Controller config requiring attestation."""
    return ExecutionControllerConfig(
        scope_config=scope_config_with_attestation,
        mcp_config=mcp_config,
        pipeline_config=pipeline_config,
        browser_config=browser_config,
        throttle_config=throttle_config,
        retention_policy=retention_policy,
    )


@pytest.fixture
def controller_config_with_duplicate(scope_config, mcp_config, pipeline_config, 
                                     browser_config, duplicate_config,
                                     throttle_config, retention_policy):
    """Controller config with duplicate exploration."""
    return ExecutionControllerConfig(
        scope_config=scope_config,
        mcp_config=mcp_config,
        pipeline_config=pipeline_config,
        browser_config=browser_config,
        duplicate_config=duplicate_config,
        throttle_config=throttle_config,
        retention_policy=retention_policy,
    )


@pytest.fixture
def controller(controller_config):
    """Default controller for tests."""
    return ExecutionController(controller_config)


@pytest.fixture
def controller_with_attestation(controller_config_with_attestation):
    """Controller requiring attestation."""
    return ExecutionController(controller_config_with_attestation)


@pytest.fixture
def controller_with_duplicate(controller_config_with_duplicate):
    """Controller with duplicate exploration."""
    return ExecutionController(controller_config_with_duplicate)


@pytest.fixture
def safe_action():
    """Default safe action for tests."""
    return SafeAction(
        action_id="test-1",
        action_type=SafeActionType.NAVIGATE,
        target="https://my-store.myshopify.com/products",
        parameters={},
        description="Navigate to products",
    )


@pytest.fixture
def attestation():
    """Default store attestation for tests."""
    return StoreOwnershipAttestation.create(
        store_domain="my-store.myshopify.com",
        attester_id="human-1",
    )
