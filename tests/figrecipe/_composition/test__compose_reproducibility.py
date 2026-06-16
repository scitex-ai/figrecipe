#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for mm-compose *reproducibility* (round-trip fidelity).

Distinct from ``test__compose_replay_fidelity`` (which checks panel *content* is
present): these guard that a composed figure REPRODUCES from its recipe the way
the live ``compose`` built it -- the bug fixed in PR #193, where the live
``plt.compose`` path and the ``reproduce`` path built the figure differently and
save-time validation failed (first a SIZE mismatch, then a same-size MSE ~5000).

Three mechanisms are guarded:

1. ``compose_bbox`` -- compose records the EXACT ``add_axes`` input (uncropped,
   PRE-replay) per panel. Reproduce places from it, so a divider plotter
   (``stx_scatter_hist``) re-splits from the same extent instead of shrinking a
   second time, and every panel lands where the live compose put it.
2. ``FigureRecord.style`` -- compose carries the panels' style onto the composed
   record, so reproduce renders tick/axis-label text in the same font (else the
   text ghosts and MSE explodes).
3. End-to-end -- ``save(..., validate=True)`` on a composite (including a divider
   panel) reproduces within the MSE threshold and does not raise.
"""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest

import figrecipe as fr


def _panel_recipe(tmp_path, name, kind):
    """Save a one-panel source recipe (``kind`` = 'plain' or 'joint')."""
    fig, ax = fr.subplots()
    if kind == "plain":
        ax.plot([0, 1, 2], [0, 1, 0], id="line")
    else:
        rng = np.random.default_rng(0)
        ax.stx_scatter_hist(
            rng.normal(size=200), rng.normal(size=200), kde=True, id="sh"
        )
    recipe = tmp_path / f"{name}.yaml"
    fr.save(fig, recipe, validate=False, verbose=False)
    return recipe


def _compose_divider(tmp_path):
    """Build a 2-panel composite (plain line over stx_scatter_hist).

    Returns (live_composed_RecordingFigure, recipe_path).
    """
    r_plain = _panel_recipe(tmp_path, "plain", "plain")
    r_joint = _panel_recipe(tmp_path, "joint", "joint")
    sources = {
        str(r_plain): {"xy_mm": (0, 0), "size_mm": (80, 35)},
        str(r_joint): {"xy_mm": (0, 37), "size_mm": (80, 80)},
    }
    comp, _ = fr.compose(sources, canvas_size_mm=(82, 119))
    recipe = tmp_path / "composite.yaml"
    fr.save(comp, recipe, validate=False, verbose=False)
    return comp, recipe


@pytest.fixture
def divider_composite(tmp_path):
    return _compose_divider(tmp_path)


def _mpl(fig):
    return fig.fig if hasattr(fig, "fig") else fig


def _main_axes_width(mpl_fig):
    """Width of the scatter_hist MAIN axes (the one carrying the scatter).

    Draw first: ``make_axes_locatable`` divider positions only settle after a
    render, so ``get_position()`` on an undrawn reproduced figure is premature.
    """
    mpl_fig.canvas.draw()
    widths = [
        a.get_position().width for a in mpl_fig.get_axes() if len(a.collections) >= 1
    ]
    return max(widths)


def test_compose_records_compose_bbox_for_every_panel(divider_composite):
    # Arrange
    comp, _ = divider_composite
    # Act
    bboxes = [getattr(ax, "compose_bbox", None) for ax in comp.record.axes.values()]
    # Assert -- every panel carries a 4-float add_axes input
    assert bboxes and all(b is not None and len(b) == 4 for b in bboxes)


def test_compose_carries_source_style_onto_record(divider_composite):
    # Arrange
    comp, _ = divider_composite
    # Act
    style = comp.record.style
    # Assert -- without this reproduce renders text in mpl's default font (ghosts)
    assert style is not None


def test_composed_figure_reproduces_at_same_figsize(divider_composite):
    # Arrange
    comp, recipe = divider_composite
    live_size = tuple(np.round(_mpl(comp).get_size_inches(), 6))
    # Act
    repro_size = tuple(np.round(_mpl(fr.reproduce(recipe)[0]).get_size_inches(), 6))
    # Assert -- identical canvas (the original failure was a SIZE mismatch)
    assert live_size == repro_size


def test_composed_divider_main_axes_not_double_shrunk(divider_composite):
    # Arrange
    comp, recipe = divider_composite
    live_w = _main_axes_width(_mpl(comp))
    repro_w = _main_axes_width(_mpl(fr.reproduce(recipe)[0]))
    # Act
    delta = abs(live_w - repro_w)
    # Assert -- pre-#193 reproduce re-ran the divider; main axes shrank again
    # (~0.64 vs ~0.78). They must now match.
    assert delta < 0.02


def test_composite_with_divider_passes_validate_on_save(tmp_path):
    # Arrange -- build fresh (a fixture recipe was saved with validate=False)
    r_plain = _panel_recipe(tmp_path, "p", "plain")
    r_joint = _panel_recipe(tmp_path, "j", "joint")
    sources = {
        str(r_plain): {"xy_mm": (0, 0), "size_mm": (80, 35)},
        str(r_joint): {"xy_mm": (0, 37), "size_mm": (80, 80)},
    }
    comp, _ = fr.compose(sources, canvas_size_mm=(82, 119))
    out = tmp_path / "composite.png"
    # Act -- validate=True reproduces the saved figure and compares; raised pre-#193
    fr.save(comp, out, validate=True, verbose=False)
    # Assert
    assert out.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
