"""
Kali MCP Toolkit - Automated Bug Bounty Hunting MCP Server

This package provides the Python orchestration layer for the Kali MCP Toolkit,
implementing the MCP protocol interface and coordinating security tool execution.
"""

__version__ = "0.1.0"
__author__ = "Kali MCP Team"

from .server import MCPServer
from .orchestrator import HuntOrchestrator
from .rule_engine import RuleEngine
from .scanner import VulnerabilityScanner, VulnerabilityRanker
from .types import (
    Target,
    BugBountyProgram,
    Finding,
    HuntSession,
    HuntPhase,
    Severity,
    FindingClassification,
)

__all__ = [
    "MCPServer",
    "HuntOrchestrator", 
    "RuleEngine",
    "VulnerabilityScanner",
    "VulnerabilityRanker",
    "Target",
    "BugBountyProgram",
    "Finding",
    "HuntSession",
    "HuntPhase",
    "Severity",
    "FindingClassification",
]