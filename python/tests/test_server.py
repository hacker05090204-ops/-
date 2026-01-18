"""
Property-based tests for MCP server implementation.

**Task 5: Implement MCP protocol layer and session management**
**Property Tests: 5.1**

Requirements validated:
- MCP Protocol Compliance
- Session Management
- Tool Registration
- Response Formatting
"""

import pytest
from hypothesis import given, strategies as st, settings
import asyncio
from datetime import datetime
import uuid

from kali_mcp.server import (
    MCPServer,
    MCPRequest,
    MCPResponse,
    ToolRegistry,
    SessionManager,
    ResponseFormatter,
    ToolDefinition,
)
from kali_mcp.types import (
    Target,
    BugBountyProgram,
    Finding,
    HuntSession,
    HuntPhase,
    Severity,
    FindingClassification,
    Evidence,
)


# ============================================================================
# Test Helpers
# ============================================================================

def create_test_finding(
    severity: Severity = Severity.HIGH,
    classification: FindingClassification = FindingClassification.BUG,
    confidence: float = 0.95,
) -> Finding:
    """Create a test finding."""
    return Finding(
        id=str(uuid.uuid4()),
        invariant_violated="AUTH_001",
        title="Test Vulnerability",
        description="A test vulnerability for testing",
        severity=severity,
        confidence=confidence,
        classification=classification,
        target="example.com",
        endpoint="/api/test",
    )


def create_test_session() -> HuntSession:
    """Create a test session."""
    return HuntSession(
        target=Target(domain="example.com"),
        program=BugBountyProgram(name="Test Program", platform="private"),
    )


# ============================================================================
# Property Test 5.1: MCP Protocol Compliance
# **Validates: Requirements 1.4, 2.5**
# ============================================================================

class TestMCPProtocolCompliance:
    """Tests for MCP protocol compliance."""

    def test_server_initialization(self):
        """Server initializes with default tools."""
        server = MCPServer()
        
        assert server.tool_registry is not None
        assert len(server.tool_registry) > 0
        assert server.session_manager is not None

    def test_tool_list_returns_all_tools(self):
        """tools/list returns all registered tools."""
        server = MCPServer()
        tools = server.list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    @pytest.mark.asyncio
    async def test_tools_list_request(self):
        """Handle tools/list MCP request."""
        server = MCPServer()
        
        request = MCPRequest(
            id="test-1",
            method="tools/list",
            params={},
        )
        
        response = await server.handle_request(request)
        
        assert response.id == "test-1"
        assert response.error is None
        assert response.result is not None
        assert "tools" in response.result

    @pytest.mark.asyncio
    async def test_tools_call_request(self):
        """Handle tools/call MCP request."""
        server = MCPServer()
        
        request = MCPRequest(
            id="test-2",
            method="tools/call",
            params={
                "name": "create_session",
                "arguments": {"target_domain": "example.com"},
            },
        )
        
        response = await server.handle_request(request)
        
        assert response.id == "test-2"
        assert response.error is None
        assert response.result is not None
        assert "session_id" in response.result

    @pytest.mark.asyncio
    async def test_unknown_method_returns_error(self):
        """Unknown method returns error response."""
        server = MCPServer()
        
        request = MCPRequest(
            id="test-3",
            method="unknown/method",
            params={},
        )
        
        response = await server.handle_request(request)
        
        assert response.id == "test-3"
        assert response.error is not None
        assert response.error["code"] == -32601

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        """Unknown tool returns error response."""
        server = MCPServer()
        
        request = MCPRequest(
            id="test-4",
            method="tools/call",
            params={
                "name": "nonexistent_tool",
                "arguments": {},
            },
        )
        
        response = await server.handle_request(request)
        
        assert response.id == "test-4"
        assert response.error is not None
        assert "not found" in response.error["message"].lower()

    def test_response_to_dict(self):
        """MCPResponse converts to dict correctly."""
        response = MCPResponse(
            id="test-5",
            result={"data": "test"},
        )
        
        d = response.to_dict()
        
        assert d["id"] == "test-5"
        assert d["result"] == {"data": "test"}
        assert "error" not in d or d.get("error") is None

    def test_error_response_to_dict(self):
        """Error MCPResponse converts to dict correctly."""
        response = MCPResponse(
            id="test-6",
            error={"code": -32600, "message": "Invalid request"},
        )
        
        d = response.to_dict()
        
        assert d["id"] == "test-6"
        assert d["error"]["code"] == -32600


class TestToolRegistry:
    """Tests for tool registry."""

    def test_register_tool(self):
        """Tool registration works correctly."""
        registry = ToolRegistry()
        
        async def handler(**kwargs):
            return {"result": "ok"}
        
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
            handler=handler,
        )
        
        registry.register(tool)
        
        assert registry.get("test_tool") is not None
        assert len(registry) == 1

    def test_get_nonexistent_tool(self):
        """Getting nonexistent tool returns None."""
        registry = ToolRegistry()
        
        assert registry.get("nonexistent") is None

    def test_list_tools(self):
        """List tools returns correct format."""
        registry = ToolRegistry()
        
        async def handler(**kwargs):
            return {}
        
        registry.register(ToolDefinition(
            name="tool1",
            description="Tool 1",
            input_schema={"type": "object"},
            handler=handler,
        ))
        registry.register(ToolDefinition(
            name="tool2",
            description="Tool 2",
            input_schema={"type": "object"},
            handler=handler,
        ))
        
        tools = registry.list_tools()
        
        assert len(tools) == 2
        assert all("name" in t for t in tools)
        assert all("description" in t for t in tools)
        assert all("inputSchema" in t for t in tools)

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=20)
    def test_tool_names_are_preserved(self, name: str):
        """Tool names are preserved exactly."""
        registry = ToolRegistry()
        
        async def handler(**kwargs):
            return {}
        
        # Skip invalid names
        if not name.strip() or '\x00' in name:
            return
        
        tool = ToolDefinition(
            name=name,
            description="Test",
            input_schema={},
            handler=handler,
        )
        
        registry.register(tool)
        retrieved = registry.get(name)
        
        assert retrieved is not None
        assert retrieved.name == name


class TestSessionManager:
    """Tests for session manager."""

    def test_create_session(self):
        """Session creation works correctly."""
        manager = SessionManager()
        
        target = Target(domain="example.com")
        session = manager.create_session(target=target)
        
        assert session.id is not None
        assert session.target == target
        assert session.is_active

    def test_get_session(self):
        """Session retrieval works correctly."""
        manager = SessionManager()
        
        session = manager.create_session()
        retrieved = manager.get_session(session.id)
        
        assert retrieved is not None
        assert retrieved.id == session.id

    def test_get_nonexistent_session(self):
        """Getting nonexistent session returns None."""
        manager = SessionManager()
        
        assert manager.get_session("nonexistent") is None

    def test_list_sessions(self):
        """List sessions returns all sessions."""
        manager = SessionManager()
        
        for _ in range(5):
            manager.create_session()
        
        sessions = manager.list_sessions()
        
        assert len(sessions) == 5

    def test_get_active_sessions(self):
        """Get active sessions filters correctly."""
        manager = SessionManager()
        
        for _ in range(3):
            manager.create_session()
        
        # Close one session
        sessions = manager.list_sessions()
        manager.close_session(sessions[0].id)
        
        active = manager.get_active_sessions()
        
        assert len(active) == 2

    def test_close_session(self):
        """Session closing works correctly."""
        manager = SessionManager()
        
        session = manager.create_session()
        assert session.is_active
        
        result = manager.close_session(session.id)
        
        assert result is True
        assert not session.is_active
        assert session.completed_at is not None

    def test_close_nonexistent_session(self):
        """Closing nonexistent session returns False."""
        manager = SessionManager()
        
        result = manager.close_session("nonexistent")
        
        assert result is False

    @given(st.integers(min_value=1, max_value=20))
    @settings(max_examples=10)
    def test_session_count_matches_created(self, count: int):
        """Session count matches number created."""
        manager = SessionManager()
        
        for _ in range(count):
            manager.create_session()
        
        assert len(manager.list_sessions()) == count


class TestResponseFormatter:
    """Tests for response formatter."""

    def test_format_finding(self):
        """Finding formatting works correctly."""
        finding = create_test_finding()
        
        formatted = ResponseFormatter.format_finding(finding)
        
        assert formatted["id"] == finding.id
        assert formatted["severity"] == finding.severity.value
        assert formatted["confidence"] == finding.confidence
        assert formatted["is_bug"] == finding.is_bug()
        assert formatted["is_reportable"] == finding.is_reportable()

    def test_format_session(self):
        """Session formatting works correctly."""
        session = create_test_session()
        
        formatted = ResponseFormatter.format_session(session)
        
        assert formatted["id"] == session.id
        assert formatted["target"] == session.target.domain
        assert formatted["is_active"] == session.is_active
        assert formatted["finding_count"] == 0

    def test_format_error(self):
        """Error formatting works correctly."""
        error = ResponseFormatter.format_error(-32600, "Invalid request")
        
        assert error["code"] == -32600
        assert error["message"] == "Invalid request"

    def test_format_error_with_data(self):
        """Error formatting with data works correctly."""
        error = ResponseFormatter.format_error(
            -32600,
            "Invalid request",
            data={"field": "target"},
        )
        
        assert error["code"] == -32600
        assert error["data"]["field"] == "target"

    @given(st.floats(min_value=0.0, max_value=1.0))
    @settings(max_examples=20)
    def test_confidence_preserved_in_formatting(self, confidence: float):
        """Confidence values are preserved in formatting."""
        finding = create_test_finding(confidence=confidence)
        
        formatted = ResponseFormatter.format_finding(finding)
        
        assert formatted["confidence"] == confidence


class TestServerToolHandlers:
    """Tests for server tool handlers."""

    @pytest.mark.asyncio
    async def test_create_session_handler(self):
        """create_session handler works correctly."""
        server = MCPServer()
        
        result = await server.handle_tool_call(
            "create_session",
            {"target_domain": "example.com"},
        )
        
        assert "session_id" in result
        assert result["target"] == "example.com"
        assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_list_sessions_handler(self):
        """list_sessions handler works correctly."""
        server = MCPServer()
        
        # Create some sessions
        await server.handle_tool_call("create_session", {"target_domain": "a.com"})
        await server.handle_tool_call("create_session", {"target_domain": "b.com"})
        
        result = await server.handle_tool_call("list_sessions", {})
        
        assert result["total"] == 2
        assert len(result["sessions"]) == 2

    @pytest.mark.asyncio
    async def test_get_session_handler(self):
        """get_session handler works correctly."""
        server = MCPServer()
        
        create_result = await server.handle_tool_call(
            "create_session",
            {"target_domain": "example.com"},
        )
        
        result = await server.handle_tool_call(
            "get_session",
            {"session_id": create_result["session_id"]},
        )
        
        assert result["id"] == create_result["session_id"]
        assert result["target"] == "example.com"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_handler(self):
        """get_session handler returns error for nonexistent session."""
        server = MCPServer()
        
        result = await server.handle_tool_call(
            "get_session",
            {"session_id": "nonexistent"},
        )
        
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_findings_handler(self):
        """get_findings handler works correctly."""
        server = MCPServer()
        
        create_result = await server.handle_tool_call(
            "create_session",
            {"target_domain": "example.com"},
        )
        
        result = await server.handle_tool_call(
            "get_findings",
            {"session_id": create_result["session_id"]},
        )
        
        assert result["session_id"] == create_result["session_id"]
        assert "findings" in result
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self):
        """Unknown tool raises ValueError."""
        server = MCPServer()
        
        with pytest.raises(ValueError, match="not found"):
            await server.handle_tool_call("nonexistent_tool", {})


class TestIntegration:
    """Integration tests for MCP server."""

    @pytest.mark.asyncio
    async def test_full_hunting_workflow(self):
        """Test complete hunting workflow."""
        server = MCPServer()
        
        # Create session
        create_result = await server.handle_tool_call(
            "create_session",
            {"target_domain": "example.com", "program_name": "Test Program"},
        )
        session_id = create_result["session_id"]
        
        # Verify session exists
        session_result = await server.handle_tool_call(
            "get_session",
            {"session_id": session_id},
        )
        assert session_result["target"] == "example.com"
        
        # List sessions
        list_result = await server.handle_tool_call("list_sessions", {})
        assert list_result["total"] >= 1
        
        # Get findings (should be empty initially)
        findings_result = await server.handle_tool_call(
            "get_findings",
            {"session_id": session_id},
        )
        assert findings_result["total"] == 0

    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self):
        """Test multiple concurrent sessions."""
        server = MCPServer()
        
        # Create multiple sessions
        sessions = []
        for i in range(5):
            result = await server.handle_tool_call(
                "create_session",
                {"target_domain": f"target{i}.com"},
            )
            sessions.append(result["session_id"])
        
        # Verify all sessions exist
        list_result = await server.handle_tool_call("list_sessions", {})
        assert list_result["total"] == 5
        assert list_result["active"] == 5
        
        # Verify each session
        for session_id in sessions:
            result = await server.handle_tool_call(
                "get_session",
                {"session_id": session_id},
            )
            assert result["id"] == session_id
            assert result["is_active"] is True
