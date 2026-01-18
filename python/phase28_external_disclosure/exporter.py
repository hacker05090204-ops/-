"""
Phase-28 Exporter: Human-Triggered Export

NO AUTHORITY / PRESENTATION ONLY

Creates disclosure packages for human-chosen disclosure.
Does NOT auto-share or auto-submit.
Does NOT make network requests.
Does NOT detect platforms.

All export is human-initiated.
"""

from datetime import datetime, timezone
from typing import Union
import hashlib
import json
import uuid

from .types import (
    DISCLAIMER,
    NOT_VERIFIED_NOTICE,
    DisclosureContext,
    ProofSelection,
    DisclosurePackage,
    PresentationError,
)
from .renderer import render_proofs


def create_disclosure_package(
    context: DisclosureContext,
    selection: ProofSelection,
    *,
    human_initiated: bool,
) -> Union[DisclosurePackage, PresentationError]:
    """
    Create disclosure package for human-chosen disclosure.
    
    NO AUTHORITY / PRESENTATION ONLY
    
    Does NOT auto-share or auto-submit.
    Does NOT make network requests.
    
    Args:
        context: Human-provided disclosure context
        selection: Human-selected proofs
        human_initiated: MUST be True
        
    Returns:
        DisclosurePackage or PresentationError
    """
    if not human_initiated:
        return PresentationError(
            error_type="HUMAN_INITIATION_REQUIRED",
            message="Package creation requires human_initiated=True",
            timestamp=datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        )
    
    # Build rendered content using static template
    rendered_lines = [
        "=" * 80,
        NOT_VERIFIED_NOTICE,
        "=" * 80,
        "",
        "DISCLOSURE PACKAGE",
        "-" * 20,
        "",
        "Context:",
        context.context_text,
        "",
        "Selected Attestations:",
    ]
    
    for att_id in selection.attestation_ids:
        rendered_lines.append(f"  - {att_id}")
    
    if not selection.attestation_ids:
        rendered_lines.append("  (none)")
    
    rendered_lines.extend([
        "",
        "Selected Bundles:",
    ])
    
    for bundle_id in selection.bundle_ids:
        rendered_lines.append(f"  - {bundle_id}")
    
    if not selection.bundle_ids:
        rendered_lines.append("  (none)")
    
    rendered_lines.extend([
        "",
        "=" * 80,
        DISCLAIMER,
        "=" * 80,
    ])
    
    rendered_content = "\n".join(rendered_lines)
    
    # Compute package hash
    package_hash = hashlib.sha256(rendered_content.encode()).hexdigest()
    
    return DisclosurePackage(
        package_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        created_by="HUMAN",
        context=context,
        selection=selection,
        rendered_content=rendered_content,
        package_hash=package_hash,
        human_initiated=True,
        disclaimer=DISCLAIMER,
        not_verified_notice=NOT_VERIFIED_NOTICE,
    )


def export_to_format(
    package: DisclosurePackage,
    format: str,
    *,
    human_initiated: bool,
) -> Union[str, PresentationError]:
    """
    Export package to specified format.
    
    NO AUTHORITY / PRESENTATION ONLY
    
    Supported formats: md, json, txt
    Does NOT auto-share or auto-submit.
    
    Args:
        package: DisclosurePackage to export
        format: Output format (md, json, txt)
        human_initiated: MUST be True
        
    Returns:
        Formatted string or PresentationError
    """
    if not human_initiated:
        return PresentationError(
            error_type="HUMAN_INITIATION_REQUIRED",
            message="Export requires human_initiated=True",
            timestamp=datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        )
    
    if format == "json":
        return json.dumps({
            "disclaimer": package.disclaimer,
            "not_verified_notice": package.not_verified_notice,
            "package_id": package.package_id,
            "created_at": package.created_at,
            "created_by": package.created_by,
            "context_id": package.context.context_id,
            "context_text": package.context.context_text,
            "selection_id": package.selection.selection_id,
            "attestation_ids": list(package.selection.attestation_ids),
            "bundle_ids": list(package.selection.bundle_ids),
            "package_hash": package.package_hash,
            "human_initiated": package.human_initiated,
        }, indent=2)
    
    elif format == "md":
        return f"""# Disclosure Package

{package.not_verified_notice}

## Package Information

- **Package ID**: {package.package_id}
- **Created**: {package.created_at}
- **Created By**: {package.created_by}
- **Package Hash**: {package.package_hash}

## Context

{package.context.context_text}

## Selected Proofs

### Attestations

{chr(10).join(f"- {att_id}" for att_id in package.selection.attestation_ids) or "(none)"}

### Bundles

{chr(10).join(f"- {bundle_id}" for bundle_id in package.selection.bundle_ids) or "(none)"}

---

{package.disclaimer}
"""
    
    else:  # txt or default
        return package.rendered_content
