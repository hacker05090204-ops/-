"""
Test Execution Layer Scope Validation

Tests for Shopify scope enforcement and store attestation.
"""

import pytest
from datetime import datetime, timezone, timedelta

from execution_layer.types import (
    SafeActionType,
    SafeAction,
    StoreOwnershipAttestation,
)
from execution_layer.scope import ShopifyScopeConfig, ShopifyScopeValidator
from execution_layer.errors import ScopeViolationError, StoreAttestationRequired


class TestShopifyScopeConfig:
    """Test ShopifyScopeConfig dataclass."""
    
    def test_default_excluded_paths(self):
        """Should have default excluded paths."""
        config = ShopifyScopeConfig(
            researcher_store_domains=frozenset({"my-store.myshopify.com"}),
        )
        assert "/admin" in config.excluded_paths
        assert "/checkout" in config.excluded_paths
        assert "/account/login" in config.excluded_paths
    
    def test_default_rules(self):
        """Should have default security rules enabled."""
        config = ShopifyScopeConfig(
            researcher_store_domains=frozenset({"my-store.myshopify.com"}),
        )
        assert config.no_live_merchants is True
        assert config.no_auth_bypass is True
        assert config.no_captcha_bypass is True
        assert config.no_account_automation is True
        assert config.no_impersonation is True
        assert config.require_store_attestation is True


class TestShopifyScopeValidator:
    """Test ShopifyScopeValidator class."""
    
    @pytest.fixture
    def config(self):
        return ShopifyScopeConfig(
            researcher_store_domains=frozenset({
                "my-store.myshopify.com",
                "test-store.myshopify.com",
            }),
            excluded_domains=frozenset({
                "live-merchant.myshopify.com",
            }),
        )
    
    @pytest.fixture
    def validator(self, config):
        return ShopifyScopeValidator(config)
    
    @pytest.fixture
    def attestation(self):
        return StoreOwnershipAttestation.create(
            store_domain="my-store.myshopify.com",
            attester_id="human-1",
        )
    
    def test_validate_authorized_domain(self, validator, attestation):
        """Should validate authorized domain with attestation."""
        validator.register_attestation(attestation)
        assert validator.validate_target("https://my-store.myshopify.com/products")
    
    def test_reject_unauthorized_domain(self, validator, attestation):
        """Should reject unauthorized domain."""
        validator.register_attestation(attestation)
        with pytest.raises(ScopeViolationError, match="not in authorized"):
            validator.validate_target("https://other-store.myshopify.com/products")
    
    def test_reject_excluded_domain(self, validator, attestation):
        """Should reject explicitly excluded domain."""
        validator.register_attestation(attestation)
        with pytest.raises(ScopeViolationError, match="explicitly excluded"):
            validator.validate_target("https://live-merchant.myshopify.com/products")
    
    def test_reject_admin_path(self, validator, attestation):
        """Should reject admin paths."""
        validator.register_attestation(attestation)
        with pytest.raises(ScopeViolationError, match="excluded from scope"):
            validator.validate_target("https://my-store.myshopify.com/admin")
    
    def test_reject_checkout_path(self, validator, attestation):
        """Should reject checkout paths."""
        validator.register_attestation(attestation)
        with pytest.raises(ScopeViolationError, match="excluded from scope"):
            validator.validate_target("https://my-store.myshopify.com/checkout")
    
    def test_reject_login_path(self, validator, attestation):
        """Should reject login paths."""
        validator.register_attestation(attestation)
        with pytest.raises(ScopeViolationError, match="excluded from scope"):
            validator.validate_target("https://my-store.myshopify.com/account/login")


class TestStoreAttestation:
    """Test store ownership attestation requirement."""
    
    @pytest.fixture
    def config(self):
        return ShopifyScopeConfig(
            researcher_store_domains=frozenset({
                "my-store.myshopify.com",
            }),
            require_store_attestation=True,
        )
    
    @pytest.fixture
    def validator(self, config):
        return ShopifyScopeValidator(config)
    
    def test_require_attestation(self, validator):
        """Should require attestation for authorized domain."""
        with pytest.raises(StoreAttestationRequired, match="attestation required"):
            validator.validate_target("https://my-store.myshopify.com/products")
    
    def test_accept_with_attestation(self, validator):
        """Should accept with valid attestation."""
        attestation = StoreOwnershipAttestation.create(
            store_domain="my-store.myshopify.com",
            attester_id="human-1",
        )
        validator.register_attestation(attestation)
        assert validator.validate_target("https://my-store.myshopify.com/products")
    
    def test_reject_expired_attestation(self, validator):
        """Should reject expired attestation."""
        now = datetime.now(timezone.utc)
        expired_attestation = StoreOwnershipAttestation(
            attestation_id="test-att",
            store_domain="my-store.myshopify.com",
            attester_id="human-1",
            attested_at=now - timedelta(days=60),
            attestation_hash="abc123",
            expires_at=now - timedelta(days=30),
        )
        with pytest.raises(ScopeViolationError, match="expired"):
            validator.register_attestation(expired_attestation)
    
    def test_attestation_for_different_domain(self, validator):
        """Attestation for different domain should not work."""
        attestation = StoreOwnershipAttestation.create(
            store_domain="other-store.myshopify.com",
            attester_id="human-1",
        )
        validator.register_attestation(attestation)
        
        # Should still require attestation for my-store
        with pytest.raises(StoreAttestationRequired):
            validator.validate_target("https://my-store.myshopify.com/products")


class TestActionValidation:
    """Test action validation against Shopify scope."""
    
    @pytest.fixture
    def config(self):
        return ShopifyScopeConfig(
            researcher_store_domains=frozenset({
                "my-store.myshopify.com",
            }),
            require_store_attestation=False,  # Disable for action tests
        )
    
    @pytest.fixture
    def validator(self, config):
        return ShopifyScopeValidator(config)
    
    def test_validate_allowed_action(self, validator):
        """Should validate allowed action type."""
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://my-store.myshopify.com/products",
            parameters={},
            description="Navigate",
        )
        assert validator.validate_action(action)
    
    def test_reject_disallowed_action(self, validator):
        """Should reject disallowed action type."""
        # INPUT_TEXT is not in default allowed_actions for Shopify
        action = SafeAction(
            action_id="test-1",
            action_type=SafeActionType.INPUT_TEXT,
            target="https://my-store.myshopify.com/search",
            parameters={"text": "test"},
            description="Search",
        )
        with pytest.raises(ScopeViolationError, match="not allowed"):
            validator.validate_action(action)
