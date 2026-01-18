"""
Browser launch boundary for the execution layer.

Production uses real Playwright. Tests inject fakes to avoid external
dependencies while preserving safety invariants.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Optional, Any, TYPE_CHECKING

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

if TYPE_CHECKING:
    from execution_layer.browser import BrowserConfig


class BrowserLauncher(Protocol):
    """Boundary for launching browsers."""

    async def launch(
        self,
        config: "BrowserConfig",
        har_path: Path,
        video_dir: Path,
        enable_video: bool,
    ) -> tuple[Browser, BrowserContext, Page]:
        ...

    async def cleanup(self) -> None:
        ...


@dataclass
class PlaywrightBrowserLauncher:
    """Real Playwright-backed browser launcher."""

    _playwright: Optional[Playwright] = None

    async def launch(
        self,
        config: "BrowserConfig",
        har_path: Path,
        video_dir: Path,
        enable_video: bool,
    ) -> tuple[Browser, BrowserContext, Page]:
        if self._playwright is None:
            self._playwright = await async_playwright().start()

        browser = await self._playwright.chromium.launch(
            headless=config.headless,
            slow_mo=config.slow_mo_ms,
        )

        context_options: dict[str, Any] = {
            "viewport": {
                "width": config.viewport_width,
                "height": config.viewport_height,
            },
            "record_har_path": str(har_path),
            "record_har_content": "embed",
        }

        if enable_video:
            video_dir.mkdir(parents=True, exist_ok=True)
            context_options["record_video_dir"] = str(video_dir)
            context_options["record_video_size"] = {
                "width": config.viewport_width,
                "height": config.viewport_height,
            }

        context = await browser.new_context(**context_options)
        page = await context.new_page()
        page.set_default_timeout(config.timeout_ms)
        return browser, context, page

    async def cleanup(self) -> None:
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


class GatedPlaywrightLauncher(PlaywrightBrowserLauncher):
    """Optional gate requiring explicit env to run real browser."""

    def __init__(self, env_flag: str = "ALLOW_REAL_BROWSER") -> None:
        super().__init__()
        self._env_flag = env_flag

    async def launch(
        self,
        config: BrowserConfig,
        har_path: Path,
        video_dir: Path,
        enable_video: bool,
    ) -> tuple[Browser, BrowserContext, Page]:
        import os

        if os.getenv(self._env_flag) != "1":
            raise RuntimeError(
                f"Real browser launch blocked: set {self._env_flag}=1 to allow Playwright"
            )
        return await super().launch(config, har_path, video_dir, enable_video)


# =============================================================================
# FAKE BROWSER LAUNCHER FOR TESTS (Category B - Environment Coupling)
# =============================================================================

class FakePage:
    """Fake Playwright Page for testing without real browser."""
    
    def __init__(self, har_path: Path, screenshots_dir: Path) -> None:
        self._har_path = har_path
        self._screenshots_dir = screenshots_dir
        self._url = "about:blank"
        self._console_handlers: list = []
    
    @property
    def url(self) -> str:
        return self._url
    
    def on(self, event: str, handler) -> None:
        if event == "console":
            self._console_handlers.append(handler)
    
    def set_default_timeout(self, timeout: int) -> None:
        pass
    
    async def goto(self, url: str, wait_until: str = "load"):
        self._url = url
        # Return a fake response
        return FakeResponse(status=200, url=url)
    
    async def click(self, selector: str) -> None:
        pass
    
    async def fill(self, selector: str, text: str) -> None:
        pass
    
    async def evaluate(self, script: str, arg: Any = None) -> Any:
        return None
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> None:
        pass
    
    async def query_selector(self, selector: str):
        return FakeElement()
    
    async def hover(self, selector: str) -> None:
        pass
    
    async def select_option(self, selector: str, value: str) -> None:
        pass
    
    async def screenshot(self, path: str) -> bytes:
        # Create a minimal PNG file
        import struct
        import zlib
        
        # Minimal 1x1 white PNG
        def create_minimal_png() -> bytes:
            signature = b'\x89PNG\r\n\x1a\n'
            
            # IHDR chunk
            ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
            ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
            
            # IDAT chunk (1x1 white pixel)
            raw_data = b'\x00\xff\xff\xff'
            compressed = zlib.compress(raw_data)
            idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
            idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
            
            # IEND chunk
            iend_crc = zlib.crc32(b'IEND') & 0xffffffff
            iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
            
            return signature + ihdr + idat + iend
        
        png_data = create_minimal_png()
        Path(path).write_bytes(png_data)
        return png_data


class FakeResponse:
    """Fake Playwright Response."""
    
    def __init__(self, status: int, url: str) -> None:
        self.status = status
        self.url = url


class FakeElement:
    """Fake Playwright Element."""
    
    async def text_content(self) -> str:
        return "fake text"
    
    async def get_attribute(self, name: str) -> Optional[str]:
        return "fake-attribute"


class FakeContext:
    """Fake Playwright BrowserContext."""
    
    def __init__(self, page: FakePage) -> None:
        self._page = page
        self._closed = False
    
    async def new_page(self) -> FakePage:
        return self._page
    
    async def close(self) -> None:
        self._closed = True


class FakeBrowser:
    """Fake Playwright Browser."""
    
    def __init__(self, context: FakeContext) -> None:
        self._context = context
        self._closed = False
    
    async def new_context(self, **kwargs) -> FakeContext:
        return self._context
    
    async def close(self) -> None:
        self._closed = True


class FakeBrowserLauncher:
    """Fake browser launcher for testing without real Playwright.
    
    This launcher creates fake browser/context/page objects that:
    - Satisfy the BrowserLauncher protocol
    - Create real files on disk for evidence (HAR, screenshots)
    - Do NOT require Playwright or a real browser
    
    Use this in tests to avoid Category B (environment coupling) failures.
    """
    
    def __init__(self) -> None:
        self._launched = False
    
    async def launch(
        self,
        config: "BrowserConfig",
        har_path: Path,
        video_dir: Path,
        enable_video: bool,
    ) -> tuple[Any, Any, Any]:  # Returns fake Browser, Context, Page
        self._launched = True
        
        # Create directories
        har_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a minimal valid HAR file
        import json
        har_content = {
            "log": {
                "version": "1.2",
                "creator": {"name": "FakeBrowserLauncher", "version": "1.0"},
                "entries": []
            }
        }
        har_path.write_text(json.dumps(har_content))
        
        screenshots_dir = har_path.parent.parent / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        page = FakePage(har_path, screenshots_dir)
        context = FakeContext(page)
        browser = FakeBrowser(context)
        
        return browser, context, page
    
    async def cleanup(self) -> None:
        self._launched = False
