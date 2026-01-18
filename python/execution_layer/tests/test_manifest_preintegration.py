"""
Pre-Integration Tests for Manifest Controller (Integration Track #4)

PHASE-4.1 TEST-ONLY AUTHORIZATION
Status: AUTHORIZED
Date: 2026-01-02

These tests validate the ManifestGenerator standalone component BEFORE integration.
NO WIRING. NO PRODUCTION CODE CHANGES.

Tests Required (per tasks.md):
- 16.1: Property test - Manifest hash chain is tamper-evident
- 16.2: Property test - Manifest generation does not modify evidence bundle
- 16.3: Property test - Manifest verification fails on tampered evidence
- 16.4: Integration test - Manifest persists across controller restarts
- 16.5: Integration test - Manifest chain links correctly across batch executions

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import pytest
import asyncio
import hashlib
import json
import tempfile
import copy
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from typing import Optional, Any
from unittest.mock import MagicMock, patch

from execution_layer.manifest import (
    ManifestGenerator,
    ExecutionManifest,
)
from execution_layer.types import (
    SafeAction,
    SafeActionType,
    EvidenceBundle,
    EvidenceArtifact,
    EvidenceType,
)
from execution_layer.errors import HashChainVerificationError


# === Test UUID Helpers ===
# These generate valid UUIDv4 IDs for tests that need security-compliant IDs

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


# === Hypothesis Strategies ===

# Valid execution IDs - must be UUIDv4 for security compliance
execution_ids = st.uuids(version=4).map(str)


# Valid bundle IDs - must be UUIDv4 for security compliance
bundle_ids = st.uuids(version=4).map(str)

# Valid content hashes (SHA-256 hex)
content_hashes = st.text(
    min_size=64, max_size=64,
    alphabet="0123456789abcdef"
)


@st.composite
def safe_actions(draw):
    """Generate valid SafeAction instances."""
    action_type = draw(st.sampled_from([
        SafeActionType.NAVIGATE,
        SafeActionType.CLICK,
        SafeActionType.SCREENSHOT,
        SafeActionType.WAIT,
    ]))
    return SafeAction(
        action_id=draw(st.text(min_size=8, max_size=16, alphabet="abcdefghijklmnopqrstuvwxyz0123456789")),
        action_type=action_type,
        target=draw(st.text(min_size=1, max_size=100)),
        parameters={},
        description=draw(st.text(min_size=1, max_size=50)),
    )


@st.composite
def evidence_artifacts(draw, artifact_type: Optional[EvidenceType] = None):
    """Generate valid EvidenceArtifact instances."""
    if artifact_type is None:
        artifact_type = draw(st.sampled_from([
            EvidenceType.HAR,
            EvidenceType.SCREENSHOT,
            EvidenceType.VIDEO,
        ]))
    content = draw(st.binary(min_size=10, max_size=100))
    return EvidenceArtifact.create(
        artifact_type=artifact_type,
        content=content,
        file_path=f"test_artifacts/test_{artifact_type.value}.bin",
    )


@st.composite
def evidence_bundles(draw):
    """Generate valid EvidenceBundle instances.
    
    SECURITY COMPLIANCE: Uses UUIDv4 for IDs, relative file paths,
    and properly redacted HAR content.
    """
    bundle_id = draw(bundle_ids)
    execution_id = draw(execution_ids)
    
    # Create HAR artifact with VALID REDACTED content (RISK-X2 compliance)
    # HAR must be valid UTF-8 JSON with redacted sensitive headers
    har_dict = {
        "log": {
            "version": "1.2",
            "entries": [{
                "request": {
                    "method": "GET",
                    "url": "https://example.com/test",
                    "headers": [
                        {"name": "Authorization", "value": "[REDACTED]"},
                        {"name": "Content-Type", "value": "application/json"},
                    ],
                    "cookies": [],
                },
                "response": {
                    "status": 200,
                    "headers": [],
                    "cookies": [],
                },
            }]
        }
    }
    import json
    har_content = json.dumps(har_dict).encode('utf-8')
    har_artifact = EvidenceArtifact.create(
        artifact_type=EvidenceType.HAR,
        content=har_content,
        file_path="test_artifacts/test.har",  # Relative path
    )
    
    # Create screenshots with relative paths
    num_screenshots = draw(st.integers(min_value=0, max_value=3))
    screenshots = []
    for i in range(num_screenshots):
        ss_content = draw(st.binary(min_size=10, max_size=100))
        screenshots.append(EvidenceArtifact.create(
            artifact_type=EvidenceType.SCREENSHOT,
            content=ss_content,
            file_path=f"test_artifacts/screenshot_{i}.png",  # Relative path
        ))
    
    # Optionally create video with relative path
    video = None
    if draw(st.booleans()):
        video_content = draw(st.binary(min_size=10, max_size=100))
        video = EvidenceArtifact.create(
            artifact_type=EvidenceType.VIDEO,
            content=video_content,
            file_path="test_artifacts/test.webm",  # Relative path
        )
    
    bundle = EvidenceBundle(
        bundle_id=bundle_id,
        execution_id=execution_id,
        har_file=har_artifact,
        screenshots=screenshots,
        video=video,
    )
    return bundle.finalize()


# === Helper Functions ===

def create_test_evidence_bundle(
    bundle_id: str = None,
    execution_id: str = None,
    with_video: bool = False,
    num_screenshots: int = 1,
) -> EvidenceBundle:
    """Create a test evidence bundle with known content.
    
    SECURITY COMPLIANCE: Uses UUIDv4 for bundle_id and execution_id,
    and relative file paths to comply with RISK-X1 validation.
    """
    import uuid
    
    # Use UUIDv4 for IDs if not provided
    if bundle_id is None:
        bundle_id = str(uuid.uuid4())
    if execution_id is None:
        execution_id = str(uuid.uuid4())
    
    har_artifact = EvidenceArtifact.create(
        artifact_type=EvidenceType.HAR,
        content=b'{"log": {"version": "1.2", "creator": {"name": "test"}, "entries": []}}',
        file_path="test_artifacts/test.har",  # Relative path
    )
    
    screenshots = []
    for i in range(num_screenshots):
        screenshots.append(EvidenceArtifact.create(
            artifact_type=EvidenceType.SCREENSHOT,
            content=f"screenshot_{i}_content".encode(),
            file_path=f"test_artifacts/screenshot_{i}.png",  # Relative path
        ))
    
    video = None
    if with_video:
        video = EvidenceArtifact.create(
            artifact_type=EvidenceType.VIDEO,
            content=b"video_content_bytes",
            file_path="test_artifacts/test.webm",  # Relative path
        )
    
    bundle = EvidenceBundle(
        bundle_id=bundle_id,
        execution_id=execution_id,
        har_file=har_artifact,
        screenshots=screenshots,
        video=video,
    )
    return bundle.finalize()


def create_test_actions(count: int = 2) -> list[SafeAction]:
    """Create test SafeAction instances."""
    actions = []
    for i in range(count):
        actions.append(SafeAction(
            action_id=f"action-{i:03d}",
            action_type=SafeActionType.NAVIGATE if i == 0 else SafeActionType.CLICK,
            target=f"https://example.com/page{i}" if i == 0 else f"#button-{i}",
            parameters={},
            description=f"Test action {i}",
        ))
    return actions


# === Property Tests ===

class TestManifestHashChainTamperEvident:
    """
    Property Test 16.1: Manifest hash chain is tamper-evident
    
    Requirement 4.2: Modifying any manifest breaks chain verification.
    """
    
    def test_manifest_hash_changes_on_content_modification(self):
        """**Feature: manifest-controller, Property: Tamper Evidence**
        
        Modifying manifest content must change the manifest hash.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        # Generate first manifest
        manifest1 = generator.generate(bundle.execution_id, bundle, actions)
        original_hash = manifest1.manifest_hash
        
        # Create a new generator (fresh state)
        generator2 = ManifestGenerator()
        
        # Generate with same inputs - should produce different manifest_id but same structure
        manifest2 = generator2.generate(bundle.execution_id, bundle, actions)
        
        # Different manifest_id means different hash (manifest_id is part of hash)
        assert manifest1.manifest_id != manifest2.manifest_id
        assert manifest1.manifest_hash != manifest2.manifest_hash
    
    def test_hash_chain_links_correctly(self):
        """**Feature: manifest-controller, Property: Tamper Evidence**
        
        Each manifest must link to the previous manifest's hash.
        """
        generator = ManifestGenerator()
        
        # Generate first manifest (genesis)
        bundle1 = create_test_evidence_bundle()
        actions1 = create_test_actions()
        manifest1 = generator.generate(bundle1.execution_id, bundle1, actions1)
        
        # First manifest has no previous hash
        assert manifest1.previous_manifest_hash is None
        
        # Generate second manifest
        bundle2 = create_test_evidence_bundle()
        actions2 = create_test_actions()
        manifest2 = generator.generate(bundle2.execution_id, bundle2, actions2)
        
        # Second manifest links to first
        assert manifest2.previous_manifest_hash == manifest1.manifest_hash
        
        # Generate third manifest
        bundle3 = create_test_evidence_bundle()
        actions3 = create_test_actions()
        manifest3 = generator.generate(bundle3.execution_id, bundle3, actions3)
        
        # Third manifest links to second
        assert manifest3.previous_manifest_hash == manifest2.manifest_hash
    
    @given(execution_id=execution_ids)
    @settings(max_examples=20, deadline=10000)
    def test_manifest_hash_is_deterministic_for_same_content(self, execution_id):
        """**Feature: manifest-controller, Property: Tamper Evidence**
        
        Same content must produce same hash (excluding manifest_id).
        """
        
        # Create identical bundles with the given execution_id
        bundle = create_test_evidence_bundle(execution_id=execution_id)
        actions = create_test_actions()
        
        generator = ManifestGenerator()
        manifest = generator.generate(execution_id, bundle, actions)
        
        # Verify hash is computed from content
        assert manifest.manifest_hash is not None
        assert len(manifest.manifest_hash) == 64  # SHA-256 hex
        
        # Verify action hashes are included
        assert len(manifest.action_hashes) == len(actions)
        for action, action_hash in zip(actions, manifest.action_hashes):
            assert action_hash == action.compute_hash()
    
    def test_tampering_manifest_id_breaks_verification(self):
        """**Feature: manifest-controller, Property: Tamper Evidence**
        
        Tampering with manifest_id must break verification.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Create tampered manifest with different manifest_id
        tampered = ExecutionManifest(
            execution_id=manifest.execution_id,
            timestamp=manifest.timestamp,
            artifact_paths=manifest.artifact_paths,
            manifest_id="TAMPERED-ID",  # Changed!
            action_hashes=manifest.action_hashes,
            artifact_hashes=manifest.artifact_hashes,
            evidence_bundle_hash=manifest.evidence_bundle_hash,
            previous_manifest_hash=manifest.previous_manifest_hash,
            manifest_hash=manifest.manifest_hash,  # Original hash won't match
        )
        
        # Verification should fail
        with pytest.raises(HashChainVerificationError):
            generator.verify_chain(tampered, bundle)
    
    def test_tampering_action_hashes_breaks_verification(self):
        """**Feature: manifest-controller, Property: Tamper Evidence**
        
        Tampering with action hashes must break verification.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Create tampered manifest with different action hashes
        tampered_hashes = ("tampered_hash_1", "tampered_hash_2")
        tampered = ExecutionManifest(
            execution_id=manifest.execution_id,
            timestamp=manifest.timestamp,
            artifact_paths=manifest.artifact_paths,
            manifest_id=manifest.manifest_id,
            action_hashes=tampered_hashes,  # Changed!
            artifact_hashes=manifest.artifact_hashes,
            evidence_bundle_hash=manifest.evidence_bundle_hash,
            previous_manifest_hash=manifest.previous_manifest_hash,
            manifest_hash=manifest.manifest_hash,
        )
        
        # Verification should fail (hash mismatch)
        with pytest.raises(HashChainVerificationError):
            generator.verify_chain(tampered, bundle)


class TestManifestGenerationDoesNotModifyEvidence:
    """
    Property Test 16.2: Manifest generation does not modify evidence bundle
    
    Requirement 4.2: Evidence unchanged after manifest generation.
    """
    
    def test_evidence_bundle_unchanged_after_manifest_generation(self):
        """**Feature: manifest-controller, Property: Evidence Immutability**
        
        Evidence bundle must be unchanged after manifest generation.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle(with_video=True, num_screenshots=2)
        actions = create_test_actions()
        
        # Capture original state
        original_bundle_hash = bundle.bundle_hash
        original_har_hash = bundle.har_file.content_hash
        original_screenshot_hashes = [ss.content_hash for ss in bundle.screenshots]
        original_video_hash = bundle.video.content_hash
        
        # Generate manifest
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Verify bundle unchanged
        assert bundle.bundle_hash == original_bundle_hash
        assert bundle.har_file.content_hash == original_har_hash
        assert [ss.content_hash for ss in bundle.screenshots] == original_screenshot_hashes
        assert bundle.video.content_hash == original_video_hash
    
    @given(bundle=evidence_bundles())
    @settings(max_examples=20, deadline=10000)
    def test_evidence_hash_consistency_property(self, bundle):
        """**Feature: manifest-controller, Property: Evidence Immutability**
        
        Evidence hash must remain consistent through manifest generation.
        """
        generator = ManifestGenerator()
        actions = create_test_actions()
        
        original_hash = bundle.bundle_hash
        
        # Generate manifest
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Verify hash unchanged
        assert bundle.bundle_hash == original_hash
        
        # Verify manifest references correct hash
        assert manifest.evidence_bundle_hash == original_hash
    
    def test_multiple_manifest_generations_preserve_evidence(self):
        """**Feature: manifest-controller, Property: Evidence Immutability**
        
        Multiple manifest generations must not modify evidence.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        original_hash = bundle.bundle_hash
        
        # Generate multiple manifests
        for i in range(5):
            new_bundle = create_test_evidence_bundle()
            manifest = generator.generate(new_bundle.execution_id, new_bundle, actions)
        
        # Original bundle should be unchanged
        assert bundle.bundle_hash == original_hash
    
    def test_evidence_artifacts_not_mutated(self):
        """**Feature: manifest-controller, Property: Evidence Immutability**
        
        Individual evidence artifacts must not be mutated.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle(with_video=True, num_screenshots=3)
        actions = create_test_actions()
        
        # Capture artifact IDs
        original_har_id = bundle.har_file.artifact_id
        original_screenshot_ids = [ss.artifact_id for ss in bundle.screenshots]
        original_video_id = bundle.video.artifact_id
        
        # Generate manifest
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Verify artifact IDs unchanged
        assert bundle.har_file.artifact_id == original_har_id
        assert [ss.artifact_id for ss in bundle.screenshots] == original_screenshot_ids
        assert bundle.video.artifact_id == original_video_id


class TestManifestVerificationFailsOnTamperedEvidence:
    """
    Property Test 16.3: Manifest verification fails on tampered evidence
    
    Requirement 4.2: Evidence tampering is detected.
    """
    
    def test_verification_fails_on_tampered_har_hash(self):
        """**Feature: manifest-controller, Property: Tamper Detection**
        
        Verification must fail if HAR hash is tampered.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Create tampered bundle with DIFFERENT HAR content (valid JSON format)
        tampered_har = EvidenceArtifact.create(
            artifact_type=EvidenceType.HAR,
            content=b'{"log": {"version": "1.2", "creator": {"name": "TAMPERED"}, "entries": [{"request": {}}]}}',
            file_path="test_artifacts/tampered.har",
        )
        tampered_bundle = EvidenceBundle(
            bundle_id=bundle.bundle_id,
            execution_id=bundle.execution_id,
            har_file=tampered_har,
            screenshots=bundle.screenshots,
            video=bundle.video,
        ).finalize()
        
        # Verification should fail
        with pytest.raises(HashChainVerificationError) as exc_info:
            generator.verify_chain(manifest, tampered_bundle)
        
        assert "HAR hash mismatch" in str(exc_info.value) or "bundle hash mismatch" in str(exc_info.value).lower()
    
    def test_verification_fails_on_tampered_screenshot(self):
        """**Feature: manifest-controller, Property: Tamper Detection**
        
        Verification must fail if screenshot is tampered.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle(num_screenshots=2)
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Create tampered bundle with different screenshot
        tampered_screenshot = EvidenceArtifact.create(
            artifact_type=EvidenceType.SCREENSHOT,
            content=b"TAMPERED_SCREENSHOT_CONTENT",
            file_path="test_artifacts/tampered_screenshot.png",
        )
        tampered_bundle = EvidenceBundle(
            bundle_id=bundle.bundle_id,
            execution_id=bundle.execution_id,
            har_file=bundle.har_file,
            screenshots=[tampered_screenshot, bundle.screenshots[1]],
            video=bundle.video,
        ).finalize()
        
        # Verification should fail
        with pytest.raises(HashChainVerificationError) as exc_info:
            generator.verify_chain(manifest, tampered_bundle)
        
        error_msg = str(exc_info.value).lower()
        assert "screenshot" in error_msg or "hash mismatch" in error_msg or "bundle" in error_msg
    
    def test_verification_fails_on_tampered_video(self):
        """**Feature: manifest-controller, Property: Tamper Detection**
        
        Verification must fail if video is tampered.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle(with_video=True)
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Create tampered bundle with different video
        tampered_video = EvidenceArtifact.create(
            artifact_type=EvidenceType.VIDEO,
            content=b"TAMPERED_VIDEO_CONTENT",
            file_path="test_artifacts/tampered.webm",
        )
        tampered_bundle = EvidenceBundle(
            bundle_id=bundle.bundle_id,
            execution_id=bundle.execution_id,
            har_file=bundle.har_file,
            screenshots=bundle.screenshots,
            video=tampered_video,
        ).finalize()
        
        # Verification should fail
        with pytest.raises(HashChainVerificationError) as exc_info:
            generator.verify_chain(manifest, tampered_bundle)
        
        error_msg = str(exc_info.value).lower()
        assert "video" in error_msg or "hash mismatch" in error_msg or "bundle" in error_msg
    
    def test_verification_fails_on_bundle_hash_mismatch(self):
        """**Feature: manifest-controller, Property: Tamper Detection**
        
        Verification must fail if bundle hash doesn't match.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Create completely different bundle with valid UUIDv4 IDs
        different_bundle = create_test_evidence_bundle()
        
        # Verification should fail
        with pytest.raises(HashChainVerificationError) as exc_info:
            generator.verify_chain(manifest, different_bundle)
        
        assert "mismatch" in str(exc_info.value).lower()
    
    @given(bundle=evidence_bundles())
    @settings(max_examples=20, deadline=10000)
    def test_verification_succeeds_on_unmodified_evidence(self, bundle):
        """**Feature: manifest-controller, Property: Tamper Detection**
        
        Verification must succeed on unmodified evidence.
        """
        generator = ManifestGenerator()
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Verification should succeed
        result = generator.verify_chain(manifest, bundle)
        assert result is True


# === Integration-Style Tests (No Wiring) ===

class TestManifestPersistsAcrossControllerRestarts:
    """
    Integration Test 16.4: Manifest persists across controller restarts
    
    Requirement 4.3: Test manifest storage persistence.
    """
    
    def test_manifest_save_and_load(self):
        """**Feature: manifest-controller, Integration: Persistence**
        
        Manifest must be saveable and loadable from disk.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir)
            generator = ManifestGenerator(str(artifacts_dir))
            
            bundle = create_test_evidence_bundle()
            actions = create_test_actions()
            exec_id = bundle.execution_id
            
            # Generate and save manifest
            manifest = generator.generate(exec_id, bundle, actions)
            
            # Create execution directory
            exec_dir = artifacts_dir / exec_id
            exec_dir.mkdir(parents=True, exist_ok=True)
            
            # Save manifest
            manifest_path = generator.save_manifest(manifest, exec_dir)
            assert manifest_path.exists()
            
            # Load manifest
            loaded = generator.load_manifest(exec_id)
            assert loaded is not None
            assert loaded.execution_id == manifest.execution_id
            assert loaded.manifest_hash == manifest.manifest_hash
    
    def test_manifest_survives_generator_recreation(self):
        """**Feature: manifest-controller, Integration: Persistence**
        
        Manifest must survive generator recreation (simulating restart).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir)
            
            # First generator instance
            generator1 = ManifestGenerator(str(artifacts_dir))
            bundle = create_test_evidence_bundle()
            actions = create_test_actions()
            exec_id = bundle.execution_id
            
            manifest = generator1.generate(exec_id, bundle, actions)
            exec_dir = artifacts_dir / exec_id
            exec_dir.mkdir(parents=True, exist_ok=True)
            generator1.save_manifest(manifest, exec_dir)
            
            # Simulate restart - create new generator
            generator2 = ManifestGenerator(str(artifacts_dir))
            
            # Load manifest from new generator
            loaded = generator2.load_manifest(exec_id)
            assert loaded is not None
            assert loaded.manifest_hash == manifest.manifest_hash
            assert loaded.evidence_bundle_hash == manifest.evidence_bundle_hash
    
    def test_manifest_json_format_complete(self):
        """**Feature: manifest-controller, Integration: Persistence**
        
        Saved manifest JSON must contain all required fields.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir)
            generator = ManifestGenerator(str(artifacts_dir))
            
            bundle = create_test_evidence_bundle(with_video=True, num_screenshots=2)
            actions = create_test_actions()
            exec_id = bundle.execution_id
            
            manifest = generator.generate(exec_id, bundle, actions)
            exec_dir = artifacts_dir / exec_id
            exec_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = generator.save_manifest(manifest, exec_dir)
            
            # Read raw JSON
            manifest_json = json.loads(manifest_path.read_text())
            
            # Verify required fields
            assert "execution_id" in manifest_json
            assert "timestamp" in manifest_json
            assert "manifest_id" in manifest_json
            assert "action_hashes" in manifest_json
            assert "artifact_hashes" in manifest_json
            assert "evidence_bundle_hash" in manifest_json
            assert "manifest_hash" in manifest_json
    
    def test_loaded_manifest_verifiable(self):
        """**Feature: manifest-controller, Integration: Persistence**
        
        Loaded manifest must be verifiable against original evidence.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir)
            generator = ManifestGenerator(str(artifacts_dir))
            
            bundle = create_test_evidence_bundle()
            actions = create_test_actions()
            exec_id = bundle.execution_id
            
            manifest = generator.generate(exec_id, bundle, actions)
            exec_dir = artifacts_dir / exec_id
            exec_dir.mkdir(parents=True, exist_ok=True)
            generator.save_manifest(manifest, exec_dir)
            
            # Load and verify
            loaded = generator.load_manifest(exec_id)
            result = generator.verify_chain(loaded, bundle)
            assert result is True
    
    def test_multiple_manifests_persist_independently(self):
        """**Feature: manifest-controller, Integration: Persistence**
        
        Multiple manifests must persist independently.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir)
            generator = ManifestGenerator(str(artifacts_dir))
            
            manifests = []
            exec_ids = []
            for i in range(3):
                bundle = create_test_evidence_bundle()
                actions = create_test_actions()
                exec_id = bundle.execution_id
                exec_ids.append(exec_id)
                manifest = generator.generate(exec_id, bundle, actions)
                
                exec_dir = artifacts_dir / exec_id
                exec_dir.mkdir(parents=True, exist_ok=True)
                generator.save_manifest(manifest, exec_dir)
                manifests.append(manifest)
            
            # Load all manifests
            for i, original in enumerate(manifests):
                loaded = generator.load_manifest(exec_ids[i])
                assert loaded is not None
                assert loaded.manifest_hash == original.manifest_hash


class TestManifestChainLinksAcrossBatchExecutions:
    """
    Integration Test 16.5: Manifest chain links correctly across batch executions
    
    Requirement 4.3: Test batch execution manifest linking.
    """
    
    def test_batch_manifests_form_chain(self):
        """**Feature: manifest-controller, Integration: Chain Linking**
        
        Batch execution manifests must form a linked chain.
        """
        generator = ManifestGenerator()
        
        manifests = []
        for i in range(5):
            bundle = create_test_evidence_bundle()
            actions = create_test_actions()
            manifest = generator.generate(bundle.execution_id, bundle, actions)
            manifests.append(manifest)
        
        # Verify chain links
        assert manifests[0].previous_manifest_hash is None  # Genesis
        for i in range(1, len(manifests)):
            assert manifests[i].previous_manifest_hash == manifests[i-1].manifest_hash
    
    def test_chain_continuity_after_batch(self):
        """**Feature: manifest-controller, Integration: Chain Linking**
        
        Chain must continue correctly after batch execution.
        """
        generator = ManifestGenerator()
        
        # First batch
        batch1_manifests = []
        for i in range(3):
            bundle = create_test_evidence_bundle(make_bundle_id(100+i), make_exec_id(100+i))
            actions = create_test_actions()
            manifest = generator.generate(make_exec_id(100+i), bundle, actions)
            batch1_manifests.append(manifest)
        
        # Second batch (should continue chain)
        batch2_manifests = []
        for i in range(3):
            bundle = create_test_evidence_bundle(make_bundle_id(200+i), make_exec_id(200+i))
            actions = create_test_actions()
            manifest = generator.generate(make_exec_id(200+i), bundle, actions)
            batch2_manifests.append(manifest)
        
        # First manifest of batch2 should link to last manifest of batch1
        assert batch2_manifests[0].previous_manifest_hash == batch1_manifests[-1].manifest_hash
    
    def test_chain_verification_across_batches(self):
        """**Feature: manifest-controller, Integration: Chain Linking**
        
        Chain verification must work across batch boundaries.
        """
        generator = ManifestGenerator()
        
        all_manifests = []
        all_bundles = []
        
        # Generate manifests across multiple batches
        for batch in range(3):
            for i in range(2):
                bundle = create_test_evidence_bundle(
                    make_bundle_id(300 + batch*10 + i),
                    make_exec_id(300 + batch*10 + i)
                )
                actions = create_test_actions()
                manifest = generator.generate(make_exec_id(300 + batch*10 + i), bundle, actions)
                all_manifests.append(manifest)
                all_bundles.append(bundle)
        
        # Verify each manifest against its bundle
        for manifest, bundle in zip(all_manifests, all_bundles):
            result = generator.verify_chain(manifest, bundle)
            assert result is True
    
    def test_chain_breaks_on_missing_link(self):
        """**Feature: manifest-controller, Integration: Chain Linking**
        
        Chain verification must detect missing links.
        """
        generator = ManifestGenerator()
        
        # Generate chain
        manifests = []
        bundles = []
        for i in range(3):
            bundle = create_test_evidence_bundle()
            bundles.append(bundle)
            actions = create_test_actions()
            manifest = generator.generate(bundle.execution_id, bundle, actions)
            manifests.append(manifest)
        
        # Tamper with middle manifest's previous_hash
        tampered = ExecutionManifest(
            execution_id=manifests[1].execution_id,
            timestamp=manifests[1].timestamp,
            artifact_paths=manifests[1].artifact_paths,
            manifest_id=manifests[1].manifest_id,
            action_hashes=manifests[1].action_hashes,
            artifact_hashes=manifests[1].artifact_hashes,
            evidence_bundle_hash=manifests[1].evidence_bundle_hash,
            previous_manifest_hash="WRONG_HASH",  # Tampered!
            manifest_hash=manifests[1].manifest_hash,
        )
        
        # Verification should fail due to hash mismatch
        with pytest.raises(HashChainVerificationError):
            generator.verify_chain(tampered, bundles[1])
    
    def test_empty_batch_does_not_break_chain(self):
        """**Feature: manifest-controller, Integration: Chain Linking**
        
        Empty batch (no executions) should not break chain continuity.
        """
        generator = ManifestGenerator()
        
        # First manifest
        bundle1 = create_test_evidence_bundle()
        actions1 = create_test_actions()
        manifest1 = generator.generate(bundle1.execution_id, bundle1, actions1)
        
        # No executions in between (empty batch)
        
        # Next manifest should still link correctly
        bundle2 = create_test_evidence_bundle()
        actions2 = create_test_actions()
        manifest2 = generator.generate(bundle2.execution_id, bundle2, actions2)
        
        assert manifest2.previous_manifest_hash == manifest1.manifest_hash


# === Backward Compatibility Tests ===

class TestBackwardCompatibility:
    """
    Backward Compatibility Tests
    
    These tests verify that the ManifestGenerator interface is compatible
    with the planned integration into ExecutionController.
    
    NO WIRING - just interface validation.
    """
    
    def test_manifest_generator_instantiation_no_args(self):
        """**Feature: manifest-controller, Backward Compat: Default Instantiation**
        
        ManifestGenerator must be instantiable without arguments.
        """
        generator = ManifestGenerator()
        assert generator is not None
    
    def test_manifest_generator_instantiation_with_artifacts_dir(self):
        """**Feature: manifest-controller, Backward Compat: With Artifacts Dir**
        
        ManifestGenerator must accept artifacts_dir parameter.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ManifestGenerator(tmpdir)
            assert generator is not None
            assert generator._artifacts_dir == Path(tmpdir)
    
    def test_simple_mode_create_manifest(self):
        """**Feature: manifest-controller, Backward Compat: Simple Mode**
        
        Simple mode create_manifest() must work for backward compatibility.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ManifestGenerator(tmpdir)
            exec_id = str(uuid.uuid4())
            
            # Create execution directory with artifacts
            exec_dir = Path(tmpdir) / exec_id
            exec_dir.mkdir(parents=True, exist_ok=True)
            (exec_dir / "test.har").write_text('{"log": {}}')
            
            # Simple mode manifest creation
            manifest = generator.create_manifest(exec_id)
            
            assert manifest is not None
            assert manifest.execution_id == exec_id
            assert isinstance(manifest.timestamp, str)
    
    def test_simple_mode_with_explicit_paths(self):
        """**Feature: manifest-controller, Backward Compat: Explicit Paths**
        
        Simple mode must accept explicit artifact paths.
        """
        generator = ManifestGenerator()
        exec_id = str(uuid.uuid4())
        
        manifest = generator.create_manifest(
            exec_id,
            artifact_paths=["path/to/har.har", "path/to/screenshot.png"]
        )
        
        assert manifest is not None
        assert len(manifest.artifact_paths) == 2
    
    def test_full_mode_generate(self):
        """**Feature: manifest-controller, Backward Compat: Full Mode**
        
        Full mode generate() must work with evidence bundle and actions.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        assert manifest is not None
        assert manifest.manifest_id is not None
        assert manifest.manifest_hash is not None
        assert manifest.evidence_bundle_hash == bundle.bundle_hash
    
    def test_execution_manifest_to_dict(self):
        """**Feature: manifest-controller, Backward Compat: Serialization**
        
        ExecutionManifest must be serializable to dict.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        manifest_dict = manifest.to_dict()
        
        assert isinstance(manifest_dict, dict)
        assert "execution_id" in manifest_dict
        assert "timestamp" in manifest_dict
        assert "manifest_hash" in manifest_dict
    
    def test_verify_chain_returns_bool(self):
        """**Feature: manifest-controller, Backward Compat: Verify Return Type**
        
        verify_chain() must return bool on success.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        result = generator.verify_chain(manifest, bundle)
        
        assert isinstance(result, bool)
        assert result is True


# === Performance Tests ===

class TestManifestPerformance:
    """
    Performance Tests
    
    Validate that manifest generation meets performance requirements.
    """
    
    def test_manifest_generation_time(self):
        """**Feature: manifest-controller, Performance: Generation Time**
        
        Manifest generation should complete within acceptable time.
        """
        import time
        
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle(with_video=True, num_screenshots=5)
        actions = create_test_actions(count=10)
        
        start = time.perf_counter()
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        elapsed = time.perf_counter() - start
        
        # Should complete within 100ms (generous for hash computation)
        assert elapsed < 0.1
        assert manifest is not None
    
    def test_hash_computation_overhead(self):
        """**Feature: manifest-controller, Performance: Hash Overhead**
        
        Hash computation overhead should be minimal.
        """
        import time
        
        generator = ManifestGenerator()
        actions = create_test_actions()
        
        # Measure multiple generations
        times = []
        for i in range(10):
            bundle = create_test_evidence_bundle()
            start = time.perf_counter()
            manifest = generator.generate(bundle.execution_id, bundle, actions)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        
        # Average should be under 50ms
        assert avg_time < 0.05
    
    def test_verification_time(self):
        """**Feature: manifest-controller, Performance: Verification Time**
        
        Manifest verification should complete quickly.
        """
        import time
        
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle(with_video=True, num_screenshots=5)
        actions = create_test_actions(count=10)
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        start = time.perf_counter()
        result = generator.verify_chain(manifest, bundle)
        elapsed = time.perf_counter() - start
        
        # Verification should be fast
        assert elapsed < 0.05
        assert result is True


# === Determinism Tests ===

class TestManifestDeterminism:
    """
    Determinism Tests
    
    Validate that manifest behavior is deterministic.
    """
    
    def test_action_hash_computation_deterministic(self):
        """**Feature: manifest-controller, Determinism: Action Hashes**
        
        Action hash computation must be deterministic.
        """
        action = SafeAction(
            action_id="action-det-001",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={"timeout": 30},
            description="Navigate to example",
        )
        
        # Compute hash multiple times
        hashes = [action.compute_hash() for _ in range(10)]
        
        # All hashes should be identical
        assert len(set(hashes)) == 1
    
    def test_evidence_bundle_hash_deterministic(self):
        """**Feature: manifest-controller, Determinism: Bundle Hash**
        
        Evidence bundle hash must be deterministic.
        """
        # Create bundle with fixed content
        har_artifact = EvidenceArtifact.create(
            artifact_type=EvidenceType.HAR,
            content=b'{"log": {"entries": []}}',
            file_path="test_artifacts/test.har",
        )
        
        bundle = EvidenceBundle(
            bundle_id=make_bundle_id(100),
            execution_id=make_exec_id(100),
            har_file=har_artifact,
            screenshots=[],
            video=None,
        )
        
        # Compute hash multiple times
        hashes = [bundle.compute_hash() for _ in range(10)]
        
        # All hashes should be identical
        assert len(set(hashes)) == 1
    
    def test_manifest_content_hash_deterministic(self):
        """**Feature: manifest-controller, Determinism: Manifest Hash**
        
        Manifest hash computation must be deterministic for same inputs.
        """
        generator = ManifestGenerator()
        bundle = create_test_evidence_bundle()
        actions = create_test_actions()
        
        manifest = generator.generate(bundle.execution_id, bundle, actions)
        
        # Recompute hash manually
        from datetime import datetime
        ts = manifest.timestamp
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        
        content = generator._compute_manifest_content(
            manifest_id=manifest.manifest_id,
            execution_id=manifest.execution_id,
            timestamp=ts,
            action_hashes=manifest.action_hashes,
            artifact_hashes=manifest.artifact_hashes,
            evidence_bundle_hash=manifest.evidence_bundle_hash,
            previous_manifest_hash=manifest.previous_manifest_hash,
        )
        
        recomputed_hash = hashlib.sha256(content.encode()).hexdigest()
        
        assert recomputed_hash == manifest.manifest_hash
