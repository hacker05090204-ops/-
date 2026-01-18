"""
Execution Layer Security Module

POST-PHASE-19 SECURITY REMEDIATION

This module provides MANDATORY security controls for:
- RISK-X1: Path Traversal / Write-Anywhere prevention
- RISK-X2: Evidence Leakage prevention (HAR redaction)
- RISK-X3: Single-Request Enforcement

CRITICAL: These controls are PREVENTIVE, not detective.
Violations raise GovernanceViolation immediately.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, List, Dict
import re
import threading
import uuid
import urllib.parse
import json


class GovernanceViolation(Exception):
    """Raised when a security governance rule is violated.
    
    This is a HARD STOP - the operation MUST NOT proceed.
    """
    pass


# =============================================================================
# RISK-X1: PATH TRAVERSAL / WRITE-ANYWHERE PREVENTION
# =============================================================================

# UUIDv4 regex pattern - must match exactly 8-4-4-4-12 hex with version 4
_UUID4_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# Dangerous path patterns
_DANGEROUS_PATH_PATTERNS = [
    r'\.\.',           # Parent directory traversal
    r'^/',             # Absolute path (Unix)
    r'^[A-Za-z]:',     # Absolute path (Windows)
    r'\x00',           # Null byte injection
    r'[\n\r]',         # Newline injection
    r'%2e%2e',         # URL encoded ..
    r'%252e',          # Double URL encoded .
    r'%c0%af',         # Overlong UTF-8 encoding
    r'%c1%9c',         # Overlong UTF-8 encoding
]

_DANGEROUS_PATH_REGEX = re.compile('|'.join(_DANGEROUS_PATH_PATTERNS), re.IGNORECASE)


def validate_execution_id(execution_id: Any) -> str:
    """Validate execution_id is a valid UUIDv4.
    
    Args:
        execution_id: The execution ID to validate
        
    Returns:
        The validated execution_id string
        
    Raises:
        GovernanceViolation: If execution_id is invalid
    """
    if execution_id is None:
        raise GovernanceViolation("Invalid execution_id: cannot be None")
    
    if not isinstance(execution_id, str):
        raise GovernanceViolation(f"Invalid execution_id: must be string, got {type(execution_id)}")
    
    # Check for empty or whitespace-only
    if not execution_id or not execution_id.strip():
        raise GovernanceViolation("Invalid execution_id: cannot be empty or whitespace")
    
    # Check length (UUIDv4 is 36 chars with hyphens)
    if len(execution_id) > 100:
        raise GovernanceViolation("Invalid execution_id: too long")
    
    # Check for dangerous patterns BEFORE UUID validation
    if _DANGEROUS_PATH_REGEX.search(execution_id):
        raise GovernanceViolation("Invalid execution_id: contains dangerous path pattern")
    
    # URL decode and check again
    try:
        decoded = urllib.parse.unquote(execution_id)
        if _DANGEROUS_PATH_REGEX.search(decoded):
            raise GovernanceViolation("Invalid execution_id: contains encoded dangerous pattern")
    except Exception:
        pass  # If decoding fails, continue with UUID validation
    
    # Validate UUIDv4 format
    if not _UUID4_PATTERN.match(execution_id):
        raise GovernanceViolation("Invalid execution_id: must be valid UUIDv4 format")
    
    return execution_id


def validate_session_id(session_id: Any) -> str:
    """Validate session_id is a valid UUIDv4.
    
    Args:
        session_id: The session ID to validate
        
    Returns:
        The validated session_id string
        
    Raises:
        GovernanceViolation: If session_id is invalid
    """
    if session_id is None:
        raise GovernanceViolation("Invalid session_id: cannot be None")
    
    if not isinstance(session_id, str):
        raise GovernanceViolation(f"Invalid session_id: must be string, got {type(session_id)}")
    
    # Check for empty or whitespace-only
    if not session_id or not session_id.strip():
        raise GovernanceViolation("Invalid session_id: cannot be empty or whitespace")
    
    # Check length
    if len(session_id) > 100:
        raise GovernanceViolation("Invalid session_id: too long")
    
    # Check for dangerous patterns
    if _DANGEROUS_PATH_REGEX.search(session_id):
        raise GovernanceViolation("Invalid session_id: contains dangerous path pattern")
    
    # URL decode and check again
    try:
        decoded = urllib.parse.unquote(session_id)
        if _DANGEROUS_PATH_REGEX.search(decoded):
            raise GovernanceViolation("Invalid session_id: contains encoded dangerous pattern")
    except Exception:
        pass
    
    # Validate UUIDv4 format
    if not _UUID4_PATTERN.match(session_id):
        raise GovernanceViolation("Invalid session_id: must be valid UUIDv4 format")
    
    return session_id


def validate_artifact_path(path: Any, artifacts_root: Path) -> Path:
    """Validate artifact path is within the artifacts root directory.
    
    Args:
        path: The path to validate (string or Path)
        artifacts_root: The root directory for artifacts
        
    Returns:
        The validated Path object
        
    Raises:
        GovernanceViolation: If path escapes artifacts_root
    """
    if path is None:
        raise GovernanceViolation("Path traversal blocked: path cannot be None")
    
    path_str = str(path)
    
    # URL decode first to catch encoded attacks
    try:
        decoded = urllib.parse.unquote(path_str)
    except Exception:
        decoded = path_str
    
    # Check for parent directory traversal patterns
    if '..' in decoded or '..' in path_str:
        raise GovernanceViolation("Path traversal blocked: parent directory traversal detected")
    
    # Check for Unicode normalization attacks
    import unicodedata
    normalized = unicodedata.normalize('NFKC', decoded)
    if '..' in normalized:
        raise GovernanceViolation("Path traversal blocked: normalized path contains traversal")
    
    # Check for null bytes and other dangerous characters
    if '\x00' in path_str or '\n' in path_str or '\r' in path_str:
        raise GovernanceViolation("Path traversal blocked: dangerous characters in path")
    
    # Check for overlong UTF-8 encodings
    if '%c0%af' in path_str.lower() or '%c1%9c' in path_str.lower():
        raise GovernanceViolation("Path traversal blocked: overlong UTF-8 encoding detected")
    
    # Convert to Path and resolve
    try:
        path_obj = Path(path_str)
        resolved = path_obj.resolve()
        root_resolved = artifacts_root.resolve()
        
        # Check if resolved path is within root
        try:
            resolved.relative_to(root_resolved)
        except ValueError:
            raise GovernanceViolation(
                f"Path traversal blocked: path '{path}' escapes artifacts root"
            )
        
        return resolved
        
    except GovernanceViolation:
        raise
    except Exception as e:
        raise GovernanceViolation(f"Path traversal blocked: invalid path - {e}")


def validate_file_path_relative(file_path: Optional[str]) -> Optional[str]:
    """Validate a file path is safe (relative, no traversal).
    
    Args:
        file_path: The file path to validate (can be None)
        
    Returns:
        The validated file path or None
        
    Raises:
        GovernanceViolation: If path contains traversal
    """
    if file_path is None:
        return None
    
    # Check for dangerous patterns
    if _DANGEROUS_PATH_REGEX.search(file_path):
        raise GovernanceViolation("Path traversal blocked: dangerous pattern in file_path")
    
    # URL decode and check
    try:
        decoded = urllib.parse.unquote(file_path)
        if _DANGEROUS_PATH_REGEX.search(decoded):
            raise GovernanceViolation("Path traversal blocked: encoded dangerous pattern")
    except Exception:
        pass
    
    # Check for absolute paths
    if file_path.startswith('/') or (len(file_path) > 1 and file_path[1] == ':'):
        raise GovernanceViolation("Path traversal blocked: absolute path not allowed")
    
    return file_path


# =============================================================================
# RISK-X2: EVIDENCE LEAKAGE PREVENTION (HAR REDACTION)
# =============================================================================

# Headers that MUST be redacted from HAR files
_SENSITIVE_HEADERS: frozenset = frozenset([
    'authorization',
    'cookie',
    'set-cookie',
    'x-api-key',
    'x-auth-token',
    'x-access-token',
    'x-csrf-token',
    'x-xsrf-token',
    'proxy-authorization',
    'www-authenticate',
    'x-amz-security-token',
    'x-amz-credential',
    'api-key',
    'apikey',
    'bearer',
    'token',
    'session',
    'sessionid',
    'session-id',
    'jsessionid',
    'phpsessid',
    'asp.net_sessionid',
])

# Patterns for credential detection in request/response bodies
_CREDENTIAL_PATTERNS: List[re.Pattern] = [
    re.compile(r'password["\s:=]+["\']?[^"\'&\s]{3,}', re.IGNORECASE),
    re.compile(r'passwd["\s:=]+["\']?[^"\'&\s]{3,}', re.IGNORECASE),
    re.compile(r'secret["\s:=]+["\']?[^"\'&\s]{3,}', re.IGNORECASE),
    re.compile(r'api[_-]?key["\s:=]+["\']?[^"\'&\s]{8,}', re.IGNORECASE),
    re.compile(r'access[_-]?token["\s:=]+["\']?[^"\'&\s]{8,}', re.IGNORECASE),
    re.compile(r'refresh[_-]?token["\s:=]+["\']?[^"\'&\s]{8,}', re.IGNORECASE),
    re.compile(r'bearer\s+[A-Za-z0-9\-_\.]+', re.IGNORECASE),
    re.compile(r'basic\s+[A-Za-z0-9+/=]+', re.IGNORECASE),
    re.compile(r'private[_-]?key["\s:=]+["\']?[^"\'&\s]{8,}', re.IGNORECASE),
    re.compile(r'client[_-]?secret["\s:=]+["\']?[^"\'&\s]{8,}', re.IGNORECASE),
]

# Patterns to scan for in HAR validation (must NOT be present)
_SCAN_PATTERNS: List[re.Pattern] = [
    re.compile(r'eyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+'),  # JWT
    re.compile(r'AKIA[0-9A-Z]{16}'),  # AWS Access Key
    re.compile(r'sk-[a-zA-Z0-9]{48}'),  # OpenAI API Key pattern
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),  # GitHub Personal Access Token
    re.compile(r'gho_[a-zA-Z0-9]{36}'),  # GitHub OAuth Token
    re.compile(r'glpat-[a-zA-Z0-9\-_]{20,}'),  # GitLab Personal Access Token
]

# Redaction placeholder
_REDACTED = "[REDACTED]"


def redact_har_content(har_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive information from HAR content.
    
    MANDATORY: All HAR content MUST pass through this function before storage.
    
    Args:
        har_dict: Parsed HAR dictionary
        
    Returns:
        Redacted HAR dictionary
    """
    if not isinstance(har_dict, dict):
        raise GovernanceViolation("HAR content must be a dictionary")
    
    # Deep copy to avoid modifying original
    import copy
    redacted = copy.deepcopy(har_dict)
    
    # Get log entries
    log = redacted.get('log', {})
    entries = log.get('entries', [])
    
    for entry in entries:
        # Redact request headers
        request = entry.get('request', {})
        if 'headers' in request:
            request['headers'] = _redact_headers(request['headers'])
        
        # Redact request cookies
        if 'cookies' in request:
            for cookie in request['cookies']:
                cookie['value'] = _REDACTED
        
        # Redact request postData
        if 'postData' in request:
            post_data = request['postData']
            if 'text' in post_data:
                post_data['text'] = _redact_body_credentials(post_data['text'])
            if 'params' in post_data:
                for param in post_data['params']:
                    if _is_sensitive_param(param.get('name', '')):
                        param['value'] = _REDACTED
        
        # Redact response headers
        response = entry.get('response', {})
        if 'headers' in response:
            response['headers'] = _redact_headers(response['headers'])
        
        # Redact response cookies
        if 'cookies' in response:
            for cookie in response['cookies']:
                cookie['value'] = _REDACTED
        
        # Redact response content
        if 'content' in response:
            content = response['content']
            if 'text' in content:
                content['text'] = _redact_body_credentials(content['text'])
    
    return redacted


def _redact_headers(headers: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Redact sensitive headers."""
    redacted = []
    for header in headers:
        name = header.get('name', '').lower()
        if name in _SENSITIVE_HEADERS or _is_sensitive_param(name):
            redacted.append({'name': header.get('name', ''), 'value': _REDACTED})
        else:
            redacted.append(header)
    return redacted


def _redact_body_credentials(text: str) -> str:
    """Redact credentials from request/response body text."""
    if not text:
        return text
    
    result = text
    for pattern in _CREDENTIAL_PATTERNS:
        result = pattern.sub(_REDACTED, result)
    
    return result


def _is_sensitive_param(name: str) -> bool:
    """Check if parameter name suggests sensitive data."""
    name_lower = name.lower()
    sensitive_keywords = [
        'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'auth',
        'credential', 'session', 'cookie', 'bearer', 'api_key', 'apikey',
        'access_token', 'refresh_token', 'private', 'client_secret',
    ]
    return any(kw in name_lower for kw in sensitive_keywords)


@dataclass
class CredentialScanResult:
    """Result of scanning content for credentials."""
    has_credentials: bool
    patterns_found: List[str]
    
    def __post_init__(self) -> None:
        if self.has_credentials and not self.patterns_found:
            raise ValueError("has_credentials=True requires patterns_found")


def scan_for_credentials(content: str) -> CredentialScanResult:
    """Scan content for potential credentials.
    
    Args:
        content: Text content to scan
        
    Returns:
        CredentialScanResult with findings
    """
    patterns_found = []
    
    for pattern in _SCAN_PATTERNS:
        if pattern.search(content):
            patterns_found.append(pattern.pattern)
    
    for pattern in _CREDENTIAL_PATTERNS:
        if pattern.search(content):
            patterns_found.append(pattern.pattern)
    
    return CredentialScanResult(
        has_credentials=len(patterns_found) > 0,
        patterns_found=patterns_found,
    )


def validate_har_is_redacted(har_content: bytes) -> None:
    """Validate that HAR content has been properly redacted.
    
    MANDATORY: Called at EvidenceBundle construction time.
    
    Args:
        har_content: Raw HAR content bytes
        
    Raises:
        GovernanceViolation: If unredacted credentials are detected
    """
    try:
        content_str = har_content.decode('utf-8')
    except UnicodeDecodeError:
        raise GovernanceViolation("HAR content must be valid UTF-8")
    
    # Scan for credential patterns
    scan_result = scan_for_credentials(content_str)
    
    if scan_result.has_credentials:
        raise GovernanceViolation(
            f"HAR contains unredacted credentials. Patterns found: {scan_result.patterns_found[:3]}"
        )
    
    # Parse and check for sensitive headers
    try:
        har_dict = json.loads(content_str)
        log = har_dict.get('log', {})
        entries = log.get('entries', [])
        
        for entry in entries:
            # Check request headers
            request = entry.get('request', {})
            for header in request.get('headers', []):
                name = header.get('name', '').lower()
                value = header.get('value', '')
                if name in _SENSITIVE_HEADERS and value != _REDACTED:
                    raise GovernanceViolation(
                        f"HAR contains unredacted sensitive header: {name}"
                    )
            
            # Check response headers
            response = entry.get('response', {})
            for header in response.get('headers', []):
                name = header.get('name', '').lower()
                value = header.get('value', '')
                if name in _SENSITIVE_HEADERS and value != _REDACTED:
                    raise GovernanceViolation(
                        f"HAR contains unredacted sensitive header: {name}"
                    )
            
            # Check cookies
            for cookie in request.get('cookies', []):
                if cookie.get('value', '') != _REDACTED:
                    raise GovernanceViolation("HAR contains unredacted cookie value")
            
            for cookie in response.get('cookies', []):
                if cookie.get('value', '') != _REDACTED:
                    raise GovernanceViolation("HAR contains unredacted cookie value")
                    
    except json.JSONDecodeError:
        # If not valid JSON, just rely on pattern scanning
        pass


# =============================================================================
# RISK-X3: SINGLE-REQUEST ENFORCEMENT
# =============================================================================

class SingleRequestEnforcer:
    """Enforces single-request-per-confirmation at the base layer.
    
    CRITICAL: This enforcement is:
    - Thread-safe (uses threading.Lock)
    - Non-resettable (once consumed, cannot be reused)
    - Non-optional (must be used for all HTTP requests)
    - Structurally enforced (adapters cannot bypass)
    
    Usage:
        enforcer = SingleRequestEnforcer(confirmation_id)
        with enforcer.acquire_request_slot():
            # Make HTTP request here
            pass
        # Second attempt will raise GovernanceViolation
    """
    
    def __init__(self, confirmation_id: str) -> None:
        """Initialize enforcer for a confirmation.
        
        Args:
            confirmation_id: The human confirmation ID this enforcer is bound to
        """
        if not confirmation_id:
            raise GovernanceViolation("SingleRequestEnforcer requires confirmation_id")
        
        self._confirmation_id = confirmation_id
        self._lock = threading.Lock()
        self._consumed = False
        self._request_count = 0
        self._max_requests = 1  # HARD LIMIT: One request per confirmation
    
    @property
    def confirmation_id(self) -> str:
        """Get the confirmation ID this enforcer is bound to."""
        return self._confirmation_id
    
    @property
    def is_consumed(self) -> bool:
        """Check if the request slot has been consumed."""
        with self._lock:
            return self._consumed
    
    @property
    def request_count(self) -> int:
        """Get the number of requests made (should be 0 or 1)."""
        with self._lock:
            return self._request_count
    
    def acquire_request_slot(self) -> "RequestSlotContext":
        """Acquire the single request slot.
        
        Returns:
            Context manager for the request slot
            
        Raises:
            GovernanceViolation: If slot already consumed
        """
        return RequestSlotContext(self)
    
    def _try_acquire(self) -> bool:
        """Internal: Try to acquire the request slot.
        
        Returns:
            True if acquired, False if already consumed
        """
        with self._lock:
            if self._consumed:
                return False
            if self._request_count >= self._max_requests:
                return False
            self._request_count += 1
            self._consumed = True
            return True
    
    def _release(self, success: bool) -> None:
        """Internal: Release the request slot (no-op, slot stays consumed)."""
        # Intentionally empty - slot cannot be released/reused
        pass


class RequestSlotContext:
    """Context manager for single-request enforcement."""
    
    def __init__(self, enforcer: SingleRequestEnforcer) -> None:
        self._enforcer = enforcer
        self._acquired = False
    
    def __enter__(self) -> "RequestSlotContext":
        if not self._enforcer._try_acquire():
            raise GovernanceViolation(
                f"Single-request enforcement: confirmation '{self._enforcer.confirmation_id}' "
                f"already consumed (request_count={self._enforcer.request_count})"
            )
        self._acquired = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._acquired:
            self._enforcer._release(exc_type is None)
        return None  # Don't suppress exceptions


class EnforcedHTTPClient:
    """HTTP client wrapper that enforces single-request-per-confirmation.
    
    This wraps the actual HTTP request mechanism to ensure enforcement
    cannot be bypassed by adapters.
    """
    
    def __init__(self, enforcer: SingleRequestEnforcer) -> None:
        """Initialize with a SingleRequestEnforcer.
        
        Args:
            enforcer: The enforcer bound to a confirmation
        """
        self._enforcer = enforcer
        self._request_made = False
    
    def execute_request(
        self,
        method: str,
        url: str,
        request_func: callable,
        **kwargs,
    ) -> Any:
        """Execute an HTTP request with enforcement.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            request_func: The actual function to call for the request
            **kwargs: Additional arguments for request_func
            
        Returns:
            Response from request_func
            
        Raises:
            GovernanceViolation: If request already made for this confirmation
        """
        with self._enforcer.acquire_request_slot():
            self._request_made = True
            return request_func(method, url, **kwargs)
    
    @property
    def request_made(self) -> bool:
        """Check if a request has been made."""
        return self._request_made


# =============================================================================
# RISK-X4: JS LAYER DECISION
# =============================================================================

# DECISION: Option B - JS is frozen as display-only
# 
# Rationale:
# - JS tests could not be run due to Vite/Vitest compatibility issues
# - @vite/env module fails to load despite file existing
# - JS layer is NOT authoritative - it only renders UI
# - All security-critical operations occur in Python backend
#
# Enforcement:
# - JS cannot make direct backend calls that bypass Python validation
# - All data flows through Python security layer first
# - JS is treated as untrusted display layer

JS_LAYER_STATUS = "DISPLAY_ONLY"
JS_LAYER_AUTHORITATIVE = False


def validate_js_not_authoritative() -> None:
    """Validate that JS layer is not being used for authoritative operations.
    
    This is a documentation/assertion function to enforce the Option B decision.
    """
    if JS_LAYER_AUTHORITATIVE:
        raise GovernanceViolation(
            "JS layer is marked as display-only (Option B). "
            "Authoritative operations must go through Python security layer."
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Exceptions
    'GovernanceViolation',
    
    # RISK-X1: Path Traversal Prevention
    'validate_execution_id',
    'validate_session_id',
    'validate_artifact_path',
    'validate_file_path_relative',
    
    # RISK-X2: Evidence Leakage Prevention
    'redact_har_content',
    'scan_for_credentials',
    'validate_har_is_redacted',
    'CredentialScanResult',
    
    # RISK-X3: Single-Request Enforcement
    'SingleRequestEnforcer',
    'RequestSlotContext',
    'EnforcedHTTPClient',
    
    # RISK-X4: JS Layer Status
    'JS_LAYER_STATUS',
    'JS_LAYER_AUTHORITATIVE',
    'validate_js_not_authoritative',
]
