"""
Adversarial Security Tests for Phase-4 Execution Layer

Tests for JavaScript injection prevention and input validation.
These tests verify that the security fixes are effective.

SECURITY TESTS:
- JS injection via scroll amount parameter
- Non-numeric input rejection
- Parameterized evaluation enforcement
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from execution_layer.browser import BrowserEngine, BrowserConfig, BrowserSession
from execution_layer.types import SafeAction, SafeActionType
from execution_layer.errors import BrowserSessionError


class TestJSInjectionPrevention:
    """Tests for JavaScript injection prevention in BrowserEngine."""
    
    @pytest.mark.asyncio
    async def test_scroll_rejects_string_injection_attempt(self) -> None:
        """
        Scroll action MUST reject string injection attempts.
        
        ADVERSARIAL: Attacker tries to inject JS via amount parameter.
        EXPECTED: BrowserSessionError raised, no JS executed.
        """
        engine = BrowserEngine()
        
        # Mock session
        mock_page = AsyncMock()
        mock_session = MagicMock(spec=BrowserSession)
        mock_session.page = mock_page
        engine._active_sessions["test-session"] = mock_session
        
        # Adversarial payload: JS injection via amount
        malicious_action = SafeAction(
            action_id="adv-001",
            action_type=SafeActionType.SCROLL,
            target="body",
            parameters={
                "direction": "down",
                "amount": "100); alert('XSS'); window.scrollBy(0, 0",  # JS injection
            },
            description="Adversarial scroll test",
        )
        
        with pytest.raises(BrowserSessionError) as exc_info:
            await engine.execute_action("test-session", malicious_action)
        
        assert "must be numeric" in str(exc_info.value)
        # Verify page.evaluate was NOT called with malicious payload
        mock_page.evaluate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_scroll_rejects_dict_injection_attempt(self) -> None:
        """
        Scroll action MUST reject dict injection attempts.
        
        ADVERSARIAL: Attacker tries to inject via dict amount.
        EXPECTED: BrowserSessionError raised.
        """
        engine = BrowserEngine()
        
        mock_page = AsyncMock()
        mock_session = MagicMock(spec=BrowserSession)
        mock_session.page = mock_page
        engine._active_sessions["test-session"] = mock_session
        
        malicious_action = SafeAction(
            action_id="adv-002",
            action_type=SafeActionType.SCROLL,
            target="body",
            parameters={
                "direction": "down",
                "amount": {"__proto__": "polluted"},  # Prototype pollution attempt
            },
            description="Adversarial scroll test",
        )
        
        with pytest.raises(BrowserSessionError) as exc_info:
            await engine.execute_action("test-session", malicious_action)
        
        assert "must be numeric" in str(exc_info.value)
        mock_page.evaluate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_scroll_rejects_list_injection_attempt(self) -> None:
        """
        Scroll action MUST reject list injection attempts.
        
        ADVERSARIAL: Attacker tries to inject via list amount.
        EXPECTED: BrowserSessionError raised.
        """
        engine = BrowserEngine()
        
        mock_page = AsyncMock()
        mock_session = MagicMock(spec=BrowserSession)
        mock_session.page = mock_page
        engine._active_sessions["test-session"] = mock_session
        
        malicious_action = SafeAction(
            action_id="adv-003",
            action_type=SafeActionType.SCROLL,
            target="body",
            parameters={
                "direction": "down",
                "amount": [100, "alert('XSS')"],  # List injection attempt
            },
            description="Adversarial scroll test",
        )
        
        with pytest.raises(BrowserSessionError) as exc_info:
            await engine.execute_action("test-session", malicious_action)
        
        assert "must be numeric" in str(exc_info.value)
        mock_page.evaluate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_scroll_rejects_none_amount(self) -> None:
        """
        Scroll action MUST reject None amount.
        
        ADVERSARIAL: Attacker tries to pass None.
        EXPECTED: BrowserSessionError raised.
        """
        engine = BrowserEngine()
        
        mock_page = AsyncMock()
        mock_session = MagicMock(spec=BrowserSession)
        mock_session.page = mock_page
        engine._active_sessions["test-session"] = mock_session
        
        malicious_action = SafeAction(
            action_id="adv-004",
            action_type=SafeActionType.SCROLL,
            target="body",
            parameters={
                "direction": "down",
                "amount": None,
            },
            description="Adversarial scroll test",
        )
        
        with pytest.raises(BrowserSessionError) as exc_info:
            await engine.execute_action("test-session", malicious_action)
        
        assert "must be numeric" in str(exc_info.value)
        mock_page.evaluate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_scroll_accepts_valid_integer(self) -> None:
        """
        Scroll action MUST accept valid integer amount.
        
        EXPECTED: Parameterized evaluation called with integer.
        """
        engine = BrowserEngine(BrowserConfig(per_action_delay_seconds=0))
        
        mock_page = AsyncMock()
        mock_session = MagicMock(spec=BrowserSession)
        mock_session.page = mock_page
        engine._active_sessions["test-session"] = mock_session
        
        valid_action = SafeAction(
            action_id="valid-001",
            action_type=SafeActionType.SCROLL,
            target="body",
            parameters={
                "direction": "down",
                "amount": 300,
            },
            description="Valid scroll test",
        )
        
        result = await engine.execute_action("test-session", valid_action)
        
        assert result["success"] is True
        assert result["scrolled"] is True
        # Verify parameterized call (not f-string)
        mock_page.evaluate.assert_called_once()
        call_args = mock_page.evaluate.call_args
        # First arg should be the function string, second should be the amount
        assert "(amount) => window.scrollBy(0, amount)" in call_args[0][0]
        assert call_args[0][1] == 300
    
    @pytest.mark.asyncio
    async def test_scroll_accepts_string_integer(self) -> None:
        """
        Scroll action MUST accept string that parses to integer.
        
        EXPECTED: String "300" is cast to int 300.
        """
        engine = BrowserEngine(BrowserConfig(per_action_delay_seconds=0))
        
        mock_page = AsyncMock()
        mock_session = MagicMock(spec=BrowserSession)
        mock_session.page = mock_page
        engine._active_sessions["test-session"] = mock_session
        
        valid_action = SafeAction(
            action_id="valid-002",
            action_type=SafeActionType.SCROLL,
            target="body",
            parameters={
                "direction": "down",
                "amount": "300",  # String that parses to int
            },
            description="Valid scroll test",
        )
        
        result = await engine.execute_action("test-session", valid_action)
        
        assert result["success"] is True
        assert result["scrolled"] is True
        # Verify the amount was cast to int
        call_args = mock_page.evaluate.call_args
        assert call_args[0][1] == 300  # Should be int, not string
    
    @pytest.mark.asyncio
    async def test_scroll_up_uses_parameterized_evaluation(self) -> None:
        """
        Scroll up action MUST use parameterized evaluation.
        
        EXPECTED: Parameterized call with negative scroll.
        """
        engine = BrowserEngine(BrowserConfig(per_action_delay_seconds=0))
        
        mock_page = AsyncMock()
        mock_session = MagicMock(spec=BrowserSession)
        mock_session.page = mock_page
        engine._active_sessions["test-session"] = mock_session
        
        valid_action = SafeAction(
            action_id="valid-003",
            action_type=SafeActionType.SCROLL,
            target="body",
            parameters={
                "direction": "up",
                "amount": 200,
            },
            description="Valid scroll up test",
        )
        
        result = await engine.execute_action("test-session", valid_action)
        
        assert result["success"] is True
        # Verify parameterized call for scroll up
        call_args = mock_page.evaluate.call_args
        assert "(amount) => window.scrollBy(0, -amount)" in call_args[0][0]
        assert call_args[0][1] == 200


class TestScrollInputValidation:
    """Property-based tests for scroll input validation."""
    
    @pytest.mark.asyncio
    async def test_scroll_rejects_float_string(self) -> None:
        """Float strings should be rejected (not truncated)."""
        engine = BrowserEngine()
        
        mock_page = AsyncMock()
        mock_session = MagicMock(spec=BrowserSession)
        mock_session.page = mock_page
        engine._active_sessions["test-session"] = mock_session
        
        action = SafeAction(
            action_id="float-001",
            action_type=SafeActionType.SCROLL,
            target="body",
            parameters={"direction": "down", "amount": "100.5"},
            description="Float string test",
        )
        
        with pytest.raises(BrowserSessionError) as exc_info:
            await engine.execute_action("test-session", action)
        
        assert "must be numeric" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_scroll_rejects_negative_string_with_injection(self) -> None:
        """Negative string with injection should be rejected."""
        engine = BrowserEngine()
        
        mock_page = AsyncMock()
        mock_session = MagicMock(spec=BrowserSession)
        mock_session.page = mock_page
        engine._active_sessions["test-session"] = mock_session
        
        action = SafeAction(
            action_id="neg-001",
            action_type=SafeActionType.SCROLL,
            target="body",
            parameters={"direction": "down", "amount": "-100; alert(1)"},
            description="Negative injection test",
        )
        
        with pytest.raises(BrowserSessionError) as exc_info:
            await engine.execute_action("test-session", action)
        
        assert "must be numeric" in str(exc_info.value)
