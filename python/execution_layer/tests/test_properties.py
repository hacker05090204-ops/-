"""
Property-Based Tests for Execution Layer

Uses Hypothesis to verify universal correctness properties.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings, assume

from execution_layer.types import (
    SafeActionType,
    ForbiddenActionType,
    SafeAction,
    ExecutionToken,
    ExecutionBatch,
    EvidenceType,
    EvidenceArtifact,
    EvidenceBundle,
    VideoPoC,
    StoreOwnershipAttestation,
    DuplicateExplorationConfig,
    MCPClassification,
    MCPVerificationResult,
)
from execution_layer.errors import (
    TokenAlreadyUsedError,
    TokenExpiredError,
    TokenMismatchError,
    VideoPoCExistsError,
    DuplicateExplorationLimitError,
    ScopeViolationError,
    ForbiddenActionError,
    ArchitecturalViolationError,
)
from execution_layer.actions import ActionValidator, SAFE_ACTIONS, FORBIDDEN_ACTIONS
from execution_layer.scope import ShopifyScopeConfig, ShopifyScopeValidator
from execution_layer.approval import HumanApprovalHook
from execution_layer.video import VideoPoCGenerator
from execution_layer.duplicate import DuplicateHandler
from execution_layer.audit import ExecutionAuditLog


# === Test UUID Helpers ===
def make_test_uuid(seed: int = 0) -> str:
    """Generate a valid UUIDv4 for tests.
    
    Uses uuid4() to generate valid UUIDv4 format that passes security validation.
    """
    return str(uuid.uuid4())


def make_exec_id(n: int = 1) -> str:
    """Generate a test execution ID (valid UUIDv4)."""
    return str(uuid.uuid4())


def make_bundle_id(n: int = 1) -> str:
    """Generate a test bundle ID (valid UUIDv4)."""
    return str(uuid.uuid4())


# === Strategies ===

safe_action_types = st.sampled_from(list(SafeActionType))
forbidden_action_types = st.sampled_from(list(ForbiddenActionType))

action_ids = st.text(min_size=1, max_size=32, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_")
approver_ids = st.text(min_size=1, max_size=32, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_")
finding_ids = st.text(min_size=1, max_size=32, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_")

# Safe targets (no forbidden paths)
safe_targets = st.sampled_from([
    "https://my-store.myshopify.com/products",
    "https://my-store.myshopify.com/collections",
    "https://my-store.myshopify.com/pages/about",
    "#button",
    ".product-card",
    "[data-testid='item']",
])


@st.composite
def safe_actions(draw):
    """Generate valid SafeAction instances."""
    return SafeAction(
        action_id=draw(action_ids),
        action_type=draw(safe_action_types),
        target=draw(safe_targets),
        parameters={},
        description="Test action",
    )


@st.composite
def execution_tokens(draw, action: SafeAction):
    """Generate ExecutionToken for a given action."""
    return ExecutionToken.generate(
        approver_id=draw(approver_ids),
        action=action,
        validity_minutes=draw(st.integers(min_value=1, max_value=60)),
    )


# === Property Tests: Token Single-Use Enforcement ===

class TestTokenSingleUseProperty:
    """
    Property 3: Token Single-Use
    For any ExecutionToken, the token SHALL be invalidated after use;
    reuse attempts SHALL be rejected.
    """
    
    @given(action_id=action_ids, approver_id=approver_ids)
    @settings(max_examples=100, deadline=5000)
    def test_token_invalidated_after_use(self, action_id, approver_id):
        """**Feature: execution-layer, Property 3: Token Single-Use**
        
        Tokens must be invalidated after first use.
        """
        assume(action_id and approver_id)
        
        hook = HumanApprovalHook()
        action = SafeAction(
            action_id=action_id,
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
        
        # Request and approve
        request = hook.request_approval(action)
        token = hook.approve(request.request_id, approver_id)
        
        # First validation should succeed
        assert hook.validate_token(token, action) is True
        
        # Invalidate token
        hook.invalidate_token(token)
        
        # Second validation should fail
        with pytest.raises(TokenAlreadyUsedError):
            hook.validate_token(token, action)
    
    @given(action_id=action_ids, approver_id=approver_ids)
    @settings(max_examples=100, deadline=5000)
    def test_used_token_tracked(self, action_id, approver_id):
        """**Feature: execution-layer, Property 3: Token Single-Use**
        
        Used tokens must be tracked.
        """
        assume(action_id and approver_id)
        
        hook = HumanApprovalHook()
        action = SafeAction(
            action_id=action_id,
            action_type=SafeActionType.CLICK,
            target="#button",
            parameters={},
            description="Test",
        )
        
        request = hook.request_approval(action)
        token = hook.approve(request.request_id, approver_id)
        
        assert hook.is_token_used(token) is False
        hook.invalidate_token(token)
        assert hook.is_token_used(token) is True


# === Property Tests: Video Idempotency ===

class TestVideoIdempotencyProperty:
    """
    Property 6: Video PoC Generation
    For any MCP BUG confirmation, the system SHALL generate a Video PoC;
    IDEMPOTENCY GUARD: Only ONE VideoPoC per finding_id.
    """
    
    @given(finding_id=finding_ids)
    @settings(max_examples=100, deadline=5000)
    def test_one_video_per_finding(self, finding_id):
        """**Feature: execution-layer, Property 6: Video PoC Idempotency**
        
        Only one VideoPoC per finding_id is allowed.
        """
        assume(finding_id)
        
        generator = VideoPoCGenerator()
        
        # Create MCP BUG result
        mcp_result = MCPVerificationResult(
            verification_id="test-verification",
            finding_id=finding_id,
            classification=MCPClassification.BUG,
            invariant_violated="test-invariant",
            proof_hash="test-proof-hash",
            verified_at=datetime.now(timezone.utc),
        )
        
        # Create evidence bundle with video
        video_artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.VIDEO,
            content=b"video_content",
        )
        bundle = EvidenceBundle(
            bundle_id=make_bundle_id(1),
            execution_id=make_exec_id(1),
            video=video_artifact,
            execution_trace=[{"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "test"}],
        )
        
        # First generation should succeed
        poc = generator.generate(finding_id, mcp_result, bundle)
        assert poc.finding_id == finding_id
        
        # Second generation should fail (idempotency guard)
        with pytest.raises(VideoPoCExistsError):
            generator.generate(finding_id, mcp_result, bundle)
    
    @given(finding_id=finding_ids)
    @settings(max_examples=100, deadline=5000)
    def test_has_poc_tracks_generated(self, finding_id):
        """**Feature: execution-layer, Property 6: Video PoC Idempotency**
        
        has_poc() must accurately track generated PoCs.
        """
        assume(finding_id)
        
        generator = VideoPoCGenerator()
        
        # Initially no PoC
        assert generator.has_poc(finding_id) is False
        
        # Generate PoC
        mcp_result = MCPVerificationResult(
            verification_id="test",
            finding_id=finding_id,
            classification=MCPClassification.BUG,
            invariant_violated=None,
            proof_hash=None,
            verified_at=datetime.now(timezone.utc),
        )
        video_artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.VIDEO,
            content=b"video",
        )
        bundle = EvidenceBundle(
            bundle_id=make_bundle_id(2),
            execution_id=make_exec_id(2),
            video=video_artifact,
            execution_trace=[{"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "test"}],
        )
        
        generator.generate(finding_id, mcp_result, bundle)
        
        # Now has PoC
        assert generator.has_poc(finding_id) is True


# === Property Tests: Duplicate Exploration Limits ===

class TestDuplicateExplorationLimitsProperty:
    """
    Property: Duplicate Exploration STOP Conditions
    Exploration must stop at configured limits.
    """
    
    @given(
        max_depth=st.integers(min_value=1, max_value=10),
        max_hypotheses=st.integers(min_value=1, max_value=10),
        max_actions=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100, deadline=5000)
    def test_max_depth_enforced(self, max_depth, max_hypotheses, max_actions):
        """**Feature: execution-layer, Property: Duplicate Exploration Limits**
        
        max_depth must be enforced.
        """
        config = DuplicateExplorationConfig(
            max_depth=max_depth,
            max_hypotheses=max_hypotheses,
            max_total_actions=max_actions,
        )
        handler = DuplicateHandler(config)
        state = handler.start_exploration("finding-1")
        
        # Should allow max_depth increments
        for _ in range(max_depth):
            handler.increment_depth(state.exploration_id)
        
        # Next increment should fail
        with pytest.raises(DuplicateExplorationLimitError):
            handler.increment_depth(state.exploration_id)
    
    @given(
        max_depth=st.integers(min_value=1, max_value=10),
        max_hypotheses=st.integers(min_value=1, max_value=10),
        max_actions=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100, deadline=5000)
    def test_max_hypotheses_enforced(self, max_depth, max_hypotheses, max_actions):
        """**Feature: execution-layer, Property: Duplicate Exploration Limits**
        
        max_hypotheses must be enforced.
        """
        config = DuplicateExplorationConfig(
            max_depth=max_depth,
            max_hypotheses=max_hypotheses,
            max_total_actions=max_actions,
        )
        handler = DuplicateHandler(config)
        state = handler.start_exploration("finding-1")
        
        # Should allow max_hypotheses generations
        for i in range(max_hypotheses):
            handler.generate_hypothesis(state.exploration_id, {"index": i})
        
        # Next generation should fail
        with pytest.raises(DuplicateExplorationLimitError):
            handler.generate_hypothesis(state.exploration_id, {"index": max_hypotheses})
    
    @given(
        max_depth=st.integers(min_value=1, max_value=10),
        max_hypotheses=st.integers(min_value=1, max_value=10),
        max_actions=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100, deadline=5000)
    def test_max_actions_enforced(self, max_depth, max_hypotheses, max_actions):
        """**Feature: execution-layer, Property: Duplicate Exploration Limits**
        
        max_total_actions must be enforced.
        """
        config = DuplicateExplorationConfig(
            max_depth=max_depth,
            max_hypotheses=max_hypotheses,
            max_total_actions=max_actions,
        )
        handler = DuplicateHandler(config)
        state = handler.start_exploration("finding-1")
        
        action = SafeAction(
            action_id="test",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
        
        # Should allow max_actions recordings
        for _ in range(max_actions):
            handler.record_action(state.exploration_id, action)
        
        # Next recording should fail
        with pytest.raises(DuplicateExplorationLimitError):
            handler.record_action(state.exploration_id, action)


# === Property Tests: Scope Validation ===

class TestScopeValidationProperty:
    """
    Property 1: Scope Enforcement
    For any action execution request, the system SHALL validate the target
    against program scope before execution.
    """
    
    @given(domain=st.sampled_from([
        "other-store.myshopify.com",
        "malicious.com",
        "evil-site.net",
        "attacker.org",
        "unauthorized.shop",
        "random-domain.io",
        "test-site.co",
        "example.com",
    ]))
    @settings(max_examples=100, deadline=5000)
    def test_unauthorized_domain_rejected(self, domain):
        """**Feature: execution-layer, Property 1: Scope Enforcement**
        
        Unauthorized domains must be rejected.
        """
        config = ShopifyScopeConfig(
            researcher_store_domains=frozenset({"my-store.myshopify.com"}),
            require_store_attestation=False,
        )
        validator = ShopifyScopeValidator(config)
        
        target = f"https://{domain}/products"
        
        with pytest.raises(ScopeViolationError):
            validator.validate_target(target)
    
    @given(path=st.sampled_from(["/admin", "/checkout", "/account/login", "/password"]))
    @settings(max_examples=100, deadline=5000)
    def test_excluded_paths_rejected(self, path):
        """**Feature: execution-layer, Property 1: Scope Enforcement**
        
        Excluded paths must be rejected.
        """
        config = ShopifyScopeConfig(
            researcher_store_domains=frozenset({"my-store.myshopify.com"}),
            require_store_attestation=False,
        )
        validator = ShopifyScopeValidator(config)
        
        target = f"https://my-store.myshopify.com{path}"
        
        with pytest.raises(ScopeViolationError):
            validator.validate_target(target)


# === Property Tests: Audit Trail Immutability ===

class TestAuditTrailProperty:
    """
    Property 9: Audit Trail Immutability
    For any execution, the audit log SHALL record the action with hash-chaining;
    records SHALL be append-only.
    """
    
    @given(num_records=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50, deadline=10000)
    def test_hash_chain_integrity(self, num_records):
        """**Feature: execution-layer, Property 9: Audit Trail Immutability**
        
        Hash chain must maintain integrity.
        """
        audit_log = ExecutionAuditLog()
        
        for i in range(num_records):
            action = SafeAction(
                action_id=f"action-{i}",
                action_type=SafeActionType.NAVIGATE,
                target="https://example.com",
                parameters={},
                description=f"Action {i}",
            )
            token = ExecutionToken.generate(
                approver_id=f"approver-{i}",
                action=action,
                validity_minutes=15,
            )
            audit_log.record(
                action=action,
                actor=f"actor-{i}",
                outcome="success",
                token=token,
                execution_id=f"exec-{i}",
            )
        
        # Verify chain integrity
        assert audit_log.verify_chain() is True
        assert audit_log.record_count == num_records
    
    @given(num_records=st.integers(min_value=2, max_value=10))
    @settings(max_examples=50, deadline=10000)
    def test_records_linked_by_hash(self, num_records):
        """**Feature: execution-layer, Property 9: Audit Trail Immutability**
        
        Each record must link to previous via hash.
        """
        audit_log = ExecutionAuditLog()
        
        for i in range(num_records):
            action = SafeAction(
                action_id=f"action-{i}",
                action_type=SafeActionType.CLICK,
                target="#button",
                parameters={},
                description=f"Action {i}",
            )
            token = ExecutionToken.generate(
                approver_id="approver",
                action=action,
                validity_minutes=15,
            )
            audit_log.record(
                action=action,
                actor="actor",
                outcome="success",
                token=token,
            )
        
        records = audit_log.get_all_records()
        
        # First record links to genesis
        assert records[0].previous_hash == ExecutionAuditLog.GENESIS_HASH
        
        # Each subsequent record links to previous
        for i in range(1, len(records)):
            assert records[i].previous_hash == records[i-1].record_hash


# === Property Tests: Action Validation ===

class TestActionValidationProperty:
    """
    Property 4: Safe Action Validation
    For any action execution, the system SHALL validate the action is safe
    and non-destructive.
    """
    
    @given(action_type=safe_action_types, action_id=action_ids)
    @settings(max_examples=100, deadline=5000)
    def test_safe_actions_accepted(self, action_type, action_id):
        """**Feature: execution-layer, Property 4: Safe Action Validation**
        
        Actions in SAFE_ACTIONS must be accepted.
        """
        assume(action_id)
        
        validator = ActionValidator()
        action = SafeAction(
            action_id=action_id,
            action_type=action_type,
            target="https://example.com/safe",
            parameters={},
            description="Safe action",
        )
        
        assert validator.validate(action) is True
    
    @given(keyword=st.sampled_from(["password", "secret", "api_key", "captcha", "admin"]))
    @settings(max_examples=100, deadline=5000)
    def test_forbidden_keywords_rejected(self, keyword):
        """**Feature: execution-layer, Property 4: Safe Action Validation**
        
        Actions with forbidden keywords must be rejected.
        """
        validator = ActionValidator()
        action = SafeAction(
            action_id="test",
            action_type=SafeActionType.INPUT_TEXT,
            target="#input",
            parameters={"text": f"my_{keyword}_value"},
            description="Test",
        )
        
        with pytest.raises(ForbiddenActionError):
            validator.validate(action)


# === Property Tests: Video PoC Only for BUG ===

class TestVideoPoCBugOnlyProperty:
    """
    Property 6: Video PoC Generation
    Video PoC SHALL only be generated for MCP-confirmed BUG classification.
    """
    
    @given(classification=st.sampled_from([MCPClassification.SIGNAL, MCPClassification.NO_ISSUE, MCPClassification.COVERAGE_GAP]))
    @settings(max_examples=100, deadline=5000)
    def test_non_bug_rejected(self, classification):
        """**Feature: execution-layer, Property 6: Video PoC BUG Only**
        
        Non-BUG classifications must be rejected.
        """
        generator = VideoPoCGenerator()
        
        mcp_result = MCPVerificationResult(
            verification_id="test",
            finding_id="finding-1",
            classification=classification,
            invariant_violated=None,
            proof_hash=None,
            verified_at=datetime.now(timezone.utc),
        )
        
        video_artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.VIDEO,
            content=b"video",
        )
        bundle = EvidenceBundle(
            bundle_id=make_bundle_id(3),
            execution_id=make_exec_id(3),
            video=video_artifact,
            execution_trace=[{"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "test"}],
        )
        
        with pytest.raises(ArchitecturalViolationError):
            generator.generate("finding-1", mcp_result, bundle)

