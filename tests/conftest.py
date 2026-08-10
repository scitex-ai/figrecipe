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


def _ensure_subprocess_coverage_shim(purelib: Path | None = None) -> Path | None:
    """Drop an idempotent `.pth` file in site-packages that auto-starts
    coverage in every child Python interpreter via
    `coverage.process_startup()`.

    `purelib` is overridable (tests pass a writable `tmp_path`) because the
    real venv site-packages is read-only in some CI environments (e.g. a
    layered/squashfs SIF image) — asserting against that path directly is
    not hermetic. Returns the `.pth` path written, or None if the write was
    skipped (read-only site-packages).
    """
    purelib = purelib if purelib is not None else Path(sysconfig.get_paths()["purelib"])
    pth = purelib / "_figrecipe_subprocess_coverage.pth"
    # `coverage` is imported ONLY inside the conditional: this .pth line runs
    # on every interpreter start in the venv (not just test runs), and an
    # unconditional top-level `import coverage` breaks any invocation where
    # coverage isn't installed (e.g. `figrecipe --help` in a plain user venv)
    # with a ModuleNotFoundError printed by site.py on every single command.
    shim = (
        "import os\n"
        "if os.environ.get('COVERAGE_PROCESS_START'):\n"
        "    import coverage\n"
        "    coverage.process_startup()\n"
    )
    try:
        if not pth.exists() or pth.read_text() != shim:
            pth.write_text(shim)
    except OSError:
        # site-packages may be read-only (e.g. system Python, or a
        # layered/squashfs CI image); silently skip — local dev venvs are
        # writable and that's where this matters.
        return None
    return pth


_ensure_subprocess_coverage_shim()

# ---------------------------------------------------------------------------
# Headless matplotlib + per-test figure cleanup.
# ---------------------------------------------------------------------------

matplotlib.use("Agg")


def _warm_matplotlib_font_cache() -> None:
    """Build matplotlib's FontManager once per (xdist worker) process at import.

    The validate-recipe tests render a figure and compare it pixel-for-pixel
    against a reference render (MSE threshold). The FIRST render in a fresh
    process triggers a lazy, expensive FontManager build (font scan + cache
    write). Under the SIF container's high xdist concurrency, multiple cold
    workers race to build/write that cache simultaneously; a worker that picks
    up a half-written cache (or falls back to a different font mid-build) ends
    up rendering with slightly different metrics than the reference, blowing the
    MSE up to ~715 and flaking ``test_validate_*`` non-deterministically.

    Forcing one trivial headless render here -- at import, before any test
    collects -- warms each worker's FontManager so every subsequent render in
    that process is metric-stable. It runs with stock rcParams (a plain
    ``plt.figure``), so it does not perturb the figrecipe/session style baseline
    that the per-test rcParams snapshot below preserves.
    """
    import warnings

    try:
        import matplotlib.pyplot as _plt

        _fig = _plt.figure()
        _fig.text(0.5, 0.5, "warm 0.9 Hz")
        _fig.canvas.draw()
        _plt.close(_fig)
    except Exception as exc:  # never let warm-up break collection
        warnings.warn(f"matplotlib font-cache warm-up failed: {exc}")


_warm_matplotlib_font_cache()


@pytest.fixture(autouse=True)
def _isolate_matplotlib_rcparams():
    """Snapshot ``matplotlib.rcParams`` before each test and restore them after.

    ``rcParams`` is global, mutable process state. Tests that apply a house
    style (e.g. ``figrecipe.apply_brand_style("scitex.plt")`` /
    ``configure_mpl``) push ``axes.spines.top``/``axes.spines.right = False``
    (and other keys) onto it and do not undo the change, so the mutation leaks
    into whatever test runs next in the same process. Under pytest-xdist each
    worker runs many modules in arbitrary order, so a leaked spine rcParam made
    the spine-mixin tests (which build a plain ``plt.subplots()`` axes and
    assume matplotlib's stock all-spines-visible default) flaky — they pass in
    isolation but fail when a style test lands first on the same worker.

    Snapshotting the *current* values (not ``rcdefaults()``) preserves the
    figrecipe/session baseline while undoing only per-test mutations, making the
    whole suite order- and xdist-independent.
    """
    snapshot = matplotlib.rcParams.copy()
    try:
        yield
    finally:
        matplotlib.rcParams.update(snapshot)


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
