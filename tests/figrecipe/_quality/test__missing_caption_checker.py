#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the STX-FM019 missing-caption checker.

The interesting half is the FALSE POSITIVES: a naive "flag every save()" rule
would fire on `stx.io.save(df, "table.csv")`, which is not a figure and needs no
caption. Most of these tests pin cases that must stay silent.
"""

import ast

import pytest

from figrecipe._quality._missing_caption_checker import MissingCaptionChecker


class _Config:
    """Minimal stand-in for the linter config the checker reads."""

    disable: set = set()
    per_rule_severity: dict = {}


def _issues(source: str):
    """Run the checker over a source snippet and return its issues."""
    pytest.importorskip("scitex_dev.linter.checker")
    from scitex_dev.linter._rules._base import Rule

    rule = Rule(
        id="STX-FM019",
        severity="warning",
        category="figure",
        message="figure saved with no caption",
        suggestion="add one",
    )
    lines = source.splitlines()
    checker = MissingCaptionChecker(lines, _Config(), rule=rule)
    checker.visit(ast.parse(source))
    return checker.issues


class TestFires:
    """A figure built and saved with no caption anywhere in scope."""

    def test_saved_figure_without_a_caption_is_flagged(self):
        # Arrange
        source = "fig, ax = fr.subplots()\nax.plot([1, 2])\nfr.save(fig, 'p.png')\n"
        # Act
        issues = _issues(source)
        # Assert
        assert len(issues) == 1

    def test_savefig_without_a_caption_is_flagged(self):
        # Arrange
        source = "fig, ax = fr.subplots()\nfig.savefig('p.png')\n"
        # Act
        issues = _issues(source)
        # Assert
        assert len(issues) == 1

    def test_each_scope_is_judged_on_its_own(self):
        # Arrange: one function captions its figure, the other does not.
        source = (
            "def good():\n"
            "    fig, ax = fr.subplots()\n"
            "    fr.save(fig, 'a.png', caption='A.')\n"
            "\n"
            "def bad():\n"
            "    fig, ax = fr.subplots()\n"
            "    fr.save(fig, 'b.png')\n"
        )
        # Act
        issues = _issues(source)
        # Assert
        assert [issue.line for issue in issues] == [7]


class TestStaysSilent:
    """The cases a naive implementation would wrongly flag."""

    def test_saving_a_dataframe_is_not_a_figure(self):
        # Arrange: the whole reason the rule requires a figure-shaped save. A
        # table needs no caption from this lint.
        source = "fig, ax = fr.subplots()\nfr.save(fig, 'p.png', caption='C.')\nstx.io.save(df, 'table.csv')\n"
        # Act
        issues = _issues(source)
        # Assert
        assert issues == []

    def test_a_scope_that_never_builds_a_figure_is_never_examined(self):
        # Arrange
        source = "stx.io.save(results, 'out.pkl')\n"
        # Act
        issues = _issues(source)
        # Assert
        assert issues == []

    def test_caption_kwarg_on_save_satisfies_the_rule(self):
        # Arrange
        source = "fig, ax = fr.subplots()\nfr.save(fig, 'p.png', caption='Figure 1.')\n"
        # Act
        issues = _issues(source)
        # Assert
        assert issues == []

    def test_add_figure_caption_call_satisfies_the_rule(self):
        # Arrange
        source = (
            "fig, ax = fr.subplots()\n"
            "fr.add_figure_caption(fig, 'Figure 1.')\n"
            "fr.save(fig, 'p.png')\n"
        )
        # Act
        issues = _issues(source)
        # Assert
        assert issues == []

    def test_panel_captions_satisfy_the_rule(self):
        # Arrange
        source = (
            "fig = fr.compose(panels, panel_captions=['A.', 'B.'])\n"
            "fr.save(fig, 'p.png')\n"
        )
        # Act
        issues = _issues(source)
        # Assert
        assert issues == []

    def test_figure_built_but_never_saved_is_not_flagged(self):
        # Arrange: nothing has been published, so there is nothing to caption.
        source = "fig, ax = fr.subplots()\nax.plot([1, 2])\n"
        # Act
        issues = _issues(source)
        # Assert
        assert issues == []

    def test_stx_allow_comment_suppresses_the_finding(self):
        # Arrange: a QC plot that never leaves the analysis directory.
        source = (
            "fig, ax = fr.subplots()\nfr.save(fig, 'qc.png')  # stx-allow: STX-FM019\n"
        )
        # Act
        issues = _issues(source)
        # Assert
        assert issues == []


# EOF
