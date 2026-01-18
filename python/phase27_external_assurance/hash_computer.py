"""
Phase-27 Hash Computer: External Assurance & Proof

NO AUTHORITY / PROOF ONLY

Computes SHA-256 hashes of artifacts.
All operations require human_initiated=True.
Returns static output only.

This module has NO execution authority, NO enforcement authority.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .types import ArtifactHash, ProofError, DISCLAIMER


def compute_artifact_hash(
    artifact_path: str,
    *,
    human_initiated: bool,
) -> ArtifactHash | ProofError:
    """
    Compute SHA-256 hash of an artifact.
    
    NO AUTHORITY / PROOF ONLY
    
    Args:
        artifact_path: Path to the artifact to hash.
        human_initiated: MUST be True. Keyword-only argument.
    
    Returns:
        ArtifactHash if successful, ProofError if failed.
        Never raises exceptions.
    
    Constraints:
        - human_initiated=True is REQUIRED
        - Returns ProofError if human_initiated=False
        - Returns ProofError if file does not exist
        - NO execution authority
        - NO enforcement authority
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Check human initiation FIRST
    if not human_initiated:
        return ProofError(
            error_type="HUMAN_INITIATION_REQUIRED",
            message="Action requires human_initiated=True",
            timestamp=timestamp,
            disclaimer=DISCLAIMER,
        )
    
    # Check file exists
    path = Path(artifact_path)
    if not path.exists():
        return ProofError(
            error_type="FILE_NOT_FOUND",
            message=f"Artifact not found: {artifact_path}",
            timestamp=timestamp,
            disclaimer=DISCLAIMER,
        )
    
    if not path.is_file():
        return ProofError(
            error_type="NOT_A_FILE",
            message=f"Path is not a file: {artifact_path}",
            timestamp=timestamp,
            disclaimer=DISCLAIMER,
        )
    
    # Compute SHA-256 hash
    try:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        hash_value = sha256.hexdigest()
    except Exception as e:
        return ProofError(
            error_type="HASH_COMPUTATION_ERROR",
            message=f"Failed to compute hash: {e}",
            timestamp=timestamp,
            disclaimer=DISCLAIMER,
        )
    
    return ArtifactHash(
        artifact_path=artifact_path,
        hash_algorithm="SHA-256",
        hash_value=hash_value,
        computed_at=timestamp,
        human_initiated=True,
        disclaimer=DISCLAIMER,
    )
