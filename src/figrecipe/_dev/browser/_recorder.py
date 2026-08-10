#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DemoRecorder base class for creating demo videos.

Provides a framework for recording browser demos with:
- Video recording via Playwright (no audio)
- Cursor and click visualization
- Caption overlays
- Title screen with blur effect
- GIF conversion
"""

import asyncio
import socket
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ._caption import hide_caption, show_caption
from ._click_effect import inject_click_effect, remove_click_effect
from ._cursor import inject_cursor, remove_cursor
from ._highlight import highlight_element
from ._utils import convert_to_gif


class DemoRecorder(ABC):
    """Base class for creating demo recordings.

    Subclass this and implement the `run` method to define
    your demo actions.

    Attributes
    ----------
    title : str
        Demo title (used for captions and filenames).
    duration_target : int
        Target duration in seconds.
    url : str
        URL to navigate to (default: http://127.0.0.1:31296).
    output_dir : Path
        Directory for output files.

    Example
    -------
    ```python
    class ChangeColorDemo(DemoRecorder):
        title = "Change Element Color"
        duration_target = 8

        async def run(self, page):
            await self.caption("Click on bar chart element")
            await page.click('[data-key="bar_0"]')
            await self.wait(1)
            await self.caption("Select red color")
            await page.click('#color-select')
    ```
    """

    title: str = "Demo"
    demo_id: str = ""  # e.g., "01" for numbered output filenames
    duration_target: int = 10
    url: str = "http://127.0.0.1:31296"
    output_dir: Path = Path("examples/demo_movie/outputs")

    def __init__(
        self,
        url: Optional[str] = None,
        output_dir: Optional[Path] = None,
        headless: bool = True,
    ):
        """Initialize DemoRecorder.

        Parameters
        ----------
        url : str, optional
            Override default URL.
        output_dir : Path, optional
            Override default output directory.
        headless : bool, optional
            Run browser in headless mode (default: True).
        """
        if url:
            self.url = url
        if output_dir:
            self.output_dir = Path(output_dir)
        self.headless = headless
        self._page = None
        self._server_process = None

    @abstractmethod
    async def run(self, page) -> None:
        """Define demo actions.

        Override this method to define the demo sequence.

        Parameters
        ----------
        page : playwright.async_api.Page
            Playwright page object.
        """
        pass

    def _is_port_open(self, host: str, port: int) -> bool:
        """Check if port is open."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0

    def _start_server(self) -> None:
        """Start figrecipe edit server if not running."""
        from urllib.parse import urlparse

        parsed = urlparse(self.url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 5050

        if self._is_port_open(host, port):
            return

        self._server_process = subprocess.Popen(
            ["figrecipe", "gui", "--no-browser", "--port", str(port), "--host", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(30):
            time.sleep(0.5)
            if self._is_port_open(host, port):
                return

        raise RuntimeError(f"Server failed to start on {host}:{port}")

    def _stop_server(self) -> None:
        """Stop server if started by this instance."""
        if self._server_process:
            self._server_process.terminate()
            self._server_process.wait(timeout=5)
            self._server_process = None

    async def caption(self, text: str, duration: float = 2.0) -> None:
        """Show caption overlay.

        Parameters
        ----------
        text : str
            Caption text to display.
        duration : float, optional
            Duration to show caption in seconds (default: 2.0).
        """
        if self._page:
            await show_caption(self._page, text)
            if duration > 0:
                await asyncio.sleep(duration)

    async def hide_caption_now(self) -> None:
        """Hide current caption immediately."""
        if self._page:
            await hide_caption(self._page)

    async def highlight(
        self,
        selector: str,
        duration: float = 1.0,
        color: str = "#FF4444",
    ) -> None:
        """Highlight an element.

        Parameters
        ----------
        selector : str
            CSS selector for element.
        duration : float, optional
            Duration to highlight in seconds (default: 1.0).
        color : str, optional
            Highlight color (default: "#FF4444").
        """
        if self._page:
            await highlight_element(self._page, selector, int(duration * 1000), color)

    async def wait(self, seconds: float) -> None:
        """Wait for specified duration.

        Parameters
        ----------
        seconds : float
            Time to wait in seconds.
        """
        await asyncio.sleep(seconds)

    async def move_to(self, locator, duration: float = 0.5) -> bool:
        """Move cursor to an element naturally.

        Parameters
        ----------
        locator : playwright.async_api.Locator
            Playwright locator for target element.
        duration : float, optional
            Animation duration in seconds (default: 0.5).

        Returns
        -------
        bool
            True if successful.
        """
        if self._page:
            from ._cursor import move_cursor_to_element

            return await move_cursor_to_element(
                self._page, locator, int(duration * 1000)
            )
        return False

    async def title_screen(
        self,
        title: str,
        subtitle: str = "",
        timestamp: str = "",
        duration: float = 2.0,
    ) -> None:
        """Show title screen with blur overlay.

        Parameters
        ----------
        title : str
            Main title text.
        subtitle : str, optional
            Subtitle text.
        timestamp : str, optional
            Timestamp to display.
        duration : float, optional
            Duration in seconds (default: 2.0).
        """
        if self._page:
            from ._caption import show_title_screen

            await show_title_screen(
                self._page, title, subtitle, timestamp, int(duration * 1000)
            )

    async def closing_screen(self, duration: float = 2.5) -> None:
        """Show closing branding screen.

        Parameters
        ----------
        duration : float, optional
            Duration in seconds (default: 2.5).
        """
        if self._page:
            from ._caption import show_closing_screen

            await show_closing_screen(self._page, int(duration * 1000))

    def _get_output_paths(self) -> tuple:
        """Get output file paths.

        Returns
        -------
        tuple
            (mp4_path, gif_path)
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self.title.lower().replace(" ", "_").replace("-", "_")
        # Add demo_id prefix if provided (e.g., "01_enable_dark_mode")
        if self.demo_id:
            filename = f"{self.demo_id}_{safe_name}"
        else:
            filename = safe_name
        mp4_path = self.output_dir / f"{filename}.mp4"
        gif_path = self.output_dir / f"{filename}.gif"
        return mp4_path, gif_path

    def _get_version_from_pyproject(self) -> str:
        """Get version from pyproject.toml instead of installed package.

        Returns
        -------
        str
            Version string (e.g., "0.8.0").
        """
        import re

        # Find pyproject.toml by traversing up from this file
        current = Path(__file__).resolve()
        for _ in range(10):  # Max 10 levels up
            pyproject = current / "pyproject.toml"
            if pyproject.exists():
                content = pyproject.read_text()
                match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
                if match:
                    return match.group(1)
            current = current.parent
        return "0.0.0"  # Fallback

    async def _setup_page(self, page) -> None:
        """Setup page with visual effects.

        Parameters
        ----------
        page : playwright.async_api.Page
            Playwright page object.
        """
        self._page = page
        await inject_cursor(page)
        await inject_click_effect(page)

    async def _cleanup_page(self, page) -> None:
        """Cleanup visual effects from page.

        Parameters
        ----------
        page : playwright.async_api.Page
            Playwright page object.
        """
        await remove_cursor(page)
        await remove_click_effect(page)
        await hide_caption(page)
        self._page = None

    async def record(self) -> Path:
        """Record the demo and save video.

        Uses visual markers (yellow flash) to reliably detect
        content start/end for trimming, regardless of page load time.

        Returns
        -------
        Path
            Path to output MP4 file.
        """
        self._start_server()

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "Playwright not installed. Install with: pip install playwright && playwright install chromium"
            )

        from datetime import datetime

        from ._video_trim import (
            inject_end_marker,
            inject_start_marker,
            process_video_with_markers,
        )

        mp4_path, _ = self._get_output_paths()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=str(self.output_dir),
                record_video_size={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            try:
                # Navigate to URL (fresh load resets state)
                await page.goto(self.url, wait_until="networkidle")

                # Wait for preview image to load
                try:
                    await page.wait_for_selector("#preview-image", timeout=10000)
                except Exception:
                    pass  # Continue even if selector not found

                # Wait for video recording to stabilize
                # Playwright needs time to start capturing frames
                await asyncio.sleep(1.0)

                # Get version and timestamp for markers
                version = self._get_version_from_pyproject()
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                # === START MARKER === (dark frame with OCR metadata)
                # Duration 500ms = ~8 frames at 15fps for reliable detection
                await inject_start_marker(
                    page,
                    version=f"figrecipe v{version}",
                    timestamp=timestamp_str,
                    duration_ms=500,
                )
                # Brief pause after marker
                await asyncio.sleep(0.2)
                self._page = page
                await self.title_screen(
                    title=self.title,
                    subtitle=f"figrecipe v{version}",
                    timestamp=timestamp_str,
                    duration=2.0,
                )

                # Setup cursor AFTER title screen
                await self._setup_page(page)

                # Run demo actions
                await self.run(page)

                # Show closing branding screen
                await self.closing_screen(duration=2.0)
                await asyncio.sleep(0.3)

                # === END MARKER === (dark frame with OCR metadata)
                # Duration 500ms = ~5 frames at 10fps for reliable detection
                await inject_end_marker(
                    page,
                    version=f"figrecipe v{version}",
                    timestamp=timestamp_str,
                    duration_ms=500,
                )
                await asyncio.sleep(0.1)

                # Cleanup
                await self._cleanup_page(page)

            except Exception as exc:
                # PA305 — every Playwright flow must capture debug artefacts
                # (screenshot + HTML) on the fail path so selector regressions
                # are diagnosable post-mortem.
                try:
                    from scitex_browser.debugging import (
                        capture_debug_artifacts_async,
                    )

                    await capture_debug_artifacts_async(
                        page, output_dir=str(self.output_dir), context=str(exc)
                    )
                except ImportError:
                    pass
                raise
            finally:
                await context.close()
                await browser.close()

            # Get recorded video and process with marker detection
            video_path = await page.video.path()
            if video_path and Path(video_path).exists():
                webm_path = Path(video_path)
                try:
                    # Detect markers and trim automatically
                    process_video_with_markers(webm_path, mp4_path, cleanup=True)
                except Exception as e:
                    print(f"Warning: Marker-based trim failed ({e}), using fallback")
                    # Fallback: simple conversion without trim
                    import subprocess

                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            str(webm_path),
                            "-c:v",
                            "libx264",
                            "-preset",
                            "fast",
                            "-crf",
                            "23",
                            str(mp4_path),
                        ],
                        capture_output=True,
                    )
                    webm_path.unlink(missing_ok=True)

        print(f"Recorded: {mp4_path}")
        return mp4_path

    async def record_and_convert(self) -> tuple:
        """Record demo and convert to GIF.

        Returns
        -------
        tuple
            (mp4_path, gif_path)
        """
        mp4_path = await self.record()
        _, gif_path = self._get_output_paths()

        try:
            convert_to_gif(mp4_path, gif_path)
            print(f"Converted: {gif_path}")
        except Exception as e:
            print(f"GIF conversion failed: {e}")
            gif_path = None

        return mp4_path, gif_path

    def execute(self) -> tuple:
        """Execute recording (synchronous wrapper).

        Returns
        -------
        tuple
            (mp4_path, gif_path)
        """
        try:
            return asyncio.run(self.record_and_convert())
        finally:
            self._stop_server()


__all__ = ["DemoRecorder"]

# EOF
