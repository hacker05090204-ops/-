"""
Test Execution Layer Types

Property-based tests for type invariants.
"""

import pytest
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings

from execution_layer.types import (
    SafeActionType,
    ForbiddenActionType,
    EvidenceType,
    ExecutionStatus,
    MCPClassification,
    SafeAction,
    ExecutionToken,
    ExecutionBatch,
    EvidenceArtifact,
    EvidenceBundle,
    VideoPoC,
    ExecutionAuditRecord,
    StoreOwnershipAttestation,
    DuplicateExplorationConfig,
)


class TestSafeActionType:
    """Test SafeActionType enum."""
    
    def test_all_safe_actions_defined(self):
        """All safe action types should be defined."""
        expected = {
            "navigate", "click", "input_text", "scroll", "wait",
            "screenshot", "get_text", "get_attribute", "hover", "select_option"
        }
        actual = {a.value for a in SafeActionType}
        assert actual == expected
    
    def test_safe_actions_are_strings(self):
        """Safe action values should be strings."""
        for action in SafeActionType:
            assert isinstance(action.value, str)


class TestForbiddenActionType:
    """Test ForbiddenActionType enum."""
    
    def test_all_forbidden_actions_defined(self):
        """All forbidden action types should be defined."""
        expected = {
            "login", "authenticate", "create_account", "delete_account",
            "modify_data", "delete_data", "bypass_captcha", "bypass_auth",
            "submit_form", "upload_file", "download_file", "execute_script",
            "impersonate", "access_admin", "payment", "checkout"
        }
        actual = {a.value for a in ForbiddenActionType}
        assert actual == expected


class TestSafeAction:
    """Test SafeAction dataclass."""
    
    def test_create_valid_action(self):
        """Should create valid SafeAction."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Navigate to example",
        )
        assert action.action_id == "test-1"
        assert action.action_type == SafeActionType.NAVIGATE
    
    def test_action_requires_id(self):
        """SafeAction should require action_id."""
        with pytest.raises(ValueError, match="must have action_id"):
            SafeAction(
                action_id="",
                action_type=SafeActionType.NAVIGATE,
                target="https://example.com",
                parameters={},
                description="Test",
            )
    
    def test_action_hash_is_deterministic(self):
        """Action hash should be deterministic."""
        action1 = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.CLICK,
            target="#button",
            parameters={"wait": True},
            description="Click button",
        )
        action2 = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.CLICK,
            target="#button",
            parameters={"wait": True},
            description="Click button",
        )
        assert action1.compute_hash() == action2.compute_hash()
    
    def test_different_actions_have_different_hashes(self):
        """Different actions should have different hashes."""
        action1 = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.CLICK,
            target="#button1",
            parameters={},
            description="Click button 1",
        )
        action2 = SafeAction(
            action_id="test-2",
            action_type=SafeActionType.CLICK,
            target="#button2",
            parameters={},
            description="Click button 2",
        )
        assert action1.compute_hash() != action2.compute_hash()


class TestExecutionToken:
    """Test ExecutionToken dataclass."""
    
    def test_generate_token(self):
        """Should generate valid token."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
        token = ExecutionToken.generate(
            approver_id="human-1",
            action=action,
            validity_minutes=15,
        )
        assert token.token_id
        assert token.approver_id == "human-1"
        assert not token.is_expired
        assert not token.is_batch
    
    def test_token_expiry(self):
        """Token should expire after validity period."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
        # Create token that's already expired
        now = datetime.now(timezone.utc)
        token = ExecutionToken(
            token_id="test-token",
            approver_id="human-1",
            approved_at=now - timedelta(hours=1),
            action_hash=action.compute_hash(),
            expires_at=now - timedelta(minutes=30),
        )
        assert token.is_expired
    
    def test_token_matches_action(self):
        """Token should match the action it was created for."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
        token = ExecutionToken.generate(
            approver_id="human-1",
            action=action,
        )
        assert token.matches_action(action)
    
    def test_token_does_not_match_different_action(self):
        """Token should not match different action."""
        action1 = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test 1",
        )
        action2 = SafeAction(
            action_id="test-2",
            action_type=SafeActionType.CLICK,
            target="#button",
            parameters={},
            description="Test 2",
        )
        token = ExecutionToken.generate(
            approver_id="human-1",
            action=action1,
        )
        assert not token.matches_action(action2)
    
    def test_batch_token_generation(self):
        """Should generate batch token for multiple actions."""
        actions = [
            SafeAction(
                action_id=f"test-{i}",
                action_type=SafeActionType.NAVIGATE,
                target=f"https://example{i}.com",
                parameters={},
                description=f"Test {i}",
            )
            for i in range(3)
        ]
        token = ExecutionToken.generate_batch(
            approver_id="human-1",
            actions=actions,
        )
        assert token.is_batch
        assert token.batch_size == 3
        assert token.matches_batch(actions)


class TestStoreOwnershipAttestation:
    """Test StoreOwnershipAttestation dataclass."""
    
    def test_create_attestation(self):
        """Should create valid attestation."""
        attestation = StoreOwnershipAttestation.create(
            store_domain="my-store.myshopify.com",
            attester_id="human-1",
            validity_days=30,
        )
        assert attestation.store_domain == "my-store.myshopify.com"
        assert attestation.attester_id == "human-1"
        assert attestation.is_valid
        assert not attestation.is_expired
    
    def test_attestation_expiry(self):
        """Attestation should expire after validity period."""
        now = datetime.now(timezone.utc)
        attestation = StoreOwnershipAttestation(
            attestation_id="test-att",
            store_domain="my-store.myshopify.com",
            attester_id="human-1",
            attested_at=now - timedelta(days=60),
            attestation_hash="abc123",
            expires_at=now - timedelta(days=30),
        )
        assert attestation.is_expired
        assert not attestation.is_valid


class TestDuplicateExplorationConfig:
    """Test DuplicateExplorationConfig dataclass."""
    
    def test_default_config(self):
        """Should have sensible defaults."""
        config = DuplicateExplorationConfig()
        assert config.max_depth == 3
        assert config.max_hypotheses == 5
        assert config.max_total_actions == 20
    
    def test_custom_config(self):
        """Should accept custom values."""
        config = DuplicateExplorationConfig(
            max_depth=5,
            max_hypotheses=10,
            max_total_actions=50,
        )
        assert config.max_depth == 5
        assert config.max_hypotheses == 10
        assert config.max_total_actions == 50
    
    def test_invalid_config(self):
        """Should reject invalid values."""
        with pytest.raises(ValueError):
            DuplicateExplorationConfig(max_depth=0)
        with pytest.raises(ValueError):
            DuplicateExplorationConfig(max_hypotheses=0)
        with pytest.raises(ValueError):
            DuplicateExplorationConfig(max_total_actions=0)
