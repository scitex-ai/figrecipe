"""STX-I001 / STX-I009 — raw ``matplotlib.pyplot`` / ``seaborn`` imports.

Both say "plot through ``stx.plt`` (figrecipe's wrapper)", so they belong to
figrecipe. Moved from the scitex-dev engine with no behaviour change: engine
metadata verbatim, the engine's exact matching, emission through
``spi.add_issue`` (the engine's gate — so research projects' ``error`` pins for
I001/I009 still apply).

Declared only when the installed scitex-dev's handover table names figrecipe
as their owner (scitex-dev >= 0.65.0); against an older engine figrecipe does
not declare them and the engine keeps emitting its own copy, so a mixed
install never collides and never loses the rule.
"""

from __future__ import annotations

import ast

__all__ = ["I001_SPEC", "I009_SPEC", "bind_raw_import_checker", "owned_import_rules"]

I001_SPEC = dict(
    id="STX-I001",
    severity="warning",
    category="import",
    message="Use `stx.plt` instead of importing matplotlib.pyplot directly",
    suggestion="Replace with `stx.plt` (or `plt` injected by @stx.session).",
    requires="scitex",
)

I009_SPEC = dict(
    id="STX-I009",
    severity="warning",
    category="import",
    message="Avoid `import seaborn` — use `stx.plt` (figrecipe wrapper) instead",
    suggestion=(
        "Replace seaborn usage with `stx.plt` / figrecipe equivalents "
        "(get_styled_axes, set_xyt, hide_spines, etc.). If you genuinely "
        "need seaborn — e.g. interop with a legacy notebook — add "
        "`# stx-allow: STX-I009` on the import line."
    ),
    requires="scitex",
)


def owned_import_rules(Rule, spi):
    """Return ``(I001, I009)`` when the engine yields them to figrecipe, else None."""
    handover = getattr(spi, "HANDOVER", {})
    if not all(handover.get(i) == "figrecipe" for i in ("STX-I001", "STX-I009")):
        return None
    return Rule(**I001_SPEC), Rule(**I009_SPEC)


def bind_raw_import_checker(I001, I009, spi):
    """Return the checker class emitting I001 / I009 exactly as the engine did."""

    class RawPlotImportChecker(ast.NodeVisitor):
        category = "import"
        # Package-availability map for the ``requires`` gate; None = detect.
        available = None

        def __init__(self, source_lines, config):
            self.source_lines = source_lines
            self.config = config
            self.issues = []

        def _emit(self, rule, node):
            lineno = node.lineno
            source = (
                self.source_lines[lineno - 1].rstrip()
                if 1 <= lineno <= len(self.source_lines)
                else ""
            )
            spi.add_issue(
                self.issues,
                rule,
                lineno,
                node.col_offset,
                source,
                self.config,
                available=self.available,
            )

        def visit_Import(self, node):
            for alias in node.names:
                if "matplotlib.pyplot" in alias.name:
                    self._emit(I001, node)
                if alias.name == "seaborn":
                    self._emit(I009, node)
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            module = node.module or ""
            if module == "matplotlib":
                if any(alias.name == "pyplot" for alias in node.names):
                    self._emit(I001, node)
            elif module and "matplotlib.pyplot" in module:
                self._emit(I001, node)
            self.generic_visit(node)

    return RawPlotImportChecker


# EOF
