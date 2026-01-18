"""
Phase-21: Patch Covenant & Update Validation

This module provides safe patching WITHOUT reopening governance.

CONSTRAINTS:
- Human confirmation REQUIRED for every patch
- NO auto-application
- NO patch analysis
- NO scoring or ranking
- NO recommendations
- NO prior phase imports (Phase-13 through Phase-20)

All operations are human-initiated and human-attributed.
"""

from .types import (
    PatchRecord,
    PatchBinding,
    SymbolConstraints,
    ValidationResult,
    ApplyResult,
)

from .patch_hash import (
    compute_patch_hash,
    create_binding_hash,
    compute_decision_hash,
)

from .symbol_validator import (
    validate_symbols,
    create_default_constraints,
)

from .confirmation import (
    record_confirmation,
    record_rejection,
)

from .binding import (
    create_patch_binding,
    verify_binding,
)

from .diff_generator import (
    DiffResult,
    generate_diff,
    extract_symbols_from_diff,
)

from .patch_applicator import (
    apply_patch,
)

from .audit_logger import (
    PatchAuditLogger,
)


__all__ = [
    # Types
    "PatchRecord",
    "PatchBinding",
    "SymbolConstraints",
    "ValidationResult",
    "ApplyResult",
    "DiffResult",
    # Hash functions
    "compute_patch_hash",
    "create_binding_hash",
    "compute_decision_hash",
    # Validation
    "validate_symbols",
    "create_default_constraints",
    # Confirmation
    "record_confirmation",
    "record_rejection",
    # Binding
    "create_patch_binding",
    "verify_binding",
    # Diff
    "generate_diff",
    "extract_symbols_from_diff",
    # Application
    "apply_patch",
    # Logging
    "PatchAuditLogger",
]

