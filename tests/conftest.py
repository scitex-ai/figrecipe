"""Root conftest for figrecipe tests.

Two responsibilities:

1. Headless matplotlib + figure cleanup (existing).
2. Subprocess coverage wiring — subprocess coverage is configured in
   pyproject.toml via coverage.py's subprocess patch; test collection must
   not install .pth files or overwrite caller-owned coverage environment
   variables.
"""

from __future__ import annotations

import gc
import sys  # noqa: F401  (kept for downstream test usage)
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pytest
from scitex_dev.testing import make_pytest_configure

# ---------------------------------------------------------------------------
# Import-vantage guard — refuse to grade a tree we are not importing.
# ---------------------------------------------------------------------------
#
# The implementation lives in scitex-dev, not here. figrecipe carried a local
# copy from #362 only because the trap bit twice on 2026-08-18 and waiting for
# the shared version meant running unprotected in the meantime; that commit said
# it should collapse to a one-line call, and this is that collapse.
#
# Keeping both would have been the joke version of this fix: forking a helper
# whose entire purpose is to stop fifteen repos each writing their own.
#
# WHAT IT DOES, so nobody has to go read scitex-dev to know why a run refused:
# if `figrecipe` resolves outside this checkout, the session raises instead of
# running. A green is a claim about the code that produced it, and a suite
# importing site-packages while you are testing a worktree cannot make that
# claim — it reports a number about somewhere else, well-formed and confident,
# with nothing in the output to say so.
#
# Set SCITEX_ALLOW_FOREIGN_IMPORT=1 to test a deliberately installed build; it
# prints loudly when used.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
pytest_configure = make_pytest_configure("figrecipe", _PROJECT_ROOT)


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
