#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STX-FM019 figure-saved-without-a-caption AST checker.

Operator-issued requirement (2026-07-12): every scientific figure needs, at
minimum, x/y axis labels with units (or a scale bar) AND a caption. A figure with
no caption forces the reader to reconstruct what they are looking at from the axes
alone; when panels are later composed, a panel with no caption of its own leaves a
hole in the assembled figure caption.

This checker covers the statically-checkable half: a script that builds a figure
and saves it, with **no caption anywhere in the same function/module scope**.

Conservative by construction, because the obvious implementation is wrong. Naively
flagging every ``save(...)`` call would fire on ``stx.io.save(df, "table.csv")`` —
saving a dataframe is not a figure and needs no caption. So a scope is only
considered at all when it BUILDS a figure (a ``subplots``/``compose`` call is
present), and only figure-shaped saves are flagged:

- ``savefig(...)``, which is a figure method by definition, or
- ``save(<name>, ...)`` where the first argument is named like a figure
  (``fig``, ``figure``, ``fig2``, ``fig_a``, ...).

``stx.io.save(df, ...)`` in a scope that also draws a figure therefore does not
fire, and a scope that only writes data files is never examined.

Caption evidence is likewise broad, since figrecipe offers several ways to give
one and any of them satisfies the requirement: ``add_figure_caption(...)``,
``add_panel_captions(...)``, ``set_caption(...)``, or a ``caption=`` /
``panel_captions=`` keyword on any call (``fr.save(fig, path, caption=...)``,
``fr.compose(..., caption=...)``).

Soft (warning) and opt-out-able with ``# stx-allow: STX-FM019``, matching
STX-FM017/018 — a genuinely caption-less figure (a schematic, a QC plot that never
leaves the analysis directory) is a legitimate choice the author should be able to
make explicitly.
"""

from __future__ import annotations

import ast
from dataclasses import replace as _replace

# A scope only gets examined if it actually builds a figure.
_FIGURE_BUILDERS = frozenset({"subplots", "compose"})

# Any of these means a caption was supplied; one is enough.
_CAPTION_CALLS = frozenset(
    {"add_figure_caption", "add_panel_captions", "set_caption", "set_panel_captions"}
)
_CAPTION_KWARGS = frozenset({"caption", "panel_captions"})


def _scitex_linter_runtime():
    """Lazily import ``(Issue, _is_allowed_by_comment)`` from scitex-linter.

    Same deferred-import discipline as the other figrecipe checkers (see
    ``_axis_alignment_checker.py`` for the full rationale): figrecipe's plugin
    factory runs *during* ``scitex_dev.linter``'s own import.
    """
    try:
        from scitex_dev.linter.checker import Issue, _is_allowed_by_comment

        return Issue, _is_allowed_by_comment
    except ImportError:  # pragma: no cover
        return None, None


def _looks_like_a_figure(node: ast.AST) -> bool:
    """Is this argument named like a figure? ``fig``, ``figure``, ``fig2``, ..."""
    if isinstance(node, ast.Name):
        name = node.id.lower()
    elif isinstance(node, ast.Attribute):
        name = node.attr.lower()
    else:
        return False
    return name == "figure" or name.startswith("fig")


class _CaptionScope:
    """Per-scope state: figure-shaped saves, plus whether a figure/caption exists."""

    __slots__ = ("save_calls", "builds_figure", "has_caption")

    def __init__(self):
        self.save_calls: list = []
        self.builds_figure = False
        self.has_caption = False


class MissingCaptionChecker(ast.NodeVisitor):
    """STX-FM019 — flag a figure saved with no caption anywhere in its scope."""

    category = "figure"

    def __init__(self, source_lines, config, rule=None):
        self.source_lines = source_lines
        self.config = config
        self.issues: list = []
        self._rule = rule  # injected by the plugin loader
        self._scopes: list = [_CaptionScope()]

    # -- helpers ----------------------------------------------------------

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
        self._scopes.append(_CaptionScope())
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

        scope = self._scope()

        if fname in _FIGURE_BUILDERS:
            scope.builds_figure = True
        if fname in _CAPTION_CALLS:
            scope.has_caption = True
        if any(kw.arg in _CAPTION_KWARGS for kw in node.keywords if kw.arg):
            scope.has_caption = True

        # savefig is a figure method by definition; a bare save(...) only counts
        # when its first argument is named like a figure -- otherwise it is just
        # as likely to be stx.io.save(df, "table.csv"), which needs no caption.
        if fname == "savefig":
            scope.save_calls.append(node)
        elif fname == "save" and node.args and _looks_like_a_figure(node.args[0]):
            scope.save_calls.append(node)

        self.generic_visit(node)

    # -- finalize ---------------------------------------------------------

    def _finalize_scope(self):
        scope = self._scope()
        if scope.builds_figure and scope.save_calls and not scope.has_caption:
            for node in scope.save_calls:
                self._emit(node)


__all__ = ["MissingCaptionChecker"]

# EOF
