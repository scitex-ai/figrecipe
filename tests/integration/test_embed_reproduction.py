#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for ax.embed(source, bounds) — PR-2.

Embeds a recipe / diagram / composed figure as a managed sub-panel that
round-trips. Each test follows strict AAA layout with exactly ONE assertion.
"""

import tempfile
from pathlib import Path

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

import matplotlib.pyplot as plt

import figrecipe as fr
from figrecipe._serializer import load_recipe


@pytest.fixture()
def tmpdir_path():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def _save_recipe(fig, path):
    try:
        fig.save_recipe(path)
    except ValueError:
        pass
    plt.close("all")


@pytest.fixture()
def single_recipe(tmpdir_path):
    """A saved single-axes recipe to embed."""
    fig, ax = fr.subplots(axes_width_mm=40, axes_height_mm=30)
    ax.plot([0, 1, 2], [0, 1, 0])
    path = tmpdir_path / "src.yaml"
    _save_recipe(fig, path)
    return path


@pytest.fixture()
def embedded_recipe(tmpdir_path, single_recipe):
    """A figure that embeds `single_recipe`, saved to a recipe."""
    fig, ax = fr.subplots(axes_width_mm=80, axes_height_mm=60)
    ax.plot([0, 1, 2, 3], [3, 2, 1, 0])
    ax.embed(str(single_recipe), bounds=[0.55, 0.55, 0.4, 0.4])
    out = tmpdir_path / "embedded.yaml"
    _save_recipe(fig, out)
    return out


def test_embed_recorded_as_subpanel(embedded_recipe):
    # Arrange
    record = load_recipe(embedded_recipe)
    parent = next(iter(record.axes.values()), None)
    # Act
    has_subpanels = bool(parent is not None and parent.subpanels)
    # Assert
    assert has_subpanels


def test_embed_reproduces_one_inset(embedded_recipe):
    # Arrange
    yaml_path = embedded_recipe
    # Act
    _, ax2 = fr.reproduce(yaml_path)
    n_child = len(ax2._ax.child_axes)
    plt.close("all")
    # Assert
    assert n_child == 1


def test_embed_single_recipe_save_no_not_reproduced(tmpdir_path, single_recipe):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=80, axes_height_mm=60)
    ax.plot([0, 1, 2, 3], [3, 2, 1, 0])
    ax.embed(str(single_recipe), bounds=[0.55, 0.55, 0.4, 0.4])
    # Act
    fr.save(fig, str(tmpdir_path / "embed_save.png"))  # real validation
    plt.close("all")
    # Assert
    assert list(tmpdir_path.glob("*not-reproduced*")) == []


def test_embed_diagram_save_no_not_reproduced(tmpdir_path):
    # Arrange
    d = fr.Diagram(title="mini", width_mm=80, height_mm=40)
    d.add_box("a", "A")
    d.add_box("b", "B")
    d.add_arrow("a", "b")
    dfig, dax = fr.subplots(axes_width_mm=80, axes_height_mm=40)
    dax.diagram(d)
    _save_recipe(dfig, tmpdir_path / "diag.yaml")
    fig, ax = fr.subplots(axes_width_mm=90, axes_height_mm=60)
    ax.plot([0, 1, 2], [0, 1, 0])
    ax.embed(str(tmpdir_path / "diag.yaml"), bounds=[0.05, 0.5, 0.45, 0.45])
    # Act
    fr.save(fig, str(tmpdir_path / "embed_diag.png"))
    plt.close("all")
    # Assert
    assert list(tmpdir_path.glob("*not-reproduced*")) == []


def test_embed_composed_creates_multiple_insets(tmpdir_path):
    # Arrange
    a, aa = fr.subplots(axes_width_mm=40, axes_height_mm=30)
    aa.plot([0, 1, 2], [2, 1, 0])
    b, bb = fr.subplots(axes_width_mm=40, axes_height_mm=30)
    bb.imshow(np.arange(9).reshape(3, 3))
    _save_recipe(a, tmpdir_path / "pa.yaml")
    _save_recipe(b, tmpdir_path / "pb.yaml")
    comp, _ = fr.compose(
        {
            str(tmpdir_path / "pa.yaml"): {"xy_mm": (0, 0), "size_mm": (40, 30)},
            str(tmpdir_path / "pb.yaml"): {"xy_mm": (0, 33), "size_mm": (40, 30)},
        },
        canvas_size_mm=(42, 65),
    )
    _save_recipe(comp, tmpdir_path / "comp.yaml")
    fig, ax = fr.subplots(axes_width_mm=100, axes_height_mm=80)
    # Act
    result = ax.embed(str(tmpdir_path / "comp.yaml"), bounds=[0.05, 0.05, 0.5, 0.9])
    n = len(result) if isinstance(result, list) else 1
    plt.close("all")
    # Assert
    assert n == 2
