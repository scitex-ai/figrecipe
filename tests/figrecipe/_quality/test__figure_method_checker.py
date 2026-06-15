"""Tests for STX-FM010 / STX-FM011 figure-method AST rules.

Real ast.parse + FigureMethodChecker — no mocks. Each test follows
Arrange / Act / Assert with one assertion. Test names are >=3 words
and describe behaviour.

The checker imports scitex_dev.linter.checker symbols lazily inside
``_emit()``, so the test module gracefully importorskips when
scitex_dev isn't installable in this environment.
"""

from __future__ import annotations

import ast

import pytest

pytest.importorskip("scitex_dev.linter.checker")
pytest.importorskip("scitex_dev.linter.config")

from figrecipe._quality._linter_plugin import get_plugin  # noqa: E402

_PLUGIN = get_plugin()
_FM010 = next(r for r in _PLUGIN["rules"] if r.id == "STX-FM010")
_FM011 = next(r for r in _PLUGIN["rules"] if r.id == "STX-FM011")


def _make_config():
    from scitex_dev.linter.config import load_config

    return load_config(start_path=__file__)


def _run(src: str):
    """Parse *src* and run the FigureMethodChecker; return issues."""
    from figrecipe._quality._linter_checkers import _make_figure_method_checker

    tree = ast.parse(src)
    source_lines = src.splitlines()
    cls = _make_figure_method_checker(_FM010, _FM011)
    checker = cls(source_lines, _make_config())
    checker.visit(tree)
    return checker.issues


# ---------------------------------------------------------------------------
# STX-FM010 — set_xlabel / set_ylabel / set_title
# ---------------------------------------------------------------------------


def test_fm010_warns_on_set_xlabel_call():
    # Arrange
    src = "def f(ax):\n    ax.set_xlabel('time')\n"

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-FM010" for i in issues)


def test_fm010_warns_on_set_ylabel_call():
    # Arrange
    src = "def f(ax):\n    ax.set_ylabel('amplitude')\n"

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-FM010" for i in issues)


def test_fm010_warns_on_set_title_call():
    # Arrange
    src = "def f(ax):\n    ax.set_title('panel A')\n"

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-FM010" for i in issues)


def test_fm010_does_not_fire_on_set_xyt_call():
    # Arrange — set_xyt is the recommended API; must not be flagged.
    src = "def f(ax):\n    ax.set_xyt('x', 'y', 't')\n"

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FM010" for i in issues)


# ---------------------------------------------------------------------------
# STX-FM011 — ax.spines[...].set_visible(False)
# ---------------------------------------------------------------------------


def test_fm011_warns_on_spines_set_visible_false():
    # Arrange
    src = "def f(ax):\n    ax.spines['top'].set_visible(False)\n"

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-FM011" for i in issues)


def test_fm011_does_not_fire_on_spines_set_visible_true():
    # Arrange — set_visible(True) is restoration; not the antipattern.
    src = "def f(ax):\n    ax.spines['top'].set_visible(True)\n"

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FM011" for i in issues)


def test_fm011_does_not_fire_on_hide_spines_call():
    # Arrange — recommended API.
    src = "def f(ax):\n    ax.hide_spines(top=True, right=True)\n"

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FM011" for i in issues)


def test_fm011_does_not_fire_on_unrelated_set_visible():
    # Arrange — set_visible(False) on something that isn't ax.spines[...].
    src = "def f(ax):\n    ax.xaxis.set_visible(False)\n"

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FM011" for i in issues)


# ---------------------------------------------------------------------------
# Allow-comment honoured
# ---------------------------------------------------------------------------


def test_fm010_respects_stx_allow_comment():
    # Arrange
    src = "def f(ax):\n    ax.set_xlabel('time')  # stx-allow: STX-FM010\n"

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-FM010" for i in issues)


# EOF
