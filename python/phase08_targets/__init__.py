"""PHASE 08 — TARGET METADATA MODEL PACKAGE"""
from phase08_targets.targets import (
    TargetType, TargetStatus, TargetMetadata,
    create_target, is_valid_target,
)
__all__ = ["TargetType", "TargetStatus", "TargetMetadata", "create_target", "is_valid_target"]
