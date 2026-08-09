#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STX-FM012 raster-tiling-of-rendered-panels AST checker.

The anti-pattern this catches actually happened: a script assembled a
multi-panel figure by opening the rendered panel PNGs with PIL and pasting
them into one canvas, downscaling as it went. Every panel's text shrank by a
different factor, so the composite carried several font sizes that no style
declared, and the mm layout contract figrecipe exists to hold was gone. The
figure looked plausible, which is why it survived to review.

figrecipe's own path composes at 1:1 from the recipes (``fr.compose``,
``Figz``, ``align_panels``), so the composite keeps every panel's mm
footprint, its text size, and its provenance.

SCOPE — deliberately narrow, because the cost of a false positive here is an
author fighting the linter over legitimate image work:

  * Only fires when the module imports an imaging library (PIL / Image /
    cv2 / imageio). A script with no such import is never examined.
  * Only COMPOSITING calls are flagged — ``paste``, ``alpha_composite``,
    ``hconcat``, ``vconcat``. These exist to put one raster inside another;
    there is no reason to reach for them while merely loading or plotting
    image DATA.
  * ``open`` / ``resize`` / ``fromarray`` / ``crop`` are NOT flagged here.
    Resizing an array to plot it via imshow is ordinary analysis, and
    rendered-panel RESCALE is its own rule (FM013) rather than a guess made
    from a resize call in isolation.

Matched by attribute name only, consistent with the rest of this plugin's
call-shape heuristics (see ``_heatmap_colorbar_checker`` for the same
approach). Candidates are collected and only emitted once the whole module
has been walked, so an imaging import placed below the call still gates it.

Escape hatch: ``# stx-allow: STX-FM012`` on the offending line — for the
genuine case of assembling image DATA (a montage of microscope tiles that IS
the data) rather than rendered figure panels.
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


class RasterTilingChecker(ast.NodeVisitor):
    """STX-FM012 — flag PIL/cv2 compositing of rendered figure panels."""

    category = "figure"

    #: Calls whose whole purpose is to put one raster inside another.
    _COMPOSITING_CALLS = frozenset(
        {"paste", "alpha_composite", "hconcat", "vconcat"}
    )

    #: Importing one of these is what makes a module a candidate at all.
    _IMAGING_MODULES = frozenset({"PIL", "Image", "cv2", "imageio"})

    def __init__(self, source_lines, config, rule=None):
        self.source_lines = source_lines
        self.config = config
        self.issues: list = []
        self._rule = rule  # injected by the plugin loader
        self._imaging_imported = False
        self._candidates: list = []

    # -- helpers --------------------------------------------------------

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

    # -- import tracking --------------------------------------------------

    def _note_module(self, dotted: str) -> None:
        if dotted and dotted.split(".")[0] in self._IMAGING_MODULES:
            self._imaging_imported = True

    def visit_Import(self, node):
        for alias in node.names:
            self._note_module(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # `from PIL import Image` — the module gate; also `from cv2 import ...`.
        self._note_module(node.module or "")
        for alias in node.names:
            self._note_module(alias.name)
        self.generic_visit(node)

    # -- call tracking ----------------------------------------------------

    def visit_Call(self, node):
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in self._COMPOSITING_CALLS:
            self._candidates.append(node)
        self.generic_visit(node)

    # -- finalize ---------------------------------------------------------

    def visit_Module(self, node):
        self.generic_visit(node)
        # Emit only now: an imaging import below the call still gates it.
        if self._imaging_imported:
            for candidate in self._candidates:
                self._emit(candidate)


__all__ = ["RasterTilingChecker"]

# EOF
