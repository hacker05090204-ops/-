"""
PHASE 10 — RISK DESCRIPTORS
2026 RE-IMPLEMENTATION

Risk descriptors WITHOUT SEVERITY SCORING.
NO RANKING. NO AUTOMATED PRIORITIZATION.

Document ID: GOV-PHASE10-2026-REIMPL-CODE
Date: 2026-01-20
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RiskCategory(Enum):
    """Categories of security risks (NOT severity levels)."""
    INFORMATION_DISCLOSURE = "information_disclosure"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INJECTION = "injection"
    CONFIGURATION = "configuration"
    CRYPTOGRAPHIC = "cryptographic"
    OTHER = "other"


@dataclass(frozen=True)
class RiskDescriptor:
    """
    Describes a security risk WITHOUT scoring or severity.
    
    NO SEVERITY. NO SCORING. NO RANKING.
    Risk assessment is a HUMAN responsibility.
    """
    risk_id: str
    category: RiskCategory
    description: str
    affected_component: str
    # NOTE: No severity field. No score field. By design.


def create_risk_descriptor(
    risk_id: str,
    category: RiskCategory,
    description: str,
    affected_component: str
) -> RiskDescriptor:
    """Create a risk descriptor. NO SCORING."""
    if not description or not description.strip():
        raise ValueError("description cannot be empty")
    
    return RiskDescriptor(
        risk_id=risk_id,
        category=category,
        description=description.strip(),
        affected_component=affected_component
    )


def get_risk_category_name(risk: RiskDescriptor) -> str:
    """Get human-readable category name."""
    return risk.category.value.replace("_", " ").title()
