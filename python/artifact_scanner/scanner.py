"""
Phase-5 Main Scanner

Main orchestrator for artifact scanning.

INVARIANTS:
- READ-ONLY: No artifacts modified
- OFFLINE: No network requests
- NO EXECUTION: No actions replayed
- NO CLASSIFICATION: Signals only

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from datetime import datetime, timezone
from typing import Optional

from artifact_scanner.loader import ArtifactLoader, HARData, ExecutionTrace
from artifact_scanner.analyzers.har import HARAnalyzer
from artifact_scanner.analyzers.console import ConsoleAnalyzer
from artifact_scanner.analyzers.trace import TraceAnalyzer
from artifact_scanner.aggregator import SignalAggregator
from artifact_scanner.types import Signal, FindingCandidate, ScanResult
from artifact_scanner.errors import (
    ScannerError,
    ArtifactNotFoundError,
    ArtifactParseError,
    NoArtifactsError,
    ArchitecturalViolationError,
    ImmutabilityViolationError,
    is_recoverable,
)


class Scanner:
    """Main scanner orchestrator.
    
    INVARIANTS:
    - READ-ONLY: No artifacts modified
    - OFFLINE: No network requests
    - NO EXECUTION: No actions replayed
    - NO CLASSIFICATION: Signals only
    """
    
    def __init__(self, artifacts_dir: str) -> None:
        """Initialize scanner with artifacts directory.
        
        Args:
            artifacts_dir: Path to artifacts directory
        """
        self._artifacts_dir = artifacts_dir
        self._loader = ArtifactLoader(artifacts_dir)
        self._aggregator = SignalAggregator()
    
    def scan(self, execution_id: str) -> ScanResult:
        """Scan all artifacts for an execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            ScanResult with signals and finding candidates
        
        Raises:
            NoArtifactsError: If no artifacts can be loaded
            ImmutabilityViolationError: If artifacts were modified during scan
        """
        scan_started_at = datetime.now(timezone.utc)
        
        # Load manifest to get artifact paths
        try:
            manifest = self._loader.load_manifest(execution_id)
            artifact_paths = manifest.artifact_paths
        except ArtifactNotFoundError:
            # Try to discover artifacts directly
            try:
                artifact_paths = self._loader.get_artifact_paths(execution_id)
            except ArtifactNotFoundError:
                raise NoArtifactsError(f"No artifacts found for execution: {execution_id}")
        
        if not artifact_paths:
            raise NoArtifactsError(f"No artifacts found for execution: {execution_id}")
        
        # Compute hashes before scan for immutability verification
        hashes_before: dict[str, str] = {}
        for path in artifact_paths:
            try:
                hashes_before[path] = self._loader.compute_file_hash(path)
            except ArtifactNotFoundError:
                pass  # Will be tracked as failed artifact
        
        # Analyze artifacts
        all_signals: list[Signal] = []
        artifacts_scanned: list[str] = []
        artifacts_failed: list[str] = []
        
        for path in artifact_paths:
            try:
                signals = self._analyze_artifact(path)
                all_signals.extend(signals)
                artifacts_scanned.append(path)
            except (ArtifactNotFoundError, ArtifactParseError) as e:
                # Graceful degradation - continue with other artifacts
                artifacts_failed.append(path)
            except ScannerError:
                # Re-raise non-recoverable errors
                raise
        
        # If all artifacts failed, raise NoArtifactsError
        if not artifacts_scanned:
            raise NoArtifactsError(
                f"All artifacts failed to load for execution: {execution_id}"
            )
        
        # Verify immutability
        immutability_verified = self._verify_immutability(
            list(hashes_before.keys()),
            hashes_before,
        )
        
        # Aggregate signals into finding candidates
        finding_candidates = self._aggregator.aggregate(all_signals)
        
        return ScanResult.create(
            execution_id=execution_id,
            signals=all_signals,
            finding_candidates=finding_candidates,
            artifacts_scanned=artifacts_scanned,
            artifacts_failed=artifacts_failed,
            scan_started_at=scan_started_at,
            immutability_verified=immutability_verified,
        )
    
    def _analyze_artifact(self, path: str) -> list[Signal]:
        """Analyze a single artifact.
        
        Args:
            path: Path to artifact
        
        Returns:
            List of signals from artifact
        
        Raises:
            ArtifactNotFoundError: If artifact not found
            ArtifactParseError: If artifact cannot be parsed
        """
        path_lower = path.lower()
        
        if path_lower.endswith(".har"):
            return self._analyze_har(path)
        elif "console" in path_lower and path_lower.endswith(".json"):
            return self._analyze_console(path)
        elif "trace" in path_lower and path_lower.endswith(".json"):
            return self._analyze_trace(path)
        else:
            # Unknown artifact type - skip
            return []
    
    def _analyze_har(self, path: str) -> list[Signal]:
        """Analyze HAR file.
        
        Args:
            path: Path to HAR file
        
        Returns:
            List of signals
        """
        har_data = self._loader.load_har(path)
        analyzer = HARAnalyzer(path)
        return analyzer.analyze(har_data)
    
    def _analyze_console(self, path: str) -> list[Signal]:
        """Analyze console log.
        
        Args:
            path: Path to console log
        
        Returns:
            List of signals
        """
        logs = self._loader.load_console_logs(path)
        analyzer = ConsoleAnalyzer(path)
        return analyzer.analyze(logs)
    
    def _analyze_trace(self, path: str) -> list[Signal]:
        """Analyze execution trace.
        
        Args:
            path: Path to trace file
        
        Returns:
            List of signals
        """
        trace = self._loader.load_execution_trace(path)
        analyzer = TraceAnalyzer(path)
        return analyzer.analyze(trace)
    
    def _verify_immutability(
        self,
        paths: list[str],
        hashes_before: dict[str, str],
    ) -> bool:
        """Verify no artifacts were modified during scan.
        
        Args:
            paths: List of artifact paths
            hashes_before: Dict of path -> hash before scan
        
        Returns:
            True if all artifacts unchanged
        
        Raises:
            ImmutabilityViolationError: If any artifact was modified
        """
        for path in paths:
            if path not in hashes_before:
                continue
            
            try:
                hash_after = self._loader.compute_file_hash(path)
                if hash_after != hashes_before[path]:
                    raise ImmutabilityViolationError(
                        f"Artifact was modified during scan: {path}"
                    )
            except ArtifactNotFoundError:
                # File was deleted - this is a violation
                raise ImmutabilityViolationError(
                    f"Artifact was deleted during scan: {path}"
                )
        
        return True
    
    # =========================================================================
    # FORBIDDEN METHODS - Raise ArchitecturalViolationError
    # =========================================================================
    
    def classify_vulnerability(self, *args, **kwargs) -> None:
        """FORBIDDEN: Classification is MCP's responsibility."""
        raise ArchitecturalViolationError(
            "Scanner cannot classify vulnerabilities - this is MCP's responsibility"
        )
    
    def assign_severity(self, *args, **kwargs) -> None:
        """FORBIDDEN: Severity assignment is human's responsibility."""
        raise ArchitecturalViolationError(
            "Scanner cannot assign severity - this is human's responsibility"
        )
    
    def compute_confidence(self, *args, **kwargs) -> None:
        """FORBIDDEN: Confidence scoring is MCP's responsibility."""
        raise ArchitecturalViolationError(
            "Scanner cannot compute confidence - this is MCP's responsibility"
        )
    
    def submit_report(self, *args, **kwargs) -> None:
        """FORBIDDEN: Report submission is human's responsibility."""
        raise ArchitecturalViolationError(
            "Scanner cannot submit reports - this is human's responsibility"
        )
    
    def trigger_execution(self, *args, **kwargs) -> None:
        """FORBIDDEN: Execution triggering is Phase-4's responsibility."""
        raise ArchitecturalViolationError(
            "Scanner cannot trigger executions - this is Phase-4's responsibility"
        )
    
    def generate_proof(self, *args, **kwargs) -> None:
        """FORBIDDEN: Proof generation is MCP's responsibility."""
        raise ArchitecturalViolationError(
            "Scanner cannot generate proofs - this is MCP's responsibility"
        )
