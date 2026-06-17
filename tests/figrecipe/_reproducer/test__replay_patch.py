#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-trip tests for ``add_patch`` recording + replay.

``ax.add_patch`` was previously dropped (not in PLOTTING/DECORATION_METHODS, no
replay handler) so any schematic patch silently vanished on reproduce. These
guard that a patch is recorded into the recipe and reconstructed on replay.

Pixel-MSE here is measured as a *delta over the plot-only baseline* rather than
an absolute threshold: the absolute baseline depends on the host's font/freetype
(a bare ``fr.subplots()+plot`` already diverges on some dev hosts), but the patch
must not add divergence on top of it -- that part is host-independent.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import yaml

import figrecipe as fr
from figrecipe._quality._validator import validate_recipe


def _mpl_ax(ax):
    return ax.ax if hasattr(ax, "ax") else ax


def _decorations(recipe_path):
    data = yaml.safe_load(recipe_path.read_text())
    return [
        call
        for ax_record in data["axes"].values()
        for call in ax_record.get("decorations", [])
    ]


def _patch_classes(ax):
    return sorted(type(p).__name__ for p in _mpl_ax(ax).patches)


def _mse(fig, recipe_path):
    res = validate_recipe(fig, str(recipe_path), mse_threshold=1e12)
    return res.mse if res.mse is not None else 0.0


def _rect_recipe(tmp_path):
    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 0], id="line")
    ax.add_patch(
        mpatches.Rectangle((0.5, 0.2), 1.0, 0.4, facecolor="orange", edgecolor="k")
    )
    recipe = tmp_path / "rect.yaml"
    fr.save(fig, recipe, validate=False, verbose=False)
    return recipe


def test_add_patch_recorded_as_decoration(tmp_path):
    # Arrange
    recipe = _rect_recipe(tmp_path)
    # Act
    patch_calls = [c for c in _decorations(recipe) if c["function"] == "add_patch"]
    descriptor = patch_calls[0]["kwargs"] if patch_calls else {}
    # Assert
    assert (
        len(patch_calls),
        descriptor.get("patch_class"),
        descriptor.get("geom", {}).get("width"),
        descriptor.get("geom", {}).get("height"),
    ) == (1, "Rectangle", 1.0, 0.4)


def test_add_patch_all_shapes_reproduce(tmp_path):
    # Arrange -- one of each handled class + a generic (FancyBboxPatch->PathPatch)
    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 0], id="line")
    ax.add_patch(mpatches.Rectangle((0.3, 0.2), 0.6, 0.4, facecolor="orange"))
    ax.add_patch(mpatches.Circle((1.5, 0.5), 0.2, facecolor="red"))
    ax.add_patch(mpatches.Ellipse((0.6, 0.8), 0.4, 0.2, angle=15, facecolor="green"))
    ax.add_patch(mpatches.Polygon([[1.0, 0.1], [1.3, 0.4], [1.0, 0.6]], facecolor="b"))
    ax.add_patch(
        mpatches.FancyBboxPatch((0.1, 0.05), 0.3, 0.1, boxstyle="round", facecolor="c")
    )
    recipe = tmp_path / "shapes.yaml"
    fr.save(fig, recipe, validate=False, verbose=False)
    # Act
    _fig2, ax2 = fr.reproduce(recipe)
    # Assert -- all five reproduced (FancyBboxPatch via the PathPatch fallback)
    assert _patch_classes(ax2) == [
        "Circle",
        "Ellipse",
        "PathPatch",
        "Polygon",
        "Rectangle",
    ]


def test_add_patch_circle_geometry_reproduced(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 0], id="line")
    ax.add_patch(mpatches.Circle((1.25, 0.5), 0.3, facecolor="none", edgecolor="red"))
    recipe = tmp_path / "circle.yaml"
    fr.save(fig, recipe, validate=False, verbose=False)
    # Act
    _fig2, ax2 = fr.reproduce(recipe)
    (circle,) = [p for p in _mpl_ax(ax2).patches if type(p).__name__ == "Circle"]
    # Assert -- centre + radius survived the round trip
    assert (
        tuple(round(v, 6) for v in circle.get_center()),
        round(circle.get_radius(), 6),
    ) == ((1.25, 0.5), 0.3)


def test_add_patch_adds_no_divergence_over_baseline(tmp_path):
    # Arrange -- baseline (plot only) vs the same plot + patches
    fig0, ax0 = fr.subplots()
    ax0.plot([0, 1, 2], [0, 1, 0], id="line")
    r0 = tmp_path / "base.yaml"
    fr.save(fig0, r0, validate=False, verbose=False)
    fig1, ax1 = fr.subplots()
    ax1.plot([0, 1, 2], [0, 1, 0], id="line")
    ax1.add_patch(
        mpatches.Rectangle((0.5, 0.2), 1.0, 0.4, facecolor="orange", edgecolor="k")
    )
    ax1.add_patch(
        mpatches.Polygon([[0.2, 0.6], [0.6, 0.9], [0.2, 0.95]], facecolor="g")
    )
    r1 = tmp_path / "patched.yaml"
    fr.save(fig1, r1, validate=False, verbose=False)
    # Act
    delta = _mse(fig1, r1) - _mse(fig0, r0)
    # Assert -- patches reproduce: no divergence over baseline (full patch pre-fix)
    assert delta <= 80.0
