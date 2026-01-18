"""
Execution Layer Anti-Detection Awareness

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This module detects automation blocking signals but does NOT attempt
to evade detection. When detection is triggered, execution STOPS
and alerts the human.

FORBIDDEN:
- Stealth plugins
- Fingerprint spoofing
- CAPTCHA bypass
- Authentication automation

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import logging

from execution_layer.errors import AutomationDetectedError


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AutomationDetectionSignal:
    """Detected automation blocking signal.
    
    OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
    """
    signal_type: str  # webdriver | fingerprint | captcha | rate_limit
    details: str
    detected_at: datetime
    url: str


class AntiDetectionObserver:
    """Observe automation detection signals (NO EVASION).
    
    OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
    
    FORBIDDEN:
    - Stealth plugins
    - Fingerprint spoofing
    - CAPTCHA bypass
    - Authentication automation
    """
    
    # Detection signals to check (OBSERVE ONLY)
    DETECTION_SIGNALS = [
        "navigator.webdriver",
        "window.chrome",
        "navigator.plugins",
        "navigator.languages",
    ]
    
    # CAPTCHA indicators (OBSERVE ONLY, NO BYPASS)
    CAPTCHA_INDICATORS = [
        "recaptcha",
        "hcaptcha",
        "captcha",
        "challenge",
        "verify you are human",
        "i'm not a robot",
    ]
    
    def __init__(self) -> None:
        self._signals: list[AutomationDetectionSignal] = []
    
    async def check_detection_signals(self, page) -> list[AutomationDetectionSignal]:
        """Check for automation detection signals.
        
        OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
        
        Returns:
            List of detected signals (empty if none)
        """
        signals: list[AutomationDetectionSignal] = []
        url = page.url
        
        try:
            # Check navigator.webdriver (OBSERVE ONLY)
            webdriver_detected = await page.evaluate("() => navigator.webdriver")
            if webdriver_detected:
                signal = AutomationDetectionSignal(
                    signal_type="webdriver",
                    details="navigator.webdriver is true",
                    detected_at=datetime.now(timezone.utc),
                    url=url,
                )
                signals.append(signal)
                self._signals.append(signal)
                logger.warning(f"Automation detection: {signal.details} at {url}")
        except Exception as e:
            logger.debug(f"Could not check webdriver signal: {e}")
        
        return signals

    async def detect_captcha(self, page) -> Optional[AutomationDetectionSignal]:
        """Detect CAPTCHA presence (observe only, NO bypass).
        
        OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
        """
        url = page.url
        
        try:
            page_content = await page.content()
            page_content_lower = page_content.lower()
            
            for indicator in self.CAPTCHA_INDICATORS:
                if indicator in page_content_lower:
                    signal = AutomationDetectionSignal(
                        signal_type="captcha",
                        details=f"CAPTCHA indicator detected: {indicator}",
                        detected_at=datetime.now(timezone.utc),
                        url=url,
                    )
                    self._signals.append(signal)
                    logger.warning(
                        f"CAPTCHA detected at {url} — NO BYPASS ATTEMPTED. "
                        f"Human intervention required."
                    )
                    return signal
        except Exception as e:
            logger.debug(f"Could not check for CAPTCHA: {e}")
        
        return None
    
    def detect_rate_limit(
        self,
        status_code: int,
        headers: Optional[dict] = None,
        url: str = "",
    ) -> Optional[AutomationDetectionSignal]:
        """Detect rate limiting (observe only).
        
        OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
        """
        if status_code == 429:
            retry_after = None
            if headers:
                retry_after = headers.get("Retry-After")
            
            signal = AutomationDetectionSignal(
                signal_type="rate_limit",
                details=f"Rate limit (429) detected. Retry-After: {retry_after}",
                detected_at=datetime.now(timezone.utc),
                url=url,
            )
            self._signals.append(signal)
            logger.warning(f"Rate limit detected at {url} — STOP and wait")
            return signal
        
        return None

    def should_stop(self, signals: list[AutomationDetectionSignal]) -> bool:
        """Determine if execution should stop due to detection.
        
        OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
        """
        # Stop on CAPTCHA detection (NO bypass)
        for signal in signals:
            if signal.signal_type == "captcha":
                return True
            if signal.signal_type == "rate_limit":
                return True
        
        return False
    
    def get_signals(self) -> list[AutomationDetectionSignal]:
        """Get all detected signals for audit."""
        return list(self._signals)
    
    def clear_signals(self) -> None:
        """Clear signal history."""
        self._signals.clear()
    
    def raise_if_should_stop(self, signals: list[AutomationDetectionSignal]) -> None:
        """Raise AutomationDetectedError if should stop.
        
        OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
        
        Raises:
            AutomationDetectedError: If detection triggers STOP
        """
        if self.should_stop(signals):
            signal_details = "; ".join(
                f"{s.signal_type}: {s.details}" for s in signals
            )
            raise AutomationDetectedError(
                f"Automation detection triggered — STOP and alert human. "
                f"Signals: {signal_details}. "
                f"NO STEALTH, NO EVASION, NO BYPASS."
            )
