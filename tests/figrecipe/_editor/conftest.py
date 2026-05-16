#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared fixtures for editor browser tests."""

import subprocess
import sys
import time
from pathlib import Path
from typing import Generator

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def check_playwright_available() -> bool:
    """Check if playwright and its browser binaries are available."""
    import importlib.util

    if importlib.util.find_spec("playwright") is None:
        return False
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            path = p.chromium.executable_path
            return Path(path).exists()
    except Exception:
        return False


requires_playwright = pytest.mark.skipif(
    not check_playwright_available(),
    reason="Playwright or Chromium browser not available",
)


def find_free_port() -> int:
    """Find a free port to use for the editor server."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class EditorServer:
    """Context manager for running the editor server in background."""

    def __init__(self, recipe_path: Path, port: int = 5051):
        self.recipe_path = recipe_path
        self.port = port
        self.process = None
        self.url = f"http://127.0.0.1:{port}"
        from urllib.parse import quote

        self._recipe_param = f"recipe={quote(str(recipe_path))}"
        self.recipe_url = f"{self.url}?{self._recipe_param}"

    def api(self, endpoint: str) -> str:
        """Build API URL with recipe query param."""
        sep = "&" if "?" in endpoint else "?"
        return f"{self.url}/{endpoint}{sep}{self._recipe_param}"

    def __enter__(self):
        """Start the editor server."""
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                f"""
import sys
sys.path.insert(0, 'src')
import figrecipe as fr
fr.gui('{self.recipe_path}', port={self.port}, open_browser=False)
""",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Allow time for server + matplotlib initialization
        max_wait = 30
        poll_interval = 0.5
        start_time = time.time()

        while time.time() - start_time < max_wait:
            # Check if process died
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                raise RuntimeError(
                    f"Editor server process exited prematurely.\n"
                    f"stderr: {stderr.decode()[:500]}"
                )

            try:
                import urllib.request

                urllib.request.urlopen(self.url, timeout=2)
                break
            except Exception:
                time.sleep(poll_interval)
        else:
            self.process.terminate()
            stdout, stderr = self.process.communicate(timeout=2)
            raise RuntimeError(
                f"Editor server failed to start on port {self.port} "
                f"after {max_wait}s.\nstderr: {stderr.decode()[:500]}"
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the editor server."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)


@pytest.fixture
def sample_recipe(tmp_path) -> Path:
    """Create a sample recipe for testing."""
    import figrecipe as fr

    rng = np.random.default_rng(42)

    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9], id="line1", label="Quadratic")
    ax.scatter(rng.random(10), rng.random(10), id="scatter1", label="Random")
    ax.set_xlabel("X Label")
    ax.set_ylabel("Y Label")
    ax.set_title("Test Figure")
    ax.legend()

    recipe_path = tmp_path / "test_recipe.yaml"
    fr.save(fig, recipe_path)
    plt.close(fig.fig)

    return recipe_path


@pytest.fixture
def editor_server(sample_recipe) -> Generator[EditorServer, None, None]:
    """Start editor server for testing."""
    port = find_free_port()
    with EditorServer(sample_recipe, port=port) as server:
        yield server
