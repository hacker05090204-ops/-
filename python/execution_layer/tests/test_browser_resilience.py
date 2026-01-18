
import asyncio
import os
import pytest
from pathlib import Path
from execution_layer.browser import BrowserEngine, BrowserConfig
from execution_layer.types import SafeAction, SafeActionType


# Skip unless ALLOW_REAL_BROWSER=1 is set
pytestmark = pytest.mark.skipif(
    os.environ.get("ALLOW_REAL_BROWSER") != "1",
    reason="Real browser tests require ALLOW_REAL_BROWSER=1"
)


@pytest.mark.asyncio
async def test_browser_resilience_recovery():
    """Verify browser recovers from crash (Track #5).
    
    This test requires a real browser and is skipped by default.
    Run with ALLOW_REAL_BROWSER=1 to execute.
    """
    print("\nStarting Resilience Test...")
    
    # 1. Init Engine with Resilience
    config = BrowserConfig(
        headless=True,
        enable_resilience=True,
        max_restarts=2,
        per_action_delay_seconds=0.1
    )
    engine = BrowserEngine(config=config)
    
    session_id = "resilience_test_session"
    execution_id = "resilience_test_exec"
    
    try:
        # 2. Start Session
        print("Starting session...")
        session = await engine.start_session(session_id, execution_id)
        
        # 3. Action 1: Normal execution
        print("Executing normal action...")
        action1 = SafeAction(
            action_id="act1",
            action_type=SafeActionType.NAVIGATE,
            target="about:blank",
            parameters={},
            description="Nav 1"
        )
        res1 = await engine.execute_action(session_id, action1)
        assert res1["success"]
        print("Action 1 success.")
        
        # 4. SIMULATE ERROR (CRASH)
        # We assume _classify_error maps 'Target closed' or similar to BrowserCrashError
        # Closing the browser or context directly simulates this.
        print("Simulating crash (closing browser)...")
        await session.browser.close()
        
        # 5. Action 2: Should trigger recovery
        print("Executing post-crash action (expecting recovery)...")
        action2 = SafeAction(
            action_id="act2",
            action_type=SafeActionType.NAVIGATE,
            target="about:blank",
            parameters={},
            description="Nav 2"
        )
        
        # This call should: 
        # a) Catch the error from disconnected browser
        # b) Classify as recoverable
        # c) Restart session
        # d) Retry and succeed
        res2 = await engine.execute_action(session_id, action2)
        
        assert res2["success"], "Action 2 failed after recovery"
        print("Action 2 success (Recovered).")
        
        # 6. Verify State
        session_after = engine._get_session(session_id)
        assert session_after.failure_count == 1, f"Failure count mismatch: {session_after.failure_count}"
        assert session_after.browser.is_connected(), "Browser should be connected after restart"
        print("State verification passed.")
        
        # 7. Stop Session and Check Evidence
        summary = await engine.stop_session(session_id)
        assert summary["failure_count"] == 1
        print("Evidence summary verified.")
        
    finally:
        await engine.cleanup()

if __name__ == "__main__":
    import sys
    # Use existing loop if running as script
    try:
        asyncio.run(test_browser_resilience_recovery())
    except KeyboardInterrupt:
        pass
