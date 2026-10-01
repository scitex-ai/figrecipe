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
  * ``open`` / ``fromarray`` / ``crop`` are never flagged.
  * ``resize`` / ``thumbnail`` are FM013 (rendered-panel rescale), and only in
    a module that ALSO composites. A resize on its own is ordinary analysis —
    scaling an array in order to plot it — so it must stay silent; a resize in
    a script that pastes panels together is panel rescale, which is what makes
    a composite carry text at several sizes. The compositing call is the
    signal that distinguishes them, which is why both rules live in one pass
    rather than in two modules that would each need it.

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
    """STX-FM012 compositing + STX-FM013 rendered-panel rescale, in one pass."""

    category = "figure"

    #: Calls whose whole purpose is to put one raster inside another.
    _COMPOSITING_CALLS = frozenset(
        {"paste", "alpha_composite", "hconcat", "vconcat"}
    )

    #: Calls that change a raster's size. Only meaningful as a finding when the
    #: module also composites — see the module docstring.
    _RESCALE_CALLS = frozenset({"resize", "thumbnail"})

    #: Importing one of these is what makes a module a candidate at all.
    _IMAGING_MODULES = frozenset({"PIL", "Image", "cv2", "imageio"})

    def __init__(self, source_lines, config, rule=None, rescale_rule=None):
        self.source_lines = source_lines
        self.config = config
        self.issues: list = []
        self._rule = rule  # FM012, injected by the plugin loader
        self._rescale_rule = rescale_rule  # FM013, optional
        self._imaging_imported = False
        self._candidates: list = []
        self._rescale_candidates: list = []

    # -- helpers --------------------------------------------------------

    def _src(self, lineno):
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].rstrip()
        return ""

    def _emit(self, node, rule=None):
        Issue, _is_allowed_by_comment = _scitex_linter_runtime()
        rule = rule if rule is not None else self._rule
        if Issue is None or rule is None:
            return  # scitex-linter not importable; checker is inert
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
        if isinstance(func, ast.Attribute):
            if func.attr in self._COMPOSITING_CALLS:
                self._candidates.append(node)
            elif func.attr in self._RESCALE_CALLS:
                self._rescale_candidates.append(node)
        self.generic_visit(node)

    # -- finalize ---------------------------------------------------------

    def visit_Module(self, node):
        self.generic_visit(node)
        # Emit only now: an imaging import below the call still gates it, and
        # FM013 needs to know whether the module composited ANYWHERE, which is
        # only knowable once the whole module has been walked.
        if not self._imaging_imported:
            return
        for candidate in self._candidates:
            self._emit(candidate)
        # A resize is only a rendered-panel rescale if panels are being
        # composited here at all. Without that, it is ordinary image work.
        if self._candidates:
            for candidate in self._rescale_candidates:
                self._emit(candidate, rule=self._rescale_rule)


__all__ = ["RasterTilingChecker"]

# EOF
