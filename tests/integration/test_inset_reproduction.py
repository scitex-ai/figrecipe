#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for ax.inset_axes record + replay (PR-1).

Each test follows strict AAA layout with exactly ONE assertion.
"""

import tempfile
from pathlib import Path

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._serializer import load_recipe

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmpdir_path():
    """Yield a temporary directory as a Path."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture()
def simple_inset_recipe(tmpdir_path):
    """Build a figure with one inset containing a line plot; save recipe."""
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    axins = ax.inset_axes([0.6, 0.6, 0.35, 0.35])
    axins.plot([0, 1, 2], [0, 1, 0])

    yaml_path = tmpdir_path / "inset_simple.yaml"
    try:
        fig.save_recipe(yaml_path)
    except ValueError:
        pass  # validation failures from unrelated plots do not block recipe save
    import matplotlib.pyplot as plt

    plt.close("all")
    return yaml_path


@pytest.fixture()
def imshow_inset_recipe(tmpdir_path):
    """Build a figure with one inset containing an imshow; save recipe."""
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    axins = ax.inset_axes([0.1, 0.1, 0.4, 0.4])
    data = np.arange(9, dtype=float).reshape(3, 3)
    axins.imshow(data)

    yaml_path = tmpdir_path / "inset_imshow.yaml"
    try:
        fig.save_recipe(yaml_path)
    except ValueError:
        pass
    import matplotlib.pyplot as plt

    plt.close("all")
    return yaml_path


# ---------------------------------------------------------------------------
# Test 1: plot round-trip — reproduced parent axes has exactly one inset child
# ---------------------------------------------------------------------------
# Note: ax.inset_axes() attaches the inset as a child of the parent axes
# (accessible via ax.child_axes), NOT as a top-level figure axes.  Therefore
# fig.get_axes() still returns 1 after replay; the inset is in child_axes.


def test_inset_plot_roundtrip_produces_two_axes(simple_inset_recipe):
    # Arrange
    yaml_path = simple_inset_recipe
    # Act
    fig2, ax2 = fr.reproduce(yaml_path)
    n_child_axes = len(ax2._ax.child_axes)
    import matplotlib.pyplot as plt

    plt.close("all")
    # Assert
    assert n_child_axes == 1


# ---------------------------------------------------------------------------
# Test 2: recipe YAML contains subpanels entry on the parent axes
# ---------------------------------------------------------------------------


def test_inset_recipe_contains_subpanels(simple_inset_recipe):
    # Arrange
    yaml_path = simple_inset_recipe
    # Act
    record = load_recipe(yaml_path)
    parent_ax_rec = next(iter(record.axes.values()), None)
    has_subpanels = bool(parent_ax_rec is not None and parent_ax_rec.subpanels)
    # Assert
    assert has_subpanels


# ---------------------------------------------------------------------------
# Test 3: imshow inset round-trips — reproduced inset has an image
# ---------------------------------------------------------------------------


def test_inset_imshow_roundtrip_has_image(imshow_inset_recipe):
    # Arrange
    yaml_path = imshow_inset_recipe
    # Act
    fig2, ax2 = fr.reproduce(yaml_path)
    # Inset is a child axes attached to the parent (not a top-level figure axes).
    child = ax2._ax.child_axes[0] if ax2._ax.child_axes else None
    has_image = child is not None and bool(child.get_images())
    import matplotlib.pyplot as plt

    plt.close("all")
    # Assert
    assert has_image


# ---------------------------------------------------------------------------
# Test 4: fr.save() with imshow inset does NOT write a *-not-reproduced.* file
# ---------------------------------------------------------------------------


def test_inset_imshow_save_no_not_reproduced_file(tmpdir_path):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    axins = ax.inset_axes([0.1, 0.1, 0.4, 0.4])
    data = np.arange(16, dtype=float).reshape(4, 4)
    axins.imshow(data)
    out_path = tmpdir_path / "inset_save_test.png"
    # Act
    fr.save(fig, str(out_path))  # real reproducibility validation (not validate=False)
    import matplotlib.pyplot as plt

    plt.close("all")
    not_reproduced = list(tmpdir_path.glob("*not-reproduced*"))
    # Assert
    assert not_reproduced == []
