"""Root conftest for figrecipe tests.

Two responsibilities:

1. Headless matplotlib + figure cleanup (existing).
2. Subprocess coverage wiring — force-set COVERAGE_PROCESS_START and
   COVERAGE_FILE at module-import time, and drop an idempotent `.pth`
   shim in site-packages so child Python interpreters (subprocess.run,
   jupyter nbconvert --execute, pytest-xdist workers) start coverage
   tracing on their own. `os.environ.setdefault` would be a no-op here
   because pytest-cov sets COVERAGE_FILE to a tmp dir before conftest
   loads.
"""

from __future__ import annotations

import gc
import os
import sys  # noqa: F401  (kept for downstream test usage)
import sysconfig
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pytest

# ---------------------------------------------------------------------------
# Subprocess coverage wiring (module-import time — must run before tests).
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Pin coverage's data file at the repo root and point process_startup at our
# pyproject so child interpreters configure themselves correctly.
os.environ["COVERAGE_PROCESS_START"] = str(_PROJECT_ROOT / "pyproject.toml")
os.environ["COVERAGE_FILE"] = str(_PROJECT_ROOT / ".coverage")


def _ensure_subprocess_coverage_shim() -> None:
    """Drop an idempotent `.pth` file in site-packages that auto-starts
    coverage in every child Python interpreter via
    `coverage.process_startup()`.
    """
    purelib = Path(sysconfig.get_paths()["purelib"])
    pth = purelib / "_figrecipe_subprocess_coverage.pth"
    shim = (
        "import os, coverage\n"
        "if os.environ.get('COVERAGE_PROCESS_START'):\n"
        "    coverage.process_startup()\n"
    )
    try:
        if not pth.exists() or pth.read_text() != shim:
            pth.write_text(shim)
    except OSError:
        # site-packages may be read-only (e.g. system Python); silently
        # skip — local dev venvs are writable and that's where this matters.
        pass


_ensure_subprocess_coverage_shim()

# ---------------------------------------------------------------------------
# Headless matplotlib + per-test figure cleanup.
# ---------------------------------------------------------------------------

matplotlib.use("Agg")


@pytest.fixture(autouse=True)
def _close_figures():
    """Close all matplotlib figures after each test to prevent memory leaks."""
    yield
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        fig.clear()
        plt.close(fig)
    plt.close("all")
    gc.collect()
