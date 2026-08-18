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


# ---------------------------------------------------------------------------
# Import-vantage guard — refuse to grade a tree we are not importing.
# ---------------------------------------------------------------------------
#
# MEASURED FOUR TIMES IN ONE DAY, 2026-08-18, three of them by people who
# already knew about the trap:
#
#   * `audit-all` resolved its sub-auditors from PATH, so a 0.53.0 entry point
#     ran 0.50.0 checks and reported a clean, self-consistent result identical
#     to 0.50.0's — nearly published as "the version made no difference".
#   * `audit-cli --path <tree>` IMPORTS the CLI, so it graded site-packages
#     rather than the tree it was pointed at.
#   * scitex-dev ran their suite from a worktree and got 1049 PASSED against
#     site-packages; only three unrelated failures revealed the wrong vantage
#     point. A no-op change would have reported a clean green about code the
#     run never touched.
#   * this repo: `pytest tests/figrecipe/_cli/` from a worktree returned
#     `4 passed` while importing the INSTALLED figrecipe 0.34.6. CI, which
#     puts the checkout on the path, failed on the first run.
#
# In every case the wrong answer was WELL-FORMED, SELF-CONSISTENT and
# CONFIDENT. Nothing warned, because from inside the process there is nothing
# anomalous about importing an installed package.
#
# A green is a claim about the code that produced it. If `figrecipe` resolves
# outside this checkout, the suite cannot make that claim, so it refuses to run
# rather than produce a number about somewhere else. Knowing about this class
# demonstrably does not prevent it — hence a mechanical check rather than a
# note in a contributing guide.
#
# Set FIGRECIPE_ALLOW_FOREIGN_IMPORT=1 to test a deliberately installed build
# (verifying a wheel, say). The opt-out is loud in the log for the same reason
# the check exists.
def _assert_tests_import_the_tree_under_test() -> None:
    import figrecipe

    imported_from = Path(figrecipe.__file__).resolve()
    if _PROJECT_ROOT in imported_from.parents:
        return
    if os.environ.get("FIGRECIPE_ALLOW_FOREIGN_IMPORT"):
        print(
            f"\nfigrecipe imported from {imported_from}, OUTSIDE {_PROJECT_ROOT} "
            f"— allowed by FIGRECIPE_ALLOW_FOREIGN_IMPORT. This run does NOT "
            f"grade the working tree.\n"
        )
        return
    raise RuntimeError(
        "tests would grade a DIFFERENT figrecipe than this checkout.\n"
        f"  tree under test : {_PROJECT_ROOT}\n"
        f"  figrecipe found : {imported_from}\n"
        "A pass here would describe code your change never touched.\n"
        "Fix, in order of preference:\n"
        f"  1. pip install -e {_PROJECT_ROOT}\n"
        f"  2. PYTHONPATH={_PROJECT_ROOT / 'src'} pytest ...\n"
        "  3. FIGRECIPE_ALLOW_FOREIGN_IMPORT=1 — only when testing an "
        "installed build ON PURPOSE."
    )


_assert_tests_import_the_tree_under_test()


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
