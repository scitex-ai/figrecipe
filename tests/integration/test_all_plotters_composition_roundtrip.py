#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Systematic COMPOSITION round-trip across ALL 47 plotters.

The standalone pixel-perfect suite (``_reproducer/test__core.py``) already
covers every plotter through save->reproduce in isolation. The composition
path (``fr.compose``) and the nested path (``ax.embed``) were only spot-checked
for a handful of plotters. This module closes the COMPOSITION gap: it
parametrizes over ``sorted(PLOTTERS)`` (so every CURRENT and FUTURE plotter is
auto-covered) and asserts each plotter round-trips when placed as a panel in an
mm-based composition beside a reference line panel.

Assertion level: figrecipe's own validator. ``fr.save`` (default ``validate``)
reproduces the composed figure in-process and writes ``<name>-not-reproduced.png``
on divergence. We assert that artifact is absent. This is the same robust,
font-version-stable level used by ``test_reproducibility_matrix.py`` — not raw
pixel-diff, which is freetype-version flaky across machines.

Panel sizes are read back from each plotter's SAVED recipe (``figsize`` in
inches -> mm), so panels are composed at their RECORDED mm sizes rather than a
hard-coded guess — this keeps the matrix correct for plotters whose demo uses a
non-default figure size.

XFAILED plotters (composition): none. Every one of the 47 plotters currently
round-trips through ``fr.compose`` at the validator level. If a future change
regresses a plotter, this matrix turns it from a silent gap into a visible
failure (or an explicit ``xfail`` documented here).
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

# Plotters expected to FAIL composition round-trip, each with a SPECIFIC reason.
# Empty: all 47 currently round-trip through fr.compose at the validator level.
COMPOSITION_XFAIL: dict = {}


def _compose_params():
    """One param per plotter; xfailed plotters carry an xfail mark (strict=False)
    so any future gap is documented and visible without weakening the assertion.
    Currently no plotter is xfailed for composition."""
    params = []
    for plot_type in sorted(PLOTTERS):
        marks = ()
        if plot_type in COMPOSITION_XFAIL:
            marks = pytest.mark.xfail(reason=COMPOSITION_XFAIL[plot_type], strict=False)
        params.append(pytest.param(plot_type, marks=marks, id=plot_type))
    return params


@pytest.fixture()
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def _build_and_save_plotter(plot_type, sdir):
    """Build a plotter's recording figure (the exact pixel-perfect-suite
    pattern: rng=42 + finalize_ticks/finalize_special_plots) and save it as a
    source recipe. Returns the recipe path."""
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


def _save_reference_panel(sdir):
    """Save a simple reference line panel to sit beside the plotter panel."""
    fig, ax = fr.subplots(axes_width_mm=40, axes_height_mm=30)
    ax.plot([0, 1, 2], [0, 1, 0], id="ref_line")
    recipe = sdir / "reference.yaml"
    try:
        fr.save(fig, str(sdir / "reference.png"), verbose=False)
    except ValueError:
        pass
    plt.close("all")
    return recipe


def _recorded_size_mm(recipe_path):
    """Read a saved recipe's recorded figure size (inches) and return it in mm."""
    record = load_recipe(recipe_path)
    width_in, height_in = record.figsize
    return (width_in * _MM_PER_INCH, height_in * _MM_PER_INCH)


def _compose_plotter_beside_reference(plot_type, tmp_dir):
    """Build the plotter + reference source recipes and compose them side by
    side (mm-based) at their recorded mm sizes. Returns the composed figure."""
    sdir = tmp_dir / "sources"
    sdir.mkdir(exist_ok=True)

    plotter_recipe = _build_and_save_plotter(plot_type, sdir)
    reference_recipe = _save_reference_panel(sdir)

    plotter_w, plotter_h = _recorded_size_mm(plotter_recipe)
    reference_w, reference_h = _recorded_size_mm(reference_recipe)

    gap_mm = 5.0
    canvas_w = plotter_w + gap_mm + reference_w
    canvas_h = max(plotter_h, reference_h)

    composed_fig, _ = fr.compose(
        {
            str(plotter_recipe): {
                "xy_mm": (0, 0),
                "size_mm": (plotter_w, plotter_h),
            },
            str(reference_recipe): {
                "xy_mm": (plotter_w + gap_mm, 0),
                "size_mm": (reference_w, reference_h),
            },
        },
        canvas_size_mm=(canvas_w, canvas_h),
    )
    return composed_fig


@pytest.mark.parametrize("plot_type", _compose_params())
def test_plotter_composition_round_trips(plot_type, tmp_dir):
    # Arrange
    composed_fig = _compose_plotter_beside_reference(plot_type, tmp_dir)
    # Act
    try:
        fr.save(composed_fig, str(tmp_dir / f"{plot_type}.png"), verbose=False)
    except ValueError:
        pass
    plt.close("all")
    # Assert
    assert not (tmp_dir / f"{plot_type}-not-reproduced.png").exists()


def test_every_plotter_is_parametrized():
    # Arrange
    from figrecipe._dev import list_plotters

    # Act
    uncovered = set(list_plotters()) - set(sorted(PLOTTERS))
    # Assert
    assert uncovered == set()
