"""STX-FIG001 axis-range-alignment AST checker.

Detects matplotlib subplot grids where multiple axes call
``set_xlim``/``set_ylim`` with different literal ranges but the figure
was NOT created with ``sharex=True`` / ``sharey=True``.

Motivation (rule #4 of `_skills/scientific/01_figures_01_standards.md`):
when several subplots plot the same quantity, mismatched axis ranges
destroy the reader's ability to compare them visually.

The checker is conservative — if the range argument is not a literal
tuple/list of numbers, we cannot prove the ranges differ, so we skip.
If only one axis sets the limit, there is nothing to compare. The opt-out
``# stx-allow: STX-FIG001`` may be placed on the figure-creation line or
on any of the offending ``set_xlim``/``set_ylim`` lines.

Severity is WARNING (not error) because two subplots can legitimately
plot different quantities (e.g. a time-series and a histogram).
"""

from __future__ import annotations

import ast
from dataclasses import replace as _replace


def _scitex_linter_runtime():
    """Lazily import ``(Issue, _is_allowed_by_comment)`` from scitex-linter.

    Deferred to call-time because ``figrecipe._linter_plugin.get_plugin``
    is itself invoked by ``scitex_dev.linter._plugin_loader.load_plugins``
    while ``scitex_dev.linter.checker`` is still mid-initialization. A
    top-level ``from scitex_dev.linter.checker import Issue`` would race
    with that init and silently fall back to ``Issue=None``, making the
    checker inert. Returning ``(None, None)`` keeps the checker tolerant
    of environments where scitex-linter is not installed at all.
    """
    try:
        from scitex_dev.linter.checker import Issue, _is_allowed_by_comment

        return Issue, _is_allowed_by_comment
    except ImportError:  # pragma: no cover
        return None, None


# Names of factory calls that produce a (fig, axes) grid in one shot.
_GRID_FACTORIES = ("subplots",)

# Method-name patterns we track per-axis.
_LIMIT_METHODS = ("set_xlim", "set_ylim")


def _extract_literal_range(node):
    """Return a (lo, hi) tuple of floats if *node* is a recognisable literal
    numeric range, else ``None``.

    Recognises three call shapes (matches matplotlib's API)::

        ax.set_ylim((0, 1))      # tuple positional
        ax.set_ylim([0, 1])      # list positional
        ax.set_ylim(0, 1)        # two positionals
        ax.set_ylim(bottom=0, top=1)  # kwargs

    Returns ``None`` if any element is non-literal (a Name, Call, etc.) —
    the checker stays conservative when it cannot prove the range value.
    """
    args = node.args
    kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}

    # Form: ax.set_xlim(lo, hi)
    if len(args) == 2 and not kwargs:
        lo = _as_number(args[0])
        hi = _as_number(args[1])
        if lo is None or hi is None:
            return None
        return (lo, hi)

    # Form: ax.set_xlim((lo, hi)) or ax.set_xlim([lo, hi])
    if len(args) == 1 and not kwargs:
        arg = args[0]
        if isinstance(arg, (ast.Tuple, ast.List)) and len(arg.elts) == 2:
            lo = _as_number(arg.elts[0])
            hi = _as_number(arg.elts[1])
            if lo is None or hi is None:
                return None
            return (lo, hi)
        return None

    # Form: ax.set_xlim(left=0, right=1)  /  ax.set_ylim(bottom=0, top=1)
    lo_key = "left" if node.func.attr == "set_xlim" else "bottom"
    hi_key = "right" if node.func.attr == "set_xlim" else "top"
    if lo_key in kwargs and hi_key in kwargs and not args:
        lo = _as_number(kwargs[lo_key])
        hi = _as_number(kwargs[hi_key])
        if lo is None or hi is None:
            return None
        return (lo, hi)

    return None


def _as_number(node):
    """Return a Python float if *node* is a numeric literal (possibly negated)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    # Handle unary minus on a literal (e.g. -1.0).
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, (int, float))
    ):
        return -float(node.operand.value)
    return None


def _is_subplots_call(node):
    """True iff *node* is a ``*.subplots(...)`` or bare ``subplots(...)`` Call."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr in _GRID_FACTORIES
    if isinstance(func, ast.Name):
        return func.id in _GRID_FACTORIES
    return False


def _kwarg_true(node, name):
    """True iff *node*.keywords contains ``name=True``."""
    for kw in node.keywords:
        if (
            kw.arg == name
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is True
        ):
            return True
    return False


def _axis_name(node):
    """If *node* is ``<name>.set_xlim`` / ``<name>.set_ylim`` return ``<name>``.

    Handles only the simple ``ax.set_xlim(...)`` shape. Subscripted axes
    arrays (``axes[0].set_ylim``) are not tracked — the checker stays
    conservative, those are out-of-scope.
    """
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in _LIMIT_METHODS:
        return None
    if isinstance(func.value, ast.Name):
        return func.value.id
    return None


class _GridScope:
    """Per-scope state: track grid creations and the limit calls that follow."""

    __slots__ = ("grids", "limits")

    def __init__(self):
        # List of grids in this scope. Each grid is a dict:
        #   {"line": int, "sharex": bool, "sharey": bool, "axes": set[str] | None}
        # axes=None means "we don't know which names belong to this grid"
        # (e.g. assigned via tuple unpacking we couldn't parse), in which
        # case any later set_x/ylim is associated with the most recent grid.
        self.grids: list[dict] = []
        # List of limit calls in this scope, each:
        #   {"method": str, "axis": str, "range": tuple|None, "node": ast.Call,
        #    "line": int}
        self.limits: list[dict] = []


def _names_from_target(target):
    """Return the set of bound Name ids from an assignment target, or None.

    Handles ``ax``, ``(fig, ax)``, ``(fig, (ax1, ax2))``. Anything else
    (subscript, attribute, Starred) -> ``None`` (caller treats grid as
    'unknown axis names').
    """
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        out: set[str] = set()
        for elt in target.elts:
            sub = _names_from_target(elt)
            if sub is None:
                return None
            out.update(sub)
        return out
    return None


def _axes_names_from_subplots_assign(node):
    """Given ``fig, ax = plt.subplots(...)`` return the names that hold axes.

    Convention: the second element of a 2-tuple target is the axes. For a
    single name on the LHS (``axes = plt.subplots(...)`` — rare) we treat
    that single name as the axes container. Returns ``None`` if we can't
    parse the binding shape.
    """
    if len(node.targets) != 1:
        return None
    target = node.targets[0]
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)) and len(target.elts) == 2:
        return _names_from_target(target.elts[1])
    return None


class AxisAlignmentChecker(ast.NodeVisitor):
    """STX-FIG001 — flag mismatched literal axis ranges in subplot grids."""

    category = "figure"

    def __init__(self, source_lines, config, rule=None):
        self.source_lines = source_lines
        self.config = config
        self.issues: list = []
        self._rule = rule  # injected by plugin loader
        # Stack of scopes (one per function/module).
        self._scopes: list[_GridScope] = [_GridScope()]

    # -- helpers ------------------------------------------------------------

    def _src(self, lineno):
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].rstrip()
        return ""

    def _scope(self):
        return self._scopes[-1]

    def _emit(self, grid, offenders):
        """Emit one issue per offending limit call (keeps line numbers honest)."""
        Issue, _is_allowed_by_comment = _scitex_linter_runtime()
        if Issue is None or self._rule is None:
            return  # scitex-linter not importable; checker is inert
        rule = self._rule
        if rule.id in self.config.disable:
            return
        # Opt-out on the figure-creation line suppresses the whole grid.
        grid_line_src = self._src(grid["line"])
        if _is_allowed_by_comment(grid_line_src, rule.id):
            return
        sev = self.config.per_rule_severity.get(rule.id)
        if sev:
            rule = _replace(rule, severity=sev)
        for off in offenders:
            line_src = self._src(off["line"])
            if _is_allowed_by_comment(line_src, rule.id):
                continue
            self.issues.append(
                Issue(
                    rule=rule,
                    line=off["line"],
                    col=off["node"].col_offset,
                    source_line=line_src,
                )
            )

    # -- scope management ---------------------------------------------------

    def visit_FunctionDef(self, node):
        self._scopes.append(_GridScope())
        self.generic_visit(node)
        self._finalize_scope()
        self._scopes.pop()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Module(self, node):
        self.generic_visit(node)
        self._finalize_scope()

    # -- statement visitors -------------------------------------------------

    def visit_Assign(self, node):
        # Detect: ``fig, ax = plt.subplots(...)`` (or ``fig.subplots(...)``).
        if isinstance(node.value, ast.Call) and _is_subplots_call(node.value):
            axes = _axes_names_from_subplots_assign(node)
            self._scope().grids.append(
                {
                    "line": node.lineno,
                    "sharex": _kwarg_true(node.value, "sharex"),
                    "sharey": _kwarg_true(node.value, "sharey"),
                    "axes": axes,  # set[str] or None
                }
            )
        self.generic_visit(node)

    def visit_Call(self, node):
        # Track ax.set_xlim / ax.set_ylim calls.
        name = _axis_name(node)
        if name is not None:
            method = node.func.attr
            rng = _extract_literal_range(node)
            self._scope().limits.append(
                {
                    "method": method,
                    "axis": name,
                    "range": rng,
                    "node": node,
                    "line": node.lineno,
                }
            )
        self.generic_visit(node)

    # -- finalize -----------------------------------------------------------

    def _finalize_scope(self):
        scope = self._scope()
        if not scope.grids or not scope.limits:
            return

        for grid in scope.grids:
            # Group limit calls belonging to this grid by method.
            # Convention: a limit call belongs to the *most recent* preceding
            # grid in the same scope. If grid.axes is known, also require
            # the axis name match. If grid.axes is None, accept any axis.
            grid_idx = scope.grids.index(grid)
            next_grid_line = (
                scope.grids[grid_idx + 1]["line"]
                if grid_idx + 1 < len(scope.grids)
                else float("inf")
            )

            by_method: dict = {"set_xlim": [], "set_ylim": []}
            for lim in scope.limits:
                if lim["line"] <= grid["line"] or lim["line"] >= next_grid_line:
                    continue
                if grid["axes"] is not None and lim["axis"] not in grid["axes"]:
                    continue
                by_method[lim["method"]].append(lim)

            # Gate by sharex/sharey: if sharing is on for that axis, skip.
            if grid["sharex"]:
                by_method["set_xlim"] = []
            if grid["sharey"]:
                by_method["set_ylim"] = []

            for method, lims in by_method.items():
                # Need at least two axes setting the same limit method, with
                # literal ranges, to even consider warning.
                concrete = [lim for lim in lims if lim["range"] is not None]
                # Distinct axis names — repeated calls on the same axis don't
                # constitute a "comparison across subplots".
                by_axis: dict = {}
                for lim in concrete:
                    by_axis.setdefault(lim["axis"], lim)
                if len(by_axis) < 2:
                    continue
                ranges = {lim["range"] for lim in by_axis.values()}
                if len(ranges) < 2:
                    continue  # all aligned
                self._emit(grid, list(by_axis.values()))
