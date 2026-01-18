"""
Test Minimal Hardening Features

Tests for:
1. Per-action delay in BrowserEngine
2. Keep last N executions retention
3. Execution manifest creation

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

import pytest
import tempfile
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone

from execution_layer.browser import BrowserConfig
from execution_layer.retention import EvidenceRetentionPolicy, EvidenceRetentionManager
from execution_layer.manifest import ManifestGenerator, ExecutionManifest


class TestPerActionDelay:
    """Test configurable per-action delay in BrowserConfig."""
    
    def test_default_delay_is_2_seconds(self):
        """Default per_action_delay_seconds should be 2.0."""
        config = BrowserConfig()
        assert config.per_action_delay_seconds == 2.0
    
    def test_custom_delay_accepted(self):
        """Custom delay values should be accepted."""
        config = BrowserConfig(per_action_delay_seconds=1.5)
        assert config.per_action_delay_seconds == 1.5
    
    def test_zero_delay_allowed(self):
        """Zero delay should be allowed (for testing)."""
        config = BrowserConfig(per_action_delay_seconds=0.0)
        assert config.per_action_delay_seconds == 0.0
    
    def test_negative_delay_rejected(self):
        """Negative delay should raise ValueError."""
        with pytest.raises(ValueError, match="per_action_delay_seconds must be >= 0"):
            BrowserConfig(per_action_delay_seconds=-1.0)


class TestKeepLastNRetention:
    """Test keep last N executions retention policy."""
    
    def test_keep_last_n_prunes_old_executions(self):
        """prune_keep_last_n should keep only N newest executions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy()
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            # Create 5 executions with different timestamps
            for i in range(5):
                exec_dir = Path(tmpdir) / f"exec-{i}"
                exec_dir.mkdir()
                artifact = exec_dir / "artifact.txt"
                artifact.write_text(f"content-{i}")
                # Touch with different times
                time.sleep(0.1)
            
            # Keep last 2
            result = manager.prune_keep_last_n(n=2)
            
            assert result.executions_pruned == 3
            # Verify only 2 remain
            remaining = list(Path(tmpdir).iterdir())
            assert len(remaining) == 2
    
    def test_keep_last_n_with_n_equals_1(self):
        """prune_keep_last_n with n=1 should keep only newest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy()
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            # Create 3 executions
            for i in range(3):
                exec_dir = Path(tmpdir) / f"exec-{i}"
                exec_dir.mkdir()
                (exec_dir / "file.txt").write_text(f"data-{i}")
                time.sleep(0.1)
            
            result = manager.prune_keep_last_n(n=1)
            
            assert result.executions_pruned == 2
            remaining = list(Path(tmpdir).iterdir())
            assert len(remaining) == 1
    
    def test_keep_last_n_invalid_n_raises(self):
        """prune_keep_last_n with n < 1 should raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = EvidenceRetentionPolicy()
            manager = EvidenceRetentionManager(policy, artifacts_dir=tmpdir)
            
            from execution_layer.errors import DiskRetentionError
            with pytest.raises(DiskRetentionError, match="n must be >= 1"):
                manager.prune_keep_last_n(n=0)


class TestExecutionManifest:
    """Test execution_manifest.json creation."""
    
    def test_create_manifest_with_execution_id(self):
        """Manifest should contain execution_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ManifestGenerator(artifacts_dir=tmpdir)
            manifest = generator.create_manifest("exec-123")
            
            assert manifest.execution_id == "exec-123"
    
    def test_create_manifest_has_timestamp(self):
        """Manifest should contain ISO timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ManifestGenerator(artifacts_dir=tmpdir)
            manifest = generator.create_manifest("exec-456")
            
            # Should be valid ISO format
            parsed = datetime.fromisoformat(manifest.timestamp.replace("Z", "+00:00"))
            assert parsed is not None
    
    def test_manifest_discovers_artifact_paths(self):
        """Manifest should auto-discover artifact paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create execution with artifacts
            exec_dir = Path(tmpdir) / "exec-789"
            exec_dir.mkdir()
            (exec_dir / "screenshot.png").write_bytes(b"png-data")
            (exec_dir / "har").mkdir()
            (exec_dir / "har" / "capture.har").write_text("{}")
            
            generator = ManifestGenerator(artifacts_dir=tmpdir)
            manifest = generator.create_manifest("exec-789")
            
            assert len(manifest.artifact_paths) == 2
            assert "exec-789/screenshot.png" in manifest.artifact_paths
            assert "exec-789/har/capture.har" in manifest.artifact_paths
    
    def test_save_and_load_manifest(self):
        """Manifest should save to and load from JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ManifestGenerator(artifacts_dir=tmpdir)
            
            # Create and save
            manifest = generator.create_manifest(
                "exec-abc",
                artifact_paths=["exec-abc/file1.txt", "exec-abc/file2.png"]
            )
            path = generator.save_manifest(manifest)
            
            # Verify file exists
            assert path.exists()
            assert path.name == "execution_manifest.json"
            
            # Load and verify
            loaded = generator.load_manifest("exec-abc")
            assert loaded is not None
            assert loaded.execution_id == "exec-abc"
            assert loaded.artifact_paths == ["exec-abc/file1.txt", "exec-abc/file2.png"]
    
    def test_manifest_json_structure(self):
        """Manifest JSON should have correct structure (NO hash chaining)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ManifestGenerator(artifacts_dir=tmpdir)
            
            manifest = generator.create_manifest(
                "exec-xyz",
                artifact_paths=["exec-xyz/data.json"]
            )
            path = generator.save_manifest(manifest)
            
            # Read raw JSON
            with open(path) as f:
                data = json.load(f)
            
            # Verify structure
            assert "execution_id" in data
            assert "timestamp" in data
            assert "artifact_paths" in data
            # NO hash chaining fields
            assert "hash" not in data
            assert "previous_hash" not in data
            assert "chain" not in data
