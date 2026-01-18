"""
Execution Layer Scope Validation

Shopify-specific scope enforcement with store ownership attestation.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, FrozenSet
from urllib.parse import urlparse

from execution_layer.types import (
    SafeAction,
    SafeActionType,
    StoreOwnershipAttestation,
)
from execution_layer.errors import (
    ScopeViolationError,
    StoreAttestationRequired,
)


@dataclass(frozen=True)
class ShopifyScopeConfig:
    """Shopify-specific scope configuration.
    
    CRITICAL RULES:
    - Only test stores created by the researcher
    - NO live merchant stores
    - NO auth bypass
    - NO CAPTCHA bypass
    - NO account automation
    - NO impersonation
    """
    # Researcher-owned store domains (ONLY these allowed)
    researcher_store_domains: FrozenSet[str]
    
    # Explicitly excluded domains (live merchants, etc.)
    excluded_domains: FrozenSet[str] = field(default_factory=frozenset)
    
    # Excluded paths (auth, admin, etc.)
    excluded_paths: FrozenSet[str] = field(default_factory=lambda: frozenset({
        "/admin",
        "/admin/auth",
        "/admin/login",
        "/checkout",
        "/cart/checkout",
        "/account/login",
        "/account/register",
        "/password",
        "/challenge",
    }))
    
    # Allowed action types for Shopify
    allowed_actions: FrozenSet[SafeActionType] = field(
        default_factory=lambda: frozenset({
            SafeActionType.NAVIGATE,
            SafeActionType.CLICK,
            SafeActionType.SCROLL,
            SafeActionType.WAIT,
            SafeActionType.SCREENSHOT,
            SafeActionType.GET_TEXT,
            SafeActionType.GET_ATTRIBUTE,
            SafeActionType.HOVER,
        })
    )
    
    # Shopify-specific rules (all True by default)
    no_live_merchants: bool = True
    no_auth_bypass: bool = True
    no_captcha_bypass: bool = True
    no_account_automation: bool = True
    no_impersonation: bool = True
    require_store_attestation: bool = True


class ShopifyScopeValidator:
    """Validates targets and actions against Shopify scope rules."""
    
    def __init__(self, config: ShopifyScopeConfig) -> None:
        self._config = config
        self._attestations: dict[str, StoreOwnershipAttestation] = {}
    
    def register_attestation(self, attestation: StoreOwnershipAttestation) -> None:
        """Register a store ownership attestation."""
        if attestation.is_expired:
            raise ScopeViolationError(
                f"Attestation for '{attestation.store_domain}' has expired"
            )
        self._attestations[attestation.store_domain] = attestation
    
    def validate_target(self, target: str) -> bool:
        """Validate target is within Shopify scope.
        
        Raises:
            ScopeViolationError: If target violates scope rules
            StoreAttestationRequired: If attestation is missing
        """
        parsed = urlparse(target)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Extract base domain (handle subdomains)
        domain_parts = domain.split(".")
        if len(domain_parts) >= 2:
            # Check for myshopify.com domains
            if domain.endswith(".myshopify.com"):
                base_domain = domain
            else:
                base_domain = ".".join(domain_parts[-2:])
        else:
            base_domain = domain
        
        # Check if domain is explicitly excluded
        self._check_excluded_domain(domain, base_domain)
        
        # Check if domain is in researcher's authorized stores
        self._check_authorized_domain(domain, base_domain)
        
        # Check if path is excluded
        self._check_excluded_path(path)
        
        # Check store ownership attestation
        if self._config.require_store_attestation:
            self._check_attestation(domain, base_domain)
        
        return True
    
    def validate_action(self, action: SafeAction) -> bool:
        """Validate action is allowed for Shopify testing.
        
        Raises:
            ScopeViolationError: If action violates Shopify rules
        """
        # Check if action type is allowed
        if action.action_type not in self._config.allowed_actions:
            raise ScopeViolationError(
                f"Action type '{action.action_type.value}' is not allowed "
                f"for Shopify testing"
            )
        
        # Validate target if it's a URL
        if action.target.startswith(("http://", "https://")):
            self.validate_target(action.target)
        
        return True
    
    def _check_excluded_domain(self, domain: str, base_domain: str) -> None:
        """Check if domain is explicitly excluded."""
        if domain in self._config.excluded_domains:
            raise ScopeViolationError(
                f"Domain '{domain}' is explicitly excluded — HARD STOP"
            )
        if base_domain in self._config.excluded_domains:
            raise ScopeViolationError(
                f"Domain '{base_domain}' is explicitly excluded — HARD STOP"
            )
    
    def _check_authorized_domain(self, domain: str, base_domain: str) -> None:
        """Check if domain is in researcher's authorized stores."""
        authorized = False
        for auth_domain in self._config.researcher_store_domains:
            if domain == auth_domain or domain.endswith(f".{auth_domain}"):
                authorized = True
                break
            if base_domain == auth_domain:
                authorized = True
                break
        
        if not authorized:
            raise ScopeViolationError(
                f"Domain '{domain}' is not in authorized researcher stores — HARD STOP"
            )
    
    def _check_excluded_path(self, path: str) -> None:
        """Check if path is excluded."""
        for excluded in self._config.excluded_paths:
            if path.startswith(excluded) or path == excluded:
                raise ScopeViolationError(
                    f"Path '{path}' is excluded from scope — HARD STOP"
                )
    
    def _check_attestation(self, domain: str, base_domain: str) -> None:
        """Check store ownership attestation exists and is valid."""
        attestation = self._attestations.get(domain) or self._attestations.get(base_domain)
        
        if attestation is None:
            raise StoreAttestationRequired(
                f"Store ownership attestation required for '{domain}' — "
                f"Human must attest they own/control this store"
            )
        
        if attestation.is_expired:
            raise StoreAttestationRequired(
                f"Store ownership attestation for '{domain}' has expired — "
                f"Human must provide new attestation"
            )
    
    def get_attestation(self, domain: str) -> Optional[StoreOwnershipAttestation]:
        """Get attestation for a domain if it exists."""
        return self._attestations.get(domain)
