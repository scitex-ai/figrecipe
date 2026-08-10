#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STX-FM018 heatmap-without-colorbar AST checker.

Companion to the figrecipe six-stat / heatmap-colorbar doctrine leaf
(``src/figrecipe/_skills/figrecipe/27_six-stat-annotation-doctrine.md``):
any 2D heatmap (``imshow``-style plot of a 2D array) MUST ship a colorbar
with tick labels, an axis label, and units on that label — the same tier
as figrecipe's existing axis-label/unit requirements elsewhere in this
lint plugin.

This checker covers the first, staticly-checkable half of that
requirement: an ``imshow(...)`` call with **no accompanying
``colorbar(...)`` call anywhere in the same function/module scope**. It
does not (and, staticly, cannot) verify tick labels / axis label / units
on the colorbar — that is a runtime/content concern the doctrine leaf
documents but which is left to review, matching the "doc-only where a
linter can't reach" acknowledgement in the sister scitex-dev doctrine.

Scope-based, mirroring ``_axis_alignment_checker.AxisAlignmentChecker``:
a new scope is pushed per function/module, ``imshow`` and ``colorbar``
calls are tallied per scope, and every ``imshow`` call in a scope with
zero ``colorbar`` calls anywhere in it is flagged at scope-finalize.
Matched by method name only (not type-resolved), consistent with the
rest of this plugin's call-shape heuristics — e.g. ``fig.colorbar(...)``,
``plt.colorbar(...)``, and ``ax.figure.colorbar(...)`` are all recognised.

figrecipe's imperative ``ax.imshow(...)`` API (``_wrappers/_axes_plots.
imshow_plot``) does **not** auto-add a colorbar — only the declarative
YAML/dict plot-spec path does (``_api/_plot_helpers._maybe_add_colorbar``),
and that path is not Python source an AST checker ever sees. So this rule
has no false-positive collision with figrecipe's own auto-colorbar
behaviour for the imperative API scripts actually lint.
"""

from __future__ import annotations

import ast
from dataclasses import replace as _replace


def _scitex_linter_runtime():
    """Lazily import ``(Issue, _is_allowed_by_comment)`` from scitex-linter.

    Same deferred-import discipline as the other figrecipe checkers (see
    ``_axis_alignment_checker.py`` for the full rationale).
    """
    try:
        from scitex_dev.linter.checker import Issue, _is_allowed_by_comment

        return Issue, _is_allowed_by_comment
    except ImportError:  # pragma: no cover
        return None, None


class _HeatmapScope:
    """Per-scope state: imshow call sites + whether a colorbar was seen."""

    __slots__ = ("imshow_calls", "has_colorbar")

    def __init__(self):
        self.imshow_calls: list = []
        self.has_colorbar = False


class HeatmapColorbarChecker(ast.NodeVisitor):
    """STX-FM018 — flag ``imshow(...)`` with no ``colorbar(...)`` in scope."""

    category = "figure"

    def __init__(self, source_lines, config, rule=None):
        self.source_lines = source_lines
        self.config = config
        self.issues: list = []
        self._rule = rule  # injected by the plugin loader
        self._scopes: list[_HeatmapScope] = [_HeatmapScope()]

    # -- helpers --------------------------------------------------------

    def _src(self, lineno):
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].rstrip()
        return ""

    def _scope(self):
        return self._scopes[-1]

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

    # -- scope management -------------------------------------------------

    def visit_FunctionDef(self, node):
        self._scopes.append(_HeatmapScope())
        self.generic_visit(node)
        self._finalize_scope()
        self._scopes.pop()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Module(self, node):
        self.generic_visit(node)
        self._finalize_scope()

    # -- call tracking ----------------------------------------------------

    def visit_Call(self, node):
        func = node.func
        if isinstance(func, ast.Attribute):
            fname = func.attr
        elif isinstance(func, ast.Name):
            fname = func.id
        else:
            fname = ""

        if fname == "imshow":
            self._scope().imshow_calls.append(node)
        elif fname == "colorbar":
            self._scope().has_colorbar = True

        self.generic_visit(node)

    # -- finalize -----------------------------------------------------------

    def _finalize_scope(self):
        scope = self._scope()
        if scope.imshow_calls and not scope.has_colorbar:
            for node in scope.imshow_calls:
                self._emit(node)


__all__ = ["HeatmapColorbarChecker"]

# EOF
