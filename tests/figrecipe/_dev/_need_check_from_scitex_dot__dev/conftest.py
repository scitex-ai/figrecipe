"""Skip the whole ``_need_check_from_scitex_dot__dev`` subtree when
``scitex_dev.plt`` is unavailable.

The submodule was renamed/removed upstream; these tests were imported
verbatim under ``_need_check_*`` (literally "need check") for later
porting. They MUST NOT break collection of the rest of the suite —
notably they break the pre-commit ``pytest-testmon`` hook with
``ModuleNotFoundError: scitex_dev.plt`` before any real test runs.

Once these tests are ported to the current scitex_dev API, this
conftest can be removed.
"""

from __future__ import annotations

import importlib.util

collect_ignore: list[str] = []
collect_ignore_glob: list[str] = []

if importlib.util.find_spec("scitex_dev.plt") is None:
    # collect_ignore is relative to this conftest's directory. Cover the
    # known-broken modules directly (top-level) and nested via glob.
    collect_ignore = ["test_plot_mpl_bar.py"]
    collect_ignore_glob = ["demo_plotters/test_*.py"]
