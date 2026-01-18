"""
Tests for Platform Adapters.

**Feature: bounty-pipeline**

Property tests validate:
- Property 6: Credential Security (credentials encrypted, never logged)
- Platform adapter interface compliance
- Session management
"""

import pytest
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings

from bounty_pipeline.adapters import (
    PlatformType,
    EncryptedCredentials,
    AuthSession,
    PlatformSchema,
    PlatformAdapter,
    HackerOneAdapter,
    BugcrowdAdapter,
    GenericMarkdownAdapter,
    get_adapter,
)
from bounty_pipeline.types import (
    SubmissionDraft,
    ValidatedFinding,
    MCPFinding,
    MCPClassification,
    ProofChain,
    SourceLinks,
    ReproductionStep,
    DraftStatus,
    SubmissionStatus,
)
from bounty_pipeline.errors import PlatformError


# =============================================================================
# Test Fixtures
# =============================================================================


def make_proof_chain() -> ProofChain:
    """Create a valid proof chain for testing."""
    return ProofChain(
        before_state={"key": "value"},
        action_sequence=[{"action": "test"}],
        after_state={"key": "changed"},
        causality_chain=[{"cause": "effect"}],
        replay_instructions=[{"step": 1}],
        invariant_violated="test_invariant",
        proof_hash="abc123",
    )


def make_mcp_finding() -> MCPFinding:
    """Create a valid MCP finding for testing."""
    return MCPFinding(
        finding_id="test-finding-001",
        classification=MCPClassification.BUG,
        invariant_violated="test_invariant",
        proof=make_proof_chain(),
        severity="high",
        cyfer_brain_observation_id="obs-001",
        timestamp=datetime.now(timezone.utc),
    )


def make_validated_finding() -> ValidatedFinding:
    """Create a validated finding for testing."""
    mcp_finding = make_mcp_finding()
    return ValidatedFinding(
        finding_id=mcp_finding.finding_id,
        mcp_finding=mcp_finding,
        proof_chain=mcp_finding.proof,
        source_links=SourceLinks(
            mcp_proof_id=mcp_finding.finding_id,
            mcp_proof_hash=mcp_finding.proof.proof_hash,
            cyfer_brain_observation_id=mcp_finding.cyfer_brain_observation_id,
        ),
    )


def make_approved_draft() -> SubmissionDraft:
    """Create an approved submission draft for testing."""
    draft = SubmissionDraft(
        draft_id="draft-001",
        finding=make_validated_finding(),
        platform="hackerone",
        report_title="Test Vulnerability Report",
        report_body="This is a test vulnerability report.",
        severity="high",
        reproduction_steps=[
            ReproductionStep(
                step_number=1,
                action="Navigate to target",
                expected_result="Page loads",
            )
        ],
        proof_summary="Proof summary here",
    )
    # Mark as approved
    draft.status = DraftStatus.APPROVED
    draft.approval_token_id = "token-123"
    return draft


# =============================================================================
# Property 6: Credential Security Tests
# =============================================================================


class TestCredentialSecurity:
    """
    **Property 6: Credential Security**
    **Validates: Requirements 5.2**

    For any API credentials stored by Bounty Pipeline,
    the credentials SHALL be encrypted at rest using Fernet
    (AES-128-CBC with HMAC-SHA256) and SHALL never appear in logs.
    """

    @given(
        api_key=st.text(min_size=8, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N"))).filter(lambda x: ":" not in x),
        api_secret=st.text(min_size=8, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    @settings(max_examples=100, deadline=5000)
    def test_credentials_can_be_decrypted(self, api_key: str, api_secret: str):
        """Encrypted credentials can be decrypted with correct key."""
        master_secret = b"test_master_secret_32_bytes_long"

        encrypted = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key=api_key,
            api_secret=api_secret,
            master_secret=master_secret,
        )

        decrypted_key, decrypted_secret = encrypted.decrypt(master_secret)

        assert decrypted_key == api_key
        assert decrypted_secret == api_secret

    def test_credentials_are_encrypted_not_plaintext(self):
        """Credentials must be encrypted, not stored in plaintext."""
        master_secret = b"test_master_secret_32_bytes_long"
        api_key = "my_super_secret_api_key_12345"
        api_secret = "my_super_secret_api_secret_67890"

        encrypted = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key=api_key,
            api_secret=api_secret,
            master_secret=master_secret,
        )

        # The full plaintext should not appear in encrypted data
        full_plaintext = f"{api_key}:{api_secret}".encode()
        assert full_plaintext != encrypted.encrypted_data

    def test_credentials_never_in_repr_or_str(self):
        """Credentials must never appear in repr() or str() output."""
        master_secret = b"test_master_secret_32_bytes_long"
        api_key = "my_super_secret_api_key_12345"
        api_secret = "my_super_secret_api_secret_67890"

        encrypted = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key=api_key,
            api_secret=api_secret,
            master_secret=master_secret,
        )

        repr_output = repr(encrypted)
        str_output = str(encrypted)

        # Full credentials should never appear
        assert api_key not in repr_output
        assert api_secret not in repr_output
        assert api_key not in str_output
        assert api_secret not in str_output
        assert "REDACTED" in repr_output

    @given(
        api_key=st.text(min_size=8, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N"))).filter(lambda x: ":" not in x),
        api_secret=st.text(min_size=8, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    @settings(max_examples=100, deadline=5000)
    def test_wrong_key_fails_decryption(self, api_key: str, api_secret: str):
        """Decryption with wrong key MUST fail (Fernet provides integrity)."""
        master_secret = b"test_master_secret_32_bytes_long"
        wrong_secret = b"wrong_master_secret_32_bytes_xx"

        encrypted = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key=api_key,
            api_secret=api_secret,
            master_secret=master_secret,
        )

        # Fernet provides authenticated encryption - wrong key MUST raise
        with pytest.raises(ValueError, match="invalid key or tampered"):
            encrypted.decrypt(wrong_secret)

    def test_session_token_never_in_repr(self):
        """Session tokens must never appear in repr() output."""
        session = AuthSession(
            platform=PlatformType.HACKERONE,
            session_id="sess-123",
            authenticated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            _token="super_secret_token_12345",
        )

        repr_output = repr(session)

        assert "super_secret_token" not in repr_output
        assert session.token == "super_secret_token_12345"  # But accessible via property

    def test_encrypted_data_has_salt(self):
        """Each encryption should use a unique salt."""
        master_secret = b"test_master_secret_32_bytes_long"
        api_key = "test_key"
        api_secret = "test_secret"

        encrypted1 = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key=api_key,
            api_secret=api_secret,
            master_secret=master_secret,
        )

        encrypted2 = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key=api_key,
            api_secret=api_secret,
            master_secret=master_secret,
        )

        # Different salts should produce different encrypted data
        assert encrypted1.salt != encrypted2.salt
        assert encrypted1.encrypted_data != encrypted2.encrypted_data

    def test_fernet_authenticated_encryption_detects_tampering(self):
        """Fernet encryption MUST detect data tampering."""
        master_secret = b"test_master_secret_32_bytes_long"
        api_key = "test_key"
        api_secret = "test_secret"

        encrypted = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key=api_key,
            api_secret=api_secret,
            master_secret=master_secret,
        )

        # Tamper with encrypted data
        tampered_data = bytearray(encrypted.encrypted_data)
        if len(tampered_data) > 10:
            tampered_data[10] ^= 0xFF  # Flip bits
        
        tampered = EncryptedCredentials(
            platform=encrypted.platform,
            encrypted_data=bytes(tampered_data),
            salt=encrypted.salt,
            key_version=encrypted.key_version,
        )

        # Fernet MUST detect tampering and raise
        with pytest.raises(ValueError, match="invalid key or tampered"):
            tampered.decrypt(master_secret)

    def test_master_secret_minimum_length(self):
        """Master secret must be at least 16 bytes."""
        short_secret = b"short"
        
        with pytest.raises(ValueError, match="at least 16 bytes"):
            EncryptedCredentials.encrypt(
                platform=PlatformType.HACKERONE,
                api_key="test_key",
                api_secret="test_secret",
                master_secret=short_secret,
            )

    def test_key_version_for_rotation(self):
        """Credentials support key versioning for rotation."""
        master_secret = b"test_master_secret_32_bytes_long"
        
        encrypted = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key="test_key",
            api_secret="test_secret",
            master_secret=master_secret,
            key_version=2,
        )
        
        assert encrypted.key_version == 2


# =============================================================================
# Platform Adapter Tests
# =============================================================================


class TestHackerOneAdapter:
    """Tests for HackerOne adapter."""

    def test_platform_type(self):
        """Adapter reports correct platform type."""
        adapter = HackerOneAdapter()
        assert adapter.platform_type == PlatformType.HACKERONE

    def test_authenticate_success(self):
        """Authentication creates valid session."""
        adapter = HackerOneAdapter()
        master_secret = b"test_master_secret_32_bytes_long"

        credentials = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key="test_key",
            api_secret="test_secret",
            master_secret=master_secret,
        )

        session = adapter.authenticate(credentials, master_secret)

        assert session.platform == PlatformType.HACKERONE
        assert not session.is_expired
        assert session.session_id

    def test_authenticate_wrong_platform_fails(self):
        """Authentication fails with wrong platform credentials."""
        adapter = HackerOneAdapter()
        master_secret = b"test_master_secret_32_bytes_long"

        credentials = EncryptedCredentials.encrypt(
            platform=PlatformType.BUGCROWD,  # Wrong platform
            api_key="test_key",
            api_secret="test_secret",
            master_secret=master_secret,
        )

        with pytest.raises(PlatformError, match="platform mismatch"):
            adapter.authenticate(credentials, master_secret)

    def test_submit_requires_approval(self):
        """Submission fails without approval."""
        adapter = HackerOneAdapter()
        master_secret = b"test_master_secret_32_bytes_long"

        credentials = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key="test_key",
            api_secret="test_secret",
            master_secret=master_secret,
        )

        session = adapter.authenticate(credentials, master_secret)

        # Create unapproved draft
        draft = SubmissionDraft(
            draft_id="draft-001",
            finding=make_validated_finding(),
            platform="hackerone",
            report_title="Test Report",
            report_body="Test body",
            severity="high",
            reproduction_steps=[],
            proof_summary="Proof",
        )

        with pytest.raises(PlatformError, match="must be approved"):
            adapter.submit_report(draft, session)

    def test_submit_approved_draft(self):
        """Approved draft can be submitted."""
        adapter = HackerOneAdapter()
        master_secret = b"test_master_secret_32_bytes_long"

        credentials = EncryptedCredentials.encrypt(
            platform=PlatformType.HACKERONE,
            api_key="test_key",
            api_secret="test_secret",
            master_secret=master_secret,
        )

        session = adapter.authenticate(credentials, master_secret)
        draft = make_approved_draft()

        receipt = adapter.submit_report(draft, session)

        assert receipt.platform == "hackerone"
        assert receipt.submission_id.startswith("h1-")
        assert receipt.receipt_hash

    def test_get_schema(self):
        """Schema has required fields."""
        adapter = HackerOneAdapter()
        schema = adapter.get_schema()

        assert schema.platform == PlatformType.HACKERONE
        assert "title" in schema.required_fields
        assert "critical" in schema.severity_values


class TestBugcrowdAdapter:
    """Tests for Bugcrowd adapter."""

    def test_platform_type(self):
        """Adapter reports correct platform type."""
        adapter = BugcrowdAdapter()
        assert adapter.platform_type == PlatformType.BUGCROWD

    def test_authenticate_success(self):
        """Authentication creates valid session."""
        adapter = BugcrowdAdapter()
        master_secret = b"test_master_secret_32_bytes_long"

        credentials = EncryptedCredentials.encrypt(
            platform=PlatformType.BUGCROWD,
            api_key="test_key",
            api_secret="test_secret",
            master_secret=master_secret,
        )

        session = adapter.authenticate(credentials, master_secret)

        assert session.platform == PlatformType.BUGCROWD
        assert not session.is_expired

    def test_submit_approved_draft(self):
        """Approved draft can be submitted."""
        adapter = BugcrowdAdapter()
        master_secret = b"test_master_secret_32_bytes_long"

        credentials = EncryptedCredentials.encrypt(
            platform=PlatformType.BUGCROWD,
            api_key="test_key",
            api_secret="test_secret",
            master_secret=master_secret,
        )

        session = adapter.authenticate(credentials, master_secret)
        draft = make_approved_draft()
        draft.platform = "bugcrowd"

        receipt = adapter.submit_report(draft, session)

        assert receipt.platform == "bugcrowd"
        assert receipt.submission_id.startswith("bc-")

    def test_severity_mapping(self):
        """Severity is mapped to Bugcrowd priority."""
        adapter = BugcrowdAdapter()

        assert adapter._map_severity_to_priority("critical") == "P1"
        assert adapter._map_severity_to_priority("high") == "P2"
        assert adapter._map_severity_to_priority("medium") == "P3"
        assert adapter._map_severity_to_priority("low") == "P4"
        assert adapter._map_severity_to_priority("informational") == "P5"


class TestGenericMarkdownAdapter:
    """Tests for generic markdown adapter."""

    def test_platform_type(self):
        """Adapter reports correct platform type."""
        adapter = GenericMarkdownAdapter()
        assert adapter.platform_type == PlatformType.GENERIC

    def test_authenticate_no_credentials_needed(self):
        """Generic adapter doesn't need real credentials."""
        adapter = GenericMarkdownAdapter()
        master_secret = b"test_master_secret_32_bytes_long"

        # Even with dummy credentials, authentication works
        credentials = EncryptedCredentials.encrypt(
            platform=PlatformType.GENERIC,
            api_key="dummy",
            api_secret="dummy",
            master_secret=master_secret,
        )

        session = adapter.authenticate(credentials, master_secret)

        assert session.platform == PlatformType.GENERIC
        assert session.session_id == "local"

    def test_submit_generates_markdown(self):
        """Submission generates markdown report."""
        adapter = GenericMarkdownAdapter()
        master_secret = b"test_master_secret_32_bytes_long"

        credentials = EncryptedCredentials.encrypt(
            platform=PlatformType.GENERIC,
            api_key="dummy",
            api_secret="dummy",
            master_secret=master_secret,
        )

        session = adapter.authenticate(credentials, master_secret)
        draft = make_approved_draft()
        draft.platform = "generic"

        receipt = adapter.submit_report(draft, session)

        assert receipt.platform == "generic"
        assert receipt.submission_id.startswith("md-")
        assert "content" in receipt.receipt_data
        assert draft.report_title in receipt.receipt_data["content"]

    def test_get_status_returns_unknown_unconfirmed(self):
        """Generic adapter always returns UNKNOWN_UNCONFIRMED status."""
        adapter = GenericMarkdownAdapter()
        master_secret = b"test_master_secret_32_bytes_long"

        credentials = EncryptedCredentials.encrypt(
            platform=PlatformType.GENERIC,
            api_key="dummy",
            api_secret="dummy",
            master_secret=master_secret,
        )

        session = adapter.authenticate(credentials, master_secret)
        status = adapter.get_status("any-id", session)

        assert status == SubmissionStatus.UNKNOWN_UNCONFIRMED


class TestGetAdapter:
    """Tests for adapter factory function."""

    def test_get_hackerone_adapter(self):
        """Factory returns HackerOne adapter."""
        adapter = get_adapter("hackerone")
        assert isinstance(adapter, HackerOneAdapter)

    def test_get_bugcrowd_adapter(self):
        """Factory returns Bugcrowd adapter."""
        adapter = get_adapter("bugcrowd")
        assert isinstance(adapter, BugcrowdAdapter)

    def test_get_generic_adapter(self):
        """Factory returns generic adapter."""
        adapter = get_adapter("generic")
        assert isinstance(adapter, GenericMarkdownAdapter)

    def test_case_insensitive(self):
        """Factory is case-insensitive."""
        assert isinstance(get_adapter("HackerOne"), HackerOneAdapter)
        assert isinstance(get_adapter("BUGCROWD"), BugcrowdAdapter)
        assert isinstance(get_adapter("Generic"), GenericMarkdownAdapter)

    def test_unsupported_platform_raises(self):
        """Factory raises for unsupported platform."""
        with pytest.raises(ValueError, match="Unsupported platform"):
            get_adapter("unknown_platform")


class TestSessionExpiry:
    """Tests for session expiry handling."""

    def test_expired_session_detected(self):
        """Expired sessions are detected."""
        session = AuthSession(
            platform=PlatformType.HACKERONE,
            session_id="sess-123",
            authenticated_at=datetime.now(timezone.utc) - timedelta(hours=2),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            _token="token",
        )

        assert session.is_expired

    def test_valid_session_not_expired(self):
        """Valid sessions are not marked expired."""
        session = AuthSession(
            platform=PlatformType.HACKERONE,
            session_id="sess-123",
            authenticated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            _token="token",
        )

        assert not session.is_expired

    def test_submit_with_expired_session_fails(self):
        """Submission with expired session fails."""
        adapter = HackerOneAdapter()

        expired_session = AuthSession(
            platform=PlatformType.HACKERONE,
            session_id="sess-123",
            authenticated_at=datetime.now(timezone.utc) - timedelta(hours=2),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            _token="token",
        )

        draft = make_approved_draft()

        with pytest.raises(PlatformError, match="expired"):
            adapter.submit_report(draft, expired_session)
