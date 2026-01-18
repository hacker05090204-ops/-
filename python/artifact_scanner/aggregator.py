"""
Phase-5 Signal Aggregator

Aggregates signals into finding candidates.

INVARIANTS:
- No severity assigned
- No classification assigned
- No confidence scoring

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from collections import defaultdict

from artifact_scanner.types import Signal, FindingCandidate


class SignalAggregator:
    """Aggregates signals into finding candidates.
    
    INVARIANTS:
    - No severity assigned
    - No classification assigned
    - No confidence scoring
    """
    
    def aggregate(self, signals: list[Signal]) -> list[FindingCandidate]:
        """Group signals by endpoint into finding candidates.
        
        Args:
            signals: List of signals to aggregate
        
        Returns:
            List of FindingCandidate instances
        """
        # Group signals by endpoint
        grouped = self.group_by_endpoint(signals)
        
        # Create finding candidates for each endpoint
        candidates: list[FindingCandidate] = []
        for endpoint, endpoint_signals in grouped.items():
            if endpoint_signals:
                candidate = FindingCandidate.create(
                    endpoint=endpoint,
                    signals=endpoint_signals,
                )
                candidates.append(candidate)
        
        return candidates
    
    def group_by_endpoint(self, signals: list[Signal]) -> dict[str, list[Signal]]:
        """Group signals by related endpoint.
        
        Args:
            signals: List of signals to group
        
        Returns:
            Dict mapping endpoint to list of signals
        """
        grouped: dict[str, list[Signal]] = defaultdict(list)
        
        for signal in signals:
            # Use endpoint if available, otherwise use "unknown"
            endpoint = signal.endpoint or "unknown"
            grouped[endpoint].append(signal)
        
        return dict(grouped)
