#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-axes post-replay finalization passes for figure reproduction.

These passes run after every axes' calls/decorations/insets have been replayed
and after colorbars are reconstructed. They are extracted from ``_core.py`` to
keep that module focused on the top-level reproduce flow (and under the
project's per-file line budget). The ordering here is load-bearing -- see the
inline comments on each pass.
"""

from typing import List, Optional

import numpy as np

from .._recorder import FigureRecord
from .._utils._grid import parse_grid_id


def finalize_reproduced_axes(
    fig,
    axes_2d: np.ndarray,
    record: FigureRecord,
    nrows: int,
    ncols: int,
    calls: Optional[List[str]],
    skip_decorations: bool,
) -> None:
    """Run the per-axes finalization passes in their required order.

    Parameters
    ----------
    fig : matplotlib Figure
        The reproduced figure (kept for signature symmetry / future passes).
    axes_2d : ndarray of Axes
        The 2D grid of raw matplotlib axes.
    record : FigureRecord
        The record being reproduced.
    nrows, ncols : int
        Grid dimensions.
    calls : list of str, optional
        Restrict reproduction to these call ids (mirrors ``reproduce``).
    skip_decorations : bool
        When True, recorded limits live in decorations and are not reapplied.
    """
    from ..styles._style_applier import finalize_special_plots, finalize_ticks

    # Finalize tick configuration and special plot types.
    for row in range(nrows):
        for col in range(ncols):
            finalize_ticks(axes_2d[row, col])
            finalize_special_plots(axes_2d[row, col], record.style or {})

    # Reapply imshow tick/spine suppression after finalize_ticks: it can
    # re-add numeric ticks on an imshow axes, and finalize_special_plots skips
    # a labelled imshow (is_specgram heuristic). Keyed on the recorded call
    # name -- the same discriminator the live imshow wrapper uses -- so save
    # and reproduce hide ticks identically (never touches a real specgram).
    from ._replay_axes import finalize_imshow_axes

    for ax_key, ax_record in record.axes.items():
        parsed = parse_grid_id(ax_key)
        row, col = parsed if parsed else (0, 0)
        finalize_imshow_axes(axes_2d[row, col], ax_record, record.style)

    # Re-apply recorded set_xlim / set_ylim LAST so explicit limits win over any
    # autoscale re-engaged by later decorations (e.g. set_xscale), insets,
    # colorbars, or the tick finalizers (NeuroVista Ask 2). Skipped when the
    # caller asked to skip decorations (the limits live in decorations).
    if not skip_decorations:
        from ._reapply_limits import reapply_recorded_limits

        for ax_key, ax_record in record.axes.items():
            parsed = parse_grid_id(ax_key)
            row, col = parsed if parsed else (0, 0)
            reapply_recorded_limits(axes_2d[row, col], ax_record, calls)

    # Re-apply the recorded FINAL spine visibility LAST. apply_style_mm (run
    # pre-replay) only hides top+right per the style behaviour, so a script that
    # hid ALL spines would otherwise keep a spurious left+bottom L-spine on
    # replay (NeuroVista Fig03b, MSE 117). final_spines is captured post-render
    # from the live axes, so this faithfully reproduces whatever the user did --
    # raw set_visible, ax.hide_spines(), or the style. ``None`` (legacy recipes)
    # -> leave the style default untouched.
    for ax_key, ax_record in record.axes.items():
        spines = getattr(ax_record, "final_spines", None)
        if not spines:
            continue
        parsed = parse_grid_id(ax_key)
        row, col = parsed if parsed else (0, 0)
        ax = axes_2d[row, col]
        for side, visible in spines.items():
            if side in ax.spines:
                ax.spines[side].set_visible(visible)

    # Pin constrained_layout panels to their recorded geometry (LAST). See the
    # function docstring -- this freezes the axes rectangles so the save-time
    # constrained_layout re-solve cannot land them at a different fixed point
    # than the original recorded (NeuroVista fig05a, same-size MSE ~907).
    pin_constrained_layout_axes(axes_2d, record)


def pin_constrained_layout_axes(axes_2d: np.ndarray, record: FigureRecord) -> None:
    """Pin reproduced constrained_layout panels to their recorded geometry.

    ``constrained_layout`` solves the panel rectangles ITERATIVELY to a fixed
    point that depends on the construction path, not just the content. The
    original figure is built via the mm ``plt.subplots`` helper (which seeds a
    ``subplots_adjust`` before constrained_layout takes over) and drawn many
    times; a fresh ``reproduce()`` builds a plain ``plt.subplots(
    constrained_layout=True)`` with no such seed. The two therefore converge to
    slightly different fixed points -- on NeuroVista fig05a the reproduced panels
    land ~0.007-0.015 figure-fraction lower with a ~0.007 taller height than the
    recorded position, shifting every spine/tick/vline ~1 px and failing the
    same-size reproducibility check (MSE ~907).

    The original records each panel's SETTLED ``get_position()`` at save time
    (``AxesRecord.bbox_uncropped``, captured AFTER ``settle_constrained_layout``).
    Re-applying it here and removing the axes from the layout solver
    (``set_in_layout(False)``) freezes the geometry so the save-time re-solve
    (``settle_constrained_layout`` in ``_api/_save.py``) cannot move it. This
    generalises the per-colorbar source-panel pin (#230 ``_pin_source_axes``) to
    EVERY panel of a constrained_layout figure. Crucially it is compatible with
    the #233 deterministic content-bbox crop: that crop is keyed on the recorded
    ``content_bbox`` and is decoupled from axes geometry, so pinning no longer
    fights the save SIZE (the reason a naive pin was rejected pre-#233).

    Scope (minimal regression): runs ONLY when ``record.constrained_layout`` is
    True AND the original layout did NOT collapse (``record.layout_collapsed``).
    A COLLAPSED layout (tiny axes, e.g. bar+log+minor-ticks in 60x40 mm) is saved
    by ``save_figure`` via the content-AWARE re-measure fallback (NOT the content-
    bbox crop), so both the original and the reproduction must re-measure the SAME
    un-pinned ink -- pinning the reproduction to the degenerate recorded rect would
    change its ink extent and break the size match. The collapse is read from the
    recipe flag captured at SAVE time (no probe draw here: a draw in the reproduce
    path perturbs already-pinned colorbar geometry). Non-constrained figures keep
    their deterministic ``subplots_adjust`` / mm-layout path untouched. Pins to
    ``bbox_uncropped`` (the panel's position in the UNCROPPED figure fraction --
    ``set_position`` is figure-fraction and the save is full-canvas), falling back
    to the cropped ``bbox`` for legacy recipes saved with ``bbox_inches="tight"``
    (whose ``bbox`` already equals the uncropped position). A constrained_layout
    panel with NEITHER recorded box is a legacy recipe predating geometry capture:
    it is left on the re-solve path with a one-time ``UserWarning`` (no silent
    fallback) -- such a recipe must be re-saved to capture the geometry.
    """
    if not getattr(record, "constrained_layout", False):
        return

    # A collapsed layout is saved via the content-aware re-measure fallback on
    # BOTH sides; pinning the reproduction would desync the ink extent. Skip it
    # (leave the axes in the solver) so the save reproduces the original fallback.
    # Read the recorded flag rather than re-probing with a draw -- a draw here
    # perturbs colorbar geometry the colorbar replay just pinned (#230).
    if getattr(record, "layout_collapsed", False):
        return

    missing_geometry = False
    for ax_key, ax_record in record.axes.items():
        parsed = parse_grid_id(ax_key)
        if parsed is None:
            continue  # mm-composed panels reproduce via their own path
        row, col = parsed
        try:
            ax = axes_2d[row, col]
        except (IndexError, KeyError):
            continue
        bbox = getattr(ax_record, "bbox_uncropped", None)
        if bbox is None or len(bbox) != 4:
            bbox = getattr(ax_record, "bbox", None)
        if bbox is None or len(bbox) != 4:
            missing_geometry = True
            continue
        ax.set_position(bbox)
        try:
            ax.set_in_layout(False)
        except Exception:
            pass  # very old matplotlib: position is still pinned above

    if missing_geometry:
        import warnings

        warnings.warn(
            "constrained_layout figure has panel(s) without recorded geometry "
            "(bbox_uncropped/bbox); leaving them on the layout re-solve path. "
            "Re-save the figure to capture panel geometry for exact "
            "constrained_layout reproduction.",
            UserWarning,
        )


__all__ = ["finalize_reproduced_axes", "pin_constrained_layout_axes"]
