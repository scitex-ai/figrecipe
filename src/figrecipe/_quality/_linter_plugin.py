"""Linter plugin for figrecipe: figure/layout, scientific-figure, and plot rules.

Rule families:
- FM001-FM009  — inch-based matplotlib patterns; suggest mm-based alternatives.
- FM010-FM011  — figure-method style rules (set_xlabel/set_ylabel/set_title
                 → set_xyt; ax.spines[...].set_visible(False) → hide_spines).
- FM016        — raw-mpl-bypass: raw `plt.subplots`/`plt.figure` figure
                 creation that bypasses figrecipe recording (→ fr.subplots).
- FM017        — six-stat-annotation-completeness: a stats-shaped annotation
                 string missing several of the six doctrine fields (n, CI,
                 method, p, effect, statistic).
- FM018        — heatmap-without-colorbar: `imshow(...)` with no `colorbar(...)`
                 call anywhere in the same function/module scope.
- FM019        — missing-caption: a scope that builds a figure and saves it with
                 no caption anywhere in that scope.
- FIG001       — scientific-figure hygiene (axis-range alignment across subplots).
- P001-P009    — bare matplotlib calls; suggest scitex/figrecipe tracked variants
                 and flag style-override kwargs.

Registered via entry point 'scitex_dev.linter.plugins' so scitex-linter
discovers these rules automatically when figrecipe is installed.

This file is the ORCHESTRATOR: it wires rules to checkers and assembles the
plugin dict. The rule literals live in ``_linter_rules.py`` (the catalogue grows
with every new rule, so keeping it here pushed the file past the size limit), and
the AST visitors live in ``_linter_checkers.py`` and the per-rule checker modules.
"""

from ._linter_checkers import (  # noqa: F401
    _make_figure_method_checker,
    _make_raw_mpl_bypass_checker,
    _make_style_kwarg_checker,
)
from ._linter_rules import make_fig_rules, make_fm_rules, make_plot_rules


def _rule_injecting_checker(module_path: str, class_name: str, rule):
    """Subclass a checker so it ships its own rule object.

    The plugin loader instantiates checkers with ``(source_lines, config)`` only,
    so each checker that needs a rule gets a thin subclass binding it. Returns
    None when the checker module cannot be imported (figrecipe is installable
    without scitex-linter, and the checkers are inert without it).
    """
    try:
        import importlib

        base = getattr(importlib.import_module(module_path), class_name)
    except ImportError:  # pragma: no cover
        return None

    class _Bound(base):  # type: ignore[misc, valid-type]
        def __init__(self, source_lines, config):
            super().__init__(source_lines, config, rule=rule)

    _Bound.__name__ = f"_{class_name}"
    return _Bound


def get_plugin():
    """Return figrecipe linter rules, call mappings, axes hints, and checkers."""
    from scitex_dev.linter._rules._base import Rule

    fm = make_fm_rules(Rule)
    fig = make_fig_rules(Rule)
    plot = make_plot_rules(Rule)

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

    style_checker = _make_style_kwarg_checker(
        plot["P006"], plot["P007"], plot["P008"], plot["P009"]
    )
    if style_checker is not None:
        checkers.append(style_checker)

    # FM010/FM011 AST checker. Deferred-import safe (see factory docstring).
    figure_method_checker = _make_figure_method_checker(fm["FM010"], fm["FM011"])
    if figure_method_checker is not None:
        checkers.append(figure_method_checker)

    # FM016 raw-mpl-bypass AST checker. Same deferred-import discipline.
    raw_mpl_bypass_checker = _make_raw_mpl_bypass_checker(fm["FM016"])
    if raw_mpl_bypass_checker is not None:
        checkers.append(raw_mpl_bypass_checker)

    for module_path, class_name, rule in (
        (
            "figrecipe._quality._axis_alignment_checker",
            "AxisAlignmentChecker",
            fig["FIG001"],
        ),
        (
            "figrecipe._quality._stat_annotation_fields_checker",
            "StatAnnotationFieldsChecker",
            fm["FM017"],
        ),
        (
            "figrecipe._quality._heatmap_colorbar_checker",
            "HeatmapColorbarChecker",
            fm["FM018"],
        ),
        (
            "figrecipe._quality._missing_caption_checker",
            "MissingCaptionChecker",
            fm["FM019"],
        ),
    ):
        checker = _rule_injecting_checker(module_path, class_name, rule)
        if checker is not None:
            checkers.append(checker)

    return {
        "rules": list(fm.values()) + list(fig.values()) + list(plot.values()),
        "call_rules": {
            # FM rules via call patterns
            (None, "tight_layout"): fm["FM002"],
            (None, "subplots_adjust"): fm["FM005"],
            (None, "savefig"): fm["FM006"],
            (None, "set_size_inches"): fm["FM008"],
            (None, "set_position"): fm["FM009"],
            # P004: plt.show()
            (None, "show"): plot["P004"],
        },
        # Axes method hints: fired when bare ax.plot() / ax.scatter() / ax.bar()
        # is detected without an stx/fr prefix.
        "axes_hints": {
            "plot": plot["P001"],
            "scatter": plot["P002"],
            "bar": plot["P003"],
        },
        "checkers": checkers,
    }
