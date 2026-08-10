"""Tests for STX-FM018 heatmap-without-colorbar AST rule.

Real ast.parse + HeatmapColorbarChecker — no mocks. Each test follows
Arrange / Act / Assert with one assertion and a >=3-word behavioural name.
"""

from __future__ import annotations

import ast

import pytest

# Skip the whole module gracefully if scitex_dev isn't importable in this
# environment — the checker itself is import-guarded the same way.
pytest.importorskip("scitex_dev.linter.checker")

from figrecipe._quality._heatmap_colorbar_checker import (  # noqa: E402
    HeatmapColorbarChecker,
)
from figrecipe._quality._linter_plugin import get_plugin  # noqa: E402

# Locate the FM018 rule object once via the plugin registration. Tests
# instantiate the checker directly with this rule, mirroring the wiring
# in _linter_plugin.py.
_PLUGIN = get_plugin()
_FM018 = next(r for r in _PLUGIN["rules"] if r.id == "STX-FM018")


def _make_config():
    """Real linter config; no mocks. The checker reads .disable and
    .per_rule_severity, both of which exist on the dataclass default.
    """
    from scitex_dev.linter.config import load_config

    return load_config(start_path=__file__)


def _run(src: str):
    """Parse *src* and run HeatmapColorbarChecker; return collected issues."""
    tree = ast.parse(src)
    source_lines = src.splitlines()
    checker = HeatmapColorbarChecker(source_lines, _make_config(), rule=_FM018)
    checker.visit(tree)
    # _finalize_scope runs on Module exit inside visit_Module; call it
    # explicitly too so top-level (non-function) imshow calls are covered
    # regardless of how the AST was dispatched. Dedup by line to be safe.
    checker._finalize_scope()
    seen = set()
    unique = []
    for issue in checker.issues:
        key = (issue.line, issue.col, issue.rule.id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique


def _fired(issues):
    return any(i.rule.id == "STX-FM018" for i in issues)


# ---------------------------------------------------------------------------
# POSITIVE — fires
# ---------------------------------------------------------------------------


def test_warns_on_imshow_with_no_colorbar_in_function():
    # Arrange
    src = "def f(ax, data):\n    ax.imshow(data)\n"

    # Act
    issues = _run(src)

    # Assert
    assert _fired(issues)


def test_warns_on_imshow_at_module_scope_with_no_colorbar():
    # Arrange
    src = "import matplotlib.pyplot as plt\nfig, ax = plt.subplots()\nax.imshow(data)\n"

    # Act
    issues = _run(src)

    # Assert
    assert _fired(issues)


# ---------------------------------------------------------------------------
# NEGATIVE — does not fire
# ---------------------------------------------------------------------------


def test_does_not_warn_when_fig_colorbar_follows_imshow():
    # Arrange
    src = (
        "def f(ax, fig, data):\n"
        "    im = ax.imshow(data)\n"
        "    fig.colorbar(im, ax=ax, label='amplitude [a.u.]')\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert not _fired(issues)


def test_does_not_warn_when_plt_colorbar_follows_imshow():
    # Arrange
    src = (
        "import matplotlib.pyplot as plt\n"
        "def f(ax, data):\n"
        "    im = ax.imshow(data)\n"
        "    plt.colorbar(im, ax=ax)\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert not _fired(issues)


def test_does_not_warn_when_no_imshow_call_present():
    # Arrange
    src = "def f(ax, x, y):\n    ax.plot(x, y)\n"

    # Act
    issues = _run(src)

    # Assert
    assert not _fired(issues)


# ---------------------------------------------------------------------------
# Escape hatch
# ---------------------------------------------------------------------------


def test_does_not_warn_when_opt_out_comment_present():
    # Arrange
    src = "def f(ax, data):\n    ax.imshow(data)  # stx-allow: STX-FM018\n"

    # Act
    issues = _run(src)

    # Assert
    assert not _fired(issues)
