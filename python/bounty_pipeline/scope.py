"""
Legal Scope Validator - Ensures all actions are within legal authorization.

This module validates that targets are within authorized scope before any action.
It enforces legal boundaries and requires human confirmation for ambiguous cases.

CRITICAL: This validator causes HARD STOP on scope violations.
Operating outside legal authorization is never acceptable.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import fnmatch
import ipaddress
from urllib.parse import urlparse

from bounty_pipeline.errors import ScopeViolationError, AuthorizationExpiredError
from bounty_pipeline.types import AuthorizationDocument


class ScopeDecision(str, Enum):
    """Result of scope validation."""

    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    AMBIGUOUS = "ambiguous"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class ScopeValidation:
    """Result of scope validation."""

    decision: ScopeDecision
    target: str
    reason: str
    requires_human_confirmation: bool = False


@dataclass(frozen=True)
class HumanConfirmationRequest:
    """Request for human confirmation on ambiguous scope."""

    target: str
    reason: str
    authorization_document: str
    requested_at: datetime


class LegalScopeValidator:
    """
    Validates that targets are within authorized scope.

    This validator ensures:
    - Target is covered by authorization document
    - Authorization has not expired
    - Target is not in excluded paths
    - Ambiguous cases require human confirmation

    ARCHITECTURAL CONSTRAINT:
    This validator causes HARD STOP on scope violations.
    Operating outside legal authorization is never acceptable.
    """

    def validate_target(
        self, target: str, auth_doc: AuthorizationDocument
    ) -> ScopeValidation:
        """
        Validate target is within authorized scope.

        Args:
            target: The target URL, domain, or IP to validate
            auth_doc: The authorization document

        Returns:
            ScopeValidation with decision and reason

        Raises:
            ScopeViolationError: If target is outside scope
            AuthorizationExpiredError: If authorization has expired
        """
        # Check authorization expiry first
        if auth_doc.is_expired:
            raise AuthorizationExpiredError(
                f"Authorization for {auth_doc.program_name} expired on "
                f"{auth_doc.valid_until.isoformat()}. "
                f"Renew authorization before proceeding."
            )

        # Check if authorization is active
        if not auth_doc.is_active:
            raise AuthorizationExpiredError(
                f"Authorization for {auth_doc.program_name} is not yet active. "
                f"Valid from {auth_doc.valid_from.isoformat()}."
            )

        # Parse target to extract domain/IP
        parsed = self._parse_target(target)

        # Check if target is in excluded paths
        if self._is_excluded(parsed, auth_doc):
            raise ScopeViolationError(
                f"Target {target} is in excluded paths for {auth_doc.program_name}. "
                f"This target is explicitly out of scope."
            )

        # Check if target is in authorized domains
        if self._is_authorized_domain(parsed, auth_doc):
            return ScopeValidation(
                decision=ScopeDecision.IN_SCOPE,
                target=target,
                reason=f"Target {target} is in authorized domains for {auth_doc.program_name}",
            )

        # Check if target is in authorized IP ranges
        if self._is_authorized_ip(parsed, auth_doc):
            return ScopeValidation(
                decision=ScopeDecision.IN_SCOPE,
                target=target,
                reason=f"Target {target} is in authorized IP ranges for {auth_doc.program_name}",
            )

        # Check if scope is ambiguous
        if self._is_ambiguous(parsed, auth_doc):
            return ScopeValidation(
                decision=ScopeDecision.AMBIGUOUS,
                target=target,
                reason=f"Target {target} scope is ambiguous for {auth_doc.program_name}. "
                f"Human confirmation required.",
                requires_human_confirmation=True,
            )

        # Target is out of scope
        raise ScopeViolationError(
            f"Target {target} is outside authorized scope for {auth_doc.program_name}. "
            f"Authorized domains: {', '.join(auth_doc.authorized_domains)}. "
            f"Authorized IP ranges: {', '.join(auth_doc.authorized_ip_ranges)}."
        )

    def _parse_target(self, target: str) -> dict:
        """Parse target into components."""
        result = {
            "original": target,
            "domain": None,
            "ip": None,
            "path": None,
        }

        # Try to parse as URL
        if "://" in target:
            parsed = urlparse(target)
            result["domain"] = parsed.netloc.split(":")[0]  # Remove port
            result["path"] = parsed.path
        else:
            # Try to parse as IP
            try:
                ipaddress.ip_address(target)
                result["ip"] = target
            except ValueError:
                # Assume it's a domain
                result["domain"] = target.split(":")[0]  # Remove port if present

        return result

    def _is_excluded(self, parsed: dict, auth_doc: AuthorizationDocument) -> bool:
        """Check if target is in excluded paths."""
        path = parsed.get("path", "")
        domain = parsed.get("domain", "")

        for excluded in auth_doc.excluded_paths:
            # Check path exclusion
            if path and fnmatch.fnmatch(path, excluded):
                return True
            # Check domain exclusion
            if domain and fnmatch.fnmatch(domain, excluded):
                return True
            # Check full target exclusion
            if fnmatch.fnmatch(parsed["original"], excluded):
                return True

        return False

    def _is_authorized_domain(
        self, parsed: dict, auth_doc: AuthorizationDocument
    ) -> bool:
        """Check if target domain is authorized."""
        domain = parsed.get("domain")
        if not domain:
            return False

        for authorized in auth_doc.authorized_domains:
            # Exact match
            if domain == authorized:
                return True
            # Wildcard match (e.g., *.example.com)
            if authorized.startswith("*."):
                base_domain = authorized[2:]
                if domain == base_domain or domain.endswith("." + base_domain):
                    return True
            # Subdomain match
            if domain.endswith("." + authorized):
                return True

        return False

    def _is_authorized_ip(self, parsed: dict, auth_doc: AuthorizationDocument) -> bool:
        """Check if target IP is in authorized ranges."""
        ip_str = parsed.get("ip")
        if not ip_str:
            return False

        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False

        for range_str in auth_doc.authorized_ip_ranges:
            try:
                # Try as network
                network = ipaddress.ip_network(range_str, strict=False)
                if ip in network:
                    return True
            except ValueError:
                # Try as single IP
                try:
                    if ip == ipaddress.ip_address(range_str):
                        return True
                except ValueError:
                    continue

        return False

    def _is_ambiguous(self, parsed: dict, auth_doc: AuthorizationDocument) -> bool:
        """Check if scope determination is ambiguous."""
        domain = parsed.get("domain")
        if not domain:
            return False

        # Check for partial matches that might be ambiguous
        for authorized in auth_doc.authorized_domains:
            # Similar domain names might be ambiguous
            if authorized in domain or domain in authorized:
                if domain != authorized:
                    return True

        return False

    def is_ambiguous(self, target: str, auth_doc: AuthorizationDocument) -> bool:
        """
        Check if scope determination is ambiguous (requires human).

        Args:
            target: The target to check
            auth_doc: The authorization document

        Returns:
            True if scope is ambiguous and requires human confirmation
        """
        parsed = self._parse_target(target)
        return self._is_ambiguous(parsed, auth_doc)

    def require_human_confirmation(
        self, target: str, reason: str
    ) -> HumanConfirmationRequest:
        """
        Request human confirmation for ambiguous scope.

        Args:
            target: The target requiring confirmation
            reason: Why confirmation is needed

        Returns:
            HumanConfirmationRequest for the human to review
        """
        return HumanConfirmationRequest(
            target=target,
            reason=reason,
            authorization_document="See authorization document for details",
            requested_at=datetime.now(timezone.utc),
        )

    def check_authorization_valid(self, auth_doc: AuthorizationDocument) -> bool:
        """
        Check if authorization document is currently valid.

        Args:
            auth_doc: The authorization document

        Returns:
            True if authorization is active and not expired
        """
        return auth_doc.is_active and not auth_doc.is_expired
