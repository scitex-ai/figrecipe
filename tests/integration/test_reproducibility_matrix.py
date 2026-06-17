#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Systematic save->reproduce reproducibility matrix.

Every gap fixed this round (add_patch, insets, embed) was the SAME bug class: a
construct accepted by figrecipe but not replayed, so it was silently dropped on
reproduce. Rather than one ad-hoc test per construct, this module tests the
PROPERTY (a figure round-trips through save->reproduce) over a registry of
construct *atoms* and curated *combinations* (the seams where interactions break:
sub-panel x content x transform). Adding coverage = one SCENARIOS entry.

Assertion level: figrecipe's own validator (no ``*-not-reproduced`` artifact),
which compares original vs reproduced in-process (version-consistent) — robust,
unlike raw pixel-diff==0 which is freetype/font-version flaky across machines.

The 47 plot-type builders already have a pixel-perfect suite
(``_reproducer/test__core.py``); ``test_every_recorded_plot_type_has_a_builder``
guards that that registry stays complete, so this module focuses on the
non-plot constructs and combinations.
"""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pytest

import figrecipe as fr


@pytest.fixture()
def tmp_path_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def _fig():
    fig, ax = fr.subplots(axes_width_mm=70, axes_height_mm=50)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return fig, ax


def _save_source(tmp, name, build):
    """Build + save a source recipe (in a subdir so its artifacts don't pollute
    the top-level not-reproduced check) and return its .yaml path."""
    sdir = tmp / "sources"
    sdir.mkdir(exist_ok=True)
    sfig, sax = fr.subplots(axes_width_mm=40, axes_height_mm=30)
    build(sax)
    try:
        fr.save(sfig, str(sdir / f"{name}.png"))
    except ValueError:
        pass
    plt.close("all")
    return sdir / f"{name}.yaml"


# --- atoms: non-plot constructs -------------------------------------------


def atom_patch_rectangle(tmp):
    fig, ax = _fig()
    ax.add_patch(
        mpatches.Rectangle(
            (0.2, 0.2), 0.5, 0.4, facecolor="red", edgecolor="k", linewidth=2
        )
    )
    return fig


def atom_patch_circle(tmp):
    fig, ax = _fig()
    ax.add_patch(mpatches.Circle((0.5, 0.5), 0.25, facecolor="blue", alpha=0.6))
    return fig


def atom_patch_ellipse(tmp):
    fig, ax = _fig()
    ax.add_patch(mpatches.Ellipse((0.5, 0.5), 0.6, 0.3, angle=20, facecolor="green"))
    return fig


def atom_patch_polygon(tmp):
    fig, ax = _fig()
    ax.add_patch(
        mpatches.Polygon([(0.1, 0.1), (0.9, 0.2), (0.5, 0.9)], facecolor="orange")
    )
    return fig


def atom_inset_imshow(tmp):
    fig, ax = fr.subplots(axes_width_mm=70, axes_height_mm=50)
    ax.plot([0, 1, 2], [0, 1, 0])
    axins = ax.inset_axes([0.6, 0.6, 0.35, 0.35])
    axins.imshow(np.arange(25).reshape(5, 5))
    return fig


# --- combinations: the seams where interactions break ---------------------


def combo_plot_inset_patch(tmp):
    fig, ax = _fig()
    ax.plot([0, 1], [0, 1])
    ax.add_patch(mpatches.Rectangle((0.1, 0.1), 0.3, 0.2, facecolor="red"))
    axins = ax.inset_axes([0.55, 0.55, 0.4, 0.4])
    axins.imshow(np.arange(16).reshape(4, 4))
    return fig


def combo_embed_recipe(tmp):
    src = _save_source(tmp, "plot", lambda ax: ax.plot([0, 1, 2], [2, 1, 0]))
    fig, ax = _fig()
    ax.plot([0, 1, 2], [0, 1, 0])
    ax.embed(str(src), bounds=[0.55, 0.1, 0.4, 0.4])
    return fig


def combo_embed_diagram(tmp):
    d = fr.Diagram(title="m", width_mm=60, height_mm=40)
    d.add_box("a", "A")
    d.add_box("b", "B")
    d.add_arrow("a", "b")
    src = _save_source(tmp, "diag", lambda ax: ax.diagram(d))
    fig, ax = _fig()
    ax.plot([0, 1, 2], [0, 1, 0])
    ax.embed(str(src), bounds=[0.05, 0.5, 0.45, 0.45])
    return fig


def combo_embed_composed(tmp):
    sdir = tmp / "sources"
    sdir.mkdir(exist_ok=True)
    a, aa = fr.subplots(axes_width_mm=40, axes_height_mm=30)
    aa.plot([0, 1, 2], [2, 1, 0])
    b, bb = fr.subplots(axes_width_mm=40, axes_height_mm=30)
    bb.imshow(np.arange(9).reshape(3, 3))
    for f, fig_ in (("pa", a), ("pb", b)):
        try:
            fr.save(fig_, str(sdir / f"{f}.png"))
        except ValueError:
            pass
    plt.close("all")
    comp, _ = fr.compose(
        {
            str(sdir / "pa.yaml"): {"xy_mm": (0, 0), "size_mm": (40, 30)},
            str(sdir / "pb.yaml"): {"xy_mm": (0, 33), "size_mm": (40, 30)},
        },
        canvas_size_mm=(42, 65),
    )
    cpath = sdir / "comp.yaml"
    try:
        comp.save_recipe(cpath)
    except ValueError:
        pass
    plt.close("all")
    fig, ax = _fig()
    ax.plot([0, 1, 2], [0, 1, 0])
    ax.embed(str(cpath), bounds=[0.05, 0.05, 0.5, 0.9])
    return fig


SCENARIOS = [
    ("patch_rectangle", atom_patch_rectangle),
    ("patch_circle", atom_patch_circle),
    ("patch_ellipse", atom_patch_ellipse),
    ("patch_polygon", atom_patch_polygon),
    ("inset_imshow", atom_inset_imshow),
    ("plot_inset_patch", combo_plot_inset_patch),
    ("embed_recipe", combo_embed_recipe),
    ("embed_diagram", combo_embed_diagram),
    ("embed_composed", combo_embed_composed),
]


@pytest.mark.parametrize("name,builder", SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_scenario_round_trips(name, builder, tmp_path_dir):
    # Arrange
    fig = builder(tmp_path_dir)
    out = tmp_path_dir / f"{name}.png"
    # Act
    try:
        fr.save(fig, str(out))
    except ValueError:
        pass
    plt.close("all")
    # Assert
    assert not (tmp_path_dir / f"{name}-not-reproduced.png").exists()


def test_every_recorded_plot_type_has_a_builder():
    # Arrange
    from figrecipe._dev import list_plotters
    from figrecipe._params import PLOTTING_METHODS

    # Act
    missing = set(PLOTTING_METHODS) - set(list_plotters())
    # Assert
    assert missing == set()
