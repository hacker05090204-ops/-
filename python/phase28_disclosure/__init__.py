"""
Phase-28: External Disclosure & Verifiable Presentation Layer

GOVERNANCE:
- PRESENTATION ONLY
- NO INTERPRETATION
- NO VERIFICATION
- NO AUTOMATION
"""
__version__ = "1.0.0"

from .types import DisclosureContext, PresentationPackage
from .formatter import format_package
from .exporter import export_package

__all__ = [
    "DisclosureContext",
    "PresentationPackage",
    "format_package",
    "export_package"
]
