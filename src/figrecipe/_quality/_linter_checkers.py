"""AST NodeVisitor factories for the figrecipe linter plugin.

Extracted from ``_linter_plugin.py`` to keep that orchestrator module
under the project line-cap and to make the checker logic independently
testable.

Three factories live here:

- ``_make_style_kwarg_checker(P006, P007, P008, P009)`` — flags
  style-override kwargs (``s=`` on scatter, ``fontsize=``, ``figsize=``,
  ``linewidth=``/``lw=``).
- ``_make_figure_method_checker(FM010, FM011)`` — flags
  ``set_xlabel`` / ``set_ylabel`` / ``set_title`` (recommend ``set_xyt``)
  and ``ax.spines[...].set_visible(False)`` (recommend ``hide_spines``).
- ``_make_label_caps_checker(P011)`` — flags axis-label / title string
  *literals* that begin with a lowercase letter (``set_xlabel("density")``,
  ``set_xyt("time", ...)``, ``suptitle("overview")``) and recommends
  capitalizing the first word. Only clear string literals are inspected;
  f-strings, variables, and `.format(...)` expressions are skipped because
  their runtime value cannot be statically proven.

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


# ---------------------------------------------------------------------------
# Label-capitalization checker (STX-P011)
# ---------------------------------------------------------------------------

# Axis-label / title setters whose FIRST positional argument is the label
# string. ``set_xyt`` / ``set_xytc`` are figrecipe's combined setters; their
# first three positional args are xlabel, ylabel, title (caption is 4th and
# is NOT a title-cased label, so it is excluded).
_LABEL_FIRST_ARG_METHODS = frozenset(
    {"set_xlabel", "set_ylabel", "set_title", "suptitle"}
)
# Combined setters: positions that hold a capitalizable label.
# index -> human-readable arg name (for the message). set_xytc adds caption
# at index 3 which is deliberately omitted.
_COMBINED_LABEL_METHODS = {
    "set_xyt": {0: "xlabel", 1: "ylabel", 2: "title"},
    "set_xytc": {0: "xlabel", 1: "ylabel", 2: "title"},
}


def _literal_str(node):
    """Return the str value if *node* is a plain string literal, else None.

    Deliberately conservative: only ``ast.Constant`` holding a ``str`` is
    treated as a literal. f-strings (``ast.JoinedStr``), names, attribute
    access, and ``.format(...)`` calls all return ``None`` so the checker
    never guesses at a runtime value (skip f-strings / variables, per spec).
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _strip_leading_groups(text):
    """Drop leading parenthetical / bracketed / math-mode groups + space.

    Publication labels often lead with a stats or unit qualifier that
    legitimately contains lowercase letters and must NOT be judged as the
    "first word":

        "(n=10) Density"   → "Density"     (skip the (n=...) group)
        "[a.u.] Power"     → "Power"       (skip the unit bracket)
        "$\\alpha$ band"    → "band"        (skip the math segment)

    A leading ``(...)`` / ``[...]`` / ``$...$`` group (and one following
    space) is removed; the rest of the label is what we capitalize-check.
    Only ONE leading group is stripped — that covers the real cases without
    over-eagerly chewing through the whole string.
    """
    s = text.lstrip()
    if not s:
        return s
    pairs = {"(": ")", "[": "]"}
    if s[0] in pairs:
        close = pairs[s[0]]
        end = s.find(close)
        if end != -1:
            return s[end + 1 :].lstrip()
    if s[0] == "$":
        end = s.find("$", 1)
        if end != -1:
            return s[end + 1 :].lstrip()
    return s


def _starts_lowercase(text):
    """True iff *text*'s first cased character is a lowercase letter.

    A leading parenthetical / bracketed / math group is stripped first (see
    :func:`_strip_leading_groups`) so a stats prefix like ``"(n=10) Density"``
    is judged on ``"Density"`` — not on the ``n`` inside ``(n=10)``. After
    that, leading non-letter characters (digits, punctuation, whitespace) are
    skipped and the first *cased* letter decides. A label with NO cased
    letter (pure ``"$\\Delta$"`` / ``"123"``) is never flagged.
    """
    stripped = _strip_leading_groups(text)
    for ch in stripped:
        if ch.isalpha():
            return ch.islower()
    return False


def _make_label_caps_checker(P011):
    """Build an AST NodeVisitor class that flags lowercase axis-label literals.

    Fires STX-P011 when a string *literal* passed as an axis label / title
    begins with a lowercase letter:

    - ``ax.set_xlabel("density")`` / ``set_ylabel`` / ``set_title`` (1st arg)
    - ``fig.suptitle("overview")`` (1st arg)
    - ``ax.set_xyt("time", "voltage", "trace")`` (x/y/title positional args)
    - ``ax.set_xytc(...)`` (x/y/title positional args; caption excluded)

    Only clear string literals are inspected — f-strings, variables, and
    ``.format(...)`` results are skipped (their value is not statically
    known). Capitalized labels and non-letter-leading labels do not fire.

    Same deferred-import discipline as the other factories in this module.
    """

    class LabelCapsChecker(ast.NodeVisitor):
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

        def _check_arg(self, arg_node, node):
            text = _literal_str(arg_node)
            if text is None:
                return  # not a literal (f-string / variable / expression)
            if not text.strip():
                return  # empty / whitespace-only label
            if _starts_lowercase(text):
                # Anchor the issue at the offending string literal so the
                # reported line/col point at the label, not the call head.
                self._emit(P011, arg_node)

        def visit_Call(self, node):
            func = node.func
            fname = (
                func.attr
                if isinstance(func, ast.Attribute)
                else (func.id if isinstance(func, ast.Name) else "")
            )

            if fname in _LABEL_FIRST_ARG_METHODS:
                if node.args:
                    self._check_arg(node.args[0], node)

            combined = _COMBINED_LABEL_METHODS.get(fname)
            if combined is not None:
                for idx, _argname in combined.items():
                    if idx < len(node.args):
                        self._check_arg(node.args[idx], node)

            self.generic_visit(node)

    return LabelCapsChecker


__all__ = [
    "_make_style_kwarg_checker",
    "_make_figure_method_checker",
    "_make_label_caps_checker",
]

# EOF
