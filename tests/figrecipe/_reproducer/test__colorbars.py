#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduction of a shared colorbar's geometry.

``fig.colorbar(im, ax=axes.ravel().tolist(), ...)`` steals space from several
panels. Under ``constrained_layout`` that steal has no single fixed point, so a
naive reproduce re-steals to a different cax width and the tight-cropped image
comes out a different pixel SIZE -- the save-time reproducibility validator then
fails loud and writes a ``<stem>-not-reproduced.<ext>`` artifact beside the
figure. The recorder now captures the colorbar's resolved geometry (``cax_bbox``
+ ``cax_ticks``) and the reproducer pins it exactly, so the reproduction matches
the original and no artifact is written.
"""

import matplotlib

matplotlib.use("Agg")

import numpy as np

import figrecipe as fr


def test_shared_colorbar_reproduces_without_artifact(tmp_path):
    # Arrange: a 2x2 imshow grid with a single colorbar shared across all tiles.
    rng = np.random.default_rng(0)
    fig, axes = fr.subplots(2, 2, constrained_layout=True)
    im = None
    for ax in axes.ravel():
        im = ax.imshow(rng.standard_normal((10, 12)), cmap="viridis")
    fig.colorbar(im, ax=axes.ravel().tolist(), label="z", shrink=0.6, pad=0.02)
    image_path = tmp_path / "shared_colorbar.png"

    # Act: save (validation reproduces the recipe and compares to the original).
    fr.save(fig, str(image_path), validate=True, verbose=False)

    # Assert: no "-not-reproduced" artifact -> the colorbar figure reproduced.
    artifact = image_path.parent / f"{image_path.stem}-not-reproduced.png"
    assert not artifact.exists()
