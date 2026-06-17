#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Systematic NESTED-composition round-trip across ALL 47 plotters.

Companion to ``test_all_plotters_composition_roundtrip.py``. Where that module
tests panel composition (``fr.compose``), this one tests NESTING via
``ax.embed`` — drawing a plotter's recipe as a managed sub-panel (inset
substrate) inside a host figure that round-trips through save->reproduce.

Two matrices:

1. ``test_plotter_single_embed_round_trips`` — parametrized over ``sorted(PLOTTERS)``
   so EVERY current and future plotter is covered. A plotter's source recipe is
   embedded as one managed sub-panel of a host line figure; the host is then
   saved with figrecipe's validator (``fr.save`` reproduces in-process and writes
   ``<name>-not-reproduced.png`` on divergence). We assert that artifact is
   absent.

2. ``test_plotter_compose_of_composed_round_trips`` — TRUE nesting: a plotter
   panel is first put into a ``fr.compose`` recipe, and that COMPOSED recipe is
   then ``ax.embed``-ed into a host (embed-of-composed → each inner panel becomes
   a nested sub-panel). Done for a representative subset (full-47 single embed is
   already covered by matrix 1; compose-of-composed over all 47 is excessive).

Assertion level: figrecipe's own validator (no ``-not-reproduced`` artifact) —
robust against freetype/font-version pixel flakiness, same level as
``test_reproducibility_matrix.py``.

XFAILED plotters (nesting):
  - ``streamplot`` (single embed): the inset/embed replay path does not coerce
    the YAML-deserialized streamplot coordinate arrays (loaded as ruamel
    ``CommentedSeq``) back to numpy before ``Axes.streamplot`` accesses
    ``.shape``. The embedded sub-panel therefore fails to redraw on reproduce
    (``UserWarning: Failed to replay streamplot: 'CommentedSeq' object has no
    attribute 'shape'``) and validation fails (MSE ~1639 >> threshold 100, the
    diff concentrated exactly in the embedded sub-panel's region). NOTE: the SAME
    streamplot round-trips fine standalone (pixel-perfect suite) AND through
    ``fr.compose`` AND through embed-OF-a-composed-recipe — the gap is specific
    to embedding a single streamplot recipe directly. Marked ``strict=False`` so
    a future source-side fix (coerce list args in the inset replay path) flips it
    green without editing this test.
"""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import figrecipe as fr
from figrecipe._dev import PLOTTERS
from figrecipe._serializer import load_recipe
from figrecipe.styles._finalize import finalize_special_plots, finalize_ticks

_MM_PER_INCH = 25.4

# Plotters expected to FAIL the SINGLE-embed round-trip, each with a reason.
SINGLE_EMBED_XFAIL = {
    "streamplot": (
        "embed/inset replay does not coerce YAML-loaded streamplot arrays "
        "(ruamel CommentedSeq) to numpy before Axes.streamplot needs .shape; "
        "embedded sub-panel fails to redraw on reproduce "
        "(UserWarning: Failed to replay streamplot: 'CommentedSeq' object has "
        "no attribute 'shape') -> validation MSE ~1639 >> 100. Standalone, "
        "compose, and embed-of-composed all round-trip; only direct single "
        "embed of a streamplot recipe regresses."
    ),
}


def _embed_params():
    """One param per plotter; xfailed plotters carry an xfail mark (strict=False)
    so the gap is documented and visible without weakening the assertion."""
    params = []
    for plot_type in sorted(PLOTTERS):
        marks = ()
        if plot_type in SINGLE_EMBED_XFAIL:
            marks = pytest.mark.xfail(
                reason=SINGLE_EMBED_XFAIL[plot_type], strict=False
            )
        params.append(pytest.param(plot_type, marks=marks, id=plot_type))
    return params


# Representative subset for the (heavier) compose-of-composed matrix. Covers
# line/bar/scatter/image/distribution/special families plus streamplot (which
# fails single embed but round-trips through embed-of-composed).
COMPOSE_OF_COMPOSED_SUBSET = [
    "bar",
    "boxplot",
    "contourf",
    "errorbar",
    "hist",
    "imshow",
    "pie",
    "plot",
    "scatter",
    "stem",
    "streamplot",
    "violinplot",
]


@pytest.fixture()
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def _build_and_save_plotter(plot_type, sdir):
    """Build a plotter's recording figure (pixel-perfect-suite pattern:
    rng=42 + finalize_ticks/finalize_special_plots) and save it as a source
    recipe. Returns the recipe path."""
    rng = np.random.default_rng(42)
    fig, ax = PLOTTERS[plot_type](fr, rng)
    style = fig._recorder.figure_record.style or {}
    axes_list = fig.flat if hasattr(fig, "flat") else [ax]
    for a in axes_list:
        mpl_ax = getattr(a, "_ax", a)
        finalize_ticks(mpl_ax)
        finalize_special_plots(mpl_ax, style)
    recipe = sdir / f"{plot_type}.yaml"
    try:
        fr.save(fig, str(sdir / f"{plot_type}.png"), verbose=False)
    except ValueError:
        pass
    plt.close("all")
    return recipe


def _save_reference_panel(sdir, name="reference"):
    """Save a simple reference line panel."""
    fig, ax = fr.subplots(axes_width_mm=40, axes_height_mm=30)
    ax.plot([0, 1, 2], [0, 1, 0], id="ref_line")
    recipe = sdir / f"{name}.yaml"
    try:
        fr.save(fig, str(sdir / f"{name}.png"), verbose=False)
    except ValueError:
        pass
    plt.close("all")
    return recipe


def _recorded_size_mm(recipe_path):
    """Read a saved recipe's recorded figure size (inches) and return it in mm."""
    record = load_recipe(recipe_path)
    width_in, height_in = record.figsize
    return (width_in * _MM_PER_INCH, height_in * _MM_PER_INCH)


def _compose_plotter_beside_reference(plot_type, sdir):
    """Compose the plotter recipe beside a reference panel (mm-based) at their
    recorded sizes, then save the COMPOSED recipe. Returns its path."""
    plotter_recipe = _build_and_save_plotter(plot_type, sdir)
    reference_recipe = _save_reference_panel(sdir)

    plotter_w, plotter_h = _recorded_size_mm(plotter_recipe)
    reference_w, reference_h = _recorded_size_mm(reference_recipe)

    gap_mm = 5.0
    composed_fig, _ = fr.compose(
        {
            str(plotter_recipe): {"xy_mm": (0, 0), "size_mm": (plotter_w, plotter_h)},
            str(reference_recipe): {
                "xy_mm": (plotter_w + gap_mm, 0),
                "size_mm": (reference_w, reference_h),
            },
        },
        canvas_size_mm=(plotter_w + gap_mm + reference_w, max(plotter_h, reference_h)),
    )
    composed_recipe = sdir / f"{plot_type}_composed.yaml"
    try:
        composed_fig.save_recipe(composed_recipe)
    except ValueError:
        pass
    plt.close("all")
    return composed_recipe


@pytest.mark.parametrize("plot_type", _embed_params())
def test_plotter_single_embed_round_trips(plot_type, tmp_dir):
    # Arrange
    sdir = tmp_dir / "sources"
    sdir.mkdir(exist_ok=True)
    source_recipe = _build_and_save_plotter(plot_type, sdir)
    host_fig, host_ax = fr.subplots(axes_width_mm=120, axes_height_mm=90)
    host_ax.plot([0, 1, 2, 3], [3, 2, 1, 0], id="host_line")
    host_ax.embed(str(source_recipe), bounds=[0.5, 0.5, 0.45, 0.45])
    # Act
    try:
        fr.save(host_fig, str(tmp_dir / f"{plot_type}.png"), verbose=False)
    except ValueError:
        pass
    plt.close("all")
    # Assert
    assert not (tmp_dir / f"{plot_type}-not-reproduced.png").exists()


@pytest.mark.parametrize(
    "plot_type", COMPOSE_OF_COMPOSED_SUBSET, ids=COMPOSE_OF_COMPOSED_SUBSET
)
def test_plotter_compose_of_composed_round_trips(plot_type, tmp_dir):
    # Arrange
    sdir = tmp_dir / "sources"
    sdir.mkdir(exist_ok=True)
    composed_recipe = _compose_plotter_beside_reference(plot_type, sdir)
    host_fig, host_ax = fr.subplots(axes_width_mm=160, axes_height_mm=110)
    host_ax.plot([0, 1, 2, 3], [3, 2, 1, 0], id="host_line")
    host_ax.embed(str(composed_recipe), bounds=[0.45, 0.45, 0.5, 0.5])
    # Act
    try:
        fr.save(host_fig, str(tmp_dir / f"{plot_type}.png"), verbose=False)
    except ValueError:
        pass
    plt.close("all")
    # Assert
    assert not (tmp_dir / f"{plot_type}-not-reproduced.png").exists()


def test_compose_of_composed_subset_is_valid():
    # Arrange
    subset = set(COMPOSE_OF_COMPOSED_SUBSET)
    # Act
    unknown = subset - set(PLOTTERS)
    # Assert
    assert unknown == set()


def test_every_plotter_is_parametrized_for_embed():
    # Arrange
    from figrecipe._dev import list_plotters

    # Act
    uncovered = set(list_plotters()) - set(sorted(PLOTTERS))
    # Assert
    assert uncovered == set()
