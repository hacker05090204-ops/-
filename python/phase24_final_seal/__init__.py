"""
Phase-24: Final System Seal & Decommission Mode

This module provides formal system seal and decommission.

CONSTRAINTS:
- Human MUST confirm seal
- Human MUST confirm decommission
- NO auto-seal
- NO auto-decommission
- NO history modification
- NO new actions after seal
- NO prior phase imports (Phase-13 through Phase-23)

All operations are human-initiated and human-attributed.
"""

from .types import (
    SystemSeal,
    DecommissionRecord,
    GovernanceStatus,
)

from .seal import (
    compute_seal_hash,
    create_seal,
)

from .decommission import (
    create_decommission,
)

from .status import (
    get_governance_status,
)


__all__ = [
    # Types
    "SystemSeal",
    "DecommissionRecord",
    "GovernanceStatus",
    # Seal
    "compute_seal_hash",
    "create_seal",
    # Decommission
    "create_decommission",
    # Status
    "get_governance_status",
]

