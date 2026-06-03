"""Linter plugin for figrecipe: figure/layout, scientific-figure, and plot rules.

Rule families:
- FM001-FM009  — inch-based matplotlib patterns; suggest mm-based alternatives.
- FIG001       — scientific-figure hygiene (axis-range alignment across subplots).
- P001-P009    — bare matplotlib calls; suggest scitex/figrecipe tracked variants
                 and flag style-override kwargs.

Registered via entry point 'scitex_dev.linter.plugins' so scitex-linter
discovers these rules automatically when figrecipe is installed.
"""


def _make_style_kwarg_checker(P006, P007, P008, P009):
    """Build an AST NodeVisitor class that flags style-override kwargs:

    - ``scatter(..., s=...)``  → P006
    - any call with ``fontsize=...``  → P007
    - any call with ``figsize=...``   → P008
    - any call with ``linewidth=`` / ``lw=``  → P009

    Returned class follows the scitex-linter checker contract:
    ``__init__(source_lines, config)`` + ``.issues`` list + ``.category``.
    """
    import ast

    try:
        from scitex_dev.linter.checker import Issue, _is_allowed_by_comment
    except ImportError:
        return None

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
                    rule=rule, line=node.lineno, col=node.col_offset, source_line=line
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


def get_plugin():
    """Return figrecipe linter rules, call mappings, axes hints, and checkers."""
    from scitex_dev.linter._rules._base import Rule

    # ------------------------------------------------------------------
    # FM: Figure / Millimeter rules (FM001-FM009)
    # ------------------------------------------------------------------
    FM001 = Rule(
        id="STX-FM001",
        severity="warning",
        category="figure",
        message="`figsize=` detected — inch-based figure sizing is imprecise for publications",
        suggestion=(
            "Use mm-based sizing: `stx.plt.subplots(axes_width_mm=40, axes_height_mm=28)` "
            "or `fig, ax = fr.subplots(axes_width_mm=40, axes_height_mm=28)` for precise control."
        ),
        requires="figrecipe",
    )

    FM002 = Rule(
        id="STX-FM002",
        severity="warning",
        category="figure",
        message="`tight_layout()` detected — layout is unpredictable across plot types",
        suggestion=(
            "Use mm-based margins: `stx.plt.subplots(margin_left_mm=15, margin_bottom_mm=12)` "
            "for deterministic layout control."
        ),
        requires="figrecipe",
    )

    FM003 = Rule(
        id="STX-FM003",
        severity="warning",
        category="figure",
        message='`bbox_inches="tight"` detected — can crop important elements unpredictably',
        suggestion=(
            "Use `fr.save(fig, './plot.png')` or `stx.io.save(fig, './plot.png')` "
            "which handle cropping intelligently."
        ),
        requires="figrecipe",
    )

    FM004 = Rule(
        id="STX-FM004",
        severity="info",
        category="figure",
        message="`constrained_layout=True` detected — conflicts with mm-based layout control",
        suggestion="Use mm-based layout from `stx.plt.subplots()` instead of constrained_layout.",
        requires="figrecipe",
    )

    FM005 = Rule(
        id="STX-FM005",
        severity="info",
        category="figure",
        message="`subplots_adjust()` with hardcoded fractions — fragile across figure sizes",
        suggestion=(
            "Use mm-based spacing: `stx.plt.subplots(space_w_mm=8, space_h_mm=10)` "
            "for size-independent layout."
        ),
        requires="figrecipe",
    )

    FM006 = Rule(
        id="STX-FM006",
        severity="info",
        category="figure",
        message="`plt.savefig()` detected — no provenance tracking",
        suggestion=(
            "Use `fr.save(fig, './plot.png')` or `stx.io.save(fig, './plot.png')` "
            "for recipe tracking and provenance."
        ),
        requires="figrecipe",
    )

    FM007 = Rule(
        id="STX-FM007",
        severity="info",
        category="figure",
        message="`rcParams` direct modification detected — hard to maintain across figures",
        suggestion="Use figrecipe style presets: `fr.load_style('SCITEX')` for consistent styling.",
        requires="figrecipe",
    )

    FM008 = Rule(
        id="STX-FM008",
        severity="warning",
        category="figure",
        message="`set_size_inches()` detected — bypasses mm-based layout control",
        suggestion=(
            "Use mm-based sizing: `fr.subplots(axes_width_mm=40, axes_height_mm=28)` "
            "or `stx.plt.subplots(axes_width_mm=40, axes_height_mm=28)` for precise control."
        ),
        requires="figrecipe",
    )

    FM009 = Rule(
        id="STX-FM009",
        severity="warning",
        category="figure",
        message="`ax.set_position()` detected — conflicts with mm-based layout control",
        suggestion=(
            "Use mm-based margins: `fr.subplots(margin_left_mm=15, margin_bottom_mm=12)` "
            "or `stx.plt.subplots(margin_left_mm=15, margin_bottom_mm=12)` for deterministic layout."
        ),
        requires="figrecipe",
    )

    # ------------------------------------------------------------------
    # FIG: Scientific-figure hygiene rules (FIG001+)
    # FIG001 — multiple subplots that declare different literal axis
    # ranges via set_xlim / set_ylim without sharex/sharey will look
    # incomparable to the reader (rule #4 of the scientific-figure
    # standards). Warning, not error: two subplots can legitimately
    # plot different quantities.
    # ------------------------------------------------------------------
    FIG001 = Rule(
        id="STX-FIG001",
        severity="warning",
        category="figure",
        message=(
            "Subplots on the same figure declare different axis ranges via "
            "set_xlim/set_ylim. If these axes plot the same quantity, "
            "mismatched ranges destroy visual comparison (rule #4 of the "
            "scientific-figure standards)."
        ),
        suggestion=(
            "Either align the ranges (e.g., min(all)..max(all)), use "
            "sharex=True/sharey=True when calling plt.subplots, or annotate "
            "the call site with `# stx-allow: STX-FIG001` if the axes "
            "intentionally plot different quantities."
        ),
    )

    # ------------------------------------------------------------------
    # P: Plot rules (P001-P005)
    # ------------------------------------------------------------------
    P001 = Rule(
        id="STX-P001",
        severity="info",
        category="plot",
        message="`ax.plot()` — consider `ax.stx_line()` for automatic CSV data export",
        suggestion="Replace `ax.plot(x, y)` with `ax.stx_line(x, y)` for tracked plotting.",
        requires="scitex",
    )

    P002 = Rule(
        id="STX-P002",
        severity="info",
        category="plot",
        message="`ax.scatter()` — consider `ax.stx_scatter()` for automatic CSV data export",
        suggestion="Replace `ax.scatter(x, y)` with `ax.stx_scatter(x, y)` for tracked plotting.",
        requires="scitex",
    )

    P003 = Rule(
        id="STX-P003",
        severity="info",
        category="plot",
        message="`ax.bar()` — consider `ax.stx_bar()` for automatic sample size annotation",
        suggestion="Replace `ax.bar(x, y)` with `ax.stx_bar(x, y)` for tracked plotting.",
        requires="scitex",
    )

    P004 = Rule(
        id="STX-P004",
        severity="info",
        category="plot",
        message="`plt.show()` is non-reproducible in batch/CI environments",
        suggestion="Remove `plt.show()` — figures are auto-saved in session output directory.",
    )

    P005 = Rule(
        id="STX-P005",
        severity="info",
        category="plot",
        message="`print()` inside @stx.session — use `logger` for tracked logging",
        suggestion="Replace `print(msg)` with `logger.info(msg)` (injected by @stx.session).",
        requires="scitex",
    )

    # ------------------------------------------------------------------
    # P: Style-override rules (P006-P009) — figrecipe + SciTeX style
    # centralizes marker size, font size, figure size, and line width.
    # Per-call overrides defeat the global style and produce inconsistent
    # figures across a paper.
    # ------------------------------------------------------------------
    P006 = Rule(
        id="STX-P006",
        severity="warning",
        category="plot",
        message="`scatter(..., s=...)` — drop `s=`; SciTeX style sizes markers automatically",
        suggestion=(
            "Remove the `s=` kwarg from scatter() calls. Marker size is tuned by the "
            "SciTeX style and overriding it produces inconsistent figures."
        ),
        requires="figrecipe",
    )

    P007 = Rule(
        id="STX-P007",
        severity="warning",
        category="plot",
        message="`fontsize=` kwarg — drop it; SciTeX style sets font sizes globally",
        suggestion=(
            "Remove `fontsize=` kwargs. Set sizes once via the SciTeX style / "
            "matplotlib rcParams instead of per-call overrides."
        ),
        requires="figrecipe",
    )

    P008 = Rule(
        id="STX-P008",
        severity="warning",
        category="plot",
        message="`figsize=` kwarg — drop it; figrecipe controls layout in mm via `figure_mm()`",
        suggestion=(
            "Remove `figsize=` from `plt.subplots()`/`plt.figure()`. Use "
            "`figrecipe.figure_mm()` (or the SciTeX style defaults) so journal "
            "column widths stay consistent."
        ),
        requires="figrecipe",
    )

    P009 = Rule(
        id="STX-P009",
        severity="warning",
        category="plot",
        message="`linewidth=` kwarg — drop it; SciTeX style sets line widths globally",
        suggestion=(
            "Remove `linewidth=`/`lw=` kwargs. Set widths once via the SciTeX "
            "style / matplotlib rcParams."
        ),
        requires="figrecipe",
    )

    # ------------------------------------------------------------------
    # Checkers: AST visitors. Imports deferred so figrecipe can be
    # installed without scitex-linter.
    # ------------------------------------------------------------------
    checkers: list = []
    try:
        from scitex_dev.linter._fm_checker import FMChecker

        checkers.append(FMChecker)
    except ImportError:
        pass

    style_checker = _make_style_kwarg_checker(P006, P007, P008, P009)
    if style_checker is not None:
        checkers.append(style_checker)

    # FIG001 axis-range-alignment checker. We subclass the base checker
    # here so it ships the FIG001 rule object without the plugin loader
    # needing to know about it.
    try:
        from figrecipe._quality._axis_alignment_checker import AxisAlignmentChecker

        class _AxisAlignmentChecker(AxisAlignmentChecker):  # type: ignore[misc, valid-type]
            def __init__(self, source_lines, config):
                super().__init__(source_lines, config, rule=FIG001)

        checkers.append(_AxisAlignmentChecker)
    except ImportError:
        pass

    return {
        "rules": [
            FM001,
            FM002,
            FM003,
            FM004,
            FM005,
            FM006,
            FM007,
            FM008,
            FM009,
            FIG001,
            P001,
            P002,
            P003,
            P004,
            P005,
            P006,
            P007,
            P008,
            P009,
        ],
        "call_rules": {
            # FM rules via call patterns
            (None, "tight_layout"): FM002,
            (None, "subplots_adjust"): FM005,
            (None, "savefig"): FM006,
            (None, "set_size_inches"): FM008,
            (None, "set_position"): FM009,
            # P004: plt.show()
            (None, "show"): P004,
        },
        # Axes method hints: fired when bare ax.plot() / ax.scatter() / ax.bar()
        # is detected without an stx/fr prefix.
        "axes_hints": {
            "plot": P001,
            "scatter": P002,
            "bar": P003,
        },
        "checkers": checkers,
    }
