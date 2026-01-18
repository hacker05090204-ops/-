# Phase-5 Artifact Scanner Architecture

## Status: FINAL (FROZEN)

**Version**: 1.0.0  
**Date**: 2025-12-30  
**Phase**: 5 - Artifact Scanner

---

## Overview

Phase-5 Artifact Scanner is a READ-ONLY artifact analysis module that consumes Phase-4 execution outputs (HAR files, screenshots, console logs, execution traces, manifests) to extract security-relevant signals. The Scanner does NOT classify vulnerabilities, assign severity, generate proofs, or submit reports — it produces signals and finding candidates for human review only.

**CRITICAL**: This system assists humans. It does not autonomously hunt, judge, or earn.

---

## Phase Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                    FROZEN PHASES (READ-ONLY)                     │
├─────────────────────────────────────────────────────────────────┤
│ Phase-1 (MCP)      │ Truth Engine - Classification, Proofs      │
│ Phase-2 (Cyfer)    │ Exploration Engine                         │
│ Phase-3 (Pipeline) │ Submission Engine                          │
│ Phase-4 (Exec)     │ Execution Layer - Artifact Production      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ READ-ONLY
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE-5 (SCANNER)                             │
├─────────────────────────────────────────────────────────────────┤
│ Input:  Phase-4 artifacts (HAR, screenshots, logs, traces)      │
│ Output: Signals + FindingCandidates (for human review)          │
│ Mode:   READ-ONLY, OFFLINE, NO EXECUTION                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HUMAN REVIEW
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HUMAN REVIEWER                                │
│ - Reviews signals and finding candidates                        │
│ - Decides next steps (escalate to MCP, discard, etc.)          │
│ - Sole authority for severity and classification               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Structure

```
artifact_scanner/
├── __init__.py           # Module exports and non-goals docstring
├── types.py              # Signal, FindingCandidate, ScanResult data models
├── errors.py             # Scanner-specific errors
├── loader.py             # Artifact loading (read-only)
├── analyzers/
│   ├── __init__.py
│   ├── har.py            # HAR file analysis
│   ├── console.py        # Console log analysis
│   └── trace.py          # Execution trace analysis
├── aggregator.py         # Signal aggregation into FindingCandidates
├── scanner.py            # Main Scanner orchestrator
├── ARCHITECTURE.md       # This file
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_types.py
    ├── test_loader.py
    ├── test_har_analyzer.py
    ├── test_console_analyzer.py
    ├── test_trace_analyzer.py
    ├── test_aggregator.py
    ├── test_scanner.py
    └── test_boundaries.py
```

---

## Architectural Constraints

### Code-Enforced Controls

| Control | Enforcement | Location |
|---------|-------------|----------|
| Forbidden fields (severity, classification, confidence) | `__post_init__` validation raises `ValueError` | `types.py` |
| Forbidden methods (classify, assign_severity, etc.) | Methods raise `ArchitecturalViolationError` | `scanner.py` |
| Artifact immutability | SHA-256 hash verification before/after scan | `scanner.py`, `loader.py` |
| Frozen data models | `@dataclass(frozen=True)` | `types.py` |

### Operator Responsibility

| Responsibility | Description |
|----------------|-------------|
| Filesystem permissions | Ensure Scanner has read-only access to artifact directories |
| Human review | All Scanner output requires human review before action |
| Severity assignment | Human reviewer assigns severity, not Scanner |
| Classification | MCP classifies vulnerabilities, not Scanner |

---

## Non-Goals (FORBIDDEN)

The Scanner SHALL NOT:

1. **Classify vulnerabilities** — MCP's responsibility
2. **Assign severity** — Human's responsibility
3. **Compute confidence scores** — MCP's responsibility
4. **Generate proofs** — MCP's responsibility
5. **Submit reports** — Human's responsibility
6. **Trigger executions** — Phase-4's responsibility with human approval
7. **Make network requests** — Offline only
8. **Execute JavaScript** — Read-only analysis
9. **Replay actions** — Read-only analysis
10. **Modify artifacts** — Immutable input
11. **Delete artifacts** — Immutable input
12. **Interact with MCP** — No direct communication
13. **Bypass human review** — All output requires human review

---

## Data Flow

```
Phase-4 Artifacts (READ-ONLY)
         │
         ▼
┌─────────────────┐
│ ArtifactLoader  │──── Hash before scan
│ (read-only)     │
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
┌───────┐ ┌────────┐ ┌──────────┐
│ HAR   │ │Console │ │ Trace    │
│Analyzer│ │Analyzer│ │ Analyzer │
└───┬───┘ └───┬────┘ └────┬─────┘
    │         │           │
    └────┬────┴───────────┘
         │
         ▼
┌─────────────────┐
│SignalAggregator │
│(no classification)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ScanResult    │──── Hash after scan (verify immutability)
│ (for human review)│
└─────────────────┘
         │
         ▼
    HUMAN REVIEWER
```

---

## Signal Types

| Signal Type | Source | Description |
|-------------|--------|-------------|
| `SENSITIVE_DATA` | HAR | API keys, tokens, credentials in responses |
| `HEADER_MISCONFIG` | HAR | Missing CSP, CORS wildcard, unsafe-inline |
| `REFLECTION` | HAR | User input reflected without encoding |
| `PATH_DISCLOSURE` | Console | Sensitive paths in stack traces |
| `DOM_ERROR` | Console | DOM manipulation issues |
| `CSP_VIOLATION` | Console | CSP violation reports |
| `STATE_ANOMALY` | Trace | Unexpected state changes, high failure rate |

---

## Error Handling

### HARD STOP Errors

| Error | Trigger | Action |
|-------|---------|--------|
| `NoArtifactsError` | No artifacts available | Stop scan, return error |
| `ArchitecturalViolationError` | Forbidden action attempted | Stop immediately, log violation |
| `ImmutabilityViolationError` | Artifact modified during scan | Stop immediately, log violation |

### Recoverable Errors

| Error | Trigger | Action |
|-------|---------|--------|
| `ArtifactNotFoundError` | Artifact file missing | Continue with other artifacts |
| `ArtifactParseError` | Artifact parse failure | Continue with other artifacts |

---

## Correctness Properties

| Property | Description | Validation |
|----------|-------------|------------|
| P1: Artifact Immutability | Hash before == hash after | `test_loader.py` |
| P2: No Classification in Signals | severity/classification/confidence = None | `test_types.py` |
| P3: No Classification in FindingCandidates | severity/classification/confidence = None | `test_types.py` |
| P4: Signal Grouping Completeness | All signals for endpoint in same candidate | `test_aggregator.py` |
| P5: Partial Result on Failure | Return results from successful artifacts | `test_scanner.py` |
| P6: Architectural Boundary Enforcement | Forbidden methods raise error | `test_boundaries.py` |
| P7: JSON Serialization Round-Trip | to_json() -> from_json() = equivalent | `test_types.py` |
| P8: Sensitive Data Detection | Patterns detected produce signals | `test_har_analyzer.py` |
| P9: Header Misconfiguration Detection | Missing headers produce signals | `test_har_analyzer.py` |
| P10: Reflection Detection | Reflected input produces signals | `test_har_analyzer.py` |

---

## Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_types.py` | 21 | Data models, forbidden fields, JSON round-trip |
| `test_loader.py` | 26 | Artifact loading, immutability |
| `test_har_analyzer.py` | 24 | HAR signal detection |
| `test_console_analyzer.py` | 18 | Console log signal detection |
| `test_trace_analyzer.py` | 12 | Trace signal detection |
| `test_aggregator.py` | 8 | Signal grouping |
| `test_scanner.py` | 16 | Full scan pipeline |
| `test_boundaries.py` | 13 | Architectural violations |
| **Total** | **138** | All properties validated |

---

## Residual Risk Acceptance

| Risk | Severity | Mitigation | Acceptance |
|------|----------|------------|------------|
| False positive signals | LOW | Human review required | ACCEPTED |
| Missed signals | LOW | Scanner is assistive, not authoritative | ACCEPTED |
| Large artifact processing | LOW | Graceful degradation on failure | ACCEPTED |

---

## Phase-5 Hardening v1 Status

**STATUS**: FINAL, FROZEN

All correctness properties validated. 138 tests passing.

Phase-5 Scanner is ready for production use as a human-assistive tool.

---

*This system assists humans. It does not autonomously hunt, judge, or earn.*
