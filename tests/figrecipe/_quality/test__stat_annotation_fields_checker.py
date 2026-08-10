"""Tests for STX-FM017 six-stat-annotation-completeness AST rule.

Real ast.parse + StatAnnotationFieldsChecker — no mocks. Each test follows
Arrange / Act / Assert with one assertion and a >=3-word behavioural name.
"""

from __future__ import annotations

import ast

import pytest

# Skip the whole module gracefully if scitex_dev isn't importable in this
# environment — the checker itself is import-guarded the same way.
pytest.importorskip("scitex_dev.linter.checker")

from figrecipe._quality._linter_plugin import get_plugin  # noqa: E402
from figrecipe._quality._stat_annotation_fields_checker import (  # noqa: E402
    StatAnnotationFieldsChecker,
)

# Locate the FM017 rule object once via the plugin registration. Tests
# instantiate the checker directly with this rule, mirroring the wiring
# in _linter_plugin.py.
_PLUGIN = get_plugin()
_FM017 = next(r for r in _PLUGIN["rules"] if r.id == "STX-FM017")


def _make_config():
    """Real linter config; no mocks. The checker reads .disable and
    .per_rule_severity, both of which exist on the dataclass default.
    """
    from scitex_dev.linter.config import load_config

    return load_config(start_path=__file__)


def _run(src: str):
    """Parse *src* and run StatAnnotationFieldsChecker; return issues."""
    tree = ast.parse(src)
    source_lines = src.splitlines()
    checker = StatAnnotationFieldsChecker(source_lines, _make_config(), rule=_FM017)
    checker.visit(tree)
    return checker.issues


def _fired(issues):
    return any(i.rule.id == "STX-FM017" for i in issues)


# ---------------------------------------------------------------------------
# POSITIVE — fires on a clearly-incomplete stats-shaped string
# ---------------------------------------------------------------------------


def test_warns_on_bare_p_value_via_ax_text():
    # Arrange
    src = "def f(ax):\n    ax.text(0.5, 0.9, 'p=0.03')\n"

    # Act
    issues = _run(src)

    # Assert
    assert _fired(issues)


def test_warns_on_bare_p_value_via_annotate():
    # Arrange
    src = "def f(ax):\n    ax.annotate('p<0.05', (0.5, 0.9))\n"

    # Act
    issues = _run(src)

    # Assert
    assert _fired(issues)


def test_warns_on_add_stat_annotation_missing_fields():
    # Arrange — only p present; n/CI/method/effect/statistic all missing.
    src = "def f(ax):\n    ax.add_stat_annotation(0, 1, text='p=0.03')\n"

    # Act
    issues = _run(src)

    # Assert
    assert _fired(issues)


def test_warns_when_only_n_and_p_present():
    # Arrange — two of six fields present, still clearly incomplete.
    src = "def f(ax):\n    ax.text(0.5, 0.9, 'n=20, p=0.03')\n"

    # Act
    issues = _run(src)

    # Assert
    assert _fired(issues)


# ---------------------------------------------------------------------------
# NEGATIVE — does not fire
# ---------------------------------------------------------------------------


def test_does_not_warn_on_compliant_six_field_annotation():
    # Arrange — all six doctrine fields present.
    src = (
        "def f(ax):\n"
        "    ax.text(0.5, 0.9, 'N=12, n=340, r=0.42, 95% CI [0.21, 0.60], "
        "t(338)=5.1, p<0.001 (Pearson correlation)')\n"
    )

    # Act
    issues = _run(src)

    # Assert
    assert not _fired(issues)


def test_does_not_warn_on_plain_caption_text():
    # Arrange — no p-value marker at all, so the string is never even
    # considered a stats annotation.
    src = "def f(ax):\n    ax.text(0.5, 0.9, 'Figure 3: representative trace')\n"

    # Act
    issues = _run(src)

    # Assert
    assert not _fired(issues)


def test_does_not_warn_on_significance_stars_only():
    # Arrange — the built-in stars shorthand has no p-value marker.
    src = "def f(ax):\n    ax.text(0.5, 0.9, '***')\n"

    # Act
    issues = _run(src)

    # Assert
    assert not _fired(issues)


def test_does_not_warn_on_dynamic_fstring_text():
    # Arrange — f-strings are not literal constants; checker skips them
    # rather than guessing at their eventual value.
    src = "def f(ax, p):\n    ax.text(0.5, 0.9, f'p={p}')\n"

    # Act
    issues = _run(src)

    # Assert
    assert not _fired(issues)


# ---------------------------------------------------------------------------
# Escape hatch
# ---------------------------------------------------------------------------


def test_does_not_warn_when_opt_out_comment_present():
    # Arrange
    src = "def f(ax):\n    ax.text(0.5, 0.9, 'p=0.03')  # stx-allow: STX-FM017\n"

    # Act
    issues = _run(src)

    # Assert
    assert not _fired(issues)
