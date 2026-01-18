"""
Phase-9 Scope Checker

Read-only scope validation that WARNS but NEVER blocks.

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- READ-ONLY access to scope data
- WARNS only, NEVER blocks navigation
- Does NOT prevent testing
- Does NOT make scope decisions
- Does NOT modify authorization data

Human decides whether to proceed.

Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Set
import uuid
import fnmatch
from urllib.parse import urlparse
import ipaddress

from browser_assistant.types import (
    ScopeWarning,
)
from browser_assistant.boundaries import Phase9BoundaryGuard


class ScopeChecker:
    """
    Read-only scope validation.
    
    SECURITY: This checker WARNS only. It NEVER:
    - Blocks navigation
    - Prevents testing
    - Makes scope decisions
    - Modifies authorization data
    - Enforces scope boundaries
    
    Human decides whether to proceed.
    
    IMPORTANT: Scope warnings are ADVISORY only.
    - Human may have additional authorization
    - Human may be testing scope boundaries intentionally
    - Human decides whether to proceed
    
    FORBIDDEN METHODS (do not add):
    - block_navigation()
    - prevent_testing()
    - enforce_scope()
    - deny_access()
    - is_authorized() - returns boolean certainty
    """
    
    def __init__(
        self,
        authorized_domains: Optional[List[str]] = None,
        authorized_ip_ranges: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the scope checker.
        
        Args:
            authorized_domains: List of authorized domains (e.g., ["*.example.com"]).
            authorized_ip_ranges: List of authorized IP ranges (e.g., ["10.0.0.0/8"]).
            excluded_paths: List of excluded paths (e.g., ["/admin/*"]).
        """
        Phase9BoundaryGuard.assert_read_only_access()
        Phase9BoundaryGuard.assert_human_confirmation_required()
        
        self._authorized_domains: Set[str] = set(authorized_domains or [])
        self._authorized_ip_ranges: Set[str] = set(authorized_ip_ranges or [])
        self._excluded_paths: Set[str] = set(excluded_paths or [])
    
    def check_scope(
        self,
        url: str,
        authorization_reference: Optional[str] = None,
    ) -> ScopeWarning:
        """
        Check if URL is within known scope.
        
        Args:
            url: URL to check.
            authorization_reference: Optional reference to authorization document.
            
        Returns:
            ScopeWarning with scope status and message.
            
        NOTE: This method NEVER blocks. It returns a warning for
        human interpretation. Even if out of scope, the human
        decides whether to proceed.
        
        IMPORTANT: Scope status is ADVISORY only.
        - Human may have additional authorization
        - Human may be testing scope boundaries intentionally
        - Human decides whether to proceed
        """
        parsed = self._parse_url(url)
        domain = parsed.get("domain")
        path = parsed.get("path", "")
        ip = parsed.get("ip")
        
        # Check if in excluded paths
        if self._is_excluded(path, domain):
            return ScopeWarning(
                warning_id=str(uuid.uuid4()),
                url=url,
                scope_status="excluded",
                warning_message=(
                    f"URL path appears to be in excluded paths. "
                    f"Human verification required before proceeding."
                ),
                authorization_reference=authorization_reference,
                timestamp=datetime.now(),
                human_confirmation_required=True,
                does_not_block=True,
                is_advisory_only=True,
            )
        
        # Check if domain is authorized
        if domain and self._is_authorized_domain(domain):
            return ScopeWarning(
                warning_id=str(uuid.uuid4()),
                url=url,
                scope_status="in_scope",
                warning_message=(
                    f"URL appears to be within authorized scope. "
                    f"Human verification still recommended."
                ),
                authorization_reference=authorization_reference,
                timestamp=datetime.now(),
                human_confirmation_required=True,
                does_not_block=True,
                is_advisory_only=True,
            )
        
        # Check if IP is authorized
        if ip and self._is_authorized_ip(ip):
            return ScopeWarning(
                warning_id=str(uuid.uuid4()),
                url=url,
                scope_status="in_scope",
                warning_message=(
                    f"IP appears to be within authorized range. "
                    f"Human verification still recommended."
                ),
                authorization_reference=authorization_reference,
                timestamp=datetime.now(),
                human_confirmation_required=True,
                does_not_block=True,
                is_advisory_only=True,
            )
        
        # Check if scope is ambiguous
        if domain and self._is_ambiguous(domain):
            return ScopeWarning(
                warning_id=str(uuid.uuid4()),
                url=url,
                scope_status="ambiguous",
                warning_message=(
                    f"Scope status is ambiguous for this URL. "
                    f"Human verification required before proceeding."
                ),
                authorization_reference=authorization_reference,
                timestamp=datetime.now(),
                human_confirmation_required=True,
                does_not_block=True,
                is_advisory_only=True,
            )
        
        # No scope information available or out of scope
        if not self._authorized_domains and not self._authorized_ip_ranges:
            return ScopeWarning(
                warning_id=str(uuid.uuid4()),
                url=url,
                scope_status="unknown",
                warning_message=(
                    f"No scope information configured. "
                    f"Human must verify authorization before testing."
                ),
                authorization_reference=authorization_reference,
                timestamp=datetime.now(),
                human_confirmation_required=True,
                does_not_block=True,
                is_advisory_only=True,
            )
        
        return ScopeWarning(
            warning_id=str(uuid.uuid4()),
            url=url,
            scope_status="out_of_scope",
            warning_message=(
                f"URL does not appear to be within configured scope. "
                f"Human verification required - you may have additional authorization."
            ),
            authorization_reference=authorization_reference,
            timestamp=datetime.now(),
            human_confirmation_required=True,
            does_not_block=True,
            is_advisory_only=True,
        )
    
    def add_authorized_domain(self, domain: str) -> None:
        """Add a domain to authorized list."""
        self._authorized_domains.add(domain)
    
    def add_authorized_ip_range(self, ip_range: str) -> None:
        """Add an IP range to authorized list."""
        self._authorized_ip_ranges.add(ip_range)
    
    def add_excluded_path(self, path: str) -> None:
        """Add a path to excluded list."""
        self._excluded_paths.add(path)
    
    def get_scope_summary(self) -> str:
        """Get summary of configured scope."""
        parts = []
        
        if self._authorized_domains:
            parts.append(f"Authorized domains: {', '.join(sorted(self._authorized_domains))}")
        else:
            parts.append("No authorized domains configured")
        
        if self._authorized_ip_ranges:
            parts.append(f"Authorized IP ranges: {', '.join(sorted(self._authorized_ip_ranges))}")
        else:
            parts.append("No authorized IP ranges configured")
        
        if self._excluded_paths:
            parts.append(f"Excluded paths: {', '.join(sorted(self._excluded_paths))}")
        else:
            parts.append("No excluded paths configured")
        
        return "\n".join(parts)
    
    def _parse_url(self, url: str) -> dict:
        """Parse URL into components."""
        result = {
            "original": url,
            "domain": None,
            "ip": None,
            "path": None,
        }
        
        if "://" in url:
            parsed = urlparse(url)
            host = parsed.netloc.split(":")[0]  # Remove port
            result["path"] = parsed.path
            
            # Check if host is IP
            try:
                ipaddress.ip_address(host)
                result["ip"] = host
            except ValueError:
                result["domain"] = host
        else:
            # Try as IP
            try:
                ipaddress.ip_address(url.split(":")[0])
                result["ip"] = url.split(":")[0]
            except ValueError:
                result["domain"] = url.split(":")[0]
        
        return result
    
    def _is_excluded(self, path: str, domain: Optional[str]) -> bool:
        """Check if path or domain is excluded."""
        for excluded in self._excluded_paths:
            if path and fnmatch.fnmatch(path, excluded):
                return True
            if domain and fnmatch.fnmatch(domain, excluded):
                return True
        return False
    
    def _is_authorized_domain(self, domain: str) -> bool:
        """Check if domain is authorized."""
        for authorized in self._authorized_domains:
            # Exact match
            if domain == authorized:
                return True
            # Wildcard match
            if authorized.startswith("*."):
                base = authorized[2:]
                if domain == base or domain.endswith("." + base):
                    return True
            # Subdomain match
            if domain.endswith("." + authorized):
                return True
        return False
    
    def _is_authorized_ip(self, ip_str: str) -> bool:
        """Check if IP is in authorized ranges."""
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        
        for range_str in self._authorized_ip_ranges:
            try:
                network = ipaddress.ip_network(range_str, strict=False)
                if ip in network:
                    return True
            except ValueError:
                try:
                    if ip == ipaddress.ip_address(range_str):
                        return True
                except ValueError:
                    continue
        return False
    
    def _is_ambiguous(self, domain: str) -> bool:
        """Check if scope is ambiguous."""
        for authorized in self._authorized_domains:
            # Similar domain names might be ambiguous
            if authorized in domain or domain in authorized:
                if domain != authorized:
                    return True
        return False
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    #
    # - block_navigation() - Phase-9 NEVER blocks
    # - prevent_testing() - Phase-9 NEVER prevents
    # - enforce_scope() - Phase-9 NEVER enforces
    # - deny_access() - Phase-9 NEVER denies
    # - is_authorized() - Phase-9 NEVER returns boolean certainty
    # - require_authorization() - Phase-9 NEVER requires
    # - validate_scope() - Phase-9 NEVER validates (only warns)
    # ========================================================================
