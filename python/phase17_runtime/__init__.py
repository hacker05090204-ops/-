"""
Phase-17 Runtime Package

GOVERNANCE CONSTRAINT:
- Runtime + Packaging ONLY
- No intelligence, automation, orchestration, or authority
- No background execution
- No headless mode
- Human-initiated actions only

This package provides:
- Window launcher (visible only)
- Lifecycle management (human-initiated)
- Signal handling (graceful shutdown)
- Audit flushing (crash-safe)
- Environment passthrough (secure)
- Package verification (manifest-based)
"""

from phase17_runtime.errors import (
    RuntimeGovernanceViolation,
    HeadlessModeViolation,
    AutomationViolation,
    BackgroundExecutionViolation,
)
from phase17_runtime.launcher import WindowLauncher
from phase17_runtime.lifecycle import LifecycleManager
from phase17_runtime.signals import SignalHandler
from phase17_runtime.audit_flush import AuditFlusher
from phase17_runtime.env_passthrough import EnvPassthrough
from phase17_runtime.config import RuntimeConfig
from phase17_runtime.packager import Packager
from phase17_runtime.verifier import PackageVerifier

__all__ = [
    "RuntimeGovernanceViolation",
    "HeadlessModeViolation",
    "AutomationViolation",
    "BackgroundExecutionViolation",
    "WindowLauncher",
    "LifecycleManager",
    "SignalHandler",
    "AuditFlusher",
    "EnvPassthrough",
    "RuntimeConfig",
    "Packager",
    "PackageVerifier",
]
