"""
Phase-23 Disclaimers: Static disclaimer injection.

Disclaimers are STATIC — defined at build time, NOT generated.
"""


# Static disclaimers by jurisdiction (defined at build time)
_DISCLAIMERS: dict[str, tuple[str, ...]] = {
    "US": (
        "DISCLAIMER: This report is provided for informational purposes only.",
        "This report does not constitute legal advice.",
        "Findings should be verified by qualified security professionals.",
        "The author makes no warranties regarding the accuracy or completeness of this report.",
    ),
    "EU": (
        "DISCLAIMER: This report is provided for informational purposes only.",
        "This report does not constitute legal advice under EU law.",
        "GDPR and other applicable regulations may apply to the handling of this report.",
        "Findings should be verified by qualified security professionals.",
    ),
    "UK": (
        "DISCLAIMER: This report is provided for informational purposes only.",
        "This report does not constitute legal advice under UK law.",
        "Findings should be verified by qualified security professionals.",
        "The author makes no warranties regarding the accuracy or completeness of this report.",
    ),
    "CA": (
        "DISCLAIMER: This report is provided for informational purposes only.",
        "This report does not constitute legal advice under Canadian law.",
        "Findings should be verified by qualified security professionals.",
    ),
    "AU": (
        "DISCLAIMER: This report is provided for informational purposes only.",
        "This report does not constitute legal advice under Australian law.",
        "Findings should be verified by qualified security professionals.",
    ),
    "OTHER": (
        "DISCLAIMER: This report is provided for informational purposes only.",
        "This report does not constitute legal advice.",
        "Consult local legal counsel for jurisdiction-specific requirements.",
        "Findings should be verified by qualified security professionals.",
    ),
}

# Default disclaimers for unknown jurisdictions
_DEFAULT_DISCLAIMERS: tuple[str, ...] = (
    "DISCLAIMER: This report is provided for informational purposes only.",
    "This report does not constitute legal advice.",
    "Findings should be verified by qualified security professionals.",
)


def get_disclaimers(jurisdiction_code: str) -> tuple[str, ...]:
    """
    Get static disclaimers for jurisdiction.
    
    This function:
    - Returns pre-defined disclaimers
    - Does NOT generate disclaimers
    - Does NOT analyze content
    - Does NOT interpret legal requirements
    
    Args:
        jurisdiction_code: Code of jurisdiction.
        
    Returns:
        Tuple of static disclaimer strings.
    """
    return _DISCLAIMERS.get(jurisdiction_code, _DEFAULT_DISCLAIMERS)

