#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Draw-count invariance of the reproduced pixel SIZE (deterministic content crop).

The save path RE-MEASURES ink at save time -- ``bbox_inches="tight"`` for
constrained_layout figures (matplotlib re-fetches ``get_tightbbox`` in
``print_figure``) and the content-aware pixel ``crop()`` for composed mm-layout
figures. That re-measure jitters sub-pixel between the ORIGINAL figure (drawn
many times during build/save) and a fresh ``reproduce()``-d one (drawn a few
times); at a pixel-rounding boundary a 0.2 px shift flips the saved width by
1 px, and the validator's ``size_tolerance=2`` turns a >=3 px delta into an
``image SIZE mismatch`` -> ``<stem>-not-reproduced.png`` (shared
``fig.colorbar(ax=[...])``, ``ax.pie()``, constrained_layout, composed
mm-layout).

The fix saves these rasters FULL-CANVAS and crops to the ONE recorded,
dpi-independent ``content_bbox`` (byte-identical on reproduce), so the saved
SIZE is a pure function of content -- independent of how many times the figure
was drawn. These guards inject EXTRA ``fig.canvas.draw()`` calls on the
reproduced figure (the exact lever that exposed the flake) and assert the
re-saved pixel size equals the original EXACTLY.
"""

import matplotlib

matplotlib.use("Agg")

import numpy as np
from PIL import Image

import figrecipe as fr

_EXTRA_DRAWS = 5


def _png_size(path):
    """Return the (width, height) pixel size of a saved PNG."""
    with Image.open(path) as img:
        return img.size


def _reproduced_size_after_draws(recipe_path, repro_png, n_draws):
    """Reproduce ``recipe_path``, draw ``n_draws`` extra times, re-save, return size."""
    import matplotlib.pyplot as plt

    rfig, _ = fr.reproduce(str(recipe_path))
    mpl_fig = rfig.fig if hasattr(rfig, "fig") else rfig
    for _ in range(n_draws):
        mpl_fig.canvas.draw()
    rfig.savefig(str(repro_png), save_recipe=False, validate=False, verbose=False)
    size = _png_size(repro_png)
    plt.close(mpl_fig)
    return size


def test_pie_reproduced_size_invariant_to_draw_count(tmp_path):
    # Arrange: a pie sets set_aspect("equal") under constrained_layout, whose
    # tight crop re-measures ink at save time.
    fig, ax = fr.subplots()
    ax.pie([3, 1, 4, 1, 5], labels=list("abcde"), autopct="")
    original_png = tmp_path / "pie.png"
    fr.save(fig, str(original_png), validate=False, verbose=False)
    original_size = _png_size(original_png)
    # Act
    reproduced_size = _reproduced_size_after_draws(
        original_png.with_suffix(".yaml"), tmp_path / "pie_repro.png", _EXTRA_DRAWS
    )
    # Assert
    assert reproduced_size == original_size


def test_shared_colorbar_reproduced_size_invariant_to_draw_count(tmp_path):
    # Arrange: two imshow panels sharing one colorbar created on the underlying
    # matplotlib figure (NOT the recorded fr.colorbar wrapper, so the #230
    # cax_bbox pinning does not apply). Under constrained_layout the steal width
    # is draw-history-dependent, so on develop the tight-cropped reproduce drifts
    # to a different pixel SIZE than the original (1408x636 vs 1377x648); the
    # full-canvas content_bbox crop removes that drift.
    data = np.arange(64).reshape(8, 8)
    fig, axes = fr.subplots(ncols=2, constrained_layout=True)
    im0 = axes[0].imshow(data)
    axes[1].imshow(data.T)
    mappable = im0.get_artist() if hasattr(im0, "get_artist") else im0
    fig.fig.colorbar(mappable, ax=[axes[0].ax, axes[1].ax])
    original_png = tmp_path / "shared_colorbar.png"
    fr.save(fig, str(original_png), validate=False, verbose=False)
    original_size = _png_size(original_png)
    # Act
    reproduced_size = _reproduced_size_after_draws(
        original_png.with_suffix(".yaml"),
        tmp_path / "shared_colorbar_repro.png",
        _EXTRA_DRAWS,
    )
    # Assert
    assert reproduced_size == original_size
