"""Skip the whole ``_need_check_from_scitex_dot__dev`` subtree when
``scitex_dev.plt`` is unavailable.

The submodule was renamed/removed upstream; these tests were imported
verbatim under ``_need_check_*`` (literally "need check") for later
porting. They MUST NOT break collection of the rest of the suite —
notably they break the pre-commit ``pytest-testmon`` hook with
``ModuleNotFoundError: scitex_dev.plt`` before any real test runs.

When ``scitex_dev.plt`` is absent, the plt-gated modules below are
excluded from collection (``collect_ignore`` /
``pytest_ignore_collect``) and the remaining guard placeholder reports
the directory as skipped, so ``pytest`` on this directory exits 0
instead of erroring (exit 2) or reporting "no tests ran" (exit 5).
When ``scitex_dev.plt`` is present again, nothing is ignored and the
smoke tests run normally.

Once these tests are ported to the current scitex_dev API, this
conftest can be removed.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).parent
_MISSING = importlib.util.find_spec("scitex_dev.plt") is None

# Test modules that import scitex_dev.plt at module import time. The guard
# placeholder (test_umbrella_staging_guard.py) is deliberately NOT listed
# so the directory still reports a skip instead of "no tests ran".
_PLT_GATED: tuple[str, ...] = (
    "test_plot_mpl_bar.py",
    "demo_plotters/test_plot_mpl_bar.py",
)

collect_ignore: list[str] = []
collect_ignore_glob: list[str] = []

if _MISSING:
    # collect_ignore is relative to this conftest's directory. Cover the
    # known-broken modules directly (top-level) and nested via glob.
    # NOTE: pytest does not consult collect_ignore for paths passed
    # explicitly on the command line, so pytest_ignore_collect below
    # (directory runs) plus importorskip guards in the test modules
    # (explicit file runs) cover the remaining cases.
    collect_ignore = ["test_plot_mpl_bar.py"]
    collect_ignore_glob = ["demo_plotters/test_*.py"]


def pytest_ignore_collect(collection_path, config):
    """Collection-ignore plt-gated modules when scitex_dev.plt is absent.

    Covers directory-level collection (parent-dir runs, testmon) including
    nested paths that collect_ignore_glob can miss. Explicitly-passed file
    paths bypass this hook as well, so the test modules additionally guard
    their hard imports with pytest.importorskip.
    """
    if not _MISSING:
        return None
    try:
        rel = Path(str(collection_path)).relative_to(_HERE)
    except ValueError:
        return None
    rel_posix = rel.as_posix()
    if rel_posix in _PLT_GATED or rel_posix.startswith("demo_plotters/"):
        # Never ignore the guard placeholder itself: it is what turns an
        # empty (exit 5) run into a clean skip (exit 0).
        if rel_posix == "demo_plotters/test_umbrella_staging_guard.py":
            return None
        return True
    return None
