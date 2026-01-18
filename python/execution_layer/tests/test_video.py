"""
Test Execution Layer Video PoC Generator

Tests for video idempotency guard and MCP BUG requirement.
"""

import pytest
import uuid
from datetime import datetime, timezone

from execution_layer.types import (
    EvidenceType,
    EvidenceArtifact,
    EvidenceBundle,
    VideoPoC,
    MCPClassification,
    MCPVerificationResult,
)
from execution_layer.video import VideoPoCGenerator
from execution_layer.errors import VideoPoCExistsError, ArchitecturalViolationError


# === Test UUID Helpers ===
def make_test_uuid(seed: int = 0) -> str:
    """Generate a valid UUIDv4 for tests.
    
    Uses uuid4() to generate valid UUIDv4 format that passes security validation.
    For deterministic tests, use the seed to create a reproducible UUID.
    """
    # Generate a real UUIDv4 - security validation requires version 4
    return str(uuid.uuid4())


def make_exec_id(n: int = 1) -> str:
    """Generate a test execution ID (valid UUIDv4)."""
    return str(uuid.uuid4())


def make_bundle_id(n: int = 1) -> str:
    """Generate a test bundle ID (valid UUIDv4)."""
    return str(uuid.uuid4())


class TestVideoPoCGenerator:
    """Test VideoPoCGenerator class."""
    
    @pytest.fixture
    def generator(self):
        return VideoPoCGenerator()
    
    @pytest.fixture
    def video_artifact(self):
        return EvidenceArtifact.create(
            artifact_type=EvidenceType.VIDEO,
            content=b"video_content",
        )
    
    @pytest.fixture
    def evidence_bundle(self, video_artifact):
        bundle = EvidenceBundle(
            bundle_id=make_bundle_id(1),
            execution_id=make_exec_id(1),
            video=video_artifact,
            execution_trace=[
                {"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "start"},
                {"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "end"},
            ],
        )
        return bundle
    
    @pytest.fixture
    def mcp_bug_result(self):
        return MCPVerificationResult(
            verification_id="verify-1",
            finding_id="finding-1",
            classification=MCPClassification.BUG,
            invariant_violated="XSS_INJECTION",
            proof_hash="proof123",
            verified_at=datetime.now(timezone.utc),
        )
    
    @pytest.fixture
    def mcp_signal_result(self):
        return MCPVerificationResult(
            verification_id="verify-2",
            finding_id="finding-2",
            classification=MCPClassification.SIGNAL,
            invariant_violated=None,
            proof_hash=None,
            verified_at=datetime.now(timezone.utc),
        )
    
    def test_generate_poc_for_bug(self, generator, mcp_bug_result, evidence_bundle):
        """Should generate VideoPoC for MCP BUG."""
        poc = generator.generate(
            finding_id="finding-1",
            mcp_result=mcp_bug_result,
            evidence_bundle=evidence_bundle,
        )
        assert poc.finding_id == "finding-1"
        assert poc.poc_hash
    
    def test_reject_non_bug(self, generator, mcp_signal_result, evidence_bundle):
        """Should reject VideoPoC for non-BUG classification."""
        with pytest.raises(ArchitecturalViolationError, match="non-BUG"):
            generator.generate(
                finding_id="finding-2",
                mcp_result=mcp_signal_result,
                evidence_bundle=evidence_bundle,
            )
    
    def test_idempotency_guard(self, generator, mcp_bug_result, evidence_bundle):
        """Should reject duplicate VideoPoC for same finding_id."""
        # First generation should succeed
        generator.generate(
            finding_id="finding-1",
            mcp_result=mcp_bug_result,
            evidence_bundle=evidence_bundle,
        )
        
        # Second generation should fail
        with pytest.raises(VideoPoCExistsError, match="already exists"):
            generator.generate(
                finding_id="finding-1",
                mcp_result=mcp_bug_result,
                evidence_bundle=evidence_bundle,
            )
    
    def test_has_poc(self, generator, mcp_bug_result, evidence_bundle):
        """Should track generated PoCs."""
        assert not generator.has_poc("finding-1")
        
        generator.generate(
            finding_id="finding-1",
            mcp_result=mcp_bug_result,
            evidence_bundle=evidence_bundle,
        )
        
        assert generator.has_poc("finding-1")
    
    def test_get_poc(self, generator, mcp_bug_result, evidence_bundle):
        """Should retrieve generated PoC."""
        poc = generator.generate(
            finding_id="finding-1",
            mcp_result=mcp_bug_result,
            evidence_bundle=evidence_bundle,
        )
        
        retrieved = generator.get_poc("finding-1")
        assert retrieved == poc
    
    def test_require_video_in_bundle(self, generator, mcp_bug_result):
        """Should require video content in evidence bundle."""
        bundle_without_video = EvidenceBundle(
            bundle_id=make_bundle_id(2),
            execution_id=make_exec_id(2),
            video=None,  # No video
        )
        
        with pytest.raises(ValueError, match="does not contain video"):
            generator.generate(
                finding_id="finding-1",
                mcp_result=mcp_bug_result,
                evidence_bundle=bundle_without_video,
            )


class TestVideoEnableDecision:
    """Test video enable decision logic."""
    
    @pytest.fixture
    def generator(self):
        return VideoPoCGenerator()
    
    @pytest.fixture
    def mcp_bug_result(self):
        return MCPVerificationResult(
            verification_id="verify-1",
            finding_id="finding-1",
            classification=MCPClassification.BUG,
            invariant_violated="XSS",
            proof_hash="proof123",
            verified_at=datetime.now(timezone.utc),
        )
    
    @pytest.fixture
    def mcp_signal_result(self):
        return MCPVerificationResult(
            verification_id="verify-2",
            finding_id="finding-2",
            classification=MCPClassification.SIGNAL,
            invariant_violated=None,
            proof_hash=None,
            verified_at=datetime.now(timezone.utc),
        )
    
    def test_enable_for_mcp_bug(self, generator, mcp_bug_result):
        """Should enable video for MCP BUG."""
        assert generator.should_enable_video(mcp_result=mcp_bug_result)
    
    def test_disable_for_signal(self, generator, mcp_signal_result):
        """Should not enable video for SIGNAL."""
        assert not generator.should_enable_video(mcp_result=mcp_signal_result)
    
    def test_enable_for_human_escalation(self, generator):
        """Should enable video for human escalation."""
        assert generator.should_enable_video(human_escalation=True)
    
    def test_disable_by_default(self, generator):
        """Should be disabled by default."""
        assert not generator.should_enable_video()
