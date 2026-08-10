#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STX-FM017 six-stat-annotation-completeness AST checker.

Companion to the scitex-dev "Statistics Completeness Doctrine"
(``scitex_dev/_skills/scientific/03_reporting_02_statistics-completeness.md``,
landed in scitex-ai/scitex-dev#290, operator-issued 2026-07-05): every
reported statistic must carry all six of

    n / 95% CI / method (test name) / p-value / effect size / test statistic

or it is incomplete. This checker is the figrecipe-side, figure-annotation
half of that doctrine: a *soft*, heuristic static check on literal string
arguments passed to the places figrecipe draws a stats annotation —
``ax.add_stat_annotation(text=...)`` (the dedicated helper, see
``_wrappers/_stat_annotation.py``), and the lower-level ``ax.text(...)`` /
``ax.annotate(...)`` calls a script might use directly for the same purpose.

Heuristic, by design (this is a warning, not a parser):

- The string must look like a stats annotation at all — it is only
  considered when it contains a p-value marker (``p=0.03`` / ``p<0.001`` /
  ...). Plain captions/labels with no p-value marker are never flagged,
  keeping false positives on ordinary text near zero.
- Once a string passes that gate, each of the six required fields is
  matched independently and loosely (word-boundary regexes, not a strict
  grammar). A string needs at least four of the six recognisable markers
  to be treated as "complete enough" — flagging only fires when *several*
  fields are clearly missing (e.g. a bare ``"p=0.03"``), never on a string
  that is merely missing one edge-case field.
- Only literal string constants are inspected (``ast.Constant``); f-strings
  and other dynamic expressions are skipped rather than guessed at.

See ``src/figrecipe/_skills/figrecipe/27_six-stat-annotation-doctrine.md``
for the full doctrine writeup (the six fields, the italic-symbol
convention, and the N-vs-n subscript convention) and a compliant example.
"""

from __future__ import annotations

import ast
import re
from dataclasses import replace as _replace

# Gate: does this string even look like a stats annotation? Also doubles as
# the "p" marker below (a string that fails this never reaches marker scoring
# at all, and any string that passes it already has the "p" marker).
_P_VALUE_MARKER = re.compile(r"p\s*[<=]\s*[0-9.]", re.IGNORECASE)

_MARKERS = {
    "n": re.compile(r"\bn\s*=\s*\d", re.IGNORECASE),
    "ci": re.compile(r"\bci\b|\d+\s*%\s*ci", re.IGNORECASE),
    "method": re.compile(
        r"(t-test|anova|wilcoxon|mann-whitney|u-test|pearson|spearman|"
        r"chi-square|chi2|kruskal|regression|correlation)",
        re.IGNORECASE,
    ),
    "p": _P_VALUE_MARKER,
    "effect": re.compile(r"(effect size|cohen|eta|η|\bd\s*=|\br\s*=)", re.IGNORECASE),
    "statistic": re.compile(
        r"(\bt\s*\(|\bf\s*\(|\bu\s*=|\bz\s*=|\bt\s*=|\bf\s*=|chi2\s*=|χ)",
        re.IGNORECASE,
    ),
}

# A string needs >= this many of the six markers to be considered complete.
_MIN_PRESENT = 4


def _present_count(text: str) -> int:
    return sum(1 for pattern in _MARKERS.values() if pattern.search(text))


def _scitex_linter_runtime():
    """Lazily import ``(Issue, _is_allowed_by_comment)`` from scitex-linter.

    Same deferred-import discipline as the other figrecipe checkers (see
    ``_axis_alignment_checker.py`` for the full rationale): figrecipe's
    plugin factory runs *during* ``scitex_dev.linter``'s own import, so a
    top-level import here would race with that init.
    """
    try:
        from scitex_dev.linter.checker import Issue, _is_allowed_by_comment

        return Issue, _is_allowed_by_comment
    except ImportError:  # pragma: no cover
        return None, None


def _fname(node: ast.Call):
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _string_candidates(node: ast.Call):
    """Return the string-literal nodes that might carry annotation text.

    - ``ax.text(x, y, s, ...)`` — third positional argument.
    - ``ax.annotate(text, xy, ...)`` — first positional argument.
    - ``ax.add_stat_annotation(..., text=...)`` — the ``text=`` keyword.
    - ``ax.text(..., s=...)`` — the ``s=`` keyword form.
    """
    fname = _fname(node)
    candidates = []
    if fname == "text" and len(node.args) >= 3:
        candidates.append(node.args[2])
    if fname == "annotate" and node.args:
        candidates.append(node.args[0])
    for kw in node.keywords:
        if kw.arg in ("text", "s"):
            candidates.append(kw.value)
    return candidates


class StatAnnotationFieldsChecker(ast.NodeVisitor):
    """STX-FM017 — flag a stats-shaped annotation string missing several
    of the six required doctrine fields (n, CI, method, p, effect, statistic).
    """

    category = "figure"

    def __init__(self, source_lines, config, rule=None):
        self.source_lines = source_lines
        self.config = config
        self.issues: list = []
        self._rule = rule  # injected by the plugin loader

    def _src(self, lineno):
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].rstrip()
        return ""

    def _emit(self, node):
        Issue, _is_allowed_by_comment = _scitex_linter_runtime()
        if Issue is None or self._rule is None:
            return  # scitex-linter not importable; checker is inert
        rule = self._rule
        if rule.id in self.config.disable:
            return
        line = self._src(node.lineno)
        if _is_allowed_by_comment(line, rule.id):
            return
        sev = self.config.per_rule_severity.get(rule.id)
        if sev:
            rule = _replace(rule, severity=sev)
        self.issues.append(
            Issue(rule=rule, line=node.lineno, col=node.col_offset, source_line=line)
        )

    def visit_Call(self, node):
        for candidate in _string_candidates(node):
            if isinstance(candidate, ast.Constant) and isinstance(candidate.value, str):
                text = candidate.value
                if _P_VALUE_MARKER.search(text) and _present_count(text) < _MIN_PRESENT:
                    self._emit(node)
                    break
        self.generic_visit(node)


__all__ = ["StatAnnotationFieldsChecker"]

# EOF
