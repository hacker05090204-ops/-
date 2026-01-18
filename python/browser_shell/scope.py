# PHASE-13 GOVERNANCE COMPLIANCE
# This module is part of Phase-13 (Controlled Bug Bounty Browser Shell)
#
# FORBIDDEN CAPABILITIES:
# - NO automation logic
# - NO execution authority
# - NO decision authority
# - NO learning or personalization
# - NO audit modification
# - NO scope expansion
# - NO session extension
# - NO batch approvals
# - NO scheduled actions
# - NO wildcards, regex, or implicit patterns
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.

"""
Scope Enforcement for Phase-13 Browser Shell.

Requirement: 2.1, 2.2, 2.3 (Scope Enforcement)

This module provides scope parsing, validation, and enforcement.
- Only explicit, enumerated target lists accepted
- NO wildcards, NO regex, NO inheritance
- Scope is IMMUTABLE within a session
- All out-of-scope requests are BLOCKED

FORBIDDEN METHODS (not implemented):
- auto_*, expand_*, bypass_*, skip_*, override_*, learn_*
"""

import hashlib
import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from browser_shell.audit_storage import AuditStorage
from browser_shell.audit_types import AuditEntry, Initiator, ActionType
from browser_shell.hash_chain import HashChain


@dataclass(frozen=True)
class ScopeParseResult:
    """
    Result of scope parsing.
    
    Immutable to prevent tampering.
    """
    valid: bool
    targets: tuple = ()  # Tuple for immutability
    error_message: str = ""


@dataclass(frozen=True)
class ScopeActivationResult:
    """
    Result of scope activation.
    
    Immutable to prevent tampering.
    """
    success: bool
    scope_hash: str = ""
    error_message: str = ""


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of request validation against scope.
    
    Immutable to prevent tampering.
    """
    allowed: bool
    blocked: bool = False
    block_reason: str = ""


class ScopeParser:
    """
    Parser for scope definitions.
    
    Per Requirement 2.1 (Scope Definition):
    - Accepts ONLY explicit, enumerated target lists
    - REJECTS wildcards (*, ?)
    - REJECTS regex patterns
    - REJECTS inheritance markers
    
    FORBIDDEN PATTERNS:
    - * (asterisk wildcard)
    - ? (question mark wildcard)
    - Regex special characters: \\ [ ] ^ $ | + { }
    - "includes subdomains", "all subdomains"
    """
    
    # Forbidden patterns that indicate wildcards or regex
    FORBIDDEN_PATTERNS = [
        r'\*',           # Asterisk wildcard
        r'\?',           # Question mark wildcard
        r'\\',           # Escape sequences (regex)
        r'\[',           # Character class (regex)
        r'\]',           # Character class (regex)
        r'\^',           # Start anchor (regex)
        r'\$',           # End anchor (regex)
        r'\|',           # Alternation (regex)
        r'\+',           # One or more (regex)
        r'\{',           # Quantifier (regex)
        r'\}',           # Quantifier (regex)
    ]
    
    # Forbidden keywords that indicate inheritance
    FORBIDDEN_KEYWORDS = [
        'includes subdomains',
        'all subdomains',
        'and subdomains',
        'with subdomains',
        'subdomain',
    ]
    
    def parse(self, scope_definition: str) -> ScopeParseResult:
        """
        Parse a scope definition.
        
        Args:
            scope_definition: Comma-separated list of explicit targets.
        
        Returns:
            ScopeParseResult indicating validity and parsed targets.
        """
        if not scope_definition or not scope_definition.strip():
            return ScopeParseResult(
                valid=False,
                error_message="Scope definition cannot be empty.",
            )
        
        # Check for forbidden keywords (inheritance)
        lower_scope = scope_definition.lower()
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in lower_scope:
                return ScopeParseResult(
                    valid=False,
                    error_message=f"Scope contains forbidden inheritance marker: '{keyword}'. "
                                  "Only explicit targets are allowed.",
                )
        
        # Check for forbidden patterns (wildcards, regex)
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, scope_definition):
                return ScopeParseResult(
                    valid=False,
                    error_message=f"Scope contains forbidden wildcard or regex pattern. "
                                  "Only explicit targets are allowed.",
                )
        
        # Parse comma-separated targets
        targets = []
        for target in scope_definition.split(','):
            target = target.strip()
            if target:
                # Validate target format (basic domain validation)
                if not self._is_valid_target(target):
                    return ScopeParseResult(
                        valid=False,
                        error_message=f"Invalid target format: '{target}'",
                    )
                targets.append(target)
        
        if not targets:
            return ScopeParseResult(
                valid=False,
                error_message="No valid targets found in scope definition.",
            )
        
        return ScopeParseResult(
            valid=True,
            targets=tuple(targets),
        )
    
    def _is_valid_target(self, target: str) -> bool:
        """
        Validate a single target.
        
        Basic validation - must look like a domain or IP.
        """
        # Must have at least one dot (domain) or be an IP
        if '.' not in target:
            return False
        
        # Must not be empty parts
        parts = target.split('.')
        if any(not part for part in parts):
            return False
        
        return True


class ScopeValidator:
    """
    Validator for scope enforcement.
    
    Per Requirement 2.2 (Scope Enforcement):
    - Every request validated against active scope BEFORE execution
    - Out-of-scope requests BLOCKED (not just logged)
    - NO bypass mechanism exists
    - All validation results logged to audit trail
    
    Per Requirement 2.3 (Scope Immutability):
    - NO scope modification within active session
    - Scope change requires session termination + new session
    
    FORBIDDEN METHODS (not implemented):
    - bypass_*, skip_*, override_*, expand_*, auto_*, learn_*
    """
    
    def __init__(
        self,
        storage: AuditStorage,
        hash_chain: HashChain,
    ) -> None:
        self._storage = storage
        self._hash_chain = hash_chain
        self._parser = ScopeParser()
        
        # Active scopes per session (session_id -> set of targets)
        self._active_scopes: Dict[str, Set[str]] = {}
        self._scope_hashes: Dict[str, str] = {}
    
    def activate_scope(
        self,
        scope_definition: str,
        session_id: str,
        human_confirmed: bool,
    ) -> ScopeActivationResult:
        """
        Activate a scope for a session.
        
        Per Requirement 2.1 (Scope Definition):
        - Scope displayed for human review before activation
        - Scope requires human confirmation
        
        Per Requirement 2.3 (Scope Immutability):
        - NO scope modification within active session
        
        Args:
            scope_definition: The scope to activate.
            session_id: The session to activate scope for.
            human_confirmed: Must be True to activate.
        
        Returns:
            ScopeActivationResult indicating success or failure.
        """
        # Check human confirmation
        if not human_confirmed:
            return ScopeActivationResult(
                success=False,
                error_message="Human confirmation is required to activate scope.",
            )
        
        # Check if session already has active scope (immutability)
        if session_id in self._active_scopes:
            return ScopeActivationResult(
                success=False,
                error_message="Scope is immutable within session. "
                              "Session already has active scope. "
                              "Terminate session and create new session for different scope.",
            )
        
        # Parse scope
        parse_result = self._parser.parse(scope_definition)
        if not parse_result.valid:
            return ScopeActivationResult(
                success=False,
                error_message=parse_result.error_message,
            )
        
        # Compute scope hash
        scope_hash = hashlib.sha256(scope_definition.encode()).hexdigest()
        
        # Log to audit trail
        self._log_scope_action(
            action_type=ActionType.SCOPE_DEFINED.value,
            session_id=session_id,
            scope_hash=scope_hash,
            details=f"Scope activated: {scope_definition}",
            outcome="SUCCESS",
        )
        
        # Store active scope
        self._active_scopes[session_id] = set(parse_result.targets)
        self._scope_hashes[session_id] = scope_hash
        
        return ScopeActivationResult(
            success=True,
            scope_hash=scope_hash,
        )
    
    def deactivate_scope(self, session_id: str) -> bool:
        """
        Deactivate scope for a session.
        
        Called when session terminates.
        """
        if session_id in self._active_scopes:
            del self._active_scopes[session_id]
        if session_id in self._scope_hashes:
            del self._scope_hashes[session_id]
        return True
    
    def validate_request(
        self,
        target: str,
        session_id: str,
    ) -> ValidationResult:
        """
        Validate a request against active scope.
        
        Per Requirement 2.2 (Scope Enforcement):
        - Every request validated BEFORE execution
        - Out-of-scope requests BLOCKED
        - All validation results logged
        
        Args:
            target: The target of the request.
            session_id: The session making the request.
        
        Returns:
            ValidationResult indicating if request is allowed.
        
        STOP Condition: Out-of-scope request triggers session termination.
        """
        # Check if session has active scope
        if session_id not in self._active_scopes:
            self._log_scope_action(
                action_type=ActionType.SCOPE_VIOLATION.value,
                session_id=session_id,
                scope_hash="",
                details=f"Request to {target} blocked: No active scope for session",
                outcome="BLOCKED",
            )
            return ValidationResult(
                allowed=False,
                blocked=True,
                block_reason="No active scope for session.",
            )
        
        active_targets = self._active_scopes[session_id]
        scope_hash = self._scope_hashes.get(session_id, "")
        
        # Check if target is in scope
        if target in active_targets:
            self._log_scope_action(
                action_type=ActionType.SCOPE_VALIDATED.value,
                session_id=session_id,
                scope_hash=scope_hash,
                details=f"Request to {target} validated: In scope",
                outcome="SUCCESS",
            )
            return ValidationResult(
                allowed=True,
                blocked=False,
            )
        
        # Target not in scope - BLOCK
        self._log_scope_action(
            action_type=ActionType.SCOPE_VIOLATION.value,
            session_id=session_id,
            scope_hash=scope_hash,
            details=f"Request to {target} blocked: Out of scope",
            outcome="BLOCKED",
        )
        
        return ValidationResult(
            allowed=False,
            blocked=True,
            block_reason=f"Target '{target}' is out of scope. Request blocked.",
        )
    
    def _log_scope_action(
        self,
        action_type: str,
        session_id: str,
        scope_hash: str,
        details: str,
        outcome: str,
    ) -> None:
        """Log scope action to audit trail."""
        last_entry = self._storage.get_last_entry()
        previous_hash = last_entry.entry_hash if last_entry else HashChain.GENESIS_HASH
        
        entry_id = f"audit-{uuid.uuid4().hex[:12]}"
        entry_timestamp = self._hash_chain.get_external_timestamp()
        
        entry_hash = self._hash_chain.compute_entry_hash(
            entry_id=entry_id,
            timestamp=entry_timestamp,
            previous_hash=previous_hash,
            action_type=action_type,
            initiator=Initiator.SYSTEM.value,
            session_id=session_id,
            scope_hash=scope_hash,
            action_details=details,
            outcome=outcome,
        )
        
        audit_entry = AuditEntry(
            entry_id=entry_id,
            timestamp=entry_timestamp,
            previous_hash=previous_hash,
            action_type=action_type,
            initiator=Initiator.SYSTEM.value,
            session_id=session_id,
            scope_hash=scope_hash,
            action_details=details,
            outcome=outcome,
            entry_hash=entry_hash,
        )
        
        self._storage.append(audit_entry)
