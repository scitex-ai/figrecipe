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
import pytest

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


def _raw_colorbar_axes(reproduced_fig):
    """Colorbar Axes on the underlying mpl figure of a reproduced RecordingFigure."""
    mpl_fig = getattr(reproduced_fig, "fig", reproduced_fig)
    return [a for a in mpl_fig.axes if getattr(a, "_colorbar", None) is not None]


@pytest.fixture
def manual_cax_roundtrip(tmp_path):
    """Build + save + reproduce a fig whose MANUAL ``plt.colorbar(im, cax=...)``.

    Reproduces the bug where the module-level ``figrecipe.pyplot.colorbar`` was the
    raw matplotlib function, so a manual colorbar bypassed the recorder, left ZERO
    ``colorbars`` entries in the recipe, and was DROPPED when the figure was rebuilt.

    Returns ``(fig, recipe_dict, reproduced_fig)``.
    """
    import yaml

    import figrecipe.pyplot as plt

    rng = np.random.default_rng(2)
    fig, ax = plt.subplots(1, 1)
    ax.imshow(rng.standard_normal((10, 10)), cmap="viridis")
    im = ax.get_images()[0]
    cax = fig.add_axes([0.9, 0.1, 0.03, 0.8])
    plt.colorbar(im, cax=cax)

    image_path = tmp_path / "manual_cax.png"
    fr.save(fig, str(image_path), validate=False, verbose=False)
    yaml_path = image_path.with_suffix(".yaml")
    recipe = yaml.safe_load(yaml_path.read_text())

    reproduced = fr.reproduce(str(yaml_path))
    rfig = reproduced[0] if isinstance(reproduced, tuple) else reproduced
    return fig, recipe, rfig


def test_manual_plt_colorbar_with_cax_is_recorded(manual_cax_roundtrip):
    # Arrange
    fig, _recipe, _rfig = manual_cax_roundtrip
    # Act
    n_recorded = len(fig.record.colorbars)
    # Assert
    assert n_recorded == 1


def test_manual_plt_colorbar_with_cax_serializes_to_recipe(manual_cax_roundtrip):
    # Arrange
    _fig, recipe, _rfig = manual_cax_roundtrip
    # Act
    colorbars = recipe.get("figure", {}).get("colorbars")
    # Assert
    assert colorbars  # used to be empty -> colorbar dropped


def test_manual_plt_colorbar_with_cax_captures_geometry(manual_cax_roundtrip):
    # Arrange
    _fig, recipe, _rfig = manual_cax_roundtrip
    # Act
    cax_bbox = recipe["figure"]["colorbars"][0].get("cax_bbox")
    # Assert
    assert cax_bbox is not None


def test_manual_plt_colorbar_with_cax_replays_colorbar_axes(manual_cax_roundtrip):
    # Arrange
    _fig, _recipe, rfig = manual_cax_roundtrip
    # Act
    n_cbar_axes = len(_raw_colorbar_axes(rfig))
    # Assert
    assert n_cbar_axes == 1


@pytest.fixture
def standalone_mappable_roundtrip(tmp_path):
    """Build + save + reproduce a manual colorbar over a STANDALONE ScalarMappable.

    The NeuroVista shared-comodulogram pattern: a freestanding
    ``cm.ScalarMappable(cmap=, norm=)`` (no source plot call) drawn into a gridspec
    ``cax``. The recorder captures a ``mappable_spec`` (cmap + clim) so the
    reproducer can rebuild the mappable and re-create the colorbar.

    Returns ``(fig, recipe_dict, reproduced_fig, (vmin, vmax))``.
    """
    import yaml
    from matplotlib import cm
    from matplotlib.colors import Normalize

    import figrecipe.pyplot as plt

    rng = np.random.default_rng(3)
    vmin, vmax = -2.0, 3.0
    fig, axes = plt.subplots(2, 2)
    for ax in np.asarray(axes).ravel():
        ax.imshow(rng.standard_normal((8, 8)), cmap="hot", vmin=vmin, vmax=vmax)
    cax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    sm = cm.ScalarMappable(cmap="hot", norm=Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    plt.colorbar(sm, cax=cax)

    image_path = tmp_path / "manual_standalone.png"
    fr.save(fig, str(image_path), validate=False, verbose=False)
    yaml_path = image_path.with_suffix(".yaml")
    recipe = yaml.safe_load(yaml_path.read_text())

    reproduced = fr.reproduce(str(yaml_path))
    rfig = reproduced[0] if isinstance(reproduced, tuple) else reproduced
    return fig, recipe, rfig, (vmin, vmax)


def test_standalone_mappable_records_cmap_spec(standalone_mappable_roundtrip):
    # Arrange
    fig, _recipe, _rfig, _clim = standalone_mappable_roundtrip
    # Act
    cmap = fig.record.colorbars[0].get("mappable_spec", {}).get("cmap")
    # Assert
    assert cmap == "hot"


def test_standalone_mappable_serializes_clim(standalone_mappable_roundtrip):
    # Arrange
    _fig, recipe, _rfig, (vmin, vmax) = standalone_mappable_roundtrip
    # Act
    spec = recipe["figure"]["colorbars"][0]["mappable_spec"]
    # Assert
    assert (spec["vmin"], spec["vmax"]) == (vmin, vmax)


def test_standalone_mappable_replays_colorbar_axes(standalone_mappable_roundtrip):
    # Arrange
    _fig, _recipe, rfig, _clim = standalone_mappable_roundtrip
    # Act
    n_cbar_axes = len(_raw_colorbar_axes(rfig))
    # Assert
    assert n_cbar_axes == 1


def test_pyplot_colorbar_is_recording_wrapper():
    # Arrange
    import matplotlib.pyplot as _mpl_plt

    import figrecipe.pyplot as plt

    # Act
    is_passthrough = plt.colorbar is _mpl_plt.colorbar
    # Assert
    assert not is_passthrough
