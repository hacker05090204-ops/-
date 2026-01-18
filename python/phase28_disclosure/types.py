from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional

class DisclosureContext(Enum):
    BUG_BOUNTY = "BUG_BOUNTY"
    LEGAL_CUSTODY = "LEGAL_CUSTODY"
    INTERNAL_AUDIT = "INTERNAL_AUDIT"
    PUBLIC_DISCLOSURE = "PUBLIC_DISCLOSURE"

@dataclass
class PresentationPackage:
    """
    A read-only container for Phase-27 proofs, formatted for disclosure.
    """
    proof_id: str
    original_bundle: Dict[str, Any] # The immutable source
    formatted_content: str
    context: DisclosureContext
    disclaimers: list[str]
    metadata: Dict[str, Any]
