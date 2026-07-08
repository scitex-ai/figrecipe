"""Tests for STX-FM016 raw-matplotlib-bypass AST rule.

Real ast.parse + RawMplBypassChecker — no mocks. Each test follows
Arrange / Act / Assert with one assertion and a >=3-word behavioural name.

The checker imports scitex_dev.linter.checker symbols lazily inside
``_emit()``, so the module importorskips when scitex_dev isn't installable.
"""

from __future__ import annotations

import ast

import pytest

pytest.importorskip("scitex_dev.linter.checker")
pytest.importorskip("scitex_dev.linter.config")

from figrecipe._quality._linter_plugin import get_plugin  # noqa: E402

_PLUGIN = get_plugin()
_FM016 = next(r for r in _PLUGIN["rules"] if r.id == "STX-FM016")


def _make_config():
    from scitex_dev.linter.config import load_config

    return load_config(start_path=__file__)


def _run(src: str):
    """Parse *src* and run the RawMplBypassChecker; return issues."""
    from figrecipe._quality._linter_checkers import _make_raw_mpl_bypass_checker

    tree = ast.parse(src)
    source_lines = src.splitlines()
    cls = _make_raw_mpl_bypass_checker(_FM016)
    checker = cls(source_lines, _make_config())
    checker.visit(tree)
    return checker.issues


def _fired(issues):
    return any(i.rule.id == "STX-FM016" for i in issues)


# ---------------------------------------------------------------------------
# Fires on raw pyplot figure creation
# ---------------------------------------------------------------------------


def test_fm016_flags_plt_subplots():
    # Arrange
    src = "import matplotlib.pyplot as plt\nfig, ax = plt.subplots()\n"
    # Act
    issues = _run(src)
    # Assert
    assert _fired(issues)


def test_fm016_flags_plt_figure():
    # Arrange
    src = "import matplotlib.pyplot as plt\nfig = plt.figure()\n"
    # Act
    issues = _run(src)
    # Assert
    assert _fired(issues)


def test_fm016_flags_dotted_matplotlib_pyplot_subplots():
    # Arrange
    src = "import matplotlib.pyplot\nfig, ax = matplotlib.pyplot.subplots()\n"
    # Act
    issues = _run(src)
    # Assert
    assert _fired(issues)


def test_fm016_flags_from_matplotlib_import_pyplot():
    # Arrange
    src = "from matplotlib import pyplot\nfig, ax = pyplot.subplots()\n"
    # Act
    issues = _run(src)
    # Assert
    assert _fired(issues)


def test_fm016_flags_bare_subplots_imported_from_pyplot():
    # Arrange
    src = "from matplotlib.pyplot import subplots\nfig, ax = subplots()\n"
    # Act
    issues = _run(src)
    # Assert
    assert _fired(issues)


# ---------------------------------------------------------------------------
# Does not fire on the tracked figrecipe / scitex equivalents
# ---------------------------------------------------------------------------


def test_fm016_ignores_fr_subplots():
    # Arrange
    src = "import figrecipe as fr\nfig, ax = fr.subplots()\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)


def test_fm016_ignores_stx_plt_subplots():
    # Arrange
    src = "import scitex as stx\nfig, ax = stx.plt.subplots()\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)


def test_fm016_ignores_subplots_bound_to_figrecipe():
    # Arrange -- `plt` rebound to figrecipe is NOT raw pyplot.
    src = "import figrecipe as plt\nfig, ax = plt.subplots()\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)


# ---------------------------------------------------------------------------
# Escape hatch
# ---------------------------------------------------------------------------


def test_fm016_respects_stx_allow_comment():
    # Arrange
    src = (
        "import matplotlib.pyplot as plt\n"
        "fig, ax = plt.subplots()  # stx-allow: STX-FM016\n"
    )
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)
