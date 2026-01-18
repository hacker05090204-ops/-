"""
Tool Orchestrator - Executes tools and submits outputs to MCP

ARCHITECTURAL CONSTRAINTS:
    1. ALL tool outputs are UNTRUSTED signals
    2. Tool outputs are NEVER interpreted as vulnerabilities
    3. All outputs MUST be submitted to MCP for classification
    4. Orchestrator does NOT classify, only executes and submits
"""

import logging
import subprocess
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone

from .types import (
    Hypothesis,
    HypothesisStatus,
    Observation,
    ExplorationAction,
    ActionType,
    ActionResult,
    ToolOutput,
    MCPClassification,
)
from .client import MCPClient, ObservationSubmissionGuard
from .errors import (
    ExplorationError,
    MCPUnavailableError,
    ArchitecturalViolationError,
)

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a security tool.
    
    NOTE: Tools are signal generators only.
    Their outputs are UNTRUSTED until MCP validates them.
    """
    name: str
    command: str
    args_template: str = ""
    timeout_seconds: int = 60
    output_parser: Optional[Callable[[str], List[Dict[str, Any]]]] = None


# Tool catalog - these are signal generators, not vulnerability detectors
TOOL_CATALOG: Dict[str, ToolDefinition] = {
    "http_probe": ToolDefinition(
        name="http_probe",
        command="curl",
        args_template="-s -o /dev/null -w '%{{http_code}}' {url}",
        timeout_seconds=30,
    ),
    "header_check": ToolDefinition(
        name="header_check",
        command="curl",
        args_template="-s -I {url}",
        timeout_seconds=30,
    ),
}


class ToolOrchestrator:
    """Orchestrates tool execution and MCP submission.
    
    ARCHITECTURAL CONSTRAINTS:
        - ALL tool outputs are UNTRUSTED
        - Tool outputs are NEVER vulnerabilities until MCP says so
        - All outputs MUST be submitted to MCP
        - This class does NOT classify findings
    """
    
    def __init__(self, mcp_client: MCPClient):
        """Initialize orchestrator with MCP client.
        
        Args:
            mcp_client: Client for submitting observations to MCP
        """
        self._mcp_client = mcp_client
        self._submission_guard = ObservationSubmissionGuard(mcp_client)
        self._tool_catalog = TOOL_CATALOG.copy()
    
    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        capture_state: bool = True
    ) -> ToolOutput:
        """Execute a tool and capture its output.
        
        CRITICAL: Tool output is an UNTRUSTED signal.
        Even if the tool claims to find a "vulnerability", it is only
        a hypothesis until MCP validates it.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            capture_state: Whether to capture before/after state
            
        Returns:
            ToolOutput with raw output (UNTRUSTED)
            
        Raises:
            ExplorationError: If tool execution fails
        """
        tool = self._tool_catalog.get(tool_name)
        if not tool:
            raise ExplorationError(f"Unknown tool: {tool_name}")
        
        start_time = time.time()
        
        try:
            # Build command
            args = tool.args_template.format(**parameters)
            full_command = f"{tool.command} {args}"
            
            logger.debug(f"Executing tool: {full_command}")
            
            # Execute tool
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=tool.timeout_seconds,
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Parse output if parser available
            parsed = []
            if tool.output_parser:
                try:
                    parsed = tool.output_parser(result.stdout)
                except Exception as e:
                    logger.warning(f"Failed to parse tool output: {e}")
            
            return ToolOutput(
                tool_name=tool_name,
                raw_output=result.stdout,
                parsed_findings=parsed,  # These are UNTRUSTED signals
                exit_code=result.returncode,
                execution_time_ms=execution_time,
            )
            
        except subprocess.TimeoutExpired:
            execution_time = int((time.time() - start_time) * 1000)
            return ToolOutput(
                tool_name=tool_name,
                raw_output="TIMEOUT",
                parsed_findings=[],
                exit_code=-1,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            raise ExplorationError(f"Tool execution failed: {e}")
    
    def normalize_output(self, tool_output: ToolOutput) -> Dict[str, Any]:
        """Normalize tool output to standard format.
        
        NOTE: Normalization does NOT interpret the output.
        It only structures it for MCP submission.
        
        Args:
            tool_output: Raw tool output
            
        Returns:
            Normalized output dictionary
        """
        return {
            "tool": tool_output.tool_name,
            "raw": tool_output.raw_output,
            "parsed": tool_output.parsed_findings,
            "exit_code": tool_output.exit_code,
            "execution_time_ms": tool_output.execution_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # NOTE: No "is_vulnerability" field - that's MCP's determination
        }
    
    def submit_to_mcp(
        self,
        hypothesis: Hypothesis,
        action: ExplorationAction,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        tool_outputs: List[ToolOutput]
    ) -> MCPClassification:
        """Submit observation to MCP for classification.
        
        CRITICAL: This is the ONLY way findings are classified.
        Cyfer Brain submits; MCP judges.
        
        Args:
            hypothesis: The hypothesis being tested
            action: The action that was executed
            before_state: State before action
            after_state: State after action
            tool_outputs: Tool outputs (UNTRUSTED signals)
            
        Returns:
            MCPClassification from MCP (authoritative)
            
        Raises:
            MCPUnavailableError: If MCP is unreachable (HARD STOP)
        """
        # Create observation
        observation = Observation(
            hypothesis_id=hypothesis.id,
            before_state=before_state,
            action=action,
            after_state=after_state,
            tool_outputs=tool_outputs,
        )
        
        # Register with guard
        self._submission_guard.register_observation(observation)
        
        # Update hypothesis status
        hypothesis.status = HypothesisStatus.SUBMITTED
        
        # Submit and get classification
        classification = self._submission_guard.submit_and_clear(observation)
        
        # Update hypothesis with MCP classification
        hypothesis.mcp_classification = classification
        hypothesis.status = HypothesisStatus.RESOLVED
        
        logger.info(
            f"MCP classified hypothesis {hypothesis.id} as {classification.classification}"
        )
        
        return classification
    
    def execute_hypothesis(
        self,
        hypothesis: Hypothesis,
        state_capturer: Optional[Callable[[], Dict[str, Any]]] = None
    ) -> MCPClassification:
        """Execute a hypothesis and submit to MCP.
        
        This is the main entry point for testing a hypothesis.
        
        Args:
            hypothesis: The hypothesis to test
            state_capturer: Optional function to capture state
            
        Returns:
            MCPClassification from MCP
            
        Raises:
            MCPUnavailableError: If MCP is unreachable
            ExplorationError: If execution fails
        """
        # Capture before state
        before_state = state_capturer() if state_capturer else {}
        
        # Execute test actions
        tool_outputs = []
        last_action = None
        
        for action in hypothesis.test_actions:
            hypothesis.status = HypothesisStatus.TESTING
            
            # Execute action
            if action.action_type == ActionType.TOOL_EXECUTION:
                tool_name = action.parameters.get("tool_name", "")
                tool_params = action.parameters.get("tool_params", {})
                
                output = self.execute_tool(tool_name, tool_params)
                tool_outputs.append(output)
            
            last_action = action
        
        # Capture after state
        after_state = state_capturer() if state_capturer else {}
        
        # Create default action if none executed
        if last_action is None:
            last_action = ExplorationAction(
                action_type=ActionType.TOOL_EXECUTION,
                target=hypothesis.description,
            )
        
        # Submit to MCP
        return self.submit_to_mcp(
            hypothesis=hypothesis,
            action=last_action,
            before_state=before_state,
            after_state=after_state,
            tool_outputs=tool_outputs,
        )
    
    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a new tool in the catalog.
        
        Args:
            tool: Tool definition to register
        """
        self._tool_catalog[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    # =========================================================================
    # EXPLICITLY REJECTED METHODS
    # =========================================================================
    
    def classify_output(self, *args, **kwargs):
        """REJECTED: Classification is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "classify tool output",
            "Submit observations to MCP via submit_to_mcp() instead."
        )
    
    def interpret_finding(self, *args, **kwargs):
        """REJECTED: Interpretation is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "interpret a finding",
            "Tool outputs are UNTRUSTED. Only MCP can interpret them."
        )
