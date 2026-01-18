"""
Execution Layer Manifest Store

Persistent storage for execution manifests with hash-chain linking.
Manifests are stored SEPARATELY from ExecutionResult (Design Option B).

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from pathlib import Path
from typing import Optional
import json

from execution_layer.manifest import ExecutionManifest


class ManifestStore:
    """Persistent storage for execution manifests.
    
    Design Option B: Manifests stored separately from ExecutionResult.
    Storage format: JSON files in {storage_dir}/{execution_id}.json
    """
    
    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
    
    async def save(self, manifest: ExecutionManifest) -> Path:
        """Save manifest to JSON file.
        
        Returns:
            Path to saved manifest file.
        """
        manifest_path = self._storage_dir / f"{manifest.execution_id}.json"
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2))
        return manifest_path
    
    async def get(self, execution_id: str) -> Optional[ExecutionManifest]:
        """Retrieve manifest by execution_id.
        
        Returns:
            ExecutionManifest if found, None otherwise.
        """
        manifest_path = self._storage_dir / f"{execution_id}.json"
        if not manifest_path.exists():
            return None
        
        data = json.loads(manifest_path.read_text())
        return self._dict_to_manifest(data)
    
    async def get_chain(
        self, start_id: str, end_id: Optional[str] = None
    ) -> list[ExecutionManifest]:
        """Retrieve manifest chain starting from start_id.
        
        Args:
            start_id: Starting execution_id
            end_id: Optional ending execution_id (inclusive)
        
        Returns:
            List of manifests in chain order (oldest first).
        """
        chain: list[ExecutionManifest] = []
        
        # Get starting manifest
        current = await self.get(start_id)
        if current is None:
            return chain
        
        chain.append(current)
        
        if end_id is None or start_id == end_id:
            return chain
        
        # Walk forward through manifests by timestamp
        all_manifests = await self._get_all_sorted()
        
        # Find start index
        start_idx = -1
        end_idx = -1
        for i, m in enumerate(all_manifests):
            if m.execution_id == start_id:
                start_idx = i
            if m.execution_id == end_id:
                end_idx = i
        
        if start_idx >= 0 and end_idx >= 0 and end_idx > start_idx:
            return all_manifests[start_idx:end_idx + 1]
        
        return chain
    
    async def _get_all_sorted(self) -> list[ExecutionManifest]:
        """Get all manifests sorted by timestamp."""
        manifests: list[ExecutionManifest] = []
        
        for path in self._storage_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                manifest = self._dict_to_manifest(data)
                manifests.append(manifest)
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Sort by timestamp
        manifests.sort(key=lambda m: str(m.timestamp))
        return manifests
    
    def _dict_to_manifest(self, data: dict) -> ExecutionManifest:
        """Convert dictionary to ExecutionManifest."""
        return ExecutionManifest(
            execution_id=data["execution_id"],
            timestamp=data["timestamp"],
            artifact_paths=data.get("artifact_paths", {}),
            manifest_id=data.get("manifest_id"),
            action_hashes=tuple(data.get("action_hashes", [])),
            artifact_hashes=data.get("artifact_hashes", {}),
            evidence_bundle_hash=data.get("evidence_bundle_hash"),
            previous_manifest_hash=data.get("previous_manifest_hash"),
            manifest_hash=data.get("manifest_hash"),
        )
