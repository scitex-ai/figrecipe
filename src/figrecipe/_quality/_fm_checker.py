"""FM001-FM009 (figure / millimetre) AST checker — owned by figrecipe.

figrecipe declares STX-FM001..FM009, and this is the checker that emits
them. It used to live in the scitex-dev engine
(``scitex_dev.linter._fm_checker.FMChecker``) and was passed through this
plugin's payload; it now lives next to the rules it enforces. The port is
verbatim — same call/assign detection, same ``stx``/``scitex``/``fr``
exemption, same context-dependent suggestion variants, same gates (config
disable, ``# stx-allow``, per-rule pin, category floor; no ``requires`` gate,
exactly as before) — so findings are unchanged.

The plugin declares the ``fm-checker`` capability; scitex-dev >= 0.65.0 then
skips its own engine copy (kept there only as the shim for an older
figrecipe).
"""

from __future__ import annotations

import ast
from dataclasses import replace

__all__ = ["bind_fm_checker"]


def _can_import(name) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def _is_exempt_call(node):
    """Check if the call is on a stx.* or fr.* object (exempt from FM rules)."""
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False
    if isinstance(func.value, ast.Name) and func.value.id in ("stx", "scitex", "fr"):
        return True
    if isinstance(func.value, ast.Attribute):
        if isinstance(func.value.value, ast.Name) and func.value.value.id in (
            "stx",
            "scitex",
            "fr",
        ):
            return True
    return False


def _has_kwarg(node, name, value=None):
    """Check if call has a specific keyword argument."""
    for kw in node.keywords:
        if kw.arg == name:
            if value is None:
                return True
            if isinstance(kw.value, ast.Constant) and kw.value.value == value:
                return True
    return False


_SIZE_MM = {
    "both": (
        "Use mm-based sizing: `stx.plt.subplots(axes_width_mm=40, axes_height_mm=28)` "
        "or `fr.subplots(axes_width_mm=40, axes_height_mm=28)`."
    ),
    "stx": "Use mm-based sizing: `stx.plt.subplots(axes_width_mm=40, axes_height_mm=28)`.",
    "fr": "Use mm-based sizing: `fr.subplots(axes_width_mm=40, axes_height_mm=28)`.",
}
_MARGIN_MM = {
    "both": (
        "Use mm-based margins: `stx.plt.subplots(margin_left_mm=15, margin_bottom_mm=12)` "
        "or `fr.subplots(margin_left_mm=15, margin_bottom_mm=12)`."
    ),
    "stx": "Use mm-based margins: `stx.plt.subplots(margin_left_mm=15, margin_bottom_mm=12)`.",
    "fr": "Use mm-based margins: `fr.subplots(margin_left_mm=15, margin_bottom_mm=12)`.",
}

# Suggestion variants: {rule_id: {context: suggestion}}
_SUGGESTIONS = {
    "STX-FM001": _SIZE_MM,
    "STX-FM002": _MARGIN_MM,
    "STX-FM003": {
        "both": "Use `stx.io.save(fig, './plot.png')` or `fr.save(fig, './plot.png')` for intelligent cropping.",
        "stx": "Use `stx.io.save(fig, './plot.png')` which handles cropping intelligently.",
        "fr": "Use `fr.save(fig, './plot.png')` which handles cropping intelligently.",
    },
    "STX-FM004": {
        "both": "Use mm-based layout from `stx.plt.subplots()` or `fr.subplots()` instead.",
        "stx": "Use mm-based layout from `stx.plt.subplots()` instead of constrained_layout.",
        "fr": "Use mm-based layout from `fr.subplots()` instead of constrained_layout.",
    },
    "STX-FM005": {
        "both": (
            "Use mm-based spacing: `stx.plt.subplots(space_w_mm=8, space_h_mm=10)` "
            "or `fr.subplots(space_w_mm=8, space_h_mm=10)`."
        ),
        "stx": "Use mm-based spacing: `stx.plt.subplots(space_w_mm=8, space_h_mm=10)`.",
        "fr": "Use mm-based spacing: `fr.subplots(space_w_mm=8, space_h_mm=10)`.",
    },
    "STX-FM006": {
        "both": "Use `stx.io.save(fig, './plot.png')` or `fr.save(fig, './plot.png')` for provenance tracking.",
        "stx": "Use `stx.io.save(fig, './plot.png')` for provenance tracking.",
        "fr": "Use `fr.save(fig, './plot.png')` for recipe tracking.",
    },
    "STX-FM007": {
        "both": "Use `stx.plt` style presets or `fr.load_style('SCITEX')` for consistent styling.",
        "stx": "Use `stx.plt` style presets for consistent styling.",
        "fr": "Use `fr.load_style('SCITEX')` for consistent styling.",
    },
    "STX-FM008": _SIZE_MM,
    "STX-FM009": _MARGIN_MM,
}


def bind_fm_checker(fm, spi):
    """Return the FM checker class bound to figrecipe's own FM rules.

    Args:
        fm: figrecipe's FM rule dict (``make_fm_rules`` output).
        spi: ``scitex_dev.linter.spi`` (for ``Issue`` / ``# stx-allow``).
    """

    class FMChecker(ast.NodeVisitor):
        """AST visitor for FM (Figure/Millimeter) rules."""

        category = "figure"

        def __init__(self, source_lines, config):
            self.source_lines = source_lines
            self.config = config
            self.issues = []
            # figrecipe is importable by construction here; the context only
            # depends on whether the scitex umbrella is (as in the engine).
            has_fr = _can_import("figrecipe") or _can_import("scitex.plt")
            has_stx = _can_import("scitex")
            if has_fr and has_stx:
                self._ctx = "both"
            elif has_stx:
                self._ctx = "stx"
            else:
                self._ctx = "fr"

        def _get_source(self, lineno):
            if 1 <= lineno <= len(self.source_lines):
                return self.source_lines[lineno - 1].rstrip()
            return ""

        def _add(self, rule, line, col, source_line):
            if rule is None:
                return
            if rule.id in self.config.disable:
                return
            if spi._is_allowed_by_comment(source_line, rule.id):
                return
            variants = _SUGGESTIONS.get(rule.id)
            if variants:
                rule = replace(
                    rule, suggestion=variants.get(self._ctx, rule.suggestion)
                )
            sev = self.config.per_rule_severity.get(rule.id)
            if not sev:
                cat_override = (
                    getattr(self.config, "category_severity_override", {}) or {}
                )
                sev = cat_override.get(rule.category)
            if sev:
                rule = replace(rule, severity=sev)
            self.issues.append(
                spi.Issue(rule=rule, line=line, col=col, source_line=source_line)
            )

        def visit_Call(self, node):
            self._check_call(node)
            self.generic_visit(node)

        def visit_Assign(self, node):
            self._check_assign(node)
            self.generic_visit(node)

        def _check_call(self, node):
            """Check Call nodes for FM001-FM006, FM008, FM009."""
            if _is_exempt_call(node):
                return
            func = node.func
            if not isinstance(func, ast.Attribute):
                return
            func_name = func.attr
            line = self._get_source(node.lineno)
            at = (node.lineno, node.col_offset, line)
            if func_name == "tight_layout":
                self._add(fm["FM002"], *at)
                return
            if func_name == "subplots_adjust":
                self._add(fm["FM005"], *at)
                return
            if func_name == "savefig":
                if _has_kwarg(node, "bbox_inches", "tight"):
                    self._add(fm["FM003"], *at)
                self._add(fm["FM006"], *at)
                return
            if func_name == "set_size_inches":
                self._add(fm["FM008"], *at)
                return
            if func_name == "set_position":
                self._add(fm["FM009"], *at)
                return
            if func_name in ("figure", "subplots", "Figure"):
                if _has_kwarg(node, "figsize"):
                    self._add(fm["FM001"], *at)
                if _has_kwarg(node, "constrained_layout", True):
                    self._add(fm["FM004"], *at)

        def _check_assign(self, node):
            """Check Assign nodes for FM007 (rcParams modification)."""
            for target in node.targets:
                if not isinstance(target, ast.Subscript):
                    continue
                val = target.value
                if not isinstance(val, ast.Attribute) or val.attr != "rcParams":
                    continue
                if isinstance(val.value, ast.Name) and val.value.id in (
                    "plt",
                    "mpl",
                    "matplotlib",
                ):
                    line = self._get_source(node.lineno)
                    self._add(fm["FM007"], node.lineno, node.col_offset, line)
                    break

    return FMChecker


# EOF
