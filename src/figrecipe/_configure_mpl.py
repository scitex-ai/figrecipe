#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Top-level matplotlib configurer for figrecipe.

Single-call entry point that loads the SCITEX style (or any registered
preset) and pushes ~30 rcParams onto matplotlib so subsequent plain
``plt.subplots()`` / ``plt.plot()`` calls inherit publication-quality
defaults — without forcing the caller through ``figrecipe.subplots``.

Migrated from ``scitex.plt.utils._configure_mpl.configure_mpl`` as
Phase 2 of the figrecipe-owns-plt rebalance. Differences from the
scitex original:

- **No env-var resolution layer** — direct kwargs override loaded
  style values. Power-user envs like ``SCITEX_PLT_AXES_WIDTH_MM=50``
  are no longer honoured here. Set them via the kwargs directly or
  via ``figrecipe.load_style``.
- **No scitex.* dependency** — uses ``figrecipe.styles.load_style`` /
  ``figrecipe.styles._dotdict.DotDict`` / ``figrecipe.colors`` instead
  of ``scitex.plt.styles`` / ``scitex.dict`` / ``scitex.plt.color``.
- **Simplified font fallback** — drops ``scitex.str.set_fallback_mode``;
  uses matplotlib's own font search (which is sufficient for the
  font names listed in SCITEX preset).
- **Same return shape**: ``(plt, COLORS_DotDict)`` so existing
  ``_, COLORS = configure_mpl(plt)`` callers don't need to change.
"""

from __future__ import annotations

import logging  # noqa: STX-I007 (figrecipe is a leaf — no @stx.session)
from typing import Any, Dict, Optional, Tuple

from .styles._dotdict import DotDict

logger = logging.getLogger(__name__)

# mm → pt conversion (matplotlib uses points internally)
_MM_TO_PT = 2.83465


def configure_mpl(
    plt,
    *,
    fig_size_mm: Optional[Tuple[float, float]] = None,
    fig_scale: float = 1.0,
    dpi_display: Optional[int] = None,
    dpi_save: Optional[int] = None,
    autolayout: bool = False,
    n_ticks: Optional[int] = None,
    hide_top_right_spines: Optional[bool] = None,
    line_width: Optional[float] = None,
    alpha: float = 1.0,
    enable_latex: bool = False,
    latex_preamble: Optional[str] = None,
    verbose: bool = False,
    **kwargs,
) -> Tuple[Any, "DotDict"]:
    """Configure matplotlib globally for publication-quality plots.

    Loads the figrecipe style (SCITEX preset by default) and pushes
    every relevant value onto ``matplotlib.rcParams`` so subsequent
    ``plt.subplots()`` / ``plt.plot()`` etc. inherit the preset.

    Parameters
    ----------
    plt : matplotlib.pyplot
        The pyplot module. Returned (mutated rcParams) for convenience.
    fig_size_mm : (float, float), optional
        Figure (width, height) in mm. If None, computed from style
        ``axes.width_mm + margins.left_mm + margins.right_mm`` and
        ``axes.height_mm + margins.top_mm + margins.bottom_mm``.
    fig_scale : float, optional
        Multiplier on the resolved ``fig_size_mm``.
    dpi_display, dpi_save : int, optional
        Inline / savefig DPIs. Default: ``style.output.display_dpi``
        and ``style.output.dpi``.
    autolayout : bool
        ``figure.autolayout`` rcParam. Default False (figrecipe uses
        constrained_layout via ``apply_style_mm``).
    n_ticks : int, optional
        Default tick count. Default: ``style.ticks.n_ticks``.
    hide_top_right_spines : bool, optional
        Default: ``style.behavior.hide_top_spine and …hide_right_spine``.
    line_width : float, optional
        Default line width (pt). Default: ``style.lines.trace_mm × 2.83``.
    alpha : float
        Alpha to apply to the colour palette. Default 1.0 (opaque).
    enable_latex : bool
        Try to enable matplotlib's LaTeX rendering. Falls back to
        mathtext on render failure.
    latex_preamble : str, optional
        Extra LaTeX preamble to inject when ``enable_latex=True``.
    verbose : bool
        Print resolution decisions.
    **kwargs
        Future-proofing; ignored.

    Returns
    -------
    (plt, COLORS) : (module, DotDict)
        ``COLORS`` is a DotDict mapping colour names to RGBA tuples
        (alpha-blended per ``alpha``). Access as ``COLORS.blue`` or
        ``COLORS['blue']``.
    """
    from .colors import PARAMS, update_alpha
    from .styles import load_style
    from .styles._dotdict import DotDict

    style = load_style()

    # ------------------------------------------------------------------
    # Resolve every value (direct kwarg overrides style; style overrides
    # default).
    # ------------------------------------------------------------------
    def _s(section: str, key: str, default: Any) -> Any:
        """Look up ``style.<section>.<key>``, fall back to *default*."""
        if style is None:
            return default
        sect = style.get(section, {}) if hasattr(style, "get") else {}
        if hasattr(sect, "get"):
            v = sect.get(key, default)
        else:
            v = getattr(sect, key, default)
        return v if v is not None else default

    if fig_size_mm is None:
        axes_w = _s("axes", "width_mm", 40)
        axes_h = _s("axes", "height_mm", 28)
        ml = _s("margins", "left_mm", 20)
        mr = _s("margins", "right_mm", 20)
        mb = _s("margins", "bottom_mm", 20)
        mt = _s("margins", "top_mm", 20)
        fig_size_mm = (axes_w + ml + mr, axes_h + mb + mt)

    output_dpi = int(_s("output", "dpi", 300))
    if dpi_save is None:
        dpi_save = output_dpi
    if dpi_display is None:
        dpi_display = int(_s("output", "display_dpi", max(100, output_dpi // 3)))

    if line_width is None:
        line_width = _s("lines", "trace_mm", 0.2) * _MM_TO_PT

    if n_ticks is None:
        n_ticks = int(_s("ticks", "n_ticks", 4))

    if hide_top_right_spines is None:
        hide_top = _s("behavior", "hide_top_spine", True)
        hide_right = _s("behavior", "hide_right_spine", True)
        hide_top_right_spines = bool(hide_top and hide_right)

    font_size = _s("fonts", "axis_label_pt", 7)
    title_size = _s("fonts", "title_pt", 8)
    tick_size = _s("fonts", "tick_label_pt", 7)
    legend_size = _s("fonts", "legend_pt", 6)

    axes_linewidth = _s("axes", "thickness_mm", 0.2) * _MM_TO_PT

    # ------------------------------------------------------------------
    # Colours: alpha-blend the palette into a DotDict.
    # ------------------------------------------------------------------
    RGBA = {k: update_alpha(v, alpha) for k, v in PARAMS["RGBA"].items()}
    RGBA_NORM = {
        k: tuple(update_alpha(v, alpha)) for k, v in PARAMS["RGBA_NORM"].items()
    }
    RGBA_NORM_FOR_CYCLE = {
        k: tuple(update_alpha(v, alpha))
        for k, v in PARAMS["RGBA_NORM_FOR_CYCLE"].items()
    }

    figsize_inch = (
        fig_size_mm[0] / 25.4 * fig_scale,
        fig_size_mm[1] / 25.4 * fig_scale,
    )

    # ------------------------------------------------------------------
    # Push the rcParams.
    # ------------------------------------------------------------------
    mpl_config: Dict[str, Any] = {
        "figure.dpi": dpi_display,
        "savefig.dpi": dpi_save,
        "figure.figsize": figsize_inch,
        "font.size": font_size,
        "axes.titlesize": title_size,
        "axes.labelsize": font_size,
        "xtick.labelsize": tick_size,
        "ytick.labelsize": tick_size,
        "legend.fontsize": legend_size,
        "legend.frameon": False,
        "legend.loc": "best",
        "figure.autolayout": autolayout,
        "axes.spines.top": not hide_top_right_spines,
        "axes.spines.right": not hide_top_right_spines,
        "axes.linewidth": axes_linewidth,
        "axes.prop_cycle": plt.cycler(color=list(RGBA_NORM_FOR_CYCLE.values())),
        "lines.linewidth": line_width,
        "lines.markersize": 6.0,
        "grid.linewidth": axes_linewidth,
        "grid.alpha": 0.3,
    }

    # LaTeX with graceful fallback — try to render a tiny equation, on
    # failure flip back to mathtext (cm).
    if enable_latex:
        latex_config = {
            "text.usetex": True,
            "text.latex.preamble": latex_preamble
            or r"\usepackage{amsmath}\usepackage{amssymb}",
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "mathtext.fontset": "cm",
        }
        try:
            with plt.rc_context(latex_config):
                # NB: deliberately no figsize= here — this is a one-shot
                # capability probe, not a real publication figure. The
                # rcParams default size is fine.
                fig = plt.figure()
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, r"$x^2 + y^2 = r^2$", usetex=True)
                fig.canvas.draw()
                plt.close(fig)
            mpl_config.update(latex_config)
            if verbose:
                logger.info("LaTeX rendering enabled")
        except Exception as exc:
            if verbose:
                logger.warning(
                    "LaTeX test render failed (%s); falling back to mathtext", exc
                )
            mpl_config.update(
                {
                    "text.usetex": False,
                    "mathtext.fontset": "cm",
                    "font.family": "serif",
                }
            )

    plt.rcParams.update(mpl_config)

    if verbose:
        logger.info(
            "configure_mpl: figsize=%s mm, dpi=%s/%s display/save, font=%spt",
            fig_size_mm,
            dpi_display,
            dpi_save,
            font_size,
        )

    return plt, DotDict(RGBA_NORM)


__all__ = ["configure_mpl"]
