"""Tests for STX-FIG001 axis-range-alignment AST rule.

Real ast.parse + AxisAlignmentChecker — no mocks. Each test follows
Arrange / Act / Assert with one assertion. Test names are >=3 words
and describe behaviour.
"""

from __future__ import annotations

import ast

import pytest

# Skip the whole module gracefully if scitex_dev isn't importable in this
# environment — the checker itself is import-guarded the same way.
pytest.importorskip("scitex_dev.linter.checker")

from figrecipe._axis_alignment_checker import AxisAlignmentChecker  # noqa: E402
from figrecipe._linter_plugin import get_plugin  # noqa: E402

# Locate the FIG001 rule object once via the plugin registration. Tests
# instantiate the checker directly with this rule, mirroring the wiring
# in _linter_plugin.py.
_PLUGIN = get_plugin()
_FIG001 = next(r for r in _PLUGIN["rules"] if r.id == "STX-FIG001")


def _make_config():
    """Real linter config; no mocks. The checker reads .disable and
    .per_rule_severity, both of which exist on the dataclass default.
    """
    from scitex_dev.linter.config import load_config

    return load_config(start_path=__file__)


def _run(src: str):
    """Parse *src* and run AxisAlignmentChecker; return collected issues."""
    tree = ast.parse(src)
    source_lines = src.splitlines()
    checker = AxisAlignmentChecker(source_lines, _make_config(), rule=_FIG001)
    checker.visit(tree)
    # _finalize_scope runs on Module exit inside visit_Module; if visit()
    # dispatched generic_visit instead we call it explicitly. Safe either
    # way — the checker guards against empty grids.
    checker._finalize_scope()
    # Deduplicate by line number (visit_Module + explicit call could
    # otherwise double-count).
    seen = set()
    unique = []
    for issue in checker.issues:
        key = (issue.line, issue.col, issue.rule.id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique


# ---------------------------------------------------------------------------
# POSITIVE — fires
# ---------------------------------------------------------------------------


def test_warns_on_mismatched_set_ylim_in_subplots():
    # Arrange
    src = (
        "import matplotlib.pyplot as plt\n"
        "def make():\n"
        "    fig, (ax1, ax2) = plt.subplots(1, 2)\n"
        "    ax1.set_ylim((0, 1))\n"
        "    ax2.set_ylim((0, 5))\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-FIG001" for i in issues)


def test_warns_on_mismatched_set_xlim_two_positional_args():
    # Arrange — two positional numeric arguments form (matplotlib API).
    src = (
        "import matplotlib.pyplot as plt\n"
        "def make():\n"
        "    fig, (ax1, ax2) = plt.subplots(1, 2)\n"
        "    ax1.set_xlim(0, 1)\n"
        "    ax2.set_xlim(0, 10)\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-FIG001" for i in issues)


# ---------------------------------------------------------------------------
# NEGATIVE — does not fire
# ---------------------------------------------------------------------------


def test_does_not_warn_when_ranges_are_aligned():
    # Arrange
    src = (
        "import matplotlib.pyplot as plt\n"
        "def make():\n"
        "    fig, (ax1, ax2) = plt.subplots(1, 2)\n"
        "    ax1.set_ylim((0, 1))\n"
        "    ax2.set_ylim((0, 1))\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FIG001" for i in issues)


def test_does_not_warn_when_sharey_is_true():
    # Arrange
    src = (
        "import matplotlib.pyplot as plt\n"
        "def make():\n"
        "    fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)\n"
        "    ax1.set_ylim((0, 1))\n"
        "    ax2.set_ylim((0, 5))\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FIG001" for i in issues)


def test_does_not_warn_when_opt_out_on_subplots_line():
    # Arrange — opt-out comment placed on figure-creation line.
    src = (
        "import matplotlib.pyplot as plt\n"
        "def make():\n"
        "    fig, (ax1, ax2) = plt.subplots(1, 2)  # stx-allow: STX-FIG001\n"
        "    ax1.set_ylim((0, 1))\n"
        "    ax2.set_ylim((0, 5))\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FIG001" for i in issues)


def test_does_not_warn_when_only_one_axis_sets_limit():
    # Arrange
    src = (
        "import matplotlib.pyplot as plt\n"
        "def make():\n"
        "    fig, (ax1, ax2) = plt.subplots(1, 2)\n"
        "    ax1.set_ylim((0, 1))\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FIG001" for i in issues)


def test_does_not_warn_on_non_literal_range_arguments():
    # Arrange — ranges are variables, checker cannot prove inequality.
    src = (
        "import matplotlib.pyplot as plt\n"
        "def make():\n"
        "    fig, (ax1, ax2) = plt.subplots(1, 2)\n"
        "    ymax_a = 1\n"
        "    ymax_b = 5\n"
        "    ax1.set_ylim((0, ymax_a))\n"
        "    ax2.set_ylim((0, ymax_b))\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FIG001" for i in issues)
