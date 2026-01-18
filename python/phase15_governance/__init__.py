# Phase-15 Governance Enforcement Module
# 
# MANDATORY DECLARATION:
# "Phase-15 may ONLY implement enforcement, validation, logging, and blocking.
# NO authority, verification, learning, autonomy, inference, ranking, scoring,
# or decision-making is permitted."
#
# This module enforces Phase-14 governance constraints.
# It does NOT make decisions, verify findings, or automate actions.

__version__ = "0.1.0"

from phase15_governance.errors import (
    GovernanceError,
    GovernanceBlockedError,
    ValidationError,
    IntegrityError,
    Phase13WriteError,
)

from phase15_governance import audit
from phase15_governance import enforcer
from phase15_governance import validator
from phase15_governance import blocker
from phase15_governance import cve_reference
from phase15_governance import phase13_guard
