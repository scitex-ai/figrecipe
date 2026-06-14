"""AST NodeVisitor factories for the figrecipe linter plugin.

Extracted from ``_linter_plugin.py`` to keep that orchestrator module
under the project line-cap and to make the checker logic independently
testable.

Two factories live here:

- ``_make_style_kwarg_checker(P006, P007, P008, P009)`` — flags
  style-override kwargs (``s=`` on scatter, ``fontsize=``, ``figsize=``,
  ``linewidth=``/``lw=``).
- ``_make_figure_method_checker(FM010, FM011)`` — flags
  ``set_xlabel`` / ``set_ylabel`` / ``set_title`` (recommend ``set_xyt``)
  and ``ax.spines[...].set_visible(False)`` (recommend ``hide_spines``).

Circular-import discipline (per neurovista 2026-06-14): both factories
defer the ``scitex_dev.linter.checker`` import into ``_emit()`` rather
than at factory-build time. figrecipe's plugin factories are called by
``load_plugins()`` *during* the scitex_dev.linter module's own import;
importing ``scitex_dev.linter.checker`` here at build time raises
ImportError, the old factory swallowed it with ``return None``, and the
checker was silently dropped from the registered checkers list.
"""

from __future__ import annotations

import ast


def _make_style_kwarg_checker(P006, P007, P008, P009):
    """Build an AST NodeVisitor class that flags style-override kwargs.

    - ``scatter(..., s=...)`` → P006
    - any call with ``fontsize=...`` → P007
    - any call with ``figsize=...``  → P008
    - any call with ``linewidth=`` / ``lw=`` → P009

    Returned class follows the scitex-linter checker contract:
    ``__init__(source_lines, config)`` + ``.issues`` list + ``.category``.
    """

    class StyleKwargChecker(ast.NodeVisitor):
        category = "plot"

        def __init__(self, source_lines, config):
            self.source_lines = source_lines
            self.config = config
            self.issues: list = []

        def _src(self, ln):
            if 1 <= ln <= len(self.source_lines):
                return self.source_lines[ln - 1].rstrip()
            return ""

        def _emit(self, rule, node):
            from dataclasses import replace as _replace

            # Deferred import — avoids the circular-import that previously
            # caused the factory to silently return None.
            from scitex_dev.linter.checker import Issue, _is_allowed_by_comment

            line = self._src(node.lineno)
            if rule.id in self.config.disable:
                return
            if _is_allowed_by_comment(line, rule.id):
                return
            sev = self.config.per_rule_severity.get(rule.id)
            if sev:
                rule = _replace(rule, severity=sev)
            self.issues.append(
                Issue(
                    rule=rule,
                    line=node.lineno,
                    col=node.col_offset,
                    source_line=line,
                )
            )

        def visit_Call(self, node):
            func = node.func
            if isinstance(func, ast.Attribute):
                fname = func.attr
            elif isinstance(func, ast.Name):
                fname = func.id
            else:
                fname = ""
            kwargs = {kw.arg for kw in node.keywords if kw.arg}
            if fname in ("scatter", "stx_scatter") and "s" in kwargs:
                self._emit(P006, node)
            if "fontsize" in kwargs:
                self._emit(P007, node)
            if "figsize" in kwargs:
                self._emit(P008, node)
            if "linewidth" in kwargs or "lw" in kwargs:
                self._emit(P009, node)
            self.generic_visit(node)

    return StyleKwargChecker


def _make_figure_method_checker(FM010, FM011):
    """Build an AST NodeVisitor class for figure-method style rules.

    - ``ax.set_xlabel(...)`` / ``ax.set_ylabel(...)`` / ``ax.set_title(...)``
        → STX-FM010 (recommend ``ax.set_xyt(x, y, t)`` instead).
    - ``ax.spines[...].set_visible(False)``
        → STX-FM011 (recommend ``ax.hide_spines(top=True, right=True, ...)``).

    Same deferred-import discipline as ``_make_style_kwarg_checker``.
    """

    class FigureMethodChecker(ast.NodeVisitor):
        category = "figure"

        def __init__(self, source_lines, config):
            self.source_lines = source_lines
            self.config = config
            self.issues: list = []

        def _src(self, ln):
            if 1 <= ln <= len(self.source_lines):
                return self.source_lines[ln - 1].rstrip()
            return ""

        def _emit(self, rule, node):
            from dataclasses import replace as _replace

            # Deferred import — see _make_style_kwarg_checker.
            from scitex_dev.linter.checker import Issue, _is_allowed_by_comment

            line = self._src(node.lineno)
            if rule.id in self.config.disable:
                return
            if _is_allowed_by_comment(line, rule.id):
                return
            sev = self.config.per_rule_severity.get(rule.id)
            if sev:
                rule = _replace(rule, severity=sev)
            self.issues.append(
                Issue(
                    rule=rule,
                    line=node.lineno,
                    col=node.col_offset,
                    source_line=line,
                )
            )

        def visit_Call(self, node):
            func = node.func
            if not isinstance(func, ast.Attribute):
                self.generic_visit(node)
                return

            fname = func.attr
            receiver = func.value

            # STX-FM010: set_xlabel / set_ylabel / set_title.
            if fname in ("set_xlabel", "set_ylabel", "set_title"):
                self._emit(FM010, node)

            # STX-FM011: ax.spines[...].set_visible(False).
            # Match shape: Call(func=Attribute(attr='set_visible',
            #     value=Subscript(value=Attribute(attr='spines'))))
            if fname == "set_visible" and isinstance(receiver, ast.Subscript):
                sub_val = receiver.value
                if isinstance(sub_val, ast.Attribute) and sub_val.attr == "spines":
                    # Only fire when the argument is literally False (the
                    # antipattern). set_visible(True) is restoration and is
                    # legitimate.
                    first_arg = node.args[0] if node.args else None
                    if isinstance(first_arg, ast.Constant) and first_arg.value is False:
                        self._emit(FM011, node)

            self.generic_visit(node)

    return FigureMethodChecker


__all__ = ["_make_style_kwarg_checker", "_make_figure_method_checker"]

# EOF
