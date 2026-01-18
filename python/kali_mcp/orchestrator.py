"""
Hunt Orchestrator - Coordinates bug bounty hunting workflows.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable, Awaitable
import uuid

from .types import (
    Target,
    BugBountyProgram,
    Finding,
    HuntSession,
    HuntPhase,
    Severity,
    FindingClassification,
    Service,
    Protocol,
    TechnologyProfile,
)

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    PAUSED = auto()


@dataclass
class WorkflowStep:
    """Single step in a hunting workflow."""
    name: str
    phase: HuntPhase
    handler: Callable[..., Awaitable[Dict[str, Any]]]
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 3


@dataclass
class WorkflowResult:
    """Result of a workflow step execution."""
    step_name: str
    status: WorkflowStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowEngine:
    """Executes multi-phase hunting workflows."""

    def __init__(self):
        self._steps: Dict[str, WorkflowStep] = {}
        self._results: Dict[str, WorkflowResult] = {}

    def register_step(self, step: WorkflowStep) -> None:
        """Register a workflow step."""
        self._steps[step.name] = step
        logger.debug(f"Registered workflow step: {step.name}")

    async def execute_step(
        self,
        step_name: str,
        context: Dict[str, Any],
    ) -> WorkflowResult:
        """Execute a single workflow step."""
        step = self._steps.get(step_name)
        if not step:
            return WorkflowResult(
                step_name=step_name,
                status=WorkflowStatus.FAILED,
                error=f"Step not found: {step_name}",
            )

        # Check dependencies
        for dep in step.dependencies:
            dep_result = self._results.get(dep)
            if not dep_result or dep_result.status != WorkflowStatus.COMPLETED:
                return WorkflowResult(
                    step_name=step_name,
                    status=WorkflowStatus.FAILED,
                    error=f"Dependency not satisfied: {dep}",
                )

        started_at = datetime.utcnow()
        try:
            output = await asyncio.wait_for(
                step.handler(context),
                timeout=step.timeout_seconds,
            )
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            result = WorkflowResult(
                step_name=step_name,
                status=WorkflowStatus.COMPLETED,
                output=output,
                duration_ms=duration_ms,
                started_at=started_at,
                completed_at=completed_at,
            )
        except asyncio.TimeoutError:
            result = WorkflowResult(
                step_name=step_name,
                status=WorkflowStatus.FAILED,
                error="Step timed out",
                started_at=started_at,
            )
        except Exception as e:
            logger.exception(f"Step {step_name} failed: {e}")
            result = WorkflowResult(
                step_name=step_name,
                status=WorkflowStatus.FAILED,
                error=str(e),
                started_at=started_at,
            )

        self._results[step_name] = result
        return result

    async def execute_phase(
        self,
        phase: HuntPhase,
        context: Dict[str, Any],
    ) -> List[WorkflowResult]:
        """Execute all steps in a phase."""
        phase_steps = [s for s in self._steps.values() if s.phase == phase]
        results = []
        
        for step in phase_steps:
            result = await self.execute_step(step.name, context)
            results.append(result)
            
            # Stop on failure unless step is optional
            if result.status == WorkflowStatus.FAILED:
                logger.warning(f"Phase {phase.name} step {step.name} failed")
                break
        
        return results

    def get_results(self) -> Dict[str, WorkflowResult]:
        """Get all workflow results."""
        return self._results.copy()

    def reset(self) -> None:
        """Reset workflow state."""
        self._results.clear()


class ToolSelector:
    """Selects optimal tools based on target characteristics."""

    def __init__(self):
        self._tool_capabilities: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register default tool capabilities."""
        self._tool_capabilities = {
            "nmap": {
                "category": "reconnaissance",
                "capabilities": ["port_scan", "service_detection", "os_detection"],
                "protocols": ["tcp", "udp"],
                "speed": "medium",
            },
            "subfinder": {
                "category": "reconnaissance",
                "capabilities": ["subdomain_enumeration"],
                "speed": "fast",
            },
            "httpx": {
                "category": "reconnaissance",
                "capabilities": ["http_probe", "technology_detection"],
                "speed": "fast",
            },
            "nuclei": {
                "category": "scanning",
                "capabilities": ["vulnerability_scan", "template_based"],
                "speed": "medium",
            },
            "sqlmap": {
                "category": "exploitation",
                "capabilities": ["sql_injection"],
                "speed": "slow",
            },
            "ffuf": {
                "category": "scanning",
                "capabilities": ["directory_bruteforce", "parameter_fuzzing"],
                "speed": "fast",
            },
        }

    def select_tools(
        self,
        target: Target,
        phase: HuntPhase,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Select optimal tools for a target and phase."""
        selected = []
        
        phase_category = {
            HuntPhase.RECONNAISSANCE: "reconnaissance",
            HuntPhase.SCANNING: "scanning",
            HuntPhase.EXPLOITATION: "exploitation",
        }.get(phase)
        
        if not phase_category:
            return selected
        
        for tool_name, capabilities in self._tool_capabilities.items():
            if capabilities.get("category") == phase_category:
                selected.append(tool_name)
        
        # Apply constraints
        if constraints:
            if constraints.get("fast_only"):
                selected = [
                    t for t in selected
                    if self._tool_capabilities[t].get("speed") == "fast"
                ]
        
        return selected

    def get_tool_capabilities(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get capabilities of a specific tool."""
        return self._tool_capabilities.get(tool_name)


class TargetAnalyzer:
    """Analyzes targets for reconnaissance and profiling."""

    async def analyze(self, target: Target) -> Dict[str, Any]:
        """Perform initial target analysis."""
        analysis = {
            "domain": target.domain,
            "subdomain_count": len(target.subdomains),
            "service_count": len(target.services),
            "has_web_services": any(
                s.protocol in [Protocol.HTTP, Protocol.HTTPS]
                for s in target.services
            ),
            "has_authentication": target.authentication is not None,
            "technology_stack": self._analyze_technology_stack(target.technology_stack),
            "attack_surface_score": self._calculate_attack_surface(target),
        }
        return analysis

    def _analyze_technology_stack(self, stack: TechnologyProfile) -> Dict[str, Any]:
        """Analyze technology stack for known vulnerabilities."""
        return {
            "web_server": stack.web_server,
            "framework": stack.application_framework,
            "language": stack.programming_language,
            "database": stack.database,
            "known_issues": [],  # Would be populated from vulnerability database
        }

    def _calculate_attack_surface(self, target: Target) -> float:
        """Calculate attack surface score (0-100)."""
        score = 0.0
        
        # More subdomains = larger attack surface
        score += min(len(target.subdomains) * 2, 30)
        
        # More services = larger attack surface
        score += min(len(target.services) * 5, 40)
        
        # Web services add to attack surface
        web_services = [
            s for s in target.services
            if s.protocol in [Protocol.HTTP, Protocol.HTTPS]
        ]
        score += min(len(web_services) * 10, 30)
        
        return min(score, 100.0)


class HuntOrchestrator:
    """
    Coordinates bug bounty hunting workflows.
    
    Manages the execution of multi-phase hunting strategies,
    tool selection, and finding aggregation.
    """

    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.tool_selector = ToolSelector()
        self.target_analyzer = TargetAnalyzer()
        self._active_sessions: Dict[str, HuntSession] = {}
        self._setup_default_workflow()

    def _setup_default_workflow(self) -> None:
        """Set up default hunting workflow steps."""
        # Reconnaissance steps
        self.workflow_engine.register_step(WorkflowStep(
            name="subdomain_enumeration",
            phase=HuntPhase.RECONNAISSANCE,
            handler=self._step_subdomain_enumeration,
        ))
        
        self.workflow_engine.register_step(WorkflowStep(
            name="service_discovery",
            phase=HuntPhase.RECONNAISSANCE,
            handler=self._step_service_discovery,
            dependencies=["subdomain_enumeration"],
        ))
        
        self.workflow_engine.register_step(WorkflowStep(
            name="technology_fingerprinting",
            phase=HuntPhase.RECONNAISSANCE,
            handler=self._step_technology_fingerprinting,
            dependencies=["service_discovery"],
        ))
        
        # Scanning steps
        self.workflow_engine.register_step(WorkflowStep(
            name="vulnerability_scan",
            phase=HuntPhase.SCANNING,
            handler=self._step_vulnerability_scan,
            dependencies=["technology_fingerprinting"],
        ))

    async def start_hunt(
        self,
        target: Target,
        program: Optional[BugBountyProgram] = None,
    ) -> HuntSession:
        """Start a new hunting session."""
        session = HuntSession(target=target, program=program)
        self._active_sessions[session.id] = session
        
        logger.info(f"Started hunt session {session.id} for {target.domain}")
        return session

    async def execute_phase(
        self,
        session_id: str,
        phase: HuntPhase,
    ) -> List[WorkflowResult]:
        """Execute a hunting phase for a session."""
        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        context = {
            "session": session,
            "target": session.target,
            "program": session.program,
        }
        
        session.current_phase = phase
        results = await self.workflow_engine.execute_phase(phase, context)
        
        return results

    def select_tools(
        self,
        target: Target,
        phase: HuntPhase,
    ) -> List[str]:
        """Select optimal tools for a target and phase."""
        return self.tool_selector.select_tools(target, phase)

    async def analyze_target(self, target: Target) -> Dict[str, Any]:
        """Analyze a target for hunting."""
        return await self.target_analyzer.analyze(target)

    def get_session(self, session_id: str) -> Optional[HuntSession]:
        """Get a hunting session by ID."""
        return self._active_sessions.get(session_id)

    def list_active_sessions(self) -> List[HuntSession]:
        """List all active hunting sessions."""
        return [s for s in self._active_sessions.values() if s.is_active]

    # Workflow step handlers
    async def _step_subdomain_enumeration(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute subdomain enumeration step."""
        target = context.get("target")
        if not target:
            return {"error": "No target specified"}
        
        # This would integrate with actual subdomain enumeration tools
        return {
            "domain": target.domain,
            "subdomains_found": 0,
            "sources": ["passive_dns", "certificate_transparency"],
            "status": "completed",
        }

    async def _step_service_discovery(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute service discovery step."""
        target = context.get("target")
        if not target:
            return {"error": "No target specified"}
        
        return {
            "domain": target.domain,
            "services_found": 0,
            "status": "completed",
        }

    async def _step_technology_fingerprinting(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute technology fingerprinting step."""
        target = context.get("target")
        if not target:
            return {"error": "No target specified"}
        
        return {
            "domain": target.domain,
            "technologies": {},
            "status": "completed",
        }

    async def _step_vulnerability_scan(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute vulnerability scanning step."""
        target = context.get("target")
        if not target:
            return {"error": "No target specified"}
        
        return {
            "domain": target.domain,
            "vulnerabilities_found": 0,
            "status": "completed",
        }