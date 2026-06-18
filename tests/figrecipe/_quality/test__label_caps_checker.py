"""Tests for STX-P010 label-capitalization AST rule.

Real ast.parse + LabelCapsChecker — no mocks. Each test follows
Arrange / Act / Assert with one assertion. Test names are >=3 words
and describe behaviour.

STX-P010 flags axis-label / title string LITERALS that start with a
lowercase letter (set_xlabel/set_ylabel/set_title/suptitle and the
x/y/title positional args of figrecipe's set_xyt/set_xytc). f-strings,
variables, and `.format(...)` results are skipped — the checker only
inspects clear string literals.

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
_P010 = next(r for r in _PLUGIN["rules"] if r.id == "STX-P010")


def _make_config():
    from scitex_dev.linter.config import load_config

    return load_config(start_path=__file__)


def _run(src: str):
    """Parse *src* and run the LabelCapsChecker; return issues."""
    from figrecipe._quality._linter_checkers import _make_label_caps_checker

    tree = ast.parse(src)
    source_lines = src.splitlines()
    cls = _make_label_caps_checker(_P010)
    checker = cls(source_lines, _make_config())
    checker.visit(tree)
    return checker.issues


def _p010_count(src: str) -> int:
    return sum(1 for i in _run(src) if i.rule.id == "STX-P010")


# ---------------------------------------------------------------------------
# Fires on lowercase string literals
# ---------------------------------------------------------------------------


def test_p010_flags_lowercase_set_xlabel():
    # Arrange
    src = 'def f(ax):\n    ax.set_xlabel("density")\n'

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-P010" for i in issues)


def test_p010_flags_lowercase_set_ylabel():
    # Arrange
    src = 'def f(ax):\n    ax.set_ylabel("frequency")\n'

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-P010" for i in issues)


def test_p010_flags_lowercase_set_title():
    # Arrange
    src = 'def f(ax):\n    ax.set_title("panel a overview")\n'

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-P010" for i in issues)


def test_p010_flags_lowercase_suptitle():
    # Arrange
    src = 'def f(fig):\n    fig.suptitle("overview of results")\n'

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-P010" for i in issues)


def test_p010_flags_lowercase_set_xyt_xlabel():
    # Arrange — set_xyt first positional (xlabel) is lowercase.
    src = 'def f(ax):\n    ax.set_xyt("time", "Voltage", "Trace")\n'

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-P010" for i in issues)


def test_p010_flags_each_lowercase_set_xyt_arg():
    # Arrange — all three x/y/title positionals are lowercase.
    src = 'def f(ax):\n    ax.set_xyt("time", "voltage", "raw trace")\n'

    # Act
    count = _p010_count(src)

    # Assert — one issue per offending literal (x, y, title).
    assert count == 3


def test_p010_flags_lowercase_set_xytc_title():
    # Arrange — set_xytc x/y/title checked (caption position excluded).
    src = 'def f(ax):\n    ax.set_xytc("X", "Y", "trace", "Caption")\n'

    # Act
    issues = _run(src)

    # Assert
    assert any(i.rule.id == "STX-P010" for i in issues)


# ---------------------------------------------------------------------------
# Does NOT fire — capitalized, non-literal, or excluded positions
# ---------------------------------------------------------------------------


def test_p010_ignores_capitalized_set_xlabel():
    # Arrange
    src = 'def f(ax):\n    ax.set_xlabel("Density")\n'

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-P010" for i in issues)


def test_p010_ignores_capitalized_set_xyt():
    # Arrange — all three labels already capitalized.
    src = 'def f(ax):\n    ax.set_xyt("Time", "Voltage", "Trace")\n'

    # Act
    count = _p010_count(src)

    # Assert
    assert count == 0


def test_p010_skips_fstring_label():
    # Arrange — f-string value is not statically known.
    src = 'def f(ax, n):\n    ax.set_xlabel(f"count {n}")\n'

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-P010" for i in issues)


def test_p010_skips_variable_label():
    # Arrange — a bare Name argument is not a literal.
    src = "def f(ax, label):\n    ax.set_xlabel(label)\n"

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-P010" for i in issues)


def test_p010_skips_format_call_label():
    # Arrange — `.format(...)` result is a Call, not a literal.
    src = 'def f(ax):\n    ax.set_xlabel("count {}".format(3))\n'

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-P010" for i in issues)


def test_p010_excludes_set_xytc_caption_position():
    # Arrange — only the caption (4th positional) is lowercase; x/y/title
    # are capitalized, so the caption must NOT trigger P010.
    src = 'def f(ax):\n    ax.set_xytc("X", "Y", "T", "lower caption")\n'

    # Act
    count = _p010_count(src)

    # Assert
    assert count == 0


def test_p010_ignores_label_starting_with_symbol():
    # Arrange — first cased letter is uppercase 'D' after the math/paren
    # prefix; nothing lowercase leads the label text.
    src = 'def f(ax):\n    ax.set_ylabel("(n=10) Density")\n'

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-P010" for i in issues)


def test_p010_ignores_label_with_no_cased_letters():
    # Arrange — pure symbol/number label has no letter to capitalize.
    src = 'def f(ax):\n    ax.set_xlabel("123 / 456")\n'

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-P010" for i in issues)


def test_p010_does_not_touch_unrelated_calls():
    # Arrange — a lowercase string in a non-label call is irrelevant.
    src = 'def f(ax):\n    ax.plot([1, 2], label="series")\n'

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-P010" for i in issues)


# ---------------------------------------------------------------------------
# Allow-comment honoured
# ---------------------------------------------------------------------------


def test_p010_respects_stx_allow_comment():
    # Arrange — intentional lowercase (e.g. a gene name) opted out.
    src = 'def f(ax):\n    ax.set_xlabel("density")  # stx-allow: STX-P010\n'

    # Act
    issues = _run(src)

    # Assert
    assert not any(i.rule.id == "STX-P010" for i in issues)


# EOF
