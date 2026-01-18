"""
Phase-29 API Server

GOVERNANCE:
- CONNECTIVITY ONLY — wraps existing execution_layer
- All endpoints require human_initiated=True
- NO background threads or tasks
- NO automation, inference, or scoring
- NO modification of frozen phases
"""

from datetime import datetime, timezone
from typing import Any, Optional
from pathlib import Path
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from phase29_api.types import (
    GovernanceViolationError,
    BrowserStartResponse,
    BrowserActionResponse,
    BrowserStopResponse,
    BrowserStatusResponse,
    EvidenceResponse,
    ErrorResponse,
    DISCLAIMER_START,
    DISCLAIMER_ACTION,
    DISCLAIMER_EVIDENCE,
    DISCLAIMER_STOP,
    DISCLAIMER_STATUS,
)
from phase29_api.validation import (
    validate_human_initiated,
    validate_session_id,
    validate_action,
    validate_no_automation_metadata,
)


# =============================================================================
# PYDANTIC MODELS FOR REQUEST VALIDATION
# =============================================================================


class InitiationMetadataModel(BaseModel):
    """Pydantic model for initiation metadata."""
    timestamp: str
    element_id: str
    user_action: str


class SessionConfigModel(BaseModel):
    """Pydantic model for session config."""
    enable_video: bool = False
    viewport_width: int = 1280
    viewport_height: int = 720


class BrowserStartRequest(BaseModel):
    """Request body for POST /api/browser/start."""
    human_initiated: bool
    session_config: Optional[SessionConfigModel] = None
    initiation_metadata: Optional[InitiationMetadataModel] = None


class ActionModel(BaseModel):
    """Pydantic model for browser action."""
    action_type: str
    target: str
    parameters: dict[str, Any] = {}


class BrowserActionRequest(BaseModel):
    """Request body for POST /api/browser/action."""
    human_initiated: bool
    session_id: str
    action: ActionModel
    initiation_metadata: Optional[InitiationMetadataModel] = None


class BrowserStopRequest(BaseModel):
    """Request body for POST /api/browser/stop."""
    human_initiated: bool
    session_id: str
    initiation_metadata: Optional[InitiationMetadataModel] = None


# =============================================================================
# APPLICATION SETUP
# =============================================================================


app = FastAPI(
    title="Phase-29 Browser API",
    description="CONNECTIVITY ONLY — Human-initiated browser execution",
    version="29.0.0",
)

# CORS configuration for localhost development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# =============================================================================
# SESSION STORAGE (In-Memory for Phase-29)
# =============================================================================


class SessionStore:
    """In-memory session storage.
    
    GOVERNANCE: No persistence, no background cleanup.
    Sessions are stored in memory only.
    """
    
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
    
    def create(self, session_id: str, execution_id: str, config: dict[str, Any]) -> None:
        """Create a new session."""
        self._sessions[session_id] = {
            "session_id": session_id,
            "execution_id": execution_id,
            "config": config,
            "status": "active",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "action_count": 0,
            "evidence": {
                "screenshots": [],
                "har_path": None,
                "video_path": None,
                "console_logs": [],
            },
        }
    
    def get(self, session_id: str) -> Optional[dict[str, Any]]:
        """Get session by ID."""
        return self._sessions.get(session_id)
    
    def update(self, session_id: str, updates: dict[str, Any]) -> None:
        """Update session data."""
        if session_id in self._sessions:
            self._sessions[session_id].update(updates)
    
    def increment_action_count(self, session_id: str) -> None:
        """Increment action count."""
        if session_id in self._sessions:
            self._sessions[session_id]["action_count"] += 1
    
    def add_evidence(self, session_id: str, evidence_type: str, data: Any) -> None:
        """Add evidence to session."""
        if session_id in self._sessions:
            if evidence_type == "screenshot":
                self._sessions[session_id]["evidence"]["screenshots"].append(data)
            elif evidence_type == "console_log":
                self._sessions[session_id]["evidence"]["console_logs"].append(data)
            else:
                self._sessions[session_id]["evidence"][evidence_type] = data
    
    def stop(self, session_id: str) -> Optional[dict[str, Any]]:
        """Stop session and return final state."""
        session = self._sessions.get(session_id)
        if session:
            session["status"] = "stopped"
            session["stopped_at"] = datetime.now(timezone.utc).isoformat()
        return session
    
    def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self._sessions


# Global session store
_session_store = SessionStore()


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================


@app.exception_handler(GovernanceViolationError)
async def governance_violation_handler(
    request: Request, exc: GovernanceViolationError
) -> JSONResponse:
    """Handle governance violations."""
    return JSONResponse(
        status_code=403,
        content={
            "success": False,
            "error": str(exc),
            "code": "GOVERNANCE_VIOLATION",
        },
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@app.post("/api/browser/start")
async def browser_start(request: BrowserStartRequest) -> dict[str, Any]:
    """Start a new browser session.
    
    GOVERNANCE: Requires human_initiated=True.
    NO background execution.
    """
    # GOVERNANCE: Validate human initiation
    validate_human_initiated(request.model_dump())
    
    if request.initiation_metadata:
        validate_no_automation_metadata(request.initiation_metadata.model_dump())
    
    # Generate IDs
    session_id = str(uuid.uuid4())
    execution_id = str(uuid.uuid4())
    
    # Create session
    config = request.session_config.model_dump() if request.session_config else {}
    _session_store.create(session_id, execution_id, config)
    
    return {
        "success": True,
        "session_id": session_id,
        "execution_id": execution_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "human_initiated": True,
        "disclaimer": DISCLAIMER_START,
    }


@app.post("/api/browser/action")
async def browser_action(request: BrowserActionRequest) -> dict[str, Any]:
    """Execute a browser action.
    
    GOVERNANCE: Requires human_initiated=True.
    Actions are explicit, not automated.
    """
    # GOVERNANCE: Validate human initiation
    validate_human_initiated(request.model_dump())
    
    if request.initiation_metadata:
        validate_no_automation_metadata(request.initiation_metadata.model_dump())
    
    # Validate action
    validate_action(request.action.model_dump())
    
    # Check session exists
    session = _session_store.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["status"] != "active":
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Generate action ID
    action_id = str(uuid.uuid4())
    executed_at = datetime.now(timezone.utc).isoformat()
    
    # Increment action count
    _session_store.increment_action_count(request.session_id)
    
    # Simulate action result (actual browser execution would go here)
    result: dict[str, Any] = {
        "action_id": action_id,
        "executed": True,
    }
    
    if request.action.action_type == "navigate":
        result["url"] = request.action.target
        result["status_code"] = 200
    elif request.action.action_type == "click":
        result["clicked"] = True
    elif request.action.action_type == "scroll":
        result["scrolled"] = True
    elif request.action.action_type == "screenshot":
        # Add screenshot to evidence
        screenshot_data = {
            "path": f"/evidence/{session['execution_id']}/screenshots/{action_id}.png",
            "captured_at": executed_at,
            "label": request.action.parameters.get("label", action_id),
        }
        _session_store.add_evidence(request.session_id, "screenshot", screenshot_data)
        result["screenshot_path"] = screenshot_data["path"]
    
    return {
        "success": True,
        "action_id": action_id,
        "action_type": request.action.action_type,
        "executed_at": executed_at,
        "result": result,
        "human_initiated": True,
        "disclaimer": DISCLAIMER_ACTION,
    }


@app.get("/api/browser/evidence")
async def browser_evidence(session_id: str, human_initiated: bool) -> dict[str, Any]:
    """Get evidence for a session.
    
    GOVERNANCE: Requires human_initiated=True.
    Evidence is READ-ONLY, no interpretation.
    """
    # GOVERNANCE: Validate human initiation
    validate_human_initiated({"human_initiated": human_initiated})
    
    # Check session exists
    session = _session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "session_id": session_id,
        "evidence": session["evidence"],
        "human_initiated": True,
        "disclaimer": DISCLAIMER_EVIDENCE,
    }


@app.post("/api/browser/stop")
async def browser_stop(request: BrowserStopRequest) -> dict[str, Any]:
    """Stop a browser session.
    
    GOVERNANCE: Requires human_initiated=True.
    Finalizes evidence capture.
    """
    # GOVERNANCE: Validate human initiation
    validate_human_initiated(request.model_dump())
    
    if request.initiation_metadata:
        validate_no_automation_metadata(request.initiation_metadata.model_dump())
    
    # Check session exists
    session = _session_store.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Stop session
    final_session = _session_store.stop(request.session_id)
    
    return {
        "success": True,
        "session_id": request.session_id,
        "stopped_at": final_session["stopped_at"] if final_session else datetime.now(timezone.utc).isoformat(),
        "evidence_summary": {
            "screenshot_count": len(session["evidence"]["screenshots"]),
            "har_captured": session["evidence"]["har_path"] is not None,
            "video_captured": session["evidence"]["video_path"] is not None,
            "console_log_count": len(session["evidence"]["console_logs"]),
        },
        "human_initiated": True,
        "disclaimer": DISCLAIMER_STOP,
    }


@app.get("/api/browser/status")
async def browser_status(session_id: str, human_initiated: bool) -> dict[str, Any]:
    """Get session status.
    
    GOVERNANCE: Requires human_initiated=True.
    Status is READ-ONLY.
    """
    # GOVERNANCE: Validate human initiation
    validate_human_initiated({"human_initiated": human_initiated})
    
    # Check session exists
    session = _session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "session_id": session_id,
        "status": session["status"],
        "started_at": session["started_at"],
        "action_count": session["action_count"],
        "human_initiated": True,
        "disclaimer": DISCLAIMER_STATUS,
    }


# =============================================================================
# HEALTH CHECK (No human_initiated required for health)
# =============================================================================


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint.
    
    GOVERNANCE: Health check does not require human_initiated.
    """
    return {
        "status": "healthy",
        "phase": "29",
        "governance": "CONNECTIVITY-ONLY",
    }
