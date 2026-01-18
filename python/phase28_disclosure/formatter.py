from typing import Any, Dict, List
from .types import DisclosureContext, PresentationPackage

DISCLAIMERS = [
    "NOT VERIFIED BY AI",
    "PROOF OF PROCESS ONLY - NOT A CERTIFICATION OF VULNERABILITY",
    "HUMAN INTERPRETATION REQUIRED"
]

def format_package(bundle: Dict[str, Any], context: DisclosureContext) -> PresentationPackage:
    """
    Format a Phase-27 bundle for a specific context.
    
    PERFORMS NO ANALYSIS.
    Applies templates only.
    """
    
    # 1. Base Content (Verbatim)
    content = f"--- DISCLOSURE PACKAGE: {context.value} ---\n\n"
    
    # 2. Mandatory Disclaimers
    for disclaimer in DISCLAIMERS:
        content += f"!!! {disclaimer} !!!\n"
    content += "\n"
    
    # 3. Proof Data (Read-Only Render)
    content += f"PROOF ID: {bundle.get('id', 'UNKNOWN')}\n"
    content += f"TIMESTAMP: {bundle.get('timestamp', 'UNKNOWN')}\n"
    content += f"HASH: {bundle.get('hash', 'UNKNOWN')}\n"
    content += f"ATTESTATION: {bundle.get('attestation', 'UNKNOWN')}\n"
    
    # 4. Contextual Template (Formatting only)
    if context == DisclosureContext.BUG_BOUNTY:
        content += "\n[SECTION: REPRODUCTION STEPS]\n(See attached Proof Bundle)\n"
    elif context == DisclosureContext.LEGAL_CUSTODY:
        content += "\n[SECTION: CHAIN OF CUSTODY]\n(See attached Hash Chain)\n"
    
    return PresentationPackage(
        proof_id=bundle.get('id', 'UNKNOWN'),
        original_bundle=bundle,
        formatted_content=content,
        context=context,
        disclaimers=DISCLAIMERS,
        metadata={"formatter": "Phase-28v1"}
    )
