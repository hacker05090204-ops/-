"""
Phase-28: External Disclosure & Verifiable Presentation Layer

NO AUTHORITY / PRESENTATION ONLY

This module provides presentation and disclosure capabilities for Phase-27 proofs.

CONSTRAINTS:
- Human MUST initiate all actions (human_initiated=True)
- NO execution authority
- NO enforcement authority
- NO automation
- NO scoring or ranking
- NO recommendations
- NO interpretation or analysis
- NO network access
- NO platform detection
- NO auto-sharing
- Static output only (MD, TXT, JSON)
- All outputs include "NOT VERIFIED" and "NO AUTHORITY" disclaimers

ALLOWED ACTIONS:
- Present Phase-27 proofs (human-initiated)
- Package artifacts for human-chosen disclosure (human-initiated)
- Format/label/display evidence (human-initiated)
- Export Phase-27 audit bundles (human-initiated)

FORBIDDEN ACTIONS:
- Verify, certify, or validate anything
- Interpret or analyze proofs
- Score, rank, or prioritize
- Recommend actions
- Auto-share or auto-submit
- Detect platforms or recipients
- Make network requests
- Run background tasks
- Modify Phase-27 or any prior phase

All operations are human-initiated and human-attributed.
"""

from .types import (
    DISCLAIMER,
    NOT_VERIFIED_NOTICE,
    DisclosureContext,
    ProofSelection,
    DisclosurePackage,
    PresentationError,
)

from .renderer import (
    render_proofs,
    render_attestation,
    render_bundle,
)

from .selector import (
    select_proofs,
    list_available_proofs,
)

from .exporter import (
    create_disclosure_package,
    export_to_format,
)


__all__ = [
    # Constants
    "DISCLAIMER",
    "NOT_VERIFIED_NOTICE",
    # Types
    "DisclosureContext",
    "ProofSelection",
    "DisclosurePackage",
    "PresentationError",
    # Renderer
    "render_proofs",
    "render_attestation",
    "render_bundle",
    # Selector
    "select_proofs",
    "list_available_proofs",
    # Exporter
    "create_disclosure_package",
    "export_to_format",
]
