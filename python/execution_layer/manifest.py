"""
Execution Layer Manifest Generator

Cryptographic manifest for execution evidence with SHA-256 hashes
and hash-chain linking for tamper-evident audit trail.

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, Union
import hashlib
import json
import secrets

from execution_layer.types import SafeAction, EvidenceBundle
from execution_layer.errors import HashChainVerificationError


@dataclass(frozen=True)
class ExecutionManifest:
    """Cryptographic manifest for execution evidence.
    
    Supports both simple mode (backward compatible) and full mode (with hashes).
    """
    execution_id: str
    timestamp: Union[datetime, str]
    artifact_paths: Union[dict[str, str], list[str]]
    # Optional fields for full mode
    manifest_id: Optional[str] = None
    action_hashes: tuple[str, ...] = ()
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    evidence_bundle_hash: Optional[str] = None
    previous_manifest_hash: Optional[str] = None
    manifest_hash: Optional[str] = None
    failure_count: int = 0

    def __post_init__(self) -> None:
        if not self.execution_id:
            raise ValueError("ExecutionManifest must have execution_id")

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to dictionary for JSON serialization."""
        ts = self.timestamp
        if isinstance(ts, datetime):
            ts = ts.isoformat()
        
        result: dict[str, Any] = {
            "execution_id": self.execution_id,
            "timestamp": ts,
            "artifact_paths": list(self.artifact_paths) if isinstance(self.artifact_paths, list) else self.artifact_paths,
        }
        
        # Add optional fields if present (full mode)
        if self.manifest_id:
            result["manifest_id"] = self.manifest_id
        if self.action_hashes:
            result["action_hashes"] = list(self.action_hashes)
        if self.artifact_hashes:
            result["artifact_hashes"] = self.artifact_hashes
        if self.evidence_bundle_hash:
            result["evidence_bundle_hash"] = self.evidence_bundle_hash
        if self.previous_manifest_hash:
            result["previous_manifest_hash"] = self.previous_manifest_hash
        if self.manifest_hash:
            result["manifest_hash"] = self.manifest_hash
        if self.failure_count > 0:
            result["failure_count"] = self.failure_count
        
        return result


class ManifestGenerator:
    """Generate cryptographic manifests for execution evidence.
    
    Supports two modes:
    1. Simple mode (backward compatible): create_manifest(), save_manifest(), load_manifest()
    2. Full mode (hardening): generate(), verify_chain()
    
    OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
    """
    
    def __init__(self, artifacts_dir: Optional[str] = None) -> None:
        self._artifacts_dir = Path(artifacts_dir) if artifacts_dir else None
        self._previous_manifest_hash: Optional[str] = None

    # =========================================================================
    # Simple mode (backward compatible)
    # =========================================================================
    
    def create_manifest(
        self,
        execution_id: str,
        artifact_paths: Optional[list[str]] = None,
    ) -> ExecutionManifest:
        """Create a simple manifest (backward compatible).
        
        Auto-discovers artifact paths if not provided.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Auto-discover artifacts if not provided
        if artifact_paths is None:
            artifact_paths = self._discover_artifacts(execution_id)
        
        return ExecutionManifest(
            execution_id=execution_id,
            timestamp=timestamp,
            artifact_paths=artifact_paths,
        )
    
    def _discover_artifacts(self, execution_id: str) -> list[str]:
        """Auto-discover artifact paths for an execution."""
        if not self._artifacts_dir:
            return []
        
        exec_dir = self._artifacts_dir / execution_id
        if not exec_dir.exists():
            return []
        
        paths: list[str] = []
        for path in exec_dir.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self._artifacts_dir)
                paths.append(str(rel_path))
        
        return sorted(paths)
    
    def save_manifest(
        self,
        manifest: ExecutionManifest,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Save manifest to execution_manifest.json."""
        if output_dir is None and self._artifacts_dir:
            output_dir = self._artifacts_dir / manifest.execution_id
        elif output_dir is None:
            raise ValueError("output_dir required when artifacts_dir not set")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "execution_manifest.json"
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2))
        return manifest_path
    
    def load_manifest(self, execution_id: str) -> Optional[ExecutionManifest]:
        """Load manifest from JSON file."""
        if not self._artifacts_dir:
            return None
        
        manifest_path = self._artifacts_dir / execution_id / "execution_manifest.json"
        if not manifest_path.exists():
            return None
        
        data = json.loads(manifest_path.read_text())
        return ExecutionManifest(
            execution_id=data["execution_id"],
            timestamp=data["timestamp"],
            artifact_paths=data.get("artifact_paths", []),
            manifest_id=data.get("manifest_id"),
            action_hashes=tuple(data.get("action_hashes", [])),
            artifact_hashes=data.get("artifact_hashes", {}),
            evidence_bundle_hash=data.get("evidence_bundle_hash"),
            previous_manifest_hash=data.get("previous_manifest_hash"),
            manifest_hash=data.get("manifest_hash"),
            failure_count=data.get("failure_count", 0),
        )

    # =========================================================================
    # Full mode (hardening with hash chain)
    # =========================================================================
    
    def generate(
        self,
        execution_id: str,
        evidence_bundle: EvidenceBundle,
        actions: list[SafeAction],
    ) -> ExecutionManifest:
        """Generate execution manifest with SHA-256 hashes (full mode)."""
        manifest_id = secrets.token_urlsafe(16)
        timestamp = datetime.now(timezone.utc)
        
        # Compute action hashes
        action_hashes = tuple(self.compute_action_hashes(actions))
        
        # Compute artifact paths and hashes
        artifact_paths: dict[str, str] = {}
        artifact_hashes: dict[str, str] = {}
        
        if evidence_bundle.har_file:
            artifact_paths["har"] = evidence_bundle.har_file.file_path or ""
            artifact_hashes["har"] = evidence_bundle.har_file.content_hash
        
        for i, screenshot in enumerate(evidence_bundle.screenshots):
            key = f"screenshot_{i}"
            artifact_paths[key] = screenshot.file_path or ""
            artifact_hashes[key] = screenshot.content_hash
        
        if evidence_bundle.video:
            artifact_paths["video"] = evidence_bundle.video.file_path or ""
            artifact_hashes["video"] = evidence_bundle.video.content_hash
        
        # Compute manifest hash
        manifest_content = self._compute_manifest_content(
            manifest_id=manifest_id,
            execution_id=execution_id,
            timestamp=timestamp,
            action_hashes=action_hashes,
            artifact_hashes=artifact_hashes,
            evidence_bundle_hash=evidence_bundle.bundle_hash,
            previous_manifest_hash=self._previous_manifest_hash,
            failure_count=evidence_bundle.failure_count,
        )
        manifest_hash = hashlib.sha256(manifest_content.encode()).hexdigest()
        
        manifest = ExecutionManifest(
            execution_id=execution_id,
            timestamp=timestamp,
            artifact_paths=artifact_paths,
            manifest_id=manifest_id,
            action_hashes=action_hashes,
            artifact_hashes=artifact_hashes,
            evidence_bundle_hash=evidence_bundle.bundle_hash,
            previous_manifest_hash=self._previous_manifest_hash,
            manifest_hash=manifest_hash,
            failure_count=evidence_bundle.failure_count,
        )
        
        # Update chain link
        self._previous_manifest_hash = manifest_hash
        return manifest

    def _compute_manifest_content(
        self,
        manifest_id: str,
        execution_id: str,
        timestamp: datetime,
        action_hashes: tuple[str, ...],
        artifact_hashes: dict[str, str],
        evidence_bundle_hash: str,
        previous_manifest_hash: Optional[str],
        failure_count: int = 0,
    ) -> str:
        """Compute content string for manifest hash."""
        parts = [
            manifest_id,
            execution_id,
            timestamp.isoformat(),
            ":".join(action_hashes),
            json.dumps(artifact_hashes, sort_keys=True),
            evidence_bundle_hash,
            previous_manifest_hash or "GENESIS",
            str(failure_count),
        ]
        return "|".join(parts)
    
    def compute_artifact_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash for a file."""
        if not file_path.exists():
            raise HashChainVerificationError(f"Artifact file not found: {file_path}")
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    
    def compute_action_hashes(self, actions: list[SafeAction]) -> list[str]:
        """Compute SHA-256 hashes for actions."""
        return [action.compute_hash() for action in actions]
    
    def verify_chain(
        self,
        manifest: ExecutionManifest,
        evidence_bundle: EvidenceBundle,
    ) -> bool:
        """Verify hash chain: manifest → evidence.
        
        Raises:
            HashChainVerificationError: If verification fails (HARD FAIL)
        """
        # Verify evidence bundle hash matches
        if manifest.evidence_bundle_hash != evidence_bundle.bundle_hash:
            raise HashChainVerificationError(
                f"Evidence bundle hash mismatch: "
                f"manifest={manifest.evidence_bundle_hash}, "
                f"bundle={evidence_bundle.bundle_hash} — HARD FAIL"
            )
        
        # Verify artifact hashes
        if evidence_bundle.har_file:
            expected = manifest.artifact_hashes.get("har")
            actual = evidence_bundle.har_file.content_hash
            if expected != actual:
                raise HashChainVerificationError(
                    f"HAR hash mismatch: manifest={expected}, actual={actual} — HARD FAIL"
                )
        
        for i, screenshot in enumerate(evidence_bundle.screenshots):
            key = f"screenshot_{i}"
            expected = manifest.artifact_hashes.get(key)
            actual = screenshot.content_hash
            if expected != actual:
                raise HashChainVerificationError(
                    f"Screenshot {i} hash mismatch: manifest={expected}, actual={actual} — HARD FAIL"
                )
        
        if evidence_bundle.video:
            expected = manifest.artifact_hashes.get("video")
            actual = evidence_bundle.video.content_hash
            if expected != actual:
                raise HashChainVerificationError(
                    f"Video hash mismatch: manifest={expected}, actual={actual} — HARD FAIL"
                )
        
        # Recompute manifest hash and verify
        ts = manifest.timestamp
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        
        recomputed_content = self._compute_manifest_content(
            manifest_id=manifest.manifest_id or "",
            execution_id=manifest.execution_id,
            timestamp=ts,
            action_hashes=manifest.action_hashes,
            artifact_hashes=manifest.artifact_hashes,
            evidence_bundle_hash=manifest.evidence_bundle_hash or "",
            previous_manifest_hash=manifest.previous_manifest_hash,
            failure_count=manifest.failure_count,
        )
        recomputed_hash = hashlib.sha256(recomputed_content.encode()).hexdigest()
        
        if recomputed_hash != manifest.manifest_hash:
            raise HashChainVerificationError(
                f"Manifest hash mismatch: stored={manifest.manifest_hash}, "
                f"recomputed={recomputed_hash} — HARD FAIL"
            )
        
        return True
