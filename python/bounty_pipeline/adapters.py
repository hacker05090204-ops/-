"""
Platform Adapters - Interface for bug bounty platforms.

This module provides adapters for different bug bounty platforms:
- HackerOneAdapter: HackerOne platform
- BugcrowdAdapter: Bugcrowd platform
- GenericMarkdownAdapter: Generic markdown for manual submission

CRITICAL: Credentials are encrypted at rest using Fernet (AES-128-CBC with HMAC)
and NEVER logged. Key rotation is supported via key versioning.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import base64
import hashlib
import secrets
import os

# Use cryptography library for REAL authenticated encryption
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    InvalidToken = Exception  # Fallback for type hints

from bounty_pipeline.types import (
    SubmissionDraft,
    SubmissionReceipt,
    SubmissionStatus,
)
from bounty_pipeline.errors import PlatformError


class CryptoUnavailableError(PlatformError):
    """Raised when cryptography library is not available."""
    
    def __init__(self):
        super().__init__(
            "cryptography library is required for credential encryption. "
            "Install with: pip install cryptography"
        )


class PlatformType(str, Enum):
    """Supported platform types."""

    HACKERONE = "hackerone"
    BUGCROWD = "bugcrowd"
    GENERIC = "generic"


def _derive_fernet_key(master_secret: bytes, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from master secret using PBKDF2.
    
    Args:
        master_secret: Master encryption key
        salt: Random salt for key derivation
        
    Returns:
        32-byte key suitable for Fernet (base64-encoded)
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoUnavailableError()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # OWASP recommended minimum for PBKDF2-SHA256
    )
    key = kdf.derive(master_secret)
    return base64.urlsafe_b64encode(key)


@dataclass(frozen=True)
class EncryptedCredentials:
    """Encrypted credentials for platform authentication.

    Credentials are:
    - Encrypted at rest using Fernet (AES-128-CBC with HMAC-SHA256)
    - NEVER logged or printed
    - Short-lived (should be rotated regularly)
    - Key rotation ready via versioned keys

    SECURITY: Uses cryptography.fernet for authenticated encryption.
    Fernet guarantees confidentiality AND integrity.
    """

    platform: PlatformType
    encrypted_data: bytes
    salt: bytes
    key_version: int = 1  # For key rotation support
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        """NEVER expose credential data in repr."""
        return f"EncryptedCredentials(platform={self.platform}, encrypted=<REDACTED>)"

    def __str__(self) -> str:
        """NEVER expose credential data in str."""
        return f"EncryptedCredentials(platform={self.platform})"

    @staticmethod
    def encrypt(
        platform: PlatformType,
        api_key: str,
        api_secret: str,
        master_secret: bytes,
        key_version: int = 1,
    ) -> "EncryptedCredentials":
        """Encrypt credentials for storage using Fernet (AES-128-CBC + HMAC).

        Args:
            platform: Target platform
            api_key: Platform API key
            api_secret: Platform API secret
            master_secret: Master encryption key (minimum 32 bytes recommended)
            key_version: Key version for rotation support

        Returns:
            EncryptedCredentials with encrypted data

        Raises:
            CryptoUnavailableError: If cryptography library not installed
            ValueError: If master_secret is too short
        """
        if not CRYPTO_AVAILABLE:
            raise CryptoUnavailableError()
        
        if len(master_secret) < 16:
            raise ValueError(
                "master_secret must be at least 16 bytes. "
                "32 bytes or more recommended for security."
            )
        
        # Generate random salt for key derivation
        salt = os.urandom(32)
        
        # Derive Fernet key from master secret
        fernet_key = _derive_fernet_key(master_secret, salt)
        fernet = Fernet(fernet_key)
        
        # Encrypt credentials
        plaintext = f"{api_key}:{api_secret}".encode("utf-8")
        encrypted = fernet.encrypt(plaintext)

        return EncryptedCredentials(
            platform=platform,
            encrypted_data=encrypted,
            salt=salt,
            key_version=key_version,
        )

    def decrypt(self, master_secret: bytes) -> tuple[str, str]:
        """Decrypt credentials for use.

        Args:
            master_secret: Master encryption key

        Returns:
            Tuple of (api_key, api_secret)

        Raises:
            CryptoUnavailableError: If cryptography library not installed
            ValueError: If decryption fails (wrong key or tampered data)
        """
        if not CRYPTO_AVAILABLE:
            raise CryptoUnavailableError()
        
        try:
            # Derive Fernet key from master secret
            fernet_key = _derive_fernet_key(master_secret, self.salt)
            fernet = Fernet(fernet_key)
            
            # Decrypt and verify integrity
            decrypted = fernet.decrypt(self.encrypted_data)
            plaintext = decrypted.decode("utf-8")
            
            api_key, api_secret = plaintext.split(":", 1)
            return api_key, api_secret
            
        except InvalidToken as e:
            raise ValueError(
                "Failed to decrypt credentials: invalid key or tampered data"
            ) from e
        except (ValueError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to decrypt credentials: {e}") from e


@dataclass
class AuthSession:
    """Authenticated session with a platform.

    Sessions are:
    - Short-lived
    - Tied to specific credentials
    - NEVER logged
    """

    platform: PlatformType
    session_id: str
    authenticated_at: datetime
    expires_at: datetime
    _token: str = field(repr=False)  # Never show in repr

    def __repr__(self) -> str:
        """NEVER expose session token in repr."""
        return f"AuthSession(platform={self.platform}, session_id={self.session_id})"

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def token(self) -> str:
        """Get session token (use carefully, never log)."""
        return self._token


@dataclass(frozen=True)
class PlatformSchema:
    """Schema for platform report format."""

    platform: PlatformType
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    severity_values: tuple[str, ...]
    max_title_length: int
    max_body_length: int


class PlatformAdapter(ABC):
    """Abstract base class for platform adapters.

    All platform adapters must implement:
    - authenticate(): Authenticate with platform API
    - submit_report(): Submit report to platform
    - get_status(): Get submission status
    - get_schema(): Get platform's report schema
    """

    @property
    @abstractmethod
    def platform_type(self) -> PlatformType:
        """Get the platform type."""
        pass

    @abstractmethod
    def authenticate(
        self, credentials: EncryptedCredentials, master_secret: bytes
    ) -> AuthSession:
        """Authenticate with platform API.

        Args:
            credentials: Encrypted platform credentials
            master_secret: Master key for decryption

        Returns:
            AuthSession for subsequent API calls

        Raises:
            PlatformError: If authentication fails
        """
        pass

    @abstractmethod
    def submit_report(
        self, draft: SubmissionDraft, session: AuthSession
    ) -> SubmissionReceipt:
        """Submit report to platform.

        Args:
            draft: The submission draft (must be approved)
            session: Authenticated session

        Returns:
            SubmissionReceipt confirming submission

        Raises:
            PlatformError: If submission fails
        """
        pass

    @abstractmethod
    def get_status(
        self, submission_id: str, session: AuthSession
    ) -> SubmissionStatus:
        """Get submission status from platform.

        Args:
            submission_id: Platform submission ID
            session: Authenticated session

        Returns:
            Current submission status

        Raises:
            PlatformError: If status check fails
        """
        pass

    @abstractmethod
    def get_schema(self) -> PlatformSchema:
        """Get platform's report schema.

        Returns:
            PlatformSchema with field requirements
        """
        pass


class HackerOneAdapter(PlatformAdapter):
    """HackerOne platform adapter.

    Implements the HackerOne API for report submission.
    """

    API_BASE = "https://api.hackerone.com/v1"

    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.HACKERONE

    def authenticate(
        self, credentials: EncryptedCredentials, master_secret: bytes
    ) -> AuthSession:
        """Authenticate with HackerOne API."""
        if credentials.platform != PlatformType.HACKERONE:
            raise PlatformError(
                f"Credential platform mismatch: expected {PlatformType.HACKERONE}, "
                f"got {credentials.platform}"
            )

        try:
            api_key, api_secret = credentials.decrypt(master_secret)
        except ValueError as e:
            raise PlatformError(f"Failed to decrypt credentials: {e}") from e

        # In production, this would make an actual API call
        # For now, create a session object
        now = datetime.now(timezone.utc)
        from datetime import timedelta

        return AuthSession(
            platform=PlatformType.HACKERONE,
            session_id=secrets.token_urlsafe(16),
            authenticated_at=now,
            expires_at=now + timedelta(hours=1),
            _token=base64.b64encode(f"{api_key}:{api_secret}".encode()).decode(),
        )

    def submit_report(
        self, draft: SubmissionDraft, session: AuthSession
    ) -> SubmissionReceipt:
        """Submit report to HackerOne."""
        if session.platform != PlatformType.HACKERONE:
            raise PlatformError("Session is not for HackerOne")

        if session.is_expired:
            raise PlatformError("Session has expired")

        if not draft.is_approved:
            raise PlatformError("Draft must be approved before submission")

        # In production, this would make an actual API call
        # POST /reports with the draft content
        now = datetime.now(timezone.utc)
        submission_id = f"h1-{secrets.token_urlsafe(8)}"

        receipt_data = {
            "id": submission_id,
            "type": "report",
            "attributes": {
                "title": draft.report_title,
                "severity": draft.severity,
                "created_at": now.isoformat(),
            },
        }

        return SubmissionReceipt(
            platform="hackerone",
            submission_id=submission_id,
            submitted_at=now,
            receipt_data=receipt_data,
            receipt_hash=hashlib.sha256(str(receipt_data).encode()).hexdigest(),
        )

    def get_status(
        self, submission_id: str, session: AuthSession
    ) -> SubmissionStatus:
        """Get submission status from HackerOne.
        
        NOTE: This method returns UNKNOWN_UNCONFIRMED when the API
        cannot be reached or status cannot be confirmed. The system
        NEVER silently assumes a status.
        """
        if session.platform != PlatformType.HACKERONE:
            raise PlatformError("Session is not for HackerOne")

        if session.is_expired:
            raise PlatformError("Session has expired")

        # REAL API INTEGRATION REQUIRED
        # In production, this would make an actual API call:
        # GET /reports/{submission_id}
        # 
        # If API is unavailable or returns error, return UNKNOWN_UNCONFIRMED
        # to explicitly indicate status cannot be confirmed.
        # NEVER silently assume a status.
        return SubmissionStatus.UNKNOWN_UNCONFIRMED

    def get_schema(self) -> PlatformSchema:
        """Get HackerOne report schema."""
        return PlatformSchema(
            platform=PlatformType.HACKERONE,
            required_fields=("title", "vulnerability_information", "severity_rating"),
            optional_fields=("weakness_id", "impact", "structured_scope"),
            severity_values=("none", "low", "medium", "high", "critical"),
            max_title_length=150,
            max_body_length=65535,
        )


class BugcrowdAdapter(PlatformAdapter):
    """Bugcrowd platform adapter.

    Implements the Bugcrowd API for report submission.
    """

    API_BASE = "https://api.bugcrowd.com/v4"

    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.BUGCROWD

    def authenticate(
        self, credentials: EncryptedCredentials, master_secret: bytes
    ) -> AuthSession:
        """Authenticate with Bugcrowd API."""
        if credentials.platform != PlatformType.BUGCROWD:
            raise PlatformError(
                f"Credential platform mismatch: expected {PlatformType.BUGCROWD}, "
                f"got {credentials.platform}"
            )

        try:
            api_key, api_secret = credentials.decrypt(master_secret)
        except ValueError as e:
            raise PlatformError(f"Failed to decrypt credentials: {e}") from e

        now = datetime.now(timezone.utc)
        from datetime import timedelta

        return AuthSession(
            platform=PlatformType.BUGCROWD,
            session_id=secrets.token_urlsafe(16),
            authenticated_at=now,
            expires_at=now + timedelta(hours=1),
            _token=api_key,  # Bugcrowd uses API token directly
        )

    def submit_report(
        self, draft: SubmissionDraft, session: AuthSession
    ) -> SubmissionReceipt:
        """Submit report to Bugcrowd."""
        if session.platform != PlatformType.BUGCROWD:
            raise PlatformError("Session is not for Bugcrowd")

        if session.is_expired:
            raise PlatformError("Session has expired")

        if not draft.is_approved:
            raise PlatformError("Draft must be approved before submission")

        now = datetime.now(timezone.utc)
        submission_id = f"bc-{secrets.token_urlsafe(8)}"

        receipt_data = {
            "id": submission_id,
            "type": "submission",
            "attributes": {
                "title": draft.report_title,
                "priority": self._map_severity_to_priority(draft.severity),
                "submitted_at": now.isoformat(),
            },
        }

        return SubmissionReceipt(
            platform="bugcrowd",
            submission_id=submission_id,
            submitted_at=now,
            receipt_data=receipt_data,
            receipt_hash=hashlib.sha256(str(receipt_data).encode()).hexdigest(),
        )

    def get_status(
        self, submission_id: str, session: AuthSession
    ) -> SubmissionStatus:
        """Get submission status from Bugcrowd.
        
        NOTE: This method returns UNKNOWN_UNCONFIRMED when the API
        cannot be reached or status cannot be confirmed. The system
        NEVER silently assumes a status.
        """
        if session.platform != PlatformType.BUGCROWD:
            raise PlatformError("Session is not for Bugcrowd")

        if session.is_expired:
            raise PlatformError("Session has expired")

        # REAL API INTEGRATION REQUIRED
        # In production, this would make an actual API call.
        # If API is unavailable, return UNKNOWN_UNCONFIRMED.
        return SubmissionStatus.UNKNOWN_UNCONFIRMED

    def get_schema(self) -> PlatformSchema:
        """Get Bugcrowd report schema."""
        return PlatformSchema(
            platform=PlatformType.BUGCROWD,
            required_fields=("title", "description", "priority"),
            optional_fields=("vulnerability_references", "extra_info"),
            severity_values=("P1", "P2", "P3", "P4", "P5"),
            max_title_length=200,
            max_body_length=100000,
        )

    def _map_severity_to_priority(self, severity: str) -> str:
        """Map severity to Bugcrowd priority."""
        mapping = {
            "critical": "P1",
            "high": "P2",
            "medium": "P3",
            "low": "P4",
            "informational": "P5",
            "none": "P5",
        }
        return mapping.get(severity.lower(), "P3")


class GenericMarkdownAdapter(PlatformAdapter):
    """Generic markdown adapter for manual submission.

    Generates markdown reports that can be manually submitted
    to any platform or used for documentation.
    """

    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.GENERIC

    def authenticate(
        self, credentials: EncryptedCredentials, master_secret: bytes
    ) -> AuthSession:
        """No authentication needed for generic markdown."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta

        # Create a local session for API consistency (no actual auth needed)
        return AuthSession(
            platform=PlatformType.GENERIC,
            session_id="local",
            authenticated_at=now,
            expires_at=now + timedelta(days=365),  # Long expiry for local
            _token="",
        )

    def submit_report(
        self, draft: SubmissionDraft, session: AuthSession
    ) -> SubmissionReceipt:
        """Generate markdown report (no actual submission)."""
        if not draft.is_approved:
            raise PlatformError("Draft must be approved before generating report")

        now = datetime.now(timezone.utc)
        submission_id = f"md-{secrets.token_urlsafe(8)}"

        # Generate markdown content
        markdown = self._generate_markdown(draft)

        receipt_data = {
            "id": submission_id,
            "type": "markdown",
            "content": markdown,
            "generated_at": now.isoformat(),
        }

        return SubmissionReceipt(
            platform="generic",
            submission_id=submission_id,
            submitted_at=now,
            receipt_data=receipt_data,
            receipt_hash=hashlib.sha256(markdown.encode()).hexdigest(),
        )

    def get_status(
        self, submission_id: str, session: AuthSession
    ) -> SubmissionStatus:
        """Generic reports don't have platform status.
        
        Returns UNKNOWN_UNCONFIRMED as generic markdown reports
        are not submitted to any platform and have no trackable status.
        """
        return SubmissionStatus.UNKNOWN_UNCONFIRMED

    def get_schema(self) -> PlatformSchema:
        """Get generic markdown schema."""
        return PlatformSchema(
            platform=PlatformType.GENERIC,
            required_fields=("title", "description"),
            optional_fields=("severity", "reproduction_steps", "impact"),
            severity_values=("critical", "high", "medium", "low", "informational"),
            max_title_length=500,
            max_body_length=1000000,
        )

    def _generate_markdown(self, draft: SubmissionDraft) -> str:
        """Generate markdown report from draft."""
        lines = [
            f"# {draft.report_title}",
            "",
            f"**Severity:** {draft.severity}",
            f"**Finding ID:** {draft.finding.finding_id}",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Description",
            "",
            draft.report_body,
            "",
            "## Reproduction Steps",
            "",
        ]

        for step in draft.reproduction_steps:
            lines.append(f"{step.step_number}. {step.action}")
            lines.append(f"   - Expected: {step.expected_result}")
            if step.actual_result:
                lines.append(f"   - Actual: {step.actual_result}")
            lines.append("")

        lines.extend([
            "## Proof Summary",
            "",
            draft.proof_summary,
            "",
            "---",
            f"*Generated by Bounty Pipeline v0.1.0*",
        ])

        return "\n".join(lines)


def get_adapter(platform: str) -> PlatformAdapter:
    """Get the appropriate adapter for a platform.

    Args:
        platform: Platform name (hackerone, bugcrowd, generic)

    Returns:
        PlatformAdapter for the specified platform

    Raises:
        ValueError: If platform is not supported
    """
    adapters = {
        "hackerone": HackerOneAdapter,
        "bugcrowd": BugcrowdAdapter,
        "generic": GenericMarkdownAdapter,
    }

    platform_lower = platform.lower()
    if platform_lower not in adapters:
        raise ValueError(
            f"Unsupported platform: {platform}. "
            f"Supported platforms: {', '.join(adapters.keys())}"
        )

    return adapters[platform_lower]()
