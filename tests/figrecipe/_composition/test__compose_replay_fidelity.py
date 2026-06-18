#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for mm-compose replay fidelity.

Covers two previously-broken panel types when composed via mm-based
``compose`` (smart recipe composer):

1. MULTI-AXES figures (e.g. ``subplots(nrows=3, ncols=1)``) used to replay as
   only the first axes; the other subplots were dropped because mm-compose only
   fetched the default axes key from the source recipe.

2. ``make_axes_locatable`` MARGINALS (``stx_scatter_hist``) used to vanish on
   replay because ``stx_*`` methods were dispatched via ``getattr`` on a raw
   matplotlib axes (which lacks them), silently dropping the call.
"""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest

import figrecipe as fr


@pytest.fixture
def stacked_composed(tmp_path):
    """Compose a 3-row source recipe into a single mm panel."""
    fig, axes = fr.subplots(nrows=3, ncols=1)
    for i, ax in enumerate(np.ravel(axes)):
        ax.plot([0, 1, 2], [i, i + 1, i], id=f"line_{i}")
    recipe = tmp_path / "stacked.yaml"
    fr.save(fig, recipe, validate=False, verbose=False)

    sources = {str(recipe): {"xy_mm": (0, 0), "size_mm": (80, 80)}}
    comp_fig, _ = fr.compose(sources, canvas_size_mm=(90, 90))
    return comp_fig.fig if hasattr(comp_fig, "fig") else comp_fig


@pytest.fixture
def joint_composed(tmp_path):
    """Compose an stx_scatter_hist source recipe into a single mm panel."""
    rng = np.random.default_rng(0)
    x = rng.normal(size=200)
    y = rng.normal(size=200)

    fig, ax = fr.subplots()
    ax.stx_scatter_hist(x, y, kde=True, id="sh")
    recipe = tmp_path / "joint.yaml"
    fr.save(fig, recipe, validate=False, verbose=False)

    sources = {str(recipe): {"xy_mm": (0, 0), "size_mm": (80, 80)}}
    comp_fig, _ = fr.compose(sources, canvas_size_mm=(90, 90))
    return comp_fig.fig if hasattr(comp_fig, "fig") else comp_fig


def test_multiaxes_source_places_all_three_subplots(stacked_composed):
    # Arrange
    mpl = stacked_composed
    # Act
    n_axes = len(mpl.get_axes())
    # Assert
    assert n_axes == 3


def test_multiaxes_subplots_each_keep_their_line(stacked_composed):
    # Arrange
    mpl = stacked_composed
    # Act
    line_counts = [len(a.lines) for a in mpl.get_axes()]
    # Assert
    assert all(n >= 1 for n in line_counts)


def test_multiaxes_subplots_are_vertically_stacked(stacked_composed):
    # Arrange
    mpl = stacked_composed
    # Act
    bottoms = sorted(a.get_position().y0 for a in mpl.get_axes())
    # Assert
    assert bottoms[0] < bottoms[1] < bottoms[2]


def test_scatter_hist_creates_main_plus_two_marginals(joint_composed):
    # Arrange
    mpl = joint_composed
    # Act
    n_axes = len(mpl.get_axes())
    # Assert
    assert n_axes >= 3


def test_scatter_hist_scatter_collection_present(joint_composed):
    # Arrange
    mpl = joint_composed
    # Act
    has_scatter = any(len(a.collections) >= 1 for a in mpl.get_axes())
    # Assert
    assert has_scatter


def test_scatter_hist_kde_marginal_lines_present(joint_composed):
    # Arrange
    mpl = joint_composed
    # Act
    has_marginal_lines = any(len(a.lines) >= 1 for a in mpl.get_axes())
    # Assert
    assert has_marginal_lines


@pytest.fixture
def labeled_imshow_recipe(tmp_path):
    """Save a labelled imshow source (axis labels, no explicit ticks)."""
    fig, ax = fr.subplots()
    ax.imshow(np.random.RandomState(0).rand(20, 20), aspect="auto", id="img")
    ax.set_xyt("Phase frequency (Hz)", "Amplitude frequency (Hz)", "Comodulogram")
    recipe = tmp_path / "labeled_imshow.yaml"
    fr.save(fig, recipe, validate=False, verbose=False)
    return recipe


def _imshow_panel(mpl_fig):
    """Return the composed axes that carries an image."""
    return next(a for a in mpl_fig.get_axes() if a.get_images())


def test_composed_labeled_imshow_suppresses_auto_ticks(labeled_imshow_recipe):
    # A labelled imshow with no explicit ticks: the live ax.imshow wrapper hides
    # imshow ticks at draw, but compose replays raw matplotlib (wrapper bypassed)
    # so without finalize the composed LIVE panel kept auto ticks that reproduce
    # then dropped -> tile-gutter pixel divergence (NeuroVista fig02 composite).
    # After the fix the composed live panel suppresses them, matching reproduce.
    # Arrange
    sources = {str(labeled_imshow_recipe): {"xy_mm": (0, 0), "size_mm": (80, 80)}}
    # Act
    comp_fig, _ = fr.compose(sources, canvas_size_mm=(90, 90))
    mpl = comp_fig.fig if hasattr(comp_fig, "fig") else comp_fig
    panel = _imshow_panel(mpl)
    # Assert
    assert list(panel.get_xticks()) == [] and list(panel.get_yticks()) == []


def test_composed_labeled_imshow_keeps_explicit_ticks(tmp_path):
    # A deliberately-labelled comodulogram (explicit Hz-band set_xticks) must
    # KEEP its ticks through composition -- finalize_imshow_axes suppresses only
    # the axis dims the recipe did not explicitly tick.
    # Arrange
    fig, ax = fr.subplots()
    ax.imshow(np.random.RandomState(0).rand(20, 20), aspect="auto", id="img")
    ax.set_xyt("Phase (Hz)", "Amp (Hz)", "Comodulogram")
    ax.set_xticks([2, 6, 12])
    recipe = tmp_path / "explicit.yaml"
    fr.save(fig, recipe, validate=False, verbose=False)
    sources = {str(recipe): {"xy_mm": (0, 0), "size_mm": (80, 80)}}
    # Act
    comp_fig, _ = fr.compose(sources, canvas_size_mm=(90, 90))
    mpl = comp_fig.fig if hasattr(comp_fig, "fig") else comp_fig
    panel = _imshow_panel(mpl)
    # Assert
    assert list(panel.get_xticks()) == [2, 6, 12]


def test_composed_labeled_imshow_live_matches_reproduce(
    labeled_imshow_recipe, tmp_path
):
    # The reported bug directly: a composed labelled imshow diverged from its
    # reproduction in the tick gutters. Guard the invariant -- the live composed
    # panel and the reproduced one must agree on imshow tick state.
    # Arrange
    sources = {str(labeled_imshow_recipe): {"xy_mm": (0, 0), "size_mm": (80, 80)}}
    comp_fig, _ = fr.compose(sources, canvas_size_mm=(90, 90))
    live = comp_fig.fig if hasattr(comp_fig, "fig") else comp_fig
    live_ticks = list(_imshow_panel(live).get_xticks())
    composed_recipe = tmp_path / "composed.yaml"
    fr.save(comp_fig, composed_recipe, validate=False, verbose=False)
    # Act
    rfig, _ = fr.reproduce(composed_recipe)
    rmpl = rfig.fig if hasattr(rfig, "fig") else rfig
    repro_ticks = list(_imshow_panel(rmpl).get_xticks())
    # Assert
    assert live_ticks == repro_ticks


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
