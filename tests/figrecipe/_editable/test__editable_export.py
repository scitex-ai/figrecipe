#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: tests/figrecipe/_editable/test__editable_export.py

"""Tests for figrecipe-native editable-figure export + save_editable."""

import copy
import json

import numpy as np
import pytest


@pytest.fixture
def editable_dict():
    import figrecipe as fr

    fig, axes = fr.subplots(2, 2)
    x = np.linspace(0, 10, 50)
    axes[0][0].plot(x, np.sin(x), id="sine")
    axes[0][1].scatter(x, np.cos(x), id="scat")
    axes[1][0].bar([1, 2, 3], [3, 1, 2], id="bars")
    axes[1][1].imshow(np.random.RandomState(0).rand(10, 10), id="img")
    return fr.export_editable(fig)


def test_export_editable_uses_editable_schema_name(editable_dict):
    # Arrange
    d = editable_dict
    # Act
    schema = d["scitex_schema"]
    # Assert
    assert schema == "scitex.plt.figure.editable"


def test_export_editable_uses_schema_version_0_3(editable_dict):
    # Arrange
    d = editable_dict
    # Act
    version = d["scitex_schema_version"]
    # Assert
    assert version == "0.3.0"


def test_export_editable_has_top_level_structure(editable_dict):
    # Arrange
    d = editable_dict
    # Act
    keys = set(d.keys())
    # Assert
    assert {"meta", "figure", "axes", "elements"} <= keys


def test_export_editable_has_four_axes(editable_dict):
    # Arrange
    d = editable_dict
    # Act
    n_axes = len(d["axes"])
    # Assert
    assert n_axes == 4


def test_export_editable_axes_carry_bbox_px(editable_dict):
    # Arrange
    d = editable_dict
    # Act
    subkeys = {k for ax in d["axes"].values() for k in ax}
    # Assert
    assert {"bbox_px", "position", "xlim", "ylim"} <= subkeys


def test_export_editable_covers_all_element_types(editable_dict):
    # Arrange
    d = editable_dict
    # Act
    types = {v["element_type"] for v in d["elements"].values()}
    # Assert
    assert {"line", "scatter", "bar", "image"} <= types


def test_export_editable_elements_have_axes_coord_space(editable_dict):
    # Arrange
    d = editable_dict
    # Act
    spaces = {v["geometry_px"].get("coord_space") for v in d["elements"].values()}
    # Assert
    assert spaces == {"axes"}


def test_export_editable_is_json_serializable(editable_dict):
    # Arrange
    d = editable_dict
    # Act
    text = json.dumps(d)
    # Assert
    assert text


def test_save_editable_writes_json_sidecar(tmp_path):
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 0], id="line")
    out = tmp_path / "plot.png"
    # Act
    fr.save(
        fig, out, save_recipe=False, validate=False, verbose=False, save_editable=True
    )
    # Assert
    assert (tmp_path / "plot.json").exists()


def test_save_editable_sidecar_has_editable_schema(tmp_path):
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 0], id="line")
    out = tmp_path / "plot.png"
    # Act
    fr.save(
        fig, out, save_recipe=False, validate=False, verbose=False, save_editable=True
    )
    data = json.loads((tmp_path / "plot.json").read_text())
    # Assert
    assert data["scitex_schema"] == "scitex.plt.figure.editable"


def test_save_editable_default_off(tmp_path):
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 0], id="line")
    out = tmp_path / "plot.png"
    # Act
    fr.save(fig, out, save_recipe=False, validate=False, verbose=False)
    # Assert
    assert not (tmp_path / "plot.json").exists()


def test_parity_with_umbrella_reference():
    # Arrange
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metadata = pytest.importorskip(
        "scitex.plt.utils.metadata",
        reason="scitex umbrella reference exporter not importable",
    )
    ref_export = metadata.export_editable_figure

    import figrecipe as fr

    def build_mpl():
        fig, axes = plt.subplots(2, 2)
        x = np.linspace(0, 10, 50)
        axes[0, 0].plot(x, np.sin(x))
        axes[0, 1].scatter(x, np.cos(x))
        axes[1, 0].bar([1, 2, 3], [3, 1, 2])
        axes[1, 1].imshow(np.random.RandomState(0).rand(10, 10))
        fig.canvas.draw()
        return fig

    def strip(d):
        d = copy.deepcopy(d)
        d["meta"].pop("exported_at", None)
        return d

    # Act
    mine = strip(fr.export_editable(build_mpl()))
    ref = strip(ref_export(build_mpl()))
    # Assert
    assert mine == ref
