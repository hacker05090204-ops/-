"""
Execution Layer Evidence Retention Policy

Manages disk space and artifact retention for evidence files.
MANDATORY: Prevents disk exhaustion and enforces retention limits.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import os
import shutil

from execution_layer.errors import DiskRetentionError


@dataclass
class EvidenceRetentionPolicy:
    """Configuration for evidence retention and disk safety.
    
    MANDATORY: Enforces disk limits to prevent exhaustion.
    
    Attributes:
        max_total_disk_mb: Maximum total disk usage in MB (default: 5000 = 5GB)
        max_artifacts_per_execution: Maximum artifacts per execution (default: 100)
        ttl_days: Time-to-live for artifacts in days (default: 30)
        warning_threshold_percent: Warn when disk usage exceeds this % (default: 80)
        critical_threshold_percent: HARD FAIL when disk usage exceeds this % (default: 95)
    """
    max_total_disk_mb: int = 5000  # 5GB default
    max_artifacts_per_execution: int = 100
    ttl_days: int = 30
    warning_threshold_percent: int = 80
    critical_threshold_percent: int = 95
    
    def __post_init__(self) -> None:
        if self.max_total_disk_mb < 100:
            raise DiskRetentionError(
                f"max_total_disk_mb must be >= 100, got {self.max_total_disk_mb}"
            )
        if self.max_artifacts_per_execution < 1:
            raise DiskRetentionError(
                f"max_artifacts_per_execution must be >= 1, got {self.max_artifacts_per_execution}"
            )
        if self.ttl_days < 1:
            raise DiskRetentionError(
                f"ttl_days must be >= 1, got {self.ttl_days}"
            )
        if self.warning_threshold_percent < 50 or self.warning_threshold_percent > 100:
            raise DiskRetentionError(
                f"warning_threshold_percent must be 50-100, got {self.warning_threshold_percent}"
            )
        if self.critical_threshold_percent < self.warning_threshold_percent:
            raise DiskRetentionError(
                f"critical_threshold_percent must be >= warning_threshold_percent"
            )


@dataclass
class RetentionStats:
    """Statistics about current retention state."""
    total_size_mb: float
    artifact_count: int
    execution_count: int
    oldest_artifact_age_days: Optional[float]
    usage_percent: float
    is_warning: bool
    is_critical: bool


@dataclass
class PruneResult:
    """Result of a prune operation."""
    executions_pruned: int
    artifacts_pruned: int
    bytes_freed: int
    reason: str
    pruned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceRetentionManager:
    """Manages evidence retention and disk safety.
    
    MANDATORY: All evidence storage MUST pass through retention checks.
    - Enforces max_total_disk_mb limit
    - Enforces max_artifacts_per_execution limit
    - Auto-prunes expired artifacts (ttl_days)
    - HARD FAIL if disk exceeds critical threshold
    - Records all pruning in audit log
    """
    
    def __init__(
        self,
        policy: EvidenceRetentionPolicy,
        artifacts_dir: str = "artifacts",
    ) -> None:
        if policy is None:
            raise DiskRetentionError("EvidenceRetentionPolicy is REQUIRED — HARD FAIL")
        self._policy = policy
        self._artifacts_path = Path(artifacts_dir)
        self._prune_log: list[PruneResult] = []
        
        # Ensure artifacts directory exists
        self._artifacts_path.mkdir(parents=True, exist_ok=True)
    
    def get_stats(self) -> RetentionStats:
        """Get current retention statistics."""
        total_size = 0
        artifact_count = 0
        execution_count = 0
        oldest_mtime: Optional[float] = None
        
        if self._artifacts_path.exists():
            for execution_dir in self._artifacts_path.iterdir():
                if execution_dir.is_dir():
                    execution_count += 1
                    for artifact_file in execution_dir.rglob("*"):
                        if artifact_file.is_file():
                            artifact_count += 1
                            total_size += artifact_file.stat().st_size
                            mtime = artifact_file.stat().st_mtime
                            if oldest_mtime is None or mtime < oldest_mtime:
                                oldest_mtime = mtime
        
        total_size_mb = total_size / (1024 * 1024)
        usage_percent = (total_size_mb / self._policy.max_total_disk_mb) * 100
        
        oldest_age_days: Optional[float] = None
        if oldest_mtime is not None:
            oldest_age_days = (datetime.now().timestamp() - oldest_mtime) / (24 * 3600)
        
        return RetentionStats(
            total_size_mb=total_size_mb,
            artifact_count=artifact_count,
            execution_count=execution_count,
            oldest_artifact_age_days=oldest_age_days,
            usage_percent=usage_percent,
            is_warning=usage_percent >= self._policy.warning_threshold_percent,
            is_critical=usage_percent >= self._policy.critical_threshold_percent,
        )
    
    def check_can_store(self, estimated_size_bytes: int = 0) -> bool:
        """Check if storage is allowed.
        
        Raises:
            DiskRetentionError: If disk is at critical threshold (HARD FAIL)
        """
        stats = self.get_stats()
        
        if stats.is_critical:
            raise DiskRetentionError(
                f"Disk usage at critical threshold: {stats.usage_percent:.1f}% "
                f"({stats.total_size_mb:.1f}MB / {self._policy.max_total_disk_mb}MB) — HARD FAIL"
            )
        
        # Check if adding estimated size would exceed limit
        estimated_mb = estimated_size_bytes / (1024 * 1024)
        projected_mb = stats.total_size_mb + estimated_mb
        projected_percent = (projected_mb / self._policy.max_total_disk_mb) * 100
        
        if projected_percent >= self._policy.critical_threshold_percent:
            raise DiskRetentionError(
                f"Adding {estimated_mb:.1f}MB would exceed critical threshold: "
                f"{projected_percent:.1f}% — HARD FAIL"
            )
        
        return True
    
    def check_artifact_count(self, execution_id: str) -> bool:
        """Check if execution has room for more artifacts.
        
        Raises:
            DiskRetentionError: If max_artifacts_per_execution exceeded (HARD FAIL)
        """
        execution_dir = self._artifacts_path / execution_id
        if not execution_dir.exists():
            return True
        
        artifact_count = sum(1 for _ in execution_dir.rglob("*") if _.is_file())
        
        if artifact_count >= self._policy.max_artifacts_per_execution:
            raise DiskRetentionError(
                f"Execution '{execution_id}' has {artifact_count} artifacts, "
                f"max is {self._policy.max_artifacts_per_execution} — HARD FAIL"
            )
        
        return True
    
    def prune_expired(self) -> PruneResult:
        """Prune artifacts older than ttl_days.
        
        Returns:
            PruneResult with details of what was pruned
        """
        cutoff = datetime.now().timestamp() - (self._policy.ttl_days * 24 * 3600)
        executions_pruned = 0
        artifacts_pruned = 0
        bytes_freed = 0
        
        if self._artifacts_path.exists():
            for execution_dir in list(self._artifacts_path.iterdir()):
                if not execution_dir.is_dir():
                    continue
                
                # Check if all artifacts in execution are expired
                all_expired = True
                execution_bytes = 0
                execution_artifacts = 0
                
                for artifact_file in execution_dir.rglob("*"):
                    if artifact_file.is_file():
                        execution_artifacts += 1
                        execution_bytes += artifact_file.stat().st_size
                        if artifact_file.stat().st_mtime > cutoff:
                            all_expired = False
                
                # Only prune if all artifacts are expired
                if all_expired and execution_artifacts > 0:
                    shutil.rmtree(execution_dir)
                    executions_pruned += 1
                    artifacts_pruned += execution_artifacts
                    bytes_freed += execution_bytes
        
        result = PruneResult(
            executions_pruned=executions_pruned,
            artifacts_pruned=artifacts_pruned,
            bytes_freed=bytes_freed,
            reason=f"TTL expired (>{self._policy.ttl_days} days)",
        )
        self._prune_log.append(result)
        return result
    
    def prune_to_threshold(self, target_percent: float = 70.0) -> PruneResult:
        """Prune oldest executions until disk usage is below target.
        
        Args:
            target_percent: Target disk usage percentage (default: 70%)
        
        Returns:
            PruneResult with details of what was pruned
        """
        stats = self.get_stats()
        if stats.usage_percent <= target_percent:
            return PruneResult(
                executions_pruned=0,
                artifacts_pruned=0,
                bytes_freed=0,
                reason="Already below target threshold",
            )
        
        # Get executions sorted by oldest first
        executions: list[tuple[Path, float, int]] = []
        if self._artifacts_path.exists():
            for execution_dir in self._artifacts_path.iterdir():
                if not execution_dir.is_dir():
                    continue
                oldest_mtime = float('inf')
                total_size = 0
                for artifact_file in execution_dir.rglob("*"):
                    if artifact_file.is_file():
                        mtime = artifact_file.stat().st_mtime
                        if mtime < oldest_mtime:
                            oldest_mtime = mtime
                        total_size += artifact_file.stat().st_size
                if oldest_mtime != float('inf'):
                    executions.append((execution_dir, oldest_mtime, total_size))
        
        # Sort by oldest first
        executions.sort(key=lambda x: x[1])
        
        executions_pruned = 0
        artifacts_pruned = 0
        bytes_freed = 0
        current_size_mb = stats.total_size_mb
        target_size_mb = (target_percent / 100) * self._policy.max_total_disk_mb
        
        for execution_dir, _, size in executions:
            if current_size_mb <= target_size_mb:
                break
            
            artifact_count = sum(1 for _ in execution_dir.rglob("*") if _.is_file())
            shutil.rmtree(execution_dir)
            
            executions_pruned += 1
            artifacts_pruned += artifact_count
            bytes_freed += size
            current_size_mb -= size / (1024 * 1024)
        
        result = PruneResult(
            executions_pruned=executions_pruned,
            artifacts_pruned=artifacts_pruned,
            bytes_freed=bytes_freed,
            reason=f"Pruned to {target_percent}% threshold",
        )
        self._prune_log.append(result)
        return result
    
    def auto_prune(self) -> Optional[PruneResult]:
        """Automatically prune if needed.
        
        Called before each execution to ensure disk safety.
        
        Returns:
            PruneResult if pruning occurred, None otherwise
        """
        stats = self.get_stats()
        
        # First, always prune expired artifacts
        expired_result = self.prune_expired()
        
        # If still at warning threshold, prune to 70%
        stats = self.get_stats()
        if stats.is_warning:
            threshold_result = self.prune_to_threshold(70.0)
            # Combine results
            return PruneResult(
                executions_pruned=expired_result.executions_pruned + threshold_result.executions_pruned,
                artifacts_pruned=expired_result.artifacts_pruned + threshold_result.artifacts_pruned,
                bytes_freed=expired_result.bytes_freed + threshold_result.bytes_freed,
                reason="Auto-prune: expired + threshold",
            )
        
        if expired_result.executions_pruned > 0:
            return expired_result
        
        return None
    
    def get_prune_log(self) -> list[PruneResult]:
        """Get all prune operations for audit."""
        return list(self._prune_log)
    
    def get_execution_size(self, execution_id: str) -> int:
        """Get total size of an execution's artifacts in bytes."""
        execution_dir = self._artifacts_path / execution_id
        if not execution_dir.exists():
            return 0
        return sum(f.stat().st_size for f in execution_dir.rglob("*") if f.is_file())
    
    def prune_keep_last_n(self, n: int = 10) -> PruneResult:
        """Keep only the last N executions, prune the rest.
        
        Args:
            n: Number of executions to keep (default: 10)
        
        Returns:
            PruneResult with details of what was pruned
        """
        if n < 1:
            raise DiskRetentionError(f"n must be >= 1, got {n}")
        
        # Get executions sorted by newest first (by modification time)
        executions: list[tuple[Path, float, int]] = []
        if self._artifacts_path.exists():
            for execution_dir in self._artifacts_path.iterdir():
                if not execution_dir.is_dir():
                    continue
                newest_mtime = 0.0
                total_size = 0
                for artifact_file in execution_dir.rglob("*"):
                    if artifact_file.is_file():
                        mtime = artifact_file.stat().st_mtime
                        if mtime > newest_mtime:
                            newest_mtime = mtime
                        total_size += artifact_file.stat().st_size
                if newest_mtime > 0:
                    executions.append((execution_dir, newest_mtime, total_size))
        
        # Sort by newest first
        executions.sort(key=lambda x: x[1], reverse=True)
        
        # Keep first N, prune the rest
        to_prune = executions[n:]
        
        executions_pruned = 0
        artifacts_pruned = 0
        bytes_freed = 0
        
        for execution_dir, _, size in to_prune:
            artifact_count = sum(1 for _ in execution_dir.rglob("*") if _.is_file())
            shutil.rmtree(execution_dir)
            
            executions_pruned += 1
            artifacts_pruned += artifact_count
            bytes_freed += size
        
        result = PruneResult(
            executions_pruned=executions_pruned,
            artifacts_pruned=artifacts_pruned,
            bytes_freed=bytes_freed,
            reason=f"Keep last {n} executions",
        )
        self._prune_log.append(result)
        return result
