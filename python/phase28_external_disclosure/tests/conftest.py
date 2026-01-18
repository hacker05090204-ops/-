"""
Phase-28 Test Fixtures

NO AUTHORITY / PRESENTATION ONLY

Provides fixtures for Phase-28 tests.
All fixtures use Phase-27 types (read-only).
"""

import pytest
from datetime import datetime, timezone

# Import Phase-27 types (READ-ONLY)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from phase27_external_assurance import (
    ArtifactHash,
    ComplianceAttestation,
    AuditBundle,
    DISCLAIMER as PHASE27_DISCLAIMER,
)


@pytest.fixture
def sample_artifact_hash() -> ArtifactHash:
    """Sample Phase-27 ArtifactHash for testing."""
    return ArtifactHash(
        artifact_path="test/artifact.py",
        hash_algorithm="SHA-256",
        hash_value="abc123def456",
        computed_at=datetime.now(timezone.utc).isoformat(),
        human_initiated=True,
        disclaimer=PHASE27_DISCLAIMER,
    )


@pytest.fixture
def sample_attestation(sample_artifact_hash: ArtifactHash) -> ComplianceAttestation:
    """Sample Phase-27 ComplianceAttestation for testing."""
    return ComplianceAttestation(
        attestation_id="test-attestation-001",
        timestamp=datetime.now(timezone.utc).isoformat(),
        artifact_hashes=(sample_artifact_hash,),
        phases_covered=(27,),
        human_initiated=True,
        disclaimer=PHASE27_DISCLAIMER,
        actor="HUMAN",
    )


@pytest.fixture
def sample_bundle(sample_attestation: ComplianceAttestation) -> AuditBundle:
    """Sample Phase-27 AuditBundle for testing."""
    return AuditBundle(
        bundle_id="test-bundle-001",
        created_at=datetime.now(timezone.utc).isoformat(),
        attestations=(sample_attestation,),
        governance_docs=("PHASE27_GOVERNANCE_FREEZE.md",),
        bundle_hash="bundle_hash_abc123",
        human_initiated=True,
        disclaimer=PHASE27_DISCLAIMER,
        actor="HUMAN",
    )


@pytest.fixture
def sample_disclosure_context():
    """Sample DisclosureContext for testing (will be created by Phase-28)."""
    # This fixture will be updated once types.py is implemented
    from phase28_external_disclosure import DisclosureContext, DISCLAIMER
    return DisclosureContext(
        context_id="test-context-001",
        provided_by="HUMAN",
        provided_at=datetime.now(timezone.utc).isoformat(),
        context_text="Human-provided disclosure context",
        human_initiated=True,
        disclaimer=DISCLAIMER,
    )


@pytest.fixture
def sample_proof_selection():
    """Sample ProofSelection for testing (will be created by Phase-28)."""
    # This fixture will be updated once types.py is implemented
    from phase28_external_disclosure import ProofSelection, DISCLAIMER
    return ProofSelection(
        selection_id="test-selection-001",
        selected_by="HUMAN",
        selected_at=datetime.now(timezone.utc).isoformat(),
        attestation_ids=("test-attestation-001",),
        bundle_ids=("test-bundle-001",),
        human_initiated=True,
        disclaimer=DISCLAIMER,
    )
