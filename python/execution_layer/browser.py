"""
Execution Layer Browser Engine

REAL Playwright browser execution. NO SIMULATION.
All actions execute against a real browser instance.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, TYPE_CHECKING
import asyncio
import os

from playwright.async_api import Browser, BrowserContext, Page

from execution_layer.types import SafeAction, SafeActionType
from execution_layer.errors import (
    BrowserSessionError,
    BrowserCrashError,
    NavigationFailureError,
    CSPBlockError,
    ExecutionLayerError,
    HeadlessOverrideError,
    BrowserFailure,
)
from execution_layer.recovery import BrowserResilienceManager, ResilienceConfig
from execution_layer.browser_launcher import BrowserLauncher, PlaywrightBrowserLauncher

if TYPE_CHECKING:
    from execution_layer.browser_failure import BrowserFailureHandler


@dataclass
class BrowserConfig:
    """Configuration for browser execution.
    
    SECURITY: headless=True is the MANDATORY default.
    Setting headless=False requires explicit human approval flag.
    """
    headless: bool = True
    headless_override_approved: bool = False  # REQUIRED if headless=False
    artifacts_dir: str = "artifacts"
    viewport_width: int = 1280
    viewport_height: int = 720
    timeout_ms: int = 30000
    slow_mo_ms: int = 0  # Slow down actions for debugging
    per_action_delay_seconds: float = 2.0  # Configurable delay between actions
    
    # Resilience Config
    max_restarts: int = 3
    enable_resilience: bool = False
    
    def __post_init__(self) -> None:
        # SECURITY GUARDRAIL: headless=False requires explicit approval
        if not self.headless and not self.headless_override_approved:
            raise HeadlessOverrideError(
                "headless=False requires headless_override_approved=True — "
                "HIGH-RISK: Non-headless mode exposes browser UI. "
                "Set headless_override_approved=True to acknowledge this risk."
            )
        # Validate per_action_delay_seconds
        if self.per_action_delay_seconds < 0:
            raise ValueError("per_action_delay_seconds must be >= 0")


@dataclass
class BrowserSession:
    """Active browser session with evidence capture enabled."""
    session_id: str
    execution_id: str
    browser: Browser
    context: BrowserContext
    page: Page
    har_path: Path
    video_dir: Path
    screenshots_dir: Path
    started_at: datetime
    screenshot_paths: list[Path] = field(default_factory=list)
    console_logs: list[dict[str, Any]] = field(default_factory=list)
    
    # Track restart counts in session for evidence bundle reference
    failure_count: int = 0


class BrowserEngine:
    """Real Playwright browser execution engine.
    
    MANDATORY: All execution is REAL. No simulation allowed.
    - Real browser launch via Playwright
    - Real HAR capture to disk
    - Real video recording to disk
    - Real screenshots to disk
    
    Optional failure_handler for evidence preservation on failures.
    NOTE: Failure handler does NOT implement automatic retry.
    All exceptions are propagated unchanged.
    """
    
    def __init__(
        self,
        config: Optional[BrowserConfig] = None,
        failure_handler: Optional["BrowserFailureHandler"] = None,
        launcher: Optional[BrowserLauncher] = None,
    ) -> None:
        self._config = config or BrowserConfig()
        self._failure_handler = failure_handler
        self._launcher: BrowserLauncher = launcher or PlaywrightBrowserLauncher()
        self._active_sessions: dict[str, BrowserSession] = {}
        
        # Resilience Manager
        resilience_config = ResilienceConfig(
            max_restarts_per_decision=self._config.max_restarts,
            enable_crash_detection=self._config.enable_resilience
        )
        self._resilience_manager = BrowserResilienceManager(resilience_config)
        
        # Ensure artifacts directory exists
        self._artifacts_path = Path(self._config.artifacts_dir)
        self._artifacts_path.mkdir(parents=True, exist_ok=True)
    
    async def start_session(
        self,
        session_id: str,
        execution_id: str,
        enable_video: bool = False,
    ) -> BrowserSession:
        """Start a new browser session with evidence capture.
        
        Args:
            session_id: Unique session identifier
            execution_id: Execution identifier for evidence grouping
            enable_video: Enable video recording (default: False)
        
        Returns:
            BrowserSession with active browser, context, and page
        
        Raises:
            BrowserSessionError: If browser fails to launch
            BrowserCrashError: If browser crashes during startup
        """
        if session_id in self._active_sessions:
            raise BrowserSessionError(f"Session '{session_id}' already exists")
        
        try:
            # Create session-specific directories
            session_dir = self._artifacts_path / execution_id
            har_dir = session_dir / "har"
            video_dir = session_dir / "videos"
            screenshots_dir = session_dir / "screenshots"
            
            har_dir.mkdir(parents=True, exist_ok=True)
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            har_path = har_dir / f"{session_id}.har"
            
            browser, context, page = await self._launcher.launch(
                self._config, har_path, video_dir, enable_video
            )
            
            # Create session
            session = BrowserSession(
                session_id=session_id,
                execution_id=execution_id,
                browser=browser,
                context=context,
                page=page,
                har_path=har_path,
                video_dir=video_dir,
                screenshots_dir=screenshots_dir,
                started_at=datetime.now(timezone.utc),
            )
            
            # Set up console log capture
            page.on("console", lambda msg: session.console_logs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": msg.type,
                "text": msg.text,
                "location": str(msg.location) if msg.location else None,
            }))
            
            self._active_sessions[session_id] = session
            return session
            
        except Exception as e:
            # Handle failure with failure_handler if available
            if self._failure_handler:
                self._failure_handler.handle_failure(
                    error=BrowserSessionError(f"Failed to start browser session: {e}"),
                    session_id=session_id,
                    execution_id=execution_id,
                    action=None,
                    partial_evidence=None,
                )
            raise BrowserSessionError(f"Failed to start browser session: {e}") from e
    
    async def capture_screenshot(
        self,
        session_id: str,
        label: str = "screenshot",
    ) -> Path:
        """Capture a screenshot in the current session.
        
        Args:
            session_id: Active session identifier
            label: Label for the screenshot file
            
        Returns:
            Path to the saved screenshot
            
        Raises:
            BrowserSessionError: If screenshot capture fails
        """
        session = self._get_session(session_id)
        
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            screenshot_path = session.screenshots_dir / f"{label}_{timestamp}.png"
            
            await session.page.screenshot(path=str(screenshot_path))
            session.screenshot_paths.append(screenshot_path)
            
            return screenshot_path
        except Exception as e:
            raise BrowserSessionError(f"Screenshot capture failed: {e}") from e
    
    async def stop_session(self, session_id: str) -> dict[str, Any]:
        """Stop browser session and finalize evidence capture.
        
        Args:
            session_id: Session to stop
        
        Returns:
            Evidence summary with file paths
            
        Raises:
            BrowserSessionError: If session cleanup fails
        """
        session = self._get_session(session_id)
        
        try:
            # Close context to finalize HAR and video
            try:
                if session.context:
                    await session.context.close()
                if session.browser:
                    await session.browser.close()
            except Exception:
                # Ignore close errors during cleanup
                pass
            
            # Collect video path if recorded
            video_path: Optional[Path] = None
            if session.video_dir.exists():
                video_files = list(session.video_dir.glob("*.webm"))
                if video_files:
                    video_path = video_files[0]
            
            evidence_summary = {
                "session_id": session_id,
                "execution_id": session.execution_id,
                "har_path": str(session.har_path) if session.har_path.exists() else None,
                "video_path": str(video_path) if video_path else None,
                "screenshot_paths": [str(p) for p in session.screenshot_paths],
                "console_logs": session.console_logs,
                "started_at": session.started_at.isoformat(),
                "stopped_at": datetime.now(timezone.utc).isoformat(),
                "failure_count": session.failure_count,
            }
            
            del self._active_sessions[session_id]
            return evidence_summary
            
        except Exception as e:
            # Collect partial evidence before handling failure
            partial_evidence = self._collect_partial_evidence(session)
            
            # Handle failure with failure_handler if available
            if self._failure_handler:
                self._failure_handler.handle_failure(
                    error=BrowserSessionError(f"Session cleanup failed: {e}"),
                    session_id=session_id,
                    execution_id=session.execution_id,
                    action=None,
                    partial_evidence=partial_evidence,
                )
            
            # Still try to remove from active sessions
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
            
            raise BrowserSessionError(f"Session cleanup failed: {e}") from e
            
    async def _restart_session(self, session_id: str) -> None:
        """Restart a failed browser session.
        
        Recoverable failure strategy:
        1. Clean up old browser/context (ignore errors)
        2. Launch new browser/context
        3. Update session object with new instances
        """
        session = self._get_session(session_id)
        
        # 1. Cleanup
        try:
            if session.context:
                await session.context.close()
            if session.browser:
                await session.browser.close()
        except Exception:
            pass
            
        # 2. Re-Launch (Logic copied from start_session, simplified)
        # Note: We reuse the existing self._playwright
        if self._playwright is None:
             self._playwright = await async_playwright().start()
             
        browser = await self._playwright.chromium.launch(
            headless=self._config.headless,
            slow_mo=self._config.slow_mo_ms,
        )
        
        # Re-create context
        context_options: dict[str, Any] = {
            "viewport": {
                "width": self._config.viewport_width,
                "height": self._config.viewport_height,
            },
            # Note: HAR path reused - Playwright might overwrite or fail if locked. 
            # Ideally we shift HAR filename.
            # But for Phase 4.1 "Basic Resilience", we accept overwrite or appends if supported.
            "record_har_path": str(session.har_path), 
            "record_har_content": "embed",
        }
        
        if session.video_dir.exists():
             context_options["record_video_dir"] = str(session.video_dir)
             context_options["record_video_size"] = {
                "width": self._config.viewport_width,
                "height": self._config.viewport_height,
            }
            
        context = await browser.new_context(**context_options)
        page = await context.new_page()
        page.set_default_timeout(self._config.timeout_ms)
        
        # Restore console logging
        page.on("console", lambda msg: session.console_logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": msg.type,
            "text": msg.text,
            "location": str(msg.location) if msg.location else None,
            "restarted": True,  # Mark log as post-restart
        }))
        
        # 3. Update Session
        session.browser = browser
        session.context = context
        session.page = page
        # Preserve other session attributes (evidence paths etc.)

    def _classify_error(self, e: Exception) -> Exception:
        """Classify generic exceptions into BrowserFailures."""
        msg = str(e).lower()
        if "target closed" in msg or "browser has been closed" in msg:
            return BrowserCrashError(f"Browser crash detected: {e}")
        if "timeout" in msg:
            return BrowserTimeoutError(f"Browser operation timed out: {e}")
        if "connection closed" in msg:
             return BrowserDisconnectError(f"Browser disconnected: {e}")
        return e
    
    def _collect_partial_evidence(self, session: "BrowserSession") -> Optional["PartialEvidence"]:
        """Collect any partial evidence from a failed session.
        
        This method attempts to preserve evidence captured before failure.
        Returns None if no evidence is available.
        """
        from execution_layer.browser_failure import PartialEvidence
        import hashlib
        
        try:
            # Try to collect HAR if available
            if session.har_path and session.har_path.exists():
                content = session.har_path.read_bytes()
                return PartialEvidence(
                    evidence_type="har",
                    content_hash=hashlib.sha256(content).hexdigest(),
                    captured_at=datetime.now(timezone.utc),
                    file_path=str(session.har_path),
                    metadata={"session_id": getattr(session, 'session_id', 'unknown')},
                )
            
            # Try to collect screenshots if available
            if session.screenshot_paths:
                last_screenshot = session.screenshot_paths[-1]
                if last_screenshot.exists():
                    content = last_screenshot.read_bytes()
                    return PartialEvidence(
                        evidence_type="screenshot",
                        content_hash=hashlib.sha256(content).hexdigest(),
                        captured_at=datetime.now(timezone.utc),
                        file_path=str(last_screenshot),
                        metadata={"session_id": getattr(session, 'session_id', 'unknown')},
                    )
            
            return None
        except Exception:
            # If evidence collection fails, return None rather than crash
            return None

    async def execute_action(
        self,
        session_id: str,
        action: SafeAction,
    ) -> dict[str, Any]:
        """Execute a safe action in the browser.
        
        Args:
            session_id: Active session identifier
            action: Safe action to execute
        
        Returns:
            Action result with any extracted data
        
        Raises:
            BrowserSessionError: If session not found or action fails
            BrowserCrashError: If browser crashes during execution
            NavigationFailureError: If navigation fails
            CSPBlockError: If CSP blocks the action
        """
        # Outer loop for resilience retry
        while True:
            session = self._get_session(session_id)
            page = session.page
            
            # Apply configurable per-action delay (default 2s)
            if self._config.per_action_delay_seconds > 0:
                await asyncio.sleep(self._config.per_action_delay_seconds)
            
            result: dict[str, Any] = {
                "action_id": action.action_id,
                "action_type": action.action_type.value,
                "target": action.target,
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "success": False,
                "delay_applied_seconds": self._config.per_action_delay_seconds,
            }
            
            try:
                if action.action_type == SafeActionType.NAVIGATE:
                    response = await page.goto(action.target, wait_until="networkidle")
                    result["status_code"] = response.status if response else None
                    result["url"] = page.url
                    
                elif action.action_type == SafeActionType.CLICK:
                    await page.click(action.target)
                    result["clicked"] = True
                    
                elif action.action_type == SafeActionType.INPUT_TEXT:
                    text = action.parameters.get("text", "")
                    await page.fill(action.target, text)
                    result["filled"] = True
                    
                elif action.action_type == SafeActionType.SCROLL:
                    direction = action.parameters.get("direction", "down")
                    amount_raw = action.parameters.get("amount", 300)
                    try:
                        amount = int(amount_raw)
                    except (TypeError, ValueError):
                        raise BrowserSessionError(
                            f"Invalid scroll amount: {amount_raw!r} - must be numeric"
                        )
                    if direction == "down":
                        await page.evaluate("(amount) => window.scrollBy(0, amount)", amount)
                    elif direction == "up":
                        await page.evaluate("(amount) => window.scrollBy(0, -amount)", amount)
                    result["scrolled"] = True
                    
                elif action.action_type == SafeActionType.WAIT:
                    wait_ms = action.parameters.get("timeout_ms", 1000)
                    selector = action.parameters.get("selector")
                    if selector:
                        await page.wait_for_selector(selector, timeout=wait_ms)
                    else:
                        await asyncio.sleep(wait_ms / 1000)
                    result["waited"] = True
                    
                elif action.action_type == SafeActionType.SCREENSHOT:
                    screenshot_path = await self.capture_screenshot(
                        session_id,
                        label=action.parameters.get("label", action.action_id),
                    )
                    result["screenshot_path"] = str(screenshot_path)
                    
                elif action.action_type == SafeActionType.GET_TEXT:
                    element = await page.query_selector(action.target)
                    if element:
                        result["text"] = await element.text_content()
                    else:
                        result["text"] = None
                        
                elif action.action_type == SafeActionType.GET_ATTRIBUTE:
                    attr_name = action.parameters.get("attribute", "")
                    element = await page.query_selector(action.target)
                    if element:
                        result["attribute_value"] = await element.get_attribute(attr_name)
                    else:
                        result["attribute_value"] = None
                        
                elif action.action_type == SafeActionType.HOVER:
                    await page.hover(action.target)
                    result["hovered"] = True
                    
                elif action.action_type == SafeActionType.SELECT_OPTION:
                    value = action.parameters.get("value", "")
                    await page.select_option(action.target, value)
                    result["selected"] = True
                
                result["success"] = True
                return result  # Success -> return immediately
                
            except Exception as e:
                # RESILIENCE LOGIC
                classified_error = self._classify_error(e)
                result["error"] = str(e)
                
                recoverable = self._resilience_manager.should_recover(classified_error)
                can_restart = self._resilience_manager.can_restart(session_id)
                
                if recoverable and can_restart:
                    # Log and Recover
                    self._resilience_manager.record_failure(session_id, classified_error)
                    self._resilience_manager.increment_restart_count(session_id)
                    session.failure_count = self._resilience_manager.get_state(session_id).restart_count
                    
                    await self._resilience_manager.wait_before_restart()
                    try:
                        await self._restart_session(session_id)
                        continue  # RETRY LOOP
                    except Exception as restart_error:
                         # Restart failed - Fatal
                         e = restart_error # Update error to restart failure
                
                # If we get here, either not recoverable, limit reached, or restart failed.
                
                # Collect partial evidence before handling failure
                partial_evidence = self._collect_partial_evidence(session)
                
                # Handle failure with failure_handler if available
                if self._failure_handler:
                    self._failure_handler.handle_failure(
                        error=BrowserSessionError(f"Action execution failed: {e}"),
                        session_id=session_id,
                        execution_id=session.execution_id,
                        action=action,
                        partial_evidence=partial_evidence,
                    )
                
                raise BrowserSessionError(f"Action execution failed: {e}") from e
    
    def _get_session(self, session_id: str) -> BrowserSession:
        """Get active session by ID."""
        session = self._active_sessions.get(session_id)
        if session is None:
            raise BrowserSessionError(f"No active session with ID '{session_id}'")
        return session
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if session is active."""
        return session_id in self._active_sessions
    
    async def cleanup(self) -> None:
        """Cleanup all sessions and launcher resources."""
        for session_id in list(self._active_sessions.keys()):
            try:
                await self.stop_session(session_id)
            except Exception:
                pass
        
        # Cleanup launcher resources
        await self._launcher.cleanup()
