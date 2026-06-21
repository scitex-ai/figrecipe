#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproducibility completeness: a recipe must reproduce PIXEL-IDENTICALLY in a
FRESH rcParams context (i.e. a new process).

Core principle (no silent fallback): everything that affected the rendered
figure must be captured in the recipe AS PRIMITIVES and restored on replay --
the active theme (e.g. SCITEX_STYLE loaded into rcParams), explicitly-specified
values, AND any globally-set rcParam. To prove the recipe is self-sufficient
(not silently leaning on ambient state), each test resets matplotlib.rcParams to
the library defaults BETWEEN save and reproduce, then asserts the reproduction
is pixel-identical (MSE == 0) at the same size. Any reliance on an uncaptured
rcParam surfaces as MSE > 0 -- fail loud, no resize/tolerance fallback.

The autouse rcParams isolation in conftest restores global rcParams after each
test, so mutating them here is safe.
"""

import matplotlib as mpl

mpl.use("Agg")
import numpy as np
import pytest

import figrecipe as fr
from figrecipe._utils._image_diff import compare_images


def _titled_line_fig():
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.plot([0, 1, 2, 3], [0, 1, 4, 9])
    ax.set_title("Reproducibility")
    ax.set_xlabel("phase f (Hz)")
    ax.set_ylabel("amp f (Hz)")
    return fig


def _imshow_fig():
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.imshow(
        np.linspace(0, 1, 225).reshape(15, 15),
        origin="lower",
        aspect="auto",
        extent=(2.0, 30.0, 60.0, 180.0),
        cmap="hot",
    )
    ax.set_xyt("phase f (Hz)", "amp f (Hz)", "comodulogram")
    ax.set_xticks([8, 16, 24], labels=["8", "16", "24"])
    return fig


def _bar_log_fig():
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.bar([0, 1, 2, 3], [10, 1000, 50, 7000])
    ax.set_yscale("log")
    ax.set_title("throughput")
    return fig


def _fresh_context_roundtrip_mse(make_fig, rc, tmp_path, dpi=150):
    """Build under ambient ``rc``, save (record), wipe rcParams to library
    defaults (simulate a new process), reproduce, and return the pixel MSE
    between original and reproduction (both rendered at ``dpi`` via the same
    RecordingFigure.savefig path). Returns +inf on any size mismatch -- a size
    divergence is a hard failure, never silently compared on a cropped overlap.
    """
    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.rcParams.update(rc)
    fig = make_fig()
    fr.save(fig, str(tmp_path / "orig.png"), validate=False)
    fig.savefig(str(tmp_path / "o.png"), save_recipe=False, dpi=dpi, verbose=False)

    mpl.rcParams.update(mpl.rcParamsDefault)  # brand-new-process simulation
    rfig, _ = fr.reproduce(str(tmp_path / "orig.yaml"))
    rfig.savefig(str(tmp_path / "r.png"), save_recipe=False, dpi=dpi, verbose=False)

    diff = compare_images(str(tmp_path / "o.png"), str(tmp_path / "r.png"))
    return diff["mse"] if diff["same_size"] else float("inf")


# rcParams set globally (e.g. by a theme / SCITEX_STYLE / user) that lie OUTSIDE
# figrecipe's curated style schema -- the recipe must still capture+restore them.
GLOBAL_RCPARAMS = [
    {"axes.titleweight": "bold"},
    {"font.weight": "bold"},
    {"font.style": "italic"},
    {"axes.titlecolor": "#aa0000"},
    {"lines.linestyle": "--"},
    {"xtick.minor.visible": True, "ytick.minor.visible": True},
    {"xtick.direction": "in", "ytick.direction": "in"},
    {"axes.titlesize": 20.0},
]

# A bundle standing in for a loaded theme (SCITEX_STYLE-like): several non-default
# rcParams at once. The recipe must persist these as primitives, not a name.
THEME_BUNDLE = {
    "axes.titleweight": "bold",
    "font.style": "italic",
    "xtick.direction": "in",
    "ytick.direction": "in",
    "axes.titlesize": 18.0,
}


@pytest.mark.parametrize("rc", GLOBAL_RCPARAMS, ids=lambda r: "+".join(sorted(r)))
def test_global_rcparam_reproduces_pixel_identical(rc, tmp_path):
    # Arrange
    make = _titled_line_fig
    # Act
    mse = _fresh_context_roundtrip_mse(make, rc, tmp_path)
    # Assert
    assert mse == 0.0


def test_loaded_theme_reproduces_pixel_identical(tmp_path):
    # Arrange
    make = _titled_line_fig
    # Act
    mse = _fresh_context_roundtrip_mse(make, THEME_BUNDLE, tmp_path)
    # Assert
    assert mse == 0.0


def test_imshow_under_global_rcparam_reproduces_pixel_identical(tmp_path):
    # Arrange
    rc = {"axes.titleweight": "bold", "font.style": "italic"}
    # Act
    mse = _fresh_context_roundtrip_mse(_imshow_fig, rc, tmp_path)
    # Assert
    assert mse == 0.0


def test_bar_logscale_under_global_rcparam_reproduces_pixel_identical(tmp_path):
    # Arrange
    rc = {"axes.titleweight": "bold", "xtick.minor.visible": True}
    # Act
    mse = _fresh_context_roundtrip_mse(_bar_log_fig, rc, tmp_path)
    # Assert
    assert mse == 0.0


def test_default_rcparams_reproduces_pixel_identical(tmp_path):
    # Arrange
    make = _titled_line_fig
    # Act
    mse = _fresh_context_roundtrip_mse(make, {}, tmp_path)
    # Assert
    assert mse == 0.0
