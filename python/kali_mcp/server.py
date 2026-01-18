"""
MCP Server - Model Context Protocol implementation for bug bounty hunting.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Awaitable
import uuid

from .types import (
    Target,
    BugBountyProgram,
    Finding,
    HuntSession,
    HuntPhase,
    Severity,
    FindingClassification,
)

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[..., Awaitable[Dict[str, Any]]]


@dataclass
class MCPRequest:
    """MCP protocol request."""
    id: str
    method: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResponse:
    """MCP protocol response."""
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        response = {"id": self.id}
        if self.error:
            response["error"] = self.error
        else:
            response["result"] = self.result
        return response


class ToolRegistry:
    """Registry for MCP tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    def __len__(self) -> int:
        return len(self._tools)


class SessionManager:
    """Manages hunting sessions."""

    def __init__(self):
        self._sessions: Dict[str, HuntSession] = {}

    def create_session(
        self,
        target: Optional[Target] = None,
        program: Optional[BugBountyProgram] = None,
    ) -> HuntSession:
        """Create a new hunting session."""
        session = HuntSession(target=target, program=program)
        self._sessions[session.id] = session
        logger.info(f"Created session: {session.id}")
        return session

    def get_session(self, session_id: str) -> Optional[HuntSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[HuntSession]:
        """List all sessions."""
        return list(self._sessions.values())

    def get_active_sessions(self) -> List[HuntSession]:
        """Get all active sessions."""
        return [s for s in self._sessions.values() if s.is_active]

    def close_session(self, session_id: str) -> bool:
        """Close a session."""
        session = self._sessions.get(session_id)
        if session:
            session.complete()
            logger.info(f"Closed session: {session_id}")
            return True
        return False


class ResponseFormatter:
    """Formats responses for MCP protocol."""

    @staticmethod
    def format_finding(finding: Finding) -> Dict[str, Any]:
        """Format a finding for response."""
        return {
            "id": finding.id,
            "invariant_violated": finding.invariant_violated,
            "title": finding.title,
            "description": finding.description,
            "severity": finding.severity.value,
            "confidence": finding.confidence,
            "classification": finding.classification.value,
            "cvss_score": finding.cvss_score,
            "cwe_id": finding.cwe_id,
            "target": finding.target,
            "endpoint": finding.endpoint,
            "is_bug": finding.is_bug(),
            "is_reportable": finding.is_reportable(),
        }

    @staticmethod
    def format_session(session: HuntSession) -> Dict[str, Any]:
        """Format a session for response."""
        return {
            "id": session.id,
            "target": session.target.domain if session.target else None,
            "program": session.program.name if session.program else None,
            "current_phase": session.current_phase.name,
            "finding_count": len(session.findings),
            "bug_count": len(session.get_bugs()),
            "is_active": session.is_active,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }

    @staticmethod
    def format_error(code: int, message: str, data: Optional[Any] = None) -> Dict[str, Any]:
        """Format an error response."""
        error = {"code": code, "message": message}
        if data:
            error["data"] = data
        return error


class MCPServer:
    """
    Model Context Protocol server for bug bounty hunting.
    
    Implements the MCP specification to expose security tools
    and hunting capabilities to AI systems.
    """

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.session_manager = SessionManager()
        self.formatter = ResponseFormatter()
        self._setup_default_tools()

    def _setup_default_tools(self) -> None:
        """Register default security tools."""
        # Session management tools
        self.tool_registry.register(ToolDefinition(
            name="create_session",
            description="Create a new bug bounty hunting session",
            input_schema={
                "type": "object",
                "properties": {
                    "target_domain": {"type": "string", "description": "Target domain to hunt"},
                    "program_name": {"type": "string", "description": "Bug bounty program name"},
                },
                "required": ["target_domain"],
            },
            handler=self._handle_create_session,
        ))

        self.tool_registry.register(ToolDefinition(
            name="list_sessions",
            description="List all hunting sessions",
            input_schema={"type": "object", "properties": {}},
            handler=self._handle_list_sessions,
        ))

        self.tool_registry.register(ToolDefinition(
            name="get_session",
            description="Get details of a specific session",
            input_schema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                },
                "required": ["session_id"],
            },
            handler=self._handle_get_session,
        ))

        # Reconnaissance tools
        self.tool_registry.register(ToolDefinition(
            name="enumerate_subdomains",
            description="Enumerate subdomains for a target domain",
            input_schema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Target domain"},
                    "session_id": {"type": "string", "description": "Session ID"},
                },
                "required": ["domain"],
            },
            handler=self._handle_enumerate_subdomains,
        ))

        self.tool_registry.register(ToolDefinition(
            name="fingerprint_technologies",
            description="Fingerprint technologies used by a target",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "session_id": {"type": "string", "description": "Session ID"},
                },
                "required": ["url"],
            },
            handler=self._handle_fingerprint_technologies,
        ))

        # Scanning tools
        self.tool_registry.register(ToolDefinition(
            name="scan_vulnerabilities",
            description="Scan target for vulnerabilities",
            input_schema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target URL or domain"},
                    "scan_type": {
                        "type": "string",
                        "enum": ["quick", "full", "owasp_top_10"],
                        "description": "Type of scan to perform",
                    },
                    "session_id": {"type": "string", "description": "Session ID"},
                },
                "required": ["target"],
            },
            handler=self._handle_scan_vulnerabilities,
        ))

        # Finding management tools
        self.tool_registry.register(ToolDefinition(
            name="get_findings",
            description="Get findings from a session",
            input_schema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "classification": {
                        "type": "string",
                        "enum": ["bug", "signal", "no_issue", "all"],
                        "description": "Filter by classification",
                    },
                },
                "required": ["session_id"],
            },
            handler=self._handle_get_findings,
        ))

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an MCP request."""
        try:
            if request.method == "tools/list":
                return MCPResponse(
                    id=request.id,
                    result={"tools": self.tool_registry.list_tools()},
                )
            elif request.method == "tools/call":
                tool_name = request.params.get("name")
                arguments = request.params.get("arguments", {})
                
                tool = self.tool_registry.get(tool_name)
                if not tool:
                    return MCPResponse(
                        id=request.id,
                        error=self.formatter.format_error(
                            -32601, f"Tool not found: {tool_name}"
                        ),
                    )
                
                result = await tool.handler(**arguments)
                return MCPResponse(id=request.id, result=result)
            else:
                return MCPResponse(
                    id=request.id,
                    error=self.formatter.format_error(
                        -32601, f"Method not found: {request.method}"
                    ),
                )
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            return MCPResponse(
                id=request.id,
                error=self.formatter.format_error(-32603, str(e)),
            )

    async def handle_tool_call(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle a tool call directly."""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        return await tool.handler(**arguments)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        return self.tool_registry.list_tools()

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific tool."""
        tool = self.tool_registry.get(tool_name)
        if tool:
            return tool.input_schema
        return None

    # Tool handlers
    async def _handle_create_session(
        self,
        target_domain: str,
        program_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle create_session tool call."""
        target = Target(domain=target_domain)
        program = BugBountyProgram(name=program_name or "default", platform="private") if program_name else None
        
        session = self.session_manager.create_session(target=target, program=program)
        return {
            "session_id": session.id,
            "target": target_domain,
            "program": program_name,
            "status": "created",
        }

    async def _handle_list_sessions(self) -> Dict[str, Any]:
        """Handle list_sessions tool call."""
        sessions = self.session_manager.list_sessions()
        return {
            "sessions": [self.formatter.format_session(s) for s in sessions],
            "total": len(sessions),
            "active": len([s for s in sessions if s.is_active]),
        }

    async def _handle_get_session(self, session_id: str) -> Dict[str, Any]:
        """Handle get_session tool call."""
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": f"Session not found: {session_id}"}
        return self.formatter.format_session(session)

    async def _handle_enumerate_subdomains(
        self,
        domain: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle enumerate_subdomains tool call."""
        # This would integrate with actual subdomain enumeration tools
        # For now, return a structured response
        return {
            "domain": domain,
            "subdomains": [],  # Would be populated by actual tool execution
            "sources_used": ["dns", "certificate_transparency", "passive_dns"],
            "status": "pending_implementation",
        }

    async def _handle_fingerprint_technologies(
        self,
        url: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle fingerprint_technologies tool call."""
        return {
            "url": url,
            "technologies": {},  # Would be populated by actual fingerprinting
            "status": "pending_implementation",
        }

    async def _handle_scan_vulnerabilities(
        self,
        target: str,
        scan_type: str = "quick",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle scan_vulnerabilities tool call."""
        return {
            "target": target,
            "scan_type": scan_type,
            "findings": [],  # Would be populated by actual scanning
            "status": "pending_implementation",
        }

    async def _handle_get_findings(
        self,
        session_id: str,
        classification: str = "all",
    ) -> Dict[str, Any]:
        """Handle get_findings tool call."""
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": f"Session not found: {session_id}"}
        
        findings = session.findings
        if classification != "all":
            findings = [
                f for f in findings
                if f.classification.value == classification
            ]
        
        return {
            "session_id": session_id,
            "findings": [self.formatter.format_finding(f) for f in findings],
            "total": len(findings),
        }